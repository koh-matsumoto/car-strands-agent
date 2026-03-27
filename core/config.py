"""
LLMプロバイダーの設定モジュール。
.env の LLM_PROVIDER 変数に応じてモデルを切り替える。
"""

import os
from dotenv import load_dotenv

load_dotenv()


def create_model():
    """
    環境変数に基づいてStrandsのモデルオブジェクトを生成して返す。
    LLM_PROVIDER が未設定の場合は Amazon Bedrock をデフォルトとして使用する。
    """
    provider = os.getenv("LLM_PROVIDER", "bedrock").lower()
    model_id = os.getenv("LLM_MODEL_ID", "claude-opus-4-5-20251001")

    if provider == "anthropic":
        from strands.models.anthropic import AnthropicModel
        return AnthropicModel(
            model_id=model_id,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
            client_args={"api_key": os.environ["ANTHROPIC_API_KEY"]},
        )

    if provider == "openai":
        from strands.models.litellm import LiteLLMModel
        params = {"api_key": os.environ["OPENAI_API_KEY"]}
        base_url = os.getenv("OPENAI_BASE_URL")
        if base_url:
            params["api_base"] = base_url
        return LiteLLMModel(model_id=f"openai/{model_id}", params=params)

    if provider == "litellm":
        from strands.models.litellm import LiteLLMModel
        params = {
            "api_base": os.environ["LLM_API_BASE"],
            "api_key": os.getenv("LLM_API_KEY", "dummy"),
        }
        return LiteLLMModel(model_id=model_id, params=params)

    if provider == "ollama":
        from strands.models.ollama import OllamaModel
        return OllamaModel(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model_id=os.getenv("OLLAMA_MODEL", model_id),
        )

    # デフォルト: Amazon Bedrock
    from strands.models.bedrock import BedrockModel
    return BedrockModel(
        model_id=model_id,
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
