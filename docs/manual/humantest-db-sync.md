# Phase 2.3 データベース同期機能 人間動作確認手順書

**作成日**: 2025-11-05
**対象**: Phase 2.3（SQLite → PostgreSQL データ同期機能）
**所要時間**: 2-4時間（データ収集時間を含む）

---

## 概要

この手順書では、host-agent群を数時間動作させてアクティビティデータを収集し、SQLiteからPostgreSQLへの同期が正常に機能していることを確認します。

---

## 前提条件

- ✅ Phase 2.3.1（環境変数管理の改善）が完了していること
- ✅ PostgreSQLコンテナが起動していること
- ✅ host-agentの仮想環境がセットアップ済みであること
- ✅ 環境変数（.env）が設定されていること

---

## 手順

### 準備: 環境のクリーンアップ

既存のデータをクリアして、新しいテストを開始します。

```bash
# プロジェクトルートに移動
cd /mnt/ext-ssd1/work/github.com/reprospective

# 1. PostgreSQLデータベースをリセット
./scripts/reset-db.sh

# 2. host-agentのローカルDBをクリア
./scripts/clean-host.sh

# 確認: データベースが空であることを確認
./scripts/show-sync-stats.sh
# → "テーブル 'sync_logs' にデータがありません" と表示されればOK
```

---

### ステップ1: PostgreSQLコンテナの起動確認

```bash
# PostgreSQL + API Gateway + Web UIを起動
./scripts/start.sh

# 接続確認
# → "✅ PostgreSQL is ready!" が表示されることを確認
```

**確認ポイント:**
- ✅ PostgreSQLが起動している（ポート6000）
- ✅ API Gatewayが起動している（ポート8800）
- ✅ Web UIが起動している（ポート3333）

---

### ステップ2: host-agentの起動

```bash
# host-agent（デスクトップモニター + ファイルウォッチャー）を起動
./scripts/start-agent.sh

# 起動確認
# → "✅ 起動完了 (2 エージェント)" が表示されることを確認
```

**確認ポイント:**
- ✅ デスクトップモニターが起動している
- ✅ ファイルシステムウォッチャーが起動している
- ✅ .envファイルの確認プロンプトが表示されない（.envが存在する）

**起動ログの確認:**

```bash
# デスクトップモニターのログ
tail -f host-agent/logs/desktop-monitor.log

# ファイルシステムウォッチャーのログ
tail -f host-agent/logs/filesystem-watcher.log
```

**期待されるログ内容:**
- `[INFO] .envファイルをロード: /mnt/ext-ssd1/work/github.com/reprospective/.env`
- `[INFO] データ同期マネージャーを初期化しました`
- `[INFO] バックグラウンド同期を開始しました`

---

### ステップ3: アクティビティデータの収集（2-4時間）

通常の作業を行いながら、host-agentにデータを収集させます。

**推奨活動:**
1. **デスクトップアクティビティ**:
   - 複数のアプリケーションを切り替える（ブラウザ、エディタ、ターミナル等）
   - 各アプリケーションで少なくとも5分以上作業
   - 合計10個以上のセッションを生成

2. **ファイル変更**:
   - 監視対象ディレクトリ内でファイルを作成・編集・削除
   - 複数のファイルタイプ（.py, .md, .txt等）を操作
   - 合計20個以上のファイルイベントを生成

**収集中の確認:**

```bash
# 5分ごとにローカルDBのデータを確認
cd host-agent
source venv/bin/activate

# デスクトップセッション数を確認
python scripts/show_sessions.py 10

# ファイルイベント数を確認
python scripts/show_file_events.py 20
```

**期待される結果:**
- セッション数が徐々に増加している
- ファイルイベント数が徐々に増加している

---

### ステップ4: 同期の確認（データ収集後）

2-4時間後、データ同期が正常に動作しているか確認します。

#### 4.1 同期統計の確認

```bash
# 同期ログを確認
./scripts/show-sync-stats.sh
```

**期待される出力:**

```
========================================
同期統計サマリー
========================================
最新10件の同期ログ:
ID | テーブル名              | 同期件数 | 失敗件数 | ステータス | 同期日時
---+-------------------------+----------+----------+------------+---------------------
 3 | desktop_activity_sessions|       10|         0| success    | 2025-11-05 15:30:00
 2 | desktop_activity_sessions|        8|         0| success    | 2025-11-05 15:25:00
 1 | desktop_activity_sessions|       12|         0| success    | 2025-11-05 15:20:00

テーブル別同期サマリー:
テーブル名              | 総同期件数 | 総失敗件数 | 最終同期日時
------------------------+------------+------------+---------------------
desktop_activity_sessions|         30|          0| 2025-11-05 15:30:00
file_change_events       |         45|          0| 2025-11-05 15:30:00
```

**確認ポイント:**
- ✅ `records_failed` が 0 であること
- ✅ `status` が `success` であること
- ✅ 最終同期日時が最近（5-10分以内）であること
- ✅ 総同期件数が予想通り（収集したデータ数とほぼ一致）

#### 4.2 PostgreSQLデータの直接確認

```bash
# PostgreSQLに接続
docker exec -it reprospective-database psql -U reprospective_user -d reprospective

# データベース内で以下のSQLを実行
```

**1. デスクトップアクティビティセッションの確認:**

```sql
-- セッション数を確認
SELECT COUNT(*) FROM desktop_activity_sessions;

-- 最新10件を表示
SELECT
    id,
    application_name,
    window_title,
    start_time,
    end_time,
    duration_seconds
FROM desktop_activity_sessions
ORDER BY start_time DESC
LIMIT 10;
```

**期待される結果:**
- セッション数が10件以上
- `application_name`, `window_title`が正しく記録されている
- `duration_seconds`が0以上

**2. ファイルイベントの確認:**

```sql
-- ファイルイベント数を確認
SELECT COUNT(*) FROM file_change_events;

-- 最新20件を表示
SELECT
    id,
    event_type,
    file_path,
    event_time,
    project_name
FROM file_change_events
ORDER BY event_time DESC
LIMIT 20;
```

**期待される結果:**
- ファイルイベント数が20件以上
- `event_type`（created, modified, deleted）が正しく記録されている
- `file_path`が正しいパスになっている

**3. 同期ログの確認:**

```sql
-- 同期ログ数を確認
SELECT COUNT(*) FROM sync_logs;

-- 最新10件を表示
SELECT
    id,
    table_name,
    records_synced,
    records_failed,
    status,
    sync_time
FROM sync_logs
ORDER BY sync_time DESC
LIMIT 10;
```

**期待される結果:**
- 同期ログが複数件存在する
- `records_failed`がすべて0
- `status`がすべて`success`

**PostgreSQLから退出:**

```sql
\q
```

#### 4.3 SQLiteローカルDBの確認

```bash
cd host-agent
source venv/bin/activate

# デスクトップアクティビティDBを確認
sqlite3 data/desktop_activity.db "SELECT COUNT(*) FROM desktop_activity_sessions WHERE synced_at IS NOT NULL;"

# ファイルイベントDBを確認
sqlite3 data/file_changes.db "SELECT COUNT(*) FROM file_change_events WHERE synced_at IS NOT NULL;"
```

**期待される結果:**
- `synced_at`フラグが付いたレコード数がPostgreSQLのレコード数と一致
- すべてのレコードが同期済みであること

---

### ステップ5: 同期の動作確認（リアルタイム）

新しいデータが5分以内にPostgreSQLに同期されることを確認します。

**5.1 新しいアクティビティを生成:**

```bash
# 新しいアプリケーションを起動（例: firefoxやchromeなど）
firefox &

# 5分間そのアプリケーションを使用
```

**5.2 SQLiteに新しいセッションが記録されているか確認:**

```bash
cd host-agent
source venv/bin/activate

# 最新のセッションを確認（synced_at列も表示）
sqlite3 data/desktop_activity.db "SELECT id, application_name, synced_at FROM desktop_activity_sessions ORDER BY start_time DESC LIMIT 5;"
```

**期待される結果:**
- 最新のセッションが記録されている
- `synced_at`が`NULL`または最近の日時

**5.3 5分後にPostgreSQLを確認:**

```bash
# 同期統計を確認
./scripts/show-sync-stats.sh

# PostgreSQLに直接接続して確認
docker exec -it reprospective-database psql -U reprospective_user -d reprospective -c "SELECT application_name, start_time FROM desktop_activity_sessions ORDER BY start_time DESC LIMIT 5;"
```

**期待される結果:**
- 新しいセッションがPostgreSQLに同期されている
- 同期統計に新しいログエントリが追加されている

---

### ステップ6: エラーケースのテスト（オプション）

#### 6.1 PostgreSQL停止時の動作確認

```bash
# PostgreSQLコンテナを停止
docker stop reprospective-database

# host-agentは動作し続けているか確認
tail -f host-agent/logs/desktop-monitor.log
# → エラーログが出るが、プロセスは停止しない

# 新しいアクティビティを生成
# → ローカルDBには記録されるが、PostgreSQLには同期されない

# PostgreSQLを再起動
docker start reprospective-database
./scripts/start.sh

# 5分後に同期が再開されているか確認
./scripts/show-sync-stats.sh
```

**期待される結果:**
- PostgreSQL停止中もhost-agentは動作し続ける
- PostgreSQL再起動後、未同期データが自動的に同期される

---

### ステップ7: 停止とクリーンアップ

```bash
# host-agentを停止
./scripts/stop-agent.sh

# PostgreSQLコンテナを停止（オプション）
./scripts/stop.sh
```

---

## チェックリスト

### 準備
- [ ] PostgreSQLコンテナが起動している
- [ ] host-agentが起動している
- [ ] .envファイルが設定されている

### データ収集
- [ ] 2-4時間の通常作業を実施
- [ ] 10個以上のデスクトップセッションを生成
- [ ] 20個以上のファイルイベントを生成

### 同期確認
- [ ] 同期統計でエラーがない（`records_failed = 0`）
- [ ] PostgreSQLにデータが正しく記録されている
- [ ] SQLiteの`synced_at`フラグが正しく設定されている
- [ ] リアルタイム同期（5分以内）が動作している

### エラーハンドリング（オプション）
- [ ] PostgreSQL停止時もhost-agentは動作し続ける
- [ ] PostgreSQL再起動後、未同期データが自動的に同期される

---

## トラブルシューティング

### 問題: 同期ログが表示されない

**原因:**
- host-agentが起動していない
- PostgreSQL接続エラー

**解決策:**

```bash
# host-agentのログを確認
tail -f host-agent/logs/desktop-monitor.log

# エラーメッセージを確認
# → "データ同期マネージャー初期化エラー" が出ていないか確認

# PostgreSQL接続確認
docker exec -it reprospective-database psql -U reprospective_user -d reprospective -c "SELECT 1;"
```

### 問題: `records_failed` が 0 以外

**原因:**
- PostgreSQLスキーマの不一致
- データ型変換エラー

**解決策:**

```bash
# 同期ログの詳細を確認
./scripts/show-sync-stats.sh

# PostgreSQLログを確認
docker logs reprospective-database | tail -n 50

# データベーススキーマを再初期化
./scripts/reset-db.sh
```

### 問題: 新しいデータが同期されない

**原因:**
- `synced_at`フラグが既に設定されている
- 同期間隔（5分）を待っていない

**解決策:**

```bash
# 最新のSQLiteデータを確認
cd host-agent
source venv/bin/activate
sqlite3 data/desktop_activity.db "SELECT id, application_name, synced_at FROM desktop_activity_sessions ORDER BY start_time DESC LIMIT 5;"

# 5分待ってから再確認
sleep 300
./scripts/show-sync-stats.sh
```

---

## 参考資料

- `docs/design/phase2_3_implementation_plan.md` - Phase 2.3実装計画
- `scripts/show-sync-stats.sh` - 同期統計表示スクリプト
- `host-agent/common/data_sync.py` - データ同期マネージャー実装
- `services/database/init/03_add_sync_logs.sql` - sync_logsテーブルスキーマ

---

**動作確認完了後、結果を記録してください:**

- 収集したセッション数: ______ 件
- 収集したファイルイベント数: ______ 件
- 同期成功数: ______ 件
- 同期失敗数: ______ 件
- 確認日時: __________
- 確認者: __________

