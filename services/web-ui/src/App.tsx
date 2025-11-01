/**
 * Reprospectiveアプリケーション
 *
 * ファイルシステム監視設定のメインアプリケーション
 */

import { Layout } from '@/components/layout/Layout';
import { DirectoryList } from '@/components/directories/DirectoryList';

function App() {
  return (
    <Layout>
      <DirectoryList />
    </Layout>
  );
}

export default App;
