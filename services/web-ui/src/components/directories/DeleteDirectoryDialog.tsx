/**
 * ディレクトリ削除確認ダイアログ
 *
 * 削除前の確認ダイアログ
 */

import { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useDeleteDirectory } from '@/hooks/useDeleteDirectory';
import type { Directory } from '@/types/directory';

interface DeleteDirectoryDialogProps {
  directory: Directory | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const DeleteDirectoryDialog = ({
  directory,
  open,
  onOpenChange,
}: DeleteDirectoryDialogProps) => {
  const deleteMutation = useDeleteDirectory();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!directory) return;

    setIsDeleting(true);
    try {
      await deleteMutation.mutateAsync(directory.id);
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to delete directory:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  if (!directory) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogClose onClick={() => onOpenChange(false)} />
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            ディレクトリを削除
          </DialogTitle>
          <DialogDescription>
            この操作は取り消せません。本当に削除しますか？
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* 削除対象の情報 */}
          <div className="rounded-md border border-red-200 bg-red-50 p-4">
            <h3 className="font-semibold text-sm mb-2">削除対象:</h3>
            <p className="text-sm font-mono break-all">{directory.directory_path}</p>
            {directory.display_name && (
              <p className="text-sm text-muted-foreground mt-1">
                ({directory.display_name})
              </p>
            )}
          </div>

          {/* 注意事項 */}
          <div className="text-sm text-muted-foreground space-y-1">
            <p>削除されるのはデータベース上の設定のみです。</p>
            <p>実際のディレクトリとファイルは削除されません。</p>
          </div>

          {/* エラーメッセージ */}
          {deleteMutation.isError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
              削除に失敗しました:{' '}
              {deleteMutation.error instanceof Error
                ? deleteMutation.error.message
                : '不明なエラー'}
            </div>
          )}

          {/* ボタン */}
          <div className="flex justify-end gap-2 pt-4">
            <Button
              type="button"
              onClick={() => onOpenChange(false)}
              className="bg-secondary text-secondary-foreground hover:bg-secondary/80"
              disabled={isDeleting}
            >
              キャンセル
            </Button>
            <Button
              type="button"
              onClick={handleDelete}
              className="bg-red-600 text-white hover:bg-red-700"
              disabled={isDeleting}
            >
              {isDeleting ? '削除中...' : '削除'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
