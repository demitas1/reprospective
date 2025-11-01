/**
 * アプリケーションエントリーポイント
 *
 * React Query Providerを設定し、アプリケーション全体で
 * サーバー状態管理を利用できるようにする
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './index.css';
import App from './App.tsx';

// React Query クライアントを作成
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // デフォルト設定: 30秒間はキャッシュを新鮮とみなす
      staleTime: 30000,
      // エラー時は自動再試行しない（ユーザーが明示的に操作する）
      retry: false,
      // ウィンドウフォーカス時に自動再取得
      refetchOnWindowFocus: true,
    },
    mutations: {
      // エラー時は自動再試行しない
      retry: false,
    },
  },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>
);
