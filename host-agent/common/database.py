"""
データベース操作モジュール

各データコレクター専用のSQLiteデータベースクラスを提供する。
各クラスは独立したDBファイルを使用し、スレッド競合を回避する。
"""

import sqlite3
import logging
import time
from pathlib import Path
from typing import Optional, List
from .models import ActivitySession


class DesktopActivityDatabase:
    """
    デスクトップアクティビティ専用データベースクラス

    desktop_activity_sessionsテーブルのみを管理する。
    """

    def __init__(self, db_path: str):
        """
        データベースを初期化

        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.connection: Optional[sqlite3.Connection] = None

        # データベースファイルのディレクトリを作成
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        self._connect()
        self._create_tables()

    def _connect(self):
        """データベースに接続"""
        try:
            # check_same_thread=False: 複数スレッドから呼び出されるため
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # 辞書形式で結果を取得
            self.logger.info(f"データベースに接続しました: {self.db_path}")
        except Exception as e:
            self.logger.error(f"データベース接続エラー: {e}")
            raise

    def _create_tables(self):
        """テーブルを作成"""
        try:
            cursor = self.connection.cursor()

            # デスクトップアクティビティセッションテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS desktop_activity_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER,
                    start_time_iso TEXT NOT NULL,
                    end_time_iso TEXT,
                    application_name TEXT NOT NULL,
                    window_title TEXT NOT NULL,
                    duration_seconds INTEGER,
                    synced_at INTEGER,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
            """)

            # インデックスを作成（検索高速化）
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_start_time
                ON desktop_activity_sessions(start_time)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_application_name
                ON desktop_activity_sessions(application_name)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_synced_at
                ON desktop_activity_sessions(synced_at)
            """)

            self.connection.commit()
            self.logger.info("データベーステーブルを作成しました")

            # マイグレーション実行
            self._migrate_add_synced_at_column()

        except Exception as e:
            self.logger.error(f"テーブル作成エラー: {e}")
            raise

    def _migrate_add_synced_at_column(self):
        """
        既存テーブルにsynced_atカラムを追加するマイグレーション

        既にカラムが存在する場合はスキップする
        """
        try:
            cursor = self.connection.cursor()

            # カラムの存在を確認
            cursor.execute("PRAGMA table_info(desktop_activity_sessions)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'synced_at' not in columns:
                self.logger.info("synced_atカラムを追加しています...")
                cursor.execute("""
                    ALTER TABLE desktop_activity_sessions
                    ADD COLUMN synced_at INTEGER
                """)

                # インデックスを作成
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_synced_at
                    ON desktop_activity_sessions(synced_at)
                """)

                self.connection.commit()
                self.logger.info("synced_atカラムを追加しました")
            else:
                self.logger.debug("synced_atカラムは既に存在します")

        except Exception as e:
            self.logger.error(f"マイグレーションエラー: {e}")
            # マイグレーションエラーは致命的ではないため、継続

    def save_session(self, session: ActivitySession) -> int:
        """
        新しいセッションをデータベースに保存

        Args:
            session: 保存するActivitySessionオブジェクト

        Returns:
            int: 保存されたセッションのID
        """
        try:
            cursor = self.connection.cursor()
            current_time = int(time.time())

            cursor.execute("""
                INSERT INTO desktop_activity_sessions
                (start_time, end_time, start_time_iso, end_time_iso,
                 application_name, window_title, duration_seconds,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.start_time,
                session.end_time,
                session.start_time_iso,
                session.end_time_iso,
                session.application_name,
                session.window_title,
                session.duration_seconds,
                current_time,
                current_time
            ))

            self.connection.commit()
            session_id = cursor.lastrowid

            self.logger.debug(
                f"セッションを保存しました: ID={session_id}, "
                f"app={session.application_name}, title={session.window_title[:30]}"
            )

            return session_id

        except Exception as e:
            self.logger.error(f"セッション保存エラー: {e}")
            raise

    def update_session_end_time(self, session_id: int, end_time: int):
        """
        セッションの終了時刻を更新

        Args:
            session_id: 更新対象のセッションID
            end_time: 終了時刻（UNIXエポック秒）
        """
        try:
            cursor = self.connection.cursor()
            current_time = int(time.time())

            # セッションを取得して継続時間を計算
            cursor.execute("""
                SELECT start_time FROM desktop_activity_sessions
                WHERE id = ?
            """, (session_id,))

            row = cursor.fetchone()
            if not row:
                self.logger.warning(f"セッションID {session_id} が見つかりません")
                return

            start_time = row['start_time']
            duration_seconds = end_time - start_time

            # ISO形式の終了時刻
            from datetime import datetime
            end_time_iso = datetime.fromtimestamp(end_time).isoformat()

            cursor.execute("""
                UPDATE desktop_activity_sessions
                SET end_time = ?,
                    end_time_iso = ?,
                    duration_seconds = ?,
                    updated_at = ?
                WHERE id = ?
            """, (end_time, end_time_iso, duration_seconds, current_time, session_id))

            self.connection.commit()

            self.logger.debug(
                f"セッション終了時刻を更新しました: ID={session_id}, "
                f"duration={duration_seconds}秒"
            )

        except Exception as e:
            self.logger.error(f"セッション更新エラー: {e}")
            raise

    def get_session_by_id(self, session_id: int) -> Optional[ActivitySession]:
        """
        IDでセッションを取得

        Args:
            session_id: セッションID

        Returns:
            Optional[ActivitySession]: 見つかった場合はActivitySession、なければNone
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM desktop_activity_sessions
                WHERE id = ?
            """, (session_id,))

            row = cursor.fetchone()
            if row:
                return ActivitySession.from_dict(dict(row))
            return None

        except Exception as e:
            self.logger.error(f"セッション取得エラー: {e}")
            return None

    def get_recent_sessions(self, limit: int = 100) -> List[ActivitySession]:
        """
        最近のセッションを取得

        Args:
            limit: 取得する最大件数

        Returns:
            List[ActivitySession]: セッションのリスト
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM desktop_activity_sessions
                ORDER BY start_time DESC
                LIMIT ?
            """, (limit,))

            sessions = []
            for row in cursor.fetchall():
                sessions.append(ActivitySession.from_dict(dict(row)))

            return sessions

        except Exception as e:
            self.logger.error(f"セッション取得エラー: {e}")
            return []

    def get_sessions_by_date(self, date_str: str) -> List[ActivitySession]:
        """
        指定日付のセッションを取得

        Args:
            date_str: 日付文字列（YYYY-MM-DD形式）

        Returns:
            List[ActivitySession]: その日のセッションのリスト
        """
        try:
            from datetime import datetime

            # 日付の開始と終了のUNIXタイムスタンプを計算
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            start_of_day = int(date_obj.timestamp())
            end_of_day = start_of_day + 86400  # 24時間後

            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM desktop_activity_sessions
                WHERE start_time >= ? AND start_time < ?
                ORDER BY start_time ASC
            """, (start_of_day, end_of_day))

            sessions = []
            for row in cursor.fetchall():
                sessions.append(ActivitySession.from_dict(dict(row)))

            return sessions

        except Exception as e:
            self.logger.error(f"セッション取得エラー: {e}")
            return []

    def close(self):
        """データベース接続をクローズ"""
        if self.connection:
            self.connection.close()
            self.logger.info("データベース接続をクローズしました")


class FileChangeDatabase:
    """
    ファイル変更イベント専用データベースクラス

    file_change_eventsテーブルのみを管理する。
    """

    def __init__(self, db_path: str):
        """
        データベースを初期化

        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.connection: Optional[sqlite3.Connection] = None

        # データベースファイルのディレクトリを作成
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        self._connect()
        self._create_tables()

    def _connect(self):
        """データベースに接続"""
        try:
            # check_same_thread=False: watchdogのスレッドから呼び出されるため
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # 辞書形式で結果を取得
            self.logger.info(f"データベースに接続しました: {self.db_path}")
        except Exception as e:
            self.logger.error(f"データベース接続エラー: {e}")
            raise

    def _create_tables(self):
        """テーブルを作成"""
        try:
            cursor = self.connection.cursor()

            # ファイル変更イベントテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_change_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_time INTEGER NOT NULL,
                    event_time_iso TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_path_relative TEXT,
                    file_name TEXT NOT NULL,
                    file_extension TEXT,
                    file_size INTEGER,
                    is_symlink INTEGER DEFAULT 0,
                    monitored_root TEXT NOT NULL,
                    project_name TEXT,
                    synced_at INTEGER,
                    created_at INTEGER NOT NULL
                )
            """)

            # ファイル変更イベント用インデックス
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_event_time
                ON file_change_events(event_time)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_project_name
                ON file_change_events(project_name)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_extension
                ON file_change_events(file_extension)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_synced_at
                ON file_change_events(synced_at)
            """)

            self.connection.commit()
            self.logger.info("データベーステーブルを作成しました")

            # マイグレーション実行
            self._migrate_add_synced_at_column()

        except Exception as e:
            self.logger.error(f"テーブル作成エラー: {e}")
            raise

    def _migrate_add_synced_at_column(self):
        """
        既存テーブルにsynced_atカラムを追加するマイグレーション

        既にカラムが存在する場合はスキップする
        """
        try:
            cursor = self.connection.cursor()

            # カラムの存在を確認
            cursor.execute("PRAGMA table_info(file_change_events)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'synced_at' not in columns:
                self.logger.info("synced_atカラムを追加しています...")
                cursor.execute("""
                    ALTER TABLE file_change_events
                    ADD COLUMN synced_at INTEGER
                """)

                # インデックスを作成
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_file_synced_at
                    ON file_change_events(synced_at)
                """)

                self.connection.commit()
                self.logger.info("synced_atカラムを追加しました")
            else:
                self.logger.debug("synced_atカラムは既に存在します")

        except Exception as e:
            self.logger.error(f"マイグレーションエラー: {e}")
            # マイグレーションエラーは致命的ではないため、継続

    def save_file_event(self, event_data: dict) -> int:
        """
        ファイル変更イベントをデータベースに保存

        Args:
            event_data: イベントデータ（辞書形式）
                必須キー: event_time, event_time_iso, event_type, file_path,
                         file_name, monitored_root
                オプション: file_path_relative, file_extension, file_size,
                           is_symlink, project_name

        Returns:
            int: 保存されたイベントのID
        """
        try:
            cursor = self.connection.cursor()
            current_time = int(time.time())

            cursor.execute("""
                INSERT INTO file_change_events
                (event_time, event_time_iso, event_type, file_path,
                 file_path_relative, file_name, file_extension, file_size,
                 is_symlink, monitored_root, project_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data['event_time'],
                event_data['event_time_iso'],
                event_data['event_type'],
                event_data['file_path'],
                event_data.get('file_path_relative'),
                event_data['file_name'],
                event_data.get('file_extension'),
                event_data.get('file_size'),
                event_data.get('is_symlink', 0),
                event_data['monitored_root'],
                event_data.get('project_name'),
                current_time
            ))

            self.connection.commit()
            event_id = cursor.lastrowid

            self.logger.debug(
                f"ファイルイベントを保存しました: ID={event_id}, "
                f"type={event_data['event_type']}, file={event_data['file_name']}"
            )

            return event_id

        except Exception as e:
            self.logger.error(f"ファイルイベント保存エラー: {e}")
            raise

    def save_file_events_batch(self, events: List[dict]):
        """
        複数のファイル変更イベントを一括保存

        Args:
            events: イベントデータのリスト
        """
        try:
            cursor = self.connection.cursor()
            current_time = int(time.time())

            event_tuples = [
                (
                    event['event_time'],
                    event['event_time_iso'],
                    event['event_type'],
                    event['file_path'],
                    event.get('file_path_relative'),
                    event['file_name'],
                    event.get('file_extension'),
                    event.get('file_size'),
                    event.get('is_symlink', 0),
                    event['monitored_root'],
                    event.get('project_name'),
                    current_time
                )
                for event in events
            ]

            cursor.executemany("""
                INSERT INTO file_change_events
                (event_time, event_time_iso, event_type, file_path,
                 file_path_relative, file_name, file_extension, file_size,
                 is_symlink, monitored_root, project_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, event_tuples)

            self.connection.commit()

            self.logger.debug(f"{len(events)}件のファイルイベントを一括保存しました")

        except Exception as e:
            self.logger.error(f"ファイルイベント一括保存エラー: {e}")
            raise

    def get_recent_file_events(self, limit: int = 100) -> List[dict]:
        """
        最近のファイルイベントを取得

        Args:
            limit: 取得する最大件数

        Returns:
            List[dict]: イベントのリスト
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM file_change_events
                ORDER BY event_time DESC
                LIMIT ?
            """, (limit,))

            events = []
            for row in cursor.fetchall():
                events.append(dict(row))

            return events

        except Exception as e:
            self.logger.error(f"ファイルイベント取得エラー: {e}")
            return []

    def close(self):
        """データベース接続をクローズ"""
        if self.connection:
            self.connection.close()
            self.logger.info("データベース接続をクローズしました")


# 後方互換性のためのエイリアス（非推奨）
# 既存コードとの互換性を保つため、Databaseクラスを残す
Database = DesktopActivityDatabase
