# DesktopActivityMonitor 設計メモ

## 実装状況

✅ **Phase 1 実装完了** (2025-10-25)

実装の詳細は以下を参照：
- `host-agent/collectors/linux_x11_monitor.py`
- `host-agent/common/models.py`
- `host-agent/common/database.py`
- `host-agent/README.md`

---

## 目的

ホスト環境で動作するデスクトップアクティビティ監視コンポーネント。
フォアグラウンドウィンドウのタイトルとアプリケーション名を定期的に取得し、セッション単位でユーザーの活動を記録する。

## 設計方針

### セッション管理

- **セッション**: 同じアプリケーション＋同じウィンドウタイトルの連続した活動期間
- ウィンドウが変わったら前のセッションを終了し、新しいセッションを開始
- 同じウィンドウが続く場合は記録しない（重複排除）

### データ保存

- **Phase 1**: SQLite（`data/host_agent.db`）
- セッション開始時刻、終了時刻、継続時間を記録
- タイムスタンプはUNIXエポック秒とISO 8601形式の両方を保存

### 設定管理

- YAML形式（`config/config.yaml`）
- 監視間隔、ログレベルなどを設定可能

### エラーハンドリング

- ウィンドウ情報取得失敗: スキップして次のサイクルへ
- データベースエラー: ログ記録して継続
- Ctrl+C: 現在のセッションを正常終了

## 技術スタック

### 依存ツール
- **xdotool**: アクティブウィンドウID取得
- **xprop**: ウィンドウプロパティ取得
- **PyYAML**: 設定ファイル読み込み

### 対応環境
- **Phase 1**: Linux X11のみ
- **Phase 2以降**: Wayland、Windows、macOS対応予定

## 将来的な拡張

### Phase 2（未実装）
- Wayland対応（`swaymsg`）
- Windows対応（`pywin32`）
- macOS対応（`AppKit`）
- PostgreSQLへのデータ同期
- アイドル状態の検出

### Phase 3（未実装）
- BrowserActivityParserとの連携（URL解析など）
- アプリケーションカテゴリの自動分類
- プロジェクト推定機能

## テスト確認項目

- [x] 同じウィンドウが続く場合、セッションが継続される
- [x] ウィンドウ変更時、前のセッションが終了し新しいセッションが開始
- [x] 終了時刻（end_time）が正しく記録される
- [x] duration_secondsが正しく計算される
- [x] 設定ファイルの監視間隔が反映される
- [x] Ctrl+Cで正常終了処理が実行される

## 参考資料

- 企画書: `docs/software_idea-ai_assited_todo.md`
- 実装: `host-agent/`
