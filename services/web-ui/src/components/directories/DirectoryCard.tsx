/**
 * ディレクトリカードコンポーネント
 *
 * 監視対象ディレクトリの情報を表示するカード
 */

import { Folder, Edit, Trash2, Power, PowerOff } from 'lucide-react';
import { useState } from 'react';
import type { Directory } from '@/types/directory';
import { useToggleDirectory } from '@/hooks/useToggleDirectory';
import { cn } from '@/lib/utils';

interface DirectoryCardProps {
  directory: Directory;
  onEdit: (directory: Directory) => void;
  onDelete: (directory: Directory) => void;
}

export const DirectoryCard = ({
  directory,
  onEdit,
  onDelete,
}: DirectoryCardProps) => {
  const toggleMutation = useToggleDirectory();
  const [isToggling, setIsToggling] = useState(false);

  const handleToggle = async () => {
    setIsToggling(true);
    try {
      await toggleMutation.mutateAsync(directory.id);
    } finally {
      setIsToggling(false);
    }
  };

  return (
    <div
      className={cn(
        'rounded-lg p-6 shadow-md hover:shadow-lg transition-all',
        directory.enabled
          ? 'bg-white'
          : 'bg-gray-50 opacity-60'
      )}
      style={{
        border: directory.enabled ? '2px solid #BFDBFE' : '2px solid #D1D5DB'
      }}
    >
      <div className="flex items-start justify-between gap-4">
        {/* 左側: アイコンと情報 */}
        <div className="flex gap-3 flex-1 min-w-0">
          <Folder
            className={cn(
              'h-5 w-5 mt-0.5 flex-shrink-0',
              directory.enabled ? 'text-primary' : 'text-muted-foreground'
            )}
          />
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-lg truncate">
              {directory.display_name || directory.directory_path.split('/').pop()}
            </h3>
            <p className="text-sm text-muted-foreground truncate" title={directory.directory_path}>
              {directory.directory_path}
            </p>
            {directory.description && (
              <p className="text-sm text-muted-foreground mt-2">
                {directory.description}
              </p>
            )}
            <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
              <span>ID: {directory.id}</span>
              <span>
                作成: {new Date(directory.created_at).toLocaleDateString('ja-JP')}
              </span>
              {directory.enabled && (
                <span className="text-green-600 font-semibold">● 監視中</span>
              )}
              {!directory.enabled && (
                <span className="text-muted-foreground">● 無効</span>
              )}
            </div>
          </div>
        </div>

        {/* 右側: アクションボタン */}
        <div className="flex gap-2 flex-shrink-0">
          <button
            onClick={handleToggle}
            disabled={isToggling}
            className={cn(
              'p-3 rounded-md transition-all border',
              directory.enabled
                ? 'hover:bg-yellow-50 text-yellow-700 border-yellow-200 hover:border-yellow-300'
                : 'hover:bg-green-50 text-green-700 border-green-200 hover:border-green-300',
              isToggling && 'opacity-50 cursor-not-allowed'
            )}
            title={directory.enabled ? '監視を無効化' : '監視を有効化'}
          >
            {directory.enabled ? (
              <PowerOff className="h-5 w-5" />
            ) : (
              <Power className="h-5 w-5" />
            )}
          </button>
          <button
            onClick={() => onEdit(directory)}
            className="p-3 rounded-md hover:bg-blue-50 text-blue-700 border border-blue-200 hover:border-blue-300 transition-all"
            title="編集"
          >
            <Edit className="h-5 w-5" />
          </button>
          <button
            onClick={() => onDelete(directory)}
            className="p-3 rounded-md hover:bg-red-50 text-red-700 border border-red-200 hover:border-red-300 transition-all"
            title="削除"
          >
            <Trash2 className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};
