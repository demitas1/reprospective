"""
デバッグエンドポイント

開発環境でのフロントエンドエラーロギング機能を提供
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Any
import logging
import json
from pathlib import Path

from app.config import settings

router = APIRouter(prefix="/api/v1/debug", tags=["debug"])
logger = logging.getLogger(__name__)

# ログファイルパス
LOG_FILE_PATH = Path("/var/log/frontend/errors.log")


class ErrorEntry(BaseModel):
    """フロントエンドエラーエントリ"""
    timestamp: str = Field(..., description="エラー発生日時（ISO 8601）")
    message: str = Field(..., description="エラーメッセージ")
    stack: Optional[str] = Field(None, description="スタックトレース")
    context: Optional[str] = Field(None, description="エラーコンテキスト")
    user_agent: Optional[str] = Field(None, description="ユーザーエージェント")
    url: Optional[str] = Field(None, description="エラー発生URL")
    component_stack: Optional[str] = Field(None, description="Reactコンポーネントスタック")
    additional_info: Optional[dict[str, Any]] = Field(None, description="追加情報")


class LogErrorsRequest(BaseModel):
    """エラーログ送信リクエスト"""
    errors: list[ErrorEntry] = Field(..., description="エラーエントリのリスト")


class LogErrorsResponse(BaseModel):
    """エラーログ送信レスポンス"""
    status: str = Field(..., description="ステータス")
    logged_count: int = Field(..., description="記録したエラー件数")
    log_file: str = Field(..., description="ログファイルパス")


@router.post("/log-errors", response_model=LogErrorsResponse, status_code=status.HTTP_201_CREATED)
async def log_frontend_errors(request: LogErrorsRequest):
    """
    フロントエンドエラーをログファイルに記録

    開発環境でのみ有効化（settings.debug_mode=True）

    Args:
        request: エラーログ送信リクエスト

    Returns:
        LogErrorsResponse: ログ記録結果

    Raises:
        HTTPException: デバッグモード無効時は403、書き込み失敗時は500
    """
    # デバッグモードでない場合は無効
    if not settings.debug_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="デバッグエンドポイントは開発環境でのみ有効です"
        )

    try:
        # ログディレクトリの作成
        LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # ログファイルに追記
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            for error in request.errors:
                log_line = json.dumps(
                    error.model_dump(),
                    ensure_ascii=False,
                    default=str
                ) + "\n"
                f.write(log_line)

        logger.info(f"フロントエンドエラーを記録: {len(request.errors)}件")

        return LogErrorsResponse(
            status="ok",
            logged_count=len(request.errors),
            log_file=str(LOG_FILE_PATH)
        )

    except Exception as e:
        logger.error(f"エラーログ記録失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ログ記録に失敗しました: {str(e)}"
        )
