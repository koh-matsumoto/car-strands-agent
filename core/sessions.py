"""
セッション管理モジュール。
会話履歴を sessions.json に保存・取得する。
"""

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

_FILE = Path(__file__).parent.parent / "sessions.json"
_lock = threading.Lock()


def _load() -> dict:
    if _FILE.exists():
        return json.loads(_FILE.read_text(encoding="utf-8"))
    return {}


def _save(data: dict) -> None:
    _FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_sessions() -> list[dict]:
    with _lock:
        data = _load()
    sessions = sorted(data.values(), key=lambda s: s["updated_at"], reverse=True)
    return [
        {"id": s["id"], "title": s["title"], "mode": s["mode"], "updated_at": s["updated_at"]}
        for s in sessions
    ]


def create_session(mode: str = "simple") -> dict:
    now = _now()
    session = {
        "id": str(uuid.uuid4()),
        "title": "新しいチャット",
        "mode": mode,
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }
    with _lock:
        data = _load()
        data[session["id"]] = session
        _save(data)
    return session


def get_session(sid: str) -> dict | None:
    with _lock:
        return _load().get(sid)


def add_message(sid: str, role: str, content: str) -> None:
    now = _now()
    with _lock:
        data = _load()
        if sid not in data:
            return
        session = data[sid]
        session["messages"].append({"role": role, "content": content, "timestamp": now})
        if role == "user" and session["title"] == "新しいチャット":
            session["title"] = content[:40] + ("…" if len(content) > 40 else "")
        session["updated_at"] = now
        _save(data)


def delete_session(sid: str) -> None:
    with _lock:
        data = _load()
        data.pop(sid, None)
        _save(data)
