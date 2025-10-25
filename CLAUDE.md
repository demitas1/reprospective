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
- **SQLiteデータベース**: 活動セッションの保存
- **設定管理**: YAML形式の設定ファイル
- **デバッグツール**: セッション表示、データベース初期化スクリプト

詳細: `host-agent/README.md`

### 📋 未実装（計画中）

#### host-agent/ (追加コレクター)
- **FileSystemWatcher**: ファイル変更監視
- **BrowserActivityParser**: ブラウザ活動解析
- **GitHubMonitor**: コミット・PR追跡（API経由）
- **SNSMonitor**: Bluesky等のSNS投稿収集

#### services/ (Dockerコンテナサービス)
- **database**: PostgreSQLサービス
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
│   └── linux_x11_monitor.py    ✅ Linux X11デスクトップモニター
├── common/
│   ├── models.py                ✅ データモデル
│   └── database.py              ✅ SQLite操作
├── config/
│   └── config.yaml              ✅ 設定ファイル
├── scripts/
│   ├── show_sessions.py         ✅ セッション表示
│   └── reset_database.py        ✅ DB初期化
└── data/
    └── host_agent.db            ✅ SQLiteデータベース
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

- **Phase 1**: SQLite単独（`host-agent/data/host_agent.db`）
  - ボリュームマウントでservicesと共有予定
  - 書き込み頻度が低いため十分

- **Phase 2**: PostgreSQL + SQLiteローカルキャッシュ
  - host-agent: ローカルSQLiteに常時書き込み
  - 定期的にPostgreSQLへバッチ同期
  - オフライン耐性、高可用性を実現

詳細: `docs/design/technical_decision-database_architecture.md`

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

# モニター起動
python collectors/linux_x11_monitor.py

# セッション確認
python scripts/show_sessions.py

# データベース初期化
python scripts/reset_database.py
```

### テスト方針

- 現在は手動テスト
- データベース内容の確認: `scripts/show_sessions.py`
- クリーンテスト: `scripts/reset_database.py`

---

## Key Design Principles

1. **段階的実装**: まず動くものを作り、徐々に拡張
2. **Minimize manual input**: 自動収集を優先、手動入力は最小限
3. **Privacy and security**: API認証情報の暗号化、ファイルアクセス権限の尊重
4. **Lightweight**: バックグラウンド動作時にユーザー作業に影響を与えない
5. **SOLID principles**: 簡潔で拡張しやすいコード設計

---

## Important Implementation Notes

### コーディング規約

- **日本語使用箇所**: コメント、ドキュメント、ユーザー向けメッセージ
- **英語使用箇所**: ディレクトリ名、ファイル名、変数名、関数名
- **設定ファイル**: YAML形式、コメントは日本語可

### セキュリティ

- API認証情報は環境変数または暗号化して保存
- `.gitignore`でデータベースファイルや設定ファイルを除外
- プライバシーに配慮したログ出力

### データベース

- タイムスタンプはUNIXエポック秒とISO 8601形式の両方を保存
- セッション管理: 同じウィンドウが続く場合は記録しない（重複排除）
- エラー時も動作継続（ログ記録してスキップ）

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
