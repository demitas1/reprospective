/**
 * ヘッダーコンポーネント
 *
 * アプリケーションタイトルとナビゲーションを表示
 */

import { FolderOpen } from 'lucide-react';

export const Header = () => {
  return (
    <header className="border-b bg-background">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center gap-3">
          <FolderOpen className="h-6 w-6 text-primary" />
          <h1 className="text-2xl font-bold">Reprospective</h1>
          <span className="text-sm text-muted-foreground">
            ファイルシステム監視設定
          </span>
        </div>
      </div>
    </header>
  );
};
