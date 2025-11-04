"""
データ同期機能テストスクリプト

テストデータを作成して同期機能をテストする
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
import time

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from common.database import DesktopActivityDatabase, FileChangeDatabase
from common.models import ActivitySession
from common.data_sync import DataSyncManager


async def test_sync():
    """同期機能をテスト"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger(__name__)

    # データベースパス
    desktop_db_path = "./data/desktop_activity.db"
    file_db_path = "./data/file_changes.db"
    postgres_url = "postgresql://reprospective_user:change_this_password@localhost:6000/reprospective"

    logger.info("=" * 60)
    logger.info("データ同期機能テスト開始")
    logger.info("=" * 60)

    # ステップ1: テストデータを作成
    logger.info("\nステップ1: テストデータを作成")
    logger.info("-" * 60)

    desktop_db = DesktopActivityDatabase(desktop_db_path)

    # テストセッションを3つ作成
    current_time = int(time.time())
    sessions = [
        ActivitySession(
            start_time=current_time - 300,
            application_name="Firefox",
            window_title="テスト - Firefox"
        ),
        ActivitySession(
            start_time=current_time - 200,
            application_name="VSCode",
            window_title="test_sync.py - VSCode"
        ),
        ActivitySession(
            start_time=current_time - 100,
            application_name="Terminal",
            window_title="bash - Terminal"
        ),
    ]

    for i, session in enumerate(sessions, 1):
        session_id = desktop_db.save_session(session)
        logger.info(f"  テストセッション{i}を作成: ID={session_id}, app={session.application_name}")

    desktop_db.close()

    # ステップ2: 同期マネージャーを初期化
    logger.info("\nステップ2: 同期マネージャーを初期化")
    logger.info("-" * 60)

    sync_manager = DataSyncManager(
        postgres_url=postgres_url,
        sqlite_desktop_db_path=desktop_db_path,
        sqlite_file_events_db_path=file_db_path,
        batch_size=100,
        sync_interval=300
    )

    await sync_manager.initialize()
    logger.info("  同期マネージャーを初期化しました")

    # ステップ3: 同期を実行
    logger.info("\nステップ3: データ同期を実行")
    logger.info("-" * 60)

    await sync_manager.sync_all()
    logger.info("  同期が完了しました")

    # ステップ4: 結果確認
    logger.info("\nステップ4: 同期結果を確認")
    logger.info("-" * 60)
    logger.info("  PostgreSQLに同期されたデータを確認してください:")
    logger.info("  ./scripts/show-sync-stats.sh")
    logger.info("")
    logger.info("  または直接SQLで確認:")
    logger.info("  docker compose exec database psql -U reprospective_user -d reprospective")
    logger.info("  SELECT * FROM desktop_activity_sessions;")
    logger.info("  SELECT * FROM sync_logs;")

    # クリーンアップ
    await sync_manager.close()

    logger.info("")
    logger.info("=" * 60)
    logger.info("テスト完了")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_sync())
