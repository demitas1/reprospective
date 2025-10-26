#!/usr/bin/env python3
"""
デバッグ用スクリプト: 最近のセッションを表示

使い方:
    python scripts/show_sessions.py [件数]

例:
    python scripts/show_sessions.py      # 最近の10件を表示
    python scripts/show_sessions.py 20   # 最近の20件を表示
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime


def format_duration(seconds):
    """
    秒数を読みやすい形式に変換

    Args:
        seconds: 秒数

    Returns:
        str: フォーマットされた文字列（例: "5m 30s", "1h 23m"）
    """
    if seconds is None:
        return "継続中"

    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}分{secs}秒"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}時間{minutes}分"


def show_sessions(limit=10):
    """
    最近のセッションを表示

    Args:
        limit: 表示する件数
    """
    # データベースパスを解決
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / "data" / "desktop_activity.db"

    if not db_path.exists():
        print(f"エラー: データベースファイルが見つかりません: {db_path}")
        print("まずモニターを起動してデータを記録してください。")
        return

    # データベースに接続
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 最近のセッションを取得
    cursor.execute("""
        SELECT
            id,
            start_time,
            end_time,
            duration_seconds,
            application_name,
            window_title
        FROM desktop_activity_sessions
        ORDER BY start_time DESC
        LIMIT ?
    """, (limit,))

    sessions = cursor.fetchall()

    if not sessions:
        print("データベースにセッションがありません。")
        print("モニターを起動してデータを記録してください。")
        conn.close()
        return

    # ヘッダー表示
    print(f"\n最近の{len(sessions)}件のセッション:")
    print("=" * 120)
    print(f"{'ID':>4} | {'開始時刻':19} | {'終了時刻':19} | {'継続時間':>12} | {'アプリケーション':25} | タイトル")
    print("-" * 120)

    # セッション表示
    for session in sessions:
        session_id = session['id']

        # 時刻をフォーマット
        start_dt = datetime.fromtimestamp(session['start_time'])
        start_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')

        if session['end_time']:
            end_dt = datetime.fromtimestamp(session['end_time'])
            end_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            end_str = "---                "

        # 継続時間をフォーマット
        duration_str = format_duration(session['duration_seconds'])

        # アプリケーション名（長すぎる場合は切り詰め）
        app_name = session['application_name']
        if len(app_name) > 25:
            app_name = app_name[:22] + "..."

        # ウィンドウタイトル（長すぎる場合は切り詰め）
        title = session['window_title']
        if len(title) > 50:
            title = title[:47] + "..."

        print(f"{session_id:4} | {start_str} | {end_str} | {duration_str:>12} | {app_name:25} | {title}")

    print("=" * 120)

    # 統計情報を表示
    cursor.execute("""
        SELECT
            COUNT(*) as total_sessions,
            SUM(duration_seconds) as total_duration,
            MIN(start_time) as first_session,
            MAX(start_time) as last_session
        FROM desktop_activity_sessions
        WHERE duration_seconds IS NOT NULL
    """)

    stats = cursor.fetchone()

    print(f"\n統計情報:")
    print(f"  総セッション数: {stats['total_sessions']}件")

    if stats['total_duration']:
        total_duration_str = format_duration(stats['total_duration'])
        print(f"  総記録時間: {total_duration_str}")

    if stats['first_session']:
        first_dt = datetime.fromtimestamp(stats['first_session'])
        print(f"  最初の記録: {first_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    if stats['last_session']:
        last_dt = datetime.fromtimestamp(stats['last_session'])
        print(f"  最新の記録: {last_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    print()

    conn.close()


def main():
    """メイン関数"""
    # コマンドライン引数から件数を取得
    limit = 10  # デフォルト

    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            if limit <= 0:
                print("エラー: 件数は正の整数を指定してください。")
                sys.exit(1)
        except ValueError:
            print(f"エラー: 無効な件数: {sys.argv[1]}")
            print("使い方: python scripts/show_sessions.py [件数]")
            sys.exit(1)

    show_sessions(limit)


if __name__ == "__main__":
    main()
