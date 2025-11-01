#!/bin/bash
# Reprospective コンテナ起動スクリプト
# Docker Composeでサービスを起動し、必要に応じてDB初期化を行う

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "================================"
echo "Reprospective コンテナ起動"
echo "================================"
echo ""

# .envファイルの確認
if [ ! -f .env ]; then
    echo "⚠️  .env ファイルが見つかりません"
    echo "📝 env.example から .env を作成します..."
    cp env.example .env
    echo "✅ .env ファイルを作成しました"
    echo "💡 必要に応じて .env を編集してください"
    echo ""
fi

# Docker Composeの確認
if ! command -v docker &> /dev/null; then
    echo "❌ Dockerがインストールされていません"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Composeがインストールされていません"
    exit 1
fi

# コンテナの起動
echo "🚀 Docker Composeでコンテナを起動します..."
docker compose up -d

# コンテナの起動を待機
echo "⏳ サービスの起動を待機中..."
sleep 5

# ヘルスチェック
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker compose exec -T database pg_isready -U reprospective_user > /dev/null 2>&1; then
        echo "✅ PostgreSQLが起動しました"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "❌ PostgreSQLの起動がタイムアウトしました"
        echo "📋 ログを確認してください: docker compose logs database"
        exit 1
    fi

    sleep 1
done

# スキーマの確認
echo ""
echo "🔍 データベーススキーマを確認中..."
TABLES=$(docker compose exec -T database psql -U reprospective_user -d reprospective -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" 2>/dev/null | tr -d ' ')

if [ "$TABLES" -eq "0" ]; then
    echo "⚠️  テーブルが見つかりません"
    echo "📝 スキーマを初期化します..."
    docker compose exec -T database psql -U reprospective_user -d reprospective < services/database/init/01_init_schema.sql
    echo "✅ スキーマを初期化しました"
else
    echo "✅ スキーマは既に初期化されています (テーブル数: $TABLES)"
fi

# 起動完了
echo ""
echo "================================"
echo "✅ 起動完了"
echo "================================"
echo ""
echo "📊 コンテナステータス:"
docker compose ps
echo ""
echo "💡 接続情報:"
echo "   Web UI:        http://localhost:3333"
echo "   API Gateway:   http://localhost:8800"
echo "   Swagger UI:    http://localhost:8800/docs"
echo "   PostgreSQL:    localhost:6000"
echo ""
echo "🔧 便利なコマンド:"
echo "   docker compose logs web-ui         # Web UIログ表示"
echo "   docker compose logs api-gateway    # API Gatewayログ表示"
echo "   docker compose logs database       # データベースログ表示"
echo "   ./scripts/stop.sh                  # 全コンテナ停止"
echo ""
