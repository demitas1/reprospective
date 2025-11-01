# Phase 2.2 実装計画: Web UI

**ステータス: 📋 計画中**

**前提条件:** Phase 2.1 (API Gateway & host-agent設定同期) 完了

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
├── Dockerfile                        # マルチステージビルド
├── nginx.conf                        # Nginx設定（本番用）
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── index.html
├── public/
│   └── favicon.ico
├── src/
│   ├── main.tsx                      # エントリーポイント
│   ├── App.tsx                       # ルートコンポーネント
│   ├── api/
│   │   ├── client.ts                 # Axios設定
│   │   └── directories.ts            # ディレクトリAPI
│   ├── components/
│   │   ├── ui/                       # Shadcn/uiコンポーネント
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── form.tsx
│   │   │   ├── input.tsx
│   │   │   ├── label.tsx
│   │   │   ├── switch.tsx
│   │   │   └── toast.tsx
│   │   ├── layout/
│   │   │   ├── Header.tsx            # ヘッダー
│   │   │   └── Layout.tsx            # レイアウト
│   │   ├── directories/
│   │   │   ├── DirectoryList.tsx     # ディレクトリ一覧
│   │   │   ├── DirectoryCard.tsx     # ディレクトリカード
│   │   │   ├── AddDirectoryDialog.tsx # 追加ダイアログ
│   │   │   ├── EditDirectoryDialog.tsx # 編集ダイアログ
│   │   │   └── DeleteDirectoryDialog.tsx # 削除確認
│   │   └── common/
│   │       ├── LoadingSpinner.tsx    # ローディング
│   │       └── ErrorMessage.tsx      # エラー表示
│   ├── hooks/
│   │   ├── useDirectories.ts         # ディレクトリ取得
│   │   ├── useAddDirectory.ts        # ディレクトリ追加
│   │   ├── useUpdateDirectory.ts     # ディレクトリ更新
│   │   ├── useDeleteDirectory.ts     # ディレクトリ削除
│   │   └── useToggleDirectory.ts     # 有効/無効切り替え
│   ├── types/
│   │   └── directory.ts              # 型定義
│   ├── lib/
│   │   ├── utils.ts                  # ユーティリティ
│   │   └── validators.ts             # ★ Zodバリデーションスキーマ
│   └── styles/
│       └── globals.css               # グローバルスタイル
└── README.md
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

## Docker統合

### Dockerfile（マルチステージビルド）

```dockerfile
# ビルドステージ
FROM node:20-alpine AS builder

WORKDIR /app

# 依存関係インストール
COPY package.json package-lock.json ./
RUN npm ci

# ソースコピー＆ビルド
COPY . .
RUN npm run build

# 本番ステージ
FROM nginx:alpine

# Nginxカスタム設定
COPY nginx.conf /etc/nginx/conf.d/default.conf

# ビルド成果物コピー
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### nginx.conf

```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # React Router対応（SPA）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # APIプロキシ（CORS対策）
    location /api/ {
        proxy_pass http://api-gateway:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # キャッシュ設定
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### docker-compose.yml 追加

```yaml
services:
  web-ui:
    build: ./services/web-ui
    container_name: reprospective-web
    restart: unless-stopped
    environment:
      # API GatewayのURL（コンテナ間通信）
      # Nginxプロキシ経由でapi-gatewayコンテナにアクセス
      VITE_API_URL: http://api-gateway:8000
    ports:
      - "${WEB_UI_PORT:-3000}:80"
    depends_on:
      api-gateway:
        condition: service_healthy
    networks:
      - reprospective-network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

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
1. ステップ1: プロジェクト基盤構築（✅ 完了）
2. **ステップ2: Docker化（優先実装）** ← 変更
3. ステップ3: API連携実装
4. ステップ4: コンポーネント実装
5. ステップ5: アプリケーション統合
6. ステップ6: 統合テスト

---

### ステップ1: プロジェクト基盤構築（✅ 完了）

1. **Vite + React 19プロジェクト作成**
   ```bash
   cd services
   npm create vite@latest web-ui -- --template react-ts
   cd web-ui
   npm install
   ```

2. **React 19.2.0にアップグレード（実験的使用）**
   ```bash
   npm install react@19.2.0 react-dom@19.2.0
   ```

3. **依存パッケージインストール**
   ```bash
   npm install @tanstack/react-query axios
   npm install react-hook-form zod @hookform/resolvers
   npm install -D tailwindcss postcss autoprefixer
   npm install -D @types/node
   npx tailwindcss init -p
   ```

4. **TypeScript パスエイリアス設定**

   `tsconfig.json` に以下を追加:
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

   `vite.config.ts` に以下を追加:
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

   **パスエイリアスの説明:**
   - `@/` を `src/` のエイリアスとして設定
   - インポート時に `import { Button } from '@/components/ui/button'` のように記述可能
   - 相対パス `../../components/ui/button` を避けられ、可読性向上
   - TypeScriptとViteの両方で設定が必要

5. **Shadcn/ui セットアップ**
   ```bash
   npx shadcn-ui@latest init
   ```

   対話的な設定で以下を選択:
   - Style: `default`
   - Base color: `slate`
   - CSS variables: `yes`
   - TypeScript: `yes`
   - React Server Components: `no`
   - Tailwind config: `tailwind.config.js`
   - Components: `src/components`
   - Utils: `src/lib/utils`
   - React Query: `yes`

   ```bash
   npx shadcn-ui@latest add button card dialog form input label switch toast
   ```

6. **ディレクトリ構成作成**
   ```bash
   mkdir -p src/{api,components/{ui,layout,directories,common},hooks,types,lib,styles}
   ```

7. **環境変数設定**
   ```bash
   # プロジェクトルートのenv.exampleを参照してservices/web-ui/.envを作成
   cat > .env << 'EOF'
   # API Gateway URL（ローカル開発環境）
   VITE_API_URL=http://localhost:8800
   EOF
   ```

### ステップ2: Docker化（優先実装）

**目的:** フロントエンドをコンテナ化し、Docker Composeで統一管理

**方針:** 実験プロジェクトのため、開発・本番ともにVite Dev Serverを使用し、実装を簡素化

#### 2-1. Dockerfile作成

**services/web-ui/Dockerfile:**

```dockerfile
FROM node:20-alpine

WORKDIR /app

# 依存関係をコピー
COPY package.json package-lock.json ./

# 依存関係インストール
RUN npm ci

# ソースコードをコピー
COPY . .

# 開発サーバーポート
EXPOSE 5173

# Vite開発サーバー起動（ホットリロード有効）
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**説明:**
- `--host 0.0.0.0`: コンテナ外からアクセス可能にする
- ホットリロード: ボリュームマウントで有効化
- 開発・本番環境で同一構成（実験プロジェクトのため）

**注意:** 本プロジェクトはローカル完結・単一ユーザーの実験プロジェクトのため、Vite Dev Serverのみで十分です。将来的に外部公開する場合はNginxへの移行を検討してください。

#### 2-2. docker-compose.yml更新

プロジェクトルートの`docker-compose.yml`にweb-uiサービスを追加:

```yaml
services:
  # ... 既存のdatabase, api-gatewayサービス ...

  # Web UI (Vite Dev Server)
  web-ui:
    build: ./services/web-ui
    container_name: reprospective-web
    restart: unless-stopped
    environment:
      # コンテナ間通信用API URL
      VITE_API_URL: http://api-gateway:8000
    ports:
      - "${WEB_UI_PORT:-3000}:5173"
    volumes:
      # ホットリロード用（ソースコードをマウント）
      - ./services/web-ui:/app
      - /app/node_modules  # node_modulesはコンテナ内のものを使用
    depends_on:
      api-gateway:
        condition: service_healthy
    networks:
      - reprospective-network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:5173/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**ポイント:**
- ボリュームマウントでホットリロード有効
- `node_modules`はコンテナ内のものを使用（ホストOSとの差異回避）
- API Gateway待機（`depends_on` + `condition: service_healthy`）

#### 2-3. .dockerignoreファイル作成

**services/web-ui/.dockerignore:**

```
node_modules
dist
.env
.env.local
npm-debug.log
.DS_Store
```

#### 2-4. 動作確認

```bash
# プロジェクトルートで実行
docker compose build web-ui
docker compose up web-ui

# ブラウザでアクセス
# http://localhost:3000 (WEB_UI_PORTが3000の場合)
# または http://localhost:3333 (env.exampleのデフォルト)

# ホットリロード確認
# services/web-ui/src/App.tsx を編集して保存
# → ブラウザが自動リロードされることを確認
```

---

### ステップ3: API連携実装

1. **バリデーション実装** (`lib/validators.ts`)
   - Zodスキーマ定義
   - ディレクトリパス検証ロジック
2. **型定義** (`types/directory.ts`)
   - APIレスポンス型定義
   - バックエンドとの整合性確認
3. **API client 設定** (`api/client.ts`)
   - Axios設定
   - エラーインターセプター
4. **ディレクトリAPI実装** (`api/directories.ts`)
   - CRUD操作関数
5. **カスタムフック実装** (`hooks/use*.ts`)
   - React Query統合
   - 楽観的更新

### ステップ4: コンポーネント実装

1. **基本レイアウト** (`Layout.tsx`, `Header.tsx`)
2. **ディレクトリカード** (`DirectoryCard.tsx`)
3. **ディレクトリ一覧** (`DirectoryList.tsx`)
4. **追加ダイアログ** (`AddDirectoryDialog.tsx`)
   - React Hook Formとの統合
   - Zodバリデーション適用
   - リアルタイムエラー表示
5. **編集ダイアログ** (`EditDirectoryDialog.tsx`)
   - 既存値のプリセット
   - バリデーション適用
6. **削除確認ダイアログ** (`DeleteDirectoryDialog.tsx`)
7. **共通コンポーネント** (`LoadingSpinner.tsx`, `ErrorMessage.tsx`)

### ステップ5: アプリケーション統合

1. **App.tsx 実装** - メインコンポーネント
2. **main.tsx 設定** - React Query Provider
3. **グローバルスタイル** - Tailwind CSS設定（✅ 完了）
4. **環境変数設定** - `.env` ファイル（✅ 完了）

### ステップ6: 統合テスト

1. **Docker統合テスト**
   ```bash
   # プロジェクトルートで実行
   docker compose up -d
   # http://localhost:3000 でアクセス確認
   ```

2. **機能テスト**
   - ディレクトリ一覧表示
   - ディレクトリ追加
   - ON/OFF切り替え
   - 編集・削除
   - エラーハンドリング
   - ホットリロード動作確認

3. **コンテナ間通信テスト**
   - web-ui → api-gateway 接続確認
   - APIエラーハンドリング確認

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

## 次のステップ

Phase 2.2実装開始後、以下の順で進めます：

1. Vite + React 19プロジェクト作成
2. 依存パッケージインストール
3. API連携実装
4. コンポーネント実装
5. Docker化
6. 統合テスト

各ステップ完了後、動作確認とドキュメント更新を行います。
