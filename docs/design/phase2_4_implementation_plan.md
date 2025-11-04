# Phase 2.4 実装計画: Web UI 活動データ可視化

**ステータス: 📋 計画中**

**前提条件:** Phase 2.3 (SQLite → PostgreSQL データ同期) 完了

---

## 概要

Phase 2.4では、PostgreSQLに同期された活動データ（デスクトップアクティビティ、ファイル変更イベント）をWeb UIで可視化する機能を実装します。これにより、ユーザーは「何をしていたか」を直感的に把握でき、プロジェクトのコア機能「記録から振り返りまで」の基本サイクルが完成します。

### 実装目標

- **活動タイムライン表示**: 日別・時間別のアクティビティ可視化
- **セッション一覧**: デスクトップアクティビティセッションの検索・フィルタ
- **ファイル変更履歴**: プロジェクト別・拡張子別のファイル変更追跡
- **統計ダッシュボード**: 日別・週別・月別の活動サマリー
- **同期ステータス表示**: データ同期状態の監視・トラブルシューティング

### 対象範囲

- **API Gateway拡張**: 活動データ取得APIエンドポイント
- **Web UIページ追加**: 4つの新規ページ（ダッシュボード、セッション、ファイル、同期）
- **データ集計**: PostgreSQLビュー・集計クエリ
- **UI/UXデザイン**: Shadcn/ui コンポーネント、Recharts グラフ
- **リアルタイム更新**: React Query自動リフレッシュ

### 対象外（将来実装）

- **高度な分析機能**（Phase 3: AI分析エンジン統合）
- **複数ホストの統合ビュー**（Phase 3: マルチホスト管理）
- **カスタムレポート生成**（Phase 3: レポート機能）
- **データエクスポート**（Phase 3: CSV/JSON出力）

---

## アーキテクチャ

### システム構成

```
┌─────────────────────────────────────────────────────┐
│                    Web UI                           │
│                 (React 19 + Vite)                   │
│                                                     │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐  │
│  │ Dashboard  │  │ Sessions   │  │ File Events │  │
│  │ Page       │  │ Page       │  │ Page        │  │
│  └──────┬─────┘  └──────┬─────┘  └──────┬──────┘  │
│         │               │                │         │
│         └───────────────┼────────────────┘         │
│                         │                          │
│                         ▼                          │
│              ┌───────────────────┐                 │
│              │  API Client       │                 │
│              │  (Axios + React   │                 │
│              │   Query)          │                 │
│              └─────────┬─────────┘                 │
└────────────────────────┼─────────────────────────┘
                         │ HTTP REST API
                         ▼
              ┌──────────────────────┐
              │   API Gateway        │
              │   (FastAPI)          │
              │                      │
              │  ┌────────────────┐  │
              │  │ /api/v1/       │  │
              │  │  activities/*  │  │
              │  └────────┬───────┘  │
              └───────────┼──────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  PostgreSQL  │
                   │              │
                   │ - desktop_   │
                   │   activity_  │
                   │   sessions   │
                   │ - file_      │
                   │   change_    │
                   │   events     │
                   │ - sync_logs  │
                   └──────────────┘
```

### データフロー

**活動データ取得フロー:**

```
1. ユーザーがダッシュボードにアクセス
   ↓
2. React Query が API Gateway にリクエスト
   GET /api/v1/activities/sessions?date=2025-11-04
   ↓
3. API Gateway が PostgreSQL にクエリ
   SELECT * FROM desktop_activity_sessions WHERE DATE(start_time_iso) = '2025-11-04'
   ↓
4. データを JSON で返却
   ↓
5. Web UI でグラフ・テーブル表示
```

---

## API設計

### 新規エンドポイント

#### 1. デスクトップアクティビティ取得

**GET /api/v1/activities/sessions**

日付範囲でデスクトップアクティビティセッションを取得

**クエリパラメータ:**
- `date` (optional): 特定の日付（YYYY-MM-DD）
- `start_date` (optional): 開始日
- `end_date` (optional): 終了日
- `application` (optional): アプリケーション名でフィルタ
- `limit` (optional): 最大件数（デフォルト100）
- `offset` (optional): オフセット（ページネーション用）

**レスポンス例:**

```json
{
  "total": 250,
  "limit": 100,
  "offset": 0,
  "sessions": [
    {
      "id": 1,
      "start_time": 1730732400,
      "end_time": 1730733000,
      "start_time_iso": "2025-11-04T10:00:00+09:00",
      "end_time_iso": "2025-11-04T10:10:00+09:00",
      "application_name": "Firefox",
      "window_title": "GitHub - reprospective",
      "duration_seconds": 600,
      "synced_at": "2025-11-04T10:15:00+09:00"
    }
  ]
}
```

#### 2. 日別アクティビティサマリー

**GET /api/v1/activities/daily-summary**

日別・アプリケーション別の集計データを取得

**クエリパラメータ:**
- `start_date` (required): 開始日（YYYY-MM-DD）
- `end_date` (required): 終了日（YYYY-MM-DD）

**レスポンス例:**

```json
{
  "summaries": [
    {
      "date": "2025-11-04",
      "application_name": "VSCode",
      "session_count": 15,
      "total_duration_seconds": 18000,
      "avg_duration_seconds": 1200
    }
  ]
}
```

#### 3. ファイル変更イベント取得

**GET /api/v1/activities/file-events**

ファイル変更イベントを取得

**クエリパラメータ:**
- `date` (optional): 特定の日付
- `start_date` (optional): 開始日
- `end_date` (optional): 終了日
- `project_name` (optional): プロジェクト名でフィルタ
- `event_type` (optional): イベントタイプ（created/modified/deleted/moved）
- `file_extension` (optional): 拡張子でフィルタ（例: .py, .js）
- `limit` (optional): 最大件数（デフォルト100）
- `offset` (optional): オフセット

**レスポンス例:**

```json
{
  "total": 1500,
  "limit": 100,
  "offset": 0,
  "events": [
    {
      "id": 1,
      "event_time": 1730732450,
      "event_time_iso": "2025-11-04T10:00:50+09:00",
      "event_type": "modified",
      "file_path": "/path/to/file.py",
      "file_path_relative": "src/file.py",
      "file_name": "file.py",
      "file_extension": ".py",
      "file_size": 5120,
      "is_symlink": false,
      "monitored_root": "/path/to",
      "project_name": "reprospective",
      "synced_at": "2025-11-04T10:01:00+09:00"
    }
  ]
}
```

#### 4. ファイル変更サマリー

**GET /api/v1/activities/file-summary**

日別・プロジェクト別・拡張子別の集計データ

**クエリパラメータ:**
- `start_date` (required): 開始日
- `end_date` (required): 終了日
- `group_by` (optional): グループ化基準（project/extension/event_type、デフォルト: project）

**レスポンス例:**

```json
{
  "summaries": [
    {
      "date": "2025-11-04",
      "project_name": "reprospective",
      "event_type": "modified",
      "file_extension": ".py",
      "event_count": 120
    }
  ]
}
```

#### 5. 同期ステータス取得

**GET /api/v1/activities/sync-status**

データ同期の状態を取得（既存の`sync_logs`テーブルを利用）

**クエリパラメータ:**
- `limit` (optional): 最大件数（デフォルト20）

**レスポンス例:**

```json
{
  "latest_sync": {
    "sync_started_at": "2025-11-04T10:00:00+09:00",
    "sync_completed_at": "2025-11-04T10:00:05+09:00",
    "table_name": "desktop_activity_sessions",
    "records_synced": 150,
    "records_failed": 0,
    "status": "success",
    "host_identifier": "hostname_username"
  },
  "sync_logs": [...]
}
```

---

## データベース設計

### 新規ビュー（集計クエリ最適化）

#### daily_activity_summary ビュー（既存）

Phase 2で既に作成済み。最適化の余地があれば調整。

```sql
-- 既存ビューの確認・調整
SELECT * FROM daily_activity_summary
WHERE activity_date >= '2025-11-01'
ORDER BY activity_date DESC, total_duration_seconds DESC;
```

#### daily_file_changes_summary ビュー（既存）

Phase 2で既に作成済み。

---

## Web UI設計

### ページ構成

#### 1. ダッシュボードページ (`/dashboard`)

**コンポーネント:**
- `DashboardHeader`: 日付選択、リフレッシュボタン
- `ActivityChart`: 時間別アクティビティグラフ（Recharts Area Chart）
- `TopApplications`: 上位アプリケーションカード（使用時間順）
- `FileActivityCard`: ファイル変更統計カード
- `SyncStatusCard`: 同期ステータス表示

**技術スタック:**
- Recharts: グラフ表示
- date-fns: 日付操作
- React Query: データ取得・キャッシュ

#### 2. セッション一覧ページ (`/sessions`)

**コンポーネント:**
- `SessionFilters`: 日付範囲、アプリケーションフィルタ
- `SessionTable`: セッション一覧テーブル（ソート・ページネーション）
- `SessionDetailDialog`: セッション詳細モーダル

**機能:**
- ページネーション（100件ずつ）
- アプリケーション名でフィルタ
- 日付範囲指定
- CSVエクスポート（将来実装）

#### 3. ファイルイベントページ (`/file-events`)

**コンポーネント:**
- `FileEventFilters`: プロジェクト、拡張子、イベントタイプフィルタ
- `FileEventTable`: イベント一覧テーブル
- `FileTreeView`: プロジェクトツリービュー（将来実装）

**機能:**
- プロジェクト別フィルタ
- 拡張子別フィルタ（.py, .js, .tsx等）
- イベントタイプ別フィルタ（created/modified/deleted）

#### 4. 同期ステータスページ (`/sync-status`)

**コンポーネント:**
- `SyncStatusOverview`: 最新同期状態
- `SyncLogsTable`: 同期ログ履歴
- `SyncErrorsCard`: エラー通知

**機能:**
- 最終同期時刻表示
- 同期成功率グラフ
- エラーログ表示
- 手動同期トリガー（将来実装）

---

## 実装手順

### ステップ1: API Gateway拡張（推定3時間）

**タスク:**
1. `services/api-gateway/app/routers/activities.py` 作成
2. 5つのエンドポイント実装（sessions, daily-summary, file-events, file-summary, sync-status）
3. Pydanticモデル作成（`app/models/activities.py`）
4. クエリパラメータバリデーション
5. PostgreSQLクエリ実装
6. エラーハンドリング

**完了条件:**
- 全エンドポイントが正常動作
- Swagger UIでAPI確認可能
- ページネーション動作確認
- フィルタ機能動作確認

### ステップ2: Web UI型定義・API連携（推定2時間）

**タスク:**
1. `services/web-ui/src/types/activity.ts` 作成
2. `services/web-ui/src/api/activities.ts` 作成（APIクライアント関数）
3. React Queryカスタムフック作成
   - `useActivitySessions.ts`
   - `useDailySummary.ts`
   - `useFileEvents.ts`
   - `useFileSummary.ts`
   - `useSyncStatus.ts`
4. Zodバリデーションスキーマ作成

**完了条件:**
- 型定義が完全
- APIクライアント関数が動作
- React Queryフックが正常動作

### ステップ3: ダッシュボードページ実装（推定4時間）

**タスク:**
1. Rechartsインストール・設定
2. `DashboardPage.tsx` 作成
3. `ActivityChart.tsx` 作成（時間別アクティビティグラフ）
4. `TopApplications.tsx` 作成（上位アプリケーションカード）
5. `FileActivityCard.tsx` 作成（ファイル変更統計）
6. `SyncStatusCard.tsx` 作成（同期ステータス）
7. 日付選択コンポーネント（date-picker）

**完了条件:**
- ダッシュボードが表示される
- グラフが正常に描画される
- データがリアルタイムで更新される

### ステップ4: セッション一覧ページ実装（推定3時間）

**タスク:**
1. `SessionsPage.tsx` 作成
2. `SessionTable.tsx` 作成（Shadcn/ui Table）
3. `SessionFilters.tsx` 作成（日付範囲、アプリケーションフィルタ）
4. `SessionDetailDialog.tsx` 作成（詳細モーダル）
5. ページネーション実装

**完了条件:**
- セッション一覧が表示される
- フィルタ機能が動作
- ページネーションが動作
- 詳細モーダルが開く

### ステップ5: ファイルイベントページ実装（推定3時間）

**タスク:**
1. `FileEventsPage.tsx` 作成
2. `FileEventTable.tsx` 作成
3. `FileEventFilters.tsx` 作成（プロジェクト、拡張子、イベントタイプ）
4. イベントタイプアイコン表示（created=+, modified=✏️, deleted=🗑️）

**完了条件:**
- ファイルイベント一覧が表示される
- フィルタ機能が動作
- イベントタイプがアイコンで識別可能

### ステップ6: 同期ステータスページ実装（推定2時間）

**タスク:**
1. `SyncStatusPage.tsx` 作成
2. `SyncStatusOverview.tsx` 作成（最新同期状態）
3. `SyncLogsTable.tsx` 作成（同期ログ履歴）
4. `SyncErrorsCard.tsx` 作成（エラー通知）

**完了条件:**
- 同期ステータスが表示される
- 同期ログ履歴が確認できる
- エラーがあれば通知される

### ステップ7: ナビゲーション・統合（推定1時間）

**タスク:**
1. `Header.tsx` にナビゲーションリンク追加
2. React Router設定更新
3. 404ページ作成
4. ローディング状態の統一
5. エラー表示の統一

**完了条件:**
- 全ページにナビゲーションからアクセス可能
- ページ遷移がスムーズ
- ローディング・エラー表示が統一

### ステップ8: 統合テスト（推定2時間）

**タスク:**
1. 実データでの動作確認
2. パフォーマンステスト（大量データ）
3. レスポンシブデザイン確認
4. ブラウザ互換性確認
5. ドキュメント作成（`docs/manual/activity-viewer.md`）

**完了条件:**
- 全機能が正常動作
- パフォーマンスが許容範囲
- モバイルでも表示可能
- ユーザーマニュアル完成

---

## 技術スタック

### 新規追加パッケージ

**Web UI:**
```json
{
  "dependencies": {
    "recharts": "^2.10.0",         // グラフ描画
    "date-fns": "^3.0.0",          // 日付操作
    "react-day-picker": "^8.10.0"  // 日付選択
  }
}
```

**API Gateway:**
```txt
# 追加の依存パッケージは不要（既存のFastAPI, asyncpgで実装可能）
```

---

## 完了条件

- [ ] API Gateway に5つの新規エンドポイントが実装されている
- [ ] Swagger UIで全エンドポイントが確認できる
- [ ] Web UIに4つの新規ページが実装されている
- [ ] ダッシュボードでアクティビティグラフが表示される
- [ ] セッション一覧が検索・フィルタできる
- [ ] ファイルイベントがプロジェクト別に確認できる
- [ ] 同期ステータスが監視できる
- [ ] ページネーションが動作する
- [ ] レスポンシブデザインが実装されている
- [ ] ユーザーマニュアルが作成されている

---

## 技術的考慮事項

### パフォーマンス

- **データベースインデックス**: `start_time_iso`, `event_time_iso` にインデックス作成済み
- **ページネーション**: 大量データでもメモリ効率的
- **React Query キャッシュ**: 5分間キャッシュ、自動バックグラウンド更新
- **Lazy Loading**: 画像・大きなコンポーネントの遅延読み込み

### UX/UI

- **ローディング状態**: スケルトンスクリーン表示
- **エラーハンドリング**: ユーザーフレンドリーなエラーメッセージ
- **レスポンシブデザイン**: モバイル・タブレット対応
- **アクセシビリティ**: キーボードナビゲーション、ARIAラベル

### セキュリティ

- **入力バリデーション**: Pydantic + Zod二重チェック
- **SQLインジェクション対策**: asyncpgプレースホルダー使用
- **認証・認可**: Phase 3で実装予定（現在はローカル環境のみ）

---

## 将来的な拡張（Phase 3以降）

### 高度な分析機能

- **AI要約**: 1日の活動を自動要約
- **生産性スコア**: 作業パターン分析
- **推奨アクション**: 改善提案

### マルチホスト管理

- **複数PCの統合ビュー**: 職場・自宅のデータを統合
- **ホスト別フィルタ**: デバイスごとの活動追跡

### レポート機能

- **週次・月次レポート**: 自動生成
- **カスタムレポート**: ユーザー定義の集計
- **データエクスポート**: CSV/JSON/PDF出力

### リアルタイム更新

- **WebSocket統合**: リアルタイムデータ更新
- **通知機能**: 重要なイベント通知

---

## 参考リンク

- [Recharts Documentation](https://recharts.org/)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Shadcn/ui Components](https://ui.shadcn.com/)
- [FastAPI Pagination](https://fastapi-pagination.netlify.app/)

---

## 次のステップ

Phase 2.4実装開始後、以下の順で進めます：

1. API Gateway拡張（エンドポイント実装）
2. Web UI型定義・API連携
3. ダッシュボードページ実装
4. セッション一覧ページ実装
5. ファイルイベントページ実装
6. 同期ステータスページ実装
7. ナビゲーション・統合
8. 統合テスト・ドキュメント作成

各ステップ完了後、動作確認とドキュメント更新を行います。

---

**推定総工数:** 20時間（API 3h + 型定義 2h + Dashboard 4h + Sessions 3h + Files 3h + Sync 2h + Nav 1h + Test 2h）

**推定完了日:** 実装開始から3日間（1日6-8時間作業の場合）
