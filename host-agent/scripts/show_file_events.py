#!/usr/bin/env python3
"""
ファイルイベント表示スクリプト

データベースに記録されたファイル変更イベントを表示する。
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# host-agent/common をインポートパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from common.database import FileChangeDatabase


def format_size(size_bytes: int) -> str:
    """
    ファイルサイズを人間が読みやすい形式にフォーマット

    Args:
        size_bytes: バイト数

    Returns:
        str: フォーマットされたサイズ文字列
    """
    if size_bytes is None:
        return "-"

    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} TB"


def show_events(database: FileChangeDatabase, limit: int = 50):
    """
    ファイルイベントを表示

    Args:
        database: FileChangeDatabaseインスタンス
        limit: 表示する最大件数
    """
    events = database.get_recent_file_events(limit)

    if not events:
        print("ファイルイベントが見つかりません。")
        return

    print(f"\n{'='*100}")
    print(f"最近のファイルイベント（最大{limit}件）")
    print(f"{'='*100}\n")

    # 統計情報
    total_events = len(events)
    event_types = {}
    total_size = 0

    for event in events:
        event_type = event['event_type']
        event_types[event_type] = event_types.get(event_type, 0) + 1

        if event['file_size']:
            total_size += event['file_size']

    # イベント詳細を表示
    for i, event in enumerate(events, 1):
        event_time = datetime.fromtimestamp(event['event_time'])
        event_type = event['event_type']
        file_name = event['file_name']
        file_path = event['file_path']
        file_size = format_size(event['file_size']) if event['file_size'] else "-"
        project_name = event['project_name'] or "(不明)"
        is_symlink = "シンボリックリンク" if event['is_symlink'] else ""

        print(f"{i:3d}. [{event_time.strftime('%Y-%m-%d %H:%M:%S')}] "
              f"{event_type:8s} | {file_name}")
        print(f"     プロジェクト: {project_name}")
        print(f"     パス: {file_path}")
        print(f"     サイズ: {file_size} {is_symlink}")
        print()

    # 統計サマリー
    print(f"{'='*100}")
    print(f"統計情報")
    print(f"{'='*100}")
    print(f"総イベント数: {total_events}")
    print(f"イベント種類:")
    for event_type, count in sorted(event_types.items()):
        print(f"  - {event_type}: {count}件")
    print(f"総ファイルサイズ: {format_size(total_size)}")

    # 時間範囲
    if events:
        oldest = datetime.fromtimestamp(events[-1]['event_time'])
        newest = datetime.fromtimestamp(events[0]['event_time'])
        print(f"時間範囲: {oldest.strftime('%Y-%m-%d %H:%M:%S')} ～ "
              f"{newest.strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"{'='*100}\n")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='ファイル変更イベントをデータベースから取得して表示します'
    )
    parser.add_argument(
        'limit',
        nargs='?',
        type=int,
        default=50,
        help='表示する最大イベント数（デフォルト: 50）'
    )
    parser.add_argument(
        '--db',
        type=str,
        default='data/file_changes.db',
        help='データベースファイルのパス（デフォルト: data/file_changes.db）'
    )

    args = parser.parse_args()

    # データベースパス
    db_path = args.db
    if not Path(db_path).is_absolute():
        # 相対パスの場合は host-agent/ からの相対パスとする
        db_path = str(Path(__file__).parent.parent / db_path)

    # データベース存在チェック
    if not Path(db_path).exists():
        print(f"エラー: データベースファイルが見つかりません: {db_path}")
        print("FileSystemWatcher を実行してファイルイベントを記録してください。")
        return 1

    # データベース接続
    database = FileChangeDatabase(db_path)

    try:
        show_events(database, args.limit)
    finally:
        database.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
