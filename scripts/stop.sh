#!/bin/bash
# Reprospective コンテナ停止スクリプト
# Docker Composeでサービスを停止する

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "================================"
echo "Reprospective コンテナ停止"
echo "================================"
echo ""

# 実行中のコンテナを確認
RUNNING=$(docker compose ps --status running --quiet 2>/dev/null | wc -l)

if [ "$RUNNING" -eq "0" ]; then
    echo "ℹ️  実行中のコンテナはありません"
    exit 0
fi

echo "📊 実行中のコンテナ:"
docker compose ps --status running
echo ""

# コンテナを停止
echo "🛑 コンテナを停止中..."
docker compose stop

echo ""
echo "✅ コンテナを停止しました"
echo ""
echo "💡 コンテナを完全に削除する場合:"
echo "   docker compose down"
echo ""
echo "💡 コンテナを再起動する場合:"
echo "   ./scripts/start.sh"
echo ""
