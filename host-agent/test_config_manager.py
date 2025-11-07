"""
ConfigManagerの動作確認テストスクリプト
"""
import sys
from pathlib import Path

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from common.config import ConfigManager

def test_config_manager():
    """ConfigManagerの動作確認"""
    print("=" * 60)
    print("ConfigManager 動作確認テスト")
    print("=" * 60)
    print()

    # ConfigManager初期化
    print("1. ConfigManagerを初期化...")
    try:
        config_manager = ConfigManager()
        print("   ✅ 初期化成功")
    except Exception as e:
        print(f"   ❌ 初期化失敗: {e}")
        return False

    print()

    # PostgreSQL URL取得
    print("2. PostgreSQL接続URLを取得...")
    try:
        postgres_url = config_manager.get_postgres_url()
        print(f"   ✅ PostgreSQL URL: {postgres_url}")

        # パスワード部分をマスク表示
        import re
        masked_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', postgres_url)
        print(f"   📝 マスク表示: {masked_url}")
    except Exception as e:
        print(f"   ❌ 取得失敗: {e}")
        return False

    print()

    # SQLiteパス取得
    print("3. SQLiteデータベースパスを取得...")
    try:
        desktop_path = config_manager.get_sqlite_desktop_path()
        file_events_path = config_manager.get_sqlite_file_events_path()
        print(f"   ✅ デスクトップDB: {desktop_path}")
        print(f"   ✅ ファイルイベントDB: {file_events_path}")

        # パスが絶対パスかチェック
        from pathlib import Path
        if Path(desktop_path).is_absolute():
            print(f"   ✅ デスクトップDBパスは絶対パス")
        else:
            print(f"   ⚠️  デスクトップDBパスは相対パス")

        if Path(file_events_path).is_absolute():
            print(f"   ✅ ファイルイベントDBパスは絶対パス")
        else:
            print(f"   ⚠️  ファイルイベントDBパスは相対パス")
    except Exception as e:
        print(f"   ❌ 取得失敗: {e}")
        return False

    print()

    # データ同期設定取得
    print("4. データ同期設定を取得...")
    try:
        sync_config = config_manager.get_data_sync_config()
        print(f"   ✅ 同期有効: {sync_config.get('enabled')}")
        print(f"   ✅ 同期間隔: {sync_config.get('sync_interval_seconds')}秒")
        print(f"   ✅ バッチサイズ: {sync_config.get('batch_size')}")
    except Exception as e:
        print(f"   ❌ 取得失敗: {e}")
        return False

    print()

    # デスクトップモニター設定取得
    print("5. デスクトップモニター設定を取得...")
    try:
        monitor_config = config_manager.get_desktop_monitor_config()
        print(f"   ✅ チェック間隔: {monitor_config.get('check_interval')}秒")
        print(f"   ✅ アイドル閾値: {monitor_config.get('idle_threshold')}秒")
    except Exception as e:
        print(f"   ❌ 取得失敗: {e}")
        return False

    print()

    # ファイルシステムウォッチャー設定取得
    print("6. ファイルシステムウォッチャー設定を取得...")
    try:
        fs_config = config_manager.get_filesystem_watcher_config()
        monitored_dirs = fs_config.get('monitored_directories', [])
        excluded_patterns = fs_config.get('excluded_patterns', [])
        print(f"   ✅ 監視ディレクトリ数: {len(monitored_dirs)}")
        if monitored_dirs:
            print(f"   📝 監視ディレクトリ:")
            for dir_path in monitored_dirs[:3]:  # 最初の3つのみ表示
                print(f"      - {dir_path}")
            if len(monitored_dirs) > 3:
                print(f"      ... 他 {len(monitored_dirs) - 3} 個")
        print(f"   ✅ 除外パターン数: {len(excluded_patterns)}")
    except Exception as e:
        print(f"   ❌ 取得失敗: {e}")
        return False

    print()
    print("=" * 60)
    print("✅ すべてのテストが成功しました！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_config_manager()
    sys.exit(0 if success else 1)
