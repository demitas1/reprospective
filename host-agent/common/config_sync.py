"""
PostgreSQLから監視対象ディレクトリ設定を同期するモジュール

機能:
- PostgreSQLから有効な監視ディレクトリを取得
- YAML設定からPostgreSQLへの初回移行
- フォールバック機能（DB接続失敗時はYAML使用）
"""
import asyncio
import asyncpg
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MonitoredDirectory:
    """監視対象ディレクトリの設定"""
    id: int
    directory_path: str  # 実際に監視するパス（resolved_path優先）
    enabled: bool
    display_name: Optional[str] = None
    description: Optional[str] = None
    display_path: Optional[str] = None  # 表示用パス（ユーザー入力値）
    resolved_path: Optional[str] = None  # 実体パス（シンボリックリンク解決後）


class ConfigSyncManager:
    """設定同期マネージャー"""

    def __init__(
        self,
        database_url: str,
        sync_interval: int = 60,
    ):
        """
        Args:
            database_url: PostgreSQL接続URL
            sync_interval: 同期間隔（秒）
        """
        self.database_url = database_url
        self.sync_interval = sync_interval
        self._pool: Optional[asyncpg.Pool] = None
        self._is_connected = False

    async def initialize(self) -> bool:
        """
        PostgreSQL接続プールを初期化

        Returns:
            接続成功: True, 失敗: False
        """
        try:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=3,
                command_timeout=30,
            )
            # プールの準備完了を確認
            await asyncio.sleep(0.1)
            self._is_connected = True
            logger.info("PostgreSQL接続プール初期化完了")
            return True
        except Exception as e:
            logger.warning(f"PostgreSQL接続失敗（フォールバックモードで動作）: {e}")
            self._is_connected = False
            return False

    async def close(self):
        """接続プールをクローズ"""
        if self._pool:
            await self._pool.close()
            logger.info("PostgreSQL接続プールをクローズしました")

    def is_connected(self) -> bool:
        """PostgreSQLに接続されているか"""
        return self._is_connected

    async def get_monitored_directories(self) -> List[MonitoredDirectory]:
        """
        有効な監視対象ディレクトリをPostgreSQLから取得

        Returns:
            MonitoredDirectoryのリスト（空の場合もあり）

        Raises:
            Exception: データベース接続エラー
        """
        if not self._is_connected or not self._pool:
            raise Exception("PostgreSQLに接続されていません")

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, directory_path, enabled, display_name, description,
                           display_path, resolved_path
                    FROM monitored_directories
                    WHERE enabled = true
                    ORDER BY id
                    """
                )

                directories = []
                for row in rows:
                    # resolved_pathを優先、なければdirectory_pathを使用
                    watch_path = row["resolved_path"] if row["resolved_path"] else row["directory_path"]

                    directories.append(
                        MonitoredDirectory(
                            id=row["id"],
                            directory_path=watch_path,  # 監視用パス
                            enabled=row["enabled"],
                            display_name=row["display_name"],
                            description=row["description"],
                            display_path=row["display_path"],  # 表示用パス
                            resolved_path=row["resolved_path"],  # 実体パス
                        )
                    )

                logger.debug(f"PostgreSQLから{len(directories)}件のディレクトリを取得")
                return directories

        except Exception as e:
            logger.error(f"ディレクトリ取得エラー: {e}")
            raise

    async def migrate_from_yaml(self, yaml_directories: List[str]) -> int:
        """
        YAML設定からPostgreSQLへ初回移行

        Args:
            yaml_directories: YAMLから読み込んだディレクトリパスのリスト

        Returns:
            移行した件数

        Raises:
            Exception: データベース接続エラー
        """
        if not self._is_connected or not self._pool:
            raise Exception("PostgreSQLに接続されていません")

        # 既存のディレクトリ数を確認
        try:
            async with self._pool.acquire() as conn:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM monitored_directories"
                )

                if count > 0:
                    logger.info(
                        f"PostgreSQLに既に{count}件のディレクトリが存在するため、移行をスキップ"
                    )
                    return 0

                # YAMLからPostgreSQLへ移行
                migrated = 0
                for dir_path in yaml_directories:
                    # 絶対パスに正規化
                    normalized_path = str(Path(dir_path).resolve())

                    try:
                        await conn.execute(
                            """
                            INSERT INTO monitored_directories
                                (directory_path, enabled, display_name, created_by, updated_by)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (directory_path) DO NOTHING
                            """,
                            normalized_path,
                            True,
                            None,
                            "yaml_migration",
                            "yaml_migration",
                        )
                        migrated += 1
                        logger.info(f"移行成功: {normalized_path}")
                    except Exception as e:
                        logger.warning(f"移行失敗: {normalized_path} - {e}")

                logger.info(f"YAML→PostgreSQL移行完了: {migrated}/{len(yaml_directories)}件")
                return migrated

        except Exception as e:
            logger.error(f"YAML移行エラー: {e}")
            raise

    async def check_for_updates(self) -> bool:
        """
        PostgreSQLの設定が更新されているか確認

        Returns:
            更新あり: True, 更新なし: False
        """
        if not self._is_connected or not self._pool:
            return False

        try:
            async with self._pool.acquire() as conn:
                # 最新のupdated_atを取得
                latest_update = await conn.fetchval(
                    """
                    SELECT MAX(updated_at)
                    FROM monitored_directories
                    """
                )

                if latest_update is None:
                    return False

                # 前回のチェック時刻と比較（簡易実装）
                # 実際には前回の時刻を保存して比較する必要がある
                return True

        except Exception as e:
            logger.error(f"更新チェックエラー: {e}")
            return False


class FallbackConfigManager:
    """
    フォールバック設定マネージャー（YAML使用）

    PostgreSQL接続失敗時に使用
    """

    def __init__(self, yaml_directories: List[str]):
        """
        Args:
            yaml_directories: YAMLから読み込んだディレクトリパスのリスト
        """
        self.yaml_directories = yaml_directories
        logger.info(f"フォールバックモード: YAML設定を使用（{len(yaml_directories)}件）")

    def get_monitored_directories(self) -> List[str]:
        """
        監視対象ディレクトリを取得（YAML設定）

        Returns:
            ディレクトリパスのリスト
        """
        return self.yaml_directories


async def create_config_sync_manager(
    database_url: str,
    yaml_directories: List[str],
    sync_interval: int = 60,
) -> tuple[Optional[ConfigSyncManager], Optional[FallbackConfigManager]]:
    """
    設定同期マネージャーまたはフォールバックマネージャーを作成

    Args:
        database_url: PostgreSQL接続URL
        yaml_directories: YAMLから読み込んだディレクトリパスのリスト
        sync_interval: 同期間隔（秒）

    Returns:
        (ConfigSyncManager or None, FallbackConfigManager or None)
        - PostgreSQL接続成功: (ConfigSyncManager, None)
        - PostgreSQL接続失敗: (None, FallbackConfigManager)
    """
    # PostgreSQL接続を試行
    manager = ConfigSyncManager(database_url, sync_interval)
    connected = await manager.initialize()

    if connected:
        # YAML→PostgreSQL初回移行
        try:
            await manager.migrate_from_yaml(yaml_directories)
        except Exception as e:
            logger.warning(f"YAML移行失敗: {e}")

        return manager, None
    else:
        # フォールバックモード
        fallback = FallbackConfigManager(yaml_directories)
        return None, fallback
