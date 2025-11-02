# Reprospective マニュアル

プロジェクトの運用・操作マニュアル集

---

## マニュアル一覧

### 開発・デバッグ

#### [エラーロギング利用マニュアル](error-logging.md)
フロントエンドエラーロギング機能の使い方

**対象読者**: 開発者、デバッグ担当者

**内容:**
- エラーロギングのON/OFF切り替え
- エラーログの確認方法（スクリプト、直接確認、リアルタイム監視）
- エラーログの消去方法
- 細粒度制御（エラーソースごとのON/OFF）
- エラーテストページの使い方
- トラブルシューティング
- よくある使用パターン

**主要コマンド:**
```bash
# エラーログを確認
./scripts/show-error-logs.sh

# エラーログを消去
./scripts/clear-error-logs.sh

# リアルタイム監視
tail -f ./logs/errors.log | jq '.'
```

---

### テスト・品質保証

#### [Web UI 人間動作確認手順書](humantest.md)
Web UIの手動テスト手順

**対象読者**: QA担当者、開発者

**内容:**
- Web UI起動・接続確認
- ディレクトリ管理機能のテスト
- CRUD操作の動作確認
- UIデザインの確認項目
- 発見された問題と修正履歴

**テスト範囲:**
- ディレクトリ追加
- ディレクトリ編集
- ON/OFF切り替え
- ディレクトリ削除
- バリデーション動作
- 楽観的更新

---

### デザイン

#### [Web UI デザインガイド](ui-design-guide.md)
Web UIのデザインシステムとコンポーネント設計

**対象読者**: フロントエンド開発者、デザイナー

**内容:**
- デザインシステム（Tailwind CSS v4、Shadcn/ui）
- カラーパレット（HSL変数システム）
- タイポグラフィ
- レイアウト原則
- コンポーネントカタログ
- アクセシビリティガイドライン
- レスポンシブデザイン
- ダークモード対応（将来実装）

**技術スタック:**
- Tailwind CSS v4.1.16
- Shadcn/ui (New York style)
- React 19.2.0
- TypeScript 5.9.3

---

## マニュアルの使い分け

### 開発中にエラーが発生した場合
→ [エラーロギング利用マニュアル](error-logging.md)

### Web UIの動作確認をしたい場合
→ [Web UI 人間動作確認手順書](humantest.md)

### Web UIのデザイン・スタイルを理解したい場合
→ [Web UI デザインガイド](ui-design-guide.md)

---

## 関連ドキュメント

### 設計ドキュメント

- [フロントエンドエラーロギング実装計画](../design/frontend-logger.md)
- [Phase 2.2 実装計画（Web UI）](../design/phase2_2_implementation_plan.md)
- [Phase 2.1 実装計画（API Gateway）](../design/phase2_1_implementation_plan.md)

### スクリプトドキュメント

- [管理スクリプト一覧](../../scripts/README.md)

---

## ライセンス

Apache License 2.0
