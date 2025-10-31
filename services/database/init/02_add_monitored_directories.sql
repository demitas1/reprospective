-- 監視対象ディレクトリテーブル
-- Phase 2.1: FileSystemWatcherの監視対象ディレクトリをPostgreSQLで管理

CREATE TABLE IF NOT EXISTS monitored_directories (
    id SERIAL PRIMARY KEY,
    directory_path TEXT UNIQUE NOT NULL,              -- 絶対パス
    enabled BOOLEAN DEFAULT true NOT NULL,             -- 有効/無効
    display_name TEXT,                                 -- 表示名（UI用）
    description TEXT,                                  -- 説明
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system' NOT NULL,         -- 追加者
    updated_by TEXT DEFAULT 'system' NOT NULL          -- 最終更新者
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_monitored_directories_enabled
    ON monitored_directories(enabled);
CREATE INDEX IF NOT EXISTS idx_monitored_directories_updated_at
    ON monitored_directories(updated_at);

-- コメント
COMMENT ON TABLE monitored_directories IS 'ファイルシステム監視対象ディレクトリ';
COMMENT ON COLUMN monitored_directories.id IS 'プライマリキー';
COMMENT ON COLUMN monitored_directories.directory_path IS '監視対象の絶対パス（UNIQUE制約）';
COMMENT ON COLUMN monitored_directories.enabled IS 'false の場合は監視を一時停止';
COMMENT ON COLUMN monitored_directories.display_name IS 'UI表示用の名前';
COMMENT ON COLUMN monitored_directories.description IS 'ディレクトリの説明';
COMMENT ON COLUMN monitored_directories.created_at IS 'レコード作成日時';
COMMENT ON COLUMN monitored_directories.updated_at IS '最終更新日時';
COMMENT ON COLUMN monitored_directories.created_by IS 'レコード作成者（api/system/user等）';
COMMENT ON COLUMN monitored_directories.updated_by IS '最終更新者';

-- updated_atの自動更新トリガー
CREATE OR REPLACE FUNCTION update_monitored_directories_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_monitored_directories_updated_at
    BEFORE UPDATE ON monitored_directories
    FOR EACH ROW
    EXECUTE FUNCTION update_monitored_directories_updated_at();
