"""
ファイルシステム監視モジュール (v2 - PostgreSQL設定同期対応)

watchdogライブラリを使用してファイルシステムの変更を監視し、
データベースに記録する。PostgreSQLから監視対象ディレクトリを動的に取得。
"""

import os
import re
import time
import signal
import logging
import threading
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

import sys
sys.path.append(str(Path(__file__).parent.parent))

from common.database import FileChangeDatabase
from common.config import ConfigManager
from common.config_sync import (
    ConfigSyncManager,
    FallbackConfigManager,
    create_config_sync_manager,
    MonitoredDirectory,
)


class FileChangeEventHandler(FileSystemEventHandler):
    """
    ファイルシステムイベントハンドラ

    watchdogのイベントを受け取り、バッファに蓄積してバッチ処理する。
    """

    def __init__(
        self,
        monitored_root: str,
        exclude_patterns: List[str],
        buffer_max_events: int,
        flush_callback
    ):
        """
        イベントハンドラを初期化

        Args:
            monitored_root: 監視ルートディレクトリ
            exclude_patterns: 除外パターンのリスト（正規表現）
            buffer_max_events: バッファ最大イベント数
            flush_callback: フラッシュ時に呼び出すコールバック関数
        """
        super().__init__()
        self.monitored_root = monitored_root
        self.exclude_patterns = [re.compile(pattern) for pattern in exclude_patterns]
        self.buffer_max_events = buffer_max_events
        self.flush_callback = flush_callback
        self.buffer = []
        self.buffer_lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def _should_exclude(self, path: str) -> bool:
        """ファイルパスが除外パターンにマッチするか判定"""
        for pattern in self.exclude_patterns:
            if pattern.search(path):
                return True
        return False

    def _estimate_project_name(self, path: str) -> Optional[str]:
        """ファイルパスからプロジェクト名を推定"""
        try:
            rel_path = os.path.relpath(path, self.monitored_root)
            parts = rel_path.split(os.sep)

            if len(parts) > 1 and parts[0] != '.':
                return parts[0]

            return None
        except Exception:
            return None

    def _create_event_data(self, event: FileSystemEvent, event_type: str) -> dict:
        """イベントデータを作成"""
        file_path = event.src_path
        file_name = os.path.basename(file_path)
        _, file_extension = os.path.splitext(file_name)
        project_name = self._estimate_project_name(file_path)

        # タイムスタンプ（UNIXタイムスタンプ整数とISO文字列）
        event_time = int(time.time())
        event_time_iso = datetime.fromtimestamp(event_time).isoformat()

        return {
            'event_time': event_time,
            'event_time_iso': event_time_iso,
            'event_type': event_type,
            'file_path': file_path,
            'file_name': file_name,
            'file_extension': file_extension,
            'project_name': project_name,
            'monitored_root': self.monitored_root,
        }

    def _add_to_buffer(self, event_data: dict):
        """イベントをバッファに追加"""
        with self.buffer_lock:
            self.buffer.append(event_data)

            # バッファが閾値を超えたら即座にフラッシュ
            if len(self.buffer) >= self.buffer_max_events:
                self.flush()

    def flush(self):
        """バッファをフラッシュ"""
        with self.buffer_lock:
            if not self.buffer:
                return

            events_to_save = self.buffer.copy()
            self.buffer.clear()

        # コールバックを呼び出し
        if self.flush_callback:
            self.flush_callback(events_to_save)

    def on_created(self, event):
        """ファイル作成イベント"""
        if event.is_directory or self._should_exclude(event.src_path):
            return

        event_data = self._create_event_data(event, 'created')
        self._add_to_buffer(event_data)

    def on_modified(self, event):
        """ファイル変更イベント"""
        if event.is_directory or self._should_exclude(event.src_path):
            return

        event_data = self._create_event_data(event, 'modified')
        self._add_to_buffer(event_data)

    def on_deleted(self, event):
        """ファイル削除イベント"""
        if event.is_directory or self._should_exclude(event.src_path):
            return

        event_data = self._create_event_data(event, 'deleted')
        self._add_to_buffer(event_data)

    def on_moved(self, event):
        """ファイル移動イベント"""
        if event.is_directory or self._should_exclude(event.src_path):
            return

        # 移動元を削除、移動先を作成として記録
        deleted_data = self._create_event_data(event, 'deleted')
        self._add_to_buffer(deleted_data)

        # 移動先のイベント
        if hasattr(event, 'dest_path'):
            original_src = event.src_path
            event.src_path = event.dest_path
            created_data = self._create_event_data(event, 'created')
            event.src_path = original_src
            self._add_to_buffer(created_data)


class FileSystemWatcherV2:
    """
    ファイルシステム監視クラス (v2)

    PostgreSQLから監視対象ディレクトリを動的に取得し、
    設定変更に応じて監視対象を更新する。
    """

    def __init__(
        self,
        config: dict,
        database: FileChangeDatabase,
        config_sync_manager: Optional[ConfigSyncManager] = None,
        fallback_manager: Optional[FallbackConfigManager] = None,
    ):
        """
        ファイルシステム監視を初期化

        Args:
            config: 設定辞書（filesystem_watcher セクション）
            database: FileChangeDatabaseインスタンス
            config_sync_manager: 設定同期マネージャー（PostgreSQL接続時）
            fallback_manager: フォールバックマネージャー（PostgreSQL接続失敗時）
        """
        self.config = config
        self.database = database
        self.config_sync_manager = config_sync_manager
        self.fallback_manager = fallback_manager
        self.logger = logging.getLogger(__name__)

        # 設定
        self.exclude_patterns = config.get('exclude_patterns', [])
        self.follow_symlinks = config.get('symlinks', {}).get('follow', False)

        buffer_config = config.get('buffer', {})
        self.buffer_max_events = buffer_config.get('max_events', 100)
        self.flush_interval = buffer_config.get('flush_interval', 10)
        self.sync_interval = config.get('sync_interval', 60)

        # 監視状態
        self.observers: Dict[str, Observer] = {}  # {directory_path: Observer}
        self.event_handlers: Dict[str, FileChangeEventHandler] = {}  # {directory_path: Handler}
        self.monitored_dirs: Set[str] = set()  # 現在監視中のディレクトリパス
        self.flush_timer = None
        self.sync_task = None
        self.is_running = False
        self.loop = None

    def _save_events_batch(self, events: List[dict]):
        """イベントをバッチ保存"""
        try:
            self.database.save_file_events_batch(events)
            self.logger.info(f"{len(events)}件のファイルイベントを保存しました")
        except Exception as e:
            self.logger.error(f"イベント保存エラー: {e}")

    def _schedule_flush(self):
        """定期フラッシュをスケジュール"""
        if not self.is_running:
            return

        # 全ハンドラをフラッシュ
        for handler in self.event_handlers.values():
            handler.flush()

        # 次回のフラッシュをスケジュール
        self.flush_timer = threading.Timer(self.flush_interval, self._schedule_flush)
        self.flush_timer.daemon = True
        self.flush_timer.start()

    def _start_observer(self, directory: str):
        """指定ディレクトリの監視を開始"""
        if directory in self.observers:
            self.logger.debug(f"既に監視中: {directory}")
            return

        if not os.path.exists(directory):
            self.logger.warning(f"監視対象ディレクトリが存在しません: {directory}")
            return

        # イベントハンドラを作成
        handler = FileChangeEventHandler(
            monitored_root=directory,
            exclude_patterns=self.exclude_patterns,
            buffer_max_events=self.buffer_max_events,
            flush_callback=self._save_events_batch
        )
        self.event_handlers[directory] = handler

        # Observerを作成して監視開始
        observer = Observer()
        observer.schedule(handler, directory, recursive=True)
        observer.start()
        self.observers[directory] = observer
        self.monitored_dirs.add(directory)

        self.logger.info(f"監視開始: {directory}")

    def _stop_observer(self, directory: str):
        """指定ディレクトリの監視を停止"""
        if directory not in self.observers:
            return

        # ハンドラをフラッシュ
        if directory in self.event_handlers:
            self.event_handlers[directory].flush()
            del self.event_handlers[directory]

        # Observerを停止
        observer = self.observers[directory]
        observer.stop()
        observer.join(timeout=5)
        del self.observers[directory]
        self.monitored_dirs.discard(directory)

        self.logger.info(f"監視停止: {directory}")

    async def _sync_directories(self):
        """PostgreSQLから設定を同期して監視対象を更新"""
        if not self.config_sync_manager:
            return

        try:
            # PostgreSQLから有効なディレクトリを取得
            pg_directories = await self.config_sync_manager.get_monitored_directories()
            pg_paths = {d.directory_path for d in pg_directories}

            # ディレクトリ情報をマップに保存（ログ出力用）
            dir_info_map = {d.directory_path: d for d in pg_directories}

            # 現在の監視対象と比較
            current_paths = self.monitored_dirs.copy()

            # 新規追加されたディレクトリを監視開始
            for path in pg_paths - current_paths:
                dir_info = dir_info_map.get(path)
                if dir_info and dir_info.display_path and dir_info.display_path != path:
                    self.logger.info(f"新しいディレクトリを検出: {dir_info.display_path} -> {path}")
                else:
                    self.logger.info(f"新しいディレクトリを検出: {path}")
                self._start_observer(path)

            # 削除されたディレクトリの監視を停止
            for path in current_paths - pg_paths:
                self.logger.info(f"ディレクトリが削除されました: {path}")
                self._stop_observer(path)

        except Exception as e:
            self.logger.error(f"設定同期エラー: {e}")

    async def _sync_loop(self):
        """定期的に設定を同期するループ"""
        while self.is_running:
            await asyncio.sleep(self.sync_interval)
            if self.is_running:
                await self._sync_directories()

    async def start_async(self):
        """監視を開始（非同期版）"""
        if self.is_running:
            self.logger.warning("FileSystemWatcherV2 は既に実行中です")
            return

        self.logger.info("ファイルシステム監視を開始します")
        self.is_running = True

        # 初期の監視対象ディレクトリを取得
        if self.config_sync_manager:
            # PostgreSQLから取得
            try:
                directories = await self.config_sync_manager.get_monitored_directories()
                initial_dirs = [d.directory_path for d in directories]
                self.logger.info(f"PostgreSQLから{len(initial_dirs)}件のディレクトリを取得")
            except Exception as e:
                self.logger.error(f"PostgreSQLからのディレクトリ取得失敗: {e}")
                initial_dirs = []

            # 定期同期タスクを開始
            if initial_dirs:
                self.sync_task = asyncio.create_task(self._sync_loop())

        elif self.fallback_manager:
            # YAMLから取得（フォールバック）
            initial_dirs = self.fallback_manager.get_monitored_directories()
            self.logger.info(f"YAML設定から{len(initial_dirs)}件のディレクトリを使用")
        else:
            self.logger.error("設定マネージャーが初期化されていません")
            return

        if not initial_dirs:
            self.logger.warning("監視対象ディレクトリが設定されていません")
            return

        # 各ディレクトリの監視を開始
        for directory in initial_dirs:
            self._start_observer(directory)

        # 定期フラッシュを開始
        self._schedule_flush()

        self.logger.info(f"ファイルシステム監視を開始しました（{len(self.observers)}ディレクトリ）")

    def stop(self):
        """監視を停止"""
        if not self.is_running:
            return

        self.logger.info("ファイルシステム監視を停止します")
        self.is_running = False

        # 同期タスクをキャンセル
        if self.sync_task:
            self.sync_task.cancel()

        # タイマーを停止
        if self.flush_timer:
            self.flush_timer.cancel()

        # 全ディレクトリの監視を停止
        for directory in list(self.observers.keys()):
            self._stop_observer(directory)

        self.logger.info("ファイルシステム監視を停止しました")


async def main_async():
    """
    スタンドアロン実行用メイン関数（非同期版）
    """
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )
    logger = logging.getLogger(__name__)

    # 設定マネージャー初期化
    config_manager = ConfigManager()

    # FileSystemWatcher設定取得
    fs_config = config_manager.get_filesystem_watcher_config()

    # データベース接続
    db_path = config_manager.get_sqlite_file_events_path()
    database = FileChangeDatabase(db_path)

    # PostgreSQL設定同期マネージャーを作成
    postgres_url = config_manager.get_postgres_url()
    yaml_directories = fs_config.get('monitored_directories', [])

    config_sync_mgr, fallback_mgr = await create_config_sync_manager(
        database_url=postgres_url,
        yaml_directories=yaml_directories,
        sync_interval=fs_config.get('sync_interval', 60)
    )

    # FileSystemWatcherV2を作成
    watcher = FileSystemWatcherV2(
        fs_config,
        database,
        config_sync_manager=config_sync_mgr,
        fallback_manager=fallback_mgr,
    )

    # シグナルハンドラ設定
    def signal_handler(sig, frame):
        logger.info("終了シグナルを受信しました")
        watcher.stop()
        database.close()
        if config_sync_mgr:
            # 非同期でクローズ
            asyncio.create_task(config_sync_mgr.close())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 監視開始（非同期）
    await watcher.start_async()

    logger.info("FileSystemWatcherV2 が実行中です。Ctrl+C で終了します。")

    # メインループは非同期待機
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("キーボード割り込みを検出しました")
        watcher.stop()
        database.close()
        if config_sync_mgr:
            await config_sync_mgr.close()
    except asyncio.CancelledError:
        logger.info("タスクがキャンセルされました")
        watcher.stop()
        database.close()
        if config_sync_mgr:
            await config_sync_mgr.close()

    return 0


def main():
    """スタンドアロン実行用メイン関数"""
    return asyncio.run(main_async())


if __name__ == '__main__':
    sys.exit(main())
