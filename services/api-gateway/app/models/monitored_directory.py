"""
監視対象ディレクトリのデータモデル
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import os


class MonitoredDirectoryBase(BaseModel):
    """監視対象ディレクトリの基本モデル"""

    directory_path: str = Field(..., description="監視対象の絶対パス")
    enabled: bool = Field(default=True, description="有効/無効")
    display_name: Optional[str] = Field(None, max_length=100, description="表示名")
    description: Optional[str] = Field(None, max_length=500, description="説明")
    display_path: Optional[str] = Field(None, description="表示用パス（ユーザー入力値）")
    resolved_path: Optional[str] = Field(None, description="実体パス（シンボリックリンク解決後）")

    @field_validator("directory_path")
    @classmethod
    def validate_directory_path(cls, v: str) -> str:
        """ディレクトリパスのバリデーション"""
        if not v:
            raise ValueError("ディレクトリパスは必須です")

        # 絶対パスチェック
        if not os.path.isabs(v):
            raise ValueError("絶対パスで指定してください")

        # パス正規化
        normalized = os.path.normpath(v)

        return normalized


class MonitoredDirectoryCreate(MonitoredDirectoryBase):
    """監視対象ディレクトリ作成用モデル"""

    created_by: str = Field(default="api", description="作成者")


class MonitoredDirectoryUpdate(BaseModel):
    """監視対象ディレクトリ更新用モデル（部分更新対応）"""

    directory_path: Optional[str] = Field(None, description="監視対象の絶対パス")
    enabled: Optional[bool] = Field(None, description="有効/無効")
    display_name: Optional[str] = Field(None, max_length=100, description="表示名")
    description: Optional[str] = Field(None, max_length=500, description="説明")
    display_path: Optional[str] = Field(None, description="表示用パス（ユーザー入力値）")
    resolved_path: Optional[str] = Field(None, description="実体パス（シンボリックリンク解決後）")
    updated_by: str = Field(default="api", description="更新者")

    @field_validator("directory_path")
    @classmethod
    def validate_directory_path(cls, v: Optional[str]) -> Optional[str]:
        """ディレクトリパスのバリデーション"""
        if v is None:
            return None

        if not v:
            raise ValueError("ディレクトリパスは空にできません")

        # 絶対パスチェック
        if not os.path.isabs(v):
            raise ValueError("絶対パスで指定してください")

        # パス正規化
        normalized = os.path.normpath(v)

        return normalized


class MonitoredDirectory(MonitoredDirectoryBase):
    """監視対象ディレクトリの完全モデル（DB取得時）"""

    id: int = Field(..., description="ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    created_by: str = Field(..., description="作成者")
    updated_by: str = Field(..., description="更新者")

    class Config:
        from_attributes = True
