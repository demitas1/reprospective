"""
ファイルシステム監視モジュール

watchdogライブラリを使用してファイルシステムの変更を監視し、
データベースに記録する。
"""

import os
import re
import time
import signal
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

import sys
sys.path.append(str(Path(__file__).parent.parent))

from common.database import FileChangeDatabase


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
        """
        ファイルパスが除外パターンにマッチするか判定

        Args:
            path: ファイルパス

        Returns:
            bool: 除外すべき場合True
        """
        for pattern in self.exclude_patterns:
            if pattern.search(path):
                return True
        return False

    def _estimate_project_name(self, path: str) -> Optional[str]:
        """
        ファイルパスからプロジェクト名を推定

        監視ルート直下のディレクトリ名をプロジェクト名とみなす。

        Args:
            path: ファイルパス

        Returns:
            Optional[str]: プロジェクト名、推定できない場合はNone
        """
        try:
            rel_path = os.path.relpath(path, self.monitored_root)
            parts = rel_path.split(os.sep)

            # ルート直下のディレクトリ名をプロジェクト名とする
            if len(parts) > 1 and parts[0] != '.':
                return parts[0]

            return None
        except Exception:
            return None

    def _create_event_data(self, event: FileSystemEvent, event_type: str) -> dict:
        """
        イベントデータを作成

        Args:
            event: ファイルシステムイベント
            event_type: イベントタイプ (created/modified/deleted/moved)

        Returns:
            dict: イベントデータ
        """
        file_path = event.src_path
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1][1:] if '.' in file_name else None

        # ファイルサイズ（削除イベント以外）
        file_size = None
        if event_type != 'deleted' and os.path.exists(file_path) and not os.path.isdir(file_path):
            try:
                file_size = os.path.getsize(file_path)
            except Exception:
                pass

        # シンボリックリンク判定
        is_symlink = 1 if os.path.islink(file_path) else 0

        # 相対パス
        try:
            file_path_relative = os.path.relpath(file_path, self.monitored_root)
        except Exception:
            file_path_relative = None

        # プロジェクト名推定
        project_name = self._estimate_project_name(file_path)

        # タイムスタンプ
        event_time = int(time.time())
        event_time_iso = datetime.fromtimestamp(event_time).isoformat()

        return {
            'event_time': event_time,
            'event_time_iso': event_time_iso,
            'event_type': event_type,
            'file_path': file_path,
            'file_path_relative': file_path_relative,
            'file_name': file_name,
            'file_extension': file_extension,
            'file_size': file_size,
            'is_symlink': is_symlink,
            'monitored_root': self.monitored_root,
            'project_name': project_name
        }

    def _add_to_buffer(self, event_data: dict):
        """
        イベントをバッファに追加

        バッファが最大数に達した場合は自動フラッシュする。

        Args:
            event_data: イベントデータ
        """
        with self.buffer_lock:
            self.buffer.append(event_data)

            if len(self.buffer) >= self.buffer_max_events:
                self._flush_buffer()

    def _flush_buffer(self):
        """
        バッファをフラッシュ（ロック取得済みであること）
        """
        if self.buffer:
            self.flush_callback(self.buffer.copy())
            self.buffer.clear()

    def flush(self):
        """
        バッファを強制フラッシュ（外部から呼び出し可能）
        """
        with self.buffer_lock:
            self._flush_buffer()

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
            # 移動先のイベントを作成するため、一時的にsrc_pathを書き換え
            original_src = event.src_path
            event.src_path = event.dest_path
            created_data = self._create_event_data(event, 'created')
            event.src_path = original_src
            self._add_to_buffer(created_data)


class FileSystemWatcher:
    """
    ファイルシステム監視クラス

    指定されたディレクトリ配下のファイル変更を監視し、
    データベースに記録する。
    """

    def __init__(self, config: dict, database: FileChangeDatabase):
        """
        ファイルシステム監視を初期化

        Args:
            config: 設定辞書（filesystem_watcher セクション）
            database: FileChangeDatabaseインスタンス
        """
        self.config = config
        self.database = database
        self.logger = logging.getLogger(__name__)

        self.monitored_directories = config.get('monitored_directories', [])
        self.exclude_patterns = config.get('exclude_patterns', [])
        self.follow_symlinks = config.get('symlinks', {}).get('follow', False)

        buffer_config = config.get('buffer', {})
        self.buffer_max_events = buffer_config.get('max_events', 100)
        self.flush_interval = buffer_config.get('flush_interval', 10)

        self.observers = []
        self.event_handlers = []
        self.flush_timer = None
        self.is_running = False

    def _save_events_batch(self, events: List[dict]):
        """
        イベントをバッチ保存

        Args:
            events: イベントデータのリスト
        """
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
        for handler in self.event_handlers:
            handler.flush()

        # 次回のフラッシュをスケジュール
        self.flush_timer = threading.Timer(self.flush_interval, self._schedule_flush)
        self.flush_timer.daemon = True
        self.flush_timer.start()

    def start(self):
        """監視を開始"""
        if self.is_running:
            self.logger.warning("FileSystemWatcher は既に実行中です")
            return

        if not self.monitored_directories:
            self.logger.warning("監視対象ディレクトリが設定されていません")
            return

        self.logger.info("ファイルシステム監視を開始します")

        # 各ディレクトリに対してObserverを作成
        for directory in self.monitored_directories:
            if not os.path.exists(directory):
                self.logger.warning(f"監視対象ディレクトリが存在しません: {directory}")
                continue

            # イベントハンドラを作成
            handler = FileChangeEventHandler(
                monitored_root=directory,
                exclude_patterns=self.exclude_patterns,
                buffer_max_events=self.buffer_max_events,
                flush_callback=self._save_events_batch
            )
            self.event_handlers.append(handler)

            # Observerを作成して監視開始
            observer = Observer()
            observer.schedule(
                handler,
                directory,
                recursive=True
            )
            observer.start()
            self.observers.append(observer)

            self.logger.info(f"監視開始: {directory} (follow_symlinks={self.follow_symlinks})")

        # 定期フラッシュを開始
        self.is_running = True
        self._schedule_flush()

        self.logger.info(f"ファイルシステム監視を開始しました（{len(self.observers)}ディレクトリ）")

    def stop(self):
        """監視を停止"""
        if not self.is_running:
            return

        self.logger.info("ファイルシステム監視を停止します")
        self.is_running = False

        # タイマーを停止
        if self.flush_timer:
            self.flush_timer.cancel()

        # 最終フラッシュ
        for handler in self.event_handlers:
            handler.flush()

        # 全Observerを停止
        for observer in self.observers:
            observer.stop()

        # 全Observerの終了を待機
        for observer in self.observers:
            observer.join(timeout=5)

        self.observers.clear()
        self.event_handlers.clear()

        self.logger.info("ファイルシステム監視を停止しました")


def main():
    """
    スタンドアロン実行用メイン関数
    """
    import yaml

    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )
    logger = logging.getLogger(__name__)

    # 設定ファイル読み込み
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    if not config_path.exists():
        logger.error(f"設定ファイルが見つかりません: {config_path}")
        return 1

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # FileSystemWatcher設定チェック
    fs_config = config.get('filesystem_watcher', {})
    if not fs_config.get('enabled', False):
        logger.error("filesystem_watcher が無効になっています")
        return 1

    # データベース接続
    db_config = config.get('database', {})
    db_path = db_config.get('file_changes', {}).get('path', 'data/file_changes.db')

    # 相対パスの場合はhost-agent/からの相対パスとする
    if not os.path.isabs(db_path):
        db_path = str(Path(__file__).parent.parent / db_path)

    database = FileChangeDatabase(db_path)

    # FileSystemWatcherを作成
    watcher = FileSystemWatcher(fs_config, database)

    # シグナルハンドラ設定
    def signal_handler(sig, frame):
        logger.info("終了シグナルを受信しました")
        watcher.stop()
        database.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 監視開始
    watcher.start()

    logger.info("FileSystemWatcher が実行中です。Ctrl+C で終了します。")

    # メインスレッドは待機
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("キーボード割り込みを検出しました")
        watcher.stop()
        database.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
