"""
ヘルスチェックエンドポイント
"""
from fastapi import APIRouter, Depends
import asyncpg
from datetime import datetime

from app.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check():
    """ヘルスチェック（簡易版）"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/health/db")
async def health_check_db(conn: asyncpg.Connection = Depends(get_db)):
    """ヘルスチェック（データベース接続確認）"""
    try:
        # データベース接続確認
        result = await conn.fetchval("SELECT 1")
        return {
            "status": "ok",
            "database": "connected",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
