"""
自動車カタログDBエージェント。
PostgreSQL の car_catalog テーブルにアクセスするツールを持ち、
親エージェントから ask_car_catalog ツールとして呼び出される。
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from strands import Agent, tool

from core.config import create_model
from core.prompts import get_prompt, PROMPT_CAR_CATALOG_AGENT

load_dotenv()

DB_URL = os.getenv(
    "MEMORY_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/agent_memory",
)


def _get_conn():
    return psycopg2.connect(DB_URL)


# ── カタログ検索ツール ─────────────────────────────────────────────────

@tool
def search_car_catalog(
    manufacturer: str = "",
    body_type: str = "",
    engine_type: str = "",
    max_price_man_yen: int = 0,
    min_fuel_economy: float = 0.0,
) -> str:
    """
    条件を指定して自動車カタログを検索する。
    すべてのパラメータは省略可能で、指定した条件のAND検索を行う。

    Args:
        manufacturer: メーカー名（例: "トヨタ", "ホンダ", "スバル"）。空文字で全メーカー。
        body_type: ボディタイプのキーワード（例: "SUV", "セダン", "ミニバン"）。空文字で絞り込みなし。
        engine_type: エンジン種別キーワード（例: "ハイブリッド", "ガソリン", "PHV"）。空文字で絞り込みなし。
        max_price_man_yen: 価格上限（万円）。0 で絞り込みなし。
        min_fuel_economy: 燃費下限（km/L）。0.0 で絞り込みなし。

    Returns:
        JSON 文字列（車種一覧）。
    """
    conditions = []
    params = []

    if manufacturer:
        conditions.append("manufacturer = %s")
        params.append(manufacturer)
    if body_type:
        conditions.append("body_type ILIKE %s")
        params.append(f"%{body_type}%")
    if engine_type:
        conditions.append("engine_type ILIKE %s")
        params.append(f"%{engine_type}%")
    if max_price_man_yen > 0:
        conditions.append("price_min_man_yen <= %s")
        params.append(max_price_man_yen)
    if min_fuel_economy > 0.0:
        conditions.append("fuel_economy_wltc >= %s")
        params.append(min_fuel_economy)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""
        SELECT manufacturer, model_name, year, body_type, engine_type,
               max_power_ps, fuel_economy_wltc, seating_capacity,
               price_min_man_yen, drivetrain
        FROM car_catalog
        {where}
        ORDER BY manufacturer, model_name
    """

    try:
        with _get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        result = [dict(r) for r in rows]
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def get_car_details(manufacturer: str, model_name: str) -> str:
    """
    指定した車種の詳細情報（安全装備・特徴・説明文を含む全カラム）を取得する。

    Args:
        manufacturer: メーカー名（例: "トヨタ"）
        model_name: 車種名（例: "プリウス"）

    Returns:
        JSON 文字列（詳細情報）。
    """
    sql = "SELECT * FROM car_catalog WHERE manufacturer = %s AND model_name = %s"
    try:
        with _get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (manufacturer, model_name))
                row = cur.fetchone()
        if row is None:
            return json.dumps(
                {"error": f"{manufacturer} {model_name} は見つかりませんでした。"},
                ensure_ascii=False,
            )
        return json.dumps(dict(row), ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def list_all_models() -> str:
    """
    カタログに登録されているすべての車種（メーカー・モデル名・年式・価格）を一覧で返す。

    Returns:
        JSON 文字列（全車種一覧）。
    """
    sql = """
        SELECT manufacturer, model_name, year, price_min_man_yen
        FROM car_catalog
        ORDER BY manufacturer, model_name
    """
    try:
        with _get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        return json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# ── カタログ専用子エージェント ────────────────────────────────────────

_catalog_agent = Agent(
    model=create_model(),
    system_prompt=get_prompt(PROMPT_CAR_CATALOG_AGENT),
    tools=[search_car_catalog, get_car_details, list_all_models],
)


@tool
def ask_car_catalog(question: str) -> str:
    """
    自動車カタログDBに関する質問をカタログ専門エージェントに委譲する。
    車種の比較・絞り込み・価格・燃費・スペック照会などに使用する。

    Args:
        question: カタログに関する質問（日本語）

    Returns:
        カタログエージェントからの回答文字列
    """
    response = _catalog_agent(question)
    return str(response)
