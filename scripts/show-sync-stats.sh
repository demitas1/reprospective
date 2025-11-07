#!/bin/bash
# データ同期統計表示スクリプト
# sync_logsテーブルから同期統計を表示する

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# オプション解析
SHOW_ALL=false
if [[ "$1" == "--all" ]]; then
    SHOW_ALL=true
fi

echo "================================"
if [[ "$SHOW_ALL" == "true" ]]; then
    echo "📊 データ同期統計 (全期間)"
else
    echo "📊 データ同期統計 (本日)"
fi
echo "================================"
echo ""

# コンテナの実行確認
if ! docker compose ps --status running --quiet database > /dev/null 2>&1; then
    echo "❌ データベースコンテナが実行されていません"
    echo "   ./scripts/start.sh でコンテナを起動してください"
    exit 1
fi

echo "📋 最新10件の同期ログ:"
echo ""

docker compose exec -T database psql -U reprospective_user -d reprospective << 'EOF'
\x
SELECT
    id,
    sync_started_at,
    sync_completed_at,
    table_name,
    records_synced,
    records_failed,
    status,
    error_message,
    host_identifier
FROM sync_logs
ORDER BY sync_started_at DESC
LIMIT 10;
EOF

echo ""
echo "================================"
echo "📈 テーブル別同期サマリー:"
echo ""

if [[ "$SHOW_ALL" == "true" ]]; then
    docker compose exec -T database psql -U reprospective_user -d reprospective << 'EOF'
SELECT
    table_name AS "テーブル名",
    COUNT(*) AS "同期回数",
    SUM(records_synced) AS "総同期件数",
    SUM(records_failed) AS "総失敗件数",
    MAX(sync_started_at) AS "最終同期時刻"
FROM sync_logs
GROUP BY table_name
ORDER BY table_name;
EOF
else
    docker compose exec -T database psql -U reprospective_user -d reprospective << 'EOF'
SELECT
    table_name AS "テーブル名",
    COUNT(*) AS "同期回数",
    SUM(records_synced) AS "総同期件数",
    SUM(records_failed) AS "総失敗件数",
    MAX(sync_started_at) AS "最終同期時刻"
FROM sync_logs
WHERE DATE(sync_started_at AT TIME ZONE 'Asia/Tokyo') = CURRENT_DATE
GROUP BY table_name
ORDER BY table_name;
EOF
fi

echo ""
echo "================================"
echo "🖥️  ホスト別同期統計:"
echo ""

if [[ "$SHOW_ALL" == "true" ]]; then
    docker compose exec -T database psql -U reprospective_user -d reprospective << 'EOF'
SELECT
    host_identifier AS "ホスト識別子",
    COUNT(*) AS "同期回数",
    SUM(records_synced) AS "総同期件数",
    SUM(records_failed) AS "総失敗件数",
    MAX(sync_started_at) AS "最終同期時刻"
FROM sync_logs
GROUP BY host_identifier
ORDER BY MAX(sync_started_at) DESC;
EOF
else
    docker compose exec -T database psql -U reprospective_user -d reprospective << 'EOF'
SELECT
    host_identifier AS "ホスト識別子",
    COUNT(*) AS "同期回数",
    SUM(records_synced) AS "総同期件数",
    SUM(records_failed) AS "総失敗件数",
    MAX(sync_started_at) AS "最終同期時刻"
FROM sync_logs
WHERE DATE(sync_started_at AT TIME ZONE 'Asia/Tokyo') = CURRENT_DATE
GROUP BY host_identifier
ORDER BY MAX(sync_started_at) DESC;
EOF
fi

echo ""
echo "================================"
echo "💡 詳細確認:"
echo "   docker compose exec database psql -U reprospective_user -d reprospective"
echo "   SELECT * FROM sync_logs ORDER BY sync_started_at DESC LIMIT 20;"
echo ""
if [[ "$SHOW_ALL" == "false" ]]; then
    echo "💡 全期間の統計を表示:"
    echo "   ./scripts/show-sync-stats.sh --all"
    echo ""
fi
