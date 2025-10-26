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

**例:**
```bash
./scripts/start-agent.sh              # すべて起動
./scripts/start-agent.sh --desktop    # デスクトップのみ
./scripts/start-agent.sh --files      # ファイルウォッチャーのみ
```

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
