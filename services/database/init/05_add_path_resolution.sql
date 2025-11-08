-- 05_add_path_resolution.sql
-- シンボリックリンク対応: display_path と resolved_path カラムの追加

-- display_path: ユーザー入力値（表示用）
-- resolved_path: 実体パス（監視用、シンボリックリンク解決後）
ALTER TABLE monitored_directories
ADD COLUMN IF NOT EXISTS display_path TEXT,
ADD COLUMN IF NOT EXISTS resolved_path TEXT;

-- 既存データの移行
-- display_path と resolved_path に既存の directory_path をコピー
UPDATE monitored_directories
SET display_path = directory_path,
    resolved_path = directory_path
WHERE display_path IS NULL;

-- インデックス追加（検索最適化）
CREATE INDEX IF NOT EXISTS idx_monitored_directories_resolved_path
ON monitored_directories(resolved_path)
WHERE resolved_path IS NOT NULL;

-- コメント追加
COMMENT ON COLUMN monitored_directories.display_path IS 'ユーザー入力パス（表示用）';
COMMENT ON COLUMN monitored_directories.resolved_path IS '実体パス（監視用、シンボリックリンク解決後）';
