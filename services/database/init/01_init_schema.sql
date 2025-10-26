-- Reprospective データベース初期化スクリプト
-- PostgreSQL 16用

-- 拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- タイムゾーン設定
SET timezone = 'Asia/Tokyo';

-- ================================
-- デスクトップアクティビティテーブル
-- ================================

CREATE TABLE IF NOT EXISTS desktop_activity_sessions (
    id BIGSERIAL PRIMARY KEY,
    start_time BIGINT NOT NULL,
    end_time BIGINT,
    start_time_iso TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time_iso TIMESTAMP WITH TIME ZONE,
    application_name TEXT NOT NULL,
    window_title TEXT NOT NULL,
    duration_seconds INTEGER,
    synced_at TIMESTAMP WITH TIME ZONE,  -- ローカルDBから同期された時刻
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_desktop_start_time ON desktop_activity_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_desktop_application_name ON desktop_activity_sessions(application_name);
CREATE INDEX IF NOT EXISTS idx_desktop_synced_at ON desktop_activity_sessions(synced_at);

-- コメント
COMMENT ON TABLE desktop_activity_sessions IS 'デスクトップアクティビティセッション';
COMMENT ON COLUMN desktop_activity_sessions.synced_at IS 'ローカルSQLiteから同期された時刻';

-- ================================
-- ファイル変更イベントテーブル
-- ================================

CREATE TABLE IF NOT EXISTS file_change_events (
    id BIGSERIAL PRIMARY KEY,
    event_time BIGINT NOT NULL,
    event_time_iso TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('created', 'modified', 'deleted', 'moved')),
    file_path TEXT NOT NULL,
    file_path_relative TEXT,
    file_name TEXT NOT NULL,
    file_extension TEXT,
    file_size BIGINT,
    is_symlink BOOLEAN DEFAULT false,
    monitored_root TEXT NOT NULL,
    project_name TEXT,
    synced_at TIMESTAMP WITH TIME ZONE,  -- ローカルDBから同期された時刻
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_file_event_time ON file_change_events(event_time);
CREATE INDEX IF NOT EXISTS idx_file_project_name ON file_change_events(project_name);
CREATE INDEX IF NOT EXISTS idx_file_extension ON file_change_events(file_extension);
CREATE INDEX IF NOT EXISTS idx_file_event_type ON file_change_events(event_type);
CREATE INDEX IF NOT EXISTS idx_file_synced_at ON file_change_events(synced_at);

-- コメント
COMMENT ON TABLE file_change_events IS 'ファイル変更イベント';
COMMENT ON COLUMN file_change_events.synced_at IS 'ローカルSQLiteから同期された時刻';

-- ================================
-- 統計ビュー（将来の分析用）
-- ================================

-- 日別アクティビティ集計ビュー
CREATE OR REPLACE VIEW daily_activity_summary AS
SELECT
    DATE(start_time_iso) as activity_date,
    application_name,
    COUNT(*) as session_count,
    SUM(duration_seconds) as total_duration_seconds,
    AVG(duration_seconds) as avg_duration_seconds
FROM desktop_activity_sessions
WHERE end_time IS NOT NULL
GROUP BY DATE(start_time_iso), application_name
ORDER BY activity_date DESC, total_duration_seconds DESC;

COMMENT ON VIEW daily_activity_summary IS '日別アクティビティ集計（アプリケーションごと）';

-- 日別ファイル変更集計ビュー
CREATE OR REPLACE VIEW daily_file_changes_summary AS
SELECT
    DATE(event_time_iso) as event_date,
    project_name,
    event_type,
    file_extension,
    COUNT(*) as event_count
FROM file_change_events
GROUP BY DATE(event_time_iso), project_name, event_type, file_extension
ORDER BY event_date DESC, event_count DESC;

COMMENT ON VIEW daily_file_changes_summary IS '日別ファイル変更集計';

-- ================================
-- 初期化完了
-- ================================

-- バージョン情報テーブル
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES (1, 'Initial schema: desktop_activity_sessions, file_change_events')
ON CONFLICT (version) DO NOTHING;

-- 初期化完了ログ
DO $$
BEGIN
    RAISE NOTICE 'Reprospective database schema initialized successfully';
END $$;
