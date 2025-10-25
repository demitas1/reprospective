# 技術的決定：データベースアーキテクチャ

## 決定事項サマリー

- **Phase 1（初期実装）**: SQLite（ボリュームマウント共有） ✅ 実装済み
- **Phase 2（本格運用）**: PostgreSQL + SQLiteローカルキャッシュ（未実装）

---

## Phase 1: SQLite単独構成（現在）

### アーキテクチャ

```
host-agent/ → SQLite (data/host_agent.db)
services/   → SQLite (ボリュームマウントで同じファイルを共有)
```

### 採用理由

1. **セットアップが簡単**: ファイルベースで依存関係なし
2. **書き込み頻度が低い**: 10秒に1回程度なので競合リスク低い
3. **段階的移行**: Phase 2への移行が容易
4. **軽量**: リソース消費が少ない

### 制約事項

- 同時書き込みが弱い（ロック競合の可能性）
- ネットワーク経由のアクセス不可
- 大量データや高頻度アクセスには不向き

---

## Phase 2: ローカルキャッシュ + PostgreSQL同期（将来）

### アーキテクチャ概要

```
┌─────────────────────────┐
│ ホスト (host-agent)      │
│  DesktopActivityMonitor │
│         ↓               │
│  SQLite (ローカル)      │  ← 常時書き込み
└─────────┼───────────────┘
          ↓ バッチ同期
┌─────────────────────────┐
│ Docker (services)       │
│  PostgreSQL (メインDB)  │  ← AI分析、Web UIがアクセス
└─────────────────────────┘
```

### 動作フロー

1. **通常時**: host-agent → ローカルSQLiteに書き込み（常時）
2. **同期時**: ローカルSQLite → PostgreSQLへバッチ転送（定期実行）
3. **読み取り**: services → PostgreSQLから読み取り

### メリット

#### 高可用性
- DBサービス停止中でもhost-agentは動作継続
- ネットワーク障害時もデータ収集が止まらない

#### パフォーマンス
- ローカル書き込みは高速（ネットワーク遅延なし）
- バッチ転送で効率的

#### データ保護
- ローカルにバックアップが残る
- 同期失敗時もデータ損失なし

#### 段階的移行
- Phase 1のSQLiteコードを活用できる

### デメリット

- 同期ロジックの実装が必要
- データの二重管理（ストレージ消費増）
- リアルタイム性の低下（同期遅延）

### 実装時の設計

#### データベーススキーマ拡張

ローカルSQLiteに追加：
- `synced` フラグ（0: 未同期, 1: 同期済み）
- `synced_at` タイムスタンプ

PostgreSQLに追加：
- `source_host` データ元ホスト名
- `original_id` ローカルDBでのID

#### 同期設定（config.yaml）

```yaml
database:
  local:
    type: sqlite
    path: data/local_cache.db
  remote:
    type: postgresql
    host: localhost
    port: 5432
    database: reprospective
  sync:
    enabled: true
    interval: 60  # 秒
    batch_size: 1000
    retention_days: 7  # ローカルキャッシュ保持期間
```

---

## 移行パス

### Phase 1（現在）
- SQLite単独
- ボリュームマウントで共有

### Phase 1.5（移行準備）
- DatabaseAdapter抽象化層を導入
- SQLite/PostgreSQL切り替え可能に

### Phase 2（本格運用）
- ローカルキャッシュ + PostgreSQL同期
- DatabaseSyncManager実装

---

## 技術的決定の背景

### なぜSQLiteから始めるか

1. 現時点では書き込み頻度が低い（10秒〜数分に1回）
2. セットアップが簡単で開発が早い
3. host-agentが単独で動作可能（DB依存なし）

### なぜPhase 2でPostgreSQLか

1. 複数サービスからの同時アクセスに対応
2. 高度なクエリや集計機能
3. スケーラビリティ
4. バックアップ・レプリケーション機能

### なぜローカルキャッシュ方式か

1. host-agentの独立性を維持
2. オフライン耐性が高い
3. パフォーマンス低下を防ぐ

---

## 参考資料

- Phase 1実装: `host-agent/common/database.py`
- Phase 2設計: このドキュメント
