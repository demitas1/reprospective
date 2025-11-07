"""
統合設定管理モジュール

環境変数、YAML設定、デフォルト値を統合的に管理する。
python-dotenvで親ディレクトリの.envを自動検索する。
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)


class ConfigManager:
    """設定管理クラス"""

    def __init__(self, config_yaml_path: Optional[str] = None):
        """
        設定を初期化

        Args:
            config_yaml_path: config.yamlのパス（省略時は自動検出）
        """
        # 1. 親ディレクトリから.envを自動検索してロード
        # find_dotenv()は現在のディレクトリから親を遡って.envを検索
        dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path:
            load_dotenv(dotenv_path)
            logger.info(f".envファイルをロード: {dotenv_path}")
        else:
            logger.warning(".envファイルが見つかりません（環境変数のみ使用）")

        # 2. YAML設定をロード（オプション）
        self.yaml_config = self._load_yaml(config_yaml_path)

    def get_postgres_url(self) -> str:
        """PostgreSQL接続URLを取得（環境変数 > YAML > デフォルト）"""
        # 優先順位1: DATABASE_URL環境変数
        if os.getenv('DATABASE_URL'):
            return os.getenv('DATABASE_URL')

        # 優先順位2: 個別環境変数から構築
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '6000')
        db_name = os.getenv('DB_NAME', 'reprospective')
        user = os.getenv('DB_USER', 'reprospective_user')
        password = os.getenv('DB_PASSWORD', 'change_this_password')

        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

    def get_sqlite_desktop_path(self) -> str:
        """デスクトップアクティビティSQLiteパスを取得"""
        path = os.getenv('SQLITE_DESKTOP_PATH', 'data/desktop_activity.db')
        return self._resolve_path(path)

    def get_sqlite_file_events_path(self) -> str:
        """ファイルイベントSQLiteパスを取得"""
        path = os.getenv('SQLITE_FILE_EVENTS_PATH', 'data/file_changes.db')
        return self._resolve_path(path)

    def get_data_sync_config(self) -> Dict[str, Any]:
        """データ同期設定を取得（YAML > デフォルト）"""
        if 'data_sync' in self.yaml_config:
            config = self.yaml_config['data_sync']
            # YAMLのキー名をコード内のキー名に変換
            return {
                'enabled': config.get('enabled', True),
                'sync_interval_seconds': config.get('interval_seconds', 300),
                'batch_size': config.get('batch_size', 100),
                'max_retries': config.get('max_retries', 5)
            }
        return {
            'enabled': True,
            'sync_interval_seconds': 300,
            'batch_size': 100,
            'max_retries': 5
        }

    def get_desktop_monitor_config(self) -> Dict[str, Any]:
        """デスクトップモニター設定を取得（YAML > デフォルト）"""
        if 'desktop_monitor' in self.yaml_config:
            config = self.yaml_config['desktop_monitor']
            # YAMLのキー名をコード内のキー名に変換
            return {
                'check_interval': config.get('monitor_interval', 1.0),
                'idle_threshold': config.get('idle_threshold', 60),
                'enabled': config.get('enabled', True)
            }
        return {
            'check_interval': 1.0,
            'idle_threshold': 60,
            'enabled': True
        }

    def get_filesystem_watcher_config(self) -> Dict[str, Any]:
        """ファイルシステムウォッチャー設定を取得（YAML > デフォルト）"""
        if 'filesystem_watcher' in self.yaml_config:
            return self.yaml_config['filesystem_watcher']
        return {
            'monitored_directories': [],
            'excluded_patterns': ['*.tmp', '*.swp', '.git/*']
        }

    def _resolve_path(self, path: str) -> str:
        """相対パスをhost-agent/からの絶対パスに解決"""
        if Path(path).is_absolute():
            return path
        host_agent_dir = Path(__file__).parent.parent
        return str(host_agent_dir / path)

    def _load_yaml(self, config_path: Optional[str]) -> Dict[str, Any]:
        """YAML設定をロード"""
        if not config_path:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        if Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
