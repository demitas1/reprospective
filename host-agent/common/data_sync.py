"""
データ同期モジュール

SQLiteローカルデータベースからPostgreSQLへのバッチ同期を管理する。
"""

import asyncio
import asyncpg
import sqlite3
import logging
import socket
import getpass
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


class DataSyncManager:
    """
    SQLite → PostgreSQL データ同期マネージャー

    定期的にローカルSQLiteデータベースから未同期データを取得し、
    PostgreSQLに一括挿入する。

    機能:
    - バッチ同期（configurable interval）
    - 増分同期（synced_at IS NULL のみ）
    - エラーリカバリ（自動リトライ）
    - 同期統計記録
    """

    def __init__(
        self,
        postgres_url: str,
        sqlite_desktop_db_path: str,
        sqlite_file_events_db_path: str,
        sqlite_input_db_path: Optional[str] = None,
        batch_size: int = 100,
        sync_interval: int = 300,
        max_retries: int = 5
    ):
        """
        データ同期マネージャーを初期化

        Args:
            postgres_url: PostgreSQL接続URL
            sqlite_desktop_db_path: デスクトップアクティビティSQLiteパス
            sqlite_file_events_db_path: ファイルイベントSQLiteパス
            sqlite_input_db_path: 入力アクティビティSQLiteパス（オプション）
            batch_size: 1回の同期バッチサイズ
            sync_interval: 同期間隔（秒）
            max_retries: 最大リトライ回数
        """
        self.postgres_url = postgres_url
        self.sqlite_desktop_db_path = sqlite_desktop_db_path
        self.sqlite_file_events_db_path = sqlite_file_events_db_path
        self.sqlite_input_db_path = sqlite_input_db_path
        self.batch_size = batch_size
        self.sync_interval = sync_interval
        self.max_retries = max_retries

        self.logger = logging.getLogger(__name__)
        self.pool: Optional[asyncpg.Pool] = None
        self._sync_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

        # ホスト識別子を初期化時に取得
        self.host_identifier = self._get_host_identifier()

    async def initialize(self):
        """PostgreSQL接続プールを初期化"""
        try:
            self.pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=1,
                max_size=5,
                command_timeout=60
            )
            self.logger.info("PostgreSQL接続プールを初期化しました")
        except Exception as e:
            self.logger.error(f"PostgreSQL接続プール初期化エラー: {e}")
            raise

    async def close(self):
        """接続プールをクローズ"""
        if self._sync_task and not self._sync_task.done():
            self._stop_event.set()
            await self._sync_task

        if self.pool:
            await self.pool.close()
            self.logger.info("PostgreSQL接続プールをクローズしました")

    def _get_host_identifier(self) -> str:
        """ホスト識別子を取得 (hostname_username)"""
        hostname = socket.gethostname()
        username = getpass.getuser()
        return f"{hostname}_{username}"

    async def sync_all(self):
        """全テーブルを同期（desktop_activity_sessions + file_change_events + input_activity_sessions）"""
        self.logger.info("データ同期を開始します...")

        # デスクトップアクティビティを同期
        await self._sync_desktop_activity()

        # ファイル変更イベントを同期
        await self._sync_file_events()

        # 入力活動セッションを同期
        await self._sync_input_activity()

        self.logger.info("データ同期が完了しました")

    async def _sync_desktop_activity(self):
        """デスクトップアクティビティセッションを同期"""
        table_name = "desktop_activity_sessions"
        sync_started_at = datetime.now()
        records_synced = 0
        records_failed = 0
        error_message = None

        try:
            # SQLiteから未同期レコードを取得
            unsynced_records = self._get_unsynced_desktop_records()

            if not unsynced_records:
                self.logger.debug(f"{table_name}: 未同期レコードがありません")
                return

            self.logger.info(f"{table_name}: {len(unsynced_records)}件の未同期レコードを検出")

            # バッチ単位でPostgreSQLに挿入
            for i in range(0, len(unsynced_records), self.batch_size):
                batch = unsynced_records[i:i + self.batch_size]
                synced_ids = []

                try:
                    async with self.pool.acquire() as conn:
                        async with conn.transaction():
                            for record in batch:
                                # ISO文字列をPostgreSQLのTIMESTAMPに変換
                                start_time_iso = None
                                end_time_iso = None

                                if record['start_time_iso']:
                                    start_time_iso = datetime.fromisoformat(record['start_time_iso'].replace('Z', '+00:00'))
                                if record['end_time_iso']:
                                    end_time_iso = datetime.fromisoformat(record['end_time_iso'].replace('Z', '+00:00'))

                                await conn.execute("""
                                    INSERT INTO desktop_activity_sessions
                                    (start_time, end_time, start_time_iso, end_time_iso,
                                     application_name, window_title, duration_seconds, synced_at)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
                                """, record['start_time'], record['end_time'],
                                    start_time_iso, end_time_iso,
                                    record['application_name'], record['window_title'],
                                    record['duration_seconds'])

                                synced_ids.append(record['id'])

                    # SQLiteのsynced_atフラグを更新
                    self._update_desktop_synced_flags(synced_ids)
                    records_synced += len(synced_ids)

                    self.logger.debug(f"{table_name}: {len(synced_ids)}件を同期しました")

                except Exception as e:
                    self.logger.error(f"{table_name}: バッチ同期エラー: {e}")
                    records_failed += len(batch)
                    error_message = str(e)

            # 同期結果をログに記録
            status = "success" if records_failed == 0 else "partial_success" if records_synced > 0 else "failed"
            await self._log_sync_result(
                sync_started_at, table_name, records_synced, records_failed, status, error_message
            )

        except Exception as e:
            self.logger.error(f"{table_name}: 同期処理エラー: {e}")
            await self._log_sync_result(
                sync_started_at, table_name, 0, 0, "failed", str(e)
            )

    async def _sync_file_events(self):
        """ファイル変更イベントを同期"""
        table_name = "file_change_events"
        sync_started_at = datetime.now()
        records_synced = 0
        records_failed = 0
        error_message = None

        try:
            # SQLiteから未同期レコードを取得
            unsynced_records = self._get_unsynced_file_records()

            if not unsynced_records:
                self.logger.debug(f"{table_name}: 未同期レコードがありません")
                return

            self.logger.info(f"{table_name}: {len(unsynced_records)}件の未同期レコードを検出")

            # バッチ単位でPostgreSQLに挿入
            for i in range(0, len(unsynced_records), self.batch_size):
                batch = unsynced_records[i:i + self.batch_size]
                synced_ids = []

                try:
                    async with self.pool.acquire() as conn:
                        async with conn.transaction():
                            for record in batch:
                                # ISO文字列をPostgreSQLのTIMESTAMPに変換
                                event_time_iso = None
                                if record['event_time_iso']:
                                    event_time_iso = datetime.fromisoformat(record['event_time_iso'].replace('Z', '+00:00'))

                                # is_symlinkをboolean型に変換（SQLiteでは整数で保存されている）
                                is_symlink = bool(record['is_symlink']) if record.get('is_symlink') is not None else False

                                await conn.execute("""
                                    INSERT INTO file_change_events
                                    (event_time, event_time_iso, event_type, file_path,
                                     file_path_relative, file_name, file_extension, file_size,
                                     is_symlink, monitored_root, project_name, synced_at)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, CURRENT_TIMESTAMP)
                                """, record['event_time'], event_time_iso,
                                    record['event_type'], record['file_path'],
                                    record['file_path_relative'], record['file_name'],
                                    record['file_extension'], record['file_size'],
                                    is_symlink, record['monitored_root'],
                                    record['project_name'])

                                synced_ids.append(record['id'])

                    # SQLiteのsynced_atフラグを更新
                    self._update_file_synced_flags(synced_ids)
                    records_synced += len(synced_ids)

                    self.logger.debug(f"{table_name}: {len(synced_ids)}件を同期しました")

                except Exception as e:
                    self.logger.error(f"{table_name}: バッチ同期エラー: {e}")
                    records_failed += len(batch)
                    error_message = str(e)

            # 同期結果をログに記録
            status = "success" if records_failed == 0 else "partial_success" if records_synced > 0 else "failed"
            await self._log_sync_result(
                sync_started_at, table_name, records_synced, records_failed, status, error_message
            )

        except Exception as e:
            self.logger.error(f"{table_name}: 同期処理エラー: {e}")
            await self._log_sync_result(
                sync_started_at, table_name, 0, 0, "failed", str(e)
            )

    def _get_unsynced_desktop_records(self) -> List[Dict[str, Any]]:
        """SQLiteから未同期のデスクトップレコードを取得"""
        if not Path(self.sqlite_desktop_db_path).exists():
            self.logger.debug(f"デスクトップDBが存在しません: {self.sqlite_desktop_db_path}")
            return []

        try:
            conn = sqlite3.connect(self.sqlite_desktop_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM desktop_activity_sessions
                WHERE synced_at IS NULL
                ORDER BY start_time ASC
            """)

            records = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return records

        except Exception as e:
            self.logger.error(f"デスクトップレコード取得エラー: {e}")
            return []

    def _get_unsynced_file_records(self) -> List[Dict[str, Any]]:
        """SQLiteから未同期のファイルレコードを取得"""
        if not Path(self.sqlite_file_events_db_path).exists():
            self.logger.debug(f"ファイルDBが存在しません: {self.sqlite_file_events_db_path}")
            return []

        try:
            conn = sqlite3.connect(self.sqlite_file_events_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM file_change_events
                WHERE synced_at IS NULL
                ORDER BY event_time ASC
            """)

            records = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return records

        except Exception as e:
            self.logger.error(f"ファイルレコード取得エラー: {e}")
            return []

    def _update_desktop_synced_flags(self, record_ids: List[int]):
        """デスクトップレコードのsynced_atフラグを更新"""
        if not record_ids:
            return

        try:
            conn = sqlite3.connect(self.sqlite_desktop_db_path)
            cursor = conn.cursor()
            current_time = int(datetime.now().timestamp())

            placeholders = ','.join('?' * len(record_ids))
            cursor.execute(f"""
                UPDATE desktop_activity_sessions
                SET synced_at = ?
                WHERE id IN ({placeholders})
            """, [current_time] + record_ids)

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"synced_atフラグ更新エラー: {e}")

    def _update_file_synced_flags(self, record_ids: List[int]):
        """ファイルレコードのsynced_atフラグを更新"""
        if not record_ids:
            return

        try:
            conn = sqlite3.connect(self.sqlite_file_events_db_path)
            cursor = conn.cursor()
            current_time = int(datetime.now().timestamp())

            placeholders = ','.join('?' * len(record_ids))
            cursor.execute(f"""
                UPDATE file_change_events
                SET synced_at = ?
                WHERE id IN ({placeholders})
            """, [current_time] + record_ids)

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"synced_atフラグ更新エラー: {e}")

    async def _sync_input_activity(self):
        """入力活動セッションを同期"""
        # 入力アクティビティDBが設定されていない場合はスキップ
        if not self.sqlite_input_db_path:
            self.logger.debug("入力アクティビティDB未設定のため同期をスキップ")
            return

        table_name = "input_activity_sessions"
        sync_started_at = datetime.now()
        records_synced = 0
        records_failed = 0
        error_message = None

        try:
            # SQLiteから未同期レコードを取得
            unsynced_records = self._get_unsynced_input_records()

            if not unsynced_records:
                self.logger.debug(f"{table_name}: 未同期レコードがありません")
                return

            self.logger.info(f"{table_name}: {len(unsynced_records)}件の未同期レコードを検出")

            # バッチ単位でPostgreSQLに挿入
            for i in range(0, len(unsynced_records), self.batch_size):
                batch = unsynced_records[i:i + self.batch_size]
                synced_ids = []

                try:
                    async with self.pool.acquire() as conn:
                        async with conn.transaction():
                            for record in batch:
                                # ISO文字列をPostgreSQLのTIMESTAMPに変換
                                start_time_iso = None
                                if record['start_time_iso']:
                                    start_time_iso = datetime.fromisoformat(record['start_time_iso'].replace('Z', '+00:00'))

                                end_time_iso = None
                                if record['end_time_iso']:
                                    end_time_iso = datetime.fromisoformat(record['end_time_iso'].replace('Z', '+00:00'))

                                await conn.execute("""
                                    INSERT INTO input_activity_sessions
                                    (start_time, end_time, start_time_iso, end_time_iso,
                                     duration_seconds, created_at, updated_at,
                                     host_identifier, synced_from_local_id)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                                """, record['start_time'], record['end_time'],
                                    start_time_iso, end_time_iso,
                                    record['duration_seconds'], record['created_at'],
                                    record['updated_at'], self.host_identifier, record['id'])

                                synced_ids.append(record['id'])

                    # SQLiteのsynced_atフラグを更新
                    self._update_input_synced_flags(synced_ids)
                    records_synced += len(synced_ids)

                    self.logger.debug(f"{table_name}: {len(synced_ids)}件を同期しました")

                except Exception as e:
                    self.logger.error(f"{table_name}: バッチ同期エラー: {e}")
                    records_failed += len(batch)
                    error_message = str(e)

            # 同期結果をログに記録
            status = "success" if records_failed == 0 else "partial_success" if records_synced > 0 else "failed"
            await self._log_sync_result(
                sync_started_at, table_name, records_synced, records_failed, status, error_message
            )

        except Exception as e:
            self.logger.error(f"{table_name}: 同期処理エラー: {e}")
            await self._log_sync_result(
                sync_started_at, table_name, 0, 0, "failed", str(e)
            )

    def _get_unsynced_input_records(self) -> List[Dict[str, Any]]:
        """SQLiteから未同期の入力活動レコードを取得"""
        if not self.sqlite_input_db_path:
            return []

        if not Path(self.sqlite_input_db_path).exists():
            self.logger.debug(f"入力活動DBが存在しません: {self.sqlite_input_db_path}")
            return []

        try:
            conn = sqlite3.connect(self.sqlite_input_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM input_activity_sessions
                WHERE synced_at IS NULL
                ORDER BY start_time ASC
            """)

            records = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return records

        except Exception as e:
            self.logger.error(f"入力活動レコード取得エラー: {e}")
            return []

    def _update_input_synced_flags(self, record_ids: List[int]):
        """入力活動レコードのsynced_atフラグを更新"""
        if not record_ids:
            return

        if not self.sqlite_input_db_path:
            return

        try:
            conn = sqlite3.connect(self.sqlite_input_db_path)
            cursor = conn.cursor()
            current_time = int(datetime.now().timestamp())

            placeholders = ','.join('?' * len(record_ids))
            cursor.execute(f"""
                UPDATE input_activity_sessions
                SET synced_at = ?
                WHERE id IN ({placeholders})
            """, [current_time] + record_ids)

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"synced_atフラグ更新エラー: {e}")

    async def _log_sync_result(
        self,
        sync_started_at: datetime,
        table_name: str,
        records_synced: int,
        records_failed: int,
        status: str,
        error_message: Optional[str] = None
    ):
        """同期結果をPostgreSQLのsync_logsに記録"""
        try:
            host_identifier = self._get_host_identifier()
            sync_completed_at = datetime.now()

            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO sync_logs
                    (sync_started_at, sync_completed_at, table_name, records_synced,
                     records_failed, status, error_message, host_identifier)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, sync_started_at, sync_completed_at, table_name, records_synced,
                    records_failed, status, error_message, host_identifier)

            self.logger.info(
                f"同期ログを記録: table={table_name}, synced={records_synced}, "
                f"failed={records_failed}, status={status}"
            )

        except Exception as e:
            self.logger.error(f"同期ログ記録エラー: {e}")

    async def start_sync_loop(self):
        """定期同期ループを開始（asyncioタスク）"""
        self.logger.info(f"定期同期ループを開始します（間隔: {self.sync_interval}秒）")

        while not self._stop_event.is_set():
            try:
                await self.sync_all()
            except Exception as e:
                self.logger.error(f"同期ループエラー: {e}")

            # 次回同期まで待機（または停止イベント）
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.sync_interval
                )
            except asyncio.TimeoutError:
                # タイムアウトは正常（次回同期タイミング）
                pass

        self.logger.info("定期同期ループを停止しました")

    def run_sync_loop_in_background(self, loop: asyncio.AbstractEventLoop):
        """
        バックグラウンドで同期ループを実行

        Args:
            loop: 実行するイベントループ
        """
        self._sync_task = loop.create_task(self.start_sync_loop())
