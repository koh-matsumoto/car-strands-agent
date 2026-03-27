# Strands Agent

[Strands Agents SDK](https://strandsagents.com/) をベースにしたマルチエージェントシステム。
親エージェントが複数の専門子エージェントをツールとして呼び出す **Agent as a Tool** パターンを実装している。

## アーキテクチャ

```
親エージェント (main_multi.py)
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
│   └── tracing.py             # OTEL トレーシング設定
├── db/
│   └── setup_car_db.py        # カタログ初期データ投入（15車種）
├── tests/
│   ├── results/
│   │   └── car_questions.json # テスト結果（自動生成）
│   └── test_car_questions.py  # 自動車質問テスト（3件）
├── docker-compose.yml         # Langfuse + postgres-memory
├── main.py                    # 起動: シンプルエージェント
├── main_multi.py              # 起動: マルチエージェント
├── pytest.ini
├── requirements.txt
├── .env.example
└── README.md
```

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

#### 起動確認

すべてのコンテナが `Up` または `healthy` になっていることを確認する。

```bash
docker compose ps
```

期待する出力（STATUS 列）：

| コンテナ名 | 役割 | ポート | 期待するSTATUS |
|---|---|---|---|
| langfuse-web | Langfuse UI | 3000 | Up (healthy) |
| langfuse-worker | バックグラウンド処理 | 3030 | Up |
| postgres | Langfuse 用DB | 5432 | Up (healthy) |
| clickhouse | イベント分析 | 8123 | Up (healthy) |
| redis | キャッシュ | 6379 | Up (healthy) |
| minio | S3互換ストレージ | 9090 | Up (healthy) |
| postgres-memory | pgvector 長期記憶用DB | 5433 | Up (healthy) |

起動直後は `starting` と表示される場合がある。数十秒待ってから再確認する。

```bash
# ログを確認する場合
docker compose logs -f langfuse-web
docker compose logs -f postgres-memory
```

---

### Step 3. Langfuse の初期設定

#### 3-1. アカウント作成

1. ブラウザで `http://localhost:3000` を開く
2. **Sign up** をクリックしてアカウントを作成する（メール・パスワードは任意）
3. 組織名・プロジェクト名を入力して作成する

#### 3-2. API キーの発行

1. Langfuse UI 左メニュー **Settings** → **API Keys** を開く
2. **Create new API key** をクリック
3. 表示された `Public Key`（`pk-lf-...`）と `Secret Key`（`sk-lf-...`）をコピーしておく

---

### Step 4. 環境変数の設定

```bash
cp .env.example .env
```

`.env` を編集して以下の項目を設定する：

```env
# ── LLMプロバイダー ──────────────────────────────
LLM_PROVIDER=anthropic           # bedrock | anthropic | openai | litellm | ollama
LLM_MODEL_ID=claude-haiku-4-5-20251001

# ── Anthropic（LLM_PROVIDER=anthropic の場合） ───
ANTHROPIC_API_KEY=sk-ant-...     # https://console.anthropic.com でAPIキーを発行

# ── Langfuse（Step 3-2 で発行したキーを設定） ────
LANGFUSE_ENABLED=true
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# ── 長期記憶DB（デフォルトのまま変更不要） ───────
MEMORY_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/agent_memory
```

#### Langfuse 接続確認

```bash
python -c "
from dotenv import load_dotenv; load_dotenv()
import os
from langfuse import Langfuse
lf = Langfuse(
    public_key=os.environ['LANGFUSE_PUBLIC_KEY'],
    secret_key=os.environ['LANGFUSE_SECRET_KEY'],
    host=os.getenv('LANGFUSE_HOST', 'http://localhost:3000'),
)
print('接続OK:', lf.auth_check())
"
```

`接続OK: True` と表示されれば成功。

#### 長期記憶DB（pgvector）接続確認

```bash
python -c "
from dotenv import load_dotenv; load_dotenv()
import os, psycopg2
conn = psycopg2.connect(os.getenv('MEMORY_DATABASE_URL'))
cur = conn.cursor()
cur.execute('SELECT version()')
print('接続OK:', cur.fetchone()[0][:40])
conn.close()
"
```

---

### Step 5. カタログDBの初期化

車種データ（トヨタ・ホンダ・スバル各5車種、計15車種）をDBに投入する。

```bash
python db/setup_car_db.py
```

期待する出力：
```
  投入: トヨタ プリウス
  投入: トヨタ ハリアー
  ...
  投入: スバル WRX S4

✓ 15 車種のデータを投入しました。
```

#### カタログDB確認

```bash
python -c "
from dotenv import load_dotenv; load_dotenv()
import os, psycopg2
conn = psycopg2.connect(os.getenv('MEMORY_DATABASE_URL'))
cur = conn.cursor()
cur.execute('SELECT manufacturer, model_name FROM car_catalog ORDER BY manufacturer, model_name')
for row in cur.fetchall():
    print(f'  {row[0]} {row[1]}')
conn.close()
"
```

---

### Step 6. エージェントの起動

#### マルチエージェント（通常の使い方）

```bash
python main_multi.py
```

```
=== Multi-Agent (親 + 自動車専門エージェント) ===
自動車に関する質問は自動的に専門エージェントへ委譲されます。
終了するには 'exit' または 'quit' を入力してください。

You: プリウスの燃費を教えて
Agent: プリウス（2023年モデル）のWLTC燃費は 28.6 km/L です...

You: 300万円以内で買えるSUVは？
Agent: カタログDBを検索します...

You: ハイブリッド車とEVの違いは？
Agent: ハイブリッド車はガソリンエンジンと電気モーターを...
```

終了するには `exit` または `quit` を入力する。

#### シンプルエージェント（ツールなし・汎用）

```bash
python main.py
```

---

### Step 7. Langfuse でトレースを確認

1. ブラウザで `http://localhost:3000` を開く
2. 左メニューの **Tracing** → **Traces** を開く
3. エージェントとやり取りするたびにトレースが追加される

トレース画面で確認できる内容：
- どのエージェントがどのツールを呼んだか
- LLM へのリクエスト・レスポンス内容とトークン数
- 各ステップの処理時間

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

次回のエージェント起動時に新しいプロンプトが自動的に反映される。Langfuse が未接続の場合はコード内のデフォルト値にフォールバックする。

---

## LLMの設定

`.env` の `LLM_PROVIDER` を変更するだけでプロバイダーを切り替えられる。

| `LLM_PROVIDER` | 説明 | 必要な設定 |
|---|---|---|
| `bedrock`（デフォルト）| Amazon Bedrock | `AWS_REGION`、AWS認証情報 |
| `anthropic` | Anthropic API | `ANTHROPIC_API_KEY` |
| `openai` | OpenAI / OpenAI互換エンドポイント | `OPENAI_API_KEY`、`OPENAI_BASE_URL`（任意） |
| `litellm` | 任意のOpenAI互換サーバー（vLLM、LM Studio等） | `LLM_API_BASE`、`LLM_API_KEY` |
| `ollama` | ローカルOllamaサーバー | `OLLAMA_HOST`、`OLLAMA_MODEL` |

---

## テスト

```bash
python -m pytest tests/ -v
```

- テスト結果（Q&A）: `tests/results/car_questions.json`
- HTMLレポート: `/tmp/strands-test-results/report.html`
- JUnit XML: `/tmp/strands-test-results/junit.xml`

---

## 長期記憶について

- **実装**: pgvector（PostgreSQL拡張）
- **埋め込みモデル**: `all-MiniLM-L6-v2`（384次元、ローカル実行・APIキー不要）
- **インデックス**: HNSW（コサイン類似度）
- **保存対象**: 各 Q&A のペア（質問 + 回答先頭200文字）
- **検索**: 意味的類似度 Top-3 を取得してプロンプトに付加

`car-agent` と `parent-agent` がそれぞれ独立した長期記憶を持つ。
セッションをまたいで過去の会話を参照できるため、繰り返し使うほど文脈を踏まえた回答になる。

---

## トラブルシューティング

**Docker コンテナが起動しない**
```bash
docker compose down -v   # ボリュームごと削除してリセット
docker compose up -d
```

**`vector type not found` エラー**
postgres-memory コンテナが `healthy` になる前に接続している可能性がある。
`docker compose ps` でステータスを確認してから再実行する。

**`credit balance too low` エラー**
Anthropic API の残高不足。`https://console.anthropic.com` でクレジットを追加する。

**Langfuse にトレースが届かない**
`.env` の `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` を確認する。
Step 4 の接続確認コマンドで `True` が返るか試す。
