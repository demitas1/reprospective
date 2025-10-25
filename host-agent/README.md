# Reprospective Host Agent

ホスト環境で動作するアクティビティ収集エージェント

## 概要

Host Agentは、ユーザーのデスクトップ上での活動を自動的に収集し、データベースに記録します。

現在実装されている機能：
- **DesktopActivityMonitor (Linux X11)**: アクティブウィンドウの追跡とセッション記録

## ディレクトリ構成

```
host-agent/
├── collectors/              # データ収集コンポーネント
│   ├── linux_x11_monitor.py # Linux X11デスクトップモニター
│   └── __init__.py
├── common/                  # 共通モジュール
│   ├── models.py            # データモデル定義
│   ├── database.py          # データベース操作
│   └── __init__.py
├── config/                  # 設定ファイル
│   ├── config.yaml          # 設定ファイル（.gitignore対象）
│   └── config.example.yaml  # 設定ファイルサンプル
├── data/                    # データディレクトリ（.gitignore対象）
│   └── host_agent.db        # SQLiteデータベース（自動生成）
├── scripts/                 # デバッグ・ユーティリティスクリプト
│   ├── show_sessions.py     # セッション表示スクリプト
│   └── reset_database.py    # データベース初期化スクリプト
├── venv/                    # Python仮想環境（.gitignore対象）
├── requirements.txt         # 依存パッケージ
└── README.md               # このファイル
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
desktop_monitor:
  enabled: true
  monitor_interval: 10  # 監視間隔（秒）
```

## 使い方

### デスクトップモニターの起動

```bash
# 仮想環境を有効化
source venv/bin/activate

# モニターを起動
python collectors/linux_x11_monitor.py
```

起動すると、以下のような動作をします：

1. 10秒ごとにアクティブウィンドウをチェック
2. ウィンドウが変わったら前のセッションを終了し、新しいセッションを開始
3. セッション情報を `data/host_agent.db` に保存

### 停止方法

`Ctrl+C` で停止します。現在のセッションは自動的に終了処理されます。

## データベース

### SQLiteデータベース構造

**desktop_activity_sessions テーブル**:

| カラム名 | 型 | 説明 |
|---------|---|------|
| id | INTEGER | プライマリキー |
| start_time | INTEGER | 開始時刻（UNIXエポック秒） |
| end_time | INTEGER | 終了時刻（UNIXエポック秒） |
| start_time_iso | TEXT | 開始時刻（ISO 8601形式） |
| end_time_iso | TEXT | 終了時刻（ISO 8601形式） |
| application_name | TEXT | アプリケーション名 |
| window_title | TEXT | ウィンドウタイトル |
| duration_seconds | INTEGER | 継続時間（秒） |
| created_at | INTEGER | レコード作成時刻 |
| updated_at | INTEGER | レコード更新時刻 |

### データベースの確認

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

または、SQLiteコマンドラインで直接確認：

```bash
# SQLiteコマンドラインで確認
sqlite3 data/host_agent.db

# 最近のセッションを表示
SELECT
    datetime(start_time, 'unixepoch', 'localtime') as start,
    datetime(end_time, 'unixepoch', 'localtime') as end,
    duration_seconds,
    application_name,
    substr(window_title, 1, 50) as title
FROM desktop_activity_sessions
ORDER BY start_time DESC
LIMIT 10;
```

### データベースの初期化

クリーンな状態からテストする場合、データベースを初期化できます：

```bash
# 仮想環境を有効化
source venv/bin/activate

# データベースを初期化（確認プロンプトあり）
python scripts/reset_database.py

# 確認なしで強制的に初期化
python scripts/reset_database.py --force
```

注意: この操作はすべてのセッションデータを削除します。

## ログレベル

`config/config.yaml` でログレベルを変更できます：

```yaml
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
```

- **DEBUG**: 詳細なデバッグ情報（セッション継続中のログも出力）
- **INFO**: 通常の情報（セッション開始・終了のみ）
- **WARNING**: 警告のみ
- **ERROR**: エラーのみ

## トラブルシューティング

### "xdotool: command not found"

`xdotool` がインストールされていません。セットアップの手順に従ってインストールしてください。

### "設定ファイルが見つかりません"

`config/config.yaml` が存在しない場合、`config/config.example.yaml` をコピーしてください：

```bash
cp config/config.example.yaml config/config.yaml
```

### Waylandで動作しない

現在、X11環境のみサポートしています。Waylandでは動作しません。
X11セッションで再ログインするか、将来のWayland対応版をお待ちください。

## 開発

### モジュール構成

- **models.py**: `ActivitySession` データクラス定義
- **database.py**: SQLite操作（CRUD）
- **linux_x11_monitor.py**: X11ウィンドウ情報取得とセッション管理

### 将来的な拡張

- Wayland対応
- FileSystemWatcher（ファイル変更監視）
- BrowserActivityParser（ブラウザ活動解析）
- PostgreSQL同期機能

## ライセンス

Apache License 2.0
