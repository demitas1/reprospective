# アクティビティサマリー生成機能 設計書

## 関連ドキュメント
- [要求仕様書](./summary-generator-requirements.md)
- **[設計書](./summary-generator-design.md)** ← 本ドキュメント
- [実装計画](./summary-generator-implementation.md)

---

## システムアーキテクチャ

### 全体構成

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  database   │    │ api-gateway │    │   web-ui    │
│ (PostgreSQL)│◄───┤  (FastAPI)  │◄───┤  (React)    │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                           │ (summary JSON配信)
                           │
                    ┌──────▼───────┐
                    │ ai-analyzer  │  ◄── 新規コンテナ
                    │  (Python)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ logs/ (ro)   │
                    │ output/ (rw) │
                    └──────────────┘
```

### ai-analyzer 内部アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    Summary Generator                         │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
      ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
      │   Log     │    │  Activity  │    │ Sensitive │
      │ Processor │    │   Hint     │    │  Content  │
      │           │    │  Manager   │    │  Filter   │
      └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              │
                      ┌───────▼────────┐
                      │  LLM Service   │
                      │  (Categorizer) │
                      └───────┬────────┘
                              │
                      ┌───────▼────────┐
                      │  Aggregator &  │
                      │   Ranker       │
                      └───────┬────────┘
                              │
                      ┌───────▼────────┐
                      │  JSON Output   │
                      └────────────────┘
```

---

## コンポーネント設計

### 1. Log Processor（ログ前処理）

**責任:** ログファイル読み込み、不要情報除外、無活動期間除外、セッション統合

**データソース:**
1. `desktop_activity_sessions.txt` - デスクトップアクティビティセッション（必須）
2. `input_activity_sessions.txt` - 入力アクティビティセッション（推奨）
3. `file_change_events.txt` - ファイル変更イベント（オプション）

**主要機能:**

**基本フィルタリング:**
- 短時間セッション除外（10秒未満）
- 一時ファイル除外（`.tmp.*`, `.swp`, `.bak`, `.git/`, `node_modules/`等）

**無活動期間除外:**
- デスクトップセッションと入力セッションの時間的重複を計算
- 実活動時間（入力があった期間）のみをカウント
- ファイルイベントには適用しない

**セッション統合:**
- 同一アプリ、60秒以内、コンテキスト類似度 > 閾値
- ファイルイベント統合（プロジェクト・ファイル単位）

**無活動期間除外アルゴリズム:**
```python
def filter_idle_periods(desktop_session, input_sessions):
    """
    デスクトップセッションから無活動期間を除外

    Args:
        desktop_session: デスクトップセッション
        input_sessions: 入力セッションリスト

    Returns:
        実活動時間（秒）、または None（除外対象）
    """
    active_time = 0

    for input_session in input_sessions:
        # 時間的重複を計算
        overlap_start = max(desktop_session.start_time, input_session.start_time)
        overlap_end = min(desktop_session.end_time, input_session.end_time)

        if overlap_start < overlap_end:
            active_time += (overlap_end - overlap_start)

    # 実活動時間が10秒未満の場合、セッション除外
    if active_time < 10:
        return None

    return active_time
```

**セッション統合ロジック:**
```python
統合条件:
- application_name が同一
- セッション間隔が 60秒以内
- コンテキスト類似度 > 0.7

コンテキスト類似度判定:
- ターミナル: カレントディレクトリパスの比較
- ブラウザ: ドメイン名の比較
- その他: window_titleの類似度（Levenshtein距離等）
```

**処理フロー:**
```
1. デスクトップセッションを読み込み
2. 入力セッションを読み込み（存在する場合）
3. 各デスクトップセッションに対して:
   a. 入力セッションとの重複期間を計算
   b. 実活動時間を算出
   c. 実活動時間 < 10秒の場合、除外
   d. それ以外の場合、duration_secondsを実活動時間で更新
4. ファイルイベントを読み込み（無活動期間除外なし）
5. セッション統合処理
```

**出力データ構造:**
```python
ProcessedSession = {
    "id": int,
    "start_time": datetime,
    "end_time": datetime,
    "duration_seconds": int,          # 実活動時間（無活動期間除外後）
    "original_duration_seconds": int, # 元の継続時間（比較用）
    "active_time_ratio": float,       # 実活動時間の割合（0.0-1.0）
    "application_name": str,
    "context": str,  # 抽出されたコンテキスト情報
    "original_sessions": [int],  # 元セッションIDリスト
}

ProcessedFileEvent = {
    "project_name": str,
    "file_path": str,
    "event_types": [str],  # ["created", "modified", ...]
    "event_count": int,
    "first_event_time": datetime,
    "last_event_time": datetime,
    "file_extension": str,
}
```

**デバッグログ:**
- `logs/YYYY-MM-DD/debug/processing_log.jsonl`
- セッション統合、除外処理、無活動期間除外の詳細を記録
- ログ例:
```json
{
  "timestamp": "2025-11-06T10:15:30",
  "action": "idle_filter",
  "desktop_session_id": 123,
  "original_duration": 3600,
  "active_duration": 1800,
  "active_ratio": 0.5,
  "input_sessions_matched": 3,
  "result": "filtered"
}
```

---

### 2. Activity Hint Manager（アクティビティヒント管理）

**責任:** プロジェクト・カテゴリー情報管理、匿名化処理

**主要機能:**
- プロジェクトヒント取得（パスからプロジェクトを識別）
- カテゴリー推定（キーワードマッチング）
- プロジェクト情報の匿名化（名前、パス、説明文）
- LLMコンテキスト情報の保持（タイプ、ドメイン、技術スタック）

**匿名化処理:**
```python
匿名化対象:
- プロジェクト名（name → anonymized_name）
- 説明文（description → anonymized_description）
- ファイルパス（paths → anonymized_path_prefix）
- セッション内のwindow_title、context（パス含む場合）

匿名化されない情報（LLM用コンテキスト）:
- カテゴリーID（category）
- プロジェクトタイプ（llm_context.type）
- ドメイン情報（llm_context.domain）
- 技術スタック（llm_context.tech_stack）
- 活動タイプ（llm_context.activity_types）
```

**API:**
```python
class ActivityHintManager:
    def get_project_hint(self, path: str) -> Optional[ProjectHint]:
        """ファイルパスからプロジェクトヒントを取得"""

    def get_category_by_keyword(self, text: str) -> Optional[str]:
        """キーワードからカテゴリーを推定"""

    def get_all_hints_for_llm(self) -> str:
        """LLMプロンプト用のヒント情報を生成（匿名化考慮）"""

    def anonymize_project_data(self, session: ProcessedSession) -> ProcessedSession:
        """プロジェクト情報を匿名化"""
```

**デバッグログ:**
- `logs/YYYY-MM-DD/debug/anonymization_log.jsonl`
- 匿名化前後の情報を記録（実験目的、アクセス権限600）

---

### 3. Sensitive Content Filter（センシティブコンテンツフィルタ）

**責任:** センシティブコンテンツの検出、除外・匿名化処理

**処理モード:**
| モード | 説明 |
|--------|------|
| `exclude` | マッチしたセッションを完全除外 |
| `anonymize` | コンテンツを曖昧な表現に置換 |
| `keep` | フィルタリングしない（ログそのまま保持） |

**処理フロー:**
```python
def filter_session(session: ProcessedSession, rules: SensitiveRules) -> Optional[ProcessedSession]:
    for rule in rules.patterns:
        if rule.matches(session):
            if rule.action == "exclude":
                return None
            elif rule.action == "anonymize":
                session.context = rule.anonymize_to
                session.window_title = "[匿名化済み]"
    return session
```

**デバッグログ:**
- `logs/YYYY-MM-DD/debug/filtering_log.jsonl`
- フィルタリング結果、統計情報を記録

---

### 4. LLM Service（カテゴライザ）

**責任:** LLMを用いたアクティビティカテゴライズ

**LLM選択:**
- OpenAI GPT-5（`gpt-5`）- $4.26/月
- OpenAI GPT-5-mini（`gpt-5-mini`）- $0.85/月
- OpenAI GPT-5-nano（`gpt-5-nano`）- $0.17/月
- GPT-4 Turbo / GPT-4o（比較・検証用）
- Ollama（オプション）
- Anthropic Claude API（オプション）

**プロンプト設計:**
匿名化されたデータでもLLMが正確にカテゴライズできるよう、十分なコンテキスト情報を提供。

```python
CATEGORIZATION_PROMPT = """
あなたはユーザーのデスクトップアクティビティログを分析し、各活動をカテゴライズする専門家です。

# ユーザー定義のプロジェクト情報
{activity_hints}

# プロジェクトコンテキスト情報（匿名化済み）
以下のプロジェクトは業務秘密保護のため匿名化されています。

- プロジェクト名: 業務プロジェクトA
  - タイプ: 業務プロジェクト (work_project)
  - ドメイン: ナレッジ管理システム (knowledge_management)
  - 技術スタック: Python, FastAPI, PostgreSQL
  - パス識別: /work/client_project_a で始まるパス

# 利用可能なカテゴリー
{categories}

# 分析対象のセッション
{sessions}

# 出力形式（JSON）
{{
  "categorized_sessions": [
    {{
      "session_id": 1,
      "category_id": "work_project",
      "project_name": "業務プロジェクトA",
      "activity_description": "プロジェクト設計ドキュメント作成",
      "confidence": 0.95
    }},
    ...
  ]
}}
"""
```

**API:**
```python
class LLMCategorizer:
    def __init__(self, model: str = "gpt-5", api_key: Optional[str] = None):
        self.model = model

    def categorize_sessions(
        self,
        sessions: List[ProcessedSession],
        hints: str,
        categories: List[CategoryDefinition]
    ) -> List[CategorizedSession]:
        """セッションをカテゴライズ"""

    def batch_categorize(
        self,
        sessions: List[ProcessedSession],
        batch_size: int = 20
    ) -> List[CategorizedSession]:
        """バッチ処理でカテゴライズ（大量セッション対応）"""
```

**出力データ構造:**
```python
CategorizedSession = {
    "session_id": int,
    "category_id": str,
    "category_name": str,
    "project_name": Optional[str],
    "activity_description": str,  # LLMが生成した活動説明
    "confidence": float,  # 0.0-1.0
    "start_time": datetime,
    "end_time": datetime,
    "duration_seconds": int,
    "application_name": str,
    "context": str,
}
```

---

### 5. Aggregator & Ranker（集約・ランク付け）

**責任:** カテゴリー別活動の集約、実行時間推定、活動強度のランク付け

**集約処理:**
```python
def aggregate_by_category(sessions: List[CategorizedSession]) -> List[CategorySummary]:
    """カテゴリーごとに活動を集約"""
    summaries = {}
    for session in sessions:
        category_id = session.category_id
        if category_id not in summaries:
            summaries[category_id] = CategorySummary(category_id=category_id)
        summaries[category_id].add_session(session)
    return list(summaries.values())
```

**活動強度ランク付け:**
```python
def calculate_rank(total_seconds: int) -> tuple[str, int]:
    """活動強度ランクを算出"""
    if total_seconds >= 10800:  # 3時間以上
        return ("S", 5)
    elif total_seconds >= 3600:  # 1時間以上
        return ("A", 4)
    elif total_seconds >= 1800:  # 30分以上
        return ("B", 3)
    elif total_seconds >= 600:  # 10分以上
        return ("C", 2)
    else:
        return ("D", 1)
```

---

### 6. JSON Output（JSON出力）

**責任:** 構造化されたサマリーデータの生成・保存

**出力先:**
1. PostgreSQL: `activity_summaries`テーブル（同一日付は最新のみ保持）
2. ファイル: `logs/YYYY-MM-DD/activity_summary.json`

**出力データ構造:**
```json
{
  "date": "2025-11-06",
  "generated_at": "2025-11-06T15:00:00+09:00",
  "metadata": {
    "total_sessions": 376,
    "filtered_sessions": 320,
    "excluded_sessions": 56,
    "total_file_events": 450,
    "llm_model": "gpt-5",
    "processing_time_seconds": 45.2,
    "idle_filtering_stats": {
      "enabled": true,
      "input_sessions_found": true,
      "desktop_sessions_before": 376,
      "desktop_sessions_after": 320,
      "desktop_sessions_excluded": 56,
      "total_time_before_seconds": 21600,
      "total_time_after_seconds": 15300,
      "time_reduction_seconds": 6300,
      "time_reduction_percentage": 29.17
    }
  },
  "categories": [
    {
      "category_id": "work_project",
      "category_name": "業務プロジェクト",
      "total_duration_seconds": 14400,
      "total_duration_formatted": "4時間0分",
      "intensity_rank": "S",
      "intensity_rank_value": 5,
      "concentration_score": 0.85,
      "session_count": 45,
      "projects": [
        {
          "project_name": "業務プロジェクトA",
          "description": "顧客向けナレッジベースシステム開発",
          "is_anonymized": true,
          "total_duration_seconds": 14400,
          "activities": [
            {
              "activity_description": "設計ドキュメント作成",
              "duration_seconds": 3600,
              "start_time": "2025-11-06T11:28:58+09:00",
              "end_time": "2025-11-06T12:28:58+09:00",
              "sessions": [47, 48, 49]
            }
          ],
          "file_changes": {
            "created": 5,
            "modified": 15,
            "deleted": 10
          }
        }
      ]
    }
  ],
  "time_distribution": {
    "morning": {
      "time_range": "07:00-12:00",
      "total_seconds": 10800,
      "top_categories": ["personal_development", "learning"]
    },
    "afternoon": {
      "time_range": "12:00-18:00",
      "total_seconds": 18000,
      "top_categories": ["work_project", "browsing"]
    }
  },
  "file_activity_summary": {
    "projects": [
      {
        "project_name": "foam-test",
        "total_events": 33,
        "files_modified": 1,
        "most_edited_file": "todo/mission.md"
      }
    ]
  },
  "insights": [
    "業務プロジェクト（業務プロジェクトA）に4時間集中して取り組んだ（強度S）",
    "個人開発（reprospective）に1時間30分取り組んだ（強度A）"
  ]
}
```

---

## データフロー

```
1. ログファイル読み込み
   - desktop_activity_sessions.txt
   - input_activity_sessions.txt
   - file_change_events.txt
   ↓
2. Log Processor
   - 基本フィルタリング（短時間セッション除外）
   - 無活動期間除外（入力セッションとの照合）
   - セッション統合
   ↓
3. Activity Hint Manager
   - プロジェクト識別
   - 匿名化処理
   ↓
4. Sensitive Content Filter
   - センシティブコンテンツ検出
   - 除外・匿名化
   ↓
5. LLM Service
   - バッチ処理でカテゴライズ
   - 活動説明生成
   ↓
6. Aggregator & Ranker
   - カテゴリー別集約
   - ランク付け
   ↓
7. JSON Output
   - PostgreSQL保存
   - ファイル出力
```

---

## データベース設計

### activity_summaries テーブル

```sql
CREATE TABLE activity_summaries (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,  -- 同一日付は1件のみ（UPSERT）
    summary_json JSONB NOT NULL,
    llm_model VARCHAR(50) NOT NULL,
    processing_time_seconds FLOAT,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_activity_summaries_date ON activity_summaries(date);
CREATE INDEX idx_activity_summaries_generated_at ON activity_summaries(generated_at);
```

---

## 技術スタック

| コンポーネント | 技術 |
|----------------|------|
| コンテナ | Docker, Docker Compose |
| 言語 | Python 3.11+ |
| LLM連携 | OpenAI Python SDK（必須）, Ollama Python SDK（オプション）, Anthropic SDK（オプション） |
| 設定管理 | PyYAML |
| 日時処理 | python-dateutil |
| JSON処理 | Python標準json |
| ログ解析 | pandas（オプション） |
| タスクキュー | Celery + Redis（オプション、バックグラウンドジョブ用） |

---

## 既知の課題と対応

### 課題1: LLMのコンテキスト長制限

**対応:**
- バッチサイズの動的調整
- 長いwindow_titleの省略（先頭100文字）

### 課題2: カテゴライズの一貫性

**対応:**
- プロンプトに過去の分類例を含める
- Few-shot learning

### 課題3: センシティブコンテンツの検出精度

**対応:**
- 複数パターンの組み合わせ
- ユーザーフィードバックによるパターン追加

---

## 設定ファイル詳細

### config/activity_hints.yaml

```yaml
projects:
  - name: "reprospective"
    description: "AI支援TODO管理システムの個人開発プロジェクト"
    keywords: ["reprospective", "host-agent", "web-ui"]
    category: "personal_development"
    paths:
      - "/home/user/work/github.com/reprospective"

  - name: "client_project_kb"
    description: "業務委託先：顧客向けナレッジベース開発"
    keywords: ["client_kb", "knowledge_base"]
    category: "work_project"
    paths:
      - "/home/user/work/ClientCompany/client_kb_project"
    # 匿名化設定（業務秘密保護）
    anonymize:
      enabled: true
      anonymized_name: "業務プロジェクトA"
      anonymized_description: "顧客向けナレッジベースシステム開発"
      anonymize_paths: true
      anonymized_path_prefix: "/work/client_project_a"
      # LLMへのコンテキスト情報（カテゴライズ用）
      llm_context:
        type: "work_project"
        domain: "knowledge_management"
        tech_stack: ["python", "fastapi", "postgresql"]
        activity_types: ["development", "documentation", "testing"]

activity_categories:
  - id: "work_project"
    display_name: "業務プロジェクト"
    priority: 1

  - id: "personal_development"
    display_name: "個人開発"
    priority: 2

  - id: "learning"
    display_name: "学習"
    priority: 3
    keywords: ["duolingo", "udemy", "qiita", "documentation"]

  - id: "research"
    display_name: "調査・情報収集"
    priority: 4
    keywords: ["duckduckgo", "google search", "wikipedia", "qiita"]

  - id: "communication"
    display_name: "コミュニケーション"
    priority: 5
    keywords: ["slack", "mail", "discord"]

  - id: "browsing"
    display_name: "ブラウジング"
    priority: 6
    keywords: ["youtube", "news", "inoreader"]

  - id: "entertainment"
    display_name: "娯楽"
    priority: 7
    keywords: ["game", "video", "streaming"]

  - id: "other"
    display_name: "その他"
    priority: 99

sensitive_content_rules:
  mode: "exclude"  # "exclude" | "anonymize" | "keep"

  patterns:
    - pattern: "fanza\\.dmm\\.co\\.jp"
      type: "adult"
      action: "exclude"

    - pattern: ".*エロ.*|.*セクシー.*|.*adult.*"
      type: "adult"
      action: "anonymize"
      anonymize_to: "アダルトコンテンツ閲覧"

  domains:
    - domain: "*.dmm.co.jp"
      if_path_contains: ["/digital/videoa/", "/mono/dvd/"]
      action: "exclude"

  applications:
    - application_name: "Brave-browser"
      window_title_pattern: ".*Incognito.*"
      action: "exclude"
```

### config/summary_generator.yaml

```yaml
log_processor:
  min_session_duration: 10  # 秒
  session_merge_interval: 60  # 秒
  context_similarity_threshold: 0.7

  # 無活動期間除外設定
  idle_filtering:
    enabled: true                     # 無活動期間除外を有効化
    min_active_time_seconds: 10       # 最小活動時間（秒）
    fallback_if_no_input_log: true    # 入力ログ不在時は除外をスキップ

  exclude_patterns:
    files:
      - "*.tmp.*"
      - "*.swp"
      - "*.bak"
      - ".git/"
      - "node_modules/"
      - "__pycache__/"

  enable_debug_logging: true  # 開発時true、本番false
  debug_log_file: "logs/{date}/debug/processing_log.jsonl"

llm:
  provider: "openai"  # "openai" | "ollama" | "anthropic"
  model: "gpt-5"  # gpt-5, gpt-5-mini, gpt-5-nano, gpt-4-turbo, gpt-4o
  api_key: null  # 環境変数から取得推奨
  temperature: 0.3
  max_tokens: 4000
  batch_size: 20  # バッチ処理のセッション数

sensitive_content:
  mode: "anonymize"  # "exclude" | "anonymize" | "keep"
  config_file: "config/activity_hints.yaml"
  enable_debug_logging: true
  debug_log_file: "logs/{date}/debug/filtering_log.jsonl"

activity_hint:
  enable_debug_logging: true
  debug_log_file: "logs/{date}/debug/anonymization_log.jsonl"

output:
  format: "json"
  pretty_print: true
  include_insights: true  # LLMによる洞察を含める
```
