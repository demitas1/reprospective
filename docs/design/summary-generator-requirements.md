# アクティビティサマリー生成機能 要求仕様書

## 関連ドキュメント
- **[要求仕様書](./summary-generator-requirements.md)** ← 本ドキュメント
- [設計書](./summary-generator-design.md)
- [実装計画](./summary-generator-implementation.md)

---

## 概要

日次ログファイル（デスクトップアクティビティセッション、入力アクティビティセッション、ファイル変更イベント）から、LLMを活用して構造化されたアクティビティサマリーを生成する機能。

### 目的

- 手動での日誌作成負担を軽減
- LLMによる自動カテゴライズで客観的な活動分析を提供
- プロジェクト別、カテゴリー別の活動時間を可視化
- 入力アクティビティによる無活動期間除外で、より正確な活動時間を計測
- プライバシー保護（センシティブコンテンツフィルタ、業務秘密匿名化）

### 責任範囲

**対象:**
- ログファイルの解析と前処理
- LLMを用いたアクティビティカテゴライズ
- カテゴリー別アクティビティ抽出
- 実行時間推定と強度ランク付け
- JSON形式でのサマリー出力
- 処理過程のログ記録（開発・チューニング目的）

**対象外:**
- 日誌テキストの生成（別モジュールが担当）
- ログファイルの収集・バックアップ（既存機能）

---

## 機能要求

### 1. ログ前処理

**目的:** 不要情報除外、セッション統合、無活動期間除外による高品質なデータ生成

**データソース:**
1. **デスクトップアクティビティセッション** - アクティブウィンドウの記録
2. **入力アクティビティセッション** - マウス・キーボード入力期間の記録
3. **ファイル変更イベント** - ファイル作成・更新・削除の記録

**要求内容:**

**基本フィルタリング:**
- 短時間セッション除外（10秒未満、設定可能）
- 一時ファイル除外（`.tmp.*`, `.swp`, `.bak`, `.git/`, `node_modules/`等）

**デスクトップアクティビティセッション処理:**
- **無活動期間除外**: 入力アクティビティセッションとの照合により、実際に入力があった期間のみを集計
  - デスクトップセッション中に入力がない期間を除外
  - 例: ウィンドウは3時間開いていたが、実際の入力は1.5時間のみ → 1.5時間として計上
- **セッション統合**: 同一アプリ、60秒以内、コンテキスト類似のセッションを統合
- **精度向上**: 「ウィンドウを開いていただけ」と「実際に作業していた」を区別

**ファイル変更イベント処理:**
- **無活動期間除外は行わない**: ファイル変更は明確な作業の証跡であるため、入力アクティビティとの照合なしにそのまま記録
- **イベント統合**: プロジェクト・ファイル単位で統合

**処理ロジック:**
```
1. デスクトップセッションを時系列順に読み込み
2. 入力アクティビティセッションを時系列順に読み込み
3. 各デスクトップセッションに対して:
   a. 入力アクティビティセッションと時間的に重複する期間を抽出
   b. 重複期間の合計時間を「実活動時間」として計算
   c. 実活動時間が閾値（10秒）未満の場合、セッション除外
4. ファイル変更イベントは無活動期間チェックなしで処理
5. セッション統合（同一アプリ、60秒以内）
```

**除外例:**
| デスクトップセッション | 入力アクティビティ | 処理結果 |
|---------------------|------------------|---------|
| 09:00-12:00 (3時間) Brave | 09:00-09:30 (30分), 11:00-11:15 (15分) | 45分として記録 |
| 14:00-14:30 (30分) VSCode | 14:00-14:25 (25分) | 25分として記録 |
| 15:00-15:05 (5分) Terminal | 入力なし | 除外（5分未満） |

**処理ログ:**
- `logs/YYYY-MM-DD/debug/processing_log.jsonl`（JSON Lines形式）
- セッション統合、除外処理、無活動期間除外の詳細を記録
- 入力アクティビティとの照合結果を記録

---

### 2. アクティビティヒント管理

**目的:** プロジェクト・カテゴリー情報の管理、業務秘密の匿名化

**要求内容:**
- プロジェクト定義（名前、説明、キーワード、パス）
- カテゴリー定義（業務、個人開発、学習、調査、コミュニケーション、ブラウジング、娯楽、その他）
- 業務秘密の匿名化設定（プロジェクト名、パス、説明文の匿名化）
- LLMコンテキスト情報の保持（タイプ、ドメイン、技術スタック、活動タイプ）

**匿名化例:**
```yaml
projects:
  - name: "client_project_kb"
    description: "業務委託先：顧客向けナレッジベース開発"
    anonymize:
      enabled: true
      anonymized_name: "業務プロジェクトA"
      anonymized_description: "顧客向けナレッジベースシステム開発"
      anonymize_paths: true
      anonymized_path_prefix: "/work/client_project_a"
      llm_context:
        type: "work_project"
        domain: "knowledge_management"
        tech_stack: ["python", "fastapi", "postgresql"]
```

**匿名化ログ:**
- `logs/YYYY-MM-DD/debug/anonymization_log.jsonl`
- 匿名化前後の情報を記録（実験目的、アクセス権限600）

---

### 3. センシティブコンテンツフィルタ

**目的:** プライバシー保護、不適切コンテンツの除外・匿名化

**要求内容:**
- パターンマッチング（正規表現、ドメイン、アプリケーション）
- 処理モード：除外（exclude）、匿名化（anonymize）、保持（keep）
- アダルトコンテンツの自動検出と処理

**フィルタリングログ:**
- `logs/YYYY-MM-DD/debug/filtering_log.jsonl`
- フィルタリング結果、統計情報を記録

---

### 4. LLMカテゴライザ

**目的:** LLMによる高精度なアクティビティ分類

**要求内容:**
- **LLMプロバイダ:** OpenAI（必須）、Ollama（オプション）、Anthropic（オプション）
- **モデル選択:**
  - 第一選択肢: GPT-5（`gpt-5`）- $4.26/月
  - 第二選択肢: GPT-5-mini（`gpt-5-mini`）- $0.85/月
  - 第三選択肢: GPT-5-nano（`gpt-5-nano`）- $0.17/月
  - 比較・検証用: GPT-4 Turbo / GPT-4o
- バッチ処理（20セッション/バッチ、設定可能）
- 匿名化対応プロンプト設計
- 信頼度スコア（0.0-1.0）

---

### 5. 集約・ランク付け

**目的:** カテゴリー別活動の集約、実行時間推定、活動強度評価

**要求内容:**
- カテゴリー別合計時間算出
- プロジェクト別合計時間算出
- 活動強度ランク付け（S/A/B/C/D、整数値5/4/3/2/1）
- 時間帯別分布（朝/午後/夕方）
- ファイル活動サマリー

**ランク定義:**
| ランク | 整数値 | 条件 | 説明 |
|--------|--------|------|------|
| S | 5 | 合計時間 >= 3時間 | 主要活動 |
| A | 4 | 1時間 <= 合計時間 < 3時間 | 重要活動 |
| B | 3 | 30分 <= 合計時間 < 1時間 | 中程度の活動 |
| C | 2 | 10分 <= 合計時間 < 30分 | 軽微な活動 |
| D | 1 | 合計時間 < 10分 | ごく短時間の活動 |

---

### 6. JSON出力

**目的:** 構造化されたサマリーデータの生成

**要求内容:**
- PostgreSQLに保存（同一日付は最新のみ保持、UPSERT）
- ファイル出力: `logs/YYYY-MM-DD/activity_summary.json`（バックアップ・デバッグ用）
- メタデータ（合計セッション数、除外数、LLMモデル、処理時間）
- カテゴリー別サマリー（合計時間、ランク、プロジェクト、活動詳細）
- 時間帯別分布
- ファイル活動サマリー
- 洞察（オプション、LLM生成）

---

## 非機能要求

### パフォーマンス

**処理時間目標:**
- 376セッション: 30-60秒以内
- バッチサイズ20: LLM呼び出し回数 = 19回

**コスト目標:**
- GPT-5使用時: $4.26/月（毎日実行）
- GPT-5-mini使用時: $0.85/月（コストパフォーマンス重視）
- GPT-5-nano使用時: $0.17/月（超低コスト、精度要検証）

**最適化手法:**
- 段階的処理（ルールベース分類 → LLM分類）
- バッチ処理（複数セッションを1回のLLM呼び出しで処理）
- プロンプトキャッシング（OpenAI機能活用）

---

### セキュリティ・プライバシー

**データ保護:**
- ローカル処理優先（LLMもローカル実行を推奨）
- クラウドLLM使用時の注意事項：
  - センシティブコンテンツは事前除外
  - 匿名化処理を必須化
  - API通信の暗号化（HTTPS）

**設定ファイルの保護:**
- `activity_hints.yaml`にはプロジェクト情報が含まれる
- アクセス権限を適切に設定（600等）

**出力JSONの取り扱い:**
- 個人情報が含まれる可能性
- バックアップ時の暗号化推奨

**デバッグログの機密性管理:**
- 実験目的のためすべて記録（`LOG_ORIGINAL_CONTENT=true`）
- ログファイルのアクセス権限を 600 に設定
- 一般向けリリース時に対処法を再検討

---

### 可用性・信頼性

**エラーハンドリング:**
- **LLM API呼び出し失敗:**
  - リトライロジック: 最大3回、指数バックオフ（1秒、2秒、4秒）
  - フォールバック不要（リトライ3回失敗後はエラー終了）
- **部分的成功:**
  - エラーとして扱い、結果を破棄（部分的なサマリーは生成しない）
  - 例: 100セッション中50件のみ成功 → エラー終了、サマリー生成せず
- **ログファイル不在:**
  - 空のサマリーを生成（metadata: total_sessions=0）
  - ログファイルが存在しない警告をサマリー内に記録
- **匿名化設定不備:**
  - 警告を出して続行

---

### 拡張性

**将来的な機能追加:**

1. **マルチモーダル対応**
   - スクリーンショット解析
   - 音声アクティビティ記録

2. **パターン学習**
   - ユーザーの分類傾向を学習
   - 自動ヒント生成

3. **リアルタイム分類**
   - ログ収集と同時にカテゴライズ
   - リアルタイムダッシュボード

4. **協調フィルタリング**
   - 複数ユーザーのパターン共有（オプトイン）

---

## ユースケース

### UC-1: オンデマンドサマリー生成

**アクター:** ユーザー

**前提条件:**
- ログファイルが存在する:
  - `logs/YYYY-MM-DD/desktop_activity_sessions.txt` (必須)
  - `logs/YYYY-MM-DD/input_activity_sessions.txt` (推奨、無活動期間除外に使用)
  - `logs/YYYY-MM-DD/file_change_events.txt` (オプション)
- OpenAI API Keyが設定されている

**正常フロー:**
1. ユーザーがWeb UIでサマリー生成ボタンをクリック
2. API Gatewayが `POST /api/v1/summary/generate` を受信
3. タスクIDを発行し、バックグラウンドジョブを起動
4. ログ前処理:
   - デスクトップセッションと入力セッションを照合
   - 無活動期間を除外
   - ファイルイベントを統合
5. ユーザーは `GET /api/v1/summary/status/{task_id}` をポーリングして進捗確認
6. 処理完了後、サマリーをPostgreSQLとファイルに保存
7. ユーザーは `GET /api/v1/summary?date=2025-11-06` でサマリーを取得

**代替フロー:**
- LLM API呼び出し失敗 → リトライ3回後エラー終了
- ログファイル不在 → 空のサマリー生成
- 入力アクティビティログ不在 → 無活動期間除外をスキップ、警告を記録

**事後条件:**
- PostgreSQLに最新サマリーが保存される
- `logs/YYYY-MM-DD/activity_summary.json` にファイル出力される
- 無活動期間除外の統計がメタデータに含まれる

---

### UC-2: CLIによる手動サマリー生成

**アクター:** 開発者

**前提条件:**
- ai-analyzerコンテナが起動している
- ログファイルが存在する:
  - `logs/YYYY-MM-DD/desktop_activity_sessions.txt` (必須)
  - `logs/YYYY-MM-DD/input_activity_sessions.txt` (推奨)
  - `logs/YYYY-MM-DD/file_change_events.txt` (オプション)

**正常フロー:**
1. 開発者がCLIコマンドを実行: `python -m reprospective.summary_generator --date 2025-11-06`
2. ログ前処理:
   - デスクトップセッションと入力セッションを照合
   - 無活動期間を除外（入力ログがある場合）
   - ファイルイベントを統合
3. LLMカテゴライズ → 集約・ランク付け → JSON出力
4. 処理完了後、結果をファイルとPostgreSQLに保存

**代替フロー:**
- `--dry-run` オプション: LLM呼び出しなし、前処理のみ実行
- `--model gpt-5-mini` オプション: コスト削減モデルを使用
- `--no-idle-filter` オプション: 無活動期間除外を無効化（比較・検証用）

**事後条件:**
- サマリーが生成され、保存される
- 処理ログに無活動期間除外の統計が記録される

---

### UC-3: 進捗確認

**アクター:** ユーザー

**前提条件:**
- サマリー生成タスクが実行中

**正常フロー:**
1. ユーザーがポーリングリクエストを送信: `GET /api/v1/summary/status/{task_id}`
2. API Gatewayが進捗情報を返却:
   ```json
   {
     "status": "processing",
     "progress": 0.45,
     "current_batch": 9,
     "total_batches": 19
   }
   ```
3. ユーザーはWeb UIで進捗バーを表示
4. 完了時に `status: "completed"` を受信

**事後条件:**
- ユーザーは処理状況を把握できる

---

## CLI インターフェース

### 基本実行

```bash
# 指定日のサマリー生成
python -m reprospective.summary_generator --date 2025-11-06

# 出力先指定
python -m reprospective.summary_generator --date 2025-11-06 --output /path/to/output.json

# センシティブコンテンツモード指定
python -m reprospective.summary_generator --date 2025-11-06 --sensitive-mode exclude
```

### モデル選択

```bash
# GPT-5（デフォルト）
python -m reprospective.summary_generator --date 2025-11-06 --llm openai --model gpt-5

# GPT-5-mini（コスト削減）
python -m reprospective.summary_generator --date 2025-11-06 --llm openai --model gpt-5-mini

# GPT-5-nano（超低コスト）
python -m reprospective.summary_generator --date 2025-11-06 --llm openai --model gpt-5-nano
```

### 開発・デバッグ

```bash
# ドライラン（LLM呼び出しなし、前処理のみ）
python -m reprospective.summary_generator --date 2025-11-06 --dry-run

# 無活動期間除外を無効化（比較・検証用）
python -m reprospective.summary_generator --date 2025-11-06 --no-idle-filter

# バッチ処理（複数日）
python -m reprospective.summary_generator --start-date 2025-11-01 --end-date 2025-11-06
```

---

## API仕様

### POST /api/v1/summary/generate

**目的:** サマリー生成を開始

**リクエスト:**
```json
{
  "date": "2025-11-06",
  "model": "gpt-5",
  "sensitive_mode": "anonymize"
}
```

**レスポンス:**
```json
{
  "task_id": "abc123",
  "status": "started",
  "message": "サマリー生成を開始しました"
}
```

---

### GET /api/v1/summary/status/{task_id}

**目的:** サマリー生成の進捗確認

**レスポンス（処理中）:**
```json
{
  "status": "processing",
  "progress": 0.45,
  "current_batch": 9,
  "total_batches": 19,
  "message": "LLMカテゴライズ中..."
}
```

**レスポンス（完了）:**
```json
{
  "status": "completed",
  "progress": 1.0,
  "summary_date": "2025-11-06",
  "processing_time_seconds": 45.2
}
```

**レスポンス（エラー）:**
```json
{
  "status": "failed",
  "error": "LLM API呼び出しが3回失敗しました",
  "retries": 3
}
```

---

### GET /api/v1/summary?date=2025-11-06

**目的:** 指定日のサマリー取得

**レスポンス:**
```json
{
  "date": "2025-11-06",
  "generated_at": "2025-11-06T15:00:00+09:00",
  "metadata": { ... },
  "categories": [ ... ],
  "time_distribution": { ... },
  "file_activity_summary": { ... },
  "insights": [ ... ]
}
```

詳細な出力形式は設計書を参照。

---

## 設定ファイル仕様

### config/activity_hints.yaml

プロジェクト、カテゴリー、センシティブコンテンツルールを定義。

```yaml
projects:
  - name: "reprospective"
    description: "AI支援TODO管理システムの個人開発プロジェクト"
    keywords: ["reprospective", "host-agent", "web-ui"]
    category: "personal_development"
    paths:
      - "/home/user/work/github.com/reprospective"

activity_categories:
  - id: "work_project"
    display_name: "業務プロジェクト"
    priority: 1

sensitive_content_rules:
  mode: "exclude"  # "exclude" | "anonymize" | "keep"
  patterns:
    - pattern: "fanza\\.dmm\\.co\\.jp"
      type: "adult"
      action: "exclude"
```

---

### config/summary_generator.yaml

サマリー生成の動作設定。

```yaml
log_processor:
  min_session_duration: 10  # 秒
  session_merge_interval: 60  # 秒
  context_similarity_threshold: 0.7

llm:
  provider: "openai"  # "openai" | "ollama" | "anthropic"
  model: "gpt-5"  # gpt-5, gpt-5-mini, gpt-5-nano, gpt-4-turbo, gpt-4o
  api_key: null  # 環境変数から取得推奨
  temperature: 0.3
  max_tokens: 4000
  batch_size: 20

sensitive_content:
  mode: "anonymize"  # "exclude" | "anonymize" | "keep"
  config_file: "config/activity_hints.yaml"

output:
  format: "json"
  pretty_print: true
  include_insights: true
```

---

## 環境変数

### 必須

- `OPENAI_API_KEY`: OpenAI APIキー（GPT-5使用時）

### オプション

- `LLM_PROVIDER`: `openai` | `ollama` | `anthropic`（デフォルト: `openai`）
- `LLM_MODEL`: `gpt-5` | `gpt-5-mini` | `gpt-5-nano` | `gpt-4-turbo` | `gpt-4o`（デフォルト: `gpt-5`）
- `OLLAMA_HOST`: `http://host.docker.internal:11434`（Ollama使用時）
- `ANTHROPIC_API_KEY`: Anthropic APIキー（Claude使用時）
- `ENABLE_DEBUG_LOGGING`: `true` | `false`（デフォルト: `true`）
- `LOG_ORIGINAL_CONTENT`: `true` | `false`（デフォルト: `true`、実験目的）
- `DATABASE_URL`: PostgreSQL接続URL

---

## 制約事項

### 技術的制約

1. **LLMコンテキスト長制限**
   - バッチサイズを動的調整
   - 長いwindow_titleを省略（先頭100文字）

2. **処理時間**
   - 大量セッション（1000件以上）の場合、処理時間が延長
   - 将来的に正規表現など非LLMアプローチで最適化

3. **カテゴライズの一貫性**
   - プロンプトに過去の分類例を含める（Few-shot learning）

4. **センシティブコンテンツ検出精度**
   - 複数パターンの組み合わせで対応
   - ユーザーフィードバックによるパターン追加

### ビジネス制約

1. **コスト**
   - GPT-5: $4.26/月（毎日実行）
   - 予算超過時はGPT-5-mini（$0.85/月）に切り替え

2. **プライバシー**
   - センシティブコンテンツは除外・匿名化必須
   - デバッグログは実験目的のみ、一般リリース時に再検討

---

## 無活動期間除外の詳細

### 目的

デスクトップアクティビティセッションは「ウィンドウがアクティブだった期間」を記録するため、実際には作業していない時間（読書中、会議中、離席中など）も含まれる可能性があります。入力アクティビティセッション（マウス・キーボード入力記録）と照合することで、より正確な活動時間を計測します。

### 処理アルゴリズム

**時間的重複の計算:**

```python
def calculate_active_time(desktop_session, input_sessions):
    """
    デスクトップセッションと入力セッションの重複期間を計算

    Args:
        desktop_session: デスクトップセッション (start_time, end_time)
        input_sessions: 入力セッションリスト [(start_time, end_time), ...]

    Returns:
        合計活動時間（秒）
    """
    active_time = 0
    for input_session in input_sessions:
        # 重複期間の計算
        overlap_start = max(desktop_session.start_time, input_session.start_time)
        overlap_end = min(desktop_session.end_time, input_session.end_time)

        if overlap_start < overlap_end:
            active_time += (overlap_end - overlap_start)

    return active_time
```

**除外判定:**

```python
# 実活動時間が10秒未満の場合、セッション除外
if active_time < 10:
    exclude_session()
else:
    # 実活動時間でセッションを更新
    session.duration_seconds = active_time
```

### 適用対象

| データタイプ | 無活動期間除外 | 理由 |
|------------|--------------|------|
| デスクトップアクティビティ | ✅ 適用 | ウィンドウがアクティブでも作業していない可能性がある |
| ファイル変更イベント | ❌ 適用しない | ファイル変更は明確な作業の証跡 |
| 入力アクティビティ | N/A | 基準として使用 |

### 統計情報の記録

処理ログおよびサマリーメタデータに以下の情報を記録:

```json
{
  "idle_filtering_stats": {
    "enabled": true,
    "input_sessions_found": true,
    "desktop_sessions_before": 150,
    "desktop_sessions_after": 142,
    "desktop_sessions_excluded": 8,
    "total_time_before_seconds": 21600,
    "total_time_after_seconds": 15300,
    "time_reduction_seconds": 6300,
    "time_reduction_percentage": 29.17
  }
}
```

### 設定オプション

**config.yaml:**
```yaml
summary_generator:
  idle_filtering:
    enabled: true                     # 無活動期間除外を有効化
    min_active_time_seconds: 10       # 最小活動時間（秒）
    fallback_if_no_input_log: true    # 入力ログ不在時の挙動
```

**CLIオプション:**
- `--no-idle-filter`: 無活動期間除外を無効化
- `--min-active-time 15`: 最小活動時間を変更（デフォルト10秒）

### エラーハンドリング

| ケース | 処理 |
|--------|------|
| 入力アクティビティログ不在 | 無活動期間除外をスキップ、警告を記録 |
| 入力ログが破損 | 無活動期間除外をスキップ、エラーを記録 |
| 時刻のずれ（システムクロック不一致） | 警告を記録し、そのまま処理 |

### 期待される効果

**精度向上の例:**

| シナリオ | 除外前 | 除外後 | 改善 |
|---------|-------|-------|------|
| ブラウザで長文記事を読んでいた | 60分 | 5分（スクロール等） | -91.7% |
| VSCodeを開いたまま会議に参加 | 120分 | 0分（入力なし） | -100% |
| 動画を視聴していた | 90分 | 3分（再生・停止操作） | -96.7% |
| コーディング作業 | 45分 | 42分 | -6.7% |

**全体的な効果:**
- 活動時間の精度向上: 推定20-30%の時間削減
- より正確なカテゴリー別時間配分
- 「実際に作業した時間」の可視化

---

## 用語集

| 用語 | 定義 |
|------|------|
| デスクトップアクティビティセッション | アクティブウィンドウの連続記録単位 |
| 入力アクティビティセッション | マウス・キーボード入力が連続している期間の記録 |
| 無活動期間 | デスクトップセッション中、入力がなかった期間 |
| 実活動時間 | デスクトップセッション中、入力があった期間の合計 |
| セッション統合 | 同一アプリ、短時間間隔、類似コンテキストのセッションを1つにまとめる処理 |
| 匿名化 | 業務秘密保護のため、プロジェクト名・パス・説明文を一般的な表現に置換 |
| センシティブコンテンツ | アダルトコンテンツ等、サマリーに含めるべきでない情報 |
| バッチ処理 | 複数セッションを1回のLLM呼び出しでまとめて処理 |
| 活動強度ランク | 合計時間に基づく活動の重要度評価（S/A/B/C/D） |
| プロンプトキャッシング | OpenAIの機能で、同一プロンプトの再利用時にコスト削減 |

---

## 参考資料

- OpenAI API: https://platform.openai.com/docs/
- OpenAI Pricing: https://platform.openai.com/docs/pricing
- Ollama Python SDK: https://github.com/ollama/ollama-python
- Anthropic Claude API: https://docs.anthropic.com/
- 類似プロジェクト: ActivityWatch, RescueTime, Toggl Track
