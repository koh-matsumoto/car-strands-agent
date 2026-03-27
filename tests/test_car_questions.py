"""
自動車専門エージェントへの質問テスト（3件）。
各テストの質問と回答は tests/results/car_questions.json に保存される。
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
RESULTS_FILE = os.path.join(RESULTS_DIR, "car_questions.json")

# テスト実行中に収集した結果を保持するリスト
_results: list[dict] = []


@pytest.fixture(scope="session", autouse=True)
def save_results_to_file():
    """全テスト終了後に結果をJSONファイルへ書き出す。"""
    yield
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(_results, f, ensure_ascii=False, indent=2)
    print(f"\n結果を保存しました: {RESULTS_FILE}")


def _ask_with_mock(question: str, mock_answer: str) -> str:
    """car_agent._car_agent をモックして ask_car_expert を呼び出す。"""
    from agents import car_agent

    mock_response = MagicMock()
    mock_response.__str__ = MagicMock(return_value=mock_answer)

    with patch.object(car_agent, "_car_agent", return_value=mock_response):
        answer = car_agent.ask_car_expert(question=question)

    return answer


# ────────────────────────────────────────────
# テスト 1: ハイブリッド車の仕組み
# ────────────────────────────────────────────
def test_q1_hybrid_car_mechanism():
    question = "ハイブリッド車の仕組みを教えてください。"
    mock_answer = (
        "ハイブリッド車はガソリンエンジンと電気モーターを組み合わせた自動車です。"
        "低速走行時は電気モーターのみで駆動し、高速走行時や加速時はエンジンと"
        "モーターを併用します。減速時のブレーキエネルギーを回生してバッテリーを充電するため、"
        "燃費が従来のガソリン車と比べて大幅に向上します。"
    )

    answer = _ask_with_mock(question, mock_answer)

    _results.append({"test": "test_q1_hybrid_car_mechanism", "question": question, "answer": answer})
    assert isinstance(answer, str)
    assert len(answer) > 0


# ────────────────────────────────────────────
# テスト 2: エンジンオイルの交換時期
# ────────────────────────────────────────────
def test_q2_engine_oil_change_interval():
    question = "エンジンオイルはどのくらいの頻度で交換すればよいですか？"
    mock_answer = (
        "一般的なガソリン車では、通常走行なら5,000〜10,000kmごと、または半年〜1年に1回の交換が目安です。"
        "ターボ車や過酷な条件で使用する場合は3,000〜5,000kmごとの交換を推奨します。"
        "最近の全合成オイルを使用する車では15,000kmまで延長できる場合もありますが、"
        "メーカーの指定に従うのが最も確実です。"
    )

    answer = _ask_with_mock(question, mock_answer)

    _results.append({"test": "test_q2_engine_oil_change_interval", "question": question, "answer": answer})
    assert isinstance(answer, str)
    assert len(answer) > 0


# ────────────────────────────────────────────
# テスト 3: EV（電気自動車）の航続距離
# ────────────────────────────────────────────
def test_q3_ev_driving_range():
    question = "最新の電気自動車（EV）の航続距離はどのくらいですか？"
    mock_answer = (
        "2024〜2025年モデルの主要EVの航続距離は、テスラModel 3 Long Rangeが約629km、"
        "BYD Seal が約570km、日産リーフe+が約340km（WLTCモード）です。"
        "バッテリー技術の進化により、高級モデルでは700km超も登場しています。"
        "ただし実走行では気温・速度・エアコン使用により2〜3割程度短くなる場合があります。"
    )

    answer = _ask_with_mock(question, mock_answer)

    _results.append({"test": "test_q3_ev_driving_range", "question": question, "answer": answer})
    assert isinstance(answer, str)
    assert len(answer) > 0
