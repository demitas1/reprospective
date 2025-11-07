# DesktopActivityMonitor 設計書

## 実装状況

✅ **Phase 1 実装完了** (2025-10-25)
✅ **Phase 2.3 データ同期機能完了** (2025-11-05)

実装の詳細は以下を参照：
- `host-agent/collectors/linux_x11_monitor.py`
- `host-agent/common/models.py` (`ActivitySession`クラス)
- `host-agent/common/database.py` (`DesktopActivityDatabase`クラス)
- `host-agent/common/data_sync.py` (SQLite → PostgreSQL同期)
- `host-agent/README.md`

---

## 目的

ホスト環境で動作するデスクトップアクティビティ監視コンポーネント。
フォアグラウンドウィンドウのタイトルとアプリケーション名を定期的に取得し、セッション単位でユーザーの活動を記録する。

## 設計方針

### セッション管理

- **セッション**: 同じアプリケーション＋同じウィンドウタイトルの連続した活動期間
- ウィンドウが変わったら前のセッションを終了し、新しいセッションを開始
- 同じウィンドウが続く場合は記録しない（重複排除）

### データ保存

**SQLiteローカルキャッシュ**:
- データベースファイル: `data/desktop_activity.db`
- セッション開始時刻、終了時刻、継続時間を記録
- タイムスタンプはUNIXエポック秒（整数）とISO 8601形式（文字列）の両方を保存
- `synced_at`カラム: PostgreSQL同期状態を管理

**PostgreSQL中央DB**:
- テーブル: `desktop_activity_sessions`
- 既存の`DataSyncManager`を使用してバッチ同期（デフォルト5分間隔、100件ずつ）
- 同期ログを`sync_logs`テーブルに記録

### 設定管理

**config.yaml**:
```yaml
desktop_monitor:
  enabled: true
  monitor_interval: 10  # 監視間隔（秒）
```

**環境変数** (`.env`):
```bash
# SQLiteデータベースパス
SQLITE_DESKTOP_PATH=data/desktop_activity.db

# PostgreSQL接続情報
DATABASE_URL=postgresql://user:password@localhost:6000/reprospective
# または個別指定
DB_HOST=localhost
DB_PORT=6000
DB_NAME=reprospective
DB_USER=reprospective_user
DB_PASSWORD=change_this_password
```

### エラーハンドリング

- **ウィンドウ情報取得失敗**: スキップして次のサイクルへ
- **データベースエラー**: ログ記録して継続
- **同期エラー**: `DataSyncManager`のリトライロジック（最大5回、指数バックオフ）
- **Ctrl+C**: 現在のセッションを正常終了し、バッファをフラッシュ

## 技術スタック

### 依存ツール
- **xdotool**: アクティブウィンドウID取得
- **xprop**: ウィンドウプロパティ取得
- **PyYAML**: 設定ファイル読み込み
- **asyncpg**: PostgreSQL非同期クライアント
- **python-dotenv**: 環境変数管理

### 対応環境
- **Phase 1（現在）**: Linux X11のみ
- **Phase 2以降**: Wayland、Windows、macOS対応予定

---

## データベーススキーマ

### SQLiteスキーマ

```sql
CREATE TABLE desktop_activity_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time INTEGER NOT NULL,           -- UNIXエポック秒
    end_time INTEGER,                      -- セッション継続中はNULL
    start_time_iso TEXT NOT NULL,          -- ISO 8601形式
    end_time_iso TEXT,
    application_name TEXT NOT NULL,        -- アプリケーション名
    window_title TEXT NOT NULL,            -- ウィンドウタイトル
    duration_seconds INTEGER,              -- 継続時間（秒）
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    synced_at INTEGER                      -- PostgreSQL同期済みフラグ
);

CREATE INDEX idx_start_time ON desktop_activity_sessions(start_time);
CREATE INDEX idx_synced_at ON desktop_activity_sessions(synced_at);
```

### PostgreSQLスキーマ

```sql
CREATE TABLE desktop_activity_sessions (
    id SERIAL PRIMARY KEY,
    start_time BIGINT NOT NULL,
    end_time BIGINT,
    start_time_iso TIMESTAMP NOT NULL,
    end_time_iso TIMESTAMP,
    application_name TEXT NOT NULL,
    window_title TEXT NOT NULL,
    duration_seconds INTEGER,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    host_identifier TEXT NOT NULL,         -- 同期元ホスト識別子
    synced_from_local_id INTEGER           -- ローカルDB ID
);

CREATE INDEX idx_desktop_start_time ON desktop_activity_sessions(start_time);
CREATE INDEX idx_desktop_host_identifier ON desktop_activity_sessions(host_identifier);
```

---

## データ同期

### 同期フロー

```
1. 定期同期（5分間隔）
   ├─ SQLiteから未同期セッションを取得（WHERE synced_at IS NULL）
   ├─ バッチ単位でPostgreSQLに挿入（デフォルト100件）
   ├─ 成功したセッションのsynced_atフラグを更新
   └─ 同期統計をsync_logsテーブルに記録

2. エラー時
   ├─ トランザクションロールバック
   ├─ 指数バックオフでリトライ（最大5回）
   └─ エラーログ記録
```

### 同期設定

```yaml
data_sync:
  enabled: true                # 同期機能有効化
  interval_seconds: 300        # 同期間隔（5分）
  batch_size: 100              # バッチサイズ
  max_retries: 5               # 最大リトライ回数
  retry_backoff_seconds: 30    # リトライ間隔
```

---

## 将来的な拡張

### Phase 2（一部完了）
- ✅ PostgreSQLへのデータ同期（完了）
- ✅ 環境変数による設定管理（完了）
- 📋 Wayland対応（`swaymsg`）
- 📋 Windows対応（`pywin32`）
- 📋 macOS対応（`AppKit`）
- 📋 アイドル状態の検出

### Phase 3（未実装）
- BrowserActivityParserとの連携（URL解析など）
- アプリケーションカテゴリの自動分類
- プロジェクト推定機能
- Web UI統合（セッション一覧、グラフ表示）

## テスト確認項目

### Phase 1（完了）
- [x] 同じウィンドウが続く場合、セッションが継続される
- [x] ウィンドウ変更時、前のセッションが終了し新しいセッションが開始
- [x] 終了時刻（end_time）が正しく記録される
- [x] duration_secondsが正しく計算される
- [x] 設定ファイルの監視間隔が反映される
- [x] Ctrl+Cで正常終了処理が実行される

### Phase 2.3 データ同期（完了）
- [x] SQLiteにセッションが保存される
- [x] PostgreSQLへバッチ同期が成功する
- [x] synced_atフラグが正しく更新される
- [x] 同期ログが記録される
- [x] エラー時のリトライロジックが動作する
- [x] データ型整合性（UNIXタイムスタンプ整数、ISO文字列）

---

## 参考資料

- 企画書: `docs/software_idea-ai_assited_todo.md`
- 実装計画: `docs/design/phase2_3_implementation_plan.md`
- 手動テスト手順: `docs/manual/humantest-db-sync.md`
- 実装: `host-agent/collectors/linux_x11_monitor.py`
- データ同期: `host-agent/common/data_sync.py`
