#!/usr/bin/env bash
# ============================================================
# Strands Agent Web UI 起動スクリプト
# 使い方: bash start_web.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 仮想環境の有効化
VENV_PATH="${HOME}/.venv/strands-agent"
if [ -f "${VENV_PATH}/bin/activate" ]; then
  source "${VENV_PATH}/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
  source ".venv/bin/activate"
else
  echo "[ERROR] 仮想環境が見つかりません。"
  echo "  以下のコマンドで作成してください:"
  echo "    python3 -m venv ~/.venv/strands-agent"
  echo "    source ~/.venv/strands-agent/bin/activate"
  echo "    pip install -r requirements.txt"
  exit 1
fi

# .env の存在確認
if [ ! -f ".env" ]; then
  echo "[ERROR] .env ファイルが見つかりません。"
  echo "  cp .env.example .env でコピーして設定してください。"
  exit 1
fi

echo ""
echo "=================================================="
echo "  Strands Agent Web UI"
echo "=================================================="
echo "  URL: http://localhost:8000"
echo "  終了: Ctrl+C"
echo "=================================================="
echo ""

uvicorn server:app --host 0.0.0.0 --port 8000 --reload
