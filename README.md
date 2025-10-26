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

Dockerコンテナとして動作するマイクロサービス（Phase 2以降で実装予定）：

- **database** 🚧: PostgreSQL（次回実装予定）
- **collector-service** 📋: GitHub/SNS等のAPI経由データ収集（計画中）
- **ai-analyzer** 📋: AI分析エンジン（要約、分類、進捗推測）（計画中）
- **api-gateway** 📋: APIゲートウェイ（計画中）
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

#### 4. PostgreSQLサービスの起動（Phase 2）

```bash
# プロジェクトルートに戻る
cd ..

# PostgreSQLコンテナを起動
docker-compose up -d database

# 起動確認
docker-compose ps
docker-compose logs database
```

接続確認：

```bash
# psqlで接続テスト
docker-compose exec database psql -U reprospective_user -d reprospective

# または、ホストから直接接続
psql -h localhost -p 5432 -U reprospective_user -d reprospective
```

## 使い方

### デスクトップモニターの起動

```bash
cd host-agent
source venv/bin/activate
python collectors/linux_x11_monitor.py
```

### ファイルシステムウォッチャーの起動

```bash
cd host-agent
source venv/bin/activate
python collectors/filesystem_watcher.py
```

### データの確認

```bash
# デスクトップセッション表示
python scripts/show_sessions.py

# ファイルイベント表示
python scripts/show_file_events.py
```

詳細は [`host-agent/README.md`](./host-agent/README.md) を参照してください。

## 開発

### ディレクトリ構成

```
reprospective/
├── CLAUDE.md                      # プロジェクト指示書
├── README.md                      # このファイル
├── docs/                          # ドキュメント
│   ├── software_idea-ai_assited_todo.md  # 企画書
│   └── design/                    # 設計ドキュメント
├── host-agent/                    # ✅ ホスト環境エージェント（実装済み）
│   ├── collectors/                # データ収集コンポーネント
│   │   ├── linux_x11_monitor.py   # デスクトップモニター
│   │   └── filesystem_watcher.py  # ファイルシステム監視
│   ├── common/                    # 共通モジュール
│   │   ├── models.py              # データモデル
│   │   └── database.py            # データベース操作
│   ├── config/                    # 設定ファイル
│   ├── data/                      # ローカルデータベース
│   ├── scripts/                   # デバッグツール
│   └── README.md
├── services/                      # 🚧 Dockerコンテナサービス（Phase 2以降）
│   ├── database/                  # PostgreSQL
│   ├── collector-service/         # API経由データ収集
│   ├── ai-analyzer/               # AI分析エンジン
│   ├── api-gateway/               # APIゲートウェイ
│   └── web-ui/                    # Webフロントエンド
└── shared/                        # 🚧 共有ライブラリ（Phase 2以降）
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

**Phase 1 - 基盤実装フェーズ** (2025-10-25時点)

### ✅ 実装済み

- **DesktopActivityMonitor** (Linux X11): デスクトップアクティビティ追跡
- **FileSystemWatcher**: ファイル変更監視
- **データベース分離アーキテクチャ**: コレクター別独立SQLite DB
- **設定管理**: YAML設定ファイル
- **デバッグツール**: セッション/イベント表示、DB初期化スクリプト

詳細: [`host-agent/README.md`](./host-agent/README.md)

### 🚧 次回実装予定 (Phase 2)

- PostgreSQL同期機能（ローカルキャッシュ+中央DB）
- Docker Compose環境構築
- Web UIプロトタイプ

### 📋 計画中

- BrowserActivityParser（ブラウザ活動解析）
- GitHubMonitor（コミット・PR追跡）
- SNSMonitor（Bluesky投稿収集）
- AI分析エンジン

## 関連ドキュメント

- [企画書](./docs/software_idea-ai_assited_todo.md) - プロジェクトの背景と詳細な機能説明
