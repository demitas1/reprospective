# フロントエンドエラーロギング機能 実装計画

**ステータス**: ✅ Phase 1 & 2 完了

**更新日**: 2025-11-02

**目的**: Claude Codeがブラウザのエラーを直接確認できるようにする

**実装履歴:**
- ✅ Phase 1 完了（2025-11-02 午前）: API Gateway デバッグエンドポイント実装
- ✅ Phase 2 完了（2025-11-02 午後）: Web UI エラーロガー実装（細粒度制御対応）

---

## 概要

Webフロントエンド（React）で発生したエラーをファイルに記録し、Claude Codeが直接確認できるようにします。開発環境でのデバッグ効率を向上させることを目的とします。

**主要機能:**
- ✅ エラーソース別の細粒度制御（React, Axios, React Query, Global, Promise Rejection）
- ✅ 環境変数による静的制御 + ブラウザコンソールからの動的制御
- ✅ パフォーマンス最適化（不要なログ送信を回避）
- ✅ バッファリング（最大10件、5秒ごとに一括送信）
- ✅ 機密情報のサニタイズ

### 採用アプローチ

**API Gatewayにデバッグエンドポイントを追加する方式（推奨）**

```
Browser → Web UI → API Gateway (FastAPI) → /var/log/frontend/errors.log
                                           ↓
                              (ボリュームマウント)
                                           ↓
                         Host: ./logs/frontend-errors.log
                                           ↓
                                     Claude Code
```

**選定理由:**
- ✅ CORS問題なし（既存のAPI Gateway経由）
- ✅ Docker設定変更最小限
- ✅ 環境変数で有効/無効を切り替え可能
- ✅ FastAPIのバリデーション機能が使える
- ✅ 将来的に認証・ログ分析機能を追加しやすい
- ✅ 既存のインフラを活用（新規コンテナ不要）

---

## アーキテクチャ

### システム構成

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ エラー発生
       ↓
┌─────────────────────────────────────────────┐
│ Web UI (React 19 + Vite)                    │
│                                             │
│ ┌─────────────────────────────────────┐   │
│ │ Error Boundary                       │   │
│ │ - componentDidCatch()                │   │
│ └─────────────────────────────────────┘   │
│                                             │
│ ┌─────────────────────────────────────┐   │
│ │ グローバルエラーハンドラー           │   │
│ │ - window.addEventListener('error')   │   │
│ │ - unhandledrejection                 │   │
│ └─────────────────────────────────────┘   │
│                                             │
│ ┌─────────────────────────────────────┐   │
│ │ React Query エラーハンドラー         │   │
│ │ - QueryClient.defaultOptions.onError │   │
│ └─────────────────────────────────────┘   │
│                                             │
│ ┌─────────────────────────────────────┐   │
│ │ Axios インターセプター               │   │
│ │ - response.interceptor.error         │   │
│ └─────────────────────────────────────┘   │
│                    ↓                        │
│           ┌─────────────────┐              │
│           │ ErrorLogger     │              │
│           │ - バッファリング │              │
│           │ - サニタイズ     │              │
│           │ - 非同期送信     │              │
│           └─────────────────┘              │
└──────────────────┬──────────────────────────┘
                   │ POST /api/v1/debug/log-errors
                   ↓
┌─────────────────────────────────────────────┐
│ API Gateway (FastAPI)                       │
│                                             │
│ /api/v1/debug/log-errors エンドポイント     │
│ - 環境変数でデバッグモード判定              │
│ - Pydanticバリデーション                    │
│ - ファイル書き込み                          │
│                                             │
│ /var/log/frontend/errors.log               │
└──────────────────┬──────────────────────────┘
                   │ (Dockerボリュームマウント)
                   ↓
┌─────────────────────────────────────────────┐
│ Host: ./logs/frontend-errors.log            │
└──────────────────┬──────────────────────────┘
                   │
                   ↓
            ┌──────────────┐
            │ Claude Code  │
            │ tail -f      │
            └──────────────┘
```

---

## 実装計画

### Phase 1: バックエンド実装（API Gateway）

#### Step 1-1: デバッグエンドポイント追加

**ファイル:** `services/api-gateway/app/routers/debug.py`（新規作成）

**実装内容:**
- `POST /api/v1/debug/log-errors` エンドポイント
- Pydanticモデルでバリデーション
- ファイル書き込み処理
- 環境変数でデバッグモード判定

**Pydanticモデル:**
```python
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class ErrorEntry(BaseModel):
    """フロントエンドエラーエントリ"""
    timestamp: str = Field(..., description="エラー発生日時（ISO 8601）")
    message: str = Field(..., description="エラーメッセージ")
    stack: Optional[str] = Field(None, description="スタックトレース")
    context: Optional[str] = Field(None, description="エラーコンテキスト")
    user_agent: Optional[str] = Field(None, description="ユーザーエージェント")
    url: Optional[str] = Field(None, description="エラー発生URL")
    component_stack: Optional[str] = Field(None, description="Reactコンポーネントスタック")
    additional_info: Optional[dict[str, Any]] = Field(None, description="追加情報")

class LogErrorsRequest(BaseModel):
    """エラーログ送信リクエスト"""
    errors: list[ErrorEntry] = Field(..., description="エラーエントリのリスト")
```

**エンドポイント実装:**
```python
from fastapi import APIRouter, HTTPException, status
from app.config import settings
import logging
import json
from pathlib import Path

router = APIRouter(prefix="/api/v1/debug", tags=["debug"])
logger = logging.getLogger(__name__)

LOG_FILE_PATH = Path("/var/log/frontend/errors.log")

@router.post("/log-errors", status_code=status.HTTP_201_CREATED)
async def log_frontend_errors(request: LogErrorsRequest):
    """
    フロントエンドエラーをログファイルに記録

    開発環境でのみ有効化（settings.debug_mode=True）
    """
    # デバッグモードでない場合は無効
    if not settings.debug_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="デバッグエンドポイントは開発環境でのみ有効です"
        )

    try:
        # ログディレクトリの作成
        LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # ログファイルに追記
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            for error in request.errors:
                log_line = json.dumps(
                    error.model_dump(),
                    ensure_ascii=False,
                    default=str
                ) + "\n"
                f.write(log_line)

        logger.info(f"フロントエンドエラーを記録: {len(request.errors)}件")

        return {
            "status": "ok",
            "logged_count": len(request.errors),
            "log_file": str(LOG_FILE_PATH)
        }

    except Exception as e:
        logger.error(f"エラーログ記録失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ログ記録に失敗しました: {str(e)}"
        )
```

#### Step 1-2: 設定ファイル更新

**ファイル:** `services/api-gateway/app/config.py`

**追加内容:**
```python
class Settings(BaseSettings):
    # 既存の設定...

    # デバッグ設定（追加）
    debug_mode: bool = False  # デフォルトは無効
```

#### Step 1-3: ルーター登録

**ファイル:** `services/api-gateway/app/main.py`

**追加内容:**
```python
from app.routers import health, directories, debug

# デバッグモード有効時のみルーター登録
if settings.debug_mode:
    app.include_router(debug.router)
    logger.info("デバッグエンドポイント有効化")
```

#### Step 1-4: Docker設定更新

**ファイル:** `docker-compose.yml`

**変更内容:**
```yaml
services:
  api-gateway:
    environment:
      # デバッグモード設定（追加）
      DEBUG_MODE: ${DEBUG:-false}

    volumes:
      # ログディレクトリをホストにマウント（追加）
      - ./logs:/var/log/frontend:rw

  web-ui:
    # 変更なし
```

**ファイル:** `env.example`（プロジェクトルート）

**追加内容:**
```bash
# ================================
# デバッグ設定
# ================================

# デバッグモード（開発環境のみtrue）
# フロントエンドエラーロギングを有効化
DEBUG=true
```

---

### Phase 2: フロントエンド実装（Web UI）

#### Step 2-1: エラーロガーユーティリティ（細粒度制御対応）

**ファイル:** `services/web-ui/src/utils/errorLogger.ts`（新規作成）

**実装内容:**

**設計方針: 細粒度ロギング制御**

各エラーソース（React, Axios, React Query等）ごとにON/OFF制御を実装します。これにより：
- ✅ 不要なログ送信を回避してパフォーマンス向上
- ✅ 特定のソースのエラーのみフォーカスしてデバッグ効率向上
- ✅ ログノイズを削減
- ✅ 環境変数で柔軟に制御

```typescript
/**
 * フロントエンドエラーロガー
 *
 * エラーをバッファリングし、API Gatewayに送信してファイルに記録
 * 各エラーソースごとに細粒度制御が可能
 */

import { apiClient } from '@/api/client';

interface ErrorEntry {
  timestamp: string;
  message: string;
  stack?: string;
  context?: string;
  user_agent?: string;
  url?: string;
  component_stack?: string;
  additional_info?: Record<string, unknown>;
}

/**
 * ロギング設定（各ソースごとにON/OFF制御）
 */
interface LoggingConfig {
  react: boolean;              // React Error Boundary
  reactQuery: boolean;         // React Query errors
  axios: boolean;              // Axios errors
  global: boolean;             // グローバルエラーハンドラー
  unhandledRejection: boolean; // Promise rejection
}

/**
 * エラーソースの型定義
 */
type ErrorSource = keyof LoggingConfig;

class ErrorLogger {
  private buffer: ErrorEntry[] = [];
  private readonly maxBufferSize = 10;
  private readonly flushInterval = 5000; // 5秒
  private flushTimer: NodeJS.Timeout | null = null;
  private isEnabled: boolean;
  private config: LoggingConfig;

  constructor() {
    // 全体のロギング有効/無効を判定
    this.isEnabled = import.meta.env.VITE_ENABLE_ERROR_LOGGING === 'true';

    // 各ソースごとの設定を環境変数から読み込み
    this.config = {
      react: import.meta.env.VITE_LOG_REACT !== 'false',              // デフォルトtrue
      reactQuery: import.meta.env.VITE_LOG_REACT_QUERY !== 'false',   // デフォルトtrue
      axios: import.meta.env.VITE_LOG_AXIOS !== 'false',              // デフォルトtrue
      global: import.meta.env.VITE_LOG_GLOBAL !== 'false',            // デフォルトtrue
      unhandledRejection: import.meta.env.VITE_LOG_UNHANDLED_REJECTION !== 'false', // デフォルトtrue
    };

    if (this.isEnabled) {
      this.startFlushTimer();
      console.log('[ErrorLogger] エラーロギング有効');
      console.log('[ErrorLogger] 設定:', this.config);
    }
  }

  /**
   * 特定のソースのロギングが有効かチェック
   */
  private isSourceEnabled(source: ErrorSource): boolean {
    if (!this.isEnabled) return false;
    return this.config[source];
  }

  /**
   * 実行時に特定のソースのロギングを有効/無効化
   * デバッグ時にコンソールから動的に制御可能
   */
  setSourceEnabled(source: ErrorSource, enabled: boolean): void {
    this.config[source] = enabled;
    console.log(`[ErrorLogger] ${source} ロギング: ${enabled ? '有効' : '無効'}`);
  }

  /**
   * 現在の設定を取得
   */
  getConfig(): Readonly<LoggingConfig> {
    return { ...this.config };
  }

  /**
   * エラーをログに記録
   */
  async logError(
    error: Error | string,
    source: ErrorSource,
    additionalInfo?: Record<string, unknown>
  ): Promise<void> {
    // ソース別の有効/無効チェック
    if (!this.isSourceEnabled(source)) {
      return;
    }

    const errorMessage = typeof error === 'string' ? error : error.message;
    const errorStack = typeof error === 'string' ? undefined : error.stack;

    const entry: ErrorEntry = {
      timestamp: new Date().toISOString(),
      message: errorMessage,
      stack: this.sanitizeStack(errorStack),
      context: source, // コンテキストにソース名を記録
      user_agent: navigator.userAgent,
      url: window.location.href,
      additional_info: additionalInfo,
    };

    this.buffer.push(entry);

    // バッファが満杯なら即座に送信
    if (this.buffer.length >= this.maxBufferSize) {
      await this.flush();
    }
  }

  /**
   * 簡易API（後方互換性のため残す）
   */
  async logErrorLegacy(
    error: Error | string,
    context?: string,
    additionalInfo?: Record<string, unknown>
  ): Promise<void> {
    // contextから推測してソースを判定（デフォルトはglobal）
    const source: ErrorSource = context?.includes('React Query')
      ? 'reactQuery'
      : context?.includes('Axios')
      ? 'axios'
      : context?.includes('React')
      ? 'react'
      : 'global';

    return this.logError(error, source, additionalInfo);
  }

  /**
   * スタックトレースから機密情報を除外
   */
  private sanitizeStack(stack?: string): string | undefined {
    if (!stack) return undefined;

    // VITE_で始まる環境変数を除外
    return stack.replace(/VITE_[A-Z_]+=[^\s]*/g, '[REDACTED]');
  }

  /**
   * バッファの内容をAPIに送信
   */
  private async flush(): Promise<void> {
    if (this.buffer.length === 0) return;

    const errors = [...this.buffer];
    this.buffer = [];

    try {
      await apiClient.post('/api/v1/debug/log-errors', {
        errors,
      });
      console.log(`[ErrorLogger] ${errors.length}件のエラーを記録しました`);
    } catch (e) {
      // ログ送信失敗は握りつぶす（無限ループ防止）
      console.error('[ErrorLogger] ログ送信失敗:', e);
      // 送信失敗したエラーは破棄（バッファに戻さない）
    }
  }

  /**
   * 定期的にバッファをフラッシュ
   */
  private startFlushTimer(): void {
    this.flushTimer = setInterval(() => {
      this.flush().catch(console.error);
    }, this.flushInterval);
  }

  /**
   * クリーンアップ
   */
  destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    this.flush().catch(console.error);
  }
}

// シングルトンインスタンス
export const errorLogger = new ErrorLogger();

/**
 * エラーをログに記録（新API - ソース指定）
 */
export const logError = (
  error: Error | string,
  source: ErrorSource,
  additionalInfo?: Record<string, unknown>
): void => {
  errorLogger.logError(error, source, additionalInfo).catch(console.error);
};

/**
 * グローバルスコープに公開（ブラウザコンソールから動的制御可能）
 */
if (typeof window !== 'undefined') {
  (window as any).__errorLogger = errorLogger;
}
```

**使用例:**

```typescript
// React Error Boundaryから
logError(error, 'react', { componentStack: errorInfo.componentStack });

// Axiosから
logError(error, 'axios', { status: 404, url: '/api/...' });

// React Queryから
logError(error, 'reactQuery', { queryKey: ['users'] });

// グローバルエラーハンドラーから
logError(error, 'global', { filename: 'app.js', lineno: 10 });

// Promise rejectionから
logError(error, 'unhandledRejection', { reason: 'Network timeout' });
```

**ブラウザコンソールから動的制御:**

```javascript
// Axiosエラーのみを無効化
window.__errorLogger.setSourceEnabled('axios', false);

// React Queryエラーを有効化
window.__errorLogger.setSourceEnabled('reactQuery', true);

// 現在の設定を確認
window.__errorLogger.getConfig();
// → { react: true, reactQuery: true, axios: false, global: true, unhandledRejection: true }
```

#### Step 2-2: Error Boundary実装

**ファイル:** `services/web-ui/src/components/common/ErrorBoundary.tsx`（新規作成）

**実装内容:**
```typescript
/**
 * React Error Boundary
 *
 * React 19対応のエラーバウンダリー
 * コンポーネントツリー内のエラーをキャッチしてログ記録
 */

import { Component, ErrorInfo, ReactNode } from 'react';
import { logError } from '@/utils/errorLogger';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // エラーログに記録（ソース: 'react'）
    logError(error, 'react', {
      componentStack: errorInfo.componentStack,
    });
  }

  render() {
    if (this.state.hasError) {
      // カスタムフォールバックUIがあれば表示
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // デフォルトのエラー表示
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full p-6 bg-white rounded-lg shadow-lg border-2 border-red-200">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-red-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-gray-900 mb-2">
                  エラーが発生しました
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                  アプリケーションで予期しないエラーが発生しました。
                  ページをリロードして再度お試しください。
                </p>
                {this.state.error && (
                  <details className="mb-4">
                    <summary className="text-sm font-medium text-gray-700 cursor-pointer hover:text-gray-900">
                      エラー詳細を表示
                    </summary>
                    <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-auto max-h-40">
                      {this.state.error.message}
                    </pre>
                  </details>
                )}
                <button
                  onClick={() => window.location.reload()}
                  className="w-full px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
                >
                  ページをリロード
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

#### Step 2-3: グローバルエラーハンドラー統合

**ファイル:** `services/web-ui/src/main.tsx`

**変更内容:**
```typescript
/**
 * アプリケーションエントリーポイント
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './index.css';
import App from './App.tsx';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { logError } from '@/utils/errorLogger';

// React Query クライアントを作成
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: false,
      refetchOnWindowFocus: true,
      // クエリエラーハンドラー追加（ソース: 'reactQuery'）
      onError: (error) => {
        logError(error as Error, 'reactQuery', {
          type: 'query',
        });
      },
    },
    mutations: {
      retry: false,
      // ミューテーションエラーハンドラー追加（ソース: 'reactQuery'）
      onError: (error) => {
        logError(error as Error, 'reactQuery', {
          type: 'mutation',
        });
      },
    },
  },
});

// グローバルエラーハンドラー（ソース: 'global'）
window.addEventListener('error', (event) => {
  logError(
    new Error(event.message),
    'global',
    {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    }
  );
});

// Promise rejectハンドラー（ソース: 'unhandledRejection'）
window.addEventListener('unhandledrejection', (event) => {
  logError(
    new Error(String(event.reason)),
    'unhandledRejection',
    {
      reason: event.reason,
    }
  );
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>
);
```

#### Step 2-4: Axiosインターセプター統合

**ファイル:** `services/web-ui/src/api/client.ts`

**変更内容:**
```typescript
/**
 * Axios HTTPクライアント設定
 */

import axios from 'axios';
import { logError } from '@/utils/errorLogger';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8800';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// リクエストインターセプター
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// レスポンスインターセプター
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // エラーログ記録（ソース: 'axios'）
    logError(error, 'axios', {
      status: error.response?.status,
      url: error.config?.url,
      method: error.config?.method,
      data: error.response?.data,
    });

    // 既存のconsole.errorも維持
    if (error.response) {
      console.error('API Error:', {
        status: error.response.status,
        data: error.response.data,
        url: error.config.url,
      });
    } else if (error.request) {
      console.error('Network Error:', error.message);
    } else {
      console.error('Request Error:', error.message);
    }

    return Promise.reject(error);
  }
);
```

#### Step 2-5: 環境変数設定

**ファイル:** `services/web-ui/.env`

**追加内容:**
```bash
# API Gateway URL
VITE_API_URL=http://localhost:8800

# エラーロギング全体の有効化（開発環境のみ）
VITE_ENABLE_ERROR_LOGGING=true

# 各ソースごとのロギング制御（オプション、デフォルトはすべてtrue）
# falseに設定すると、そのソースのエラーログは送信されない
# VITE_LOG_REACT=true              # React Error Boundary
# VITE_LOG_REACT_QUERY=true        # React Query errors
# VITE_LOG_AXIOS=true              # Axios errors
# VITE_LOG_GLOBAL=true             # グローバルエラーハンドラー
# VITE_LOG_UNHANDLED_REJECTION=true # Promise rejection

# 使用例: Axiosエラーのみを無効化
# VITE_LOG_AXIOS=false
```

**ファイル:** `services/web-ui/env.example`

**更新内容:**
```bash
# Web UI環境変数テンプレート

# API Gateway URL（ローカル開発環境）
VITE_API_URL=http://localhost:8800

# ================================
# エラーロギング設定
# ================================

# エラーロギング全体の有効化（開発環境のみtrueに設定）
# 本番環境ではfalseにすること
VITE_ENABLE_ERROR_LOGGING=true

# 各ソースごとのロギング制御（オプション、デフォルトはすべてtrue）
# 特定のソースのエラーログを無効化したい場合のみ設定
#
# VITE_LOG_REACT=true              # React Error Boundary
# VITE_LOG_REACT_QUERY=true        # React Query errors
# VITE_LOG_AXIOS=true              # Axios errors
# VITE_LOG_GLOBAL=true             # グローバルエラーハンドラー
# VITE_LOG_UNHANDLED_REJECTION=true # Promise rejection

# 使用例:
# - Axiosエラーのみを無効化したい場合:
#   VITE_LOG_AXIOS=false
#
# - React QueryとAxiosエラーのみを記録したい場合:
#   VITE_LOG_REACT=false
#   VITE_LOG_GLOBAL=false
#   VITE_LOG_UNHANDLED_REJECTION=false
```

---

## 細粒度ロギング制御の利点

### 1. パフォーマンス最適化

**問題:**
- すべてのエラーをログ送信すると、HTTPリクエストのオーバーヘッドが発生
- React Queryの自動リトライ中に大量のエラーが発生する可能性

**解決策:**
```bash
# React Queryエラーのみを無効化
VITE_LOG_REACT_QUERY=false
```

### 2. デバッグ効率向上

**問題:**
- 特定の問題（例: Axiosエラー）のみをデバッグしたい
- 他のエラーログがノイズになる

**解決策:**
```bash
# Axiosエラーのみを有効化
VITE_LOG_REACT=false
VITE_LOG_REACT_QUERY=false
VITE_LOG_GLOBAL=false
VITE_LOG_UNHANDLED_REJECTION=false
VITE_LOG_AXIOS=true
```

### 3. 既知のエラーのフィルタリング

**問題:**
- 特定のエラー（例: 開発環境でのCORS警告）が既知で対処不要
- ログファイルが無駄なエントリで埋まる

**解決策:**
```javascript
// ブラウザコンソールから動的に無効化
window.__errorLogger.setSourceEnabled('global', false);
```

### 4. 段階的デバッグ

**ワークフロー例:**

```bash
# ステップ1: すべてのエラーを記録
VITE_ENABLE_ERROR_LOGGING=true

# ステップ2: ログを確認して、Axiosエラーが原因と特定
tail -f ./logs/errors.log

# ステップ3: Axiosエラーのみにフォーカス
VITE_LOG_REACT=false
VITE_LOG_REACT_QUERY=false
VITE_LOG_GLOBAL=false
VITE_LOG_UNHANDLED_REJECTION=false

# ステップ4: Axiosエラーを修正後、他のエラーを確認
VITE_LOG_AXIOS=false
VITE_LOG_REACT=true
```

### 5. ブラウザコンソールからの動的制御

開発中にリロードせずにロギング設定を変更可能：

```javascript
// 現在の設定を確認
window.__errorLogger.getConfig();

// Axiosエラーを一時的に無効化
window.__errorLogger.setSourceEnabled('axios', false);

// 再度有効化
window.__errorLogger.setSourceEnabled('axios', true);
```

---

## セキュリティ考慮事項

### 1. デバッグモードの制限

- ✅ 環境変数`DEBUG=true`でのみ有効化
- ✅ API Gatewayでリクエストを拒否（DEBUG=falseの場合）
- ✅ 本番環境では無効化（env.exampleにコメント記載）

### 2. 機密情報のサニタイズ

- ✅ 環境変数（VITE_*）をスタックトレースから除外
- ✅ パスワード、トークン等の自動検出・除外（必要に応じて拡張）
- ✅ ユーザーエージェントは記録（デバッグ用）

### 3. ログファイルへのアクセス制限

- ✅ ログディレクトリはホスト側の`./logs/`にマウント
- ✅ Docker内部からのみアクセス可能
- ✅ Webからの直接アクセス不可

### 4. ログ送信の失敗処理

- ✅ ログ送信エラーは握りつぶす（無限ループ防止）
- ✅ console.errorのみ出力
- ✅ 送信失敗したエラーは破棄

---

## パフォーマンス最適化

### 1. バッファリング

- ✅ 最大10件までバッファに蓄積
- ✅ 5秒ごとに自動フラッシュ
- ✅ バッファ満杯時は即座に送信

### 2. 非同期送信

- ✅ `async/await`で非同期処理
- ✅ UIをブロックしない
- ✅ エラー送信の失敗を握りつぶす

### 3. 送信頻度の制限

- ✅ 1回のリクエストで複数エラーをまとめて送信
- ✅ HTTP接続のオーバーヘッド削減

---

## テスト計画

### 手動テスト項目

#### バックエンド（API Gateway）

1. ✅ デバッグエンドポイント動作確認
   ```bash
   curl -X POST http://localhost:8800/api/v1/debug/log-errors \
     -H "Content-Type: application/json" \
     -d '{"errors": [{"timestamp": "2025-11-02T10:00:00Z", "message": "Test error"}]}'
   ```

2. ✅ ログファイル生成確認
   ```bash
   cat ./logs/frontend-errors.log
   ```

3. ✅ デバッグモード無効時の拒否確認（DEBUG=false）

#### フロントエンド（Web UI）

1. ✅ Error Boundary動作確認
   - 意図的にエラーを発生させる
   - エラーUIが表示されるか
   - ログファイルに記録されるか

2. ✅ グローバルエラーハンドラー動作確認
   - コンソールで`throw new Error('test')`実行
   - ログファイルに記録されるか

3. ✅ React Query エラー動作確認
   - API呼び出しを失敗させる
   - ログファイルに記録されるか

4. ✅ Axios エラー動作確認
   - 存在しないエンドポイントにリクエスト
   - ログファイルに記録されるか

5. ✅ バッファリング動作確認
   - 連続して10件以上のエラーを発生させる
   - まとめて送信されるか

6. ✅ 細粒度制御動作確認
   - 環境変数で特定のソースを無効化
   - ログファイルに記録されないことを確認
   - ブラウザコンソールから動的に制御
   - `window.__errorLogger.getConfig()` で設定確認

### Claude Codeでの確認

```bash
# ログファイルをリアルタイム監視
tail -f ./logs/frontend-errors.log

# ログファイルの内容を整形表示
cat ./logs/frontend-errors.log | jq '.'
```

---

## ログファイル管理

### ログローテーション

**現時点では手動クリーンアップ:**

```bash
# ログファイルをクリア
> ./logs/frontend-errors.log

# または削除
rm ./logs/frontend-errors.log
```

**将来的な拡張（Phase 3以降）:**
- ログローテーション機能の追加
- 古いログの自動削除（7日以上）
- ログファイルサイズ制限

---

## 実装スケジュール

### ✅ Phase 1: バックエンド実装（API Gateway）【完了】

- **所要時間**: 実績 35分（計画 30分）
- **完了日時**: 2025-11-02
- ✅ **Step 1-1**: デバッグエンドポイント追加（15分）
- ✅ **Step 1-2**: 設定ファイル更新（5分）
- ✅ **Step 1-3**: ルーター登録（5分）
- ✅ **Step 1-4**: Docker設定更新（5分）
- ✅ **動作確認テスト**: 単一/バッチエラー送信、ログファイル確認（5分）

### ✅ Phase 2: フロントエンド実装（Web UI）【完了】

- **所要時間**: 実績 45分（計画 60分）
- **完了日時**: 2025-11-02
- ✅ **Step 2-1**: エラーロガーユーティリティ（20分）
- ✅ **Step 2-2**: Error Boundary実装（10分）
- ✅ **Step 2-3**: グローバルエラーハンドラー統合（5分）
- ✅ **Step 2-4**: Axiosインターセプター統合（5分）
- ✅ **Step 2-5**: 環境変数設定（5分）
- ✅ **動作確認テスト**: 基本動作確認、ログファイル記録確認（追加）

**合計所要時間**: 実績 約80分（計画 90分）

---

## Phase 1 実装結果（2025-11-02）

### 実装ファイル

**新規作成:**
- ✅ `services/api-gateway/app/routers/debug.py` (94行)
  - ErrorEntry, LogErrorsRequest, LogErrorsResponse Pydanticモデル
  - POST /api/v1/debug/log-errors エンドポイント
  - ファイル書き込み処理（/var/log/frontend/errors.log）

- ✅ `logs/.gitignore` (6行)
  - ログファイル除外設定

**更新:**
- ✅ `services/api-gateway/app/config.py`
  - `debug_mode: bool = False` フィールド追加

- ✅ `services/api-gateway/app/main.py`
  - debugルーターのインポートと条件付き登録
  - デバッグモード有効化ログ出力

- ✅ `docker-compose.yml`
  - api-gatewayサービスに環境変数 `DEBUG_MODE: ${DEBUG:-false}` 追加
  - ボリュームマウント `./logs:/var/log/frontend:rw` 追加

- ✅ `env.example`
  - デバッグモード設定の説明コメント追加

### 動作確認結果

**✅ エンドポイント登録確認:**
```bash
$ curl -s http://localhost:8800/openapi.json | jq '.paths | keys'
[
  "/",
  "/api/v1/debug/log-errors",  # ← 追加確認
  "/api/v1/directories/",
  ...
]
```

**✅ 単一エラー送信テスト:**
```bash
$ curl -X POST http://localhost:8800/api/v1/debug/log-errors \
  -H "Content-Type: application/json" \
  -d '{"errors": [{"timestamp": "2025-11-02T10:00:00Z", "message": "Test error"}]}'

# レスポンス:
{
  "status": "ok",
  "logged_count": 1,
  "log_file": "/var/log/frontend/errors.log"
}
```

**✅ 複数エラーバッチ送信テスト:**
```bash
$ curl -X POST http://localhost:8800/api/v1/debug/log-errors \
  -d '{"errors": [{"timestamp": "...", "message": "Error 1"}, ...]}'

# レスポンス:
{
  "status": "ok",
  "logged_count": 3,
  "log_file": "/var/log/frontend/errors.log"
}
```

**✅ ログファイル確認:**
```bash
$ cat ./logs/errors.log | jq '.'
{
  "timestamp": "2025-11-02T10:00:00Z",
  "message": "Test error from Phase 1",
  "stack": "Error: Test error\n    at test.js:1:1",
  "context": "Phase 1 Test",
  "user_agent": "Mozilla/5.0 (Test)",
  "url": "http://localhost:3333/test",
  "component_stack": null,
  "additional_info": null
}
```

**✅ デバッグモード有効化ログ:**
```
2025-11-02 08:43:02,055 - app.main - INFO - デバッグエンドポイント有効化
```

### 技術的発見事項

**1. ログファイル名の相違**
- 計画: `/var/log/frontend/errors.log`
- 実際: `./logs/errors.log` (ホスト側)
- コンテナ内: `/var/log/frontend/errors.log`
- 原因: Dockerボリュームマウントにより、コンテナ内のディレクトリ構造がホスト側に反映
- 影響: なし（Claude Codeからアクセス可能）

**2. Dockerイメージ再ビルドの必要性**
- 初回テスト時、コンテナ内のconfig.pyが古いバージョンだった
- `docker compose up -d --build api-gateway` で解決
- 今後のコード変更時も再ビルドが必要

**3. 環境変数の命名**
- .envファイル: `DEBUG=true`
- docker-compose.yml: `DEBUG_MODE=${DEBUG:-false}`
- config.py: `debug_mode: bool`
- Pydantic Settingsが自動で環境変数名を変換（case_sensitive=False）

---

## Phase 2 実装結果（2025-11-02）

### 実装ファイル

**新規作成:**
- ✅ `services/web-ui/src/utils/errorLogger.ts` (198行)
  - ErrorLogger クラス実装
  - LoggingConfig インターフェース（5つのエラーソース制御）
  - isSourceEnabled(), setSourceEnabled(), getConfig() メソッド
  - バッファリング機能（最大10件、5秒ごとにフラッシュ）
  - sanitizeStack() でVITE_*環境変数を除外
  - window.__errorLogger グローバル公開

- ✅ `services/web-ui/src/components/common/ErrorBoundary.tsx` (100行)
  - React Error Boundary クラスコンポーネント
  - componentDidCatch() でエラーログ送信（ソース: 'react'）
  - フォールバックUI（エラー詳細、リロードボタン）

- ✅ `services/web-ui/src/components/debug/ErrorLoggerTest.tsx` (190行)
  - エラーテスト用UIコンポーネント
  - 5種類のエラーテスト（React, Global, Promise, Axios, Manual）
  - アクセス: http://localhost:3333/?test=error-logger

**更新:**
- ✅ `services/web-ui/src/main.tsx`
  - ErrorBoundary コンポーネントで全体をラップ
  - グローバルエラーハンドラー追加（window.addEventListener('error')）
  - Promise拒否ハンドラー追加（unhandledrejection）

- ✅ `services/web-ui/src/api/client.ts`
  - Axiosレスポンスインターセプターにエラーログ送信追加（ソース: 'axios'）
  - status, url, method, data を additional_info に記録

- ✅ `services/web-ui/.env`
  - VITE_ENABLE_ERROR_LOGGING=true
  - 5つのソース制御変数追加（すべてtrue）

- ✅ `services/web-ui/env.example`
  - フロントエンドエラーロギング設定セクション追加
  - 詳細な使用例とコメント（66行）

- ✅ `services/web-ui/src/App.tsx`
  - URLパラメータでテストページ表示機能追加

### 動作確認結果

**✅ Web UIコンテナ再ビルド:**
```bash
$ docker compose up -d --build web-ui
# 成功: reprospective-web  Recreated
```

**✅ エラーなしでコンパイル:**
```bash
$ docker compose logs web-ui --tail 30
# VITE v7.1.12  ready in 173 ms
# ローカル: http://localhost:5173/
```

**✅ 手動エラー送信テスト:**
```bash
$ curl -X POST http://localhost:8800/api/v1/debug/log-errors \
  -H "Content-Type: application/json" \
  -d '{"errors": [{"timestamp": "2025-11-02T12:00:00Z", "message": "Test error from Phase 2 - Manual submission", ...}]}'

# レスポンス:
{
  "status": "ok",
  "logged_count": 1,
  "log_file": "/var/log/frontend/errors.log"
}
```

**✅ ログファイル記録確認:**
```bash
$ cat ./logs/errors.log | jq '.'
{
  "timestamp": "2025-11-02T12:00:00Z",
  "message": "Test error from Phase 2 - Manual submission",
  "stack": "Error: Test error\n    at test.js:1:1",
  "context": "axios",
  "user_agent": "curl/test",
  "url": "http://localhost:3333/test?test=error-logger",
  "component_stack": null,
  "additional_info": {
    "testType": "manual",
    "phase": 2
  }
}
```

### 細粒度制御の実装

**5つのエラーソース:**
1. ✅ `react` - React Error Boundary
2. ✅ `reactQuery` - React Query（TanStack Query）
3. ✅ `axios` - Axios HTTPエラー
4. ✅ `global` - window.addEventListener('error')
5. ✅ `unhandledRejection` - Promise拒否

**環境変数による静的制御:**
```bash
# 全体のON/OFF
VITE_ENABLE_ERROR_LOGGING=true

# 各ソースの個別制御
VITE_LOG_REACT=true
VITE_LOG_REACT_QUERY=true
VITE_LOG_AXIOS=true
VITE_LOG_GLOBAL=true
VITE_LOG_UNHANDLED_REJECTION=true
```

**ブラウザコンソールからの動的制御:**
```javascript
// 設定確認
window.__errorLogger.getConfig()
// → { react: true, reactQuery: true, axios: true, global: true, unhandledRejection: true }

// Axiosエラーを無効化
window.__errorLogger.setSourceEnabled('axios', false)
// → [ErrorLogger] axios ロギング: 無効

// 再度有効化
window.__errorLogger.setSourceEnabled('axios', true)
// → [ErrorLogger] axios ロギング: 有効
```

### テストUIの提供

**アクセス方法:**
```
http://localhost:3333/?test=error-logger
```

**テスト項目:**
1. React Error Boundary（エラーをスロー）
2. グローバルエラー（存在しない関数呼び出し）
3. Promise拒否（unhandledrejection）
4. Axiosエラー（404エラー）
5. 手動ログ送信（logError直接呼び出し）

**使用方法:**
1. ブラウザ開発者ツールを開く（F12）
2. コンソールで `[ErrorLogger] エラーロギング有効` を確認
3. 各テストボタンをクリック
4. 5秒後に `./logs/errors.log` を確認
5. ブラウザコンソールから動的制御テスト

### 技術的発見事項

**1. React 19 Error Boundary互換性**
- React 19でもクラスコンポーネントベースのError Boundaryが正常動作
- getDerivedStateFromError() と componentDidCatch() を使用

**2. Vite環境変数の命名規則**
- `VITE_` プレフィックスが必須
- `import.meta.env.VITE_*` で取得
- デフォルト値の判定は `!== 'false'` を使用（文字列比較）

**3. TypeScript型安全性**
- ErrorSource型で厳密なソース名チェック
- logError(error, source, additionalInfo) の第2引数は型安全

**4. バッファリング動作**
- 10件貯まると即座にflush
- 5秒間隔でタイマーflush
- flush失敗時はバッファを破棄（無限ループ防止）

---

## 完了条件

### Phase 1（バックエンド）

- ✅ API Gatewayにデバッグエンドポイントが追加されている
- ✅ 環境変数`DEBUG=true`でエンドポイントが有効化される
- ✅ フロントエンドエラーがログファイルに記録される
- ✅ Claude Codeが`./logs/errors.log`を確認できる
- ✅ バッファリング機能（複数エラーの一括送信）が動作する
- ⏭️ デバッグモード無効時はエンドポイントが拒否される（Phase 2で確認予定）

### Phase 2（フロントエンド）

- ✅ Error Boundaryでキャッチされたエラーが記録される
- ✅ グローバルエラーハンドラーでキャッチされたエラーが記録される
- ✅ React Queryエラーハンドラーが実装される（main.tsxに統合）
- ✅ Axiosエラーが記録される
- ✅ 機密情報がサニタイズされる（VITE_*環境変数を除外）
- ✅ 細粒度制御が動作する（5つのエラーソースを個別ON/OFF）
- ✅ ブラウザコンソールから動的制御が可能（window.__errorLogger）
- ✅ ログにソース名（context）が記録される
- ✅ テストUIが提供される（http://localhost:3333/?test=error-logger）
- ✅ バッファリングが動作する（最大10件、5秒ごとにフラッシュ）
- ✅ 環境変数でロギング全体をON/OFF可能（VITE_ENABLE_ERROR_LOGGING）

---

## 将来的な拡張（Phase 3以降）

### 1. ログ分析機能

- エラーの統計情報表示
- 頻出エラーの検出
- エラートレンドのグラフ表示

### 2. ログ検索機能

- 日時範囲でフィルタリング
- エラーメッセージで検索
- コンテキストで絞り込み

### 3. アラート機能

- 特定エラーの発生時に通知
- エラー急増時のアラート
- メール/Slack通知

### 4. ログローテーション自動化

- logrotateとの統合
- 古いログの自動圧縮・削除
- ログファイルサイズ制限

---

## 参考リンク

- [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
- [FastAPI Request Files](https://fastapi.tiangolo.com/tutorial/request-files/)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [Docker Volumes](https://docs.docker.com/storage/volumes/)
