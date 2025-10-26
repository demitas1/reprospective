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

**Phase 1 - 実験的実装フェーズ** (2025-10-25時点)

### ✅ 実装済み

#### host-agent/
デスクトップアクティビティ監視エージェント（Linux X11環境）

- **DesktopActivityMonitor**: アクティブウィンドウ追跡とセッション記録
- **FileSystemWatcher**: ファイル変更監視とイベント記録
- **データベース分離アーキテクチャ**: コレクター別独立DB（スレッド競合回避）
- **設定管理**: YAML形式の設定ファイル
- **デバッグツール**: セッション/イベント表示、DB初期化スクリプト

詳細: `host-agent/README.md`, `docs/design/`

### 🚧 次回実装予定

#### services/database (PostgreSQLサービス)
- Docker Composeでのpostgresql起動
- データベーススキーマ定義
- host-agentからの同期機能実装
  - ローカルSQLite → PostgreSQLバッチ同期
  - 同期済みレコードの管理（synced_atカラム）

目的: ローカルキャッシュ+中央DBアーキテクチャの実現

### 📋 未実装（計画中）

#### host-agent/ (追加コレクター)
- **BrowserActivityParser**: ブラウザ活動解析
- **GitHubMonitor**: コミット・PR追跡（API経由）
- **SNSMonitor**: Bluesky等のSNS投稿収集

#### services/ (その他コンテナサービス)
- **ai-analyzer**: AI分析エンジン
- **api-gateway**: APIゲートウェイ
- **web-ui**: Webフロントエンド
- **collector-service**: API経由データ収集

#### shared/
- データモデル定義
- ユーティリティライブラリ

詳細: `docs/software_idea-ai_assited_todo.md`

---

## Architecture

### Current Architecture (Phase 1)

```
host-agent/
├── collectors/
│   ├── linux_x11_monitor.py     ✅ Linux X11デスクトップモニター
│   └── filesystem_watcher.py    ✅ ファイルシステム監視
├── common/
│   ├── models.py                ✅ データモデル
│   └── database.py              ✅ 分離されたDB操作クラス
├── config/
│   └── config.yaml              ✅ 設定ファイル
├── scripts/
│   ├── show_sessions.py         ✅ セッション表示
│   ├── show_file_events.py      ✅ ファイルイベント表示
│   └── reset_database.py        ✅ DB初期化
└── data/
    ├── desktop_activity.db      ✅ デスクトップアクティビティDB
    └── file_changes.db          ✅ ファイル変更イベントDB
```

### Planned Architecture (Phase 2+)

```
reprospective/
├── host-agent/              # ホスト環境エージェント
│   ├── collectors/          # データ収集（ファイル、デスクトップ）
│   ├── common/              # 共通ライブラリ
│   └── data/                # ローカルSQLiteキャッシュ
├── services/                # Dockerサービス
│   ├── database/            # PostgreSQL
│   ├── ai-analyzer/         # AI分析
│   ├── api-gateway/         # API
│   └── web-ui/              # フロントエンド
└── shared/                  # 共有ライブラリ
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

### host-agent の開発

```bash
cd host-agent

# 仮想環境の有効化
source venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt

# コレクター起動
python collectors/linux_x11_monitor.py      # デスクトップ監視
python collectors/filesystem_watcher.py      # ファイル監視

# データ確認
python scripts/show_sessions.py             # セッション表示
python scripts/show_file_events.py          # ファイルイベント表示

# データベース初期化
python scripts/reset_database.py            # 全DB削除
python scripts/reset_database.py --desktop  # デスクトップDBのみ
python scripts/reset_database.py --files    # ファイルDBのみ
```

### テスト方針

- 現在は手動テスト
- データ確認: `scripts/show_sessions.py`, `scripts/show_file_events.py`
- クリーンテスト: `scripts/reset_database.py`

---

## 実装履歴

### 2025-10-25: データベース分離アーキテクチャ実装

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

**次のステップ:**
PostgreSQL同期機能の実装により、Phase 2のアーキテクチャへ移行

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
├── software_idea-ai_assited_todo.md      # 企画書（日本語）
└── design/                               # 設計ドキュメント
    ├── host_agent-desktop_activity_monitor.md        # DesktopActivityMonitor設計
    └── technical_decision-database_architecture.md   # DB設計判断
```

設計ドキュメントは概要のみ記載。詳細実装はソースコードとREADMEを参照。

---

## Quick Reference

### よく使うコマンド

```bash
# モニター起動
cd host-agent && source venv/bin/activate && python collectors/linux_x11_monitor.py

# 最近のセッション表示
python scripts/show_sessions.py 20

# データベース初期化
python scripts/reset_database.py
```

### 主要ファイル

- `host-agent/collectors/linux_x11_monitor.py`: デスクトップモニター本体
- `host-agent/common/models.py`: ActivitySessionデータクラス
- `host-agent/common/database.py`: SQLite操作
- `host-agent/config/config.yaml`: 設定ファイル

---

## Next Steps (予定)

1. FileSystemWatcher実装
2. BrowserActivityParser実装
3. Docker Composeセットアップ（PostgreSQL、Web UI）
4. AI分析エンジンのプロトタイプ
5. 対話的レビューUIのプロトタイプ

---

## License

Apache License 2.0
