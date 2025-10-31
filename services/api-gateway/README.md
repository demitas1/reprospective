# Reprospective API Gateway

監視対象ディレクトリ管理API（FastAPI）

## 概要

FileSystemWatcherの監視対象ディレクトリをPostgreSQLで管理し、REST APIで操作可能にします。

## 技術スタック

- **言語**: Python 3.11
- **フレームワーク**: FastAPI 0.115.0
- **データベースクライアント**: asyncpg (PostgreSQL非同期接続)
- **バリデーション**: Pydantic v2

## APIエンドポイント

### ヘルスチェック

```bash
GET /health              # 簡易ヘルスチェック
GET /health/db           # データベース接続確認
```

### 監視対象ディレクトリ管理

```bash
GET    /api/v1/directories              # 全ディレクトリ取得
GET    /api/v1/directories?enabled_only=true  # 有効なディレクトリのみ取得
GET    /api/v1/directories/{id}         # 特定ディレクトリ取得
POST   /api/v1/directories              # ディレクトリ追加
PUT    /api/v1/directories/{id}         # ディレクトリ更新
DELETE /api/v1/directories/{id}         # ディレクトリ削除
PATCH  /api/v1/directories/{id}/toggle  # 有効/無効切り替え
```

## データモデル

### MonitoredDirectory (取得時)

```json
{
  "id": 1,
  "directory_path": "/home/user/projects",
  "enabled": true,
  "display_name": "プロジェクト",
  "description": "開発プロジェクト用",
  "created_at": "2025-10-31T10:00:00+09:00",
  "updated_at": "2025-10-31T10:00:00+09:00",
  "created_by": "api",
  "updated_by": "api"
}
```

### MonitoredDirectoryCreate (作成時)

```json
{
  "directory_path": "/home/user/projects",
  "enabled": true,
  "display_name": "プロジェクト",
  "description": "開発プロジェクト用",
  "created_by": "api"
}
```

### MonitoredDirectoryUpdate (更新時、部分更新対応)

```json
{
  "directory_path": "/home/user/new_path",  // オプション
  "enabled": false,                          // オプション
  "display_name": "新しい名前",              // オプション
  "description": "新しい説明",                // オプション
  "updated_by": "api"
}
```

## 使い方

### Docker Composeで起動

```bash
# プロジェクトルートから
docker compose up -d api-gateway

# ログ確認
docker compose logs -f api-gateway
```

### APIドキュメント

起動後、以下のURLでSwagger UIにアクセス可能：

- Swagger UI: http://localhost:8800/docs
- ReDoc: http://localhost:8800/redoc

### curlでの操作例

**注意:** デフォルトポートは8800です（env.exampleでは8000）。`.env`ファイルで変更可能。

#### ヘルスチェック

```bash
# API稼働状態確認
curl http://localhost:8800/health

# データベース接続確認
curl http://localhost:8800/health/db
```

#### ディレクトリ一覧取得

```bash
# 全ディレクトリ取得
curl http://localhost:8800/api/v1/directories/

# 有効なディレクトリのみ取得
curl 'http://localhost:8800/api/v1/directories/?enabled_only=true'
```

#### ディレクトリ追加

```bash
curl -X POST http://localhost:8800/api/v1/directories/ \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/home/user/projects",
    "enabled": true,
    "display_name": "プロジェクト",
    "description": "開発プロジェクト用"
  }'
```

#### 特定ディレクトリ取得

```bash
curl http://localhost:8800/api/v1/directories/1
```

#### ディレクトリ更新（部分更新対応）

```bash
curl -X PUT http://localhost:8800/api/v1/directories/1 \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "新しい名前",
    "description": "新しい説明"
  }'
```

#### 有効/無効切り替え

```bash
curl -X PATCH http://localhost:8800/api/v1/directories/1/toggle
```

#### ディレクトリ削除

```bash
curl -X DELETE http://localhost:8800/api/v1/directories/1
```

## 開発

### ローカル開発環境

```bash
cd services/api-gateway

# 仮想環境作成
python -m venv venv
source venv/bin/activate

# 依存パッケージインストール
pip install -r requirements.txt

# 環境変数設定（プロジェクトルートの.envを参照）
export DATABASE_URL="postgresql://reprospective_user:password@localhost:6000/reprospective"

# 開発サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8800
```

### ディレクトリ構成

```
services/api-gateway/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIアプリケーション
│   ├── config.py            # 設定管理
│   ├── database.py          # DB接続管理
│   ├── models/
│   │   ├── __init__.py
│   │   └── monitored_directory.py  # Pydanticモデル
│   └── routers/
│       ├── __init__.py
│       ├── health.py        # ヘルスチェック
│       └── directories.py   # ディレクトリ管理API
└── README.md
```

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `DATABASE_URL` | PostgreSQL接続URL | `postgresql://...` |
| `API_PORT` | APIサーバーポート | `8000` |
| `API_HOST` | APIサーバーホスト | `0.0.0.0` |
| `LOG_LEVEL` | ログレベル | `INFO` |
| `CORS_ORIGINS` | CORS許可オリジン | `http://localhost:3333,...` |

## バリデーション

### directory_path

- 必須フィールド
- 絶対パスであること
- 自動的にパス正規化される

### display_name

- オプション
- 最大100文字

### description

- オプション
- 最大500文字

## エラーレスポンス

```json
{
  "detail": "エラーメッセージ"
}
```

### HTTPステータスコード

- `200 OK`: 成功
- `201 Created`: 作成成功
- `204 No Content`: 削除成功
- `400 Bad Request`: バリデーションエラー
- `404 Not Found`: リソースが見つからない
- `409 Conflict`: ディレクトリパスが重複
- `500 Internal Server Error`: サーバーエラー

## ライセンス

Apache License 2.0
