# 技術決定: データベース分離アーキテクチャ

## 決定事項

各データコレクター（DesktopActivityMonitor、FileSystemWatcher等）は、独立したSQLiteデータベースファイルを使用する。

## 背景

### 現状の問題

- 複数のコレクターが単一のSQLiteデータベース（`host_agent.db`）を共有
- SQLiteはスレッドセーフではないため、`check_same_thread=False`だけでは競合問題が根本解決されない
- 将来的にコレクターが増えると競合リスクが増大
- 一つのコレクターのDB問題が全体に影響

## 新アーキテクチャ

### データベースファイル構成

```
data/
├── desktop_activity.db      # DesktopActivityMonitor専用
├── file_changes.db          # FileSystemWatcher専用
└── (将来) browser_activity.db
```

### クラス設計

各コレクター専用のDatabaseクラスを提供：

- `DesktopActivityDatabase`: desktop_activity_sessionsテーブルのみ
- `FileChangeDatabase`: file_change_eventsテーブルのみ

各クラスは独立したDB接続を持ち、スレッド競合が発生しない。

### 設定ファイル

```yaml
database:
  desktop_activity:
    path: data/desktop_activity.db
  file_changes:
    path: data/file_changes.db
```

## メリット

1. **スレッド安全性**: 各コレクターが独立したDB接続を持つため競合が解消
2. **独立性**: コレクターが独立して動作（障害の影響範囲を局所化）
3. **PostgreSQL同期の簡素化**:
   - 各DBファイルを独立して同期可能
   - 同期タイミングを個別に制御可能
   - 同期失敗時の影響を局所化
4. **デバッグの容易さ**: 問題のあるコレクターのDBだけを調査可能
5. **スケーラビリティ**: 新しいコレクター追加が容易

## デメリットと対策

### デメリット

1. クロスコレクター分析が複雑（複数DBにまたがるクエリ）
2. DBファイル数の増加

### 対策

- Phase 2でPostgreSQLに統合されるため、分析はPostgreSQL側で実施
- ローカルDBはキャッシュとして機能するだけなので、複雑なクエリは不要

## PostgreSQL同期設計（Phase 2）

### 同期方式

各ローカルDBから定期的にPostgreSQLへバッチ同期：

1. 各DBに`synced_at`カラムを追加
2. `synced_at IS NULL`のレコードを抽出
3. PostgreSQLへINSERT
4. 成功したら`synced_at`を更新

### 統合後のPostgreSQLスキーマ

全てのテーブルが単一のPostgreSQLデータベースに統合され、
クロスコレクター分析が可能になる。

## 移行方針

### Phase 1（現在）

- 既存の`host_agent.db`を使用しているコードをリファクタリング
- 各コレクターが専用DBファイルを使用するように変更
- 既存データの移行は不要（開発段階のため）

### Phase 2（将来）

- PostgreSQL同期機能の実装
- Web UIでの設定管理
- ローカルキャッシュとしてのSQLite活用

## 実装ファイル

- `common/database.py`: 分離されたDatabaseクラス
- `collectors/linux_x11_monitor.py`: DesktopActivityDatabase使用
- `collectors/filesystem_watcher.py`: FileChangeDatabase使用
- `config/config.yaml`: DB パス設定追加

## 参考

- SQLiteスレッドセーフティ: https://www.sqlite.org/threadsafe.html
- 設計原則: 単一責任の原則（SRP）- 各DBは一つのコレクターのみを担当
