"""
設定管理モジュール
環境変数から設定を読み込む
"""
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import field_validator


class Settings(BaseSettings):
    """アプリケーション設定"""

    # データベース設定
    database_url: str = "postgresql://reprospective_user:change_this_password@database:5432/reprospective"

    # API設定
    api_title: str = "Reprospective API Gateway"
    api_description: str = "監視対象ディレクトリ管理API"
    api_version: str = "0.1.0"
    api_port: int = 8000
    api_host: str = "0.0.0.0"

    # ログ設定
    log_level: str = "INFO"

    # CORS設定（開発用）
    cors_origins: list[str] = ["http://localhost:3333", "http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """CORS originsをカンマ区切り文字列から配列に変換"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # 環境変数名の自動変換（例: DATABASE_URL → database_url）
        case_sensitive = False


# グローバル設定インスタンス
settings = Settings()
