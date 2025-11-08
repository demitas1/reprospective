/**
 * 監視対象ディレクトリ型定義
 *
 * バックエンドAPI（services/api-gateway/app/models/monitored_directory.py）と完全に一致
 */

/**
 * 監視対象ディレクトリ（APIレスポンス型）
 *
 * GET /api/v1/directories/ のレスポンス型
 * GET /api/v1/directories/{id} のレスポンス型
 */
export interface Directory {
  id: number;
  directory_path: string;          // バックエンドと一致（path ではない）
  enabled: boolean;                // バックエンドと一致（is_enabled ではない）
  display_name: string | null;
  description: string | null;
  display_path: string | null;     // 表示用パス（ユーザー入力値）
  resolved_path: string | null;    // 実体パス（シンボリックリンク解決後）
  created_at: string;              // ISO 8601形式の日時文字列
  updated_at: string;              // ISO 8601形式の日時文字列
  created_by: string;
  updated_by: string;
}

/**
 * 監視対象ディレクトリ作成用（POST /api/v1/directories/）
 *
 * バックエンドのMonitoredDirectoryCreateモデルに対応
 */
export interface DirectoryCreate {
  directory_path: string;          // 必須: 絶対パス
  enabled?: boolean;               // オプション: デフォルトtrue
  display_name?: string;           // オプション: 表示名（最大100文字）
  description?: string;            // オプション: 説明（最大500文字）
  created_by?: string;             // オプション: デフォルト"api"
}

/**
 * 監視対象ディレクトリ更新用（PUT /api/v1/directories/{id}）
 *
 * バックエンドのMonitoredDirectoryUpdateモデルに対応
 * すべてのフィールドがオプション（部分更新対応）
 */
export interface DirectoryUpdate {
  directory_path?: string;         // オプション: 絶対パス
  enabled?: boolean;               // オプション: 有効/無効
  display_name?: string;           // オプション: 表示名（最大100文字）
  description?: string;            // オプション: 説明（最大500文字）
  updated_by?: string;             // オプション: デフォルト"api"
}

/**
 * API エラーレスポンス型
 */
export interface ApiError {
  detail: string | ApiErrorDetail[];
}

export interface ApiErrorDetail {
  loc: (string | number)[];
  msg: string;
  type: string;
}
