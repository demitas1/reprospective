-- InputMonitor用テーブル作成
-- 入力活動セッション（マウス・キーボード入力期間）を記録

CREATE TABLE IF NOT EXISTS input_activity_sessions (
    id SERIAL PRIMARY KEY,
    start_time BIGINT NOT NULL,                -- 開始時刻（UNIXエポック秒）
    end_time BIGINT,                           -- 終了時刻（UNIXエポック秒、継続中はNULL）
    start_time_iso TIMESTAMP NOT NULL,         -- 開始時刻（ISO 8601形式）
    end_time_iso TIMESTAMP,                    -- 終了時刻（ISO 8601形式）
    duration_seconds INTEGER,                  -- 継続時間（秒）
    created_at BIGINT NOT NULL,                -- レコード作成時刻
    updated_at BIGINT NOT NULL,                -- レコード更新時刻
    host_identifier TEXT NOT NULL,             -- 同期元ホスト識別子
    synced_from_local_id INTEGER               -- ローカルDB ID
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_input_start_time ON input_activity_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_input_host_identifier ON input_activity_sessions(host_identifier);

-- コメント追加
COMMENT ON TABLE input_activity_sessions IS '入力活動セッション（マウス・キーボード入力期間）';
COMMENT ON COLUMN input_activity_sessions.start_time IS '開始時刻（UNIXエポック秒）';
COMMENT ON COLUMN input_activity_sessions.end_time IS '終了時刻（UNIXエポック秒）';
COMMENT ON COLUMN input_activity_sessions.duration_seconds IS '継続時間（秒）';
COMMENT ON COLUMN input_activity_sessions.host_identifier IS '同期元ホスト識別子（hostname_username形式）';
COMMENT ON COLUMN input_activity_sessions.synced_from_local_id IS 'SQLiteローカルDBのID';
