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
  react: boolean; // React Error Boundary
  reactQuery: boolean; // React Query errors
  axios: boolean; // Axios errors
  global: boolean; // グローバルエラーハンドラー
  unhandledRejection: boolean; // Promise rejection
}

/**
 * エラーソースの型定義
 */
export type ErrorSource = keyof LoggingConfig;

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
      react: import.meta.env.VITE_LOG_REACT !== 'false', // デフォルトtrue
      reactQuery: import.meta.env.VITE_LOG_REACT_QUERY !== 'false', // デフォルトtrue
      axios: import.meta.env.VITE_LOG_AXIOS !== 'false', // デフォルトtrue
      global: import.meta.env.VITE_LOG_GLOBAL !== 'false', // デフォルトtrue
      unhandledRejection:
        import.meta.env.VITE_LOG_UNHANDLED_REJECTION !== 'false', // デフォルトtrue
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
