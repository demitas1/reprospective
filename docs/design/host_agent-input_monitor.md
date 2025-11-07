# InputMonitor 設計書

## 実装状況

✅ 設計完了（2025-11-07）
📋 実装準備中

---

## 目的

ホスト環境で動作する入力デバイス監視コンポーネント。
マウス、キーボードの入力を監視し、入力活動がある期間を記録する。

**プライバシー保護**: 入力イベントの発生のみ検知し、具体的な入力内容（キーストローク、マウス座標等）は記録しない。

---

## 設計方針

### セッション管理

- **セッション**: マウスまたはキーボードの入力が設定した一定時間以内に連続して行われている期間をユーザーが活動している時間として記録する
- **無操作タイムアウト**: デフォルト120秒（設定可能）の間、マウスもキーボードも入力がない場合、活動中断と判断しセッション終了とする
- **セッション再開**: 活動中断状態からマウスまたはキーボードの入力があった場合、新しいセッションが開始されたと判断する
- **セッション統合**: マウスとキーボードが同時に動いている場合、単一のセッションとして記録（別々に分けない）

### 記録するデータ

**最小限のデータのみ記録**（粒度: A）:
- セッション開始時刻（UNIXタイムスタンプ）
- セッション終了時刻（UNIXタイムスタンプ）
- 継続時間（秒）

**記録しないデータ**:
- 入力種別（マウス/キーボード）
- キーストローク内容
- マウス座標・移動距離
- その他の詳細統計

**理由**: シンプルに「ユーザーが活動していた期間」を記録することが目的。詳細な統計は不要。

### データ保存

**SQLiteローカルキャッシュ**:
- データベースファイル: `data/input_activity.db`
- テーブル: `input_activity_sessions`

**PostgreSQL中央DB**:
- テーブル: `input_activity_sessions`
- 既存の`DataSyncManager`を使用してバッチ同期

**スキーマ設計**:
```sql
-- SQLite版
CREATE TABLE input_activity_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time INTEGER NOT NULL,          -- UNIXタイムスタンプ（秒）
    end_time INTEGER,                     -- セッション継続中はNULL
    start_time_iso TEXT NOT NULL,         -- ISO 8601形式
    end_time_iso TEXT,
    duration_seconds INTEGER,             -- 継続時間（秒）
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    synced_at INTEGER                     -- PostgreSQL同期用
);

CREATE INDEX idx_input_start_time ON input_activity_sessions(start_time);
CREATE INDEX idx_input_synced_at ON input_activity_sessions(synced_at);

-- PostgreSQL版
CREATE TABLE input_activity_sessions (
    id SERIAL PRIMARY KEY,
    start_time BIGINT NOT NULL,
    end_time BIGINT,
    start_time_iso TIMESTAMP NOT NULL,
    end_time_iso TIMESTAMP,
    duration_seconds INTEGER,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    host_identifier TEXT NOT NULL,        -- 同期元ホスト識別子
    synced_from_local_id INTEGER          -- ローカルDB ID
);

CREATE INDEX idx_input_start_time ON input_activity_sessions(start_time);
CREATE INDEX idx_input_host_identifier ON input_activity_sessions(host_identifier);
```

### 設定管理

`config.yaml`に以下の設定を追加:

```yaml
# 入力デバイス監視設定
input_monitor:
  enabled: true                    # 監視有効化
  idle_timeout_seconds: 120        # 無操作タイムアウト（秒）
```

環境変数:
```bash
SQLITE_INPUT_PATH=data/input_activity.db  # SQLiteパス（オプション）
```

### エラーハンドリング

- **入力監視失敗**: ライブラリ初期化エラー時、フォールバック実装を試行
- **権限エラー**: ユーザーに権限不足を通知し、セットアップ手順を表示
- **データベースエラー**: 既存のhost-agentと同様のエラーハンドリング
- **同期エラー**: 既存の`DataSyncManager`のリトライロジックを使用

---

## 技術スタック

### 依存ツール

**優先順位順に実装を試行**:

1. **pynput** (第一選択)
   - クロスプラットフォーム、使いやすい
   - X11環境で通常ユーザー権限で動作
   - インストール: `pip install pynput`

2. **python-xlib** (フォールバック1)
   - X11イベント監視
   - X11環境専用
   - インストール: `pip install python-xlib`

3. **python-evdev** (フォールバック2)
   - Linuxカーネルの入力デバイスインターフェース
   - rootまたはinputグループ権限が必要
   - インストール: `pip install evdev`

**その他**:
- **PyYAML**: 設定ファイル読み込み
- **asyncio**: 非同期処理
- **threading**: セッションタイムアウト監視

### 対応環境

**Phase 1（現在）**:
- Linux X11環境

**Phase 2（将来）**:
- Linux Wayland環境
- Windows
- macOS

---

## アーキテクチャ

### データモデル

`common/models.py`に`InputActivitySession`クラスを追加:

```python
@dataclass
class InputActivitySession:
    """
    入力活動セッションを表すデータクラス

    マウスまたはキーボードの入力が連続している期間を表す。
    """

    id: Optional[int] = None           # データベースのID
    start_time: int = 0                # 開始時刻（UNIXエポック秒）
    end_time: Optional[int] = None     # 終了時刻（UNIXエポック秒）
    created_at: int = 0                # レコード作成時刻
    updated_at: int = 0                # レコード更新時刻

    @property
    def start_time_iso(self) -> str:
        """開始時刻のISO 8601形式文字列"""
        return datetime.fromtimestamp(self.start_time).isoformat()

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
```

### データベースクラス

`common/database.py`に`InputActivityDatabase`クラスを追加:

```python
class InputActivityDatabase:
    """入力活動セッションのデータベース操作クラス"""

    def __init__(self, db_path: str):
        """初期化"""

    def create_session(self, session: InputActivitySession) -> int:
        """セッション作成"""

    def update_session(self, session: InputActivitySession) -> None:
        """セッション更新"""

    def get_unsynced_sessions(self, limit: int = 100) -> List[InputActivitySession]:
        """未同期セッション取得"""

    def mark_sessions_as_synced(self, session_ids: List[int]) -> None:
        """同期済みフラグ更新"""
```

### コレクタークラス

`collectors/input_monitor.py`:

```python
class InputMonitor:
    """入力デバイス監視クラス"""

    def __init__(self, config: dict, database: InputActivityDatabase):
        """初期化"""
        self.config = config
        self.database = database
        self.idle_timeout = config.get('input_monitor', {}).get('idle_timeout_seconds', 120)
        self.current_session: Optional[InputActivitySession] = None
        self.last_input_time: float = 0

    def start_monitoring(self) -> None:
        """監視開始（pynput → xlib → evdev の順で試行）"""

    def _try_pynput(self) -> bool:
        """pynputで監視を試行"""

    def _try_xlib(self) -> bool:
        """xlibで監視を試行"""

    def _try_evdev(self) -> bool:
        """evdevで監視を試行"""

    def _on_input_event(self) -> None:
        """入力イベント発生時のコールバック"""

    def _check_session_timeout(self) -> None:
        """セッションタイムアウトチェック（別スレッドで実行）"""

    def _start_session(self) -> None:
        """セッション開始"""

    def _end_session(self) -> None:
        """セッション終了"""
```

---

## 実装計画

### Phase 1: 基盤実装（2-3時間）

1. **データモデル実装**: `InputActivitySession`クラス追加
2. **データベースクラス実装**: `InputActivityDatabase`クラス追加
3. **PostgreSQLスキーマ追加**: `04_add_input_activity_sessions.sql`作成
4. **設定ファイル更新**: `config.yaml`に`input_monitor`セクション追加
5. **依存パッケージ追加**: `requirements.txt`更新

### Phase 2: コレクター実装（3-4時間）

1. **InputMonitorクラス実装**: 基本構造
2. **pynput統合**: 第一選択の実装
3. **フォールバック実装**: xlib, evdev対応
4. **セッション管理**: タイムアウト監視、開始/終了処理
5. **エラーハンドリング**: 権限エラー、ライブラリエラー対応

### Phase 3: データ同期統合（1-2時間）

1. **DataSyncManager拡張**: `input_activity_sessions`テーブル同期追加
2. **バッチ同期テスト**: SQLite → PostgreSQL同期確認

### Phase 4: デバッグ・テスト（1-2時間）

1. **デバッグスクリプト作成**: `scripts/show_input_sessions.py`
2. **手動テスト実施**: 入力監視、セッション記録、同期確認
3. **ドキュメント更新**: README.md, CLAUDE.md

**総推定工数**: 7-11時間

---

## テスト確認項目

### 機能テスト

- [ ] pynputで入力イベント検知
- [ ] フォールバック実装（xlib, evdev）が動作
- [ ] セッション開始が正しく記録される
- [ ] セッション終了（120秒タイムアウト）が正しく記録される
- [ ] セッション再開時に新しいセッションが作成される
- [ ] SQLiteにセッションが保存される
- [ ] PostgreSQLへ同期が成功する

### エッジケーステスト

- [ ] 権限不足時のエラーメッセージ表示
- [ ] ライブラリ未インストール時のフォールバック
- [ ] 長時間セッション（数時間）の記録
- [ ] 短時間セッション（数秒）の記録
- [ ] データベース接続失敗時の挙動

### パフォーマンステスト

- [ ] 入力イベント処理のCPU使用率
- [ ] メモリ使用量（長時間実行）
- [ ] データベース書き込み頻度

---

## セキュリティ考慮事項

### プライバシー保護

- ✅ キーストローク内容を記録しない
- ✅ マウス座標を記録しない
- ✅ 入力内容に関する情報を一切記録しない
- ✅ 「活動していた期間」のみ記録

### 権限管理

- pynput: 通常ユーザー権限で動作（X11環境）
- evdev: inputグループまたはroot権限が必要
- 権限不足時は明確なエラーメッセージを表示

### データ保護

- ローカルDB: `data/input_activity.db`（gitignore対象）
- PostgreSQL: 環境変数で認証情報管理
- 同期データ: 匿名化不要（セッション時刻のみ）

---

## 将来の拡張

### Phase 2以降

- Wayland環境対応
- Windows環境対応（`pywin32`）
- macOS環境対応（`Quartz`）
- Web UI統合（入力活動グラフ表示）
- 他のコレクターとの相関分析（デスクトップ活動 vs 入力活動）

---

## 参考資料

- [pynput ドキュメント](https://pynput.readthedocs.io/)
- [python-xlib GitHub](https://github.com/python-xlib/python-xlib)
- [python-evdev ドキュメント](https://python-evdev.readthedocs.io/)
