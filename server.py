"""
Strands Agent Web サーバー。
FastAPI でエージェントをWebインターフェースとして提供する。

起動: uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.tracing import setup_langfuse_tracing
from core.tts import generate_audio
from core.sessions import list_sessions, create_session, get_session, add_message, delete_session
from agents.agent import build_agent
from agents.parent_agent import build_parent_agent
from core.memory import LongTermMemory


executor = ThreadPoolExecutor(max_workers=2)
state: dict = {}
_simple_lock = asyncio.Lock()
_multi_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_langfuse_tracing()
    print("[Server] エージェントを初期化中...")
    state["simple"] = build_agent()
    state["multi"] = build_parent_agent()
    try:
        state["memory"] = LongTermMemory(agent_id="parent-agent")
        print("[Server] 長期記憶DBに接続しました。")
    except Exception as e:
        print(f"[Server] 長期記憶DBに接続できません（マルチモードは記憶なしで動作）: {e}")
        state["memory"] = None
    print("[Server] 準備完了。")
    yield
    if state.get("memory"):
        state["memory"].close()


app = FastAPI(lifespan=lifespan)


# ── リクエストモデル ──────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str
    mode: str = "simple"
    tts: bool = True

class NewSessionRequest(BaseModel):
    mode: str = "simple"


# ── エージェント実行 ──────────────────────────────────────

def _run_simple(message: str) -> str:
    return str(state["simple"](message))


def _run_multi(message: str) -> str:
    memory: LongTermMemory | None = state.get("memory")
    if memory:
        memories = memory.search(message, top_k=3)
        if memories:
            context = "\n".join(f"- {m['content']}" for m in memories)
            augmented = f"[過去の記憶（参考情報）]\n{context}\n\n[ユーザーの入力]\n{message}"
        else:
            augmented = message
    else:
        augmented = message

    answer = str(state["multi"](augmented))

    if memory:
        memory.add(content=f"Q: {message}\nA: {answer[:200]}", metadata={"type": "qa"})

    return answer


# ── セッション API ────────────────────────────────────────

@app.get("/api/sessions")
async def api_list_sessions():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, list_sessions)


@app.post("/api/sessions")
async def api_create_session(req: NewSessionRequest):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, create_session, req.mode)


@app.get("/api/sessions/{sid}")
async def api_get_session(sid: str):
    loop = asyncio.get_event_loop()
    session = await loop.run_in_executor(executor, get_session, sid)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません。")
    return session


@app.delete("/api/sessions/{sid}")
async def api_delete_session(sid: str):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, delete_session, sid)
    return {"ok": True}


# ── チャット API ──────────────────────────────────────────

@app.post("/api/chat")
async def chat(req: ChatRequest):
    if req.mode not in ("simple", "multi"):
        raise HTTPException(status_code=400, detail="mode は 'simple' または 'multi' を指定してください。")

    loop = asyncio.get_event_loop()

    await loop.run_in_executor(executor, add_message, req.session_id, "user", req.message)

    if req.mode == "multi":
        async with _multi_lock:
            response = await loop.run_in_executor(executor, _run_multi, req.message)
    else:
        async with _simple_lock:
            response = await loop.run_in_executor(executor, _run_simple, req.message)

    await loop.run_in_executor(executor, add_message, req.session_id, "agent", response)

    audio_b64 = None
    if req.tts:
        audio_bytes = await loop.run_in_executor(executor, generate_audio, response)
        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode()

    return {"response": response, "audio": audio_b64}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
