"""
Langfuse トレーシング設定モジュール。
OTEL exporter を Langfuse の OTEL エンドポイントに向ける。

前提:
  .env に LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY が設定されていること。
  LANGFUSE_ENABLED=false にするとトレーシングをスキップできる。
"""

import base64
import os

from dotenv import load_dotenv

load_dotenv()


def setup_langfuse_tracing() -> bool:
    """
    Langfuse への OTEL トレーシングを初期化する。
    LANGFUSE_ENABLED が false の場合はスキップして False を返す。
    成功時は True を返す。
    """
    if os.getenv("LANGFUSE_ENABLED", "true").lower() == "false":
        return False

    public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
    secret_key = os.environ["LANGFUSE_SECRET_KEY"]
    host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

    # Langfuse は Basic 認証（pk:sk を Base64 エンコード）を要求する
    auth_token = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    endpoint = f"{host}/api/public/otel/v1/traces"

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": "strands-agent"})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=endpoint,
                headers={"Authorization": f"Basic {auth_token}"},
            )
        )
    )
    trace.set_tracer_provider(provider)

    print(f"[Tracing] Langfuse OTEL トレーシングを有効化: {host}")
    return True
