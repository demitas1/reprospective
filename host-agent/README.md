# Reprospective Host Agent

ホスト環境で動作するアクティビティ収集エージェント

## 概要

Host Agentは、ユーザーのデスクトップ上での活動を自動的に収集し、データベースに記録します。

現在実装されている機能：
- **DesktopActivityMonitor (Linux X11)**: アクティブウィンドウの追跡とセッション記録
- **FileSystemWatcher**: 指定ディレクトリ配下のファイル変更監視とイベント記録

## ディレクトリ構成

```
host-agent/
├── collectors/                # データ収集コンポーネント
│   ├── linux_x11_monitor.py   # Linux X11デスクトップモニター
│   ├── filesystem_watcher.py  # ファイルシステム監視
│   └── __init__.py
├── common/                    # 共通モジュール
│   ├── models.py              # データモデル定義
│   ├── database.py            # データベース操作
│   └── __init__.py
├── config/                    # 設定ファイル
│   ├── config.yaml            # 設定ファイル（.gitignore対象）
│   └── config.example.yaml    # 設定ファイルサンプル
├── data/                      # データディレクトリ（.gitignore対象）
│   ├── desktop_activity.db    # デスクトップアクティビティDB（自動生成）
│   └── file_changes.db        # ファイル変更イベントDB（自動生成）
├── scripts/                   # デバッグ・ユーティリティスクリプト
│   ├── show_sessions.py       # デスクトップセッション表示スクリプト
│   ├── show_file_events.py    # ファイルイベント表示スクリプト
│   └── reset_database.py      # データベース初期化スクリプト
├── venv/                      # Python仮想環境（.gitignore対象）
├── requirements.txt           # 依存パッケージ
└── README.md                  # このファイル
```

## セットアップ

### 前提条件

- Python 3.10以上
- Linux X11環境（Wayland未対応）
- `xdotool` および `xprop` コマンド
- `sqlite3` コマンド（データベース確認用）

### システムコマンドのインストール

```bash
# Ubuntu/Debian
sudo apt install xdotool x11-utils sqlite3

# Fedora
sudo dnf install xdotool xorg-x11-utils sqlite

# Arch Linux
sudo pacman -S xdotool xorg-xprop sqlite
```

### Pythonパッケージのインストール

```bash
# 仮想環境の有効化
cd host-agent
source venv/bin/activate

# 依存パッケージをインストール
pip install -r requirements.txt
```

### 設定ファイルの準備

設定ファイルは既に作成されています（`config/config.yaml`）。
必要に応じて監視間隔などを変更してください。

```yaml
# config/config.yaml
database:
  desktop_activity:
    path: data/desktop_activity.db
  file_changes:
    path: data/file_changes.db

desktop_monitor:
  enabled: true
  monitor_interval: 10

filesystem_watcher:
  enabled: true
  monitored_directories:
    - /path/to/your/work/directory
```

詳細は`config/config.example.yaml`を参照してください。

## 使い方

### デスクトップモニターの起動

```bash
# 仮想環境を有効化
source venv/bin/activate

# モニターを起動
python collectors/linux_x11_monitor.py
```

起動すると、以下のような動作をします：

アクティブウィンドウの変化を監視し、セッション情報を `data/desktop_activity.db` に保存します。

### ファイルシステムウォッチャーの起動

```bash
# 仮想環境を有効化
source venv/bin/activate

# ファイルシステムウォッチャーを起動
python collectors/filesystem_watcher.py
```

指定ディレクトリのファイル変更を監視し、イベントを `data/file_changes.db` に保存します。

### 停止方法

`Ctrl+C` で停止します。現在のセッションやバッファ内のイベントは自動的に保存されます。

## データベース

各コレクターは独立したSQLiteデータベースを使用します（スレッド競合を回避）：

- `data/desktop_activity.db`: デスクトップアクティビティセッション
- `data/file_changes.db`: ファイル変更イベント

テーブル定義の詳細は`common/database.py`を参照してください。

### データベースの確認

#### デスクトップセッションの確認

デバッグ用スクリプトを使用して、最近のセッションを確認できます：

```bash
# 仮想環境を有効化
source venv/bin/activate

# 最近の10件を表示（デフォルト）
python scripts/show_sessions.py

# 最近の20件を表示
python scripts/show_sessions.py 20

# 最近の100件を表示
python scripts/show_sessions.py 100
```

#### ファイルイベントの確認

ファイル変更イベントも同様に確認できます：

```bash
# 仮想環境を有効化
source venv/bin/activate

# 最近の50件を表示（デフォルト）
python scripts/show_file_events.py

# 最近の100件を表示
python scripts/show_file_events.py 100
```

#### SQLiteコマンドラインで直接確認

```bash
# デスクトップアクティビティDB
sqlite3 data/desktop_activity.db "SELECT * FROM desktop_activity_sessions ORDER BY start_time DESC LIMIT 10;"

# ファイル変更イベントDB
sqlite3 data/file_changes.db "SELECT * FROM file_change_events ORDER BY event_time DESC LIMIT 10;"
```

### データベースの初期化

```bash
python scripts/reset_database.py              # 全DBを削除
python scripts/reset_database.py --desktop    # デスクトップDBのみ削除
python scripts/reset_database.py --files      # ファイルDBのみ削除
```

## アーキテクチャ

### データベース分離

各コレクターは独立したSQLiteデータベースを使用し、スレッド競合を回避：
- `DesktopActivityDatabase`: デスクトップセッション管理
- `FileChangeDatabase`: ファイルイベント管理

詳細は`docs/design/technical_decision-database_separation.md`を参照。

### 将来的な拡張

- PostgreSQL同期（ローカルキャッシュ+バッチ同期）
- Web UIでの設定管理
- Wayland対応
- BrowserActivityParser

## ライセンス

Apache License 2.0
