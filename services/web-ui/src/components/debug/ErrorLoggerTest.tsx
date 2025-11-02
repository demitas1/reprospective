/**
 * エラーロガーテストコンポーネント
 *
 * 各エラーソースをテストするためのUIコンポーネント
 * ブラウザで http://localhost:3333/test にアクセスして使用
 */

import { useState } from 'react';
import { apiClient } from '@/api/client';
import { logError } from '@/utils/errorLogger';

export const ErrorLoggerTest = () => {
  const [result, setResult] = useState<string>('');

  // Test 1: React Error Boundary
  const [shouldThrow, setShouldThrow] = useState(false);

  if (shouldThrow) {
    throw new Error('Test error from React Error Boundary');
  }

  // Test 2: グローバルエラー（window.error）
  const testGlobalError = () => {
    setResult('グローバルエラーをトリガー中...');
    // グローバルエラーを発生させる
    setTimeout(() => {
      // @ts-expect-error - テスト用に意図的にエラーを発生
      window.nonExistentFunction();
    }, 100);
  };

  // Test 3: Promise拒否
  const testUnhandledRejection = () => {
    setResult('Promise拒否をトリガー中...');
    setTimeout(() => {
      Promise.reject(new Error('Test unhandled rejection'));
    }, 100);
  };

  // Test 4: Axiosエラー（存在しないエンドポイント）
  const testAxiosError = async () => {
    setResult('Axiosエラーをトリガー中...');
    try {
      await apiClient.get('/api/v1/nonexistent-endpoint');
    } catch (error) {
      setResult('Axiosエラーが発生しました（ログに記録されました）');
    }
  };

  // Test 5: 手動ログ送信
  const testManualLog = () => {
    setResult('手動ログを送信中...');
    logError(
      new Error('Manual test error'),
      'react',
      { testType: 'manual', timestamp: new Date().toISOString() }
    );
    setResult('手動ログを送信しました');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          エラーロガーテスト
        </h1>
        <p className="text-sm text-gray-600 mb-8">
          各ボタンをクリックして異なるエラーソースをテストできます。
          エラーは ./logs/errors.log に記録されます。
        </p>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">テスト一覧</h2>

          <div className="space-y-4">
            {/* Test 1: React Error Boundary */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium mb-2">
                Test 1: React Error Boundary
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                Reactコンポーネント内でエラーをスロー（エラーUI表示）
              </p>
              <button
                onClick={() => setShouldThrow(true)}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Reactエラーをスロー
              </button>
            </div>

            {/* Test 2: グローバルエラー */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium mb-2">
                Test 2: グローバルエラー（window.error）
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                存在しない関数を呼び出してグローバルエラーを発生
              </p>
              <button
                onClick={testGlobalError}
                className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
              >
                グローバルエラーをトリガー
              </button>
            </div>

            {/* Test 3: Promise拒否 */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium mb-2">
                Test 3: Promise拒否（unhandledrejection）
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                キャッチされないPromise拒否を発生
              </p>
              <button
                onClick={testUnhandledRejection}
                className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
              >
                Promise拒否をトリガー
              </button>
            </div>

            {/* Test 4: Axiosエラー */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium mb-2">
                Test 4: Axiosエラー（HTTPエラー）
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                存在しないAPIエンドポイントにリクエスト（404エラー）
              </p>
              <button
                onClick={testAxiosError}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Axiosエラーをトリガー
              </button>
            </div>

            {/* Test 5: 手動ログ */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium mb-2">
                Test 5: 手動ログ送信
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                logError()関数を直接呼び出してログ送信
              </p>
              <button
                onClick={testManualLog}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                手動ログを送信
              </button>
            </div>
          </div>
        </div>

        {/* 結果表示 */}
        {result && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-900">{result}</p>
          </div>
        )}

        {/* 使用方法 */}
        <div className="bg-gray-100 rounded-lg p-6 mt-6">
          <h2 className="text-lg font-semibold mb-3">使用方法</h2>
          <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
            <li>ブラウザの開発者ツールを開く（F12）</li>
            <li>コンソールタブで以下を確認:
              <ul className="list-disc list-inside ml-6 mt-1">
                <li>[ErrorLogger] エラーロギング有効</li>
                <li>[ErrorLogger] 設定: ...</li>
              </ul>
            </li>
            <li>各テストボタンをクリック</li>
            <li>5秒後に ./logs/errors.log を確認</li>
            <li>コンソールで動的制御:
              <ul className="list-disc list-inside ml-6 mt-1">
                <li>window.__errorLogger.getConfig()</li>
                <li>window.__errorLogger.setSourceEnabled('axios', false)</li>
              </ul>
            </li>
          </ol>
        </div>
      </div>
    </div>
  );
};
