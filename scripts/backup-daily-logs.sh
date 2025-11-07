#!/bin/bash
# 毎日のデータベースログをバックアップするスクリプト

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# .envファイルから環境変数を読み込む
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# デフォルト設定
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-6000}
DB_NAME=${DB_NAME:-reprospective}
DB_USER=${DB_USER:-reprospective_user}
DB_PASSWORD=${DB_PASSWORD:-change_this_password}

# 日付を引数から取得（指定がない場合は今日）
TARGET_DATE=${1:-$(date +%Y-%m-%d)}
LOG_DIR="$PROJECT_ROOT/logs/$TARGET_DATE"

echo "================================================"
echo "日次ログバックアップ: $TARGET_DATE"
echo "================================================"

# ログディレクトリを作成
mkdir -p "$LOG_DIR"

echo "出力先: $LOG_DIR"
echo ""

# 1. デスクトップアクティビティセッションを出力
echo "[1/3] デスクトップアクティビティセッションをバックアップ中..."
DESKTOP_OUTPUT="$LOG_DIR/desktop_activity_sessions.txt"

PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-psqlrc --pset pager=off -c "
SELECT
    id,
    to_char(start_time_iso, 'YYYY-MM-DD HH24:MI:SS') as start_time,
    to_char(end_time_iso, 'YYYY-MM-DD HH24:MI:SS') as end_time,
    duration_seconds,
    application_name,
    window_title
FROM
    desktop_activity_sessions
WHERE
    DATE(start_time_iso) = '$TARGET_DATE'
ORDER BY
    start_time ASC;
" > "$DESKTOP_OUTPUT"

DESKTOP_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-psqlrc --pset pager=off -t -c "
SELECT COUNT(*) FROM desktop_activity_sessions WHERE DATE(start_time_iso) = '$TARGET_DATE';
" | xargs)

echo "  ✓ ${DESKTOP_COUNT}件のセッションを記録しました"
echo "  → $DESKTOP_OUTPUT"
echo ""

# 2. ファイル変更イベントを出力
echo "[2/3] ファイル変更イベントをバックアップ中..."
FILE_OUTPUT="$LOG_DIR/file_change_events.txt"

PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-psqlrc --pset pager=off -c "
SELECT
    id,
    to_char(event_time_iso, 'YYYY-MM-DD HH24:MI:SS') as event_time,
    event_type,
    file_path,
    file_extension,
    file_size,
    is_symlink,
    monitored_root,
    project_name
FROM
    file_change_events
WHERE
    DATE(event_time_iso) = '$TARGET_DATE'
ORDER BY
    event_time ASC;
" > "$FILE_OUTPUT"

FILE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-psqlrc --pset pager=off -t -c "
SELECT COUNT(*) FROM file_change_events WHERE DATE(event_time_iso) = '$TARGET_DATE';
" | xargs)

echo "  ✓ ${FILE_COUNT}件のファイルイベントを記録しました"
echo "  → $FILE_OUTPUT"
echo ""

# 3. 同期ログを出力
echo "[3/3] 同期ログをバックアップ中..."
SYNC_OUTPUT="$LOG_DIR/sync_logs.txt"

PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-psqlrc --pset pager=off -c "
SELECT
    id,
    to_char(sync_started_at, 'YYYY-MM-DD HH24:MI:SS') as sync_started,
    to_char(sync_completed_at, 'YYYY-MM-DD HH24:MI:SS') as sync_completed,
    table_name,
    records_synced,
    records_failed,
    status,
    error_message
FROM
    sync_logs
WHERE
    DATE(sync_started_at) = '$TARGET_DATE'
ORDER BY
    sync_started_at ASC;
" > "$SYNC_OUTPUT"

SYNC_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-psqlrc --pset pager=off -t -c "
SELECT COUNT(*) FROM sync_logs WHERE DATE(sync_started_at) = '$TARGET_DATE';
" | xargs)

echo "  ✓ ${SYNC_COUNT}件の同期ログを記録しました"
echo "  → $SYNC_OUTPUT"
echo ""

# サマリー表示
echo "================================================"
echo "バックアップ完了"
echo "================================================"
echo "対象日: $TARGET_DATE"
echo "出力先: $LOG_DIR"
echo ""
echo "統計:"
echo "  - デスクトップセッション: ${DESKTOP_COUNT}件"
echo "  - ファイルイベント: ${FILE_COUNT}件"
echo "  - 同期ログ: ${SYNC_COUNT}件"
echo ""
