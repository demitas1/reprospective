# フロントエンドエラーロギング 利用マニュアル

**対象読者**: Reprospective開発者、デバッグ担当者

**最終更新**: 2025-11-02

---

## 目次

1. [概要](#概要)
2. [エラーロギングのON/OFF切り替え](#エラーロギングのonoff切り替え)
3. [エラーログの確認](#エラーログの確認)
4. [エラーログの消去](#エラーログの消去)
5. [細粒度制御（高度な使い方）](#細粒度制御高度な使い方)
6. [エラーテストページ](#エラーテストページ)
7. [トラブルシューティング](#トラブルシューティング)

---

## 概要

Reprospective Web UIでは、フロントエンド（ブラウザ）で発生したエラーを自動的にログファイルに記録する機能を提供しています。この機能により、Claude Codeが直接エラーログを確認してデバッグを支援できます。

**主要機能:**
- ✅ React Error Boundary、Axios、グローバルエラーなど5種類のエラーソースを自動記録
- ✅ 環境変数で簡単にON/OFF切り替え
- ✅ エラーソースごとに個別ON/OFF可能（細粒度制御）
- ✅ ブラウザコンソールから動的制御
- ✅ ログファイルはホスト環境から直接アクセス可能（`./logs/errors.log`）

**記録されるエラーの種類:**
1. **React Error Boundary** - Reactコンポーネント内のエラー
2. **React Query** - TanStack Queryのクエリ・ミューテーションエラー
3. **Axios** - HTTP通信エラー（API呼び出し失敗など）
4. **Global** - グローバルエラーハンドラー（`window.error`）
5. **UnhandledRejection** - キャッチされないPromise拒否

---

## エラーロギングのON/OFF切り替え

### 方法1: 環境変数で制御（推奨）

#### すべてのエラーログを有効化

1. `services/web-ui/.env` を編集:

```bash
# エラーロギング全体を有効化
VITE_ENABLE_ERROR_LOGGING=true

# 各ソースもすべて有効（デフォルトでtrue）
VITE_LOG_REACT=true
VITE_LOG_REACT_QUERY=true
VITE_LOG_AXIOS=true
VITE_LOG_GLOBAL=true
VITE_LOG_UNHANDLED_REJECTION=true
```

2. Web UIコンテナを再起動:

```bash
docker compose restart web-ui
```

3. ブラウザで http://localhost:3333 にアクセス

4. ブラウザの開発者ツール（F12）を開いてコンソールを確認:

```
[ErrorLogger] エラーロギング有効
[ErrorLogger] 設定: { react: true, reactQuery: true, axios: true, global: true, unhandledRejection: true }
```

✅ このメッセージが表示されれば、エラーロギングが有効になっています。

#### すべてのエラーログを無効化

1. `services/web-ui/.env` を編集:

```bash
# エラーロギング全体を無効化
VITE_ENABLE_ERROR_LOGGING=false
```

2. Web UIコンテナを再起動:

```bash
docker compose restart web-ui
```

✅ `[ErrorLogger]` メッセージが表示されなければ、無効化されています。

**注意事項:**
- ⚠️ 環境変数を変更した後は必ずコンテナを再起動してください
- ⚠️ 本番環境では `VITE_ENABLE_ERROR_LOGGING=false` に設定すること

---

## エラーログの確認

### 方法1: スクリプトで確認（推奨）

#### 最新10件を表示

```bash
./scripts/show-error-logs.sh
```

**出力例:**
```
========================================
フロントエンドエラーログ表示
========================================

総エラー件数: 15 件

最新 10 件のエラーログを表示:

{
  "timestamp": "2025-11-02T14:00:00Z",
  "message": "Uncaught TypeError: Cannot read property 'foo' of undefined",
  "stack": "Error: Cannot read property 'foo' of undefined\n    at App.tsx:42:15",
  "context": "global",
  "user_agent": "Mozilla/5.0 (X11; Linux x86_64)...",
  "url": "http://localhost:3333/",
  "component_stack": null,
  "additional_info": {
    "filename": "http://localhost:3333/src/App.tsx",
    "lineno": 42,
    "colno": 15
  }
}
...
```

#### 最新N件を表示

```bash
./scripts/show-error-logs.sh 50    # 最新50件
./scripts/show-error-logs.sh 100   # 最新100件
```

#### すべてのエラーログを表示

```bash
./scripts/show-error-logs.sh all
```

### 方法2: ファイルを直接確認

```bash
# ログファイルをそのまま表示
cat ./logs/errors.log

# jqで整形表示
cat ./logs/errors.log | jq '.'

# 最新20件を整形表示
tail -n 20 ./logs/errors.log | jq '.'
```

### 方法3: リアルタイム監視

エラーが発生したらリアルタイムで確認できます:

```bash
tail -f ./logs/errors.log | jq '.'
```

**使用例:**
1. ターミナルで上記コマンドを実行（実行したまま）
2. ブラウザで操作してエラーを発生させる
3. ターミナルに自動的にエラーログが表示される

**停止方法:** `Ctrl + C`

---

## エラーログの消去

### 方法1: スクリプトで消去（推奨）

#### 確認プロンプト付き消去

```bash
./scripts/clear-error-logs.sh
```

**実行例:**
```
========================================
フロントエンドエラーログ消去
========================================

現在のエラー件数: 15 件

最新5件のプレビュー:
     1	Uncaught TypeError: Cannot read property 'foo' of undefined
     2	Network Error: Failed to fetch
     3	API Error: 404 Not Found
     4	React Error: Objects are not valid as a React child
     5	Promise rejection: timeout

警告: この操作は元に戻せません！
すべてのエラーログを削除しますか？ (yes/no)
```

**`yes` と入力すると削除実行:**
```
✅ エラーログを消去しました

ログファイル: ./logs/errors.log
削除件数: 15 件

ログファイルは空になりました。
```

**`yes` 以外を入力するとキャンセル:**
```
キャンセルしました。
```

#### 強制消去（確認なし）

```bash
./scripts/clear-error-logs.sh -f
# または
./scripts/clear-error-logs.sh --force
```

**用途:** 自動化スクリプト、繰り返しテスト実行時など

### 方法2: ファイルを直接クリア

```bash
# ログファイルをクリア
> ./logs/errors.log

# または削除
rm ./logs/errors.log
```

**注意:** ファイルを削除した場合、次回エラー発生時に自動的に再作成されます。

---

## 細粒度制御（高度な使い方）

エラーソースごとにロギングをON/OFFできます。これにより、特定のエラーのみをフォーカスしてデバッグ効率を向上できます。

### 使用例1: Axiosエラーのみを記録

**状況:** API通信エラーだけをデバッグしたい

**設定:**

`services/web-ui/.env` を編集:

```bash
# 全体は有効
VITE_ENABLE_ERROR_LOGGING=true

# Axiosのみ有効、他は無効
VITE_LOG_REACT=false
VITE_LOG_REACT_QUERY=false
VITE_LOG_AXIOS=true
VITE_LOG_GLOBAL=false
VITE_LOG_UNHANDLED_REJECTION=false
```

Web UIを再起動:

```bash
docker compose restart web-ui
```

**結果:** Axios HTTPエラーのみがログに記録されます。

### 使用例2: React関連エラーのみを記録

**状況:** Reactコンポーネントのエラーだけをデバッグしたい

**設定:**

```bash
VITE_ENABLE_ERROR_LOGGING=true

# React Error BoundaryとReact Queryのみ有効
VITE_LOG_REACT=true
VITE_LOG_REACT_QUERY=true
VITE_LOG_AXIOS=false
VITE_LOG_GLOBAL=false
VITE_LOG_UNHANDLED_REJECTION=false
```

**結果:** React関連のエラーのみがログに記録されます。

### 使用例3: ブラウザコンソールから動的制御

**状況:** ブラウザで作業中に、リロードせずにロギング設定を変更したい

**手順:**

1. ブラウザの開発者ツール（F12）を開く
2. コンソールタブに切り替え
3. 以下のコマンドを実行:

```javascript
// 現在の設定を確認
window.__errorLogger.getConfig()
// → { react: true, reactQuery: true, axios: true, global: true, unhandledRejection: true }

// Axiosエラーを一時的に無効化
window.__errorLogger.setSourceEnabled('axios', false)
// → [ErrorLogger] axios ロギング: 無効

// 再度確認
window.__errorLogger.getConfig()
// → { react: true, reactQuery: true, axios: false, global: true, unhandledRejection: true }

// Axiosエラーを再度有効化
window.__errorLogger.setSourceEnabled('axios', true)
// → [ErrorLogger] axios ロギング: 有効
```

**利点:**
- ✅ ブラウザのリロード不要
- ✅ すぐに設定変更を試せる
- ✅ 一時的な制御に最適

**注意:** ブラウザをリロードすると環境変数の設定に戻ります。

### エラーソース一覧

| ソース名 | 説明 | 環境変数 | 動的制御 |
|---------|------|---------|---------|
| `react` | React Error Boundary | `VITE_LOG_REACT` | `window.__errorLogger.setSourceEnabled('react', true/false)` |
| `reactQuery` | React Query（TanStack Query） | `VITE_LOG_REACT_QUERY` | `window.__errorLogger.setSourceEnabled('reactQuery', true/false)` |
| `axios` | Axios HTTPエラー | `VITE_LOG_AXIOS` | `window.__errorLogger.setSourceEnabled('axios', true/false)` |
| `global` | グローバルエラーハンドラー | `VITE_LOG_GLOBAL` | `window.__errorLogger.setSourceEnabled('global', true/false)` |
| `unhandledRejection` | Promise拒否 | `VITE_LOG_UNHANDLED_REJECTION` | `window.__errorLogger.setSourceEnabled('unhandledRejection', true/false)` |

---

## エラーテストページ

エラーロギングが正常に動作しているかテストできる専用UIを提供しています。

### アクセス方法

```
http://localhost:3333/?test=error-logger
```

### 使用方法

1. ブラウザで上記URLにアクセス
2. 開発者ツール（F12）を開いてコンソールを表示
3. 「エラーロガーテスト」ページが表示される
4. 5種類のテストボタンが表示される:
   - **Test 1: React Error Boundary** - Reactエラーをスロー
   - **Test 2: グローバルエラー** - 存在しない関数を呼び出し
   - **Test 3: Promise拒否** - unhandledrejectionをトリガー
   - **Test 4: Axiosエラー** - 存在しないAPIエンドポイントにリクエスト（404）
   - **Test 5: 手動ログ** - `logError()` を直接呼び出し

5. テストボタンをクリック
6. 5秒待つ（バッファリングのため）
7. エラーログを確認:

```bash
./scripts/show-error-logs.sh
```

### テスト後のクリーンアップ

```bash
./scripts/clear-error-logs.sh -f
```

---

## トラブルシューティング

### Q1: エラーログが記録されない

**確認項目:**

1. **エラーロギングが有効か確認:**

```bash
# .envファイルを確認
cat services/web-ui/.env | grep VITE_ENABLE_ERROR_LOGGING
# → VITE_ENABLE_ERROR_LOGGING=true であること
```

2. **ブラウザコンソールでログ確認:**

ブラウザで http://localhost:3333 にアクセス後、開発者ツール（F12）を開いて:

```
[ErrorLogger] エラーロギング有効
```

このメッセージが表示されない場合:
- `VITE_ENABLE_ERROR_LOGGING=false` になっている
- Web UIコンテナが再起動されていない

**解決策:**

```bash
# .envを修正
vim services/web-ui/.env
# VITE_ENABLE_ERROR_LOGGING=true に設定

# コンテナ再起動
docker compose restart web-ui
```

3. **デバッグモードが有効か確認:**

```bash
# プロジェクトルートの.envを確認
cat .env | grep DEBUG
# → DEBUG=true であること
```

DEBUGがfalseの場合、API Gatewayがエラーログを受け付けません。

**解決策:**

```bash
# プロジェクトルートの.envを修正
vim .env
# DEBUG=true に設定

# API Gatewayコンテナ再起動
docker compose restart api-gateway
```

4. **API Gatewayが起動しているか確認:**

```bash
docker compose ps api-gateway
# → State: Up であること
```

### Q2: 特定のエラーソースが記録されない

**確認項目:**

1. **該当ソースが有効か確認:**

ブラウザコンソールで:

```javascript
window.__errorLogger.getConfig()
```

無効になっているソースがあれば:

```javascript
// 例: axiosを有効化
window.__errorLogger.setSourceEnabled('axios', true)
```

2. **環境変数を確認:**

```bash
cat services/web-ui/.env | grep VITE_LOG_
```

すべてのソースを有効化:

```bash
VITE_LOG_REACT=true
VITE_LOG_REACT_QUERY=true
VITE_LOG_AXIOS=true
VITE_LOG_GLOBAL=true
VITE_LOG_UNHANDLED_REJECTION=true
```

### Q3: ログファイルが見つからない

**確認項目:**

```bash
# ログファイルの存在確認
ls -la ./logs/errors.log
```

存在しない場合:

1. **まだエラーが発生していない:**
   - エラーテストページでエラーを発生させる: http://localhost:3333/?test=error-logger

2. **ディレクトリが存在しない:**

```bash
mkdir -p ./logs
touch ./logs/errors.log
```

3. **Dockerボリュームマウントの問題:**

```bash
# docker-compose.ymlを確認
grep -A 5 "api-gateway:" docker-compose.yml | grep volumes
# → - ./logs:/var/log/frontend:rw が含まれていること
```

### Q4: スクリプトが実行できない（Permission denied）

**原因:** 実行権限がない

**解決策:**

```bash
chmod +x ./scripts/show-error-logs.sh
chmod +x ./scripts/clear-error-logs.sh
```

### Q5: jqがインストールされていない

**症状:**
```
./scripts/show-error-logs.sh
# → jq: command not found
```

**解決策:**

```bash
# Ubuntu/Debian
sudo apt install jq

# macOS
brew install jq

# Fedora/RHEL
sudo dnf install jq
```

**代替手段（jqなしでも動作）:**

スクリプトはjqがなくても動作しますが、整形表示されません:

```bash
# 生のJSONが表示される
./scripts/show-error-logs.sh
```

---

## よくある使用パターン

### パターン1: 開発初期段階

**目的:** すべてのエラーを記録して全体像を把握

**設定:**

```bash
VITE_ENABLE_ERROR_LOGGING=true
# 個別設定は不要（デフォルトですべてtrue）
```

**ワークフロー:**

```bash
# 1. Web UI起動
docker compose up -d

# 2. ブラウザで操作
# http://localhost:3333

# 3. エラーログ確認
./scripts/show-error-logs.sh

# 4. 定期的にクリア
./scripts/clear-error-logs.sh -f
```

### パターン2: 特定エラーのデバッグ

**目的:** Axiosエラーだけにフォーカス

**設定:**

```bash
VITE_ENABLE_ERROR_LOGGING=true
VITE_LOG_REACT=false
VITE_LOG_REACT_QUERY=false
VITE_LOG_AXIOS=true
VITE_LOG_GLOBAL=false
VITE_LOG_UNHANDLED_REJECTION=false
```

**ワークフロー:**

```bash
# 1. ログクリア
./scripts/clear-error-logs.sh -f

# 2. ブラウザで問題の操作を実行

# 3. リアルタイム監視
tail -f ./logs/errors.log | jq '.'

# 4. Ctrl+C で停止

# 5. ログ分析
./scripts/show-error-logs.sh all
```

### パターン3: 本番環境

**目的:** エラーロギング無効化

**設定:**

```bash
VITE_ENABLE_ERROR_LOGGING=false
```

**理由:**
- パフォーマンスへの影響を最小化
- 不要なログ送信を防止
- セキュリティ（エラー情報の漏洩防止）

---

## 関連リンク

- [フロントエンドエラーロギング実装計画](../design/frontend-logger.md)
- [スクリプト一覧](../../scripts/README.md)
- [Web UI 人間動作確認手順書](humantest.md)

---

**ライセンス**: Apache License 2.0
