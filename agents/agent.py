"""
Strands Agent SDK を使ったシンプルなAIエージェント。
ツールは持たず、LLMの知識のみで応答する。
"""

from strands import Agent
from core.config import create_model
from core.prompts import get_prompt, PROMPT_SIMPLE_AGENT


def build_agent() -> Agent:
    """エージェントを構築して返す。"""
    agent = Agent(
        model=create_model(),
        system_prompt=get_prompt(PROMPT_SIMPLE_AGENT),
        # tools=[]  # ← ツールなし（デフォルト）
    )
    return agent
