-- データ同期ログテーブル
-- Phase 2.3: SQLite → PostgreSQL データ同期の統計・監視用

CREATE TABLE IF NOT EXISTS sync_logs (
    id BIGSERIAL PRIMARY KEY,
    sync_started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    sync_completed_at TIMESTAMP WITH TIME ZONE,
    table_name TEXT NOT NULL,                          -- desktop_activity_sessions or file_change_events
    records_synced INTEGER DEFAULT 0,                  -- 同期成功件数
    records_failed INTEGER DEFAULT 0,                  -- 同期失敗件数
    status TEXT NOT NULL,                              -- success, partial_success, failed
    error_message TEXT,                                -- エラーメッセージ
    host_identifier TEXT,                              -- 同期元ホスト識別子 (hostname_username)
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_sync_logs_started_at
    ON sync_logs(sync_started_at);
CREATE INDEX IF NOT EXISTS idx_sync_logs_table_name
    ON sync_logs(table_name);
CREATE INDEX IF NOT EXISTS idx_sync_logs_status
    ON sync_logs(status);
CREATE INDEX IF NOT EXISTS idx_sync_logs_host_identifier
    ON sync_logs(host_identifier);

-- コメント
COMMENT ON TABLE sync_logs IS 'SQLite → PostgreSQL データ同期ログ';
COMMENT ON COLUMN sync_logs.id IS 'プライマリキー';
COMMENT ON COLUMN sync_logs.sync_started_at IS '同期開始時刻';
COMMENT ON COLUMN sync_logs.sync_completed_at IS '同期完了時刻';
COMMENT ON COLUMN sync_logs.table_name IS '同期対象テーブル名';
COMMENT ON COLUMN sync_logs.records_synced IS '同期成功件数';
COMMENT ON COLUMN sync_logs.records_failed IS '同期失敗件数';
COMMENT ON COLUMN sync_logs.status IS '同期ステータス (success/partial_success/failed)';
COMMENT ON COLUMN sync_logs.error_message IS 'エラーメッセージ（失敗時のみ）';
COMMENT ON COLUMN sync_logs.host_identifier IS '同期元ホスト識別子';
COMMENT ON COLUMN sync_logs.created_at IS 'レコード作成日時';

-- スキーマバージョン管理テーブル（存在しない場合のみ作成）
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- バージョン3を記録
INSERT INTO schema_version (version, description)
VALUES (3, 'Add sync_logs table for SQLite to PostgreSQL data synchronization')
ON CONFLICT (version) DO NOTHING;
