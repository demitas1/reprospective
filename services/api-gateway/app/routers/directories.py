"""
監視対象ディレクトリ管理APIエンドポイント
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import asyncpg
import logging

from app.database import get_db
from app.models import (
    MonitoredDirectory,
    MonitoredDirectoryCreate,
    MonitoredDirectoryUpdate,
)

router = APIRouter(prefix="/api/v1/directories", tags=["directories"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[MonitoredDirectory])
async def list_directories(
    enabled_only: bool = False, conn: asyncpg.Connection = Depends(get_db)
):
    """
    監視対象ディレクトリの一覧取得

    Args:
        enabled_only: Trueの場合、有効なディレクトリのみ取得
    """
    try:
        if enabled_only:
            query = """
                SELECT id, directory_path, enabled, display_name, description,
                       created_at, updated_at, created_by, updated_by
                FROM monitored_directories
                WHERE enabled = true
                ORDER BY updated_at DESC
            """
        else:
            query = """
                SELECT id, directory_path, enabled, display_name, description,
                       created_at, updated_at, created_by, updated_by
                FROM monitored_directories
                ORDER BY updated_at DESC
            """

        rows = await conn.fetch(query)
        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"ディレクトリ一覧取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ディレクトリ一覧の取得に失敗しました",
        )


@router.get("/{directory_id}", response_model=MonitoredDirectory)
async def get_directory(
    directory_id: int, conn: asyncpg.Connection = Depends(get_db)
):
    """
    特定のディレクトリ取得

    Args:
        directory_id: ディレクトリID
    """
    try:
        query = """
            SELECT id, directory_path, enabled, display_name, description,
                   created_at, updated_at, created_by, updated_by
            FROM monitored_directories
            WHERE id = $1
        """
        row = await conn.fetchrow(query, directory_id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {directory_id} のディレクトリが見つかりません",
            )

        return dict(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ディレクトリ取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ディレクトリの取得に失敗しました",
        )


@router.post("/", response_model=MonitoredDirectory, status_code=status.HTTP_201_CREATED)
async def create_directory(
    directory: MonitoredDirectoryCreate, conn: asyncpg.Connection = Depends(get_db)
):
    """
    監視対象ディレクトリを追加

    Args:
        directory: ディレクトリ情報
    """
    try:
        query = """
            INSERT INTO monitored_directories
                (directory_path, enabled, display_name, description, created_by, updated_by)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, directory_path, enabled, display_name, description,
                      created_at, updated_at, created_by, updated_by
        """
        row = await conn.fetchrow(
            query,
            directory.directory_path,
            directory.enabled,
            directory.display_name,
            directory.description,
            directory.created_by,
            directory.created_by,
        )

        logger.info(f"ディレクトリ追加成功: {directory.directory_path}")
        return dict(row)

    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"ディレクトリ '{directory.directory_path}' は既に登録されています",
        )
    except Exception as e:
        logger.error(f"ディレクトリ追加エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ディレクトリの追加に失敗しました",
        )


@router.put("/{directory_id}", response_model=MonitoredDirectory)
async def update_directory(
    directory_id: int,
    directory: MonitoredDirectoryUpdate,
    conn: asyncpg.Connection = Depends(get_db),
):
    """
    ディレクトリ情報を更新

    Args:
        directory_id: ディレクトリID
        directory: 更新情報
    """
    try:
        # 存在確認
        check_query = "SELECT id FROM monitored_directories WHERE id = $1"
        exists = await conn.fetchval(check_query, directory_id)

        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {directory_id} のディレクトリが見つかりません",
            )

        # 更新するフィールドを動的に構築
        update_fields = []
        params = [directory_id]
        param_count = 2

        if directory.directory_path is not None:
            update_fields.append(f"directory_path = ${param_count}")
            params.append(directory.directory_path)
            param_count += 1

        if directory.enabled is not None:
            update_fields.append(f"enabled = ${param_count}")
            params.append(directory.enabled)
            param_count += 1

        if directory.display_name is not None:
            update_fields.append(f"display_name = ${param_count}")
            params.append(directory.display_name)
            param_count += 1

        if directory.description is not None:
            update_fields.append(f"description = ${param_count}")
            params.append(directory.description)
            param_count += 1

        update_fields.append(f"updated_by = ${param_count}")
        params.append(directory.updated_by)

        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新する項目が指定されていません",
            )

        query = f"""
            UPDATE monitored_directories
            SET {", ".join(update_fields)}
            WHERE id = $1
            RETURNING id, directory_path, enabled, display_name, description,
                      created_at, updated_at, created_by, updated_by
        """

        row = await conn.fetchrow(query, *params)

        logger.info(f"ディレクトリ更新成功: ID {directory_id}")
        return dict(row)

    except HTTPException:
        raise
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"ディレクトリ '{directory.directory_path}' は既に登録されています",
        )
    except Exception as e:
        logger.error(f"ディレクトリ更新エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ディレクトリの更新に失敗しました",
        )


@router.delete("/{directory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_directory(
    directory_id: int, conn: asyncpg.Connection = Depends(get_db)
):
    """
    ディレクトリを削除

    Args:
        directory_id: ディレクトリID
    """
    try:
        query = "DELETE FROM monitored_directories WHERE id = $1 RETURNING id"
        row = await conn.fetchrow(query, directory_id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {directory_id} のディレクトリが見つかりません",
            )

        logger.info(f"ディレクトリ削除成功: ID {directory_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ディレクトリ削除エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ディレクトリの削除に失敗しました",
        )


@router.patch("/{directory_id}/toggle", response_model=MonitoredDirectory)
async def toggle_directory(
    directory_id: int, conn: asyncpg.Connection = Depends(get_db)
):
    """
    ディレクトリの有効/無効を切り替え

    Args:
        directory_id: ディレクトリID
    """
    try:
        query = """
            UPDATE monitored_directories
            SET enabled = NOT enabled, updated_by = 'api'
            WHERE id = $1
            RETURNING id, directory_path, enabled, display_name, description,
                      created_at, updated_at, created_by, updated_by
        """
        row = await conn.fetchrow(query, directory_id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {directory_id} のディレクトリが見つかりません",
            )

        logger.info(f"ディレクトリ切り替え成功: ID {directory_id}, enabled={row['enabled']}")
        return dict(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ディレクトリ切り替えエラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ディレクトリの切り替えに失敗しました",
        )
