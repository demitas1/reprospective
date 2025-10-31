# Phase 2.1 実装計画: API Gateway & host-agent設定同期

**ステータス: ✅ 完了 (2025-10-31)**

## 概要

FileSystemWatcherの監視対象ディレクトリ設定をPostgreSQLに保存し、API経由で動的に更新可能にする。
host-agentはPostgreSQLから設定を取得し、60秒間隔で自動同期する。

## 実装内容

#### 1. データベーススキーマ拡張

**新規テーブル:**

```sql
-- 監視対象ディレクトリテーブル
CREATE TABLE monitored_directories (
    id SERIAL PRIMARY KEY,
    directory_path TEXT UNIQUE NOT NULL,      -- 絶対パス
    enabled BOOLEAN DEFAULT true,              -- 有効/無効
    display_name TEXT,                         -- 表示名（UI用）
    description TEXT,                          -- 説明
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',          -- 追加者
    updated_by TEXT DEFAULT 'system'           -- 最終更新者
);

-- インデックス
CREATE INDEX idx_monitored_directories_enabled ON monitored_directories(enabled);
CREATE INDEX idx_monitored_directories_updated_at ON monitored_directories(updated_at);

-- コメント
COMMENT ON TABLE monitored_directories IS 'ファイルシステム監視対象ディレクトリ';
COMMENT ON COLUMN monitored_directories.enabled IS 'false の場合は監視を一時停止';
```

**マイグレーションスクリプト:** `services/database/init/02_add_monitored_directories.sql`

#### 2. API Gateway サービス

**技術スタック:**
- **言語**: Python 3.11
- **フレームワーク**: FastAPI
- **ライブラリ**:
  - `asyncpg` (PostgreSQL非同期クライアント)
  - `pydantic` (バリデーション)
  - `python-dotenv` (環境変数管理)

**ディレクトリ構成:**

```
services/api-gateway/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPIアプリケーション
│   ├── config.py                  # 設定管理
│   ├── database.py                # DB接続管理
│   ├── models/
│   │   ├── __init__.py
│   │   └── monitored_directory.py # Pydanticモデル
│   └── routers/
│       ├── __init__.py
│       ├── health.py              # ヘルスチェック
│       └── directories.py         # ディレクトリ管理API
└── README.md
```

**API エンドポイント:**

```
GET    /health                          # ヘルスチェック
GET    /api/v1/directories              # 全ディレクトリ取得
GET    /api/v1/directories/{id}         # 特定ディレクトリ取得
POST   /api/v1/directories              # ディレクトリ追加
PUT    /api/v1/directories/{id}         # ディレクトリ更新
DELETE /api/v1/directories/{id}         # ディレクトリ削除
PATCH  /api/v1/directories/{id}/toggle  # 有効/無効切り替え
```

**リクエスト/レスポンス例:**

```json
// POST /api/v1/directories
{
  "directory_path": "/home/user/projects",
  "enabled": true,
  "display_name": "プロジェクト",
  "description": "開発プロジェクト用"
}

// Response
{
  "id": 1,
  "directory_path": "/home/user/projects",
  "enabled": true,
  "display_name": "プロジェクト",
  "description": "開発プロジェクト用",
  "created_at": "2025-10-26T16:00:00+09:00",
  "updated_at": "2025-10-26T16:00:00+09:00",
  "created_by": "api",
  "updated_by": "api"
}
```

**バリデーション:**
- `directory_path`: 絶対パスであること、ディレクトリが存在すること（オプション）
- `display_name`: 最大100文字
- `description`: 最大500文字

**docker-compose.yml への追加:**

```yaml
services:
  api-gateway:
    build: ./services/api-gateway
    container_name: reprospective-api
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://reprospective_user:${POSTGRES_PASSWORD}@database:5432/reprospective
      API_PORT: ${API_GATEWAY_PORT:-8000}
    ports:
      - "${API_GATEWAY_PORT:-8000}:8000"
    depends_on:
      database:
        condition: service_healthy
    networks:
      - reprospective-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
```

#### 3. host-agent の設定同期機能

**実装場所:** `host-agent/common/config_sync.py`

**機能:**
1. 定期的にPostgreSQLから設定を取得（デフォルト60秒間隔）
2. YAMLからの移行処理（初回起動時）
3. フォールバック機能（DB接続失敗時はYAMLを使用）

**動作フロー:**

```
起動時:
1. config.yaml を読み込み
2. PostgreSQLに接続試行
   - 成功 → monitored_directories テーブルを確認
     - テーブルが空 → config.yaml の内容をDBに移行
     - テーブルに既存データ → DBの設定を使用
   - 失敗 → config.yaml の設定を使用（警告ログ出力）

定期同期（60秒ごと）:
1. SELECT * FROM monitored_directories WHERE enabled = true
2. 現在の監視設定と比較
3. 変更があれば:
   - 新規追加されたディレクトリ → Observerを追加
   - 削除されたディレクトリ → Observerを停止・削除
   - enabled=false に変更 → Observerを停止
   - enabled=true に変更 → Observerを開始
```

**設定クラス:**

```python
class DirectoryConfig:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url
        self.sync_interval = 60  # 秒

    async def get_monitored_directories(self) -> List[MonitoredDirectory]:
        """DBから有効な監視対象ディレクトリを取得"""
        pass

    async def migrate_from_yaml(self, yaml_config: dict):
        """YAML設定をDBに移行"""
        pass
```

**host-agent/collectors/filesystem_watcher.py への統合:**

```python
# 設定同期タスクを追加
self.config_sync_task = asyncio.create_task(self._sync_config_loop())

async def _sync_config_loop(self):
    """定期的に設定を同期"""
    while self.is_running:
        try:
            await self._sync_directories()
        except Exception as e:
            logger.error(f"設定同期エラー: {e}")
        await asyncio.sleep(self.sync_interval)
```

#### 4. curl での動作確認例

```bash
# ヘルスチェック
curl http://localhost:8000/health

# 全ディレクトリ取得
curl http://localhost:8000/api/v1/directories

# ディレクトリ追加
curl -X POST http://localhost:8000/api/v1/directories \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/home/user/projects",
    "enabled": true,
    "display_name": "プロジェクト"
  }'

# 有効/無効切り替え
curl -X PATCH http://localhost:8000/api/v1/directories/1/toggle

# ディレクトリ削除
curl -X DELETE http://localhost:8000/api/v1/directories/1
```

---

## 実装完了状況

### ✅ 完了項目

**API Gateway:**
- PostgreSQL `monitored_directories` テーブル作成
- FastAPI RESTful API実装（全CRUD操作）
- Pydantic v2モデル、バリデーション
- Docker Compose統合、ヘルスチェック
- Swagger UI対応 (http://localhost:8800/docs)
- API管理スクリプト5本 (`scripts/api-*.sh`)

**host-agent設定同期:**
- `common/config_sync.py`: PostgreSQL設定同期モジュール
- `collectors/filesystem_watcher_v2.py`: PostgreSQL連携版ウォッチャー
- 動的設定同期（60秒間隔）
- YAML→PostgreSQL自動移行機能
- フォールバック機能（PostgreSQL接続失敗時）
- 非同期処理（asyncpg + asyncio）

**動作確認:**
- PostgreSQL接続・ディレクトリ取得
- API経由でディレクトリ追加→60秒以内に自動監視開始
- API経由でディレクトリ無効化→60秒以内に自動監視停止
- YAML→PostgreSQL自動移行

---

## 次のステップ

**Phase 2.2: Web UI実装**

詳細は `phase2_2_implementation_plan.md` を参照してください。

主要実装内容:
- React 19 + Vite フロントエンド
- 監視ディレクトリ設定UI
- 活動データ可視化（将来）
- AI分析結果表示（将来）

