#!/usr/bin/env python3
"""
データベース初期化スクリプト

データベースファイルを削除し、クリーンな状態から開始できるようにする。

使い方:
    python scripts/reset_database.py              # すべてのDBを削除
    python scripts/reset_database.py --desktop    # デスクトップアクティビティDBのみ削除
    python scripts/reset_database.py --files      # ファイル変更イベントDBのみ削除

注意:
    このスクリプトを実行すると、すべてのデータが削除されます。
    実行前に確認プロンプトが表示されます。
"""

import sys
import sqlite3
from pathlib import Path


def get_db_info(db_path: Path, table_name: str) -> int:
    """
    データベースの情報を取得

    Args:
        db_path: データベースファイルパス
        table_name: テーブル名

    Returns:
        int: レコード数
    """
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def reset_database(db_type='all', force=False):
    """
    データベースをリセット

    Args:
        db_type: 'all', 'desktop', 'files'のいずれか
        force: True の場合、確認なしで削除
    """
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"

    # 削除対象のDBを決定
    dbs_to_reset = []

    if db_type in ['all', 'desktop']:
        desktop_db = data_dir / "desktop_activity.db"
        if desktop_db.exists():
            count = get_db_info(desktop_db, 'desktop_activity_sessions')
            dbs_to_reset.append(('デスクトップアクティビティDB', desktop_db, f'{count}件のセッション'))
        elif db_type == 'desktop':
            print(f"デスクトップアクティビティDBが存在しません: {desktop_db}")
            return

    if db_type in ['all', 'files']:
        files_db = data_dir / "file_changes.db"
        if files_db.exists():
            count = get_db_info(files_db, 'file_change_events')
            dbs_to_reset.append(('ファイル変更イベントDB', files_db, f'{count}件のイベント'))
        elif db_type == 'files':
            print(f"ファイル変更イベントDBが存在しません: {files_db}")
            return

    if not dbs_to_reset:
        print("削除するデータベースファイルが見つかりません。")
        print("既にクリーンな状態です。")
        return

    # データベースの情報を表示
    print("\n削除対象のデータベース:")
    print("=" * 70)
    for name, path, info in dbs_to_reset:
        print(f"  {name}")
        print(f"    パス: {path}")
        print(f"    データ: {info}")
    print("=" * 70)

    # 確認プロンプト
    if not force:
        print("\n警告: この操作はすべてのデータを削除します。")
        response = input("本当に削除しますか？ (yes/no): ").strip().lower()

        if response not in ['yes', 'y']:
            print("キャンセルしました。")
            return

    # データベースファイルを削除
    print()
    for name, path, _ in dbs_to_reset:
        try:
            path.unlink()
            print(f"✓ {name}を削除しました: {path}")
        except Exception as e:
            print(f"✗ {name}の削除に失敗しました: {e}")
            sys.exit(1)

    print("\n次回モニター起動時に新しいデータベースが作成されます。")


def main():
    """メイン関数"""
    # コマンドライン引数をチェック
    db_type = 'all'
    force = False

    for arg in sys.argv[1:]:
        if arg in ['-h', '--help']:
            print(__doc__)
            return
        elif arg in ['-f', '--force']:
            force = True
        elif arg == '--desktop':
            db_type = 'desktop'
        elif arg == '--files':
            db_type = 'files'
        else:
            print(f"不明なオプション: {arg}")
            print("使い方: python scripts/reset_database.py [--desktop|--files] [-f|--force]")
            sys.exit(1)

    reset_database(db_type, force)


if __name__ == "__main__":
    main()
