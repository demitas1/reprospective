/**
 * Reprospectiveアプリケーション
 *
 * ファイルシステム監視設定のメインアプリケーション
 */

import { Layout } from '@/components/layout/Layout';
import { DirectoryList } from '@/components/directories/DirectoryList';
import { ErrorLoggerTest } from '@/components/debug/ErrorLoggerTest';

function App() {
  // URLパラメータでテストページを表示
  const params = new URLSearchParams(window.location.search);
  const isTestMode = params.get('test') === 'error-logger';

  if (isTestMode) {
    return <ErrorLoggerTest />;
  }

  return (
    <Layout>
      <DirectoryList />
    </Layout>
  );
}

export default App;
