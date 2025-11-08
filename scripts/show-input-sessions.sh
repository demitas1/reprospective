#!/bin/bash
# PostgreSQLのinput_activity_sessionsテーブルから最新n件を表示

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# デフォルト設定
LIMIT=${1:-10}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-6000}
DB_NAME=${DB_NAME:-reprospective}
DB_USER=${DB_USER:-reprospective_user}
DB_PASSWORD=${DB_PASSWORD:-change_this_password}

echo "================================================"
echo "Input Activity Sessions (最新 ${LIMIT} 件)"
echo "================================================"
echo ""

# PostgreSQLクエリを実行（ページャー無効化）
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-psqlrc --pset pager=off -c "
SELECT
    id,
    to_char(start_time_iso, 'YYYY-MM-DD HH24:MI:SS') as start_time,
    to_char(end_time_iso, 'YYYY-MM-DD HH24:MI:SS') as end_time,
    duration_seconds,
    host_identifier
FROM
    input_activity_sessions
ORDER BY
    start_time_iso DESC
LIMIT ${LIMIT};
"

echo ""
echo "総レコード数:"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-psqlrc --pset pager=off -t -c "
SELECT COUNT(*) FROM input_activity_sessions;
"
