"""
親エージェント。
自動車専門の子エージェントと自動車カタログエージェントを Tool として持ち、
必要に応じて委譲する。
"""

from strands import Agent
from core.config import create_model
from agents.car_agent import ask_car_expert
from agents.car_catalog_agent import ask_car_catalog
from core.prompts import get_prompt, PROMPT_PARENT_AGENT


def build_parent_agent() -> Agent:
    """親エージェントを構築して返す。"""
    agent = Agent(
        model=create_model(),
        system_prompt=get_prompt(PROMPT_PARENT_AGENT),
        tools=[ask_car_expert, ask_car_catalog],
    )
    return agent
