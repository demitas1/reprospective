#!/bin/bash
# Reprospective host-agent データクリーンアップスクリプト
# host-agentのローカルSQLiteデータベースを削除する

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "================================"
echo "⚠️  host-agent データクリーンアップ"
echo "================================"
echo ""
echo "このスクリプトは以下を実行します:"
echo "  1. host-agent/data/ 配下のSQLiteデータベースを削除"
echo "     - desktop_activity.db"
echo "     - file_changes.db"
echo ""
echo "⚠️  警告: ローカルの全活動データが削除されます！"
echo ""

# データベースファイルの確認
HOST_DATA_DIR="$PROJECT_ROOT/host-agent/data"
DESKTOP_DB="$HOST_DATA_DIR/desktop_activity.db"
FILES_DB="$HOST_DATA_DIR/file_changes.db"

DESKTOP_EXISTS=false
FILES_EXISTS=false
DESKTOP_SIZE=""
FILES_SIZE=""

if [ -f "$DESKTOP_DB" ]; then
    DESKTOP_EXISTS=true
    DESKTOP_SIZE=$(du -h "$DESKTOP_DB" 2>/dev/null | cut -f1)
fi

if [ -f "$FILES_DB" ]; then
    FILES_EXISTS=true
    FILES_SIZE=$(du -h "$FILES_DB" 2>/dev/null | cut -f1)
fi

# データベースが存在しない場合
if [ "$DESKTOP_EXISTS" = false ] && [ "$FILES_EXISTS" = false ]; then
    echo "ℹ️  削除するデータベースファイルがありません"
    exit 0
fi

# 現在のデータベース情報を表示
echo "📊 現在のデータベース:"
if [ "$DESKTOP_EXISTS" = true ]; then
    echo "  ✓ desktop_activity.db ($DESKTOP_SIZE)"
fi
if [ "$FILES_EXISTS" = true ]; then
    echo "  ✓ file_changes.db ($FILES_SIZE)"
fi
echo ""

# 確認プロンプト
read -p "本当にhost-agentのデータベースを削除しますか? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ キャンセルしました"
    exit 0
fi

echo ""
echo "🗑️  データベースを削除中..."

# データベースファイルを削除
DELETED_COUNT=0

if [ "$DESKTOP_EXISTS" = true ]; then
    rm -f "$DESKTOP_DB"
    echo "  - desktop_activity.db を削除しました"
    DELETED_COUNT=$((DELETED_COUNT + 1))
fi

if [ "$FILES_EXISTS" = true ]; then
    rm -f "$FILES_DB"
    echo "  - file_changes.db を削除しました"
    DELETED_COUNT=$((DELETED_COUNT + 1))
fi

# WALファイルとSHMファイルも削除
rm -f "$HOST_DATA_DIR"/*.db-wal 2>/dev/null || true
rm -f "$HOST_DATA_DIR"/*.db-shm 2>/dev/null || true

echo ""
echo "✅ host-agentのデータベースを削除しました ($DELETED_COUNT ファイル)"
echo ""
echo "💡 host-agentを再起動すると、新しいデータベースが自動作成されます:"
echo "   cd host-agent"
echo "   source venv/bin/activate"
echo "   python collectors/linux_x11_monitor.py"
echo "   python collectors/filesystem_watcher.py"
echo ""
