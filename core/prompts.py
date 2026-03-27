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
        "あなたは気さくなAIアシスタントです。"
        "返答は必ず1〜3文以内に収めてください。"
        "箇条書き・見出し・長い説明は禁止。普通の話し言葉で短く返す。"
        "詳しく聞きたそうなら「もっと詳しく話す？」と一言添える程度でOK。"
        "日本語で答える。"
    ),
    PROMPT_CAR_AGENT: (
        "あなたは車好きの専門家です。"
        "返答は必ず1〜3文以内に収めてください。"
        "箇条書き・見出し・長い説明は禁止。口語で短くテンポよく返す。"
        "クルマと無関係な質問は「それは専門外ですね」と一言で断る。"
        "日本語で答える。"
    ),
    PROMPT_PARENT_AGENT: (
        "あなたは気さくなAIアシスタントです。"
        "返答は必ず1〜3文以内に収めてください。"
        "箇条書き・見出し・長い説明は禁止。口語で短くテンポよく返す。"
        "クルマ・バイク・乗り物の話題は ask_car_expert を使う。"
        "トヨタ・ホンダ・スバルの車種・価格・スペックは ask_car_catalog を使う。"
        "日本語で答える。"
    ),
    PROMPT_CAR_CATALOG_AGENT: (
        "あなたはトヨタ・ホンダ・スバルのカタログ専門家です。"
        "返答は必ず1〜3文以内に収めてください。"
        "箇条書き・見出し・長い説明は禁止。口語で短くテンポよく返す。"
        "必ず search_car_catalog / get_car_details / list_all_models を使って答える。"
        "日本語で答える。"
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
