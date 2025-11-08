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

**✅ シンボリックリンク対応機能実装完了** (2025-11-08)

**✅ InputMonitor実装・本番運用準備完了** (2025-11-08)

**Phase 2.3 - データ同期機能 ✅ 完了** (2025-11-05)

### 🔄 次回の再開ポイント

**状況:**
- ✅ **シンボリックリンク対応機能実装完了** (2025-11-08)
  - Web UIからシンボリックリンクパスを入力可能
  - システムが自動的に実体パスに解決
  - 表示用パスと監視用パスを分離
  - DirectoryCardで両方のパス表示
- ✅ **InputMonitor（入力デバイス監視）本番運用完了** (2025-11-08)
  - Phase 1-4すべて完了（実績: 約5-6時間）
  - **同期バグ修正完了** (2025-11-08)
    - ✅ asyncioイベントループのブロック問題を解決
    - ✅ PostgreSQL自動同期が正常動作（5分間隔）
    - ✅ 起動時の未同期データ自動検出・同期機能動作確認
  - **運用統合完了** - start-agent.sh/stop-agent.sh統合済み
    - ✅ `./scripts/start-agent.sh` で3コレクター自動起動
    - ✅ `./scripts/start-agent.sh --input` で個別起動可能
    - ✅ `./scripts/stop-agent.sh --input` でグレースフルシャットダウン
  - **全機能動作確認済み**
    - ✅ 入力イベント検知（マウス・キーボード）
    - ✅ セッション記録（SQLite）- 複数セッション記録成功
    - ✅ タイムアウト動作（120秒無操作でセッション終了）
    - ✅ PostgreSQL自動同期（定期同期ループ正常動作）
    - ✅ グレースフルシャットダウン（SIGTERM、タスククリーンアップ）
  - マウス・キーボード入力を監視し、ユーザー活動期間を記録
  - pynput統合、スレッド間排他制御、シグナルハンドラ実装済み
  - asyncio + threading 適切な並行処理実装
- ✅ **アクティビティサマリー生成機能 設計更新完了** (2025-11-07)
  - InputMonitorによる無活動期間除外機能を統合
  - 推定精度向上：20-30%の時間削減

**現在の本番運用状態:**
- ✅ 3コレクター稼働中: desktop-monitor, filesystem-watcher, input-monitor
- ✅ PostgreSQL自動同期（5分間隔）
- ✅ ローカルSQLiteキャッシュ + 中央PostgreSQL構成
- ✅ データ表示スクリプト整備完了

**次回の作業候補:**
1. **Phase 2.4（Web UI活動データ可視化）** - 既存データの可視化（推奨）
   - 推定工数: 20時間
   - InputMonitor実装完了により、入力アクティビティデータも可視化可能
2. **アクティビティサマリー生成機能の実装** - LLMベースのサマリー生成
   - 設計完了済み、実装開始可能
   - 推定工数: 6-10日
   - InputMonitor実装完了により、無活動期間除外機能が利用可能

**参考資料:**
- `docs/design/host_agent-input_monitor.md` - InputMonitor設計書（851行、2025-11-08更新）
- `docs/design/host_agent-desktop_activity_monitor.md` - DesktopActivityMonitor設計書（更新済み）
- `docs/design/host_agent-filesystem_watcher.md` - FileSystemWatcher設計書（更新済み）
- `docs/design/summary-generator-requirements.md` - サマリー生成：要求仕様書（更新済み、730行）
- `docs/design/summary-generator-design.md` - サマリー生成：設計書（更新済み、720行）
- `docs/design/summary-generator-implementation.md` - サマリー生成：実装計画（更新済み、640行）
- `docs/design/phase2_4_implementation_plan.md` - Phase 2.4実装計画
- `logs/2025-11-05/` - Phase 2.3手動テスト時のデータ記録

---

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

### ✅ Phase 2.3 データ同期機能 完了（2025-11-05）

#### SQLite → PostgreSQL データ同期
**実装完了内容:**
- ✅ PostgreSQLスキーマ拡張（`sync_logs`テーブル作成）
- ✅ SQLiteスキーママイグレーション（`synced_at`カラム追加）
- ✅ `DataSyncManager`クラス実装（`host-agent/common/data_sync.py`）
- ✅ バッチ同期機能（デフォルト100件ずつ、5分間隔）
- ✅ 増分同期（未同期データのみ転送）
- ✅ collector統合（linux_x11_monitor.pyにasyncio統合）
- ✅ 管理スクリプト（`scripts/show-sync-stats.sh`）
- ✅ **データ型問題の修正**（event_time: datetime→int、is_symlink: int→boolean変換）

**手動テスト結果（2025-11-05）:**
- ✅ デスクトップセッション同期: 133件成功
- ✅ ファイルイベント同期: 8件成功（修正後）
- ✅ 同期ログ記録: 47回の同期実行を記録
- ❌ **発見された問題**: ファイルイベント同期で2,288件失敗（修正前）
  - 原因1: `event_time`がdatetime型（文字列）で保存されていた → int型に修正
  - 原因2: `is_symlink`が整数で送信されていた → boolean型変換を追加

**実施した修正:**
1. `filesystem_watcher_v2.py` (94行目)
   - `event_time = datetime.now()` → `event_time = int(time.time())`
   - UNIXタイムスタンプ整数として保存
2. `data_sync.py` (210行目)
   - `is_symlink = bool(record['is_symlink'])`
   - PostgreSQL boolean型への変換処理追加
3. 既存の不正データをクリーンアップ（text型event_timeを削除）

**技術的成果:**
- SQLiteローカルDB → PostgreSQL中央DBへの自動同期
- オフライン耐性（ネットワーク障害時もローカルに蓄積）
- 同期状態管理（synced_atフラグ、sync_logsテーブル）
- エラーリカバリ（トランザクション保証、バッチ単位コミット）
- データ型整合性の確保（UNIXタイムスタンプ、boolean型）

**データ記録:**
- `logs/2025-11-05/desktop_activity_sessions.txt` - 125件のセッション記録
- `logs/2025-11-05/sync_logs.txt` - 42件の同期ログ記録

詳細: `docs/design/phase2_3_implementation_plan.md`

### ✅ Phase 2.3-extra フロントエンドエラーロギング 完了（2025-11-02）

#### services/api-gateway (FastAPI) - デバッグエンドポイント追加
**実装完了内容:**
- ✅ `POST /api/v1/debug/log-errors` エンドポイント
- ✅ Pydanticモデル（ErrorEntry, LogErrorsRequest, LogErrorsResponse）
- ✅ JSON Lines形式でログファイル記録（./logs/errors.log）
- ✅ 環境変数でデバッグモードON/OFF（DEBUG=true/false）
- ✅ Docker ボリュームマウント（./logs:/var/log/frontend:rw）

**動作確認済み:**
- ✅ 単一エラー送信・記録
- ✅ 複数エラーバッチ送信・記録
- ✅ デバッグモード有効/無効切り替え
- ✅ ログファイルへのアクセス確認

#### services/web-ui (React 19 + Vite) - エラーロガー実装
**実装完了内容:**

**細粒度制御対応:**
- ✅ 5つのエラーソース個別ON/OFF（react, reactQuery, axios, global, unhandledRejection）
- ✅ 環境変数による静的制御（VITE_LOG_*）
- ✅ ブラウザコンソールからの動的制御（window.__errorLogger）

**コンポーネント:**
- ✅ `utils/errorLogger.ts` - ErrorLoggerクラス、バッファリング、サニタイズ
- ✅ `components/common/ErrorBoundary.tsx` - React Error Boundary
- ✅ `components/debug/ErrorLoggerTest.tsx` - エラーテストUI
- ✅ グローバルエラーハンドラー統合（main.tsx）
- ✅ Axiosインターセプター統合（api/client.ts）

**機能:**
- ✅ バッファリング（最大10件、5秒ごとにフラッシュ）
- ✅ 機密情報サニタイズ（VITE_*環境変数除外）
- ✅ エラーソース記録（context フィールド）
- ✅ 追加情報記録（URL, User Agent, Stack Trace等）

**動作確認済み:**
- ✅ 全エラーソース記録動作確認
- ✅ 細粒度制御動作確認（環境変数・動的制御）
- ✅ バッファリング動作確認
- ✅ ログファイル記録確認
- ✅ エラーテストページ動作確認（http://localhost:3333/?test=error-logger）

**管理スクリプト:**
- ✅ `scripts/show-error-logs.sh` - エラーログ表示（jq整形、件数指定可能）
- ✅ `scripts/clear-error-logs.sh` - エラーログ消去（確認プロンプト、強制モード）

**ドキュメント:**
- ✅ `docs/design/frontend-logger.md` - 実装計画・結果
- ✅ `docs/manual/error-logging.md` - 利用マニュアル（ON/OFF、確認、消去、細粒度制御、トラブルシューティング）

詳細: `docs/design/frontend-logger.md`, `docs/manual/error-logging.md`

### ✅ Phase 2.3.1 環境変数管理の改善 完了（2025-11-05）

#### 実装完了内容
**Phase 1: 基盤整備（1-2時間）**
- ✅ `host-agent/requirements.txt`に`python-dotenv>=1.0.0`追加
- ✅ `host-agent/common/config.py`新規作成（ConfigManagerクラス）
- ✅ プロジェクトルート`env.example`更新（DATABASE_URL、DB_PORT=6000等）
- ✅ `host-agent/env.example`新規作成

**Phase 2: 既存コード移行（2-3時間）**
- ✅ `linux_x11_monitor.py`、`filesystem_watcher_v2.py`、`test_sync.py`修正
- ✅ ハードコードされたPostgreSQL接続情報を削除

**Phase 3: 設定ファイル更新（30分）**
- ✅ `config.yaml`更新（postgres_urlをコメントアウト）
- ✅ `scripts/start-agent.sh`修正（.env存在確認追加）

**Phase 4: ドキュメント更新（30分-1時間）**
- ✅ `CLAUDE.md`、`host-agent/README.md`更新

**動作確認済み:**
- ✅ ConfigManager単体テスト成功（環境変数取得、SQLiteパス解決、YAML設定取得）
- ✅ 全Pythonファイル構文チェック成功

**技術的成果:**
- セキュリティリスク解消（パスワードのハードコード削除）
- 環境ごとの設定切り替え可能（開発・本番の分離）
- YAML設定との共存（機密情報は環境変数、その他はYAML）
- シンボリックリンク不要（python-dotenvの自動検索）
- 下位互換性維持（既存のconfig.yamlも動作）

**修正ファイル: 11ファイル（新規2、修正9）**

**手動テスト手順書:**
- ✅ `docs/manual/humantest-db-sync.md` - データベース同期機能の確認手順書作成
- ✅ `docs/manual/humantest-webui.md` - Web UI確認手順書（リネーム）

詳細: `docs/design/refactoring_proposal.md`

### 📋 Phase 2.4 Web UI 活動データ可視化（計画中）

#### 実装予定内容
**API Gateway拡張:**
- 活動データ取得APIエンドポイント（5個）
  - `GET /api/v1/activities/sessions` - セッション一覧取得
  - `GET /api/v1/activities/daily-summary` - 日別サマリー
  - `GET /api/v1/activities/file-events` - ファイルイベント取得
  - `GET /api/v1/activities/file-summary` - ファイルサマリー
  - `GET /api/v1/activities/sync-status` - 同期ステータス

**Web UI新規ページ:**
- ダッシュボードページ（`/dashboard`）
  - 時間別アクティビティグラフ（Recharts）
  - 上位アプリケーションカード
  - ファイル変更統計
  - 同期ステータス表示
- セッション一覧ページ（`/sessions`）
  - フィルタ・検索機能
  - ページネーション
  - 詳細モーダル
- ファイルイベントページ（`/file-events`）
  - プロジェクト別フィルタ
  - 拡張子別フィルタ
  - イベントタイプ別表示
- 同期ステータスページ（`/sync-status`）
  - 最新同期状態
  - 同期ログ履歴
  - エラー通知

**技術スタック:**
- Recharts: グラフ描画
- date-fns: 日付操作
- React Day Picker: 日付選択

**推定工数:** 20時間（3日間）

詳細: `docs/design/phase2_4_implementation_plan.md`

### 📋 Phase 2.5以降（将来実装）

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

詳細: `docs/software_idea-ai_assited_todo.md`

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
│   └── ai-analyzer/                      📋 AI分析エンジン（設計中）
│       ├── app/
│       │   ├── main.py                   📋 サマリー生成CLI
│       │   ├── summary_generator/        📋 サマリー生成コンポーネント
│       │   │   ├── log_processor.py      📋 ログ前処理（セッション統合）
│       │   │   ├── activity_hint_manager.py 📋 ヒント管理・匿名化
│       │   │   ├── sensitive_filter.py   📋 センシティブコンテンツフィルタ
│       │   │   ├── llm_service.py        📋 LLMカテゴライザ（OpenAI/Ollama/Claude）
│       │   │   ├── aggregator.py         📋 集約・ランク付け
│       │   │   └── json_output.py        📋 JSON出力
│       │   └── utils/
│       ├── config/
│       │   ├── activity_hints.yaml       📋 プロジェクト・カテゴリー定義
│       │   └── summary_generator.yaml    📋 サマリー生成設定
│       ├── Dockerfile                    📋 Dockerイメージ
│       └── requirements.txt              📋 依存パッケージ
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
│   │   ├── phase2_2_implementation_plan.md   ✅ Phase 2.2実装計画（完了）
│   │   ├── phase2_3_implementation_plan.md   ✅ Phase 2.3実装計画（完了）
│   │   ├── phase2_4_implementation_plan.md   📋 Phase 2.4実装計画（次候補）
│   │   ├── summary-generator-requirements.md ✅ サマリー生成機能：要求仕様書
│   │   ├── summary-generator-design.md       ✅ サマリー生成機能：設計書
│   │   └── summary-generator-implementation.md ✅ サマリー生成機能：実装計画
│   └── manual/                           # 運用マニュアル
│       ├── humantest-webui.md            ✅ Web UI人間動作確認手順書
│       └── humantest-db-sync.md          ✅ データベース同期確認手順書
│
├── docker-compose.yml                    ✅ Docker Compose設定
└── env.example                           ✅ 環境変数テンプレート
```

### Future Architecture (Phase 3+)

```
reprospective/
├── services/
│   └── ai-analyzer/                      📋 AI分析エンジン（設計完了、実装待ち）
│       ├── summary_generator/            # アクティビティサマリー生成
│       └── analyzers/                    # 将来の追加分析機能
└── shared/                               📋 共有ライブラリ（計画中）
    ├── models/                           # 共通データモデル
    └── utils/                            # ユーティリティ
```

**ai-analyzer実装の前提条件:**
- 設計上の不明点6項目の決定（`docs/design/summary-generator.md` 参照）
  1. 起動トリガー（オンデマンド/定期実行/ハイブリッド）
  2. サマリー保存先（PostgreSQL/ファイル/両方）
  3. エラーハンドリング戦略
  4. バッチ処理の進捗表示方法
  5. LLMモデル選択（GPT-4 Turbo/GPT-4o/GPT-5）
  6. 匿名化デバッグログの機密性管理

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

### エラーログ管理

```bash
# エラーログを確認（最新10件）
./scripts/show-error-logs.sh

# エラーログを確認（最新50件）
./scripts/show-error-logs.sh 50

# すべてのエラーログを確認
./scripts/show-error-logs.sh all

# リアルタイムでエラーログを監視
tail -f ./logs/errors.log | jq '.'

# エラーログをクリア（確認あり）
./scripts/clear-error-logs.sh

# エラーログをクリア（強制実行）
./scripts/clear-error-logs.sh -f

# エラーテストページにアクセス
# http://localhost:3333/?test=error-logger
```

### テスト方針

- 現在は手動テスト
- Web UI: `docs/manual/humantest.md` の手順書に従う
- エラーログ: `docs/manual/error-logging.md` の利用マニュアル参照
- データ確認: `host-agent/scripts/show_sessions.py`, `show_file_events.py`
- クリーンテスト: `scripts/clean-*.sh`

---

## Claude Code エラーログ活用ガイド

### ユーザーからエラー報告を受けた場合の対応フロー

ユーザーから「Web UIでエラーが発生した」「動作がおかしい」等の報告を受けた場合、以下の手順で対応してください：

**Step 1: エラーログを確認**

```bash
# 最新のエラーログを確認（最新10件）
./scripts/show-error-logs.sh

# より多くのログが必要な場合
./scripts/show-error-logs.sh 50
```

**Step 2: エラー内容を分析**

各エラーエントリには以下の情報が含まれています：

```json
{
  "timestamp": "エラー発生日時",
  "message": "エラーメッセージ",
  "stack": "スタックトレース",
  "context": "エラーソース（react/axios/global等）",
  "url": "エラー発生ページURL",
  "additional_info": {
    "status": "HTTPステータス（axiosの場合）",
    "method": "HTTPメソッド",
    "filename": "エラー発生ファイル（globalの場合）",
    "lineno": "行番号"
  }
}
```

**Step 3: エラーソースを特定**

- `context: "react"` → React コンポーネント内のエラー
- `context: "axios"` → API通信エラー
- `context: "reactQuery"` → React Query エラー
- `context: "global"` → グローバルエラー（window.error）
- `context: "unhandledRejection"` → Promise拒否

**Step 4: 該当コードを確認**

`stack` フィールドや `additional_info.filename` から該当ファイルを特定し、Readツールで確認：

```typescript
// 例: スタックトレースから services/web-ui/src/App.tsx:42 を特定
```

**Step 5: 修正提案または追加調査**

- エラー原因が明確な場合: 修正案を提示
- 不明な場合: 追加情報を要求（再現手順、ブラウザ環境等）

### プロアクティブなエラーログ確認

ユーザーが明示的に依頼していなくても、以下の状況では自発的にエラーログを確認することを推奨：

1. **コード変更後:**
   - Web UIのコードを変更した後
   - 「テストしてください」と言われた後

2. **デバッグセッション中:**
   - ユーザーが「動作確認中」と言っている場合
   - 5分ごとに新しいエラーがないか確認

3. **セッション開始時（オプション）:**
   - 前回から新しいエラーが記録されているか確認

### エラーログがない場合

```bash
./scripts/show-error-logs.sh
# → "ログファイルは存在しますが、エントリがありません"
```

この場合:
- ✅ エラーロギングが正常に動作している
- ✅ 現時点でエラーは発生していない
- ユーザーに「エラーログは空です。問題なく動作しているようです。」と報告

### エラーログのクリア

分析後、ログが溜まってきた場合はクリアを提案：

```bash
./scripts/clear-error-logs.sh -f
```

**クリアのタイミング:**
- エラー修正完了後
- テストセッション開始前
- ログ件数が100件を超えた場合

### 重要な注意点

- ⚠️ エラーログは開発環境でのみ有効（DEBUG=true）
- ⚠️ 本番環境では `VITE_ENABLE_ERROR_LOGGING=false` に設定すること
- ⚠️ ログファイルは `./logs/errors.log` に記録される（gitignore対象）

### エラーテストページ

エラーロギングが正常に動作しているかテストする場合：

```
http://localhost:3333/?test=error-logger
```

5種類のエラーをテストできるUIが表示されます。

---

## 実装履歴

### 2025-11-08: InputMonitor同期バグ修正完了

**InputMonitor PostgreSQL同期機能の修正（実績: 30分）**

**背景:**
- InputMonitorが正常に動作していたが、PostgreSQLへの同期が実行されていなかった
- SQLiteには7件のセッションが記録されていたが、PostgreSQLには1件のみ
- ログに同期関連のメッセージが初期化以降出力されていなかった

**原因:**
- `input_monitor.py`の321行目で`monitor.start_monitoring()`がブロッキング呼び出しだった
- asyncioイベントループが完全にブロックされ、`asyncio.create_task(sync_manager.start_sync_loop())`で作成した同期タスクが実行されなかった

**修正内容:**

**input_monitor.py (304-342行目):**
- ✅ InputMonitorを`threading.Thread`で別スレッド起動に変更
- ✅ asyncioイベントループを`await stop_event.wait()`で維持
- ✅ シグナルハンドラで`stop_event.set()`してグレースフルシャットダウン
- ✅ クリーンアップ処理を`finally`ブロックに移動（sync_task.cancel(), sync_manager.close()）

**動作確認結果:**
- ✅ 起動直後に未同期6件を自動検出・同期
- ✅ PostgreSQLに7件すべて記録
- ✅ 新規セッション（ID=8）も記録開始
- ✅ 定期同期ループが正常動作（300秒間隔）
- ✅ ログに同期メッセージが正常出力（`定期同期ループを開始します`, `input_activity_sessions: 6件の未同期レコードを検出`）

**技術的成果:**
- asyncioとthreadingの適切な分離（CPU boundな監視はスレッド、I/O boundな同期はasyncio）
- イベントループのブロック回避（バックグラウンドタスクが正常に実行可能）
- グレースフルシャットダウンの改善（タスクキャンセル、接続プールクローズ）

**修正ファイル: 1ファイル**
- `host-agent/collectors/input_monitor.py` (304-342行目)

---

### 2025-11-08: シンボリックリンク対応機能実装完了

**FileSystemWatcher シンボリックリンク対応（実績: 約2時間）**

**背景:**
- ユーザーが `/home/demitas/work/github.com/reprospective`（シンボリックリンク）を入力するとエラー
- 実体パス `/mnt/ext-ssd1/work/github.com/reprospective` を指定する必要があった
- ユーザー体験向上のため、シンボリックリンク自動解決機能を実装

**実装内容:**

**Phase 1: PostgreSQLスキーマ更新**
- ✅ `services/database/init/05_add_path_resolution.sql` 作成
- ✅ `display_path`（表示用パス）、`resolved_path`（実体パス）カラム追加
- ✅ 既存データマイグレーション実施

**Phase 2: API Gateway実装**
- ✅ `app/utils/path_resolver.py` 新規作成（148行）
  - `resolve_directory_path()`: シンボリックリンク解決ロジック
  - `validate_absolute_path()`: 絶対パス検証
  - `check_path_accessibility()`: アクセス権限確認
- ✅ Pydanticモデル更新（`display_path`, `resolved_path`追加）
- ✅ 全エンドポイント修正（GET/POST/PUT/PATCH）
  - パス解決統合
  - レスポンスに新フィールド含める

**Phase 3: host-agent更新**
- ✅ `common/config_sync.py` 修正
  - `MonitoredDirectory`データクラスに`display_path`, `resolved_path`追加
  - `get_monitored_directories()`で`resolved_path`優先使用
- ✅ `collectors/filesystem_watcher_v2.py` ログ改善
  - シンボリックリンク情報をログに表示
  - `display_path -> resolved_path` 形式で出力

**Phase 4: Web UI更新**
- ✅ `types/directory.ts` 型定義更新
- ✅ `DirectoryCard.tsx` 表示改善
  - 実体パスが表示パスと異なる場合、「→ 実体: ...」を表示

**動作確認:**
- ✅ API動作確認（パス解決正常、シンボリックリンク対応）
- ✅ Web UI確認（エラーなし、実体パス表示）
- ✅ ログ確認（新規エラーなし）

**技術的成果:**
- ユーザーはシンボリックリンクパスを入力可能
- システムが自動的に実体パスに解決
- 表示用パスと監視用パスを分離
- host-agentは実体パスを監視

**修正ファイル: 9ファイル（新規3、更新6）**

**新規作成:**
- `services/database/init/05_add_path_resolution.sql`
- `services/api-gateway/app/utils/path_resolver.py`
- `services/api-gateway/app/utils/__init__.py`

**更新:**
- `services/api-gateway/app/models/monitored_directory.py`
- `services/api-gateway/app/routers/directories.py`
- `host-agent/common/config_sync.py`
- `host-agent/collectors/filesystem_watcher_v2.py`
- `services/web-ui/src/types/directory.ts`
- `services/web-ui/src/components/directories/DirectoryCard.tsx`

---

### 2025-11-08: InputMonitor実装・手動テスト・運用統合完了

**Phase 1-4実装完了（実績: 約5-6時間）**

**Phase 1: 基盤実装（実績1時間）**
- ✅ `InputActivitySession`データモデル追加（`common/models.py`）
- ✅ `InputActivityDatabase`クラス実装（344行、`common/database.py`）
- ✅ PostgreSQLスキーマ作成（`services/database/init/04_add_input_activity_sessions.sql`）
- ✅ 設定ファイル更新（`config/config.yaml`）
- ✅ pynput依存関係追加（`requirements.txt`）

**Phase 2: InputMonitorコレクター実装（実績2時間）**
- ✅ `collectors/input_monitor.py`作成（324行）
- ✅ pynput統合（マウス・キーボード監視）
- ✅ スレッド間排他制御（`threading.Lock`）
- ✅ タイムアウトチェックスレッド（120秒無操作検知）
- ✅ シグナルハンドラ（SIGTERM, SIGINT）
- ✅ 未終了セッション削除機能
- ✅ DISPLAY環境変数チェック

**Phase 3: データ同期統合（実績1時間）**
- ✅ `DataSyncManager`への入力アクティビティ同期機能追加
- ✅ `_sync_input_activity()`メソッド実装
- ✅ SQLite→PostgreSQLバッチ同期（5分間隔）
- ✅ `input_monitor.py`でDataSyncManager統合

**Phase 4: デバッグ・テスト（実績1時間）**
- ✅ デバッグスクリプト作成（`scripts/show_input_sessions.py`）
- ✅ PostgreSQLスキーマ適用
- ✅ pynputインストール
- ✅ モジュールインポートテスト成功

**手動テスト完了（実績1.5時間）**

**ConfigManager拡張（実績30分）:**
- ✅ `get_sqlite_input_path()`メソッド追加
- ✅ `get_input_monitor_config()`メソッド追加
- ✅ `DataSyncManager`のhost_identifier初期化修正

**機能テスト結果:**
1. **入力イベント検知テスト** ✅
   - マウス・キーボード入力を正常に検知
   - セッション開始・終了のログ出力確認

2. **セッション記録テスト** ✅
   - SQLiteデータベースに2セッション記録成功
   - セッション1: 52秒（09:54:31 - 09:55:23）
   - セッション2: 2分10秒（09:57:08 - 09:59:18）

3. **タイムアウト動作テスト** ✅
   - 120秒無操作後、自動的にセッション終了
   - タイムアウトチェックスレッド正常動作

4. **PostgreSQL同期テスト** ✅
   - 手動同期トリガーで1件同期成功
   - sync_logsテーブルに記録（records_synced=1, status=success）
   - SQLiteのsynced_atフラグ更新確認

5. **グレースフルシャットダウンテスト** ✅
   - SIGTERM受信で正常終了
   - リスナー停止、スレッド終了、DB接続クローズ確認

**技術的成果:**
- プライバシー保護設計（入力内容は記録せず、セッション期間のみ）
- スレッドセーフな実装（threading.Lock）
- 堅牢なエラーハンドリング（未終了セッション削除、シグナルハンドラ）
- オフライン耐性（SQLiteローカルキャッシュ + PostgreSQL同期）

**運用統合（実績: 約1時間）**

**start-agent.sh/stop-agent.sh統合:**
- ✅ `--input`オプション追加
- ✅ 全エージェント起動時にInputMonitorも自動起動
- ✅ 個別起動・停止対応
- ✅ ヘルプメッセージ更新

**動作確認:**
- ✅ `./scripts/start-agent.sh --input` - 正常起動確認
- ✅ `./scripts/stop-agent.sh --input` - グレースフルシャットダウン確認
- ✅ ログファイル記録確認（`logs/input-monitor.log`）

**PostgreSQL表示スクリプト作成:**
- ✅ `scripts/show-input-sessions.sh` 作成
- ✅ PostgreSQLから入力セッション表示
- ✅ 引数で件数指定可能（デフォルト10件）
- ✅ 総レコード数表示

**ファイル監視動作確認:**
- ✅ PostgreSQL設定修正（正しいディレクトリパスに更新）
- ✅ 存在しないディレクトリを無効化
- ✅ 60秒設定同期動作確認
- ✅ ファイルイベント記録テスト成功（created, modified, deleted）

**修正ファイル: 14ファイル（新規4、更新10）**

**新規作成:**
- `host-agent/collectors/input_monitor.py` (324行)
- `services/database/init/04_add_input_activity_sessions.sql` (45行)
- `host-agent/scripts/show_input_sessions.py` (175行)
- `scripts/show-input-sessions.sh` (42行) - PostgreSQL表示スクリプト

**更新:**
- `host-agent/common/models.py` - InputActivitySession追加
- `host-agent/common/database.py` - InputActivityDatabase追加（344行）
- `host-agent/common/config.py` - get_sqlite_input_path(), get_input_monitor_config()追加
- `host-agent/config/config.yaml` - input_monitor設定追加
- `host-agent/requirements.txt` - pynput>=1.7.6追加
- `host-agent/common/data_sync.py` - 入力アクティビティ同期機能追加、host_identifier初期化修正
- `scripts/start-agent.sh` - InputMonitor起動対応
- `scripts/stop-agent.sh` - InputMonitor停止対応
- `CLAUDE.md` - InputMonitor実装完了ステータス更新

**本番運用準備完了:**
- ✅ 3つのコレクター統合（desktop-monitor, filesystem-watcher, input-monitor）
- ✅ 自動起動スクリプト整備
- ✅ データ表示スクリプト整備
- ✅ PostgreSQL同期機能統合

---

### 2025-11-07: InputMonitor設計 & サマリー生成機能設計更新

**InputMonitor（入力デバイス監視）設計完了（実績3-4時間）:**
- 要求仕様の確認と設計方針の決定
  - データ粒度：セッション開始/終了時刻のみ（入力種別なし）
  - プライバシー保護：入力内容は記録しない
  - 技術選択：pynput → python-xlib → python-evdev の優先順位
- `docs/design/host_agent-input_monitor.md` 新規作成（360行）
  - セッション管理ロジック（無操作タイムアウト120秒、設定可能）
  - データベーススキーマ（SQLite/PostgreSQL）
  - アーキテクチャ設計（データモデル、DBクラス、コレクタークラス）
  - 実装計画（Phase 1-4、推定工数7-11時間）
  - セキュリティ考慮事項

**既存設計書の更新:**
- `docs/design/host_agent-desktop_activity_monitor.md` 更新
  - Phase 2.3データ同期機能完了の記載
  - データベーススキーマ追加、環境変数設定説明追加
- `docs/design/host_agent-filesystem_watcher.md` 更新
  - Phase 2.1/2.3完了の記載
  - 設定同期機能、データ同期機能の詳細セクション追加

**アクティビティサマリー生成機能 設計更新（実績2-3時間）:**
- 無活動期間除外機能を統合（InputMonitor連携）
- `docs/design/summary-generator-requirements.md` 更新（730行）
  - データソースに入力アクティビティを追加
  - ログ前処理に無活動期間除外の詳細を追加
  - 新規セクション「無活動期間除外の詳細」追加
  - 処理アルゴリズム、統計情報、期待される効果（20-30%時間削減）
- `docs/design/summary-generator-design.md` 更新（720行）
  - Log Processorに無活動期間除外アルゴリズム追加
  - 出力データ構造に`active_time_ratio`等追加
  - メタデータに`idle_filtering_stats`追加
  - 設定ファイルに`idle_filtering`設定追加
- `docs/design/summary-generator-implementation.md` 更新（640行）
  - Phase 1実装タスクに無活動期間除外を追加
  - ユニットテストにテストケース例を追加
  - トラブルシューティングに入力ログ関連を追加

**技術的成果:**
- InputMonitorにより「実際に作業していた時間」を精緻に計測可能
- デスクトップセッションと入力セッションの時間的重複計算アルゴリズム設計
- ファイルイベントは無活動期間除外の対象外（明確な作業の証跡）
- 推定精度向上：20-30%の時間削減（例：3時間のブラウジング → 実活動45分）

**修正ファイル: 6ファイル（新規1、更新5）**

---

### 2025-11-05: Phase 2.3 データ同期機能の修正・完了

**手動テスト実施（実績1時間）:**
- デスクトップセッション同期: 正常動作確認
- ファイルイベント同期: 2,288件の失敗を発見

**問題調査（実績30分）:**
1. **問題1: event_timeのデータ型不一致**
   - PostgreSQL: `bigint`型（UNIXタイムスタンプ）を期待
   - SQLite: `text`型（`'2025-11-05 21:16:00.486786'`）で保存されていた
   - 原因: `filesystem_watcher_v2.py`で`datetime.now()`をそのまま保存

2. **問題2: is_symlinkのboolean型変換不足**
   - PostgreSQL: `boolean`型を期待
   - 送信: 整数`0`が送られていた
   - 原因: `data_sync.py`で型変換処理がなかった

**修正実装（実績1.5時間）:**
1. `filesystem_watcher_v2.py` (94-95行目)
   ```python
   # 修正前
   event_time = datetime.now()
   event_time_iso = event_time.isoformat()

   # 修正後
   event_time = int(time.time())
   event_time_iso = datetime.fromtimestamp(event_time).isoformat()
   ```

2. `data_sync.py` (209-210行目)
   ```python
   # 追加
   is_symlink = bool(record['is_symlink']) if record.get('is_symlink') is not None else False
   ```

3. `common/database.py` (44-45行目)
   ```python
   # SQLiteスレッドセーフティ修正
   self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
   ```

4. `scripts/show_file_events.py` (19-40行目)
   ```python
   # parse_event_time()関数を追加してタイムスタンプ変換を統一
   ```

5. 既存データクリーンアップ
   - text型の不正データを削除（147件）

**動作確認（実績30分）:**
- ✅ ファイルイベント同期成功: 8件
- ✅ デスクトップセッション同期継続成功
- ✅ 同期ログ正常記録
- ✅ PostgreSQLデータ確認完了

**修正ファイル: 5ファイル**
- `host-agent/collectors/filesystem_watcher_v2.py`
- `host-agent/common/data_sync.py`
- `host-agent/common/database.py`
- `host-agent/collectors/linux_x11_monitor.py`（スレッド分離）
- `host-agent/scripts/show_file_events.py`

**データ保存:**
- `logs/2025-11-05/desktop_activity_sessions.txt` (125件)
- `logs/2025-11-05/sync_logs.txt` (42件の同期ログ)

---

### 2025-11-05: Phase 2.3.1 環境変数管理の改善完了

**実装内容（実績4-6時間）:**

**Phase 1: 基盤整備（1-2時間）**
- ✅ `host-agent/requirements.txt`に`python-dotenv>=1.0.0`追加
- ✅ `host-agent/common/config.py`新規作成（ConfigManagerクラス実装）
  - `find_dotenv(usecwd=True)`で親ディレクトリの.envを自動検索
  - PostgreSQL接続URL取得（環境変数 > デフォルト値の優先順位）
  - SQLiteパス取得（相対パス→絶対パス変換）
  - YAML設定取得（data_sync, desktop_monitor, filesystem_watcher）
- ✅ プロジェクトルート`env.example`更新
  - `DATABASE_URL`, `DB_PORT=6000`に変更
  - `SQLITE_DESKTOP_PATH`, `SQLITE_FILE_EVENTS_PATH`追加
- ✅ `host-agent/env.example`新規作成

**Phase 2: 既存コード移行（2-3時間）**
- ✅ `linux_x11_monitor.py`修正：ConfigManager使用に変更
- ✅ `filesystem_watcher_v2.py`修正：ConfigManager使用に変更
- ✅ `test_sync.py`修正：ConfigManager使用に変更
- ✅ ハードコードされたPostgreSQL接続情報を削除

**Phase 3: 設定ファイル更新（30分）**
- ✅ `config.yaml`更新：`postgres_url`をコメントアウト、環境変数移行ガイド追加
- ✅ `scripts/start-agent.sh`修正：.env存在確認ロジック追加

**Phase 4: ドキュメント更新（30分-1時間）**
- ✅ `CLAUDE.md`更新：実装履歴追加
- ✅ `host-agent/README.md`更新：環境変数設定説明追加

**技術的成果:**
- セキュリティリスク解消（パスワードのハードコード削除）
- 環境ごとの設定切り替え可能（開発・本番の分離）
- YAML設定との共存（機密情報は環境変数、その他はYAML）
- シンボリックリンク不要（python-dotenvの自動検索）
- 下位互換性維持（既存のconfig.yamlも動作）

**環境変数の優先順位:**
1. `DATABASE_URL`が設定されている場合、それを最優先
2. `DB_HOST`, `DB_PORT`等の個別環境変数から構築
3. デフォルト値を使用

**修正ファイル: 11ファイル（新規2、修正9）**

---

### 2025-11-04: Phase 2.3 データ同期機能完了

**SQLite → PostgreSQL データ同期（実績6時間）**

**ステップ1: PostgreSQLスキーマ拡張（実績1時間）**
- ✅ `services/database/init/03_add_sync_logs.sql` 作成
- ✅ `sync_logs`テーブル作成（10カラム、4インデックス）
- ✅ `scripts/reset-db.sh` 修正（全SQLファイル実行に改良）
- ✅ テーブル作成確認（5テーブル合計）

**ステップ2: SQLiteスキーママイグレーション（実績1時間）**
- ✅ `DesktopActivityDatabase._migrate_add_synced_at_column()` 実装
- ✅ `FileChangeDatabase._migrate_add_synced_at_column()` 実装
- ✅ `synced_at`カラム追加（既存DBの自動アップグレード）
- ✅ インデックス作成（`idx_synced_at`, `idx_file_synced_at`）

**ステップ3: データ同期モジュール実装（実績2時間）**
- ✅ `host-agent/common/data_sync.py` 作成（500行以上）
- ✅ `DataSyncManager`クラス実装
  - `initialize()`: PostgreSQL接続プール初期化
  - `sync_all()`: 全テーブル同期
  - `_sync_desktop_activity()`: デスクトップセッション同期
  - `_sync_file_events()`: ファイルイベント同期
  - `_get_unsynced_*_records()`: 未同期レコード取得
  - `_update_*_synced_flags()`: synced_atフラグ更新
  - `_log_sync_result()`: 同期統計記録
  - `start_sync_loop()`: 定期同期ループ
- ✅ ISO文字列→TIMESTAMP型変換実装
- ✅ バッチ処理（デフォルト100件）
- ✅ エラーハンドリング・リトライロジック

**ステップ4: collector統合（実績1時間）**
- ✅ `linux_x11_monitor.py` asyncio統合
- ✅ `main_async()` 関数実装
- ✅ `DataSyncManager` 統合
- ✅ バックグラウンド同期ループ起動
- ✅ `config.yaml` 拡張（data_sync設定追加）
- ✅ PostgreSQL接続URL修正（ポート6000対応）

**ステップ5: 管理スクリプト作成（実績30分）**
- ✅ `scripts/show-sync-stats.sh` 作成
- ✅ 最新10件の同期ログ表示
- ✅ テーブル別同期サマリー
- ✅ ホスト別同期統計
- ✅ 実行権限付与

**ステップ6: 統合テスト（実績30分）**
- ✅ `host-agent/test_sync.py` 作成
- ✅ 12件のテストデータ作成・同期成功
- ✅ PostgreSQLデータ挿入確認
- ✅ `sync_logs`テーブル記録確認
- ✅ 同期統計スクリプト動作確認

**技術的課題と解決:**
1. **ISO文字列→TIMESTAMP型変換エラー**
   - 問題: PostgreSQLが文字列をdatetime型として受け入れない
   - 解決: `datetime.fromisoformat()`で明示的に変換
2. **PostgreSQLポート設定**
   - 問題: デフォルトポート5432が6000に変更されていた
   - 解決: 接続URLを修正（localhost:6000）
3. **パスワード認証エラー**
   - 問題: `reprospective_password`が間違っていた
   - 解決: Dockerコンテナから実際のパスワード取得（`change_this_password`）

**動作確認結果:**
- ✅ 12件のセッションを正常に同期
- ✅ `records_synced=12, records_failed=0, status=success`
- ✅ ホスト識別子: `demitas-ryzen_demitas`
- ✅ 同期時刻: 2025-11-04 21:38:50

**次のステップ:**
Phase 2.4 - Web UI活動データ可視化（推定20時間）

### 2025-11-02: Phase 2.3-extra フロントエンドエラーロギング完了

**Phase 1: API Gateway デバッグエンドポイント（実績35分）**
- ✅ `services/api-gateway/app/routers/debug.py` 作成（94行）
- ✅ `services/api-gateway/app/config.py` 更新（debug_mode追加）
- ✅ `services/api-gateway/app/main.py` 更新（debugルーター登録）
- ✅ `docker-compose.yml` 更新（DEBUG_MODE環境変数、./logs ボリュームマウント）
- ✅ `env.example` 更新（DEBUG設定説明追加）
- ✅ `logs/.gitignore` 作成
- ✅ 動作確認完了（単一エラー送信、バッチエラー送信、ログファイル記録）

**Phase 2: Web UI エラーロガー実装（実績45分）**
- ✅ `services/web-ui/src/utils/errorLogger.ts` 作成（198行）
  - ErrorLogger クラス、細粒度制御、バッファリング、サニタイズ
- ✅ `services/web-ui/src/components/common/ErrorBoundary.tsx` 作成（100行）
- ✅ `services/web-ui/src/components/debug/ErrorLoggerTest.tsx` 作成（190行）
- ✅ `services/web-ui/src/main.tsx` 更新（ErrorBoundary統合、グローバルエラーハンドラー）
- ✅ `services/web-ui/src/api/client.ts` 更新（Axiosインターセプター）
- ✅ `services/web-ui/src/App.tsx` 更新（テストページルーティング）
- ✅ `services/web-ui/.env` 更新（エラーロギング環境変数）
- ✅ `services/web-ui/env.example` 更新（詳細な説明・使用例）

**管理スクリプト追加:**
- ✅ `scripts/show-error-logs.sh` - エラーログ表示（jq整形、件数指定、all オプション）
- ✅ `scripts/clear-error-logs.sh` - エラーログ消去（確認プロンプト、-f 強制モード）
- ✅ `scripts/README.md` 更新（新スクリプトのドキュメント追加）

**ドキュメント作成:**
- ✅ `docs/design/frontend-logger.md` 更新（Phase 1 & 2 完了状況、実装結果追加）
- ✅ `docs/manual/error-logging.md` 作成（643行）
  - エラーロギングのON/OFF切り替え
  - エラーログの確認・消去方法
  - 細粒度制御の使い方
  - エラーテストページの使い方
  - トラブルシューティング（5項目）
  - よくある使用パターン（3パターン）
- ✅ `docs/manual/README.md` 作成（マニュアル一覧）

**動作確認完了:**
- ✅ 全エラーソース記録動作確認
- ✅ 細粒度制御動作確認（環境変数・ブラウザコンソール）
- ✅ バッファリング動作確認
- ✅ スクリプト動作確認（show-error-logs.sh, clear-error-logs.sh）
- ✅ エラーテストページ動作確認

**技術的成果:**
- 5つのエラーソース個別制御（react, reactQuery, axios, global, unhandledRejection）
- 環境変数による静的制御 + ブラウザコンソールからの動的制御
- パフォーマンス最適化（バッファリング、不要ログ送信回避）
- 機密情報保護（VITE_*環境変数のサニタイズ）
- 開発者体験向上（包括的なドキュメント、便利なスクリプト）

### 2025-11-01: Phase 2.2 Web UI完了 + 人間動作確認・修正完了

**人間動作確認結果:**
- ✅ 基本機能テスト完了（ディレクトリ追加、編集、削除、ON/OFF切り替え）
- ✅ UIデザイン改善実施
- ✅ 環境変数修正（docker-compose.yml）
- ✅ スクリプト修正（scripts/start.sh）

**修正内容:**

1. **環境変数の修正:**
   - 問題: docker-compose.ymlで`VITE_API_URL: http://api-gateway:8000`とハードコードされており、ブラウザからアクセス不可
   - 解決: docker-compose.ymlの環境変数上書きを削除、services/web-ui/.env（`http://localhost:8800`）を使用

2. **scripts/start.sh の修正:**
   - 問題: `docker compose up -d database`でdatabaseのみ起動
   - 解決: `docker compose up -d`に変更し、全サービス（database, api-gateway, web-ui）を起動
   - 接続情報表示を追加（Web UI, API Gateway, Swagger UI, PostgreSQL）

3. **UIデザイン改善:**
   - DirectoryCard: パディング増加（p-4→p-6）、ボタンサイズ拡大（h-4→h-5）
   - ボーダー: インラインスタイルで明示的に指定（Tailwind CSS v4のカスタムカラー問題を回避）
   - 背景色: 有効時は白、無効時はグレー
   - 影効果: カードに立体感を追加
   - DirectoryList: カード間の余白増加（gap-4→gap-6）

**動作確認済み:**
- ✅ http://localhost:3333 でWeb UIアクセス可能
- ✅ ディレクトリ一覧表示
- ✅ ディレクトリ追加（バリデーション動作）
- ✅ ディレクトリ編集
- ✅ ON/OFF切り替え（楽観的更新）
- ✅ ディレクトリ削除
- ✅ UIデザイン：ボーダー、影、ホバー効果すべて正常表示

### 2025-11-01: Phase 2.2 Web UI実装（全6ステップ）

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
