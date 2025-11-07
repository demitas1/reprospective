# リファクタリング提案書: Phase 2.4前の準備作業

**作成日:** 2025-11-04
**対象範囲:** 環境変数管理、テストフレームワーク導入

---

## 概要

Phase 2.4（Web UI活動データ可視化）の実装前に、以下の2つのリファクタリングを検討する。

1. **環境変数管理の改善**: ハードコードされた設定値を.envファイルから読み込むように変更
2. **テストフレームワーク導入**: pytestを導入してテストコードを体系化

---

## 1. 環境変数管理の改善

### 現状分析

#### ✅ 既に.envを使用している箇所
- `docker-compose.yml`: 環境変数を正しく読み込んでいる
- API Gatewayスクリプト (`scripts/api-*.sh`): `${API_GATEWAY_URL:-http://localhost:8800}` でデフォルト値を設定

#### ❌ ハードコードされている箇所

**1. host-agent/config/config.yaml**
```yaml
postgres_url: "postgresql://reprospective_user:change_this_password@localhost:6000/reprospective"
```
→ パスワード、ポート番号がハードコード

**2. host-agent/test_sync.py**
```python
postgres_url = "postgresql://reprospective_user:change_this_password@localhost:6000/reprospective"
```
→ テストコードにパスワードがハードコード

**3. host-agent/collectors/filesystem_watcher_v2.py**
```python
postgres_url = os.getenv('DATABASE_URL', 'postgresql://reprospective_user:change_this_password@localhost:6000/reprospective')
```
→ デフォルト値にパスワードがハードコード（os.getenv使用は正しい）

### 影響範囲

| ファイル | ハードコード内容 | 影響度 | リスク |
|---------|----------------|--------|--------|
| `host-agent/config/config.yaml` | パスワード、ポート | **高** | セキュリティリスク（YAMLがgitにコミット済み） |
| `host-agent/test_sync.py` | パスワード、ポート | 中 | テストコードのみ、実運用に影響なし |
| `host-agent/collectors/filesystem_watcher_v2.py` | パスワード（デフォルト値） | 低 | 既にos.getenv使用、デフォルト値のみの問題 |

### 提案: 実施すべき

**理由:**
1. **セキュリティ**: config.yamlがパスワードを含んでgitにコミットされている
2. **保守性**: ポート番号変更時に複数ファイル修正が必要
3. **環境差異**: 開発・本番で異なる設定を使い分けられない

**優先度: 🔴 高（Phase 2.4前に実施推奨）**

### 実装計画

#### ステップ1: config.yamlの環境変数化（1時間）

**修正前:**
```yaml
database:
  postgres_url: "postgresql://reprospective_user:change_this_password@localhost:6000/reprospective"
```

**修正後:**
```yaml
database:
  postgres_url: "${DATABASE_URL}"  # 環境変数から取得
```

**または、YAMLを廃止してPythonで環境変数を直接読み込む:**
```python
# host-agent/common/config.py (新規作成)
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '6000')
    DB_NAME = os.getenv('DB_NAME', 'reprospective')
    DB_USER = os.getenv('DB_USER', 'reprospective_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'change_this_password')

    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
```

**推奨アプローチ: Pythonで環境変数を直接読み込む**
- YAMLの環境変数展開は複雑
- python-dotenvを使えばシンプル
- 型チェック・バリデーションも可能

#### ステップ2: 依存パッケージ追加（10分）

```txt
# host-agent/requirements.txt
python-dotenv>=1.0.0
```

#### ステップ3: 既存コードの修正（1時間）

**1. linux_x11_monitor.py**
```python
# 修正前
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 修正後
from common.config import Config
config = Config()
```

**2. data_sync.py**
```python
# コンストラクタで環境変数から取得
from common.config import Config

sync_manager = DataSyncManager(
    postgres_url=Config().DATABASE_URL,
    ...
)
```

**3. test_sync.py**
```python
# 修正前
postgres_url = "postgresql://reprospective_user:change_this_password@localhost:6000/reprospective"

# 修正後
from common.config import Config
postgres_url = Config().DATABASE_URL
```

#### ステップ4: .envファイル配置（不要）

**採用アプローチ: Option 3 - python-dotenvで親ディレクトリ自動検索**

`ConfigManager`クラスが`find_dotenv(usecwd=True)`で自動的にプロジェクトルートの`.env`を検索するため、シンボリックリンクやコピーは不要。

**プロジェクトルート/.env** (既に存在)
```env
# 既存の設定に以下を追加
DATABASE_URL=postgresql://reprospective_user:change_this_password@localhost:6000/reprospective
SQLITE_DESKTOP_PATH=data/desktop_activity.db
SQLITE_FILE_EVENTS_PATH=data/file_changes.db
```

**メリット:**
- シンボリックリンク不要
- host-agent/内のどのスクリプトからでも自動検出
- 開発者のセットアップ手順が簡略化

#### ステップ5: ドキュメント更新（30分）

- `host-agent/README.md`: 環境変数設定の説明追加
- `CLAUDE.md`: リファクタリング履歴追加

**総推定工数: 4-6時間**

---

### 詳細な実装計画

#### Phase 1: 基盤整備（1-2時間）

**1.1 python-dotenv導入**
```bash
# host-agent/requirements.txt に追加
python-dotenv>=1.0.0
```

**1.2 `host-agent/common/config.py` 新規作成**

```python
"""
統合設定管理モジュール

環境変数、YAML設定、デフォルト値を統合的に管理する。
python-dotenvで親ディレクトリの.envを自動検索する。
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)

class ConfigManager:
    """設定管理クラス"""

    def __init__(self, config_yaml_path: Optional[str] = None):
        """
        設定を初期化

        Args:
            config_yaml_path: config.yamlのパス（省略時は自動検出）
        """
        # 1. 親ディレクトリから.envを自動検索してロード
        # find_dotenv()は現在のディレクトリから親を遡って.envを検索
        dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path:
            load_dotenv(dotenv_path)
            logger.info(f".envファイルをロード: {dotenv_path}")
        else:
            logger.warning(".envファイルが見つかりません（環境変数のみ使用）")

        # 2. YAML設定をロード（オプション）
        self.yaml_config = self._load_yaml(config_yaml_path)

    def get_postgres_url(self) -> str:
        """PostgreSQL接続URLを取得（環境変数 > YAML > デフォルト）"""
        # 優先順位1: DATABASE_URL環境変数
        if os.getenv('DATABASE_URL'):
            return os.getenv('DATABASE_URL')

        # 優先順位2: 個別環境変数から構築
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '6000')
        db_name = os.getenv('DB_NAME', 'reprospective')
        user = os.getenv('DB_USER', 'reprospective_user')
        password = os.getenv('DB_PASSWORD', 'change_this_password')

        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

    def get_sqlite_desktop_path(self) -> str:
        """デスクトップアクティビティSQLiteパスを取得"""
        path = os.getenv('SQLITE_DESKTOP_PATH', 'data/desktop_activity.db')
        return self._resolve_path(path)

    def get_sqlite_file_events_path(self) -> str:
        """ファイルイベントSQLiteパスを取得"""
        path = os.getenv('SQLITE_FILE_EVENTS_PATH', 'data/file_changes.db')
        return self._resolve_path(path)

    def get_data_sync_config(self) -> Dict[str, Any]:
        """データ同期設定を取得（YAML > デフォルト）"""
        if 'data_sync' in self.yaml_config:
            return self.yaml_config['data_sync']
        return {
            'enabled': True,
            'sync_interval_seconds': 300,
            'batch_size': 100
        }

    def get_desktop_monitor_config(self) -> Dict[str, Any]:
        """デスクトップモニター設定を取得（YAML > デフォルト）"""
        if 'desktop_monitor' in self.yaml_config:
            return self.yaml_config['desktop_monitor']
        return {
            'check_interval': 1.0,
            'idle_threshold': 60
        }

    def get_filesystem_watcher_config(self) -> Dict[str, Any]:
        """ファイルシステムウォッチャー設定を取得（YAML > デフォルト）"""
        if 'filesystem_watcher' in self.yaml_config:
            return self.yaml_config['filesystem_watcher']
        return {
            'monitored_directories': [],
            'excluded_patterns': ['*.tmp', '*.swp', '.git/*']
        }

    def _resolve_path(self, path: str) -> str:
        """相対パスをhost-agent/からの絶対パスに解決"""
        if Path(path).is_absolute():
            return path
        host_agent_dir = Path(__file__).parent.parent
        return str(host_agent_dir / path)

    def _load_yaml(self, config_path: Optional[str]) -> Dict[str, Any]:
        """YAML設定をロード"""
        if not config_path:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        if Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
```

**1.3 環境変数テンプレート更新**

**プロジェクトルート `env.example` に追加:**
```env
# PostgreSQL接続設定（オプション: 完全なURLで指定）
DATABASE_URL=postgresql://reprospective_user:change_this_password@localhost:6000/reprospective

# または個別に指定
DB_HOST=localhost
DB_PORT=6000
DB_NAME=reprospective
DB_USER=reprospective_user
DB_PASSWORD=change_this_password

# SQLiteデータベースパス（host-agent用）
SQLITE_DESKTOP_PATH=data/desktop_activity.db
SQLITE_FILE_EVENTS_PATH=data/file_changes.db
```

**`host-agent/.env.example` 新規作成:**
```env
# host-agent固有の環境変数
# このファイルはプロジェクトルートの.envがある場合は不要です

# PostgreSQL接続設定
DATABASE_URL=postgresql://reprospective_user:change_this_password@localhost:6000/reprospective

# SQLiteデータベースパス
SQLITE_DESKTOP_PATH=data/desktop_activity.db
SQLITE_FILE_EVENTS_PATH=data/file_changes.db
```

#### Phase 2: 既存コード移行（2-3時間）

**2.1 `linux_x11_monitor.py` 修正**

```python
# 修正前
config_path = Path(__file__).parent.parent / "config" / "config.yaml"
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 修正後
from common.config import ConfigManager

config_manager = ConfigManager()
postgres_url = config_manager.get_postgres_url()
desktop_db_path = config_manager.get_sqlite_desktop_path()
monitor_config = config_manager.get_desktop_monitor_config()
```

**2.2 `filesystem_watcher_v2.py` 修正**

```python
# 修正前
postgres_url = os.getenv('DATABASE_URL', 'postgresql://reprospective_user:change_this_password@localhost:6000/reprospective')

# 修正後
from common.config import ConfigManager

config_manager = ConfigManager()
postgres_url = config_manager.get_postgres_url()
```

**2.3 `data_sync.py` 修正**

DataSyncManagerのコンストラクタ呼び出し側で`ConfigManager`を使用:

```python
# 呼び出し側（linux_x11_monitor.py等）
from common.config import ConfigManager

config_manager = ConfigManager()
sync_manager = DataSyncManager(
    postgres_url=config_manager.get_postgres_url(),
    sqlite_desktop_db_path=config_manager.get_sqlite_desktop_path(),
    sqlite_file_events_db_path=config_manager.get_sqlite_file_events_path(),
)
```

**2.4 `test_sync.py` 修正**

```python
# 修正前
postgres_url = "postgresql://reprospective_user:change_this_password@localhost:6000/reprospective"
sqlite_desktop_db_path = "./data/desktop_activity.db"
sqlite_file_events_db_path = "./data/file_changes.db"

# 修正後
from common.config import ConfigManager

config_manager = ConfigManager()
postgres_url = config_manager.get_postgres_url()
sqlite_desktop_db_path = config_manager.get_sqlite_desktop_path()
sqlite_file_events_db_path = config_manager.get_sqlite_file_events_path()
```

#### Phase 3: 設定ファイル更新（30分）

**3.1 `config.yaml` 更新**

```yaml
# データベース設定（環境変数に移行）
database:
  # 非推奨: 以下の設定は環境変数 DATABASE_URL または DB_* で指定してください
  # postgres_url: "postgresql://reprospective_user:change_this_password@localhost:6000/reprospective"

  # SQLiteデータベースパス（環境変数 SQLITE_*PATH で上書き可能）
  sqlite_desktop_db: "data/desktop_activity.db"
  sqlite_file_events_db: "data/file_changes.db"

# その他の設定は引き続きYAMLで管理
desktop_monitor:
  check_interval: 1.0
  idle_threshold: 60

filesystem_watcher:
  excluded_patterns:
    - "*.tmp"
    - "*.swp"
    - ".git/*"
    - "__pycache__/*"

data_sync:
  enabled: true
  sync_interval_seconds: 300
  batch_size: 100
```

**3.2 `scripts/start-agent.sh` 修正**

```bash
#!/bin/bash

# .env存在確認
if [ ! -f .env ]; then
    echo "警告: .envファイルが見つかりません"
    echo "env.exampleをコピーして.envを作成してください:"
    echo "  cp env.example .env"
    echo ""
    read -p "デフォルト設定で続行しますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

cd host-agent
source venv/bin/activate
python collectors/linux_x11_monitor.py
```

#### Phase 4: ドキュメント更新（30分-1時間）

**4.1 `CLAUDE.md` 更新**

実装履歴セクションに追加:
```markdown
### 2025-11-05: Phase 2.3.1 環境変数管理の改善完了

**実装内容:**
- python-dotenv導入、`find_dotenv()`で親ディレクトリ.env自動検索
- `host-agent/common/config.py`新規作成（ConfigManagerクラス）
- 既存コード4ファイル修正（linux_x11_monitor.py, filesystem_watcher_v2.py, test_sync.py, data_sync.py呼び出し側）
- config.yamlのPostgreSQL接続情報をコメントアウト
- 環境変数優先順位: DATABASE_URL > DB_* > デフォルト値

**技術的成果:**
- セキュリティリスク解消（パスワードのハードコード削除）
- 環境ごとの設定切り替え可能
- YAML設定との共存（機密情報は環境変数、その他はYAML）
```

**4.2 `host-agent/README.md` 更新**

セットアップ手順に追加:
```markdown
### 環境変数設定

host-agentは以下の環境変数を使用します。プロジェクトルートの`.env`ファイルが自動的に検索・読み込まれます。

| 環境変数 | 説明 | デフォルト値 |
|---------|------|------------|
| `DATABASE_URL` | PostgreSQL接続URL（完全指定） | - |
| `DB_HOST` | PostgreSQLホスト | `localhost` |
| `DB_PORT` | PostgreSQLポート | `6000` |
| `DB_NAME` | データベース名 | `reprospective` |
| `DB_USER` | データベースユーザー名 | `reprospective_user` |
| `DB_PASSWORD` | データベースパスワード | `change_this_password` |
| `SQLITE_DESKTOP_PATH` | デスクトップアクティビティSQLiteパス | `data/desktop_activity.db` |
| `SQLITE_FILE_EVENTS_PATH` | ファイルイベントSQLiteパス | `data/file_changes.db` |

**優先順位:**
1. `DATABASE_URL`が設定されている場合、それを最優先
2. 設定されていない場合、`DB_HOST`, `DB_PORT`等から構築
3. 環境変数がない場合、デフォルト値を使用

**セットアップ:**
```bash
# プロジェクトルートで.envを作成
cp env.example .env
vim .env  # 必要に応じて編集

# host-agentから.envが自動的に検索される（シンボリックリンク不要）
cd host-agent
python collectors/linux_x11_monitor.py
```
```

---

### 修正対象ファイル一覧

| ファイルパス | 種別 | 修正内容 |
|------------|------|---------|
| `host-agent/common/config.py` | 新規作成 | ConfigManagerクラス実装 |
| `host-agent/.env.example` | 新規作成 | host-agent固有の環境変数テンプレート |
| `host-agent/requirements.txt` | 修正 | python-dotenv追加 |
| `host-agent/collectors/linux_x11_monitor.py` | 修正 | ConfigManager使用に変更 |
| `host-agent/collectors/filesystem_watcher_v2.py` | 修正 | ConfigManager使用に変更 |
| `host-agent/test_sync.py` | 修正 | ConfigManager使用に変更 |
| `host-agent/config/config.yaml` | 修正 | postgres_urlをコメントアウト |
| `env.example` | 修正 | DATABASE_URL, SQLITE_*追加 |
| `scripts/start-agent.sh` | 修正 | .env存在確認追加 |
| `CLAUDE.md` | 修正 | 実装履歴追加 |
| `host-agent/README.md` | 修正 | 環境変数説明追加 |

**総計: 11ファイル（新規2、修正9）**

---

### 環境変数の命名規則

| 環境変数名 | 説明 | デフォルト値 | 用途 |
|-----------|------|------------|------|
| `DATABASE_URL` | PostgreSQL接続URL（完全指定） | - | PostgreSQL接続（最優先） |
| `DB_HOST` | PostgreSQLホスト | `localhost` | PostgreSQL接続 |
| `DB_PORT` | PostgreSQLポート | `6000` | PostgreSQL接続 |
| `DB_NAME` | データベース名 | `reprospective` | PostgreSQL接続 |
| `DB_USER` | データベースユーザー名 | `reprospective_user` | PostgreSQL接続 |
| `DB_PASSWORD` | データベースパスワード | `change_this_password` | PostgreSQL接続 |
| `SQLITE_DESKTOP_PATH` | デスクトップアクティビティSQLiteパス | `data/desktop_activity.db` | ローカルDB |
| `SQLITE_FILE_EVENTS_PATH` | ファイルイベントSQLiteパス | `data/file_changes.db` | ローカルDB |

**優先順位:**
- `DATABASE_URL`が設定されている場合、それを最優先
- 設定されていない場合、`DB_HOST`, `DB_PORT`等から構築
- 環境変数がない場合、デフォルト値を使用

---

### 実装上の注意点

#### 1. YAML設定との共存

**方針:**
- **環境変数**: 機密情報（パスワード）、環境依存情報（ホスト、ポート）
- **YAML**: 監視間隔、除外パターン、その他の設定

**理由:**
- config.yamlには監視間隔、除外パターン等も含まれる
- すべてを環境変数化すると設定が煩雑になる
- 機密情報のみ環境変数化することで、セキュリティと利便性を両立

#### 2. 下位互換性の維持

**対応:**
- `ConfigManager`の優先順位: 環境変数 > YAML > デフォルト値
- 既存の`config.yaml`の`postgres_url`は削除せず、コメントアウト
- 移行ガイドをコメントとして追加
- README.mdとCLAUDE.mdに移行手順を明記

#### 3. テストスクリプトの扱い

**対応:**
- `test_sync.py`も`ConfigManager`を使用
- デフォルト値で動作するようにする（ローカル開発環境のデフォルト値を想定）
- CI/CD環境では環境変数で上書き可能

#### 4. エラーハンドリング

**対応:**
- `ConfigManager`に詳細なログ出力を実装
- `.env`ファイルが見つからない場合は警告を出すが、デフォルト値で続行
- PostgreSQL接続エラー時は設定値を（パスワード以外）ログ出力

#### 5. セキュリティ

**対応:**
- `.gitignore`に`.env`が記載されているか確認
- `env.example`に「.envファイルは絶対にコミットしない」旨の警告コメントを追加
- CLAUDE.mdにも注意事項を記載

#### 6. 環境変数の不一致問題

**現状:**
- `env.example`: `DB_PORT=5432`
- `docker-compose.yml`: `POSTGRES_PORT:-5432`
- host-agent実装: ポート6000を期待

**対応:**
- `env.example`のデフォルト値を`6000`に統一
- docker-compose.ymlは既にポート6000でマッピング済み（`6000:5432`）
- ドキュメントで明記

---

### 実装の推奨順序

1. **Phase 1: 基盤整備**（1-2時間）
   - python-dotenv追加
   - ConfigManager実装
   - 環境変数テンプレート更新

2. **Phase 2: 既存コード移行**（2-3時間）
   - linux_x11_monitor.py修正
   - filesystem_watcher_v2.py修正
   - test_sync.py修正
   - data_sync.py呼び出し側修正

3. **Phase 3: 設定ファイル更新**（30分）
   - config.yaml更新
   - start-agent.sh修正

4. **Phase 4: ドキュメント更新**（30分-1時間）
   - CLAUDE.md更新
   - host-agent/README.md更新

**総推定工数: 4-6時間**

---

## 2. テストフレームワーク導入（pytest）

### 現状分析

#### 現在のテスト状況
- ✅ `host-agent/test_sync.py`: 手動実行スクリプト（asyncio.run使用）
- ❌ テストフレームワーク未導入
- ❌ テストの自動化なし
- ❌ カバレッジ測定なし

#### test_sync.pyの特性
```python
async def test_sync():
    """同期機能をテスト"""
    # テストデータ作成
    # 同期実行
    # 結果確認（目視）

if __name__ == "__main__":
    asyncio.run(test_sync())
```

→ **単体テストではなく、統合テストスクリプト**

### 影響範囲

| 項目 | 現状 | pytest導入後 |
|------|------|--------------|
| テスト実行 | `python test_sync.py` | `pytest` |
| アサーション | なし（目視確認） | `assert`文で自動検証 |
| テスト分離 | 単一関数 | 複数テストケースに分割 |
| CI/CD統合 | 不可 | 可能 |
| カバレッジ | 不明 | 測定可能 |

### 提案: 段階的に実施

**理由:**
1. **Phase 2.4の優先度が高い**: 先にUI実装を進めるべき
2. **テストコード量が少ない**: 現時点では1ファイルのみ
3. **統合テストの性質**: 単体テストより統合テストが重要な段階

**優先度: 🟡 中（Phase 2.4後に実施推奨）**

### 実装計画（Phase 2.4後）

#### ステップ1: pytest導入（30分）

```bash
# host-agent/requirements-dev.txt (新規作成)
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
```

```bash
pip install -r requirements-dev.txt
```

#### ステップ2: テスト構造化（2時間）

**ディレクトリ構成:**
```
host-agent/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest設定・フィクスチャ
│   ├── unit/                    # 単体テスト
│   │   ├── test_database.py
│   │   ├── test_models.py
│   │   └── test_config.py
│   └── integration/             # 統合テスト
│       ├── test_data_sync.py    # test_sync.pyをリファクタ
│       └── test_collectors.py
├── pytest.ini                   # pytest設定ファイル
└── test_sync.py                 # 既存（削除または移行）
```

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

**conftest.py:**
```python
import pytest
from common.config import Config

@pytest.fixture
def config():
    """設定フィクスチャ"""
    return Config()

@pytest.fixture
def test_db_path(tmp_path):
    """テスト用DBパス"""
    return str(tmp_path / "test.db")
```

#### ステップ3: 既存テストのリファクタリング（2時間）

**tests/integration/test_data_sync.py:**
```python
import pytest
from common.data_sync import DataSyncManager
from common.database import DesktopActivityDatabase

@pytest.mark.asyncio
async def test_sync_desktop_sessions(config):
    """デスクトップセッションの同期テスト"""
    sync_manager = DataSyncManager(
        postgres_url=config.DATABASE_URL,
        sqlite_desktop_db_path="./data/desktop_activity.db",
        sqlite_file_events_db_path="./data/file_changes.db",
    )

    await sync_manager.initialize()
    await sync_manager.sync_all()

    # アサーション追加
    assert sync_manager.pool is not None

    await sync_manager.close()

@pytest.mark.asyncio
async def test_sync_with_mock_data(test_db_path):
    """モックデータでの同期テスト"""
    # テストデータ作成
    # 同期実行
    # アサーションで検証
    pass
```

#### ステップ4: CI/CD統合（1時間）

**GitHub Actions設定（.github/workflows/test.yml）:**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd host-agent
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          cd host-agent
          pytest --cov=common --cov=collectors
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

**総推定工数: 5.5時間**

---

## 推奨実施順序

### 🔴 Phase 2.4前に実施（必須）

**1. 環境変数管理の改善（4-6時間）**
- セキュリティリスク（パスワードがgitにコミット済み）
- Phase 2.4でも環境変数を多用するため、先に整備すべき

### 🟡 Phase 2.4後に実施（推奨）

**2. pytest導入（5.5時間）**
- 現時点ではテストコード量が少ない
- Phase 2.4でコード量が増えた後に導入する方が効率的
- UI実装を優先すべき

---

## 実施判断基準

### 環境変数管理の改善

#### 実施すべき理由 ✅
1. **セキュリティ**: config.yamlのパスワードがgitに記録されている
2. **Phase 2.4との関連性**:
   - API Gateway設定（ポート、URL）
   - データベース接続設定
   - 両方とも環境変数化が必要
3. **工数が少ない**: 4-6時間で完了
4. **技術的負債の解消**: 早期対応で後続フェーズに影響しない

#### 実施しない理由（該当なし）
- 特になし

**判断: 🔴 実施推奨（Phase 2.4前）**

---

### pytest導入

#### 実施を遅らせる理由 ✅
1. **Phase 2.4の優先度**: UI実装の方が価値が高い
2. **現在のテストコード量**: 1ファイルのみ、手動テストで十分
3. **統合テストの性質**:
   - 現段階では統合テストが主
   - 単体テストを書くほどロジックが複雑ではない
4. **Phase 2.4後の方が効率的**:
   - API Gatewayのテストも同時に整備できる
   - Web UIのテスト（Jest/Vitest）と合わせて戦略を立てられる

#### 早期実施すべき理由
1. **CI/CD統合**: 自動テストがあればリグレッション検出できる
2. **コード品質**: テストがあれば安心してリファクタリングできる

**判断: 🟡 Phase 2.4後に実施（Phase 2.5の前）**

---

## 最終推奨

### Phase 2.4前のリファクタリング計画

```
┌─────────────────────────────────────────────────┐
│ Phase 2.3.1: 環境変数管理の改善 (4-6時間)      │
├─────────────────────────────────────────────────┤
│ 1. python-dotenv導入                            │
│ 2. common/config.py作成                         │
│ 3. 既存コード修正（4ファイル）                  │
│ 4. ドキュメント更新                             │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Phase 2.4: Web UI活動データ可視化 (20時間)     │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Phase 2.5: pytest導入・テスト体系化 (5.5時間)  │
├─────────────────────────────────────────────────┤
│ 1. pytest導入                                   │
│ 2. テスト構造化                                 │
│ 3. 既存テストのリファクタリング                │
│ 4. CI/CD統合                                    │
└─────────────────────────────────────────────────┘
```

### 実施内容

**✅ 実施する: 環境変数管理の改善**
- Phase 2.4前に実施
- セキュリティリスク解消
- 推定工数: 4-6時間

**⏸️ 延期する: pytest導入**
- Phase 2.4後（Phase 2.5）に実施
- UI実装を優先
- 推定工数: 5.5時間

---

## 参考資料

- [python-dotenv Documentation](https://pypi.org/project/python-dotenv/)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [GitHub Actions for Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)

---

**結論: Phase 2.4前に環境変数管理の改善のみ実施し、pytestは後回しにする。**
