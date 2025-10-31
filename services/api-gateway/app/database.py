"""
データベース接続管理
asyncpgを使用したPostgreSQL非同期接続
"""
import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# グローバル接続プール
_pool: asyncpg.Pool | None = None


async def init_db_pool() -> None:
    """データベース接続プールを初期化"""
    global _pool
    try:
        _pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
        logger.info("データベース接続プール初期化完了")
    except Exception as e:
        logger.error(f"データベース接続プール初期化エラー: {e}")
        raise


async def close_db_pool() -> None:
    """データベース接続プールを閉じる"""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("データベース接続プールをクローズしました")


async def get_db_connection() -> asyncpg.Connection:
    """データベース接続を取得"""
    if not _pool:
        raise RuntimeError("データベース接続プールが初期化されていません")
    return await _pool.acquire()


async def release_db_connection(conn: asyncpg.Connection) -> None:
    """データベース接続を解放"""
    if _pool:
        await _pool.release(conn)


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """FastAPI Depends用のデータベース接続ジェネレーター"""
    conn = await get_db_connection()
    try:
        yield conn
    finally:
        await release_db_connection(conn)
