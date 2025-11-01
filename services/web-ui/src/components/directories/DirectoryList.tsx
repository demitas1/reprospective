/**
 * ディレクトリ一覧コンポーネント
 *
 * 監視対象ディレクトリの一覧表示と管理
 */

import { Plus } from 'lucide-react';
import { useState } from 'react';
import { DirectoryCard } from './DirectoryCard';
import { AddDirectoryDialog } from './AddDirectoryDialog';
import { EditDirectoryDialog } from './EditDirectoryDialog';
import { DeleteDirectoryDialog } from './DeleteDirectoryDialog';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { useDirectories } from '@/hooks/useDirectories';
import type { Directory } from '@/types/directory';

export const DirectoryList = () => {
  const { data: directories, isLoading, error } = useDirectories();
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [editingDirectory, setEditingDirectory] = useState<Directory | null>(null);
  const [deletingDirectory, setDeletingDirectory] = useState<Directory | null>(null);

  if (isLoading) {
    return (
      <div className="py-12">
        <LoadingSpinner size="lg" text="ディレクトリ情報を読み込み中..." />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorMessage
        title="データ取得エラー"
        message={
          error instanceof Error
            ? error.message
            : 'ディレクトリ情報の取得に失敗しました'
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">監視対象ディレクトリ</h2>
          <p className="text-sm text-muted-foreground mt-1">
            ファイルシステム監視の対象ディレクトリを管理します
          </p>
        </div>
        <button
          onClick={() => setIsAddDialogOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          新規追加
        </button>
      </div>

      {/* ディレクトリ一覧 */}
      {!directories || directories.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed rounded-lg">
          <p className="text-muted-foreground">
            監視対象ディレクトリが登録されていません
          </p>
          <button
            onClick={() => setIsAddDialogOpen(true)}
            className="mt-4 text-primary hover:underline"
          >
            最初のディレクトリを追加
          </button>
        </div>
      ) : (
        <div className="grid gap-6">
          {directories.map((directory) => (
            <DirectoryCard
              key={directory.id}
              directory={directory}
              onEdit={setEditingDirectory}
              onDelete={setDeletingDirectory}
            />
          ))}
        </div>
      )}

      {/* ダイアログ */}
      <AddDirectoryDialog
        open={isAddDialogOpen}
        onOpenChange={setIsAddDialogOpen}
      />
      <EditDirectoryDialog
        directory={editingDirectory}
        open={editingDirectory !== null}
        onOpenChange={(open) => !open && setEditingDirectory(null)}
      />
      <DeleteDirectoryDialog
        directory={deletingDirectory}
        open={deletingDirectory !== null}
        onOpenChange={(open) => !open && setDeletingDirectory(null)}
      />
    </div>
  );
};
