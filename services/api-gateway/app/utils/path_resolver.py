"""
パス解決ユーティリティ

シンボリックリンクを含むディレクトリパスを実体パスに解決する機能を提供します。
"""
import os
import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def resolve_directory_path(input_path: str) -> Tuple[str, Optional[str]]:
    """
    ディレクトリパスを解決する

    Args:
        input_path: ユーザー入力のディレクトリパス

    Returns:
        (display_path, resolved_path) のタプル
        - display_path: ユーザー入力値（表示用、正規化済み）
        - resolved_path: 実体パス（監視用）、解決失敗時はNone

    Examples:
        >>> resolve_directory_path("/home/user/work")
        ("/home/user/work", "/mnt/ssd/work")  # シンボリックリンクの場合

        >>> resolve_directory_path("/home/user/projects")
        ("/home/user/projects", "/home/user/projects")  # 通常のディレクトリ

        >>> resolve_directory_path("/nonexistent")
        ("/nonexistent", None)  # 存在しないパス
    """
    # 入力パスをクリーンアップ
    display_path = input_path.strip()

    try:
        # パスオブジェクトを作成（~展開を含む）
        path = Path(display_path).expanduser()

        # 絶対パスに正規化
        display_path = str(path.absolute())

        # パスが存在する場合のみ解決を試みる
        if path.exists():
            try:
                # シンボリックリンクを解決
                resolved = path.resolve(strict=True)
                resolved_str = str(resolved)

                # 解決後のパスと元のパスが異なる場合、ログに記録
                if resolved_str != display_path:
                    logger.info(
                        f"パス解決成功: {display_path} -> {resolved_str}"
                    )

                return (display_path, resolved_str)

            except RuntimeError as e:
                # シンボリックリンクのループ検出
                logger.error(
                    f"シンボリックリンクループ検出: {display_path}, エラー: {e}"
                )
                return (display_path, None)

            except (OSError, PermissionError) as e:
                # 権限エラーやその他のOSエラー
                logger.warning(
                    f"パス解決失敗（権限エラー）: {display_path}, エラー: {e}"
                )
                # 権限がない場合でも、元のパスを返す
                return (display_path, display_path)

        else:
            # パスが存在しない場合
            logger.warning(
                f"パスが存在しません（将来作成される可能性があるため警告のみ）: {display_path}"
            )
            # 将来作成される可能性があるため、拒否はせずNoneを返す
            return (display_path, None)

    except Exception as e:
        # その他の予期しないエラー
        logger.error(
            f"パス解決中に予期しないエラー: {display_path}, エラー: {e}",
            exc_info=True
        )
        return (display_path, None)


def validate_absolute_path(path: str) -> bool:
    """
    パスが絶対パスかどうかを検証する

    Args:
        path: 検証するパス

    Returns:
        絶対パスの場合True、それ以外False
    """
    try:
        return Path(path).is_absolute()
    except Exception:
        return False


def check_path_accessibility(path: str) -> Tuple[bool, Optional[str]]:
    """
    パスが読み取り可能かどうかをチェックする

    Args:
        path: チェックするパス

    Returns:
        (is_accessible, error_message) のタプル
        - is_accessible: アクセス可能な場合True
        - error_message: エラーメッセージ（アクセス可能な場合はNone）
    """
    try:
        path_obj = Path(path)

        # パスが存在しない場合
        if not path_obj.exists():
            return (False, f"パスが存在しません: {path}")

        # ディレクトリではない場合
        if not path_obj.is_dir():
            return (False, f"ディレクトリではありません: {path}")

        # 読み取り権限がない場合
        if not os.access(path, os.R_OK):
            return (False, f"読み取り権限がありません: {path}")

        # 実行権限がない場合（ディレクトリの場合、実行権限が必要）
        if not os.access(path, os.X_OK):
            return (False, f"実行権限がありません: {path}")

        return (True, None)

    except Exception as e:
        return (False, f"パスのアクセス確認中にエラー: {e}")
