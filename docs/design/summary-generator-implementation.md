# アクティビティサマリー生成機能 実装計画

## 関連ドキュメント
- [要求仕様書](./summary-generator-requirements.md)
- [設計書](./summary-generator-design.md)
- **[実装計画](./summary-generator-implementation.md)** ← 本ドキュメント

---

## 実装フェーズ

### Phase 1: 基盤実装（2-3日）

**目標:** ログ前処理とヒント管理の実装

**タスク:**
- [ ] Log Processor実装
  - ログファイル読み込み（desktop_activity, input_activity, file_change）
  - 基本フィルタリング（短時間セッション除外）
  - **無活動期間除外（新規）**
    - 入力セッションとの時間的重複計算
    - 実活動時間の算出
    - 統計情報の記録
  - セッション統合ロジック
  - デバッグログ記録
- [ ] Activity Hint Manager実装
  - プロジェクトヒント検索
  - カテゴリー推定
  - 匿名化処理
  - LLMコンテキスト情報生成
- [ ] 設定ファイル定義
  - `activity_hints.yaml`
  - `summary_generator.yaml`（idle_filtering設定追加）
- [ ] ユニットテスト作成
  - 無活動期間除外ロジックのテスト
  - 時間的重複計算のテスト

**成果物:**
- `app/summary_generator/log_processor.py`
- `app/summary_generator/activity_hint_manager.py`
- `config/activity_hints.yaml`
- `config/summary_generator.yaml`
- テストコード

---

### Phase 2: LLM統合（2-3日）

**目標:** LLMカテゴライザの実装と精度評価

**タスク:**
- [ ] LLM Service実装
  - OpenAI API連携
  - プロンプトエンジニアリング
  - バッチ処理
  - エラーハンドリング（リトライ、部分的成功の検出）
- [ ] プロンプト最適化
  - 匿名化対応プロンプト設計
  - Few-shot learning
- [ ] カテゴライズ精度評価
  - テストデータでの検証
  - モデル比較（GPT-5 vs GPT-5-mini vs GPT-4 Turbo）

**成果物:**
- `app/summary_generator/llm_service.py`
- プロンプトテンプレート
- 精度評価レポート

---

### Phase 3: フィルタ・集約（1-2日）

**目標:** センシティブコンテンツフィルタと集約処理の実装

**タスク:**
- [ ] Sensitive Content Filter実装
  - パターンマッチング
  - 除外・匿名化処理
  - デバッグログ記録
- [ ] Aggregator & Ranker実装
  - カテゴリー別集約
  - ランク付けロジック
  - 時間帯別分布計算
- [ ] JSON Output実装
  - PostgreSQL保存（UPSERT）
  - ファイル出力
  - メタデータ生成

**成果物:**
- `app/summary_generator/sensitive_filter.py`
- `app/summary_generator/aggregator.py`
- `app/summary_generator/json_output.py`

---

### Phase 4: 統合テスト・調整（1-2日）

**目標:** エンドツーエンドテスト、パフォーマンス最適化

**タスク:**
- [ ] 統合テスト
  - 実データでのテスト（logs/2025-11-06/）
  - 各コンポーネントの連携確認
  - エラーケースのテスト
- [ ] パフォーマンス最適化
  - 処理時間計測
  - バッチサイズ調整
  - メモリ使用量の最適化
- [ ] ドキュメント整備
  - README作成
  - API仕様書更新
  - 運用マニュアル作成

**成果物:**
- 統合テストスイート
- パフォーマンスレポート
- ドキュメント

---

**総推定工数:** 6-10日

---

## Dockerコンテナ構成

### docker-compose.yml への追加

```yaml
  ai-analyzer:
    build: ./services/ai-analyzer
    container_name: reprospective-analyzer
    restart: unless-stopped

    environment:
      # データベース接続
      DATABASE_URL: postgresql://${POSTGRES_USER:-reprospective_user}:${POSTGRES_PASSWORD:-change_this_password}@database:5432/${POSTGRES_DB:-reprospective}

      # LLM設定
      LLM_PROVIDER: ${LLM_PROVIDER:-openai}  # openai | ollama | anthropic
      LLM_MODEL: ${LLM_MODEL:-gpt-5}  # gpt-5, gpt-5-mini, gpt-5-nano, gpt-4-turbo, gpt-4o
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}  # 必須（OpenAI使用時）
      OLLAMA_HOST: ${OLLAMA_HOST:-http://host.docker.internal:11434}  # ホストのOllama（オプション）
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}  # オプション

      # デバッグ設定
      ENABLE_DEBUG_LOGGING: ${ENABLE_DEBUG_LOGGING:-true}
      LOG_ORIGINAL_CONTENT: ${LOG_ORIGINAL_CONTENT:-true}  # 実験目的のため有効

    volumes:
      # ログファイルへのアクセス（読み取り専用）
      - ./logs:/app/logs:ro
      # 設定ファイル
      - ./services/ai-analyzer/config:/app/config:ro
      # 出力先（activity_summary.json、debug logs）
      - ./logs:/app/output:rw

    depends_on:
      database:
        condition: service_healthy

    networks:
      - reprospective-network

    # リソース制限（LLM処理は重い）
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

---

## ディレクトリ構造

```
reprospective/
└── services/
    └── ai-analyzer/
        ├── Dockerfile
        ├── requirements.txt
        ├── config/
        │   ├── activity_hints.yaml
        │   └── summary_generator.yaml
        ├── app/
        │   ├── __init__.py
        │   ├── main.py
        │   ├── summary_generator/
        │   │   ├── __init__.py
        │   │   ├── log_processor.py
        │   │   ├── activity_hint_manager.py
        │   │   ├── sensitive_filter.py
        │   │   ├── llm_service.py
        │   │   ├── aggregator.py
        │   │   └── json_output.py
        │   └── utils/
        │       ├── logger.py
        │       └── config_loader.py
        └── tests/
            ├── test_log_processor.py
            ├── test_activity_hint_manager.py
            ├── test_sensitive_filter.py
            ├── test_llm_service.py
            ├── test_aggregator.py
            └── test_integration.py
```

---

## Dockerfile

```dockerfile
# services/ai-analyzer/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 依存パッケージインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコピー
COPY app/ ./app/
COPY config/ ./config/

# 非rootユーザーで実行
RUN useradd -m -u 1000 analyzer && chown -R analyzer:analyzer /app
USER analyzer

# デフォルトコマンド（CLI実行）
CMD ["python", "-m", "app.main", "--help"]
```

---

## requirements.txt

```txt
# LLM連携
openai>=1.0.0
ollama>=0.1.0  # オプション
anthropic>=0.5.0  # オプション

# データ処理
pyyaml>=6.0
python-dateutil>=2.8.0
pandas>=2.0.0  # オプション

# データベース
psycopg2-binary>=2.9.0
asyncpg>=0.29.0

# タスクキュー（オプション）
celery>=5.0.0
redis>=4.0.0

# ユーティリティ
python-dotenv>=1.0.0
```

---

## テスト戦略

### ユニットテスト

**対象:**
- Log Processor:
  - セッション統合ロジック
  - **無活動期間除外ロジック（新規）**
  - 時間的重複計算
  - 実活動時間の算出
- Activity Hint Manager: プロジェクト検索、匿名化処理
- Sensitive Content Filter: パターンマッチング
- Aggregator: 時間計算、ランク付け

**テストケース例（無活動期間除外）:**
```python
def test_idle_filter_full_overlap():
    """デスクトップセッションと入力セッションが完全に重複"""
    desktop = Session(start=1000, end=2000)  # 1000秒
    input_sessions = [Session(start=1000, end=2000)]  # 1000秒
    active_time = calculate_active_time(desktop, input_sessions)
    assert active_time == 1000

def test_idle_filter_partial_overlap():
    """部分的な重複"""
    desktop = Session(start=1000, end=3000)  # 2000秒
    input_sessions = [
        Session(start=1000, end=1500),  # 500秒
        Session(start=2500, end=2800)   # 300秒
    ]
    active_time = calculate_active_time(desktop, input_sessions)
    assert active_time == 800

def test_idle_filter_no_overlap():
    """重複なし → 除外"""
    desktop = Session(start=1000, end=2000)
    input_sessions = [Session(start=3000, end=4000)]
    active_time = calculate_active_time(desktop, input_sessions)
    assert active_time == 0
```

**ツール:**
- pytest
- pytest-cov（カバレッジ）

**実行:**
```bash
cd services/ai-analyzer
pytest tests/ -v --cov=app/summary_generator
```

---

### 統合テスト

**対象:**
- 実際のログファイルを使用したエンドツーエンドテスト
- 複数日分のデータでのテスト
- 無活動期間除外機能の実データでの動作確認
- LLMのモック使用でテスト高速化

**テストデータ:**
- `logs/2025-11-06/desktop_activity_sessions.txt`
- `logs/2025-11-06/input_activity_sessions.txt`（新規）
- `logs/2025-11-06/file_change_events.txt`

**テストシナリオ:**
1. **無活動期間除外あり**: 入力ログが存在する場合
   - 実活動時間の計算が正しいか
   - 統計情報（idle_filtering_stats）が記録されるか
2. **無活動期間除外なし**: 入力ログが存在しない場合
   - フォールバック動作が正しいか
   - 警告が記録されるか
3. **--no-idle-filter オプション**: 除外を無効化した場合
   - 処理時間の比較
   - 結果の差分確認

**実行:**
```bash
cd services/ai-analyzer
pytest tests/test_integration.py -v
```

---

### 評価指標

**カテゴライズ精度:**
- 手動分類との一致率 > 90%
- テストデータ: 100セッション、手動で正解ラベル付与

**処理時間:**
- 1日分のログ（376セッション）< 60秒

**LLM呼び出し回数:**
- 最小化（バッチ処理で19回以下）

---

## API Gateway統合

### 新規エンドポイント

#### POST /api/v1/summary/generate

**実装:**
```python
# services/api-gateway/app/routers/summary.py
from fastapi import APIRouter, BackgroundTasks
import uuid

router = APIRouter(prefix="/api/v1/summary", tags=["summary"])

@router.post("/generate")
async def generate_summary(
    request: GenerateSummaryRequest,
    background_tasks: BackgroundTasks
):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(run_summary_generator, task_id, request.date, request.model)
    return {"task_id": task_id, "status": "started"}
```

#### GET /api/v1/summary/status/{task_id}

**実装:**
```python
@router.get("/status/{task_id}")
async def get_summary_status(task_id: str):
    # Redis等からタスク状態を取得
    status = get_task_status(task_id)
    return status
```

#### GET /api/v1/summary

**実装:**
```python
@router.get("")
async def get_summary(date: str):
    # PostgreSQLから取得
    summary = await db.fetch_one(
        "SELECT summary_json FROM activity_summaries WHERE date = $1",
        date
    )
    return summary["summary_json"]
```

---

### タスクキュー実装

**Celery使用例:**
```python
# services/ai-analyzer/app/tasks.py
from celery import Celery

app = Celery('summary_generator', broker='redis://redis:6379/0')

@app.task
def generate_summary_task(task_id: str, date: str, model: str):
    # サマリー生成処理
    result = run_summary_generator(date, model)
    # Redisに結果を保存
    save_task_result(task_id, result)
```

---

## Web UI統合

### 新規ページ

#### サマリーページ (`/summary`)

**コンポーネント:**
```typescript
// services/web-ui/src/pages/SummaryPage.tsx
export function SummaryPage() {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const { data: summary, isLoading } = useSummary(selectedDate);

  return (
    <div>
      <DatePicker value={selectedDate} onChange={setSelectedDate} />
      {isLoading ? <LoadingSpinner /> : <SummaryView summary={summary} />}
    </div>
  );
}
```

**API連携:**
```typescript
// services/web-ui/src/hooks/useSummary.ts
export function useSummary(date: Date) {
  return useQuery({
    queryKey: ['summary', formatDate(date)],
    queryFn: () => fetchSummary(formatDate(date)),
  });
}
```

---

## 運用

### デプロイ手順

```bash
# 1. 環境変数設定
cp .env.example .env
vim .env  # OPENAI_API_KEY等を設定

# 2. コンテナビルド・起動
docker compose build ai-analyzer
docker compose up -d ai-analyzer

# 3. 動作確認
docker compose logs -f ai-analyzer
```

### サマリー生成実行

```bash
# オンデマンド実行（Web UIからボタンクリック）
# → POST /api/v1/summary/generate が呼ばれる

# 手動実行（CLI）
docker compose exec ai-analyzer python -m app.main --date 2025-11-06
```

### ログ確認

```bash
# 入力データ確認
cat logs/2025-11-06/desktop_activity_sessions.txt
cat logs/2025-11-06/input_activity_sessions.txt  # 無活動期間除外用
cat logs/2025-11-06/file_change_events.txt

# 処理ログ（無活動期間除外の詳細も含む）
cat logs/2025-11-06/debug/processing_log.jsonl | jq '.'

# 匿名化ログ
cat logs/2025-11-06/debug/anonymization_log.jsonl | jq '.'

# フィルタリングログ
cat logs/2025-11-06/debug/filtering_log.jsonl | jq '.'

# サマリー出力（idle_filtering_stats含む）
cat logs/2025-11-06/activity_summary.json | jq '.metadata.idle_filtering_stats'
cat logs/2025-11-06/activity_summary.json | jq '.'
```

---

## パフォーマンス最適化

### 1. バッチサイズ調整

**現状:** 20セッション/バッチ

**最適化:**
- LLMコンテキスト長制限に応じて動的調整
- GPT-5: 最大50セッション/バッチ
- GPT-5-mini: 最大100セッション/バッチ

### 2. プロンプトキャッシング

**OpenAI機能活用:**
- 固定部分（プロジェクト情報、カテゴリー定義）をキャッシュ
- コスト削減: キャッシュ入力 = 通常の1/10

### 3. ルールベース分類の強化

**第1段階でLLM呼び出しを削減:**
- キーワードマッチングで明確なケースを分類
- LLMは不明なケースのみ使用
- 目標: LLM呼び出し回数を50%削減

---

## 拡張性

### 将来的な機能追加

#### 1. マルチモーダル対応

**実装:**
- スクリーンショット解析（GPT-5 Vision API）
- 音声アクティビティ記録（Whisper API）

#### 2. パターン学習

**実装:**
- ユーザーの分類傾向を学習
- 自動ヒント生成（教師なし学習）

#### 3. リアルタイム分類

**実装:**
- ログ収集と同時にカテゴライズ
- リアルタイムダッシュボード（WebSocket）

#### 4. 協調フィルタリング

**実装:**
- 複数ユーザーのパターン共有（オプトイン）
- プライバシー保護技術（差分プライバシー）

---

## トラブルシューティング

### LLM API呼び出しエラー

**症状:** `LLM API呼び出しが3回失敗しました`

**原因:**
- APIキーが無効
- レート制限超過
- ネットワーク障害

**対処:**
1. `OPENAI_API_KEY`を確認
2. OpenAIダッシュボードでAPI使用状況を確認
3. リトライ間隔を延長（`summary_generator.yaml`）

### 部分的成功エラー

**症状:** `100セッション中50件のみ成功`

**原因:**
- LLMのレスポンスが不正なJSON
- プロンプトが長すぎてコンテキスト長制限超過

**対処:**
1. デバッグログで失敗したバッチを確認
2. バッチサイズを削減（20 → 10）
3. プロンプトを簡略化

---

### 入力ログ不在エラー

**症状:** `入力アクティビティログが見つかりません`

**原因:**
- InputMonitorが起動していない
- ログファイルがまだ生成されていない

**対処:**
1. InputMonitorが起動しているか確認
2. フォールバック動作を確認（無活動期間除外をスキップ）
3. `--no-idle-filter`オプションで実行して動作確認

**影響:**
- 無活動期間除外が行われない
- 活動時間が過大評価される可能性
- メタデータに`idle_filtering_stats.enabled: false`が記録される

---

### 時間削減率が異常に高い

**症状:** `time_reduction_percentage: 95%` など、異常に高い削減率

**原因:**
- 入力ログとデスクトップログの時刻がずれている
- InputMonitorの無操作タイムアウト設定が短すぎる

**対処:**
1. システムクロックの同期を確認（NTP）
2. InputMonitorの`idle_timeout_seconds`設定を確認（デフォルト120秒）
3. デバッグログで時刻のずれを確認

### PostgreSQL接続エラー

**症状:** `could not connect to server`

**原因:**
- PostgreSQLコンテナが起動していない
- `DATABASE_URL`が間違っている

**対処:**
1. `docker compose ps`でコンテナ状態を確認
2. `docker compose logs database`でエラーを確認
3. `DATABASE_URL`を修正

---

## 参考資料

- OpenAI API Documentation: https://platform.openai.com/docs/
- OpenAI Pricing: https://platform.openai.com/docs/pricing
- Celery Documentation: https://docs.celeryq.dev/
- FastAPI BackgroundTasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
- Docker Compose: https://docs.docker.com/compose/
