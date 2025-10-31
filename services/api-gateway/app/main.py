"""
Reprospective API Gateway
監視対象ディレクトリ管理API
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.database import init_db_pool, close_db_pool
from app.routers import health, directories

# ロギング設定
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時処理
    logger.info("API Gateway起動中...")
    await init_db_pool()
    logger.info("API Gateway起動完了")

    yield

    # 終了時処理
    logger.info("API Gatewayシャットダウン中...")
    await close_db_pool()
    logger.info("API Gatewayシャットダウン完了")


# FastAPIアプリケーション
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
)

# CORS設定（開発用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(health.router)
app.include_router(directories.router)


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health",
    }
