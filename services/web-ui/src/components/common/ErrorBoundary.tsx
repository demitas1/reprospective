/**
 * React Error Boundary
 *
 * Reactコンポーネント内のエラーをキャッチしてログに記録
 * フォールバックUIを表示してアプリケーションのクラッシュを防ぐ
 */

import { Component, ReactNode } from 'react';
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
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Reactエラーをログに記録
    logError(error, 'react', {
      componentStack: errorInfo.componentStack,
    });

    console.error('[ErrorBoundary] Reactエラー:', error, errorInfo);
  }

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // カスタムフォールバックUIがあれば使用
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // デフォルトエラーUI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
            <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full">
              <svg
                className="w-6 h-6 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>

            <h1 className="mt-4 text-xl font-semibold text-gray-900 text-center">
              エラーが発生しました
            </h1>

            <p className="mt-2 text-sm text-gray-600 text-center">
              予期しないエラーが発生しました。ページをリロードしてください。
            </p>

            {this.state.error && (
              <div className="mt-4 p-3 bg-gray-50 rounded border border-gray-200">
                <p className="text-xs font-mono text-gray-700 break-all">
                  {this.state.error.message}
                </p>
              </div>
            )}

            <button
              onClick={this.handleReload}
              className="mt-6 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              ページをリロード
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
