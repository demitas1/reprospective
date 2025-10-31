# Phase 2 実装計画: 監視対象ディレクトリのDB管理とWeb UI

## 概要

FileSystemWatcherの監視対象ディレクトリ設定をPostgreSQLに保存し、API経由で動的に更新可能にする。
初期段階ではcURL、次の段階でReact 19 + ViteによるWeb UIを実装する。

## 実装フェーズ

### Phase 2.1: API Gateway & Database Schema（curl対応）

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

### Phase 2.2: Web UI（React 19 + Vite）

#### 1. Web UI サービス

**技術スタック:**
- **フロントエンド**: React 19
- **ビルドツール**: Vite
- **UI ライブラリ**:
  - Tailwind CSS（スタイリング）
  - Shadcn/ui（コンポーネント）
- **状態管理**: React Query (TanStack Query)
- **HTTP クライアント**: Axios

**ディレクトリ構成:**

```
services/web-ui/
├── Dockerfile
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── index.html
├── public/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   └── directories.ts         # API クライアント
│   ├── components/
│   │   ├── ui/                     # Shadcn/ui コンポーネント
│   │   ├── DirectoryList.tsx      # ディレクトリ一覧
│   │   ├── DirectoryCard.tsx      # ディレクトリカード
│   │   ├── AddDirectoryForm.tsx   # 追加フォーム
│   │   └── EditDirectoryModal.tsx # 編集モーダル
│   ├── hooks/
│   │   └── useDirectories.ts      # カスタムフック
│   ├── types/
│   │   └── directory.ts           # 型定義
│   └── styles/
│       └── globals.css
├── nginx.conf                      # Nginx設定（本番用）
└── README.md
```

**docker-compose.yml への追加:**

```yaml
services:
  web-ui:
    build: ./services/web-ui
    container_name: reprospective-web
    restart: unless-stopped
    environment:
      VITE_API_URL: http://localhost:${API_GATEWAY_PORT:-8000}
    ports:
      - "${WEB_UI_PORT:-3000}:80"
    depends_on:
      - api-gateway
    networks:
      - reprospective-network
```

#### 2. 主要画面設計

**ディレクトリ管理画面:**

```
┌────────────────────────────────────────────────────────────┐
│ Reprospective - ファイルシステム監視設定                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ 監視対象ディレクトリ                    [+ 新規追加]      │
│                                                            │
│ ┌────────────────────────────────────────────────────┐    │
│ │ 📁 /home/user/projects                   [ON]  [⋮] │    │
│ │ プロジェクト                                        │    │
│ │ 開発プロジェクト用                                  │    │
│ │ 最終更新: 2025-10-26 16:00                         │    │
│ └────────────────────────────────────────────────────┘    │
│                                                            │
│ ┌────────────────────────────────────────────────────┐    │
│ │ 📁 /home/user/Documents                 [OFF] [⋮] │    │
│ │ ドキュメント                                        │    │
│ │ 一時的に無効化中                                    │    │
│ │ 最終更新: 2025-10-25 12:00                         │    │
│ └────────────────────────────────────────────────────┘    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**主要機能:**
- ディレクトリ一覧表示（リアルタイム更新）
- ON/OFFトグルスイッチ
- 新規追加フォーム
- 編集・削除機能
- フィルタリング（有効/無効）
- 検索機能

#### 3. React Query による状態管理

```typescript
// src/hooks/useDirectories.ts
export const useDirectories = () => {
  return useQuery({
    queryKey: ['directories'],
    queryFn: fetchDirectories,
    refetchInterval: 30000, // 30秒ごとに再取得
  });
};

export const useAddDirectory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: addDirectory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['directories'] });
    },
  });
};

export const useToggleDirectory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: toggleDirectory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['directories'] });
    },
  });
};
```

---

## 実装順序

### ステップ1: データベーススキーマ拡張
- [ ] `services/database/init/02_add_monitored_directories.sql` 作成
- [ ] マイグレーションスクリプト実行確認

### ステップ2: API Gateway 基盤構築
- [ ] `services/api-gateway/` ディレクトリ作成
- [ ] Dockerfile、requirements.txt 作成
- [ ] FastAPI アプリケーション基本構造
- [ ] PostgreSQL接続設定
- [ ] ヘルスチェックエンドポイント

### ステップ3: ディレクトリ管理API実装
- [ ] Pydantic モデル定義
- [ ] CRUD エンドポイント実装
- [ ] バリデーション実装
- [ ] エラーハンドリング

### ステップ4: docker-compose 統合
- [ ] api-gateway サービス追加
- [ ] 環境変数設定
- [ ] ネットワーク設定
- [ ] ヘルスチェック設定

### ステップ5: curl での動作確認
- [ ] 各エンドポイントのテスト
- [ ] エラーケースの確認
- [ ] ドキュメント作成

### ステップ6: host-agent 設定同期機能
- [ ] `common/config_sync.py` 実装
- [ ] YAML→DB 移行ロジック
- [ ] 定期同期ロジック
- [ ] フォールバック機能
- [ ] FileSystemWatcher への統合

### ステップ7: Web UI 基盤構築
- [ ] `services/web-ui/` ディレクトリ作成
- [ ] Vite + React 19 セットアップ
- [ ] Tailwind CSS セットアップ
- [ ] Shadcn/ui インストール
- [ ] ルーティング設定

### ステップ8: Web UI API クライアント
- [ ] Axios 設定
- [ ] API クライアント実装
- [ ] React Query セットアップ
- [ ] カスタムフック実装

### ステップ9: Web UI コンポーネント実装
- [ ] DirectoryList コンポーネント
- [ ] DirectoryCard コンポーネント
- [ ] AddDirectoryForm コンポーネント
- [ ] EditDirectoryModal コンポーネント
- [ ] トグルスイッチコンポーネント

### ステップ10: Web UI Docker化
- [ ] Dockerfile 作成（マルチステージビルド）
- [ ] nginx 設定
- [ ] docker-compose 統合

### ステップ11: 統合テスト
- [ ] エンドツーエンドテスト
- [ ] パフォーマンステスト
- [ ] エラーハンドリングテスト

---

## 技術的考慮事項

### セキュリティ
- [ ] API 認証・認可（Phase 2.3で実装予定）
- [ ] CORS 設定
- [ ] パス検証（ディレクトリトラバーサル対策）
- [ ] 入力サニタイゼーション

### パフォーマンス
- [ ] PostgreSQL インデックス最適化
- [ ] API レスポンスキャッシュ
- [ ] Web UI コンポーネント最適化
- [ ] バンドルサイズ最適化

### 可用性
- [ ] データベース接続エラーハンドリング
- [ ] API エラーハンドリング
- [ ] フォールバック機能
- [ ] ログ記録

### 保守性
- [ ] API ドキュメント（OpenAPI/Swagger）
- [ ] コンポーネントドキュメント（Storybook検討）
- [ ] ユニットテスト
- [ ] E2Eテスト（Playwright検討）

---

## 除外項目（YAMLで管理継続）

以下の設定は引き続き `config.yaml` で管理：
- `exclude_patterns`: 除外パターン（正規表現）
- `symlinks.follow`: シンボリックリンク追跡設定
- `buffer.max_events`: バッファ最大イベント数
- `buffer.flush_interval`: フラッシュ間隔

**理由:**
- 頻繁に変更しない設定
- ホスト環境固有の設定
- YAMLでの管理が適切

---

## マイルストーン

### Phase 2.1 完了条件
- ✅ PostgreSQLに monitored_directories テーブル作成
- ✅ API Gateway でディレクトリCRUD操作可能
- ✅ curl でディレクトリ追加・更新・削除が可能
- ✅ host-agent が DB から設定を取得して動的に監視対象を変更
- ✅ YAML→DB 移行が正常に動作

### Phase 2.2 完了条件
- ✅ Web UI でディレクトリ一覧表示
- ✅ Web UI でディレクトリ追加・編集・削除
- ✅ Web UI でON/OFF切り替え
- ✅ リアルタイムで設定変更が反映
- ✅ レスポンシブデザイン

---

## 想定される課題と対策

### 課題1: host-agentとPostgreSQLの接続
**対策:**
- asyncpg での非同期接続
- 接続プール管理
- 再接続ロジック
- フォールバック機能

### 課題2: 設定変更の即時反映
**対策:**
- 定期ポーリング（60秒間隔）
- 将来的にWebSocket/SSE検討

### 課題3: マルチホスト対応
**対策:**
- host_id カラム追加検討（Phase 3）
- ホストごとの設定管理

### 課題4: パス検証
**対策:**
- 絶対パス検証
- 存在確認（オプション）
- セキュリティチェック

---

## 次のステップ

Phase 2.1（API Gateway）の実装から開始することを推奨します。

実装準備完了後、以下の順で進めます：
1. データベーススキーマ拡張
2. API Gateway 基盤構築
3. curl での動作確認
4. host-agent 統合
5. Web UI 実装

各ステップ完了後、動作確認とドキュメント更新を行います。
