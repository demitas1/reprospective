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

- **FileSystemWatcher**: ファイルシステムの変更監視
- **DesktopActivityMonitor**: デスクトップアクティビティの追跡
- **BrowserActivityParser**: ブラウザ活動の解析

### コンテナサービス (`services/`)

Dockerコンテナとして動作するマイクロサービス：

- **collector-service**: GitHub/SNS等のAPI経由データ収集
- **database**: PostgreSQL等のデータベース
- **ai-analyzer**: AI分析エンジン（要約、分類、進捗推測）
- **api-gateway**: APIゲートウェイ
- **web-ui**: Webフロントエンド（レビュー、計画、可視化）

### 共有ライブラリ (`shared/`)

ホストエージェントとサービス間で共有するコード：

- データモデル定義
- ファイルタイプ分類
- コンテンツ解析ユーティリティ

## セットアップ

### 前提条件

- Python 3.10以上（host-agent用）
- Docker & Docker Compose（services用）
- Node.js 18以上（web-ui用）

### インストール手順

1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/reprospective.git
cd reprospective
```

2. 環境変数の設定

```bash
cp env.example .env
# .env を編集して必要な設定を記入
```

3. ホストエージェントのセットアップ

```bash
cd host-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. Dockerサービスの起動

```bash
docker-compose up -d
```

## 使い方

### ホストエージェントの起動

```bash
cd host-agent
source venv/bin/activate
python main.py
```

### Webインターフェースへのアクセス

ブラウザで `http://localhost:3000` を開く

### サービスの停止

```bash
docker-compose down
```

## 開発

### ディレクトリ構成

```
reprospective/
├── docs/                   # ドキュメント
├── host-agent/            # ホスト環境エージェント
├── services/              # Dockerコンテナサービス群
│   ├── collector-service/ # API経由データ収集
│   ├── database/          # データベース
│   ├── ai-analyzer/       # AI分析エンジン
│   ├── api-gateway/       # APIゲートウェイ
│   └── web-ui/            # Webフロントエンド
├── shared/                # 共有ライブラリ
├── docker-compose.yml     # サービスオーケストレーション
├── env.example            # 環境変数サンプル
└── Makefile              # 開発用コマンド
```

### 開発ガイドライン

- コーディングはSOLID原則に従い、簡潔で拡張しやすいコードを心がける
- コメントとドキュメントは日本語で記述
- ディレクトリ名、ファイル名は英語を使用
- コミット前に必ずテストを実行

詳細は [`CLAUDE.md`](./CLAUDE.md) を参照してください。

## ライセンス

Apache License 2.0 - 詳細は [LICENSE.txt](./LICENSE.txt) を参照

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## プロジェクトステータス

現在、実験的な実装フェーズです。各コンポーネントを順次実装中です。

## 関連ドキュメント

- [企画書](./docs/software_idea-ai_assited_todo.md) - プロジェクトの背景と詳細な機能説明
