"""
データモデル定義

アクティビティセッションやその他のデータ構造を定義する。
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class InputActivitySession:
    """
    入力活動セッションを表すデータクラス

    マウスまたはキーボードの入力が連続している期間を表す。
    入力種別（マウス/キーボード）は記録せず、セッション期間のみを記録する。
    """

    id: Optional[int] = None           # データベースのID（保存後に設定される）
    start_time: int = 0                # 開始時刻（UNIXエポック秒）
    end_time: Optional[int] = None     # 終了時刻（UNIXエポック秒、セッション継続中はNone）
    created_at: int = 0                # レコード作成時刻（UNIXエポック秒）
    updated_at: int = 0                # レコード更新時刻（UNIXエポック秒）

    @property
    def start_time_iso(self) -> str:
        """開始時刻のISO 8601形式文字列"""
        if self.start_time:
            return datetime.fromtimestamp(self.start_time).isoformat()
        return ""

    @property
    def end_time_iso(self) -> Optional[str]:
        """終了時刻のISO 8601形式文字列"""
        if self.end_time:
            return datetime.fromtimestamp(self.end_time).isoformat()
        return None

    @property
    def duration_seconds(self) -> Optional[int]:
        """セッションの継続時間（秒）"""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None

    def to_dict(self) -> dict:
        """辞書形式に変換（データベース保存用）"""
        return {
            'id': self.id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'start_time_iso': self.start_time_iso,
            'end_time_iso': self.end_time_iso,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @staticmethod
    def from_dict(data: dict) -> 'InputActivitySession':
        """辞書からInputActivitySessionオブジェクトを生成"""
        return InputActivitySession(
            id=data.get('id'),
            start_time=data.get('start_time', 0),
            end_time=data.get('end_time'),
            created_at=data.get('created_at', 0),
            updated_at=data.get('updated_at', 0)
        )

    def __repr__(self) -> str:
        """文字列表現"""
        duration = f"{self.duration_seconds}s" if self.duration_seconds else "継続中"
        return (f"InputActivitySession(id={self.id}, "
                f"start={self.start_time_iso}, "
                f"duration={duration})")


@dataclass
class ActivitySession:
    """
    活動セッションを表すデータクラス

    セッションは同じアプリケーション・同じウィンドウタイトルの連続した活動期間を表す。
    """

    id: Optional[int] = None           # データベースのID（保存後に設定される）
    start_time: int = 0                # 開始時刻（UNIXエポック秒）
    end_time: Optional[int] = None     # 終了時刻（UNIXエポック秒、セッション継続中はNone）
    application_name: str = ""         # アプリケーション名（例: "Brave-browser"）
    window_title: str = ""             # ウィンドウタイトル（例: "GitHub - Brave"）
    created_at: int = 0                # レコード作成時刻（UNIXエポック秒）
    updated_at: int = 0                # レコード更新時刻（UNIXエポック秒）

    @property
    def start_time_iso(self) -> str:
        """開始時刻のISO 8601形式文字列"""
        if self.start_time:
            return datetime.fromtimestamp(self.start_time).isoformat()
        return ""

    @property
    def end_time_iso(self) -> Optional[str]:
        """終了時刻のISO 8601形式文字列"""
        if self.end_time:
            return datetime.fromtimestamp(self.end_time).isoformat()
        return None

    @property
    def duration_seconds(self) -> Optional[int]:
        """セッションの継続時間（秒）"""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None

    def is_same_session(self, application_name: str, window_title: str) -> bool:
        """
        指定されたアプリケーション名とウィンドウタイトルが同じセッションかを判定

        Args:
            application_name: アプリケーション名
            window_title: ウィンドウタイトル

        Returns:
            bool: 同じセッションならTrue
        """
        return (self.application_name == application_name and
                self.window_title == window_title)

    def to_dict(self) -> dict:
        """辞書形式に変換（データベース保存用）"""
        return {
            'id': self.id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'start_time_iso': self.start_time_iso,
            'end_time_iso': self.end_time_iso,
            'application_name': self.application_name,
            'window_title': self.window_title,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @staticmethod
    def from_dict(data: dict) -> 'ActivitySession':
        """辞書からActivitySessionオブジェクトを生成"""
        return ActivitySession(
            id=data.get('id'),
            start_time=data.get('start_time', 0),
            end_time=data.get('end_time'),
            application_name=data.get('application_name', ''),
            window_title=data.get('window_title', ''),
            created_at=data.get('created_at', 0),
            updated_at=data.get('updated_at', 0)
        )

    def __repr__(self) -> str:
        """文字列表現"""
        duration = f"{self.duration_seconds}s" if self.duration_seconds else "継続中"
        return (f"ActivitySession(id={self.id}, "
                f"app='{self.application_name}', "
                f"title='{self.window_title[:30]}...', "
                f"duration={duration})")
