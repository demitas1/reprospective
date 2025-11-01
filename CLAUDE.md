# CLAUDE.md

回答はすべて日本語で行ってください
ソースコード中のコメント、ユーザー向けメッセージ文字列は日本語で書く
ドキュメントも指定がない場合は日本語で作成
コーディングはSOLID原則に従い、簡潔で拡張しやすいものにする
ディレクトリ名、ファイル名は英語を使用
git commit は実行前に必ず確認を求める

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Reprospective** is an AI-assisted TODO and activity management system designed to reduce the manual input burden of traditional TODO apps. The core concept is "from recording to retrospection" - the system automatically collects user activities and uses AI to help visualize "what was done" rather than requiring manual logging.

---

## Project Status

**Phase 2.2 - Web UI ✅ 完了** (2025-11-01)

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

### ✅ Phase 2.1 API Gateway & 設定同期 完了（2025-10-31）

#### services/api-gateway (FastAPI)
**実装完了内容:**
- ✅ PostgreSQL `monitored_directories` テーブル作成
- ✅ FastAPI RESTful API実装（CRUD操作完全動作）
- ✅ Pydanticモデルとバリデーション実装
- ✅ Docker Compose統合、ヘルスチェック実装
- ✅ Swagger UI対応（http://localhost:8800/docs）
- ✅ エラーハンドリング、ログ記録
- ✅ API管理スクリプト（scripts/api-*.sh）

**動作確認済み:**
- ✅ 全CRUD操作（GET/POST/PUT/DELETE/PATCH）
- ✅ バリデーション（絶対パス、重複チェック）
- ✅ データベース接続プール管理
- ✅ 日本語データ処理

詳細: `services/api-gateway/README.md`

#### host-agent設定同期機能
**実装完了内容:**
- ✅ `common/config_sync.py`: PostgreSQL設定同期モジュール
- ✅ `collectors/filesystem_watcher_v2.py`: PostgreSQL連携版ウォッチャー
- ✅ 動的設定同期（60秒間隔）
- ✅ YAML→PostgreSQL自動移行機能
- ✅ フォールバック機能（DB接続失敗時はYAML使用）
- ✅ 非同期処理（asyncpg + asyncio）

**動作確認済み:**
- ✅ PostgreSQLからディレクトリ設定を自動取得
- ✅ ディレクトリ追加時の自動監視開始（60秒以内）
- ✅ ディレクトリ無効化時の自動監視停止（60秒以内）
- ✅ 初回起動時のYAML→PostgreSQL移行
- ✅ PostgreSQL接続失敗時のYAMLフォールバック

詳細: `host-agent/README.md`, `docs/design/phase2_1_implementation_plan.md`

### ✅ Phase 2.2 Web UI 完了（2025-11-01）

#### services/web-ui (React 19 + Vite)
**実装完了内容:**

**Step 1 & 2: プロジェクト基盤 & Docker化**
- ✅ Vite + React 19.2.0 + TypeScript プロジェクト構築
- ✅ Tailwind CSS v4 + Shadcn/ui セットアップ
- ✅ TypeScript パスエイリアス設定（`@/*`）
- ✅ React Query (TanStack Query v5)、Axios、Zod、React Hook Form インストール
- ✅ Dockerコンテナ化（Vite Dev Server使用）
- ✅ docker-compose.yml統合、ホットリロード動作確認
- ✅ 環境変数管理（services/web-ui/env.example）

**Step 3: API連携実装**
- ✅ 型定義（directory.ts）
- ✅ Zodバリデーションスキーマ（validators.ts）
- ✅ Axiosクライアント設定（api/client.ts, directories.ts）
- ✅ React Queryカスタムフック5個（useDirectories, useAdd, useUpdate, useDelete, useToggle）
- ✅ 楽観的更新実装（全ミューテーション）

**Step 4: コンポーネント実装**
- ✅ UIコンポーネント6個（button, dialog, input, label, switch, textarea）
- ✅ 共通コンポーネント2個（LoadingSpinner, ErrorMessage）
- ✅ レイアウトコンポーネント2個（Header, Layout）
- ✅ ディレクトリ管理コンポーネント5個（DirectoryCard, DirectoryList, Add/Edit/DeleteDialog）

**Step 5: アプリケーション統合**
- ✅ main.tsx: React Query Provider設定
- ✅ App.tsx: Layout + DirectoryList統合

**Step 6: 統合テスト**
- ✅ Docker環境動作確認
- ✅ コンテナ間通信テスト（web-ui → api-gateway）
- ✅ API Gateway接続テスト
- ✅ Vite Dev Server正常起動確認

**技術スタック:**
- React 19.2.0
- Vite 7.1.12
- TypeScript 5.9.3
- Tailwind CSS 4.1.16
- Shadcn/ui (New York style)
- TanStack Query v5
- Axios 1.7.9
- Zod 3.24.1
- React Hook Form 7.54.2

**動作確認済み:**
- ✅ Dockerコンテナビルド・起動成功
- ✅ http://localhost:3333 でアクセス可能
- ✅ ホットリロード機能動作確認
- ✅ Tailwind CSS v4 正常動作
- ✅ コンテナ間通信（web-ui → api-gateway）
- ✅ 全CRUD操作動作確認
- ✅ 楽観的更新動作確認

詳細: `docs/design/phase2_2_implementation_plan.md`, `docs/manual/humantest.md`

### 📋 Phase 2.3以降（計画中）

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

詳細: `docs/software_idea-ai_assited_todo.md`, `docs/design/phase2_2_implementation_plan.md`

---

## Architecture

### Current Architecture (Phase 2.2)

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
│   ├── web-ui/                           ✅ React 19 + Vite（実装完了）
│   │   ├── src/
│   │   │   ├── main.tsx                  ✅ エントリーポイント（React Query Provider）
│   │   │   ├── App.tsx                   ✅ アプリケーション統合
│   │   │   ├── components/
│   │   │   │   ├── ui/                   ✅ Shadcn/ui UIコンポーネント（6個）
│   │   │   │   ├── common/               ✅ 共通コンポーネント（LoadingSpinner, ErrorMessage）
│   │   │   │   ├── layout/               ✅ レイアウト（Header, Layout）
│   │   │   │   └── directories/          ✅ ディレクトリ管理（5コンポーネント）
│   │   │   ├── api/
│   │   │   │   ├── client.ts             ✅ Axiosクライアント
│   │   │   │   └── directories.ts        ✅ ディレクトリAPI関数
│   │   │   ├── hooks/
│   │   │   │   ├── useDirectories.ts     ✅ 一覧取得フック
│   │   │   │   ├── useAddDirectory.ts    ✅ 追加ミューテーション
│   │   │   │   ├── useUpdateDirectory.ts ✅ 更新ミューテーション
│   │   │   │   ├── useDeleteDirectory.ts ✅ 削除ミューテーション
│   │   │   │   └── useToggleDirectory.ts ✅ 切り替えミューテーション
│   │   │   ├── types/
│   │   │   │   └── directory.ts          ✅ 型定義
│   │   │   ├── lib/
│   │   │   │   ├── utils.ts              ✅ ユーティリティ関数
│   │   │   │   └── validators.ts         ✅ Zodバリデーションスキーマ
│   │   │   └── index.css                 ✅ Tailwind CSS v4設定
│   │   ├── Dockerfile                    ✅ Vite Dev Server用Dockerfile
│   │   ├── .dockerignore                 ✅ Docker除外設定
│   │   ├── tailwind.config.js            ✅ Tailwind設定
│   │   ├── components.json               ✅ Shadcn/ui設定
│   │   ├── package.json                  ✅ 依存パッケージ
│   │   └── env.example                   ✅ 環境変数テンプレート
│   └── ai-analyzer/                      📋 AI分析エンジン（計画中）
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
├── docs/
│   ├── design/                           # 設計ドキュメント
│   │   ├── phase2_1_implementation_plan.md   ✅ Phase 2.1実装計画（完了）
│   │   └── phase2_2_implementation_plan.md   ✅ Phase 2.2実装計画（完了）
│   └── manual/                           # 運用マニュアル
│       └── humantest.md                  ✅ Web UI人間動作確認手順書
│
├── docker-compose.yml                    ✅ Docker Compose設定
└── env.example                           ✅ 環境変数テンプレート
```

### Future Architecture (Phase 3+)

```
reprospective/
├── services/
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

### Web UI起動・確認

```bash
# プロジェクトルートで実行
./scripts/start.sh

# Web UIアクセス
# http://localhost:3333

# 人間動作確認手順書参照
# docs/manual/humantest.md
```

### テスト方針

- 現在は手動テスト
- Web UI: `docs/manual/humantest.md` の手順書に従う
- データ確認: `host-agent/scripts/show_sessions.py`, `show_file_events.py`
- クリーンテスト: `scripts/clean-*.sh`

---

## 実装履歴

### 2025-11-01: Phase 2.2 Web UI完了（全6ステップ）

**実装内容:**

**Step 1: プロジェクト基盤構築**
- Vite + React 19.2.0 + TypeScript プロジェクト作成
- Tailwind CSS v4.1.16 セットアップ（`@import "tailwindcss"`構文）
- Shadcn/ui 設定（New York style、HSLカラーシステム）
- 依存パッケージインストール：
  - TanStack Query v5（サーバー状態管理）
  - Axios 1.7.9（HTTPクライアント）
  - Zod 3.24.1（バリデーション）
  - React Hook Form 7.54.2（フォーム管理）
- TypeScript パスエイリアス設定（`@/*` → `./src/*`）
- ディレクトリ構造構築（components, api, hooks, types, lib）

**Step 2: Dockerコンテナ化**
- `services/web-ui/Dockerfile` 作成（Node.js 20-alpine、Vite Dev Server）
- `docker-compose.yml` 更新（web-uiサービス追加）
- ボリュームマウント設定（ホットリロード有効化）
- 環境変数管理（`VITE_API_URL`）

**Step 3: API連携実装**
- 型定義（`types/directory.ts`）
- Zodバリデーションスキーマ（`lib/validators.ts`）
- Axiosクライアント設定（`api/client.ts`, `api/directories.ts`）
- React Queryカスタムフック5個（useDirectories, useAdd, useUpdate, useDelete, useToggle）
- 楽観的更新実装（全ミューテーション）

**Step 4: コンポーネント実装**
- UIコンポーネント6個（button, dialog, input, label, switch, textarea）
- 共通コンポーネント2個（LoadingSpinner, ErrorMessage）
- レイアウトコンポーネント2個（Header, Layout）
- ディレクトリ管理コンポーネント5個（DirectoryCard, DirectoryList, Add/Edit/DeleteDialog）

**Step 5: アプリケーション統合**
- main.tsx: React Query Provider設定
- App.tsx: Layout + DirectoryList統合

**Step 6: 統合テスト**
- Docker環境動作確認
- コンテナ間通信テスト（web-ui → api-gateway）
- API Gateway接続テスト
- 人間動作確認手順書作成（`docs/manual/humantest.md`）

**技術的決定:**
- Tailwind CSS v4使用：`@import "tailwindcss"`構文
- Vite Dev Server のみ使用（Nginx不使用、実験プロジェクトのため）
- 楽観的更新パターン実装（即座のUI反映、エラー時自動ロールバック）
- 3層バリデーション（フロントエンド形式チェック、バックエンドセキュリティチェック、host-agent実在確認）

**動作確認:**
- ✅ 全6ステップ完了
- ✅ Docker環境でWeb UIが起動（http://localhost:3333）
- ✅ コンテナ間通信正常
- ✅ 全CRUD操作動作確認
- ✅ 楽観的更新動作確認
- ✅ ホットリロード機能動作確認

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

### 2025-10-31: Phase 2.1完了（API Gateway & host-agent設定同期）

**実装内容:**

**API Gateway (FastAPI):**
- `services/api-gateway/`: FastAPI RESTful API実装
- `monitored_directories`テーブル用CRUD APIエンドポイント（GET/POST/PUT/DELETE/PATCH）
- Pydantic v2モデル、バリデーション（絶対パス、重複チェック）
- Docker Compose統合、ヘルスチェック、Swagger UI
- API管理スクリプト5本（`scripts/api-*.sh`）

**host-agent設定同期:**
- `common/config_sync.py`: PostgreSQL設定同期モジュール（asyncpg使用）
- `collectors/filesystem_watcher_v2.py`: PostgreSQL連携版ウォッチャー
- 定期同期ロジック（60秒間隔）、動的ディレクトリ追加・削除
- YAML→PostgreSQL自動移行機能
- フォールバック機能（PostgreSQL接続失敗時はYAML使用）

**技術的決定:**
- asyncpg + asyncioで非同期PostgreSQL操作
- 専用スレッドではなくasyncioイベントループで同期タスク実行
- 接続プールをイベントループと同じスレッドで管理（競合回避）
- Pydantic field_validator でCORS設定のカンマ区切り文字列をリストに変換

**動作確認:**
- PostgreSQLからディレクトリ設定を自動取得
- API経由でディレクトリ追加→60秒以内に監視開始を確認
- API経由でディレクトリ無効化→60秒以内に監視停止を確認
- 初回起動時のYAML→PostgreSQL移行を確認

**次のステップ:**
Phase 2.2 - Web UI、または追加コレクター（BrowserActivityParser等）

### 2025-10-26: Phase 2基盤構築（PostgreSQL + 管理スクリプト）

**実装内容:**
- **PostgreSQL 16コンテナ**: Docker Compose設定、スキーマ初期化SQL
- **管理スクリプト**: コンテナ起動・停止、DB初期化、クリーンアップ（7スクリプト）
- **host-agent管理**: バックグラウンド起動・停止スクリプト（PID管理、個別起動対応）
- **ドキュメント**: `services/database/README.md`, `scripts/README.md`
- **Phase 2実装計画**: `docs/design/phase2_1_implementation_plan.md`作成

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
    ├── phase2_1_implementation_plan.md                   # Phase 2.1実装計画（完了）
    └── phase2_2_implementation_plan.md                   # Phase 2.2実装計画
```

設計ドキュメントは概要のみ記載。詳細実装はソースコードとREADMEを参照。

---

## Quick Reference

### よく使うコマンド

```bash
# 環境起動
docker compose up -d         # 全サービス起動（database, api-gateway, web-ui）
# または個別起動
./scripts/start.sh           # PostgreSQL + API Gateway起動
docker compose up -d web-ui  # Web UI起動
./scripts/start-agent.sh     # host-agent起動

# Web UI確認
# http://localhost:3333

# データ確認
cd host-agent && source venv/bin/activate
python scripts/show_sessions.py 20         # 最新20セッション
python scripts/show_file_events.py 50      # 最新50ファイルイベント

# 環境停止
./scripts/stop-agent.sh      # host-agent停止
docker compose down          # 全サービス停止

# データクリーンアップ
./scripts/reset-db.sh        # PostgreSQLデータベースリセット
./scripts/clean-host.sh      # host-agentローカルDBクリア
./scripts/clean-docker.sh    # Docker完全クリーンアップ
```

### 主要ファイル

**host-agent:**
- `host-agent/collectors/linux_x11_monitor.py`: デスクトップモニター本体
- `host-agent/collectors/filesystem_watcher.py`: ファイルシステムウォッチャー (v1)
- `host-agent/collectors/filesystem_watcher_v2.py`: PostgreSQL連携版ウォッチャー
- `host-agent/common/models.py`: データモデル
- `host-agent/common/database.py`: SQLite操作
- `host-agent/common/config_sync.py`: PostgreSQL設定同期
- `host-agent/config/config.yaml`: 設定ファイル

**services:**
- `services/api-gateway/`: FastAPI API Gateway
- `services/web-ui/`: React 19 + Vite フロントエンド（Step 1&2完了）
- `services/web-ui/src/types/`: TypeScript型定義
- `services/web-ui/src/api/`: APIクライアント
- `services/web-ui/env.example`: 環境変数テンプレート

**infrastructure:**
- `docker-compose.yml`: Docker Compose設定（database, api-gateway, web-ui）
- `services/database/init/01_init_schema.sql`: PostgreSQLスキーマ
- `services/database/init/02_add_monitored_directories.sql`: 監視ディレクトリテーブル
- `scripts/*.sh`: 管理スクリプト（Docker、host-agent、API操作）

**docs:**
- `docs/design/phase2_1_implementation_plan.md`: Phase 2.1実装計画（完了）
- `docs/design/phase2_2_implementation_plan.md`: Phase 2.2実装計画（Step 1&2完了）
- `docs/design/phase2_3_implementation_plan.md`: Phase 2.3実装計画（データ同期）

---

## Next Steps - Phase 2.2以降

**次の実装候補:**

### Option 1: Web UI (Phase 2.2)
- React 19 + Vite + TypeScript
- 監視ディレクトリ設定UI
- 活動データ可視化（セッション、ファイル変更）
- ダッシュボード機能

### Option 2: 追加コレクター
- BrowserActivityParser: ブラウザ履歴解析
- GitHubMonitor: GitHub API経由でコミット・PR追跡
- SNSMonitor: Bluesky等のSNS投稿収集

### Option 3: AI分析エンジン (Phase 2.3)
- LLM統合（Claude API / OpenAI API）
- 活動データの自動要約・分類
- 進捗推測・レポート生成
- 対話的レビュー機能

詳細: `docs/design/phase2_2_implementation_plan.md`, `docs/software_idea-ai_assited_todo.md`

---

## License

Apache License 2.0
