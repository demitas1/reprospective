# CLAUDE.md

回答はすべて日本語で行ってください
ソースコード中のコメント、ユーザー向けメッセージ文字列は日本語で書く
ドキュメントも指定がない場合は日本語で作成
コーディングはSOLID原則に従い、簡潔で拡張しやすいものにする
ディレクトリ名、ファイル名は英語を使用

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Reprospective** is an AI-assisted TODO and activity management system designed to reduce the manual input burden of traditional TODO apps. The core concept is "from recording to retrospection" - the system automatically collects user activities and uses AI to help visualize "what was done" rather than requiring manual logging.

---

## Project Status

**Phase 2.1 - API Gateway & Database Integration** (2025-10-26時点)

### ✅ Phase 1 完了 (2025-10-25)

#### host-agent/
デスクトップアクティビティ監視エージェント（Linux X11環境）

- **DesktopActivityMonitor**: アクティブウィンドウ追跡とセッション記録
- **FileSystemWatcher**: ファイル変更監視とイベント記録
- **データベース分離アーキテクチャ**: コレクター別独立DB（スレッド競合回避）
- **設定管理**: YAML形式の設定ファイル
- **デバッグツール**: セッション/イベント表示、DB初期化スクリプト

詳細: `host-agent/README.md`, `docs/design/`

#### infrastructure/ (基盤)
- **Docker Compose**: PostgreSQL 16コンテナ構成
- **管理スクリプト**: コンテナ起動・停止、DB初期化、クリーンアップ
- **PostgreSQLスキーマ**: desktop_activity_sessions, file_change_eventsテーブル

詳細: `services/database/README.md`, `scripts/README.md`

### ✅ Phase 2.1 API Gateway 完了（2025-10-31）

#### services/api-gateway (FastAPI)
**実装完了内容:**
- ✅ PostgreSQL `monitored_directories` テーブル作成
- ✅ FastAPI RESTful API実装（CRUD操作完全動作）
- ✅ Pydanticモデルとバリデーション実装
- ✅ Docker Compose統合、ヘルスチェック実装
- ✅ Swagger UI対応（http://localhost:8800/docs）
- ✅ エラーハンドリング、ログ記録

**動作確認済み:**
- ✅ 全CRUD操作（GET/POST/PUT/DELETE/PATCH）
- ✅ バリデーション（絶対パス、重複チェック）
- ✅ データベース接続プール管理
- ✅ 日本語データ処理

詳細: `services/api-gateway/README.md`

### 🚧 Phase 2.1+ 次回実装予定

#### host-agent設定同期機能
- PostgreSQLから監視ディレクトリ設定を取得
- FileSystemWatcherへの統合（動的設定変更）
- YAML→PostgreSQL移行機能
- フォールバック機能（DB接続失敗時）

詳細: `docs/design/phase2_implementation_plan.md`

### 📋 Phase 2.2以降（計画中）

#### services/web-ui (React 19 + Vite)
- 監視ディレクトリ設定UI
- 活動データ可視化
- AI分析結果表示
- 対話的レビューインターフェース

#### host-agent/ (追加コレクター)
- **BrowserActivityParser**: ブラウザ活動解析
- **GitHubMonitor**: コミット・PR追跡（API経由）
- **SNSMonitor**: Bluesky等のSNS投稿収集

#### services/ (その他コンテナサービス)
- **ai-analyzer**: AI分析エンジン
- **collector-service**: API経由データ収集
- **認証・セキュリティ**: JWT認証、CORS設定

#### shared/
- データモデル定義
- ユーティリティライブラリ

詳細: `docs/software_idea-ai_assited_todo.md`, `docs/design/phase2_implementation_plan.md`

---

## Architecture

### Current Architecture (Phase 2.1)

```
reprospective/
├── host-agent/                           # ✅ ホスト環境エージェント
│   ├── collectors/
│   │   ├── linux_x11_monitor.py          ✅ Linux X11デスクトップモニター
│   │   └── filesystem_watcher.py         ✅ ファイルシステム監視
│   ├── common/
│   │   ├── models.py                     ✅ データモデル
│   │   └── database.py                   ✅ 分離されたDB操作クラス
│   ├── config/
│   │   └── config.yaml                   ✅ 設定ファイル
│   ├── scripts/
│   │   ├── show_sessions.py              ✅ セッション表示
│   │   ├── show_file_events.py           ✅ ファイルイベント表示
│   │   └── reset_database.py             ✅ DB初期化
│   └── data/
│       ├── desktop_activity.db           ✅ デスクトップアクティビティDB
│       └── file_changes.db               ✅ ファイル変更イベントDB
│
├── services/                             # Dockerサービス
│   ├── database/                         ✅ PostgreSQL 16
│   │   ├── init/
│   │   │   ├── 01_init_schema.sql        ✅ 初期スキーマ
│   │   │   └── 02_add_monitored_directories.sql  ✅ 監視ディレクトリテーブル
│   │   ├── conf/postgresql.conf          ✅ PostgreSQL設定
│   │   └── README.md                     ✅ ドキュメント
│   ├── api-gateway/                      ✅ FastAPI (実装完了)
│   │   ├── app/
│   │   │   ├── main.py                   ✅ FastAPIアプリケーション
│   │   │   ├── config.py                 ✅ 設定管理
│   │   │   ├── database.py               ✅ DB接続管理
│   │   │   ├── models/                   ✅ Pydanticモデル
│   │   │   └── routers/                  ✅ APIエンドポイント
│   │   ├── Dockerfile                    ✅ Dockerイメージ
│   │   ├── requirements.txt              ✅ 依存パッケージ
│   │   └── README.md                     ✅ ドキュメント
│   ├── ai-analyzer/                      📋 AI分析エンジン（計画中）
│   └── web-ui/                           📋 React 19 + Vite（計画中）
│
├── scripts/                              ✅ 管理スクリプト
│   ├── start.sh                          ✅ PostgreSQL起動
│   ├── stop.sh                           ✅ PostgreSQL停止
│   ├── reset-db.sh                       ✅ DB初期化
│   ├── clean-docker.sh                   ✅ Docker完全クリーンアップ
│   ├── clean-host.sh                     ✅ host-agent DBクリーンアップ
│   ├── start-agent.sh                    ✅ host-agent起動
│   ├── stop-agent.sh                     ✅ host-agent停止
│   └── README.md                         ✅ スクリプトドキュメント
│
├── docs/design/                          # 設計ドキュメント
│   └── phase2_implementation_plan.md     ✅ Phase 2実装計画
│
├── docker-compose.yml                    ✅ Docker Compose設定
└── env.example                           ✅ 環境変数テンプレート
```

### Future Architecture (Phase 2.2+)

```
reprospective/
├── services/
│   ├── web-ui/                           📋 React 19 + Vite
│   │   ├── src/
│   │   │   ├── components/               # React コンポーネント
│   │   │   ├── pages/                    # ページコンポーネント
│   │   │   └── api/                      # API クライアント
│   │   └── Dockerfile
│   └── ai-analyzer/                      📋 AI分析エンジン
│       └── analyzers/                    # 各種分析ロジック
└── shared/                               📋 共有ライブラリ
    ├── models/                           # 共通データモデル
    └── utils/                            # ユーティリティ
```

---

## Key Technical Decisions

### Database Strategy

- **Phase 1**: コレクター別独立SQLite
  - `data/desktop_activity.db`: デスクトップアクティビティ
  - `data/file_changes.db`: ファイル変更イベント
  - スレッド競合を回避、各コレクターが独立動作

- **Phase 2**: PostgreSQL + SQLiteローカルキャッシュ
  - 各ローカルDBからPostgreSQLへバッチ同期
  - オフライン耐性、高可用性を実現

詳細: `docs/design/technical_decision-database_separation.md`

### Cross-Platform Support

- **Phase 1**: Linux X11のみ
- **Phase 2+**: OS固有実装 + 共通インターフェース
  - Linux: X11（実装済み）、Wayland（計画）
  - Windows: `pywin32`（計画）
  - macOS: `AppKit`（計画）

各OSで最適化された実装を提供し、データモデルとDB操作を共通化。

---

## Development Workflow

### 環境セットアップ

```bash
# 1. 環境変数設定
cp env.example .env
vim .env  # パスワード等を設定

# 2. PostgreSQLコンテナ起動
./scripts/start.sh

# 3. host-agent仮想環境セットアップ
cd host-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 日常的な開発フロー

```bash
# PostgreSQL起動
./scripts/start.sh

# host-agentをバックグラウンドで起動
./scripts/start-agent.sh

# 作業...

# データ確認
cd host-agent
source venv/bin/activate
python scripts/show_sessions.py             # セッション表示
python scripts/show_file_events.py          # ファイルイベント表示

# 停止
./scripts/stop-agent.sh
./scripts/stop.sh
```

### host-agent個別起動（開発・デバッグ用）

```bash
cd host-agent
source venv/bin/activate

# コレクター個別起動（フォアグラウンド）
python collectors/linux_x11_monitor.py      # デスクトップ監視
python collectors/filesystem_watcher.py      # ファイル監視

# データベース初期化
python scripts/reset_database.py            # 全DB削除
python scripts/reset_database.py --desktop  # デスクトップDBのみ
python scripts/reset_database.py --files    # ファイルDBのみ
```

### データ管理

```bash
# PostgreSQLデータベースをリセット
./scripts/reset-db.sh

# host-agentローカルDBをクリア
./scripts/clean-host.sh

# Docker環境を完全クリーンアップ
./scripts/clean-docker.sh
```

### テスト方針

- 現在は手動テスト
- データ確認: `host-agent/scripts/show_sessions.py`, `show_file_events.py`
- クリーンテスト: `scripts/clean-*.sh`

---

## 実装履歴

### 2025-10-31: Phase 2.1 API Gateway完了

**実装内容:**
- **FastAPI API Gateway**: 監視ディレクトリ管理CRUD API完全実装
- **PostgreSQLテーブル**: `monitored_directories`テーブル作成
- **Pydanticモデル**: バリデーション、型チェック実装
- **Docker統合**: docker-compose.ymlに統合、ヘルスチェック実装
- **Swagger UI**: 自動APIドキュメント生成
- **エラーハンドリング**: 適切なHTTPステータスコード、日本語エラーメッセージ

**技術スタック:**
- FastAPI 0.115.0
- asyncpg 0.29.0 (PostgreSQL非同期クライアント)
- Pydantic v2 (バリデーション)
- uvicorn (ASGIサーバー)

**動作確認:**
- 全エンドポイント正常動作（GET/POST/PUT/DELETE/PATCH）
- バリデーション機能確認（絶対パス、重複チェック）
- Swagger UI確認（http://localhost:8800/docs）

**次のステップ:**
host-agent設定同期機能（PostgreSQLから設定取得、動的監視対象変更）

### 2025-10-26: Phase 2基盤構築（PostgreSQL + 管理スクリプト）

**実装内容:**
- **PostgreSQL 16コンテナ**: Docker Compose設定、スキーマ初期化SQL
- **管理スクリプト**: コンテナ起動・停止、DB初期化、クリーンアップ（7スクリプト）
- **host-agent管理**: バックグラウンド起動・停止スクリプト（PID管理、個別起動対応）
- **ドキュメント**: `services/database/README.md`, `scripts/README.md`
- **Phase 2実装計画**: `docs/design/phase2_implementation_plan.md`作成

**技術的決定:**
- Docker Compose v2使用（`docker compose`コマンド）
- PostgreSQLヘルスチェック: `pg_isready`で起動待機
- スクリプトに確認プロンプト追加（破壊的操作の安全性向上）
- PIDファイル管理でプロセス重複防止

**次のステップ:**
Phase 2.1実装 - FastAPI API Gateway + monitored_directoriesテーブル

### 2025-10-25: Phase 1完了（データベース分離アーキテクチャ実装）

**課題:**
- 複数コレクターが単一SQLiteを共有するとスレッド競合が発生
- `check_same_thread=False`だけでは根本解決にならない

**解決策:**
- コレクター別に独立したSQLiteデータベースを使用
- `DesktopActivityDatabase`, `FileChangeDatabase`クラスに分離
- 各DBが独立して動作、競合なし

**実装内容:**
- `common/database.py`: 2つの専用DBクラスに分離
- 設定ファイル: DB パスを個別指定
- デバッグスクリプト: 各DB対応に更新
- 設計書: `docs/design/technical_decision-database_separation.md`

---

## Key Design Principles

1. **段階的実装**: まず動くものを作り、徐々に拡張
2. **単一責任**: 各DBは一つのコレクターのみを担当（SRP）
3. **オフライン耐性**: ローカルキャッシュ+バッチ同期
4. **SOLID principles**: 簡潔で拡張しやすいコード設計

---

## Documentation Structure

```
docs/
├── software_idea-ai_assited_todo.md                      # 企画書（日本語）
└── design/                                               # 設計ドキュメント
    ├── host_agent-desktop_activity_monitor.md            # DesktopActivityMonitor設計
    ├── host_agent-filesystem_watcher.md                  # FileSystemWatcher設計
    ├── technical_decision-database_separation.md         # DB分離アーキテクチャ
    └── phase2_implementation_plan.md                     # Phase 2実装計画
```

設計ドキュメントは概要のみ記載。詳細実装はソースコードとREADMEを参照。

---

## Quick Reference

### よく使うコマンド

```bash
# 環境起動
./scripts/start.sh           # PostgreSQL起動
./scripts/start-agent.sh     # host-agent起動

# データ確認
cd host-agent && source venv/bin/activate
python scripts/show_sessions.py 20         # 最新20セッション
python scripts/show_file_events.py 50      # 最新50ファイルイベント

# 環境停止
./scripts/stop-agent.sh      # host-agent停止
./scripts/stop.sh            # PostgreSQL停止

# データクリーンアップ
./scripts/reset-db.sh        # PostgreSQLデータベースリセット
./scripts/clean-host.sh      # host-agentローカルDBクリア
./scripts/clean-docker.sh    # Docker完全クリーンアップ
```

### 主要ファイル

**host-agent:**
- `host-agent/collectors/linux_x11_monitor.py`: デスクトップモニター本体
- `host-agent/collectors/filesystem_watcher.py`: ファイルシステムウォッチャー
- `host-agent/common/models.py`: データモデル
- `host-agent/common/database.py`: SQLite操作
- `host-agent/config/config.yaml`: 設定ファイル

**infrastructure:**
- `docker-compose.yml`: Docker Compose設定
- `services/database/init/01_init_schema.sql`: PostgreSQLスキーマ
- `scripts/*.sh`: 管理スクリプト
- `docs/design/phase2_implementation_plan.md`: Phase 2実装計画

---

## Next Steps - Phase 2.1実装

**次回セッションで実装予定:**

1. **PostgreSQL `monitored_directories` テーブル追加**
   - マイグレーションSQLの作成
   - スキーマ更新

2. **FastAPI API Gateway実装**
   - `services/api-gateway/` ディレクトリ作成
   - FastAPI基本構成（main.py, requirements.txt）
   - monitored_directories CRUD APIエンドポイント
   - Dockerfile & docker-compose.yml更新

3. **host-agent設定読み込み機能拡張**
   - `filesystem_watcher.py`: PostgreSQLからディレクトリ設定読み込み
   - YAML→PostgreSQLフォールバック実装
   - asyncpg依存追加

4. **動作確認**
   - curlコマンドでAPI操作確認
   - host-agentがPostgreSQL設定を読み込むことを確認

詳細: `docs/design/phase2_implementation_plan.md`

---

## License

Apache License 2.0
