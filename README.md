# Reprospective

AI支援によるToDo管理・活動記録システム

## 概要

Reprospectiveは、ユーザーの日常的な作業活動を自動的に収集・分析し、AIの支援により「何をしたか」を可視化するシステムです。従来のToDo管理アプリケーションの手動入力の負担を最小限に抑え、正確な活動記録と未来の計画作成を支援します。

### コンセプト

「記録する」から「振り返る」へ。

ユーザーは作業に集中し、システムが自動的に活動を追跡。一日の終わりに、AIとの対話を通じて活動を振り返り、明日への計画を立てます。

## 主要機能

- **自動活動収集**: GitHub、SNS、ファイルシステム、デスクトップ活動の自動追跡
- **AI分析**: 収集データをAIが自動的に分析・要約・分類
- **対話的レビュー**: 自然言語での対話を通じた活動の確認と修正
- **計画作成支援**: 過去の実績に基づく現実的な計画の立案
- **活動可視化**: 時間の使い方、カテゴリ別配分、トレンドのグラフ表示
- **日誌生成**: Markdown形式での活動記録の自動保存

## アーキテクチャ

本システムは、ホスト環境で動作するエージェントとDockerコンテナで動作するサービス群で構成されています。

### ホストエージェント (`host-agent/`)

ホストシステムのリソースに直接アクセスするコンポーネント：

- **DesktopActivityMonitor** ✅: デスクトップアクティビティの追跡（Linux X11対応）
- **FileSystemWatcher** ✅: ファイルシステムの変更監視
- **BrowserActivityParser** 🚧: ブラウザ活動の解析（計画中）

### コンテナサービス (`services/`)

Dockerコンテナとして動作するマイクロサービス：

- **database** ✅: PostgreSQL 16（実装完了）
- **api-gateway** ✅: FastAPI RESTful API（実装完了）
- **collector-service** 📋: GitHub/SNS等のAPI経由データ収集（計画中）
- **ai-analyzer** 📋: AI分析エンジン（要約、分類、進捗推測）（計画中）
- **web-ui** 📋: Webフロントエンド（レビュー、計画、可視化）（計画中）

### 共有ライブラリ (`shared/`)

ホストエージェントとサービス間で共有するコード（Phase 2以降で実装予定）：

- データモデル定義 📋
- ファイルタイプ分類 📋
- コンテンツ解析ユーティリティ 📋

## セットアップ

### 前提条件

**Phase 1 (host-agent)**
- Python 3.10以上
- Linux X11環境（デスクトップモニター用）
- `xdotool`、`xprop`コマンド

**Phase 2 (services)**
- Docker & Docker Compose

### インストール手順

#### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/reprospective.git
cd reprospective
```

#### 2. 環境変数の設定

```bash
cp env.example .env
# .env を編集してデータベースパスワードなどを設定
vim .env
```

#### 3. ホストエージェントのセットアップ

```bash
cd host-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

システムコマンドのインストール（Linux）：

```bash
# Ubuntu/Debian
sudo apt install xdotool x11-utils

# Fedora
sudo dnf install xdotool xorg-x11-utils

# Arch Linux
sudo pacman -S xdotool xorg-xprop
```

設定ファイルの編集：

```bash
# config/config.yaml を編集して監視対象ディレクトリを設定
vim config/config.yaml
```

#### 4. PostgreSQLサービスの起動

```bash
# プロジェクトルートに戻る
cd ..

# PostgreSQLコンテナを起動（自動的にスキーマ初期化）
./scripts/start.sh

# 起動確認
docker compose ps
docker compose logs database
```

接続確認：

```bash
# psqlで接続テスト
docker compose exec database psql -U reprospective_user -d reprospective

# または、ホストから直接接続
psql -h localhost -p 5432 -U reprospective_user -d reprospective
```

## 使い方

### 推奨: 管理スクリプトを使用

```bash
# PostgreSQL起動
./scripts/start.sh

# host-agentをバックグラウンドで起動（全コレクター）
./scripts/start-agent.sh

# データ確認
cd host-agent && source venv/bin/activate
python scripts/show_sessions.py          # デスクトップセッション表示
python scripts/show_file_events.py       # ファイルイベント表示

# 停止
./scripts/stop-agent.sh                  # host-agent停止
./scripts/stop.sh                        # PostgreSQL停止
```

### 個別起動（開発・デバッグ用）

デスクトップモニターの起動（フォアグラウンド）:

```bash
cd host-agent
source venv/bin/activate
python collectors/linux_x11_monitor.py
```

ファイルシステムウォッチャーの起動（フォアグラウンド）:

```bash
cd host-agent
source venv/bin/activate
python collectors/filesystem_watcher.py
```

### 管理スクリプト詳細

管理スクリプトの詳細な使い方は [`scripts/README.md`](./scripts/README.md) を参照してください。

host-agentの詳細は [`host-agent/README.md`](./host-agent/README.md) を参照してください。

## 開発

### ディレクトリ構成

```
reprospective/
├── CLAUDE.md                      # プロジェクト指示書
├── README.md                      # このファイル
├── docker-compose.yml             # ✅ Docker Compose設定
├── env.example                    # ✅ 環境変数テンプレート
├── docs/                          # ドキュメント
│   ├── software_idea-ai_assited_todo.md  # 企画書
│   └── design/                    # 設計ドキュメント
│       ├── host_agent-desktop_activity_monitor.md
│       ├── host_agent-filesystem_watcher.md
│       ├── technical_decision-database_separation.md
│       └── phase2_implementation_plan.md  # ✅ Phase 2実装計画
├── scripts/                       # ✅ 管理スクリプト
│   ├── start.sh                   # PostgreSQL起動
│   ├── stop.sh                    # PostgreSQL停止
│   ├── reset-db.sh                # データベースリセット
│   ├── clean-docker.sh            # Docker完全クリーンアップ
│   ├── clean-host.sh              # host-agent DBクリア
│   ├── start-agent.sh             # host-agent起動
│   ├── stop-agent.sh              # host-agent停止
│   └── README.md
├── host-agent/                    # ✅ ホスト環境エージェント
│   ├── collectors/                # データ収集コンポーネント
│   │   ├── linux_x11_monitor.py   # デスクトップモニター
│   │   └── filesystem_watcher.py  # ファイルシステム監視
│   ├── common/                    # 共通モジュール
│   │   ├── models.py              # データモデル
│   │   └── database.py            # データベース操作
│   ├── config/                    # 設定ファイル
│   │   └── config.yaml
│   ├── data/                      # ローカルデータベース
│   ├── scripts/                   # デバッグツール
│   └── README.md
├── services/                      # Dockerコンテナサービス
│   ├── database/                  # ✅ PostgreSQL 16
│   │   ├── init/                  # スキーマ初期化SQL
│   │   ├── conf/                  # PostgreSQL設定
│   │   └── README.md
│   ├── api-gateway/               # 🚧 FastAPI (Phase 2.1)
│   ├── collector-service/         # 📋 API経由データ収集（計画中）
│   ├── ai-analyzer/               # 📋 AI分析エンジン（計画中）
│   └── web-ui/                    # 📋 Webフロントエンド（Phase 2.2）
└── shared/                        # 📋 共有ライブラリ（計画中）
```

### 開発ガイドライン

- コーディングはSOLID原則に従い、簡潔で拡張しやすいコードを心がける
- コメントとドキュメントは日本語で記述
- ディレクトリ名、ファイル名は英語を使用
- コミット前に必ずテストを実行

詳細は [`CLAUDE.md`](./CLAUDE.md) を参照してください。

## ライセンス

Apache License 2.0 - 詳細は [LICENSE.txt](./LICENSE.txt) を参照


## プロジェクトステータス

**Phase 2.1 - API Gateway 完了** (2025-10-31時点)

### ✅ Phase 1 完了 (2025-10-25)

- **DesktopActivityMonitor** (Linux X11): デスクトップアクティビティ追跡
- **FileSystemWatcher**: ファイル変更監視
- **データベース分離アーキテクチャ**: コレクター別独立SQLite DB
- **設定管理**: YAML設定ファイル
- **デバッグツール**: セッション/イベント表示、DB初期化スクリプト

詳細: [`host-agent/README.md`](./host-agent/README.md)

### ✅ Phase 2基盤 完了 (2025-10-26)

- **PostgreSQL 16コンテナ**: Docker Compose設定、スキーマ初期化
- **管理スクリプト**: コンテナ・host-agent起動/停止、データクリーンアップ（7スクリプト）
- **ドキュメント**: 管理スクリプトREADME、PostgreSQL設定ガイド

詳細: [`services/database/README.md`](./services/database/README.md), [`scripts/README.md`](./scripts/README.md)

### ✅ Phase 2.1 API Gateway 完了 (2025-10-31)

- **API Gateway** (FastAPI): 監視ディレクトリ設定のCRUD API実装完了
- **PostgreSQL統合**: `monitored_directories`テーブル作成、CRUD操作完全動作
- **RESTful API**: GET/POST/PUT/DELETE/PATCH エンドポイント実装
- **Swagger UI**: http://localhost:8800/docs でAPIドキュメント閲覧可能
- **Docker統合**: docker-compose.ymlに統合、自動起動・ヘルスチェック対応
- **バリデーション**: 絶対パスチェック、重複チェック、エラーハンドリング完備

詳細: [`services/api-gateway/README.md`](./services/api-gateway/README.md)

**動作確認済みエンドポイント:**
```bash
# ヘルスチェック
GET  /health              # API稼働状態確認
GET  /health/db           # データベース接続確認

# ディレクトリ管理
GET    /api/v1/directories/              # 全ディレクトリ取得
GET    /api/v1/directories/{id}          # 特定ディレクトリ取得
POST   /api/v1/directories/              # ディレクトリ追加
PUT    /api/v1/directories/{id}          # ディレクトリ更新
DELETE /api/v1/directories/{id}          # ディレクトリ削除
PATCH  /api/v1/directories/{id}/toggle   # 有効/無効切り替え
```

### 🚧 Phase 2.1+ 次回実装予定

- **host-agent設定同期**: PostgreSQLから監視ディレクトリを取得
- **FileSystemWatcher統合**: DB設定に基づく動的監視対象変更

### 📋 Phase 2.2以降 計画中

- **Web UI** (React 19 + Vite): 監視ディレクトリ設定UI、活動データ可視化
- **BrowserActivityParser**: ブラウザ活動解析
- **GitHubMonitor**: コミット・PR追跡
- **SNSMonitor**: Bluesky投稿収集
- **AI分析エンジン**: 活動データ分析・要約

## 関連ドキュメント

- [企画書](./docs/software_idea-ai_assited_todo.md) - プロジェクトの背景と詳細な機能説明
- [Phase 2実装計画](./docs/design/phase2_implementation_plan.md) - Phase 2.1/2.2の実装計画
- [host-agent README](./host-agent/README.md) - host-agentの詳細説明
- [PostgreSQL README](./services/database/README.md) - PostgreSQL設定とスキーマ
- [API Gateway README](./services/api-gateway/README.md) - FastAPI APIの使い方
- [管理スクリプト README](./scripts/README.md) - 管理スクリプトの使い方
