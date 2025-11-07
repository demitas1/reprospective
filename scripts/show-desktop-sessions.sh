#!/bin/bash
# PostgreSQLのdesktop_activity_sessionsテーブルから最新n件を表示

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# .envファイルから環境変数を読み込む
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# デフォルト設定
LIMIT=${1:-10}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-6000}
DB_NAME=${DB_NAME:-reprospective_db}
DB_USER=${DB_USER:-reprospective_user}
DB_PASSWORD=${DB_PASSWORD:-change_this_password}

echo "================================================"
echo "Desktop Activity Sessions (最新 ${LIMIT} 件)"
echo "================================================"
echo ""

# PostgreSQLクエリを実行（ページャー無効化）
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-psqlrc --pset pager=off -c "
SELECT
    id,
    application_name,
    window_title,
    to_char(start_time_iso, 'YYYY-MM-DD HH24:MI:SS') as start_time,
    to_char(end_time_iso, 'YYYY-MM-DD HH24:MI:SS') as end_time,
    duration_seconds,
    to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
FROM
    desktop_activity_sessions
ORDER BY
    start_time DESC
LIMIT ${LIMIT};
"

echo ""
echo "総レコード数:"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-psqlrc --pset pager=off -t -c "
SELECT COUNT(*) FROM desktop_activity_sessions;
"
