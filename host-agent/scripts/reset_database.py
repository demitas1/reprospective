#!/usr/bin/env python3
"""
データベース初期化スクリプト

データベースファイルを削除し、クリーンな状態から開始できるようにする。

使い方:
    python scripts/reset_database.py

注意:
    このスクリプトを実行すると、すべてのセッションデータが削除されます。
    実行前に確認プロンプトが表示されます。
"""

import sys
from pathlib import Path


def reset_database(force=False):
    """
    データベースをリセット

    Args:
        force: True の場合、確認なしで削除
    """
    # データベースパスを解決
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / "data" / "host_agent.db"

    if not db_path.exists():
        print(f"データベースファイルが存在しません: {db_path}")
        print("既にクリーンな状態です。")
        return

    # データベースの情報を表示
    import sqlite3
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # セッション数を取得
        cursor.execute("SELECT COUNT(*) FROM desktop_activity_sessions")
        session_count = cursor.fetchone()[0]

        conn.close()

        print(f"\n現在のデータベース: {db_path}")
        print(f"記録されているセッション数: {session_count}件")
    except Exception as e:
        print(f"\nデータベース情報の取得中にエラーが発生しました: {e}")
        print(f"データベースファイル: {db_path}")

    # 確認プロンプト
    if not force:
        print("\n警告: この操作はすべてのセッションデータを削除します。")
        response = input("本当に削除しますか？ (yes/no): ").strip().lower()

        if response not in ['yes', 'y']:
            print("キャンセルしました。")
            return

    # データベースファイルを削除
    try:
        db_path.unlink()
        print(f"\n✓ データベースを削除しました: {db_path}")
        print("次回モニター起動時に新しいデータベースが作成されます。")
    except Exception as e:
        print(f"\nエラー: データベースの削除に失敗しました: {e}")
        sys.exit(1)


def main():
    """メイン関数"""
    # コマンドライン引数をチェック
    force = False
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-f', '--force']:
            force = True
        elif sys.argv[1] in ['-h', '--help']:
            print(__doc__)
            return
        else:
            print(f"不明なオプション: {sys.argv[1]}")
            print("使い方: python scripts/reset_database.py [-f|--force]")
            sys.exit(1)

    reset_database(force)


if __name__ == "__main__":
    main()
