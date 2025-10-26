#!/bin/bash
# Reprospective Docker完全クリーンアップスクリプト
# コンテナ、イメージ、ボリュームを完全に削除する

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "================================"
echo "⚠️  Docker完全クリーンアップ"
echo "================================"
echo ""
echo "このスクリプトは以下を実行します:"
echo "  1. すべてのコンテナを停止・削除"
echo "  2. 永続化ボリュームを削除"
echo "  3. ネットワークを削除"
echo ""
echo "⚠️  警告: データベースの全データが完全に削除されます！"
echo "⚠️  警告: ボリュームを削除すると復元できません！"
echo ""

# 確認プロンプト
read -p "本当にDockerリソースを完全に削除しますか? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ キャンセルしました"
    exit 0
fi

echo ""
echo "🗑️  Dockerリソースを削除中..."

# 実行中のコンテナを確認
RUNNING=$(docker compose ps --status running --quiet 2>/dev/null | wc -l)
if [ "$RUNNING" -gt "0" ]; then
    echo "  - コンテナを停止中..."
    docker compose stop > /dev/null 2>&1
fi

# コンテナとネットワークを削除
echo "  - コンテナとネットワークを削除中..."
docker compose down > /dev/null 2>&1

# ボリュームを削除
echo "  - 永続化ボリュームを削除中..."
docker compose down -v > /dev/null 2>&1

# 残存ボリュームの確認と削除
VOLUMES=$(docker volume ls -q | grep reprospective 2>/dev/null || true)
if [ -n "$VOLUMES" ]; then
    echo "  - 残存ボリュームを削除中..."
    echo "$VOLUMES" | xargs docker volume rm > /dev/null 2>&1 || true
fi

echo ""
echo "✅ Dockerリソースを完全に削除しました"
echo ""
echo "📊 削除内容:"
echo "  - コンテナ: 削除完了"
echo "  - ボリューム: 削除完了"
echo "  - ネットワーク: 削除完了"
echo ""
echo "💡 再度起動する場合:"
echo "   ./scripts/start.sh"
echo ""
echo "💡 イメージも削除する場合:"
echo "   docker rmi postgres:16-alpine"
echo ""
