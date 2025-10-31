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
- **フレームワーク**: React 19
- **ビルドツール**: Vite
- **言語**: TypeScript
- **UIライブラリ**:
  - Tailwind CSS（スタイリング）
  - Shadcn/ui（コンポーネント）
- **状態管理**: React Query (TanStack Query v5)
- **HTTPクライアント**: Axios
- **フォーム管理**: React Hook Form + Zod

**インフラ:**
- **Webサーバー**: Nginx（本番）/ Vite Dev Server（開発）
- **コンテナ化**: Docker（マルチステージビルド）
- **オーケストレーション**: Docker Compose

### システム構成

```
┌──────────────┐      HTTP      ┌──────────────┐
│   Browser    │ ─────────────> │   Web UI     │
│              │                 │ (React/Nginx)│
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
│   │   └── utils.ts                  # ユーティリティ
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

**バリデーション:**
- 絶対パスチェック
- 重複チェック（パス）
- 空白文字トリム

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
          dir.id === id ? { ...dir, is_enabled: !dir.is_enabled } : dir
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

### 型定義

**types/directory.ts:**

```typescript
export interface Directory {
  id: number;
  path: string;
  display_name: string | null;
  description: string | null;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface DirectoryCreate {
  path: string;
  display_name?: string;
  description?: string;
}

export interface DirectoryUpdate {
  path?: string;
  display_name?: string;
  description?: string;
  is_enabled?: boolean;
}
```

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
      # 開発時はViteのAPIプロキシを使用
      # 本番時はNginxのプロキシを使用（/api/でルーティング）
      VITE_API_URL: http://localhost:${API_GATEWAY_PORT:-8800}
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

---

## 実装手順

### ステップ1: プロジェクト基盤構築

1. **Vite + React 19プロジェクト作成**
   ```bash
   cd services
   npm create vite@latest web-ui -- --template react-ts
   cd web-ui
   npm install
   ```

2. **依存パッケージインストール**
   ```bash
   npm install @tanstack/react-query axios
   npm install react-hook-form zod @hookform/resolvers
   npm install -D tailwindcss postcss autoprefixer
   npm install -D @types/node
   npx tailwindcss init -p
   ```

3. **Shadcn/ui セットアップ**
   ```bash
   npx shadcn-ui@latest init
   npx shadcn-ui@latest add button card dialog form input label switch toast
   ```

4. **ディレクトリ構成作成**
   ```bash
   mkdir -p src/{api,components/{ui,layout,directories,common},hooks,types,lib,styles}
   ```

### ステップ2: API連携実装

1. **API client 設定** (`api/client.ts`)
2. **ディレクトリAPI実装** (`api/directories.ts`)
3. **型定義** (`types/directory.ts`)
4. **カスタムフック実装** (`hooks/use*.ts`)

### ステップ3: コンポーネント実装

1. **基本レイアウト** (`Layout.tsx`, `Header.tsx`)
2. **ディレクトリカード** (`DirectoryCard.tsx`)
3. **ディレクトリ一覧** (`DirectoryList.tsx`)
4. **追加ダイアログ** (`AddDirectoryDialog.tsx`)
5. **編集ダイアログ** (`EditDirectoryDialog.tsx`)
6. **削除確認ダイアログ** (`DeleteDirectoryDialog.tsx`)
7. **共通コンポーネント** (`LoadingSpinner.tsx`, `ErrorMessage.tsx`)

### ステップ4: アプリケーション統合

1. **App.tsx 実装** - メインコンポーネント
2. **main.tsx 設定** - React Query Provider
3. **グローバルスタイル** - Tailwind CSS設定
4. **環境変数設定** - `.env` ファイル

### ステップ5: Docker化

1. **Dockerfile作成** - マルチステージビルド
2. **nginx.conf作成** - SPA対応設定
3. **docker-compose.yml更新** - web-uiサービス追加
4. **ビルド確認**
   ```bash
   docker compose build web-ui
   docker compose up web-ui
   ```

### ステップ6: 統合テスト

1. **ローカル起動テスト**
   ```bash
   # 開発サーバー
   cd services/web-ui
   npm run dev
   ```

2. **Docker統合テスト**
   ```bash
   docker compose up -d
   # http://localhost:3000 でアクセス確認
   ```

3. **機能テスト**
   - ディレクトリ一覧表示
   - ディレクトリ追加
   - ON/OFF切り替え
   - 編集・削除
   - エラーハンドリング

---

## 完了条件

- [ ] Web UIが http://localhost:3000 でアクセス可能
- [ ] ディレクトリ一覧がAPI経由で表示される
- [ ] 新規ディレクトリ追加が正常に動作
- [ ] ディレクトリ編集が正常に動作
- [ ] ON/OFF切り替えが即座に反映される
- [ ] ディレクトリ削除が正常に動作
- [ ] エラー時に適切なメッセージが表示される
- [ ] 30秒ごとに自動更新される
- [ ] レスポンシブデザインが動作する
- [ ] Dockerコンテナとして起動できる
- [ ] README.mdが作成され、使い方が文書化されている

---

## 技術的考慮事項

### セキュリティ

- **CORS設定**: API Gateway側で許可オリジン設定
- **入力サニタイゼーション**: パス検証、XSS対策
- **CSP (Content Security Policy)**: 適切なヘッダー設定

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
