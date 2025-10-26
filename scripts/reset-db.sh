#!/bin/bash
# Reprospective データベースリセットスクリプト
# PostgreSQLのデータベースを完全に初期化する（全データ・スキーマ削除）

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "================================"
echo "⚠️  データベースリセット"
echo "================================"
echo ""
echo "このスクリプトは以下を実行します:"
echo "  1. PostgreSQL内の全テーブルを削除"
echo "  2. スキーマを再初期化"
echo ""
echo "⚠️  警告: すべてのデータが削除されます！"
echo ""

# 確認プロンプト
read -p "本当にデータベースをリセットしますか? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ キャンセルしました"
    exit 0
fi

# コンテナの実行確認
if ! docker compose ps --status running --quiet database > /dev/null 2>&1; then
    echo "⚠️  データベースコンテナが実行されていません"
    echo "🚀 コンテナを起動します..."
    ./scripts/start.sh
    echo ""
fi

echo ""
echo "🗑️  データベースをリセット中..."

# 全テーブルを削除
echo "  - 既存テーブルを削除..."
docker compose exec -T database psql -U reprospective_user -d reprospective << 'EOF' > /dev/null 2>&1
DROP TABLE IF EXISTS desktop_activity_sessions CASCADE;
DROP TABLE IF EXISTS file_change_events CASCADE;
DROP TABLE IF EXISTS schema_version CASCADE;
DROP VIEW IF EXISTS daily_activity_summary CASCADE;
DROP VIEW IF EXISTS daily_file_changes_summary CASCADE;
EOF

# スキーマを再初期化
echo "  - スキーマを再初期化..."
docker compose exec -T database psql -U reprospective_user -d reprospective < services/database/init/01_init_schema.sql > /dev/null

# 確認
TABLES=$(docker compose exec -T database psql -U reprospective_user -d reprospective -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" 2>/dev/null | tr -d ' ')

echo ""
echo "✅ データベースをリセットしました"
echo ""
echo "📊 現在のテーブル数: $TABLES"
echo ""
echo "💡 テーブル一覧を確認:"
echo "   docker compose exec database psql -U reprospective_user -d reprospective -c '\dt'"
echo ""
