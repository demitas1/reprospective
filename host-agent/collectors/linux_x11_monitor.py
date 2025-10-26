"""
Linux X11デスクトップアクティビティモニター

X11環境でのアクティブウィンドウ情報を取得し、活動セッションとして記録する。
"""

import subprocess
import time
import logging
from typing import Optional, Tuple
from pathlib import Path
import sys

# 親ディレクトリをパスに追加（common モジュールをインポートするため）
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.models import ActivitySession
from common.database import DesktopActivityDatabase


class LinuxX11Monitor:
    """
    Linux X11環境でデスクトップアクティビティを監視するクラス

    xdotoolとxpropを使用してアクティブウィンドウの情報を取得し、
    セッション単位でデータベースに記録する。
    """

    def __init__(self, config: dict, database: DesktopActivityDatabase):
        """
        モニターを初期化

        Args:
            config: 設定辞書
            database: Databaseインスタンス
        """
        self.config = config
        self.database = database
        self.logger = logging.getLogger(__name__)

        # 監視間隔（秒）
        self.monitor_interval = config.get('desktop_monitor', {}).get('monitor_interval', 10)

        # 現在のセッション
        self.current_session: Optional[ActivitySession] = None
        self.current_session_id: Optional[int] = None

        # 監視実行フラグ
        self.is_running = False

        self.logger.info(f"LinuxX11Monitor初期化完了（監視間隔: {self.monitor_interval}秒）")

    def get_active_window_info(self) -> Optional[Tuple[str, str]]:
        """
        アクティブウィンドウの情報を取得

        Returns:
            Optional[Tuple[str, str]]: (window_title, application_name) または None
        """
        try:
            # アクティブウィンドウIDを取得
            active_window_id = subprocess.check_output(
                ["xdotool", "getactivewindow"],
                universal_newlines=True,
                stderr=subprocess.DEVNULL
            ).strip()

            # ウィンドウプロパティを取得
            xprop_output = subprocess.check_output(
                ["xprop", "-id", active_window_id, "WM_NAME", "WM_CLASS"],
                universal_newlines=True,
                stderr=subprocess.DEVNULL
            ).strip()

            # WM_NAMEとWM_CLASSを解析
            window_title = ""
            application_name = ""

            for line in xprop_output.split("\n"):
                if "WM_NAME" in line:
                    # WM_NAME(STRING) = "タイトル" 形式から抽出
                    window_title = line.split("=", 1)[-1].strip().strip('"')
                elif "WM_CLASS" in line:
                    # WM_CLASS(STRING) = "instance", "class" 形式から class を抽出
                    parts = line.split("=", 1)[-1].strip().split(",")
                    if len(parts) >= 2:
                        application_name = parts[-1].strip().strip('"')
                    elif len(parts) == 1:
                        application_name = parts[0].strip().strip('"')

            if window_title and application_name:
                return (window_title, application_name)
            else:
                self.logger.debug("ウィンドウ情報の取得に失敗しました（タイトルまたはアプリ名が空）")
                return None

        except subprocess.CalledProcessError as e:
            self.logger.debug(f"ウィンドウ情報取得エラー: {e}")
            return None
        except FileNotFoundError as e:
            self.logger.error(
                f"必要なコマンドが見つかりません: {e}\n"
                "xdotoolとxpropをインストールしてください:\n"
                "  sudo apt install xdotool x11-utils"
            )
            return None
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            return None

    def start_monitoring(self):
        """
        監視を開始

        監視ループを実行し、アクティブウィンドウの変化を検出してセッションを記録する。
        """
        self.is_running = True
        self.logger.info("デスクトップアクティビティの監視を開始しました")

        try:
            while self.is_running:
                # アクティブウィンドウ情報を取得
                window_info = self.get_active_window_info()

                if window_info:
                    window_title, application_name = window_info
                    self._process_window_change(application_name, window_title)

                # 監視間隔待機
                time.sleep(self.monitor_interval)

        except KeyboardInterrupt:
            self.logger.info("\nキーボード割り込みを受信しました")
        finally:
            self.stop_monitoring()

    def stop_monitoring(self):
        """
        監視を停止

        現在のセッションを終了し、データベース接続をクローズする。
        """
        self.is_running = False

        # 現在のセッションを終了
        if self.current_session_id:
            self._end_current_session()

        self.logger.info("デスクトップアクティビティの監視を停止しました")

    def _process_window_change(self, application_name: str, window_title: str):
        """
        ウィンドウ変更を処理

        Args:
            application_name: アプリケーション名
            window_title: ウィンドウタイトル
        """
        current_time = int(time.time())

        # 現在のセッションと同じかチェック
        if self.current_session and self.current_session.is_same_session(application_name, window_title):
            # 同じセッションなので何もしない
            self.logger.debug(f"セッション継続中: {application_name} - {window_title[:30]}")
            return

        # 異なるウィンドウに切り替わった場合

        # 前のセッションを終了
        if self.current_session_id:
            self._end_current_session()

        # 新しいセッションを開始
        self._start_new_session(application_name, window_title, current_time)

    def _start_new_session(self, application_name: str, window_title: str, start_time: int):
        """
        新しいセッションを開始

        Args:
            application_name: アプリケーション名
            window_title: ウィンドウタイトル
            start_time: 開始時刻（UNIXエポック秒）
        """
        self.current_session = ActivitySession(
            start_time=start_time,
            application_name=application_name,
            window_title=window_title
        )

        # データベースに保存
        self.current_session_id = self.database.save_session(self.current_session)
        self.current_session.id = self.current_session_id

        self.logger.info(
            f"新しいセッション開始: ID={self.current_session_id}, "
            f"app={application_name}, title={window_title[:50]}"
        )

    def _end_current_session(self):
        """現在のセッションを終了"""
        if not self.current_session_id:
            return

        end_time = int(time.time())

        # データベースの終了時刻を更新
        self.database.update_session_end_time(self.current_session_id, end_time)

        # セッション情報を取得して継続時間をログ出力
        session = self.database.get_session_by_id(self.current_session_id)
        if session:
            duration = session.duration_seconds or 0
            self.logger.info(
                f"セッション終了: ID={self.current_session_id}, "
                f"duration={duration}秒, "
                f"app={session.application_name}"
            )

        # 現在のセッションをクリア
        self.current_session = None
        self.current_session_id = None


def main():
    """
    メイン関数（スタンドアローン実行用）
    """
    import yaml
    from pathlib import Path

    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger(__name__)

    # 設定ファイルを読み込み
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"

    if not config_path.exists():
        logger.error(f"設定ファイルが見つかりません: {config_path}")
        logger.info("config.example.yamlをconfig.yamlにコピーしてください")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # データベースパスを解決（相対パスの場合は host-agent/ からの相対）
    db_path = config['database']['desktop_activity']['path']
    if not Path(db_path).is_absolute():
        db_path = str(Path(__file__).parent.parent / db_path)

    # データベース初期化
    database = DesktopActivityDatabase(db_path)

    # モニター起動
    monitor = LinuxX11Monitor(config, database)

    try:
        monitor.start_monitoring()
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
    finally:
        database.close()


if __name__ == "__main__":
    main()
