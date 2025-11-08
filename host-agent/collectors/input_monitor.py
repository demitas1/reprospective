"""
入力デバイス監視モジュール

マウス、キーボードの入力を監視し、入力活動がある期間を記録する。
プライバシー保護: 入力イベントの発生のみ検知し、具体的な入力内容は記録しない。
"""

import os
import signal
import sys
import time
import logging
import threading
import asyncio
import yaml
from pathlib import Path
from typing import Optional

# 親ディレクトリをパスに追加（common モジュールをインポートするため）
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.models import InputActivitySession
from common.database import InputActivityDatabase
from common.data_sync import DataSyncManager
from common.config import ConfigManager


class InputMonitor:
    """
    入力デバイス監視クラス

    マウス・キーボードの入力を監視し、セッション単位でデータベースに記録する。
    入力種別（マウス/キーボード）は記録せず、セッション期間のみを記録する。
    """

    def __init__(self, config: dict, database: InputActivityDatabase):
        """
        モニターを初期化

        Args:
            config: 設定辞書
            database: InputActivityDatabaseインスタンス
        """
        self.config = config
        self.database = database
        self.logger = logging.getLogger(__name__)

        # 設定
        self.idle_timeout = config.get('idle_timeout_seconds', 120)
        self.timeout_check_interval = config.get('timeout_check_interval', 10)

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

        self.logger.info(
            f"InputMonitor初期化完了（idle_timeout: {self.idle_timeout}秒, "
            f"check_interval: {self.timeout_check_interval}秒）"
        )

    def start_monitoring(self) -> None:
        """
        監視開始（pynput → xlib → evdev の順で試行）

        現在はpynputのみ実装。フォールバックは将来実装。
        """
        self.is_running = True
        self.logger.info("入力デバイスの監視を開始します")

        # タイムアウトチェックスレッドを開始
        self.timeout_thread = threading.Thread(
            target=self._check_session_timeout,
            daemon=True  # メインスレッド終了時に自動終了
        )
        self.timeout_thread.start()
        self.logger.info("タイムアウトチェックスレッドを開始しました")

        # pynputで監視を試行
        if self._try_pynput():
            # pynput成功時は無限ループで監視継続
            try:
                while self.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("\nキーボード割り込みを受信しました")
        else:
            self.logger.error("入力監視の開始に失敗しました")
            self.is_running = False

    def stop_monitoring(self) -> None:
        """
        監視停止（リスナー停止、スレッド終了、セッション終了）
        """
        self.is_running = False
        self.logger.info("入力デバイスの監視を停止します")

        # pynputリスナーを停止
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.logger.debug("マウスリスナーを停止しました")
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.logger.debug("キーボードリスナーを停止しました")

        # タイムアウトスレッドが終了するのを待つ
        if self.timeout_thread and self.timeout_thread.is_alive():
            self.timeout_thread.join(timeout=5.0)
            self.logger.debug("タイムアウトチェックスレッドを終了しました")

        # 現在のセッションを終了
        with self.session_lock:
            if self.current_session_id:
                self._end_session()

        self.logger.info("監視を停止しました")

    def _try_pynput(self) -> bool:
        """
        pynputで監視を試行

        環境要件:
        - DISPLAY環境変数が設定されていること（X11セッション）
        - pynputがインストールされていること

        Returns:
            bool: 成功した場合True
        """
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

    def _on_input_event(self, *args, **kwargs):
        """
        入力イベント発生時のコールバック（マウス・キーボード共通）

        pynputリスナーから呼び出されるため、引数は可変長。
        引数の内容は使用せず、イベント発生のみ記録する。

        スレッドセーフ: session_lockで保護
        """
        with self.session_lock:
            current_time = time.time()

            if self.current_session is None:
                self._start_session()

            self.last_input_time = current_time

    def _check_session_timeout(self) -> None:
        """
        セッションタイムアウトチェック（別スレッドで定期実行）

        idle_timeout秒間入力がない場合、セッションを終了する。
        timeout_check_interval秒ごとにチェックを実行。

        スレッドセーフ: session_lockで保護
        """
        while self.is_running:
            time.sleep(self.timeout_check_interval)

            with self.session_lock:
                if self.current_session and \
                   (time.time() - self.last_input_time) > self.idle_timeout:
                    self._end_session()

    def _start_session(self) -> None:
        """
        セッション開始

        注意: session_lockで保護された状態で呼び出すこと
        """
        current_time = int(time.time())
        self.current_session = InputActivitySession(
            start_time=current_time
        )
        self.last_input_time = time.time()

        # データベースに保存
        self.current_session_id = self.database.create_session(self.current_session)
        self.current_session.id = self.current_session_id

        self.logger.info(
            f"セッション開始: ID={self.current_session_id}, "
            f"start={self.current_session.start_time_iso}"
        )

    def _end_session(self) -> None:
        """
        セッション終了

        注意: session_lockで保護された状態で呼び出すこと
        """
        if not self.current_session_id:
            return

        end_time = int(time.time())

        # データベースに終了時刻を更新
        self.database.update_session_end_time(self.current_session_id, end_time)

        # セッション情報を取得して表示
        session = self.database.get_session_by_id(self.current_session_id)
        if session:
            self.logger.info(
                f"セッション終了: ID={self.current_session_id}, "
                f"duration={session.duration_seconds}秒"
            )

        # 現在のセッションをクリア
        self.current_session = None
        self.current_session_id = None


async def main_async():
    """InputMonitorのメイン処理（非同期）"""

    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    )
    logger = logging.getLogger(__name__)

    # 設定読み込み
    config_manager = ConfigManager()
    input_config = config_manager.get_input_monitor_config()

    # 入力モニターが有効か確認
    if not input_config.get('enabled', True):
        logger.info("InputMonitorは無効化されています（config.yaml: input_monitor.enabled=false）")
        return

    # データベース初期化
    db_path = config_manager.get_sqlite_input_path()
    database = InputActivityDatabase(db_path)

    # 未終了セッション削除
    deleted_count = database.delete_incomplete_sessions()
    if deleted_count > 0:
        logger.info(f"前回の未終了セッション {deleted_count} 件を削除しました")

    # DataSyncManager初期化（input_activity_sessionsのみ同期）
    postgres_url = config_manager.get_postgres_url()
    sync_config = config_manager.get_data_sync_config()

    sync_manager = DataSyncManager(
        postgres_url=postgres_url,
        sqlite_desktop_db_path=config_manager.get_sqlite_desktop_path(),
        sqlite_file_events_db_path=config_manager.get_sqlite_file_events_path(),
        sqlite_input_db_path=db_path,
        batch_size=sync_config.get('batch_size', 100),
        sync_interval=sync_config.get('sync_interval_seconds', 300),
        max_retries=sync_config.get('max_retries', 5)
    )
    await sync_manager.initialize()

    # バックグラウンド同期ループ開始
    asyncio.create_task(sync_manager.start_sync_loop())

    # InputMonitor開始（別スレッドで実行）
    monitor = InputMonitor(input_config, database)

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

    # 正常終了時のクリーンアップ
    database.close()


def main():
    """エントリーポイント"""
    asyncio.run(main_async())


if __name__ == '__main__':
    main()
