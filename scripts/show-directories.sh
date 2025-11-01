#!/bin/bash
# 監視ディレクトリ一覧表示スクリプト
# PostgreSQLデータベースから監視対象ディレクトリを取得して表示

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "================================"
echo "監視ディレクトリ一覧"
echo "================================"
echo ""

# .envファイルの確認
if [ ! -f .env ]; then
    echo "❌ .env ファイルが見つかりません"
    exit 1
fi

# 環境変数を読み込み
source .env

# PostgreSQLユーザー名の確認
POSTGRES_USER=${POSTGRES_USER:-reprospective_user}

# データベース接続確認
if ! docker compose exec -T database pg_isready -U "$POSTGRES_USER" > /dev/null 2>&1; then
    echo "❌ PostgreSQLに接続できません"
    echo "💡 コンテナが起動しているか確認してください: docker compose ps"
    exit 1
fi

# ディレクトリ一覧を取得
echo "📊 登録されている監視ディレクトリ:"
echo ""

docker compose exec -T database psql -U "$POSTGRES_USER" -d reprospective -c "
SELECT
    id AS \"ID\",
    directory_path AS \"ディレクトリパス\",
    CASE WHEN enabled THEN '✅ 有効' ELSE '❌ 無効' END AS \"状態\",
    COALESCE(display_name, '-') AS \"表示名\",
    COALESCE(description, '-') AS \"説明\",
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') AS \"作成日時\",
    TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI:SS') AS \"更新日時\"
FROM monitored_directories
ORDER BY id;
"

# 件数を表示
COUNT=$(docker compose exec -T database psql -U "$POSTGRES_USER" -d reprospective -t -c "SELECT COUNT(*) FROM monitored_directories;" | tr -d ' ')
ENABLED_COUNT=$(docker compose exec -T database psql -U "$POSTGRES_USER" -d reprospective -t -c "SELECT COUNT(*) FROM monitored_directories WHERE enabled = true;" | tr -d ' ')
DISABLED_COUNT=$(docker compose exec -T database psql -U "$POSTGRES_USER" -d reprospective -t -c "SELECT COUNT(*) FROM monitored_directories WHERE enabled = false;" | tr -d ' ')

echo ""
echo "================================"
echo "📈 統計情報"
echo "================================"
echo "合計: ${COUNT}件"
echo "有効: ${ENABLED_COUNT}件"
echo "無効: ${DISABLED_COUNT}件"
echo ""

echo "💡 便利なコマンド:"
echo "   ./scripts/api-list-directories.sh     # API経由で一覧取得"
echo "   ./scripts/api-add-directory.sh        # 新規ディレクトリ追加"
echo "   ./scripts/api-toggle-directory.sh     # 有効/無効切り替え"
echo "   Web UI: http://localhost:3333          # ブラウザで管理"
echo ""
