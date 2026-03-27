# Strands Agent

[Strands Agents SDK](https://strandsagents.com/) をベースにしたマルチエージェントシステム。
親エージェントが複数の専門子エージェントをツールとして呼び出す **Agent as a Tool** パターンを実装している。
ElevenLabs による音声合成（TTS）と、会話履歴を管理できる Web UI を搭載。

## アーキテクチャ

```
親エージェント (parent_agent.py)
├── ask_car_expert      → 自動車全般の質問に回答 + pgvector 長期記憶
└── ask_car_catalog     → カタログDB（トヨタ/ホンダ/スバル 15車種）を検索
                           ├── search_car_catalog   条件絞り込み検索
                           ├── get_car_details      特定車種の詳細取得
                           └── list_all_models      全車種一覧
```

**共通基盤：**
- **短期記憶**: Strands 組み込みの会話履歴（セッション内）
- **長期記憶**: pgvector による意味検索（セッションをまたいで保持）
- **プロンプト管理**: Langfuse Prompt Management（バージョン管理・UI編集）
- **トレーシング**: Langfuse + OpenTelemetry（リクエスト・ツール呼び出しの可視化）
- **TTS**: ElevenLabs API による音声合成・再生
- **Web UI**: FastAPI + セッション履歴管理

## フォルダ構成

```
strands-agent/
├── agents/                    # エージェント定義
│   ├── agent.py               # シンプルエージェント（ツールなし）
│   ├── car_agent.py           # 自動車専門エージェント + 長期記憶
│   ├── car_catalog_agent.py   # カタログDBエージェント（DB検索ツール）
│   └── parent_agent.py        # 親エージェント（2つの子を持つ）
├── core/                      # 共通基盤
│   ├── config.py              # LLMプロバイダー設定・切り替えロジック
│   ├── memory.py              # pgvector 長期記憶
│   ├── prompts.py             # Langfuse プロンプト管理
│   ├── sessions.py            # Web UI セッション管理（sessions.json）
│   ├── tracing.py             # OTEL トレーシング設定
│   └── tts.py                 # ElevenLabs TTS
├── db/
│   └── setup_car_db.py        # カタログ初期データ投入（15車種）
├── static/
│   └── index.html             # Web UI フロントエンド
├── tests/
│   ├── results/
│   │   └── car_questions.json # テスト結果（自動生成）
│   └── test_car_questions.py  # 自動車質問テスト（3件）
├── docker-compose.yml         # Langfuse + postgres-memory
├── main.py                    # CLI起動: シンプルエージェント
├── main_multi.py              # CLI起動: マルチエージェント（TTS付き）
├── server.py                  # Web UI サーバー（FastAPI）
├── start_web.sh               # Web UI 起動スクリプト
├── requirements.txt
├── sessions.json              # Web UIの会話履歴（自動生成）
├── .env.example
└── README.md
```

---

## Web UI の起動（最速手順）

### 前提条件
- 初回セットアップ（下記 Step 1〜5）が完了していること
- Dockerコンテナが起動していること

### 起動コマンド

```bash
bash start_web.sh
```

ブラウザで `http://localhost:8000` を開く。

### start_web.sh でできること

| 処理 | 内容 |
|---|---|
| 仮想環境の自動検出・有効化 | `~/.venv/strands-agent` または `.venv` を自動検出 |
| .env の存在確認 | なければエラーメッセージで案内 |
| サーバー起動 | `uvicorn server:app --reload` でホットリロード有効 |

### Web UI の機能

| 機能 | 説明 |
|---|---|
| サイドバー | 過去の会話一覧（今日・昨日・先週・もっと前でグループ化） |
| 新しいチャット | `+` ボタンで新規セッション作成 |
| 会話履歴の復元 | セッションをクリックすると過去の会話を全件表示 |
| セッション削除 | `×` ボタンで削除 |
| モード切り替え | シンプル / マルチエージェント |
| TTS | エージェントの返答をブラウザで音声再生（ElevenLabs） |
| 自動タイトル | 最初のメッセージからタイトルを自動生成 |
| Markdown表示 | コードブロック・表・箇条書きをレンダリング |

---

## 使い方（初回セットアップから起動まで）

### Step 1. 仮想環境・依存関係のインストール

> **WSL2環境の注意:** Windowsファイルシステム上（`/mnt/c/...`）では仮想環境の作成に制限があるため、Linuxネイティブパスに作成する。

```bash
# 仮想環境を作成して有効化
python3 -m venv ~/.venv/strands-agent
source ~/.venv/strands-agent/bin/activate

# 依存ライブラリをインストール
cd /path/to/strands-agent
pip install -r requirements.txt
```

次回以降の有効化：
```bash
source ~/.venv/strands-agent/bin/activate
```

---

### Step 2. Docker コンテナの起動

```bash
docker compose up -d
```

すべてのコンテナが `Up` または `healthy` になっていることを確認する。

```bash
docker compose ps
```

| コンテナ名 | 役割 | ポート | 期待するSTATUS |
|---|---|---|---|
| langfuse-web | Langfuse UI | 3000 | Up (healthy) |
| langfuse-worker | バックグラウンド処理 | 3030 | Up |
| postgres | Langfuse 用DB | 5432 | Up (healthy) |
| clickhouse | イベント分析 | 8123 | Up (healthy) |
| redis | キャッシュ | 6379 | Up (healthy) |
| minio | S3互換ストレージ | 9090 | Up (healthy) |
| postgres-memory | pgvector 長期記憶用DB | 5433 | Up (healthy) |

---

### Step 3. Langfuse の初期設定

1. ブラウザで `http://localhost:3000` を開く
2. **Sign up** でアカウントを作成する
3. **Settings** → **API Keys** → **Create new API key** でキーを発行する

---

### Step 4. 環境変数の設定

```bash
cp .env.example .env
```

`.env` を編集して以下の項目を設定する：

```env
# ── LLMプロバイダー ──────────────────────────────
LLM_PROVIDER=anthropic
LLM_MODEL_ID=claude-haiku-4-5-20251001

# ── Anthropic API ────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-...

# ── Langfuse ─────────────────────────────────────
LANGFUSE_ENABLED=true
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# ── 長期記憶DB ───────────────────────────────────
MEMORY_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/agent_memory

# ── ElevenLabs TTS ───────────────────────────────
TTS_ENABLED=true
ELEVENLABS_API_KEY=...        # https://elevenlabs.io/app/settings/api-keys
ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb
ELEVENLABS_MODEL_ID=eleven_v3
ELEVENLABS_OUTPUT_FORMAT=mp3_44100_128
ELEVENLABS_SPEED=1.5          # 1.0=標準 / 1.5=1.5倍速 / 2.0=最大
```

---

### Step 5. カタログDBの初期化

```bash
python db/setup_car_db.py
```

---

### Step 6. Web UI を起動する

```bash
bash start_web.sh
```

ブラウザで `http://localhost:8000` を開く。

---

### Step 7. CLI で使う場合（オプション）

```bash
# マルチエージェント（TTS付き）
python main_multi.py

# シンプルエージェント
python main.py
```

---

## ElevenLabs TTS の設定

| 環境変数 | 説明 | デフォルト |
|---|---|---|
| `TTS_ENABLED` | `false` で音声OFF | `true` |
| `ELEVENLABS_API_KEY` | APIキー（必須） | - |
| `ELEVENLABS_VOICE_ID` | ボイスID | `JBFqnCBsd6RMkjVDRZzb`（George） |
| `ELEVENLABS_MODEL_ID` | モデル | `eleven_v3` |
| `ELEVENLABS_OUTPUT_FORMAT` | 音声フォーマット | `mp3_44100_128` |
| `ELEVENLABS_SPEED` | 話速（0.5〜2.0） | `1.0` |

APIキーは [ElevenLabs ダッシュボード](https://elevenlabs.io/app/settings/api-keys) で取得。

---

## LLMプロバイダーの切り替え

`.env` の `LLM_PROVIDER` を変更するだけで切り替えられる。

| `LLM_PROVIDER` | 説明 | 必要な設定 |
|---|---|---|
| `bedrock`（デフォルト）| Amazon Bedrock | `AWS_REGION`、AWS認証情報 |
| `anthropic` | Anthropic API | `ANTHROPIC_API_KEY` |
| `openai` | OpenAI / OpenAI互換 | `OPENAI_API_KEY`、`OPENAI_BASE_URL`（任意） |
| `litellm` | 任意のOpenAI互換サーバー | `LLM_API_BASE`、`LLM_API_KEY` |
| `ollama` | ローカルOllama | `OLLAMA_HOST`、`OLLAMA_MODEL` |

---

## プロンプト管理（Langfuse）

各エージェントのシステムプロンプトは Langfuse UI から編集・バージョン管理できる。

| プロンプト名 | 対象エージェント |
|---|---|
| `simple-agent-system-prompt` | シンプルエージェント |
| `car-agent-system-prompt` | 自動車専門エージェント |
| `car-catalog-agent-system-prompt` | カタログDBエージェント |
| `parent-agent-system-prompt` | 親エージェント |

**編集手順：** Langfuse UI → **Prompt Management** → プロンプト名を選択 → 編集 → `production` ラベルで保存

Langfuse が未接続の場合は `core/prompts.py` 内のデフォルト値にフォールバックする。

---

## テスト

```bash
python -m pytest tests/ -v
```

- テスト結果（Q&A）: `tests/results/car_questions.json`

---

## トラブルシューティング

**Docker コンテナが起動しない**
```bash
docker compose down -v
docker compose up -d
```

**`vector type not found` エラー**
`postgres-memory` コンテナが `healthy` になる前に接続している。`docker compose ps` でステータスを確認してから再実行する。

**`credit balance too low` エラー**
Anthropic API の残高不足。`https://console.anthropic.com` でクレジットを追加する。

**Langfuse にトレースが届かない**
`.env` の `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` を確認する。

**音声が再生されない（Web UI）**
ブラウザの自動再生ポリシーによりブロックされる場合がある。ページを一度クリックしてからメッセージを送ると再生される。

**start_web.sh で仮想環境が見つからないと言われる**
```bash
python3 -m venv ~/.venv/strands-agent
source ~/.venv/strands-agent/bin/activate
pip install -r requirements.txt
```
