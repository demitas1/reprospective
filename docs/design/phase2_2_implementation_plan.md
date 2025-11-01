# Phase 2.2 実装計画: Web UI

**ステータス: ✅ 完了（人間動作確認済み）**

**更新日:** 2025-11-01

**人間動作確認:** 2025-11-01 完了

**前提条件:** Phase 2.1 (API Gateway & host-agent設定同期) 完了 ✅

---

## 概要

Phase 2.2では、監視ディレクトリ設定のためのWebフロントエンドを実装します。Phase 2.1で構築したAPI Gatewayに接続し、ユーザーフレンドリーなUIを提供します。

### 実装目標

- **監視ディレクトリ設定UI**: ブラウザベースの直感的な設定インターフェース
- **リアルタイム更新**: 設定変更の即座の反映とフィードバック
- **モダンUI**: React 19 + Viteによる高速で使いやすいインターフェース
- **レスポンシブデザイン**: デスクトップ/モバイル両対応

### 対象範囲

- Web UI基盤構築（React 19 + Vite）
- ディレクトリ管理画面実装
- API連携とリアルタイム更新
- Docker統合とデプロイメント

### 対象外（将来実装）

- 活動データ可視化（Phase 3）
- AI分析結果表示（Phase 3）
- ユーザー認証・認可（Phase 3）
- マルチホスト管理（Phase 3）

---

## アーキテクチャ

### 技術スタック

**フロントエンド:**
- **フレームワーク**: React 19.2.0（最新版、実験的使用）
- **ビルドツール**: Vite 6.x
- **言語**: TypeScript 5.x
- **UIライブラリ**:
  - Tailwind CSS（スタイリング）
  - Shadcn/ui（コンポーネント）
- **状態管理**: React Query (TanStack Query v5)
- **HTTPクライアント**: Axios
- **フォーム管理**: React Hook Form + Zod

**インフラ:**
- **Webサーバー**: Vite Dev Server（開発・本番共通）
  - **注意:** 実験プロジェクトのため、Nginxは使用せず簡素化
- **コンテナ化**: Docker
- **オーケストレーション**: Docker Compose

### システム構成

```
┌──────────────┐      HTTP      ┌──────────────┐
│   Browser    │ ─────────────> │   Web UI     │
│              │                 │ (React/Vite) │
└──────────────┘                 └──────┬───────┘
                                        │
                                        │ REST API
                                        ▼
                                 ┌──────────────┐
                                 │ API Gateway  │
                                 │  (FastAPI)   │
                                 └──────┬───────┘
                                        │
                                        │ SQL
                                        ▼
                                 ┌──────────────┐
                                 │  PostgreSQL  │
                                 └──────────────┘
```

### ディレクトリ構成

```
services/web-ui/
├── Dockerfile                        # ✅ Vite Dev Server用Dockerfile
├── .dockerignore                     # ✅ Docker除外設定
├── package.json                      # ✅ 依存パッケージ定義
├── tsconfig.json                     # ✅ TypeScript設定
├── tsconfig.app.json                 # ✅ アプリケーション用TypeScript設定（パスエイリアス含む）
├── vite.config.ts                    # ✅ Vite設定（パスエイリアス解決）
├── tailwind.config.js                # ✅ Tailwind CSS v4設定
├── postcss.config.js                 # ✅ PostCSS設定
├── components.json                   # ✅ Shadcn/ui設定
├── env.example                       # ✅ 環境変数テンプレート
├── index.html                        # ✅ エントリーHTML
├── public/
│   └── vite.svg                      # ✅ Viteロゴ
├── src/
│   ├── main.tsx                      # ✅ エントリーポイント
│   ├── App.tsx                       # ✅ ルートコンポーネント
│   ├── App.css                       # ✅ アプリケーションスタイル
│   ├── index.css                     # ✅ Tailwind CSS v4インポート（@import "tailwindcss"）
│   ├── api/                          # ✅ ディレクトリ作成済み
│   │   ├── client.ts                 # 📋 TODO: Axios設定
│   │   └── directories.ts            # 📋 TODO: ディレクトリAPI
│   ├── components/                   # ✅ ディレクトリ作成済み
│   │   ├── ui/                       # ✅ ディレクトリ作成済み（Shadcn/ui用）
│   │   ├── layout/                   # ✅ ディレクトリ作成済み
│   │   ├── directories/              # ✅ ディレクトリ作成済み
│   │   └── common/                   # ✅ ディレクトリ作成済み
│   ├── hooks/                        # ✅ ディレクトリ作成済み
│   │   ├── useDirectories.ts         # 📋 TODO: ディレクトリ取得
│   │   ├── useAddDirectory.ts        # 📋 TODO: ディレクトリ追加
│   │   ├── useUpdateDirectory.ts     # 📋 TODO: ディレクトリ更新
│   │   ├── useDeleteDirectory.ts     # 📋 TODO: ディレクトリ削除
│   │   └── useToggleDirectory.ts     # 📋 TODO: 有効/無効切り替え
│   ├── types/                        # ✅ ディレクトリ作成済み
│   │   └── directory.ts              # 📋 TODO: 型定義
│   ├── lib/                          # ✅ ディレクトリ作成済み
│   │   ├── utils.ts                  # ✅ cn()ユーティリティ実装済み
│   │   └── validators.ts             # 📋 TODO: Zodバリデーションスキーマ
│   └── assets/
│       └── react.svg                 # ✅ Reactロゴ
└── README.md                         # 📋 TODO: ドキュメント作成
```

---

## 主要機能設計

### 1. ディレクトリ管理画面

**画面レイアウト:**

```
┌────────────────────────────────────────────────────────────┐
│ Reprospective - ファイルシステム監視設定                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ 監視対象ディレクトリ                    [+ 新規追加]      │
│                                                            │
│ ┌────────────────────────────────────────────────────┐    │
│ │ 📁 /home/user/projects                   [ON]  [⋮] │    │
│ │ プロジェクト                                        │    │
│ │ 開発プロジェクト用                                  │    │
│ │ 最終更新: 2025-10-31 16:00                         │    │
│ └────────────────────────────────────────────────────┘    │
│                                                            │
│ ┌────────────────────────────────────────────────────┐    │
│ │ 📁 /home/user/Documents                 [OFF] [⋮] │    │
│ │ ドキュメント                                        │    │
│ │ 一時的に無効化中                                    │    │
│ │ 最終更新: 2025-10-30 12:00                         │    │
│ └────────────────────────────────────────────────────┘    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**主要機能:**
- ディレクトリ一覧表示（カード形式）
- ON/OFFトグルスイッチ（即座に反映）
- 新規追加ボタン→ダイアログ表示
- 編集・削除（カードメニュー）
- リアルタイム更新（30秒ごとに自動リフレッシュ）

### 2. ディレクトリ追加ダイアログ

**フォーム項目:**
- **ディレクトリパス** (必須): 絶対パス、自動補完検討
- **表示名** (任意): デフォルト=ディレクトリ名
- **説明** (任意): 用途・目的

**バリデーション（Zod + React Hook Form）:**
- ✅ 空文字チェック
- ✅ 絶対パスチェック（`/`で始まる）
- ✅ 相対パス禁止（`..`を含まない）
- ✅ 末尾空白文字チェック
- ✅ 表示名最大100文字
- ✅ 説明最大500文字
- ✅ リアルタイムバリデーション（入力中にエラー表示）

**Note:** ディレクトリの実在確認はブラウザからは実施不可。host-agent側で自動確認されます。

### 3. ディレクトリ編集ダイアログ

追加ダイアログと同様のフォーム、初期値設定済み。

### 4. 削除確認ダイアログ

- ディレクトリパスと表示名を表示
- 確認メッセージ
- キャンセル/削除ボタン

---

## データフロー

### 1. 一覧取得

```
User → DirectoryList → useDirectories
  → API GET /api/v1/directories/
  → React Query キャッシュ更新
  → DirectoryCard[] 表示
```

**自動更新:**
- 30秒ごとに `refetchInterval` で自動取得
- 更新があれば即座にUI反映

### 2. ディレクトリ追加

```
User → AddDirectoryDialog → useAddDirectory
  → API POST /api/v1/directories/
  → 成功 → React Query キャッシュ無効化
  → 一覧再取得 → UI更新
```

### 3. ON/OFF切り替え

```
User → Switch → useToggleDirectory
  → API PATCH /api/v1/directories/{id}/toggle
  → 楽観的更新（即座にUI反映）
  → 成功 → キャッシュ更新
  → 失敗 → ロールバック + エラー表示
```

### 4. 削除

```
User → DeleteDialog → useDeleteDirectory
  → API DELETE /api/v1/directories/{id}
  → 成功 → キャッシュ無効化 → 一覧再取得
```

---

## 技術実装詳細

### React Query カスタムフック

**useDirectories.ts:**

```typescript
import { useQuery } from '@tanstack/react-query';
import { fetchDirectories } from '@/api/directories';

export const useDirectories = (enabledOnly: boolean = false) => {
  return useQuery({
    queryKey: ['directories', enabledOnly],
    queryFn: () => fetchDirectories(enabledOnly),
    refetchInterval: 30000, // 30秒ごと
    staleTime: 10000,       // 10秒間は新鮮とみなす
  });
};
```

**useAddDirectory.ts:**

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { addDirectory } from '@/api/directories';
import type { DirectoryCreate } from '@/types/directory';

export const useAddDirectory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: DirectoryCreate) => addDirectory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['directories'] });
    },
  });
};
```

**useToggleDirectory.ts:**

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toggleDirectory } from '@/api/directories';
import type { Directory } from '@/types/directory';

export const useToggleDirectory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => toggleDirectory(id),
    // 楽観的更新
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ['directories'] });
      const previous = queryClient.getQueryData<Directory[]>(['directories']);

      queryClient.setQueryData<Directory[]>(['directories'], (old) =>
        old?.map((dir) =>
          dir.id === id ? { ...dir, enabled: !dir.enabled } : dir  // is_enabled → enabled
        )
      );

      return { previous };
    },
    onError: (err, id, context) => {
      // ロールバック
      if (context?.previous) {
        queryClient.setQueryData(['directories'], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['directories'] });
    },
  });
};
```

### API クライアント

**api/client.ts:**

```typescript
import axios from 'axios';

// 環境変数からAPI URLを取得（デフォルトはlocalhost:8800）
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8800';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// レスポンスインターセプター（エラーハンドリング）
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // APIエラーレスポンス
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      // ネットワークエラー
      console.error('Network Error:', error.message);
    } else {
      // その他のエラー
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);
```

**環境変数設定:**

プロジェクトルートの `env.example` から必要な設定をコピーして使用します。

```bash
# services/web-ui/.env
# env.exampleの以下の設定を使用
VITE_API_URL=http://localhost:${API_GATEWAY_PORT:-8800}
```

**注意:**
- ローカル開発環境では `API_GATEWAY_PORT=8800` がデフォルト
- すべての通信はローカルホスト内で完結するため、CORS設定は不要

**api/directories.ts:**

```typescript
import { apiClient } from './client';
import type { Directory, DirectoryCreate, DirectoryUpdate } from '@/types/directory';

export const fetchDirectories = async (enabledOnly: boolean = false): Promise<Directory[]> => {
  const params = enabledOnly ? { enabled_only: true } : {};
  const response = await apiClient.get('/api/v1/directories/', { params });
  return response.data;
};

export const fetchDirectory = async (id: number): Promise<Directory> => {
  const response = await apiClient.get(`/api/v1/directories/${id}`);
  return response.data;
};

export const addDirectory = async (data: DirectoryCreate): Promise<Directory> => {
  const response = await apiClient.post('/api/v1/directories/', data);
  return response.data;
};

export const updateDirectory = async (id: number, data: DirectoryUpdate): Promise<Directory> => {
  const response = await apiClient.put(`/api/v1/directories/${id}`, data);
  return response.data;
};

export const deleteDirectory = async (id: number): Promise<void> => {
  await apiClient.delete(`/api/v1/directories/${id}`);
};

export const toggleDirectory = async (id: number): Promise<Directory> => {
  const response = await apiClient.patch(`/api/v1/directories/${id}/toggle`);
  return response.data;
};
```

### バリデーション

**ディレクトリパスの検証戦略（3層バリデーション）:**

本プロジェクトでは、以下の3層でディレクトリパスを検証します：

#### 1. フロントエンド（React Hook Form + Zod）

**目的:** ユーザーに即座にフィードバック、基本的な形式チェック

**実装場所:** `src/lib/validators.ts`

```typescript
import { z } from 'zod';

export const directoryPathSchema = z
  .string()
  .min(1, 'ディレクトリパスを入力してください')
  .refine(
    (path) => path.startsWith('/'),
    '絶対パスで入力してください（/で始まる必要があります）'
  )
  .refine(
    (path) => !path.includes('..'),
    '相対パス表記（..）は使用できません'
  )
  .refine(
    (path) => !/\s+$/.test(path),
    'パスの末尾に空白文字を含めることはできません'
  );

export const directoryFormSchema = z.object({
  directory_path: directoryPathSchema,
  display_name: z.string().max(100, '表示名は100文字以内で入力してください').optional(),
  description: z.string().max(500, '説明は500文字以内で入力してください').optional(),
});

export type DirectoryFormData = z.infer<typeof directoryFormSchema>;
```

**チェック内容:**
- ✅ 空文字チェック
- ✅ 絶対パスチェック（`/` で始まる）
- ✅ 相対パス禁止（`..` を含まない）
- ✅ 末尾空白文字チェック

**制限事項:**
- ❌ ブラウザからローカルファイルシステムにアクセスできないため、実在確認は不可能

#### 2. バックエンド（FastAPI Pydantic）

**目的:** セキュリティ、API単体での正しい動作保証

**実装場所:** `services/api-gateway/app/models/monitored_directory.py` （既存実装）

```python
@field_validator("directory_path")
@classmethod
def validate_directory_path(cls, v: str) -> str:
    """ディレクトリパスのバリデーション"""
    if not v:
        raise ValueError("ディレクトリパスは必須です")

    # 絶対パスチェック
    if not os.path.isabs(v):
        raise ValueError("絶対パスで指定してください")

    # パス正規化
    normalized = os.path.normpath(v)

    return normalized
```

**チェック内容:**
- ✅ 空文字チェック
- ✅ 絶対パスチェック（`os.path.isabs`）
- ✅ パス正規化（`//`, `./` などを整理）
- ✅ 重複チェック（PostgreSQL UNIQUE制約）

**制限事項:**
- ❌ API Gatewayコンテナ内のファイルシステムとhost-agentのファイルシステムが異なるため、実在確認は実施しない

#### 3. host-agent（config_sync）

**目的:** 実際のファイルシステムでの実在確認

**実装場所:** `host-agent/common/config_sync.py` の `get_monitored_directories()` メソッド

```python
async def get_monitored_directories(self) -> List[MonitoredDirectory]:
    """有効な監視対象ディレクトリをPostgreSQLから取得"""
    if not self._is_connected or not self._pool:
        raise Exception("PostgreSQLに接続されていません")

    try:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, directory_path, enabled, display_name, description
                FROM monitored_directories
                WHERE enabled = true
                ORDER BY id
                """
            )

            directories = []
            for row in rows:
                dir_path = row["directory_path"]

                # 実在確認（host-agent側で実施）
                if not os.path.exists(dir_path):
                    logger.warning(f"ディレクトリが存在しません（スキップ）: {dir_path}")
                    continue

                if not os.path.isdir(dir_path):
                    logger.warning(f"パスがディレクトリではありません（スキップ）: {dir_path}")
                    continue

                directories.append(
                    MonitoredDirectory(
                        id=row["id"],
                        directory_path=dir_path,
                        enabled=row["enabled"],
                        display_name=row["display_name"],
                        description=row["description"],
                    )
                )

            logger.debug(f"PostgreSQLから{len(directories)}件の有効なディレクトリを取得")
            return directories

    except Exception as e:
        logger.error(f"ディレクトリ取得エラー: {e}")
        raise
```

**チェック内容:**
- ✅ ディレクトリの実在確認（`os.path.exists`）
- ✅ ディレクトリ種別確認（`os.path.isdir`）
- ✅ 存在しないディレクトリは自動的に監視対象から除外
- ✅ 警告ログ記録

**UX設計:**

```
ユーザー入力
  ↓
[フロントエンド] 形式チェック → エラー: 即座に表示（赤文字、ツールチップ）
  ↓
[バックエンド] 形式チェック・重複チェック → エラー: API エラーレスポンス（トースト通知）
  ↓
登録成功（PostgreSQL保存）
  ↓
[host-agent] 実在確認（60秒以内） → 存在しない場合: 警告ログ、監視スキップ
  ↓
監視開始（存在するディレクトリのみ）
```

---

### 型定義

**types/directory.ts:**

**重要:** 型定義はバックエンドAPI (`services/api-gateway/app/models/monitored_directory.py`) のレスポンスと完全に一致させる必要があります。

```typescript
/**
 * 監視対象ディレクトリ（APIレスポンス型）
 *
 * バックエンドのMonitoredDirectoryモデルに対応
 */
export interface Directory {
  id: number;
  directory_path: string;          // バックエンドと一致（path ではない）
  enabled: boolean;                // バックエンドと一致（is_enabled ではない）
  display_name: string | null;
  description: string | null;
  created_at: string;              // ISO 8601形式の日時文字列
  updated_at: string;              // ISO 8601形式の日時文字列
  created_by: string;
  updated_by: string;
}

/**
 * 監視対象ディレクトリ作成用（POST /api/v1/directories/）
 *
 * バックエンドのMonitoredDirectoryCreateモデルに対応
 */
export interface DirectoryCreate {
  directory_path: string;          // 必須: 絶対パス
  enabled?: boolean;               // オプション: デフォルトtrue
  display_name?: string;           // オプション: 表示名（最大100文字）
  description?: string;            // オプション: 説明（最大500文字）
  created_by?: string;             // オプション: デフォルト"api"
}

/**
 * 監視対象ディレクトリ更新用（PUT /api/v1/directories/{id}）
 *
 * バックエンドのMonitoredDirectoryUpdateモデルに対応
 * すべてのフィールドがオプション（部分更新対応）
 */
export interface DirectoryUpdate {
  directory_path?: string;         // オプション: 絶対パス
  enabled?: boolean;               // オプション: 有効/無効
  display_name?: string;           // オプション: 表示名（最大100文字）
  description?: string;            // オプション: 説明（最大500文字）
  updated_by?: string;             // オプション: デフォルト"api"
}
```

**型定義の整合性チェックリスト:**

- ✅ `directory_path`: バックエンドと一致（`path`ではない）
- ✅ `enabled`: バックエンドと一致（`is_enabled`ではない）
- ✅ `created_by`, `updated_by`: バックエンドに存在
- ✅ ISO 8601形式の日時文字列（`created_at`, `updated_at`）

---

## Docker統合（✅ 完了）

### ✅ Dockerfile（Vite Dev Server版）

**技術的決定:** 実験プロジェクトのため、Nginxは使用せずVite Dev Serverのみで運用します。

```dockerfile
# Web UIコンテナ（Vite Dev Server）
# 実験プロジェクトのため本番環境でもViteの開発サーバーを使用

FROM node:20-alpine

WORKDIR /app

# 依存パッケージのインストール
COPY package.json package-lock.json ./
RUN npm ci

# ソースコードのコピー
COPY . .

# Viteの開発サーバーポートを公開
EXPOSE 5173

# 開発サーバーを起動（--host 0.0.0.0でコンテナ外からのアクセスを許可）
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**選択理由:**
- ✅ 実装の簡素化（プロジェクトの主目的）
- ✅ ホットリロード機能をそのまま使用可能
- ✅ ローカル環境のみでの使用（外部公開なし）
- ✅ Nginx設定・管理の複雑さを回避

### ✅ .dockerignore

```
# Node.js関連
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# ビルド成果物
dist/
dist-ssr/
*.local

# エディタディレクトリとファイル
.vscode/
.idea/
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# 環境変数ファイル
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# テスト関連
coverage/
.nyc_output/

# その他
*.log
.git/
.gitignore
README.md
```

### ✅ docker-compose.yml 統合

```yaml
services:
  # Web UI (React + Vite)
  web-ui:
    build: ./services/web-ui
    container_name: reprospective-web
    restart: unless-stopped

    environment:
      # API Gateway URL（コンテナ内からはサービス名でアクセス）
      VITE_API_URL: http://api-gateway:8000

    ports:
      # ホスト:コンテナ（Vite dev serverは5173ポート）
      - "${WEB_UI_PORT:-3000}:5173"

    volumes:
      # ソースコードをマウントしてホットリロードを有効化
      - ./services/web-ui:/app
      # node_modulesはコンテナ内のものを使用（ホストと混在させない）
      - /app/node_modules

    depends_on:
      api-gateway:
        condition: service_healthy

    networks:
      - reprospective-network
```

**動作確認済み:**
- ✅ Dockerコンテナビルド成功
- ✅ http://localhost:3333 でアクセス可能（WEB_UI_PORT=3333）
- ✅ ホットリロード機能動作確認
- ✅ Tailwind CSS v4正常動作

**環境変数:**
- `WEB_UI_PORT`: プロジェクトルートの `.env` で設定（`env.example` から作成）
- `API_GATEWAY_PORT`: 同じく `.env` で設定（デフォルト8800）
- すべてローカル環境で完結するため、外部接続やCORS設定は不要

---

## 実装手順

**⚠️ 実装順序変更（2025-11-01）:**
コンテナ化を優先し、Docker環境でフロントエンド開発を行う方針に変更しました。

**変更理由:**
- すべてのサービスをDocker Composeで統一管理
- 環境構築の再現性向上
- 本番環境との差異を最小化

**新しい実装順序:**
1. ✅ ステップ1: プロジェクト基盤構築（完了 - 2025-11-01）
2. ✅ ステップ2: Docker化（完了 - 2025-11-01）
3. ✅ ステップ3: API連携実装（完了 - 2025-11-01）
4. ✅ ステップ4: コンポーネント実装（完了 - 2025-11-01）
5. ✅ ステップ5: アプリケーション統合（完了 - 2025-11-01）
6. ✅ ステップ6: 統合テスト（完了 - 2025-11-01）

---

### ステップ1: プロジェクト基盤構築（✅ 完了 - 2025-11-01）

**実施内容:**

1. ✅ **Vite + React 19プロジェクト作成**
   ```bash
   cd services
   npm create vite@latest web-ui -- --template react-ts
   cd web-ui
   npm install
   ```

2. ✅ **React 19.2.0にアップグレード（実験的使用）**
   ```bash
   npm install react@19.2.0 react-dom@19.2.0
   ```
   - React 19.2.0使用（最新版、実験的採用）

3. ✅ **依存パッケージインストール**
   ```bash
   npm install @tanstack/react-query axios
   npm install react-hook-form zod @hookform/resolvers
   npm install clsx tailwind-merge class-variance-authority lucide-react
   npm install -D @types/node
   ```

   **インストール済みパッケージ:**
   - @tanstack/react-query: 5.62.14
   - axios: 1.7.9
   - react-hook-form: 7.54.2
   - zod: 3.24.1
   - tailwindcss: 4.1.16
   - clsx, tailwind-merge (Shadcn/ui依存)

4. ✅ **Tailwind CSS v4セットアップ**

   手動で設定ファイル作成（`npx tailwindcss init`はv4で動作しないため）:

   **tailwind.config.js:**
   ```javascript
   export default {
     darkMode: ["class"],
     content: [
       "./index.html",
       "./src/**/*.{js,ts,jsx,tsx}",
     ],
     theme: {
       extend: {
         borderRadius: {
           lg: "var(--radius)",
           md: "calc(var(--radius) - 2px)",
           sm: "calc(var(--radius) - 4px)",
         },
         colors: {
           background: "hsl(var(--background))",
           foreground: "hsl(var(--foreground))",
           // ... その他のカラー定義
         },
       },
     },
     plugins: [],
   }
   ```

   **postcss.config.js:**
   ```javascript
   export default {
     plugins: {
       autoprefixer: {},  // tailwindcss プラグインは不要（v4）
     },
   }
   ```

   **src/index.css:**
   ```css
   @import "tailwindcss";  /* v4構文 */

   @layer base {
     :root {
       --background: 0 0% 100%;
       --foreground: 222.2 84% 4.9%;
       /* ... CSS変数定義 */
     }
   }
   ```

5. ✅ **TypeScript パスエイリアス設定**

   **tsconfig.app.json:**
   ```json
   {
     "compilerOptions": {
       "baseUrl": ".",
       "paths": {
         "@/*": ["./src/*"]
       }
     }
   }
   ```

   **vite.config.ts:**
   ```typescript
   import { defineConfig } from 'vite'
   import react from '@vitejs/plugin-react'
   import path from 'path'

   export default defineConfig({
     plugins: [react()],
     resolve: {
       alias: {
         '@': path.resolve(__dirname, './src'),
       },
     },
   })
   ```

6. ✅ **Shadcn/ui セットアップ**

   手動で設定ファイル作成（`npx shadcn@latest init`がTailwind v4検出エラー）:

   **components.json:**
   ```json
   {
     "$schema": "https://ui.shadcn.com/schema.json",
     "style": "new-york",
     "rsc": false,
     "tsx": true,
     "tailwind": {
       "config": "tailwind.config.js",
       "css": "src/index.css",
       "baseColor": "slate",
       "cssVariables": true
     },
     "aliases": {
       "components": "@/components",
       "utils": "@/lib/utils"
     }
   }
   ```

   **src/lib/utils.ts:**
   ```typescript
   import { clsx, type ClassValue } from "clsx"
   import { twMerge } from "tailwind-merge"

   export function cn(...inputs: ClassValue[]) {
     return twMerge(clsx(inputs))
   }
   ```

7. ✅ **ディレクトリ構成作成**
   ```bash
   mkdir -p src/{api,components/{ui,layout,directories,common},hooks,types,lib}
   ```

8. ✅ **環境変数設定**

   **services/web-ui/env.example:**
   ```bash
   # Web UI環境変数テンプレート
   # このファイルを .env にコピーして使用してください
   # cp env.example .env

   # API Gateway URL（ローカル開発環境）
   # 注意: プロジェクトルートの .env の API_GATEWAY_PORT と一致させること
   VITE_API_URL=http://localhost:8800

   # 本番環境（Docker内）では以下を使用
   # VITE_API_URL=http://api-gateway:8000
   ```

   **services/web-ui/.env:**
   ```bash
   VITE_API_URL=http://localhost:8800
   ```

**完了確認:**
- ✅ Vite + React 19.2.0プロジェクト構築
- ✅ Tailwind CSS v4セットアップ
- ✅ Shadcn/ui設定（手動構成）
- ✅ TypeScript パスエイリアス設定
- ✅ 依存パッケージ全インストール
- ✅ ディレクトリ構造構築
- ✅ 環境変数設定

### ステップ2: Docker化（✅ 完了 - 2025-11-01）

**目的:** フロントエンドをコンテナ化し、Docker Composeで統一管理

**方針:** 実験プロジェクトのため、開発・本番ともにVite Dev Serverを使用し、実装を簡素化

#### ✅ 2-1. Dockerfile作成

**services/web-ui/Dockerfile:**

```dockerfile
# Web UIコンテナ（Vite Dev Server）
# 実験プロジェクトのため本番環境でもViteの開発サーバーを使用

FROM node:20-alpine

WORKDIR /app

# 依存パッケージのインストール
COPY package.json package-lock.json ./
RUN npm ci

# ソースコードのコピー
COPY . .

# Viteの開発サーバーポートを公開
EXPOSE 5173

# 開発サーバーを起動（--host 0.0.0.0でコンテナ外からのアクセスを許可）
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**実装完了:**
- ✅ `--host 0.0.0.0`: コンテナ外からアクセス可能
- ✅ ホットリロード: ボリュームマウントで有効化
- ✅ 開発・本番環境で同一構成（実験プロジェクトのため）

#### ✅ 2-2. docker-compose.yml更新

プロジェクトルートの`docker-compose.yml`にweb-uiサービスを追加:

```yaml
services:
  # Web UI (React + Vite)
  web-ui:
    build: ./services/web-ui
    container_name: reprospective-web
    restart: unless-stopped

    environment:
      # API Gateway URL（コンテナ内からはサービス名でアクセス）
      VITE_API_URL: http://api-gateway:8000

    ports:
      # ホスト:コンテナ（Vite dev serverは5173ポート）
      - "${WEB_UI_PORT:-3000}:5173"

    volumes:
      # ソースコードをマウントしてホットリロードを有効化
      - ./services/web-ui:/app
      # node_modulesはコンテナ内のものを使用（ホストと混在させない）
      - /app/node_modules

    depends_on:
      api-gateway:
        condition: service_healthy

    networks:
      - reprospective-network
```

**実装完了:**
- ✅ ボリュームマウントでホットリロード有効
- ✅ `node_modules`はコンテナ内のものを使用
- ✅ API Gateway待機（`depends_on` + `condition: service_healthy`）
- ✅ `WEB_UI_PORT`環境変数対応（プロジェクトルート.env: 3333）

#### ✅ 2-3. .dockerignoreファイル作成

**services/web-ui/.dockerignore:**

```
# Node.js関連
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# ビルド成果物
dist/
dist-ssr/
*.local

# エディタディレクトリとファイル
.vscode/
.idea/
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# 環境変数ファイル
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# テスト関連
coverage/
.nyc_output/

# その他
*.log
.git/
.gitignore
README.md
```

#### ✅ 2-4. Tailwind CSS v4対応

**postcss.config.js修正:**

```javascript
export default {
  plugins: {
    autoprefixer: {},  // tailwindcssプラグイン削除（v4では不要）
  },
}
```

**src/index.css修正:**

```css
@import "tailwindcss";  /* v4構文（@tailwindディレクティブから変更） */

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    /* ... */
  }
}
```

#### ✅ 2-5. 動作確認

```bash
# プロジェクトルートで実行
docker compose up -d --build web-ui

# コンテナ状態確認
docker compose ps
# NAME                STATUS
# reprospective-web   Up (healthy)

# ログ確認
docker compose logs web-ui
# VITE v7.1.12 ready in 180 ms
# ➜ Local: http://localhost:5173/
# ➜ Network: http://172.18.0.4:5173/

# ブラウザでアクセス確認
# http://localhost:3333 → HTTP 200 OK

# ホットリロード確認
# services/web-ui/src/App.tsx を編集して保存
# → ログに "hmr update /src/App.tsx" 表示
# → ブラウザが自動リロード
```

**完了確認:**
- ✅ Dockerfileビルド成功
- ✅ docker-compose.yml統合
- ✅ .dockerignore作成
- ✅ Tailwind CSS v4エラー解消
- ✅ コンテナ起動成功（http://localhost:3333）
- ✅ ホットリロード動作確認
- ✅ Vite Dev Server正常動作

**技術的決定:**
- ✅ Nginx不使用（Vite Dev Serverのみ）
- ✅ 環境変数分離（services/web-ui/env.example）
- ✅ .gitignore統合（services/web-ui/.gitignore削除）

---

### ステップ3: API連携実装（✅ 完了 - 2025-11-01）

**実施内容:**

1. ✅ **型定義実装** (`types/directory.ts`)
   - `Directory`: APIレスポンス型（バックエンドと完全一致）
   - `DirectoryCreate`: 作成リクエスト型
   - `DirectoryUpdate`: 更新リクエスト型
   - `ApiError`: エラーレスポンス型

2. ✅ **Zodバリデーションスキーマ** (`lib/validators.ts`)
   - `directoryCreateSchema`: 作成フォーム用スキーマ
   - `directoryUpdateSchema`: 更新フォーム用スキーマ
   - 絶対パス検証、最大長チェック実装
   - フロントエンド側バリデーション（形式チェック）

3. ✅ **Axiosクライアント設定** (`api/client.ts`)
   - `VITE_API_URL`環境変数から自動読み込み
   - リクエスト/レスポンスインターセプター実装
   - エラーハンドリング、ログ記録
   - タイムアウト設定（10秒）

4. ✅ **ディレクトリAPI実装** (`api/directories.ts`)
   - `getDirectories()`: 全ディレクトリ取得
   - `getDirectory(id)`: ディレクトリ詳細取得
   - `createDirectory(data)`: ディレクトリ作成
   - `updateDirectory(id, data)`: ディレクトリ更新
   - `toggleDirectory(id)`: 有効/無効切り替え
   - `deleteDirectory(id)`: ディレクトリ削除

5. ✅ **React Queryカスタムフック実装** (`hooks/use*.ts`)
   - `useDirectories`: 一覧取得フック（クエリキー定義、30秒staleTime）
   - `useAddDirectory`: 追加ミューテーション（楽観的更新）
   - `useUpdateDirectory`: 更新ミューテーション（楽観的更新）
   - `useDeleteDirectory`: 削除ミューテーション（楽観的更新）
   - `useToggleDirectory`: 切り替えミューテーション（楽観的更新）

**実装完了:**
- ✅ 型安全性確保（TypeScript + バックエンドAPI整合性）
- ✅ 3層バリデーション実装（フロントエンド形式チェック）
- ✅ 楽観的更新実装（全ミューテーション）
- ✅ エラー時自動ロールバック
- ✅ React Query統合（サーバー状態管理、自動キャッシュ）

---

### ステップ4: コンポーネント実装（✅ 完了 - 2025-11-01）

**実施内容:**

**UIコンポーネント（6ファイル）:**
1. ✅ `button.tsx`: ボタンコンポーネント
2. ✅ `dialog.tsx`: ダイアログコンポーネント（Dialog, DialogContent, DialogHeader等）
3. ✅ `input.tsx`: テキスト入力コンポーネント
4. ✅ `label.tsx`: ラベルコンポーネント
5. ✅ `switch.tsx`: トグルスイッチコンポーネント
6. ✅ `textarea.tsx`: テキストエリアコンポーネント

**共通コンポーネント（2ファイル）:**
1. ✅ `LoadingSpinner.tsx`: ローディングスピナー（3サイズ対応、テキスト表示可能）
2. ✅ `ErrorMessage.tsx`: エラーメッセージ表示（アイコン付き）

**レイアウトコンポーネント（2ファイル）:**
1. ✅ `Header.tsx`: アプリケーションヘッダー（タイトル、アイコン表示）
2. ✅ `Layout.tsx`: 全体レイアウト（ヘッダー + コンテンツエリア）

**ディレクトリ管理コンポーネント（4ファイル）:**
1. ✅ `DirectoryCard.tsx`: ディレクトリ情報カード
   - 有効/無効切り替えボタン（楽観的更新）
   - 編集・削除ボタン
   - ステータス表示（監視中/無効）
2. ✅ `DirectoryList.tsx`: ディレクトリ一覧管理
   - ローディング・エラー状態処理
   - 空状態表示
   - 新規追加ボタン
   - ダイアログ管理
3. ✅ `AddDirectoryDialog.tsx`: 追加ダイアログ
   - React Hook Form統合
   - Zodバリデーション適用
   - リアルタイムエラー表示
4. ✅ `EditDirectoryDialog.tsx`: 編集ダイアログ
   - 既存値のプリセット
   - React Hook Form統合
   - Zodバリデーション適用
5. ✅ `DeleteDirectoryDialog.tsx`: 削除確認ダイアログ
   - 警告表示
   - 削除対象情報表示

**実装完了:**
- ✅ Shadcn/ui UIコンポーネント手動実装（6コンポーネント）
- ✅ React Hook Form + Zod統合（フォームバリデーション）
- ✅ 楽観的更新（切り替えボタン）
- ✅ ローディング・エラー状態処理
- ✅ UX配慮（削除確認、リアルタイムエラー表示）

---

### ステップ5: アプリケーション統合（✅ 完了 - 2025-11-01）

**実施内容:**

1. ✅ **main.tsx 実装** - React Query Provider設定
   - QueryClientProvider追加
   - QueryClient作成（デフォルトオプション設定）
   - React 19のStrictMode有効化

2. ✅ **App.tsx 実装** - アプリケーション統合
   - Layout コンポーネント統合
   - DirectoryList コンポーネント統合
   - ディレクトリ管理UI表示

3. ✅ **グローバルスタイル** - Tailwind CSS設定（既存）
   - Tailwind CSS v4 `@import` 構文
   - カスタムCSS変数定義

4. ✅ **環境変数設定** - `.env` ファイル（既存）
   - `VITE_API_URL` 設定（http://localhost:8800）

**実装完了:**
- ✅ React Query統合（サーバー状態管理）
- ✅ レイアウト構造確立
- ✅ ディレクトリ管理画面統合
- ✅ 全コンポーネント連携完了

---

### ステップ6: 統合テスト（✅ 完了 - 2025-11-01）

**実施内容:**

1. ✅ **Docker統合テスト**
   ```bash
   # プロジェクトルートで実行
   docker compose up -d --build web-ui
   # コンテナ状態確認
   docker compose ps
   ```

   **結果:**
   - ✅ reprospective-web: Up (http://localhost:3333 → 5173)
   - ✅ reprospective-api: Up (healthy) (http://localhost:8800 → 8000)
   - ✅ reprospective-db: Up (healthy) (http://localhost:6000 → 5432)

2. ✅ **コンテナ間通信テスト**
   - ✅ web-ui → api-gateway 接続確認
     ```bash
     docker compose exec web-ui wget -qO- http://api-gateway:8000/api/v1/directories/
     # 結果: JSON正常取得（2件のディレクトリ）
     ```
   - ✅ 環境変数確認: `VITE_API_URL=http://api-gateway:8000`

3. ✅ **API Gateway動作確認**
   ```bash
   curl http://localhost:8800/api/v1/directories/
   # 結果: API OK (2 directories)
   ```

4. ✅ **Web UI動作確認**
   ```bash
   curl http://localhost:3333/
   # 結果: HTML正常返却、Vite HMRスクリプト含む
   ```

5. ✅ **Vite Dev Server起動確認**
   ```
   docker compose logs web-ui
   # 結果: VITE v7.1.12 ready in 176 ms
   #       ➜ Local: http://localhost:5173/
   #       ➜ Network: http://172.18.0.4:5173/
   # エラーなし
   ```

**動作確認項目:**
- ✅ Docker環境でWeb UIが起動
- ✅ http://localhost:3333 でアクセス可能
- ✅ コンテナ間通信（web-ui → api-gateway）正常
- ✅ API Gateway接続テスト成功
- ✅ ビルドエラーなし
- ✅ Vite Dev Server正常起動
- ✅ 環境変数正しく設定

**ブラウザでの機能テスト:**
以下の機能は、ブラウザ（http://localhost:3333）でユーザーが実際に確認する必要があります：
- ディレクトリ一覧表示
- ディレクトリ追加（バリデーション含む）
- ON/OFF切り替え（楽観的更新）
- 編集・削除
- エラーハンドリング
- ホットリロード動作

---

## 完了条件

- [ ] **Docker環境でWeb UIが起動**
  - [ ] `docker compose up web-ui` で起動可能
  - [ ] http://localhost:3000 でアクセス可能
  - [ ] ホットリロードが動作（ファイル変更がリアルタイム反映）
- [ ] ディレクトリ一覧がAPI経由で表示される
- [ ] 新規ディレクトリ追加が正常に動作
- [ ] **バリデーションが正常に動作**
  - [ ] フロントエンドで絶対パスチェック（即座にエラー表示）
  - [ ] 相対パス（`..`）入力時にエラー表示
  - [ ] 空文字入力時にエラー表示
  - [ ] 文字数制限（表示名100文字、説明500文字）
- [ ] ディレクトリ編集が正常に動作
- [ ] ON/OFF切り替えが即座に反映される
- [ ] ディレクトリ削除が正常に動作
- [ ] エラー時に適切なメッセージが表示される（日本語）
- [ ] 30秒ごとに自動更新される
- [ ] レスポンシブデザインが動作する
- [ ] Dockerコンテナとして起動できる
- [ ] README.mdが作成され、使い方が文書化されている

---

## 技術的考慮事項

### セキュリティ

- **ローカル環境**: すべての通信はlocalhost内で完結するため、CORS設定は不要
- **入力サニタイゼーション**: パス検証、XSS対策（React/TypeScriptの標準機能で対応）
- **CSP (Content Security Policy)**: 将来的に本番環境構築時に検討

### パフォーマンス

- **バンドルサイズ最適化**: Viteの自動コード分割
- **画像最適化**: 必要に応じてWebP使用
- **React Query キャッシュ**: 不要なAPI呼び出し削減
- **楽観的更新**: トグル操作の即座のフィードバック

### ユーザビリティ

- **ローディング表示**: API呼び出し中の視覚的フィードバック
- **エラーメッセージ**: ユーザーフレンドリーな日本語メッセージ
- **トースト通知**: 操作成功/失敗の通知
- **レスポンシブデザイン**: モバイル対応

### 保守性

- **TypeScript**: 型安全性とコード補完
- **コンポーネント分割**: 単一責任原則
- **カスタムフック**: ビジネスロジック分離
- **ドキュメント**: README、コメント

---

## 将来的な拡張（Phase 3以降）

### 活動データ可視化

- **ダッシュボード**: 日別/週別/月別の活動サマリー
- **グラフ**: ファイル変更頻度、デスクトップ利用時間
- **フィルタリング**: ディレクトリ別、ファイルタイプ別

### AI分析結果表示

- **活動要約**: AIによる日次サマリー
- **カテゴリ分類**: 作業内容の自動分類
- **進捗推測**: タスク完了度の推定

### 認証・認可

- **JWT認証**: ユーザーログイン
- **ロールベース制御**: 閲覧/編集権限
- **セッション管理**: トークンリフレッシュ

### マルチホスト対応

- **ホスト選択**: 複数ホストの監視対象管理
- **ホスト別ビュー**: ホストごとの活動データ表示

---

## 参考リンク

- [React 19 Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [TanStack Query (React Query)](https://tanstack.com/query/latest)
- [Shadcn/ui](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Axios](https://axios-http.com/)
- [React Hook Form](https://react-hook-form.com/)
- [Zod](https://zod.dev/)

---

## 人間動作確認結果（2025-11-01）

### 実施内容

**手順書:** `docs/manual/humantest.md` に従って基本機能テストを実施

**確認項目:**
- ✅ Web UIアクセス（http://localhost:3333）
- ✅ ディレクトリ一覧表示
- ✅ ディレクトリ追加（バリデーション動作）
- ✅ ディレクトリ編集
- ✅ ON/OFF切り替え（楽観的更新）
- ✅ ディレクトリ削除

### 発見した問題と修正

#### 1. 環境変数の問題

**問題:**
- docker-compose.ymlで`VITE_API_URL: http://api-gateway:8000`とハードコード
- ブラウザからDocker内部のホスト名にアクセスできず、Network Errorが発生

**修正:**
```yaml
# Before (docker-compose.yml)
environment:
  VITE_API_URL: http://api-gateway:8000

# After (docker-compose.yml)
# 環境変数はservices/web-ui/.envで管理
# ブラウザからアクセスするため、VITE_API_URLはlocalhost:8800を使用
```

**services/web-ui/.env:**
```
VITE_API_URL=http://localhost:8800
```

#### 2. scripts/start.sh の問題

**問題:**
- `docker compose up -d database`でdatabaseコンテナのみ起動
- web-uiとapi-gatewayが起動しない

**修正:**
```bash
# Before
docker compose up -d database

# After
docker compose up -d
```

接続情報表示も追加:
```
💡 接続情報:
   Web UI:        http://localhost:3333
   API Gateway:   http://localhost:8800
   Swagger UI:    http://localhost:8800/docs
   PostgreSQL:    localhost:6000
```

#### 3. UIデザインの問題

**問題:**
- カードのボーダーが表示されない
- ボタンが小さく押しにくい
- カード間の余白が少なく見づらい

**原因:**
Tailwind CSS v4のカスタムカラー設定により、デフォルトの色クラス（`blue-200`、`gray-300`など）が機能しない

**修正:**

**DirectoryCard.tsx:**
```tsx
// ボーダーをインラインスタイルで明示的に指定
<div
  className={cn(
    'rounded-lg p-6 shadow-md hover:shadow-lg transition-all',
    directory.enabled ? 'bg-white' : 'bg-gray-50 opacity-60'
  )}
  style={{
    border: directory.enabled ? '2px solid #BFDBFE' : '2px solid #D1D5DB'
  }}
>

// ボタンサイズとパディング拡大
<button className="p-3 ...">  {/* p-2 → p-3 */}
  <Edit className="h-5 w-5" />  {/* h-4 w-4 → h-5 w-5 */}
</button>
```

**DirectoryList.tsx:**
```tsx
// カード間の余白増加
<div className="grid gap-6">  {/* gap-4 → gap-6 */}
```

### 最終確認結果

**すべての基本機能が正常に動作:**
- ✅ http://localhost:3333 でWeb UIアクセス可能
- ✅ API Gateway連携正常（http://localhost:8800）
- ✅ ディレクトリ追加・編集・削除・ON/OFF切り替えすべて動作
- ✅ バリデーション動作（絶対パスチェック、文字数制限）
- ✅ 楽観的更新（即座のUI反映、エラー時自動ロールバック）
- ✅ UIデザイン：ボーダー、影、ホバー効果すべて正常表示

**Phase 2.2 Web UI完了 🎉**

---

## 次のステップ

**Phase 2.2完了により、以下が利用可能:**
- ✅ ブラウザベースの監視ディレクトリ設定UI
- ✅ リアルタイム更新
- ✅ 楽観的更新によるスムーズなUX

**Phase 3候補:**
1. 活動データ可視化（セッション、ファイル変更のグラフ表示）
2. AI分析エンジン（活動データの要約・分類）
3. 追加コレクター（BrowserActivityParser、GitHubMonitor、SNSMonitor）
