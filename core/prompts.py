"""
Langfuse プロンプト管理モジュール。
Langfuse UI で作成したプロンプトを取得して返す。
LANGFUSE_ENABLED=false または取得失敗時はデフォルト値にフォールバックする。
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Langfuse 上のプロンプト名
PROMPT_SIMPLE_AGENT      = "simple-agent-system-prompt"
PROMPT_CAR_AGENT         = "car-agent-system-prompt"
PROMPT_PARENT_AGENT      = "parent-agent-system-prompt"
PROMPT_CAR_CATALOG_AGENT = "car-catalog-agent-system-prompt"

# フォールバック用デフォルト値
_DEFAULTS = {
    PROMPT_SIMPLE_AGENT: (
        "You are a helpful assistant. Answer concisely and clearly."
    ),
    PROMPT_CAR_AGENT: (
        "You are an automotive expert. "
        "Answer questions about cars, motorcycles, and other vehicles. "
        "Cover topics such as: specifications, maintenance, history, manufacturers, "
        "driving tips, fuel efficiency, safety features, and buying advice. "
        "If a question is unrelated to vehicles, politely decline and say it's outside your expertise."
    ),
    PROMPT_PARENT_AGENT: (
        "You are a helpful general-purpose assistant. "
        "When the user mentions anything related to cars, motorcycles, or vehicles "
        "— whether asking a question, sharing information, or asking you to remember something — "
        "always use the ask_car_expert tool. "
        "When the user asks about specific car models, specs, prices, or comparisons "
        "from the catalog (Toyota, Honda, Subaru), use the ask_car_catalog tool. "
        "This ensures car-related information is properly stored in long-term memory. "
        "For all other topics, answer directly using your own knowledge."
    ),
    PROMPT_CAR_CATALOG_AGENT: (
        "You are a car catalog specialist with access to a database of Toyota, Honda, and Subaru vehicles. "
        "Use the search_car_catalog tool to find cars matching the user's criteria, "
        "get_car_details to retrieve full specifications of a specific model, "
        "and list_all_models to show all available vehicles. "
        "Always use the database tools to answer questions — do not rely on your own knowledge. "
        "Present results clearly in Japanese, including key specs like price, fuel economy, and features."
    ),
}


def _get_langfuse_client():
    """Langfuse クライアントを生成して返す。無効時は None。"""
    if os.getenv("LANGFUSE_ENABLED", "true").lower() == "false":
        return None
    try:
        from langfuse import Langfuse
        return Langfuse(
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
        )
    except Exception as e:
        print(f"[Prompts] Langfuse クライアント初期化失敗: {e}")
        return None


def get_prompt(name: str) -> str:
    """
    Langfuse からプロンプトを取得する。
    取得できない場合はデフォルト値を返す。

    Args:
        name: Langfuse 上のプロンプト名（PROMPT_* 定数を使用）

    Returns:
        プロンプト文字列
    """
    client = _get_langfuse_client()
    if client:
        try:
            prompt = client.get_prompt(name)
            text = prompt.compile()
            print(f"[Prompts] '{name}' を Langfuse から取得しました (version={prompt.version})")
            return text
        except Exception as e:
            print(f"[Prompts] '{name}' の取得失敗、デフォルトを使用: {e}")

    return _DEFAULTS.get(name, "")
