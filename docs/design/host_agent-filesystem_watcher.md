# FileSystemWatcher 設計メモ

## 実装状況

🚧 **未実装** - 設計フェーズ

---

## 目的

ホスト環境で動作するファイルシステム監視コンポーネント。
ユーザーが指定したディレクトリ配下のファイル変更（作成・更新・削除）を検出し、ユーザーの作業活動を記録する。

## 設計方針

### 監視対象の範囲

**原則**: ユーザーが設定ファイルで明示的に指定したディレクトリとそのサブディレクトリのみを監視。

- 自動的にホームディレクトリ全体を監視することはしない
- ユーザーが意図しないディレクトリの監視を防ぐ
- プライバシーとパフォーマンスの両立

### 設定方法の進化

#### Phase 1（初期実装）: ローカル設定ファイル

```yaml
# config/config.yaml
filesystem_watcher:
  enabled: true
  monitored_directories:
    - /home/user/work/projects
    - /home/user/Documents/notes
```

- ユーザーが手動で`config.yaml`を編集
- シンプルで実装が容易
- host-agentの再起動が必要

#### Phase 2（将来）: Webフロントエンドからの設定

```
┌─────────────────────────────────────┐
│ Web UI (services)                   │
│  監視設定画面                        │
│   ├─ ディレクトリリスト表示         │
│   │   ├─ /home/user/work  [ON]      │
│   │   ├─ /home/user/docs  [OFF]     │
│   │   └─ /tmp/project     [ON]      │
│   ├─ ディレクトリ追加              │
│   ├─ 一時的にON/OFF切り替え        │
│   └─ 除外パターン設定              │
└─────────┬───────────────────────────┘
          ↓ API経由でDB更新
┌─────────────────────────────────────┐
│ PostgreSQL (services)               │
│  monitored_directories テーブル    │
│   ├─ /home/user/work (enabled=true) │
│   └─ /home/user/docs (enabled=false)│
└─────────┬───────────────────────────┘
          ↓ 定期的に同期
┌─────────────────────────────────────┐
│ host-agent                          │
│  FileSystemWatcher                  │
│   └─ enabled=trueのディレクトリを監視│
└─────────────────────────────────────┘
```

#### 設定データベーススキーマ（Phase 2想定）

```sql
-- 監視対象ディレクトリテーブル
CREATE TABLE monitored_directories (
    id SERIAL PRIMARY KEY,
    directory_path TEXT UNIQUE NOT NULL,    -- 監視対象パス（絶対パス）
    enabled BOOLEAN DEFAULT true,            -- 有効/無効
    display_name TEXT,                       -- 表示名（UIで使用）
    description TEXT,                        -- 説明（「仕事用プロジェクト」など）
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    created_by TEXT,                         -- 追加したユーザー/システム
    updated_by TEXT                          -- 最終更新者
);

-- グローバル設定テーブル
CREATE TABLE filesystem_watcher_settings (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,                -- 設定キー
    value JSONB NOT NULL,                    -- 設定値（JSON形式）
    updated_at TIMESTAMP NOT NULL,
    updated_by TEXT
);

-- 例: 除外パターンの設定
INSERT INTO filesystem_watcher_settings (key, value, updated_at, updated_by) VALUES
('exclude_patterns',
 '[".*\\.tmp$", ".*/node_modules/.*", ".*/__pycache__/.*"]',
 NOW(),
 'web_ui');

-- 例: 監視対象ディレクトリ
INSERT INTO monitored_directories
(directory_path, enabled, display_name, description, created_at, updated_at, created_by) VALUES
('/home/user/work', true, '仕事用', '仕事関連のプロジェクト', NOW(), NOW(), 'web_ui'),
('/home/user/Documents', false, 'ドキュメント', '一時的に無効化中', NOW(), NOW(), 'web_ui'),
('/home/user/projects/experiment', true, '実験プロジェクト', NULL, NOW(), NOW(), 'web_ui');
```

**ディレクトリごとに1レコードのメリット**:
- ✅ 一時的にON/OFFの切り替えが容易（再起動不要）
- ✅ ディレクトリごとにメタデータ（表示名、説明）を保存可能
- ✅ 追加・削除の履歴管理が容易
- ✅ UIで個別の制御が直感的
- ✅ 将来的な拡張が容易（ディレクトリごとの除外パターンなど）

**Phase 1→Phase 2移行戦略**:
1. Phase 1: `config.yaml`の配列形式のみサポート
2. 移行期: 初回起動時に`config.yaml`の内容をDBに移行
3. Phase 2: DBをプライマリ、`config.yaml`はフォールバックのみ

### シンボリックリンクの扱い

#### 基本方針

シンボリックリンクは**追跡しない（follow_symlinks: false）**

**理由**:
1. **無限ループの防止**: 循環参照によるシステム負荷
2. **監視範囲の明確化**: ユーザーが指定した範囲外への拡大を防ぐ
3. **パフォーマンス**: 予期しない大量ファイル監視を防ぐ
4. **プライバシー**: 意図しないディレクトリへのアクセスを防ぐ

#### 動作詳細

| ケース | 動作 | 理由 |
|--------|------|------|
| 監視対象内のシンボリックリンク（ファイル） | リンク自体の作成・削除は記録、リンク先は監視しない | リンク作成は作業の一部として記録 |
| 監視対象内のシンボリックリンク（ディレクトリ） | リンク自体の作成・削除は記録、リンク先は監視しない | 無限ループ防止 |
| 監視対象自体がシンボリックリンク | 実体を解決して監視 | ユーザーが明示的に指定した場合は意図的 |

### 基本機能

1. **ファイル変更の検出**
   - ファイルの作成（新規ファイル）
   - ファイルの更新（既存ファイルの編集）
   - ファイルの削除
   - ファイルの移動・リネーム

2. **監視対象のフィルタリング**
   - 監視対象ディレクトリの指定（ユーザーが明示的に指定）
   - enabled=trueのディレクトリのみ監視
   - 除外パターンの設定（正規表現）
     - 一時ファイル（`*.tmp`, `*.swp`, `*~`）
     - ビルド成果物（`node_modules/`, `__pycache__/`, `target/`, `build/`）
     - VCS関連（`.git/`, `.svn/`）

3. **変更内容の記録**
   - ファイルパス（監視対象ディレクトリからの相対パスも保存）
   - 変更タイプ（作成/更新/削除/移動）
   - タイムスタンプ
   - ファイルサイズ
   - ファイル拡張子
   - 推定プロジェクト（パスから推測）

### データ保存戦略

#### ファイル変更イベントテーブル（SQLite/PostgreSQL共通）

```sql
CREATE TABLE file_change_events (
    id INTEGER PRIMARY KEY,
    event_time INTEGER NOT NULL,           -- UNIXエポック秒
    event_time_iso TEXT NOT NULL,          -- ISO 8601形式
    event_type TEXT NOT NULL,              -- created/modified/deleted/moved
    file_path TEXT NOT NULL,               -- 絶対パス
    file_path_relative TEXT,               -- 相対パス（監視対象ルートからの相対）
    file_name TEXT NOT NULL,               -- ファイル名
    file_extension TEXT,                   -- 拡張子
    file_size INTEGER,                     -- バイト
    is_symlink INTEGER DEFAULT 0,          -- シンボリックリンクか（0 or 1）
    monitored_root TEXT NOT NULL,          -- どの監視対象に属するか
    project_name TEXT,                     -- 推定プロジェクト名
    created_at INTEGER NOT NULL            -- レコード作成時刻
);

CREATE INDEX idx_event_time ON file_change_events(event_time);
CREATE INDEX idx_project_name ON file_change_events(project_name);
CREATE INDEX idx_file_extension ON file_change_events(file_extension);
```

### ファイルタイプの分類

ファイル拡張子から作業種別を推定：

| カテゴリ | 拡張子例 | 作業種別 |
|---------|---------|---------|
| プログラミング | `.py`, `.js`, `.rs`, `.go`, `.java` | 開発 |
| マークアップ | `.html`, `.css`, `.md`, `.xml` | 文書作成 |
| 設定ファイル | `.yaml`, `.json`, `.toml`, `.ini` | 設定 |
| 3Dモデル | `.blend`, `.fbx`, `.obj` | 3Dモデリング |
| 画像 | `.png`, `.jpg`, `.svg`, `.kra`, `.xcf` | グラフィックデザイン |
| 動画 | `.mp4`, `.mov`, `.avi` | 動画編集 |
| ドキュメント | `.docx`, `.pdf`, `.odt` | 文書作成 |

### プロジェクト推定

ファイルパスからプロジェクトを推定：

1. **Gitリポジトリ**: `.git`ディレクトリの親ディレクトリ名
2. **特徴的なファイル**: `package.json`, `Cargo.toml`, `pom.xml`があるディレクトリ
3. **監視対象ディレクトリの直下**: 監視対象直下のディレクトリ名

### パフォーマンス考慮事項

#### 高頻度イベントの対策

1. **バッチ書き込み**
   - イベントをメモリにバッファリング
   - 一定数（例: 100件）または一定時間（例: 10秒）ごとにDB書き込み

2. **重複イベントの除外**
   - 同じファイルの連続した変更を集約
   - 変更検出後、短時間（例: 1秒）のクールダウン期間を設ける

3. **除外パターンの最適化**
   - 頻繁に変更されるファイル（ログファイルなど）を除外
   - システムファイル、一時ファイルを除外

## 技術スタック

### Python実装

- **watchdog**: Pythonのファイルシステム監視ライブラリ
  - クロスプラットフォーム対応
  - inotify（Linux）、FSEvents（macOS）、ReadDirectoryChangesW（Windows）を抽象化
  - イベント駆動型

### 依存パッケージ

```python
# requirements.txt
watchdog>=4.0.0  # ファイルシステム監視
```

## 設定ファイル

### Phase 1: ローカル設定ファイルのみ

```yaml
# config/config.yaml
filesystem_watcher:
  enabled: true

  # 監視対象ディレクトリ（配列形式）
  monitored_directories:
    - /home/user/work
    - /home/user/Documents
    - /home/user/projects

  # シンボリックリンクの扱い
  symlinks:
    follow: false              # シンボリックリンクを追跡しない（推奨）

  # 除外パターン（正規表現）
  exclude_patterns:
    - ".*\\.tmp$"
    - ".*\\.swp$"
    - ".*~$"
    - ".*/node_modules/.*"
    - ".*/__pycache__/.*"
    - ".*/\\.git/.*"
    - ".*/\\.venv/.*"
    - ".*/venv/.*"
    - ".*/build/.*"
    - ".*/dist/.*"
    - ".*/target/.*"
    - ".*\\.log$"

  # バッファ設定
  buffer:
    max_events: 100            # バッファ最大イベント数
    flush_interval: 10         # フラッシュ間隔（秒）
```

### Phase 2: 設定DB統合（将来）

```yaml
# config/config.yaml
filesystem_watcher:
  enabled: true

  # 設定ソース（config_file または database）
  config_source: database     # Phase 2: DBから設定を読み込み

  # DB設定の同期間隔
  config_sync_interval: 60    # 秒（DBから設定を再読み込みする間隔）

  # フォールバック設定（DBが利用不可の場合）
  fallback:
    monitored_directories:
      - /home/user/work
```

## 動作フロー

### Phase 1

```
1. 起動時
   ├─ config.yamlから設定を読み込み
   ├─ 各ディレクトリの存在確認
   ├─ 除外パターンをコンパイル
   ├─ watchdogのObserverを初期化（follow_symlinks=False）
   └─ 各監視対象にEventHandlerを登録

2. ファイル変更検出時
   ├─ イベントを受信（created/modified/deleted/moved）
   ├─ 除外パターンにマッチするか確認 → スキップ
   ├─ ファイル情報を収集（パス、サイズ、拡張子）
   ├─ プロジェクト名を推定
   ├─ イベントをバッファに追加
   └─ バッファが閾値に達したらDB書き込み

3. 定期フラッシュ（10秒ごと）
   └─ バッファ内のイベントをDBに一括書き込み

4. 終了時
   ├─ バッファ内の残りイベントをフラッシュ
   ├─ Observerを停止
   └─ データベース接続をクローズ
```

### Phase 2（設定DB統合後）

```
1. 起動時
   ├─ データベースからmonitored_directoriesテーブルを読み込み
   │   ├─ WHERE enabled = true の行のみ取得
   │   └─ 失敗時: config.yamlのフォールバック設定を使用
   ├─ filesystem_watcher_settingsから除外パターンなど読み込み
   ├─ （以下Phase 1と同じ）

2. 定期的な設定同期（60秒ごと）
   ├─ monitored_directoriesテーブルから最新設定を取得
   │   └─ SELECT * FROM monitored_directories WHERE enabled = true
   ├─ 設定が変更されているか確認
   │   ├─ 新しいディレクトリが追加された
   │   ├─ ディレクトリがenabled=falseに変更された
   │   └─ ディレクトリが削除された
   ├─ 変更あり
   │   ├─ 変更のあったディレクトリのObserverのみ停止/起動
   │   └─ ログに記録（「/home/user/work の監視を開始」など）
   └─ 変更なし → 何もしない

3. ファイル変更検出時（Phase 1と同じ）

4. 終了時（Phase 1と同じ）
```

## Webフロントエンドの操作例（Phase 2）

### 監視ディレクトリ管理画面

```
┌────────────────────────────────────────────────────────────┐
│ ファイルシステム監視設定                                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ 監視対象ディレクトリ                                        │
│                                                            │
│ ┌────────────────────────────────────────────────────┐    │
│ │ /home/user/work                           [ON]  [×] │    │
│ │ 仕事用                                              │    │
│ │ 最終更新: 2025-10-25 15:30                         │    │
│ └────────────────────────────────────────────────────┘    │
│                                                            │
│ ┌────────────────────────────────────────────────────┐    │
│ │ /home/user/Documents                     [OFF] [×] │    │
│ │ ドキュメント                                        │    │
│ │ 最終更新: 2025-10-24 12:00                         │    │
│ └────────────────────────────────────────────────────┘    │
│                                                            │
│ [+ ディレクトリを追加]                                      │
│                                                            │
│ 除外パターン                                                │
│ ┌────────────────────────────────────────────────────┐    │
│ │ .*\.tmp$                                           │    │
│ │ .*/node_modules/.*                                 │    │
│ │ .*/__pycache__/.*                                  │    │
│ └────────────────────────────────────────────────────┘    │
│ [編集]                                                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**操作**:
- ON/OFFトグル: 即座に反映（次の同期サイクルで有効化/無効化）
- [×]: ディレクトリを削除（確認ダイアログ表示）
- [+ ディレクトリを追加]: ファイルパス入力ダイアログ

## セキュリティとプライバシー

1. **監視範囲の明確化**
   - ユーザーが明示的に指定したディレクトリのみ監視
   - シンボリックリンクを追跡しないことで、意図しない範囲の監視を防ぐ

2. **機密ファイルの除外**
   - `.env`, `credentials.json`, `*.key`, `*.pem`などを除外パターンに含める
   - ファイル内容は読み取らない（パスとメタデータのみ）

3. **Webフロントエンドからの設定変更（Phase 2）**
   - 認証・認可の実装（設定変更権限の管理）
   - ディレクトリパスのバリデーション（危険なパスを拒否）
   - 監査ログ（誰がいつ設定を変更したか記録）

## 将来的な拡張

### Phase 2
- **Webフロントエンドからの設定**: 監視対象ディレクトリをUI上で追加・削除・ON/OFF
- **設定DB統合**: PostgreSQLに設定を保存（ディレクトリごとに1レコード）
- **動的な設定反映**: 再起動なしで監視対象を追加・削除

### Phase 3
- **ディレクトリごとの詳細設定**: 個別の除外パターン、バッファサイズなど
- **ファイル差分解析**: Git diffを利用した変更内容の解析
- **複数ホストの統合管理**: 複数PCの監視設定を一元管理

## テスト確認項目

### Phase 1
- [ ] ファイル作成イベントの検出
- [ ] ファイル更新イベントの検出
- [ ] ファイル削除イベントの検出
- [ ] 除外パターンが正しく動作
- [ ] シンボリックリンクが追跡されない
- [ ] 監視対象がシンボリックリンクの場合、実体が監視される
- [ ] 監視対象ディレクトリが存在しない場合の処理
- [ ] バッファリングとバッチ書き込み
- [ ] プロジェクト名の推定
- [ ] ファイルタイプの分類

### Phase 2
- [ ] データベースから設定を読み込める
- [ ] enabled=trueのディレクトリのみ監視される
- [ ] ディレクトリのON/OFF切り替えが反映される
- [ ] 新しいディレクトリの追加が反映される
- [ ] ディレクトリの削除が反映される
- [ ] フォールバック設定が動作する
- [ ] Webフロントエンドから設定を変更できる

## 参考資料

- watchdogライブラリ: https://pypi.org/project/watchdog/
- DesktopActivityMonitor実装: `host-agent/collectors/linux_x11_monitor.py`
- データベース設計: `docs/design/technical_decision-database_architecture.md`
