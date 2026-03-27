"""
自動車専門の子エージェント。
親エージェントから Tool として呼び出される。
長期記憶（pgvector）を使って過去の会話内容を参照・保存する。
"""

from strands import Agent
from strands.tools import tool
from core.config import create_model
from core.prompts import get_prompt, PROMPT_CAR_AGENT
from core.memory import LongTermMemory

# 子エージェントのインスタンス（モジュールロード時に1度だけ生成）
_car_agent = Agent(
    model=create_model(),
    system_prompt=get_prompt(PROMPT_CAR_AGENT),
)

# 長期記憶（car_agent 専用）
_memory = LongTermMemory(agent_id="car-agent")


@tool
def ask_car_expert(question: str) -> str:
    """
    自動車の専門家エージェントに質問する。
    車・バイク・乗り物に関する質問（仕様、メンテナンス、歴史、メーカー、
    燃費、安全機能、購入アドバイスなど）に答えられる。

    Args:
        question: 自動車・乗り物に関する質問

    Returns:
        専門家エージェントからの回答
    """
    # 1. 長期記憶から関連する過去の情報を検索
    memories = _memory.search(question, top_k=3)
    if memories:
        context = "\n".join(f"- {m['content']}" for m in memories)
        augmented = f"[過去の記憶（参考情報）]\n{context}\n\n[質問]\n{question}"
    else:
        augmented = question

    # 2. エージェントに回答させる
    response = _car_agent(augmented)
    answer = str(response)

    # 3. 今回の Q&A を長期記憶に保存（回答は先頭200文字に圧縮）
    _memory.add(
        content=f"Q: {question}\nA: {answer[:200]}",
        metadata={"type": "qa"},
    )

    return answer
