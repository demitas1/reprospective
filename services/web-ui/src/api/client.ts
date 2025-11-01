/**
 * Axios HTTPクライアント設定
 */

import axios from 'axios';

/**
 * API Gateway のベースURL
 *
 * 環境変数 VITE_API_URL から取得
 * - ホスト環境: http://localhost:8800
 * - Docker環境: http://api-gateway:8000
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8800';

/**
 * Axiosインスタンス
 *
 * すべてのAPI呼び出しでこのインスタンスを使用
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10秒
});

/**
 * リクエストインターセプター
 *
 * 将来的に認証トークンを追加する場合はここで実施
 */
apiClient.interceptors.request.use(
  (config) => {
    // 将来的にJWTトークンを追加
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * レスポンスインターセプター
 *
 * エラーハンドリングとログ記録
 */
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // エラーログ記録
    if (error.response) {
      // サーバーがエラーレスポンスを返した場合
      console.error('API Error:', {
        status: error.response.status,
        data: error.response.data,
        url: error.config.url,
      });
    } else if (error.request) {
      // リクエストは送信されたがレスポンスがない場合
      console.error('Network Error:', error.message);
    } else {
      // リクエスト設定中にエラーが発生した場合
      console.error('Request Error:', error.message);
    }

    return Promise.reject(error);
  }
);
