# Phase 2.3 実装計画: SQLite → PostgreSQL データ同期

**ステータス: 📋 計画中**

**前提条件:** Phase 2.1 (API Gateway & host-agent設定同期) 完了

---

## 概要

Phase 2.3では、host-agentのローカルSQLiteデータベースに記録されたデスクトップアクティビティとファイル変更イベントをPostgreSQLに同期する機能を実装します。これにより、分散して記録されたデータを中央データベースに集約し、長期保存・分析・可視化を可能にします。

### 実装目標

- **バッチ同期**: SQLiteからPostgreSQLへの定期的なデータ転送
- **増分同期**: 未同期データのみを効率的に転送
- **オフライン耐性**: ネットワーク障害時もローカルDBにデータ蓄積
- **データ整合性**: 重複排除、トランザクション保証
- **エラーリカバリ**: 同期失敗時の自動リトライとログ記録

### 対象範囲

- データ同期モジュール実装 (`host-agent/common/data_sync.py`)
- 同期状態管理（同期済みフラグ、最終同期時刻）
- バッチ同期タスク（定期実行、手動トリガー）
- 同期統計・監視機能
- PostgreSQLスキーマ拡張（同期メタデータ）

### 対象外（将来実装）

- リアルタイム同期（Phase 3: ストリーミング同期）
- 双方向同期（PostgreSQL → SQLite）
- データ圧縮・暗号化（Phase 3: セキュリティ強化）
- マルチホスト集約（Phase 3: マルチホスト管理）

---

## アーキテクチャ

### システム構成

```
┌────────────────────────────────────────────────────────┐
│                    host-agent                          │
│                                                        │
│  ┌──────────────────┐      ┌──────────────────┐      │
│  │ Desktop Monitor  │      │ Filesystem       │      │
│  │                  │      │ Watcher          │      │
│  └────────┬─────────┘      └────────┬─────────┘      │
│           │ write                   │ write          │
│           ▼                         ▼                │
│  ┌──────────────────┐      ┌──────────────────┐      │
│  │ desktop_         │      │ file_changes.db  │      │
│  │ activity.db      │      │ (SQLite)         │      │
│  │ (SQLite)         │      │                  │      │
│  └────────┬─────────┘      └────────┬─────────┘      │
│           │                         │                │
│           │    ┌──────────────────┐ │                │
│           └───►│  Data Sync       │◄┘                │
│                │  Module          │                  │
│                │  (asyncpg)       │                  │
│                └────────┬─────────┘                  │
│                         │ batch sync                 │
└─────────────────────────┼────────────────────────────┘
                          │
                          ▼
                   ┌──────────────────┐
                   │  PostgreSQL      │
                   │  (Container)     │
                   │                  │
                   │  - desktop_      │
                   │    activity_     │
                   │    sessions      │
                   │  - file_change_  │
                   │    events        │
                   │  - sync_logs     │
                   └──────────────────┘
```

### データフロー

**定期バッチ同期（デフォルト5分間隔）:**

```
1. 同期タスク起動
   ↓
2. SQLiteから未同期レコード取得 (synced_at IS NULL)
   ↓
3. PostgreSQL接続確認
   ↓
4. バッチ単位でINSERT (トランザクション)
   ↓
5. 成功 → SQLiteのsynced_atフラグ更新
   ↓
6. 同期統計を記録 (sync_logs)
```

**エラー時の動作:**

```
PostgreSQL接続失敗
   ↓
ローカルSQLiteに蓄積継続
   ↓
次回同期タスクで自動リトライ
   ↓
指数バックオフ付きリトライ（最大5回）
```

---

## データベース設計

### SQLiteスキーマ拡張

**desktop_activity_sessions テーブル拡張:**

```sql
-- 新規追加カラム
ALTER TABLE desktop_activity_sessions
ADD COLUMN synced_at INTEGER;  -- PostgreSQLに同期された時刻（UNIXエポック秒）
```

**file_change_events テーブル (新規):**

```sql
CREATE TABLE IF NOT EXISTS file_change_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time INTEGER NOT NULL,              -- イベント発生時刻（UNIXエポック秒）
    event_time_iso TEXT NOT NULL,             -- ISO 8601形式
    event_type TEXT NOT NULL,                 -- created/modified/deleted/moved
    file_path TEXT NOT NULL,                  -- 絶対パス
    file_path_relative TEXT,                  -- 監視ルートからの相対パス
    file_name TEXT NOT NULL,                  -- ファイル名
    file_extension TEXT,                      -- 拡張子（例: .py, .md）
    file_size INTEGER,                        -- ファイルサイズ（バイト）
    is_symlink INTEGER DEFAULT 0,             -- シンボリックリンクか
    monitored_root TEXT NOT NULL,             -- 監視ルートディレクトリ
    project_name TEXT,                        -- プロジェクト名（オプション）
    synced_at INTEGER,                        -- PostgreSQLに同期された時刻
    created_at INTEGER NOT NULL               -- レコード作成時刻
);

CREATE INDEX idx_file_event_time ON file_change_events(event_time);
CREATE INDEX idx_file_synced_at ON file_change_events(synced_at);
```

### PostgreSQL スキーマ

**既存テーブル（Phase 2で作成済み）:**

- `desktop_activity_sessions`: デスクトップアクティビティセッション
  - 既に `synced_at TIMESTAMP WITH TIME ZONE` カラムあり
- `file_change_events`: ファイル変更イベント
  - 既に `synced_at TIMESTAMP WITH TIME ZONE` カラムあり

**sync_logs テーブル（新規）:**

```sql
CREATE TABLE IF NOT EXISTS sync_logs (
    id BIGSERIAL PRIMARY KEY,
    sync_started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    sync_completed_at TIMESTAMP WITH TIME ZONE,
    table_name TEXT NOT NULL,                          -- desktop_activity_sessions or file_change_events
    records_synced INTEGER DEFAULT 0,                  -- 同期成功件数
    records_failed INTEGER DEFAULT 0,                  -- 同期失敗件数
    status TEXT NOT NULL,                              -- success, partial_success, failed
    error_message TEXT,                                -- エラーメッセージ
    host_identifier TEXT,                              -- 同期元ホスト識別子
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_sync_logs_started_at ON sync_logs(sync_started_at);
CREATE INDEX idx_sync_logs_table_name ON sync_logs(table_name);
CREATE INDEX idx_sync_logs_status ON sync_logs(status);
CREATE INDEX idx_sync_logs_host_identifier ON sync_logs(host_identifier);
```

---

## 実装詳細

### 1. データ同期モジュール

**実装場所:** `host-agent/common/data_sync.py`

**主要クラス:** `DataSyncManager`

**コンストラクタパラメータ:**
- `postgres_url`: PostgreSQL接続URL
- `sqlite_desktop_db_path`: デスクトップアクティビティSQLiteパス
- `sqlite_file_events_db_path`: ファイルイベントSQLiteパス
- `batch_size`: 1回の同期バッチサイズ（デフォルト100）
- `sync_interval`: 同期間隔秒（デフォルト300秒=5分）
- `max_retries`: 最大リトライ回数（デフォルト5）

**主要メソッド:**

| メソッド名 | 機能概要 |
|-----------|---------|
| `initialize()` | PostgreSQL接続プール初期化 |
| `close()` | 接続プールをクローズ |
| `sync_all()` | 全テーブルを同期（desktop + file_events） |
| `_sync_desktop_activity()` | デスクトップアクティビティセッションを同期 |
| `_sync_file_events()` | ファイル変更イベントを同期 |
| `_get_unsynced_desktop_records()` | SQLiteから未同期のデスクトップレコード取得 |
| `_get_unsynced_file_records()` | SQLiteから未同期のファイルレコード取得 |
| `_update_desktop_synced_flags()` | デスクトップレコードのsynced_atフラグ更新 |
| `_update_file_synced_flags()` | ファイルレコードのsynced_atフラグ更新 |
| `_log_sync_result()` | 同期結果をPostgreSQLのsync_logsに記録 |
| `_get_host_identifier()` | ホスト識別子取得（hostname_username） |
| `start_sync_loop()` | 定期同期ループを開始（asyncioタスク） |

**同期ロジック:**
1. SQLiteから `synced_at IS NULL` のレコードを取得
2. バッチサイズ単位でPostgreSQLにINSERT（トランザクション）
3. INSERT成功後、SQLiteの `synced_at` を現在時刻で更新
4. 同期結果を `sync_logs` テーブルに記録
5. エラー時はログ記録、次回リトライ

### 2. SQLiteスキーママイグレーション

**実装場所:** `host-agent/common/database.py`

**DesktopActivityDatabase クラス拡張:**

| メソッド名 | 機能概要 |
|-----------|---------|
| `migrate_add_synced_at_column()` | synced_atカラムをマイグレーション追加 |

**FileChangeDatabase クラス（新規）:**

| メソッド名 | 機能概要 |
|-----------|---------|
| `__init__(db_path)` | データベース初期化、テーブル作成 |
| `_connect()` | SQLite接続 |
| `_create_tables()` | file_change_eventsテーブル作成 |
| `save_event(event_data)` | ファイルイベントを保存 |
| `get_recent_events(limit)` | 最新イベント取得 |
| `close()` | データベース接続をクローズ |

### 3. collector統合

**実装場所:** `host-agent/collectors/linux_x11_monitor.py` (メイン起動スクリプト)

**統合内容:**
- `DataSyncManager` のインポート
- 同期マネージャーインスタンス作成
- `sync_manager.initialize()` で接続プール初期化
- `sync_manager.start_sync_loop()` をasyncioタスクで起動
- シャットダウン時に `sync_manager.close()` で接続クローズ

### 4. 設定ファイル拡張

**実装場所:** `host-agent/config/config.yaml`

**新規追加設定:**

```yaml
database:
  desktop_activity_db: "./data/desktop_activity.db"
  file_events_db: "./data/file_changes.db"
  postgres_url: "postgresql://reprospective_user:${POSTGRES_PASSWORD}@localhost:5432/reprospective"

data_sync:
  enabled: true                # 同期機能有効化
  interval_seconds: 300        # 同期間隔（デフォルト5分）
  batch_size: 100              # バッチサイズ
  max_retries: 5               # 最大リトライ回数
  retry_backoff_seconds: 30    # リトライ間隔（指数バックオフ）
```

---

## PostgreSQL マイグレーションスクリプト

**実装場所:** `services/database/init/03_add_sync_logs.sql`

**内容:**
- `sync_logs` テーブル作成
- インデックス作成（started_at, table_name, status, host_identifier）
- `schema_version` テーブルにバージョン2を記録

---

## 管理スクリプト

### scripts/show-sync-stats.sh（新規）

**機能:** データ同期統計を表示

**表示内容:**
- 最新10件の同期ログ（テーブル名、開始時刻、同期件数、ステータス、ホスト識別子）
- テーブル別同期サマリー（同期回数、総同期件数、最終同期時刻）
- ホスト別同期統計（ホスト識別子、同期回数、総同期件数、最終同期時刻）

### scripts/trigger-sync.sh（新規、将来実装）

**機能:** 手動同期トリガー（Phase 2.3では未実装、ログ出力のみ）

**将来実装方法:**
- UNIXソケット経由でhost-agentに同期シグナル送信
- HTTPエンドポイント（ローカルAPI）
- ファイルフラグ（.sync_now）の監視

---

## 実装手順

### ステップ1: PostgreSQLスキーマ拡張

1. `services/database/init/03_add_sync_logs.sql` を作成
2. `./scripts/reset-db.sh` でDBリセット（既存データ注意）
3. `sync_logs` テーブル作成確認

### ステップ2: SQLiteスキーママイグレーション

1. `common/database.py` に `migrate_add_synced_at_column()` メソッド追加
2. `FileChangeDatabase` クラス実装
3. マイグレーション実行確認

### ステップ3: データ同期モジュール実装

1. `host-agent/common/data_sync.py` を作成
2. `DataSyncManager` クラス実装
3. 各メソッド実装（sync_all, _sync_desktop_activity, _sync_file_events等）
4. エラーハンドリング、ロギング追加

### ステップ4: collector統合

1. `collectors/linux_x11_monitor.py` に同期マネージャー統合
2. `config/config.yaml` に同期設定追加
3. 起動・停止確認

### ステップ5: 管理スクリプト作成

1. `scripts/show-sync-stats.sh` 作成
2. `scripts/trigger-sync.sh` 作成（ログ出力のみ）
3. 実行権限付与

### ステップ6: 統合テスト

1. **ローカル同期テスト**: PostgreSQL起動 → host-agent起動 → 5分後にデータ同期確認
2. **オフライン耐性テスト**: PostgreSQL停止 → host-agent動作継続 → PostgreSQL再起動 → 自動同期確認
3. **大量データ同期テスト**: 数時間のデータ蓄積 → 同期パフォーマンス確認

---

## 完了条件

- [ ] `sync_logs` テーブルがPostgreSQLに作成されている
- [ ] SQLiteに `synced_at` カラムが追加されている
- [ ] `DataSyncManager` クラスが実装されている
- [ ] デスクトップアクティビティの同期が正常に動作する
- [ ] ファイルイベントの同期が正常に動作する
- [ ] 同期統計が `sync_logs` テーブルに記録される
- [ ] PostgreSQL接続失敗時もローカルSQLiteに蓄積継続される
- [ ] PostgreSQL復旧後、自動的に未同期データが同期される
- [ ] `show-sync-stats.sh` が動作する
- [ ] README.mdが更新され、同期機能の使い方が文書化されている

---

## 技術的考慮事項

### パフォーマンス

- **バッチサイズ調整**: デフォルト100件、環境に応じて調整可能
- **インデックス活用**: `synced_at IS NULL` クエリの高速化
- **接続プール**: asyncpgの接続プール（最大5接続）
- **トランザクション**: バッチ単位でコミット（全件失敗を防ぐ）

### データ整合性

- **重複排除**: PostgreSQLのid列はSQLiteと独立（AUTOINCREMENT）
- **順序保証**: start_time/event_timeでソート
- **アトミック更新**: トランザクション内でINSERT + synced_atフラグ更新

### 障害復旧

- **自動リトライ**: 指数バックオフ付き（最大5回）
- **同期ログ**: 成功/失敗を記録、監視・デバッグに活用
- **フラグ管理**: synced_atフラグで同期状態を永続化

### セキュリティ

- **接続文字列**: 環境変数経由でパスワード管理
- **SQLインジェクション対策**: asyncpgのプレースホルダー使用
- **ログ秘匿**: 接続URLをログに出力しない

---

## 将来的な拡張（Phase 3以降）

### リアルタイム同期

- **ストリーミング同期**: イベント発生時に即座にPostgreSQLへ送信
- **キューイング**: RabbitMQ/Redisを使用したメッセージキュー
- **WebSocket通知**: リアルタイム同期状態通知

### 双方向同期

- **PostgreSQL → SQLite**: 設定変更をローカルに反映
- **コンフリクト解決**: タイムスタンプベースの競合解決
- **マージロジック**: 複数ホストの同期

### 最適化

- **圧縮**: 大量データの転送時に圧縮
- **差分同期**: 変更検出とデルタ転送
- **並列化**: 複数テーブルの並行同期

### 監視・アラート

- **同期遅延監視**: 最終同期時刻の監視
- **エラーアラート**: 連続失敗時の通知
- **ダッシュボード**: Web UI上で同期状態可視化

---

## 参考リンク

- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [PostgreSQL Bulk Insert Best Practices](https://www.postgresql.org/docs/current/populate.html)

---

## 次のステップ

Phase 2.3実装開始後、以下の順で進めます：

1. PostgreSQLスキーマ拡張（sync_logs）
2. SQLiteスキーママイグレーション（synced_at）
3. DataSyncManager実装
4. collector統合
5. 統合テスト
6. ドキュメント更新

各ステップ完了後、動作確認とドキュメント更新を行います。
