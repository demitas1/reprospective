# InputMonitor 設計書

## 実装状況

✅ 設計完了（2025-11-07）
✅ 設計更新完了（2025-11-08）- スレッド排他制御、強制終了対策、データ同期方針を追加
📋 実装準備中

---

## 目的

ホスト環境で動作する入力デバイス監視コンポーネント。
マウス、キーボードの入力を監視し、入力活動がある期間を記録する。

**プライバシー保護**: 入力イベントの発生のみ検知し、具体的な入力内容（キーストローク、マウス座標等）は記録しない。

---

## 設計方針

### セッション管理

- **セッション**: マウスまたはキーボードの入力が設定した一定時間以内に連続して行われている期間をユーザーが活動している時間として記録する
- **無操作タイムアウト**: デフォルト120秒（設定可能）の間、マウスもキーボードも入力がない場合、活動中断と判断しセッション終了とする
- **セッション再開**: 活動中断状態からマウスまたはキーボードの入力があった場合、新しいセッションが開始されたと判断する
- **セッション統合**: マウスとキーボードが同時に動いている場合、単一のセッションとして記録（別々に分けない）

### 記録するデータ

**最小限のデータのみ記録**（粒度: A）:
- セッション開始時刻（UNIXタイムスタンプ）
- セッション終了時刻（UNIXタイムスタンプ）
- 継続時間（秒）

**記録しないデータ**:
- 入力種別（マウス/キーボード）
- キーストローク内容
- マウス座標・移動距離
- その他の詳細統計

**理由**: シンプルに「ユーザーが活動していた期間」を記録することが目的。詳細な統計は不要。

### データ保存

**SQLiteローカルキャッシュ**:
- データベースファイル: `data/input_activity.db`
- テーブル: `input_activity_sessions`

**PostgreSQL中央DB**:
- テーブル: `input_activity_sessions`
- 既存の`DataSyncManager`を使用してバッチ同期

**スキーマ設計**:
```sql
-- SQLite版
CREATE TABLE input_activity_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time INTEGER NOT NULL,          -- UNIXタイムスタンプ（秒）
    end_time INTEGER,                     -- セッション継続中はNULL
    start_time_iso TEXT NOT NULL,         -- ISO 8601形式
    end_time_iso TEXT,
    duration_seconds INTEGER,             -- 継続時間（秒）
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    synced_at INTEGER                     -- PostgreSQL同期用
);

CREATE INDEX idx_input_start_time ON input_activity_sessions(start_time);
CREATE INDEX idx_input_synced_at ON input_activity_sessions(synced_at);

-- PostgreSQL版
CREATE TABLE input_activity_sessions (
    id SERIAL PRIMARY KEY,
    start_time BIGINT NOT NULL,
    end_time BIGINT,
    start_time_iso TIMESTAMP NOT NULL,
    end_time_iso TIMESTAMP,
    duration_seconds INTEGER,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    host_identifier TEXT NOT NULL,        -- 同期元ホスト識別子
    synced_from_local_id INTEGER          -- ローカルDB ID
);

CREATE INDEX idx_input_start_time ON input_activity_sessions(start_time);
CREATE INDEX idx_input_host_identifier ON input_activity_sessions(host_identifier);
```

### 設定管理

`config.yaml`に以下の設定を追加:

```yaml
# 入力デバイス監視設定
input_monitor:
  enabled: true                    # 監視有効化（デフォルト: true）
  idle_timeout_seconds: 120        # 無操作タイムアウト（秒）
  timeout_check_interval: 10       # タイムアウトチェック間隔（秒）
```

**デフォルト設定の理由**:
- `enabled: true`: アクティビティサマリー生成機能の精度向上に必須
- 入力内容は記録しないため、プライバシーリスクは最小限

環境変数:
```bash
SQLITE_INPUT_PATH=data/input_activity.db  # SQLiteパス（オプション）
```

### エラーハンドリング

- **入力監視失敗**: ライブラリ初期化エラー時、フォールバック実装を試行
- **権限エラー**: ユーザーに権限不足を通知し、セットアップ手順を表示
- **データベースエラー**: 既存のhost-agentと同様のエラーハンドリング
- **同期エラー**: 既存の`DataSyncManager`のリトライロジックを使用
- **強制終了**: シグナルハンドラで正常終了処理を実行、未終了セッションは起動時に削除

### 環境要件

**pynput使用時**:
- **X11セッション内で起動が必須**（`DISPLAY`環境変数が必要）
- SSH経由でのリモート起動は対象外
- X11セッションがない場合、自動的にフォールバック実装を試行

**python-xlib使用時**:
- X11環境専用
- pynputと同様、`DISPLAY`環境変数が必要

**python-evdev使用時**:
- フォールバック実装のため、必要になってから再検討
- ユーザーが`input`グループに所属する必要がある

---

## 技術スタック

### 依存ツール

**優先順位順に実装を試行**:

1. **pynput** (第一選択)
   - クロスプラットフォーム、使いやすい
   - X11環境で通常ユーザー権限で動作
   - インストール: `pip install pynput`

2. **python-xlib** (フォールバック1)
   - X11イベント監視
   - X11環境専用
   - インストール: `pip install python-xlib`

3. **python-evdev** (フォールバック2)
   - Linuxカーネルの入力デバイスインターフェース
   - rootまたはinputグループ権限が必要
   - インストール: `pip install evdev`

**その他**:
- **PyYAML**: 設定ファイル読み込み
- **asyncio**: 非同期処理
- **threading**: セッションタイムアウト監視

### 対応環境

**Phase 1（現在）**:
- Linux X11環境

**Phase 2（将来）**:
- Linux Wayland環境
- Windows
- macOS

---

## アーキテクチャ

### データモデル

`common/models.py`に`InputActivitySession`クラスを追加:

```python
@dataclass
class InputActivitySession:
    """
    入力活動セッションを表すデータクラス

    マウスまたはキーボードの入力が連続している期間を表す。
    """

    id: Optional[int] = None           # データベースのID
    start_time: int = 0                # 開始時刻（UNIXエポック秒）
    end_time: Optional[int] = None     # 終了時刻（UNIXエポック秒）
    created_at: int = 0                # レコード作成時刻
    updated_at: int = 0                # レコード更新時刻

    @property
    def start_time_iso(self) -> str:
        """開始時刻のISO 8601形式文字列"""
        return datetime.fromtimestamp(self.start_time).isoformat()

    @property
    def end_time_iso(self) -> Optional[str]:
        """終了時刻のISO 8601形式文字列"""
        if self.end_time:
            return datetime.fromtimestamp(self.end_time).isoformat()
        return None

    @property
    def duration_seconds(self) -> Optional[int]:
        """セッションの継続時間（秒）"""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None
```

### データベースクラス

`common/database.py`に`InputActivityDatabase`クラスを追加:

```python
class InputActivityDatabase:
    """入力活動セッションのデータベース操作クラス"""

    def __init__(self, db_path: str):
        """初期化"""

    def create_session(self, session: InputActivitySession) -> int:
        """セッション作成"""

    def update_session_end_time(self, session_id: int, end_time: int) -> None:
        """セッション終了時刻を更新"""

    def get_unsynced_sessions(self, limit: int = 100) -> List[InputActivitySession]:
        """未同期セッション取得"""

    def mark_sessions_as_synced(self, session_ids: List[int]) -> None:
        """同期済みフラグ更新"""

    def delete_incomplete_sessions(self) -> int:
        """未終了セッション（end_time=NULL）を削除

        プロセス強制終了時に残った不完全なセッションをクリーンアップする。
        起動時に呼び出される。

        Returns:
            int: 削除されたセッション数
        """
```

### コレクタークラス

`collectors/input_monitor.py`:

```python
import threading

class InputMonitor:
    """入力デバイス監視クラス"""

    def __init__(self, config: dict, database: InputActivityDatabase):
        """初期化"""
        self.config = config
        self.database = database
        self.logger = logging.getLogger(__name__)

        # 設定
        self.idle_timeout = config.get('input_monitor', {}).get('idle_timeout_seconds', 120)
        self.timeout_check_interval = config.get('input_monitor', {}).get('timeout_check_interval', 10)

        # セッション管理
        self.current_session: Optional[InputActivitySession] = None
        self.current_session_id: Optional[int] = None
        self.last_input_time: float = 0

        # スレッド間排他制御
        self.session_lock = threading.Lock()

        # 監視実行フラグ
        self.is_running = False

        # タイムアウトチェックスレッド
        self.timeout_thread: Optional[threading.Thread] = None

        # pynputリスナー
        self.mouse_listener = None
        self.keyboard_listener = None

    def start_monitoring(self) -> None:
        """監視開始（pynput → xlib → evdev の順で試行）"""

    def stop_monitoring(self) -> None:
        """監視停止（リスナー停止、スレッド終了、セッション終了）"""

    def _try_pynput(self) -> bool:
        """pynputで監視を試行

        環境要件:
        - DISPLAY環境変数が設定されていること（X11セッション）
        - pynputがインストールされていること

        Returns:
            bool: 成功した場合True
        """

    def _try_xlib(self) -> bool:
        """xlibで監視を試行（フォールバック1）

        環境要件:
        - DISPLAY環境変数が設定されていること（X11セッション）
        - python-xlibがインストールされていること

        Returns:
            bool: 成功した場合True
        """

    def _try_evdev(self) -> bool:
        """evdevで監視を試行（フォールバック2）

        環境要件:
        - ユーザーがinputグループに所属していること
        - evdevがインストールされていること

        Returns:
            bool: 成功した場合True
        """

    def _on_input_event(self) -> None:
        """入力イベント発生時のコールバック（マウス・キーボード共通）

        スレッドセーフ: session_lockで保護
        """

    def _check_session_timeout(self) -> None:
        """セッションタイムアウトチェック（別スレッドで定期実行）

        idle_timeout秒間入力がない場合、セッションを終了する。
        timeout_check_interval秒ごとにチェックを実行。

        スレッドセーフ: session_lockで保護
        """

    def _start_session(self) -> None:
        """セッション開始

        注意: session_lockで保護された状態で呼び出すこと
        """

    def _end_session(self) -> None:
        """セッション終了

        注意: session_lockで保護された状態で呼び出すこと
        """
```

### 環境要件チェック

pynput/xlibを使用する前に、DISPLAY環境変数の存在を確認する：

```python
import os

def _try_pynput(self) -> bool:
    """pynputで監視を試行"""
    # DISPLAY環境変数チェック
    if not os.environ.get('DISPLAY'):
        self.logger.warning(
            "DISPLAY環境変数が設定されていません（X11セッションが必要）\n"
            "InputMonitorはX11セッション内で起動してください。\n"
            "SSH経由でのリモート起動は対象外です。"
        )
        return False

    try:
        from pynput import mouse, keyboard

        # リスナー作成
        self.mouse_listener = mouse.Listener(
            on_move=self._on_input_event,
            on_click=self._on_input_event,
            on_scroll=self._on_input_event
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_input_event,
            on_release=self._on_input_event
        )

        # リスナー開始
        self.mouse_listener.start()
        self.keyboard_listener.start()

        self.logger.info("pynputによる入力監視を開始しました")
        return True

    except ImportError:
        self.logger.warning("pynputがインストールされていません: pip install pynput")
        return False
    except Exception as e:
        self.logger.warning(f"pynput初期化失敗: {e}")
        return False
```

### スレッド間排他制御

InputMonitorは以下の2つのスレッドから`current_session`にアクセスするため、`threading.Lock`を使用して排他制御を行う：

1. **入力イベントスレッド**: pynputのリスナーコールバック（`_on_input_event`）
2. **タイムアウトチェックスレッド**: 定期的にタイムアウトを確認（`_check_session_timeout`）

**実装例**:
```python
def _on_input_event(self, *args, **kwargs):
    """入力イベント発生時のコールバック

    pynputリスナーから呼び出されるため、引数は可変長。
    引数の内容は使用せず、イベント発生のみ記録する。
    """
    with self.session_lock:
        current_time = time.time()

        if self.current_session is None:
            self._start_session()

        self.last_input_time = current_time

def _check_session_timeout(self):
    """タイムアウトチェックスレッド"""
    while self.is_running:
        time.sleep(self.timeout_check_interval)

        with self.session_lock:
            if self.current_session and \
               (time.time() - self.last_input_time) > self.idle_timeout:
                self._end_session()
```

### 強制終了時の対策

プロセスがkillされた場合に備えて、以下の対策を実装する：

#### 1. シグナルハンドラ登録

SIGTERM, SIGINTを捕捉して正常終了処理を実行：

```python
import signal
import sys

def main():
    monitor = InputMonitor(config, database)

    def signal_handler(sig, frame):
        logger.info(f"シグナル {sig} を受信しました")
        monitor.stop_monitoring()
        database.close()
        sys.exit(0)

    # シグナルハンドラ登録
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # 監視開始
    monitor.start_monitoring()
```

#### 2. 未終了セッションの削除

起動時に`end_time=NULL`のセッションを削除：

```python
class InputActivityDatabase:
    def delete_incomplete_sessions(self) -> int:
        """未終了セッション（end_time=NULL）を削除"""
        try:
            cursor = self.connection.cursor()

            # 削除対象のセッションを取得
            cursor.execute("""
                SELECT id, start_time FROM input_activity_sessions
                WHERE end_time IS NULL
            """)
            incomplete_sessions = cursor.fetchall()

            if incomplete_sessions:
                session_ids = [s['id'] for s in incomplete_sessions]
                self.logger.warning(
                    f"未終了セッション {len(session_ids)} 件を削除します: {session_ids}"
                )

                # 削除実行
                cursor.execute("""
                    DELETE FROM input_activity_sessions
                    WHERE end_time IS NULL
                """)

                self.connection.commit()
                return len(session_ids)

            return 0

        except Exception as e:
            self.logger.error(f"未終了セッション削除エラー: {e}")
            return 0

# 起動時に呼び出し
database = InputActivityDatabase(db_path)
deleted_count = database.delete_incomplete_sessions()
if deleted_count > 0:
    logger.info(f"前回の未終了セッション {deleted_count} 件を削除しました")
```

### データ同期の実装方針

InputMonitorは**独立したプロセス**として動作し、独自の`DataSyncManager`インスタンスを持つ。

**理由**:
- **単一責任原則（SRP）**: 各コレクターが独立して動作
- **障害の局所化**: InputMonitorがクラッシュしてもDesktopActivityMonitorは影響を受けない
- **起動・停止の柔軟性**: ユーザーが個別に有効/無効を制御可能

**実装**:
```python
# collectors/input_monitor.py

async def main_async():
    """InputMonitorのメイン処理（非同期）"""

    # 設定読み込み
    config_manager = ConfigManager()
    config = yaml.safe_load(open('config/config.yaml'))

    # データベース初期化
    db_path = config_manager.get_sqlite_path('input')
    database = InputActivityDatabase(db_path)

    # 未終了セッション削除
    deleted_count = database.delete_incomplete_sessions()
    if deleted_count > 0:
        logger.info(f"前回の未終了セッション {deleted_count} 件を削除しました")

    # DataSyncManager初期化（input_activity_sessionsのみ同期）
    sync_manager = DataSyncManager(config, logger)
    await sync_manager.initialize()

    # バックグラウンド同期ループ開始
    asyncio.create_task(sync_manager.start_sync_loop())

    # InputMonitor開始（別スレッドで実行）
    monitor = InputMonitor(config, database)

    # シグナルハンドラ登録
    def signal_handler(sig, frame):
        logger.info(f"シグナル {sig} を受信しました")
        monitor.stop_monitoring()
        database.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # 監視開始（ブロッキング）
    monitor.start_monitoring()

def main():
    """エントリーポイント"""
    asyncio.run(main_async())

if __name__ == '__main__':
    main()
```

**DataSyncManagerへの統合**:

`common/data_sync.py`に`_sync_input_activity()`メソッドを追加し、
各コレクターが必要なテーブルのみを同期する：

```python
class DataSyncManager:
    async def sync_all(self):
        """全テーブルを同期"""
        # 各コレクターは必要なメソッドのみ呼び出す
        # linux_x11_monitor.py: _sync_desktop_activity()のみ
        # filesystem_watcher_v2.py: _sync_file_events()のみ
        # input_monitor.py: _sync_input_activity()のみ

        # ここでは全テーブル同期（将来の専用同期デーモン用）
        await self._sync_desktop_activity()
        await self._sync_file_events()
        await self._sync_input_activity()

    async def _sync_input_activity(self):
        """入力活動セッションを同期"""
        # 実装は_sync_desktop_activity()と同様
```

---

## 実装計画

### Phase 1: 基盤実装（2-3時間）

1. **データモデル実装**: `InputActivitySession`クラス追加
   - `common/models.py`更新
   - UNIXタイムスタンプとISO形式の両方をサポート
2. **データベースクラス実装**: `InputActivityDatabase`クラス追加
   - `common/database.py`更新
   - `create_session()`, `update_session_end_time()`, `delete_incomplete_sessions()`実装
   - マイグレーション処理（`synced_at`カラム追加）
3. **PostgreSQLスキーマ追加**: `04_add_input_activity_sessions.sql`作成
   - `services/database/init/`に配置
   - `input_activity_sessions`テーブル定義
4. **設定ファイル更新**: `config.yaml`に`input_monitor`セクション追加
   - `enabled: true`, `idle_timeout_seconds: 120`, `timeout_check_interval: 10`
5. **依存パッケージ追加**: `requirements.txt`更新
   - `pynput>=1.7.6`追加

### Phase 2: コレクター実装（3-4時間）

1. **InputMonitorクラス実装**: 基本構造
   - `collectors/input_monitor.py`新規作成
   - スレッド間排他制御（`threading.Lock`）
   - タイムアウトチェックスレッド管理
2. **pynput統合**: 第一選択の実装
   - DISPLAY環境変数チェック
   - マウス・キーボードリスナー実装
   - リスナーライフサイクル管理（開始・停止）
3. **フォールバック実装**: xlib対応（evdevは将来実装）
   - `_try_pynput()` → `_try_xlib()`の順で試行
4. **セッション管理**: タイムアウト監視、開始/終了処理
   - `_on_input_event()`: 入力イベント発生時の処理
   - `_check_session_timeout()`: 別スレッドで定期実行
   - `_start_session()`, `_end_session()`: Lockで保護
5. **エラーハンドリング**: 権限エラー、ライブラリエラー対応
   - 環境要件チェック（DISPLAY環境変数）
   - ImportErrorハンドリング
6. **シグナルハンドラ実装**: SIGTERM, SIGINT捕捉
   - 正常終了処理の実行
7. **未終了セッション削除**: 起動時処理
   - `database.delete_incomplete_sessions()`呼び出し

### Phase 3: データ同期統合（1-2時間）

1. **DataSyncManager拡張**: `input_activity_sessions`テーブル同期追加
   - `common/data_sync.py`更新
   - `_sync_input_activity()`メソッド実装
   - `sync_all()`メソッドに追加
2. **main_async()実装**: 独立プロセスとして動作
   - DataSyncManagerインスタンス作成
   - バックグラウンド同期ループ開始
   - InputMonitor起動
3. **バッチ同期テスト**: SQLite → PostgreSQL同期確認
   - 手動テストでデータ同期を確認

### Phase 4: デバッグ・テスト（1-2時間）

1. **デバッグスクリプト作成**: `scripts/show_input_sessions.py`
   - 最近のセッションを表示
   - 日付別フィルタリング
2. **手動テスト実施**: 入力監視、セッション記録、同期確認
   - pynput動作確認
   - タイムアウト動作確認（120秒待機）
   - セッション開始・終了記録確認
   - PostgreSQL同期確認
   - 強制終了（Ctrl+C, kill）時の挙動確認
   - 未終了セッション削除確認
3. **ドキュメント更新**: README.md, CLAUDE.md
   - InputMonitor概要追加
   - 起動・停止方法追加
   - トラブルシューティング追加

**総推定工数**: 7-11時間

### 実装順序の推奨

1. Phase 1 → Phase 2-1,2,4 → Phase 2-6,7 → Phase 3 → Phase 4
   - まず基盤とpynput統合を完成させる
   - シグナルハンドラと未終了セッション削除を実装
   - データ同期を統合
   - 最後にテストとドキュメント

2. Phase 2-3（フォールバック実装）とPhase 2-5（詳細なエラーハンドリング）は優先度低
   - pynputが動作すれば十分
   - 必要になってから実装

---

## テスト確認項目

### 機能テスト

- [ ] pynputで入力イベント検知
  - [ ] マウス移動イベント
  - [ ] マウスクリックイベント
  - [ ] キーボード入力イベント
- [ ] セッション開始が正しく記録される
  - [ ] 初回入力時にセッション作成
  - [ ] start_time, start_time_isoが記録される
- [ ] セッション終了（120秒タイムアウト）が正しく記録される
  - [ ] 120秒間入力なしでセッション終了
  - [ ] end_time, end_time_iso, duration_secondsが記録される
- [ ] セッション再開時に新しいセッションが作成される
  - [ ] タイムアウト後の入力で新セッション開始
- [ ] SQLiteにセッションが保存される
  - [ ] セッション開始時にレコード作成
  - [ ] セッション終了時にend_time更新
- [ ] PostgreSQLへ同期が成功する
  - [ ] 5分間隔でバッチ同期
  - [ ] synced_atフラグが更新される
  - [ ] 同期ログが記録される

### スレッド間排他制御テスト

- [ ] 入力イベントとタイムアウトチェックの同時アクセスが正常動作
- [ ] 長時間実行時にデッドロックが発生しない
- [ ] Lockによる性能劣化がない

### 強制終了テスト

- [ ] Ctrl+C（SIGINT）で正常終了処理が実行される
  - [ ] 現在のセッションが終了される
  - [ ] データベースが正常にクローズされる
- [ ] kill（SIGTERM）で正常終了処理が実行される
- [ ] kill -9（SIGKILL）で強制終了された場合
  - [ ] 次回起動時に未終了セッションが削除される
  - [ ] 削除ログが記録される

### 環境要件テスト

- [ ] DISPLAY環境変数なしで起動した場合
  - [ ] エラーメッセージが表示される
  - [ ] フォールバック実装を試行する
- [ ] pynput未インストール時
  - [ ] ImportErrorが捕捉される
  - [ ] フォールバック実装を試行する

### エッジケーステスト

- [ ] 長時間セッション（数時間）の記録
- [ ] 短時間セッション（数秒）の記録
  - [ ] 入力後すぐに120秒待機して終了
- [ ] データベース接続失敗時の挙動
- [ ] PostgreSQL接続失敗時の同期リトライ

### パフォーマンステスト

- [ ] 入力イベント処理のCPU使用率
  - [ ] 高頻度入力時（タイピング、マウス移動）
  - [ ] アイドル時
- [ ] メモリ使用量（長時間実行）
  - [ ] 24時間実行後のメモリリーク確認
- [ ] データベース書き込み頻度
  - [ ] セッション開始時: 1回
  - [ ] セッション終了時: 1回
  - [ ] 入力イベントごとには書き込まない

---

## セキュリティ考慮事項

### プライバシー保護

- ✅ キーストローク内容を記録しない
- ✅ マウス座標を記録しない
- ✅ 入力内容に関する情報を一切記録しない
- ✅ 「活動していた期間」のみ記録

### 権限管理

- pynput: 通常ユーザー権限で動作（X11環境）
- evdev: inputグループまたはroot権限が必要
- 権限不足時は明確なエラーメッセージを表示

### データ保護

- ローカルDB: `data/input_activity.db`（gitignore対象）
- PostgreSQL: 環境変数で認証情報管理
- 同期データ: 匿名化不要（セッション時刻のみ）

---

## 将来の拡張

### Phase 2以降

- Wayland環境対応
- Windows環境対応（`pywin32`）
- macOS環境対応（`Quartz`）
- Web UI統合（入力活動グラフ表示）
- 他のコレクターとの相関分析（デスクトップ活動 vs 入力活動）

---

## 参考資料

- [pynput ドキュメント](https://pynput.readthedocs.io/)
- [python-xlib GitHub](https://github.com/python-xlib/python-xlib)
- [python-evdev ドキュメント](https://python-evdev.readthedocs.io/)

---

## 更新履歴

### 2025-11-08: 設計更新（Phase 2）

**追加内容**:

1. **スレッド間排他制御の詳細化**
   - `threading.Lock`を使用した排他制御の実装方針
   - 入力イベントスレッドとタイムアウトチェックスレッドの同期

2. **強制終了時の対策**
   - シグナルハンドラ登録（SIGTERM, SIGINT）
   - 未終了セッション（`end_time=NULL`）の削除処理
   - 起動時のクリーンアップ処理

3. **データ同期の実装方針**
   - 独立プロセスとしての動作（責任範囲の分離）
   - 独自のDataSyncManagerインスタンス
   - `main_async()`関数の実装詳細

4. **環境要件の明確化**
   - pynput: DISPLAY環境変数が必須、SSH経由は対象外
   - python-xlib: DISPLAY環境変数が必須
   - evdev: フォールバック実装のため将来実装

5. **設定のデフォルト値決定**
   - `enabled: true`（アクティビティサマリー生成機能の精度向上に必須）
   - `timeout_check_interval: 10`（タイムアウトチェック間隔）

6. **実装計画の詳細化**
   - Phase 1-4の具体的なタスクリスト
   - 実装順序の推奨
   - 優先度の低いタスクの明確化

7. **テスト確認項目の拡充**
   - スレッド間排他制御テスト
   - 強制終了テスト
   - 環境要件テスト
   - パフォーマンステストの詳細化

**設計判断**:
- タイムアウトチェック: オプションA（別スレッド）採用
- データ同期統合: オプションB（別プロセス、責任範囲の分離）採用
- 未終了セッション: 削除（推定終了時刻での補完は行わない）
- デフォルト設定: `enabled: true`

**次のステップ**: 実装開始可能（推定7-11時間）

### 2025-11-07: 初版作成

- InputMonitorの基本設計完成
- データモデル、データベーススキーマ、コレクタークラスの設計
- Phase 1-4の実装計画策定
