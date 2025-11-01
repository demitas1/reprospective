# Reprospective 管理スクリプト

プロジェクトの起動・停止・データ管理を行うスクリプト集

## スクリプト一覧

### Docker管理スクリプト

#### start.sh
PostgreSQLコンテナを起動し、必要に応じてデータベースを初期化します。

```bash
./scripts/start.sh
```

**機能:**
- .envファイルが存在しない場合は自動作成
- Docker Composeでコンテナを起動
- PostgreSQLの起動を待機
- スキーマが未初期化の場合は自動初期化

### stop.sh
実行中のコンテナを停止します（データは保持）。

```bash
./scripts/stop.sh
```

**機能:**
- 実行中のコンテナを確認
- コンテナを停止（データボリュームは削除しない）

### reset-db.sh
PostgreSQLのデータベースを完全にリセットします。

```bash
./scripts/reset-db.sh
```

**機能:**
- 全テーブルとビューを削除
- スキーマを再初期化
- 確認プロンプトあり（`yes`入力が必要）

**⚠️ 警告:** PostgreSQL内の全データが削除されます

### clean-docker.sh
Dockerのコンテナ、ボリューム、ネットワークを完全に削除します。

```bash
./scripts/clean-docker.sh
```

**機能:**
- コンテナを停止・削除
- 永続化ボリュームを削除
- ネットワークを削除
- 確認プロンプトあり（`yes`入力が必要）

**⚠️ 警告:** データベースの全データが完全に削除されます（復元不可）

### clean-host.sh
host-agentのローカルSQLiteデータベースを削除します。

```bash
./scripts/clean-host.sh
```

**機能:**
- `host-agent/data/desktop_activity.db` を削除
- `host-agent/data/file_changes.db` を削除
- 関連するWAL/SHMファイルも削除
- 確認プロンプトあり（`yes`入力が必要）

**⚠️ 警告:** ローカルの全活動データが削除されます

### データ表示スクリプト

#### show-directories.sh
PostgreSQLデータベースから監視対象ディレクトリの一覧を表示します。

```bash
./scripts/show-directories.sh
```

**機能:**
- PostgreSQLから直接データ取得
- 日本語カラム名で見やすく表示
- 統計情報表示（合計、有効、無効の件数）
- 有効/無効状態を絵文字で表示

**出力例:**
```
 ID |       ディレクトリパス        |  状態   |     表示名
----+-------------------------------+---------+-----------------
  5 | /home/demitas/work/github.com | ✅ 有効 | work/github.com
  7 | /home/demitas/work/rakugaki   | ✅ 有効 | rakugaki

統計情報
合計: 2件
有効: 2件
無効: 0件
```

### API管理スクリプト

#### api-list-directories.sh
API経由で監視対象ディレクトリの一覧を取得・表示します。

```bash
./scripts/api-list-directories.sh           # 全ディレクトリ取得
./scripts/api-list-directories.sh --enabled  # 有効なディレクトリのみ取得
```

**機能:**
- 全ディレクトリまたは有効なディレクトリのみ取得
- jqがあれば見やすく整形表示
- カラー表示対応

#### api-add-directory.sh
新しい監視対象ディレクトリを追加します。

```bash
./scripts/api-add-directory.sh <ディレクトリパス> [表示名] [説明]
```

**例:**
```bash
./scripts/api-add-directory.sh /home/user/projects "プロジェクト" "開発用"
./scripts/api-add-directory.sh /home/user/Documents "ドキュメント"
./scripts/api-add-directory.sh /home/user/work
```

**機能:**
- 絶対パス自動変換（相対パス指定時）
- 重複チェック
- 詳細なエラーメッセージ表示

#### api-update-directory.sh
既存ディレクトリの情報を更新します（部分更新対応）。

```bash
./scripts/api-update-directory.sh <ID> [オプション]
```

**オプション:**
- `--path <新パス>`: ディレクトリパスを変更
- `--name <表示名>`: 表示名を変更
- `--desc <説明>`: 説明を変更
- `--enable`: 有効化
- `--disable`: 無効化

**例:**
```bash
./scripts/api-update-directory.sh 1 --name "新しい名前"
./scripts/api-update-directory.sh 1 --desc "新しい説明"
./scripts/api-update-directory.sh 1 --name "プロジェクト" --desc "開発用ディレクトリ"
./scripts/api-update-directory.sh 1 --disable
```

**機能:**
- 更新前後の情報表示
- 複数項目同時更新可能
- 絶対パス自動変換

#### api-toggle-directory.sh
ディレクトリの有効/無効を切り替えます。

```bash
./scripts/api-toggle-directory.sh <ID>
```

**例:**
```bash
./scripts/api-toggle-directory.sh 1
```

**機能:**
- ワンクリックで有効/無効切り替え
- 現在の状態を表示
- 切り替え後のメッセージ表示

#### api-delete-directory.sh
ディレクトリを削除します（確認プロンプトあり）。

```bash
./scripts/api-delete-directory.sh <ID>
```

**例:**
```bash
./scripts/api-delete-directory.sh 1
```

**機能:**
- 削除前に対象情報を表示
- 確認プロンプト（`yes`入力必須）
- 安全な削除操作

### host-agent管理スクリプト

#### start-agent.sh
host-agentのコレクターをバックグラウンドで起動します。

```bash
./scripts/start-agent.sh [オプション]
```

**オプション:**
- `--all`: すべてのエージェントを起動（デフォルト）
- `--desktop`: デスクトップモニターのみ起動
- `--files`: ファイルシステムウォッチャーのみ起動

**機能:**
- バックグラウンドで起動（`nohup`使用）
- PIDファイル管理（`.pids/`ディレクトリ）
- ログファイル出力（`logs/`ディレクトリ）
- 既に実行中の場合はスキップ
- **ファイルウォッチャーは`filesystem_watcher_v2.py`（PostgreSQL連携版）を使用**

**例:**
```bash
./scripts/start-agent.sh              # すべて起動
./scripts/start-agent.sh --desktop    # デスクトップのみ
./scripts/start-agent.sh --files      # ファイルウォッチャーv2のみ
```

**注意:** ファイルウォッチャーはPostgreSQL連携版（v2）を使用します。監視対象ディレクトリはPostgreSQLから動的に取得され、API経由で変更可能です。

#### stop-agent.sh
実行中のhost-agentコレクターを停止します。

```bash
./scripts/stop-agent.sh [オプション]
```

**オプション:**
- `--all`: すべてのエージェントを停止（デフォルト）
- `--desktop`: デスクトップモニターのみ停止
- `--files`: ファイルシステムウォッチャーのみ停止

**機能:**
- 正常終了（SIGTERM送信）
- タイムアウト時は強制終了（SIGKILL）
- PIDファイルのクリーンアップ

**例:**
```bash
./scripts/stop-agent.sh               # すべて停止
./scripts/stop-agent.sh --desktop     # デスクトップのみ
./scripts/stop-agent.sh --files       # ファイルウォッチャーのみ
```

## 使用例

### 初回起動

```bash
# 1. PostgreSQLコンテナを起動（自動的にDBも初期化）
./scripts/start.sh

# 2. host-agentを起動
./scripts/start-agent.sh
```

### 完全クリーンアップ

すべてをゼロから始める場合：

```bash
# 1. Dockerリソースを完全削除
./scripts/clean-docker.sh

# 2. host-agentのローカルデータを削除
./scripts/clean-host.sh

# 3. 再起動
./scripts/start.sh
```

### 日常的な使用

```bash
# コンテナとエージェントを起動
./scripts/start.sh
./scripts/start-agent.sh

# 作業...

# エージェントとコンテナを停止
./scripts/stop-agent.sh
./scripts/stop.sh
```

### API経由での監視ディレクトリ管理

`filesystem_watcher_v2.py`を使用している場合、監視対象ディレクトリをAPI経由で動的に変更できます。変更は60秒以内に自動的に反映されます。

```bash
# ディレクトリ一覧確認
./scripts/api-list-directories.sh

# 新しいディレクトリを追加（60秒以内に監視開始）
./scripts/api-add-directory.sh /home/user/projects "プロジェクト" "開発用"

# ディレクトリ情報を更新
./scripts/api-update-directory.sh 1 --name "新しい名前"

# 一時的に無効化（60秒以内に監視停止）
./scripts/api-toggle-directory.sh 1

# 再度有効化（60秒以内に監視再開）
./scripts/api-toggle-directory.sh 1

# ディレクトリを削除
./scripts/api-delete-directory.sh 1
```

**自動同期:** `filesystem_watcher_v2.py`は60秒間隔でPostgreSQLから設定を取得し、監視対象を自動的に追加・削除します。

### エージェントのログ確認

```bash
# ログをリアルタイム表示
tail -f host-agent/logs/desktop-monitor.log
tail -f host-agent/logs/filesystem-watcher.log

# 収集データを確認
cd host-agent
source venv/bin/activate
python scripts/show_sessions.py
python scripts/show_file_events.py
```

### データベースのみリセット

PostgreSQLのデータのみ削除してスキーマを再初期化：

```bash
./scripts/reset-db.sh
```

## トラブルシューティング

### "Permission denied" エラー

スクリプトに実行権限がない場合：

```bash
chmod +x scripts/*.sh
```

### コンテナが起動しない

ログを確認：

```bash
docker compose logs database
```

### データベース接続エラー

接続確認：

```bash
docker compose exec database psql -U reprospective_user -d reprospective
```

## 注意事項

- すべてのスクリプトはプロジェクトルートから実行可能です
- データ削除系のスクリプトは確認プロンプトが表示されます
- `yes` と正確に入力しないとキャンセルされます
- スクリプトは `set -e` を使用しているため、エラー時に自動停止します

## ライセンス

Apache License 2.0
