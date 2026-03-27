"""
長期記憶モジュール。
pgvector を使って会話内容をベクトルとして保存し、意味検索で取得する。
埋め込みには sentence-transformers（ローカル実行・APIキー不要）を使用する。
"""

import os
from typing import Optional

import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

load_dotenv()

# 埋め込みモデル（初回呼び出し時にロード）
_encoder = None
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def _get_encoder():
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer
        print(f"[Memory] 埋め込みモデルをロード中: {EMBEDDING_MODEL}")
        _encoder = SentenceTransformer(EMBEDDING_MODEL)
    return _encoder


class LongTermMemory:
    """
    エージェントの長期記憶。
    add()   : テキストをベクトル化してDBに保存
    search(): クエリに意味的に近い記憶を取得
    """

    _TABLE = "agent_memories"

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self._conn = psycopg2.connect(
            os.getenv("MEMORY_DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/agent_memory")
        )
        # extension を先に作成してから vector 型を登録する
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        self._conn.commit()
        register_vector(self._conn)
        self._init_db()

    def _init_db(self) -> None:
        """テーブルとインデックスを初期化する（冪等）。"""
        with self._conn.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._TABLE} (
                    id          SERIAL PRIMARY KEY,
                    agent_id    VARCHAR(100)  NOT NULL,
                    content     TEXT          NOT NULL,
                    embedding   vector({EMBEDDING_DIM}),
                    metadata    JSONB,
                    created_at  TIMESTAMPTZ   DEFAULT NOW()
                )
            """)
            # HNSW インデックス（データ数に関係なく作成可能）
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {self._TABLE}_hnsw_idx
                ON {self._TABLE} USING hnsw (embedding vector_cosine_ops)
            """)
        self._conn.commit()

    def add(self, content: str, metadata: Optional[dict] = None) -> None:
        """テキストをベクトル化して長期記憶に保存する。"""
        from psycopg2.extras import Json
        embedding = _get_encoder().encode(content).tolist()
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {self._TABLE} (agent_id, content, embedding, metadata)
                VALUES (%s, %s, %s, %s)
                """,
                (self.agent_id, content, embedding, Json(metadata or {})),
            )
        self._conn.commit()

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """クエリに意味的に近い記憶を返す（コサイン類似度順）。"""
        embedding = _get_encoder().encode(query).tolist()
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT content, metadata,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM   {self._TABLE}
                WHERE  agent_id = %s
                ORDER  BY embedding <=> %s::vector
                LIMIT  %s
                """,
                (embedding, self.agent_id, embedding, top_k),
            )
            rows = cur.fetchall()
        return [
            {"content": row[0], "metadata": row[1], "similarity": round(float(row[2]), 4)}
            for row in rows
        ]

    def close(self) -> None:
        self._conn.close()
