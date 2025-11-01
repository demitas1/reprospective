/**
 * ディレクトリ編集ダイアログ
 *
 * React Hook Form + Zodバリデーションを使用
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { useUpdateDirectory } from '@/hooks/useUpdateDirectory';
import { directoryUpdateSchema, type DirectoryUpdateFormData } from '@/lib/validators';
import type { Directory } from '@/types/directory';

interface EditDirectoryDialogProps {
  directory: Directory | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const EditDirectoryDialog = ({
  directory,
  open,
  onOpenChange,
}: EditDirectoryDialogProps) => {
  const updateMutation = useUpdateDirectory();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
    setValue,
  } = useForm<DirectoryUpdateFormData>({
    resolver: zodResolver(directoryUpdateSchema),
  });

  const enabled = watch('enabled');

  // directoryが変わったらフォームをリセット
  useEffect(() => {
    if (directory) {
      reset({
        directory_path: directory.directory_path,
        enabled: directory.enabled,
        display_name: directory.display_name || '',
        description: directory.description || '',
      });
    }
  }, [directory, reset]);

  const onSubmit = async (data: DirectoryUpdateFormData) => {
    if (!directory) return;

    setIsSubmitting(true);
    try {
      await updateMutation.mutateAsync({
        id: directory.id,
        data: {
          directory_path: data.directory_path,
          enabled: data.enabled,
          display_name: data.display_name || undefined,
          description: data.description || undefined,
        },
      });
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to update directory:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    reset();
    onOpenChange(false);
  };

  if (!directory) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogClose onClick={handleClose} />
        <DialogHeader>
          <DialogTitle>ディレクトリ情報を編集</DialogTitle>
          <DialogDescription>
            監視対象ディレクトリの設定を変更します
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* ディレクトリパス */}
          <div className="space-y-2">
            <Label htmlFor="edit_directory_path">
              ディレクトリパス <span className="text-red-500">*</span>
            </Label>
            <Input
              id="edit_directory_path"
              placeholder="/home/user/projects"
              {...register('directory_path')}
            />
            {errors.directory_path && (
              <p className="text-sm text-red-500">{errors.directory_path.message}</p>
            )}
          </div>

          {/* 表示名 */}
          <div className="space-y-2">
            <Label htmlFor="edit_display_name">表示名（任意）</Label>
            <Input
              id="edit_display_name"
              placeholder="プロジェクトディレクトリ"
              {...register('display_name')}
            />
            {errors.display_name && (
              <p className="text-sm text-red-500">{errors.display_name.message}</p>
            )}
          </div>

          {/* 説明 */}
          <div className="space-y-2">
            <Label htmlFor="edit_description">説明（任意）</Label>
            <Textarea
              id="edit_description"
              placeholder="このディレクトリについての説明"
              rows={3}
              {...register('description')}
            />
            {errors.description && (
              <p className="text-sm text-red-500">{errors.description.message}</p>
            )}
          </div>

          {/* 有効/無効 */}
          <div className="flex items-center justify-between">
            <Label htmlFor="edit_enabled">監視を有効化</Label>
            <Switch
              id="edit_enabled"
              checked={enabled}
              onCheckedChange={(checked) => setValue('enabled', checked)}
            />
          </div>

          {/* エラーメッセージ */}
          {updateMutation.isError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
              更新に失敗しました:{' '}
              {updateMutation.error instanceof Error
                ? updateMutation.error.message
                : '不明なエラー'}
            </div>
          )}

          {/* ボタン */}
          <div className="flex justify-end gap-2 pt-4">
            <Button
              type="button"
              onClick={handleClose}
              className="bg-secondary text-secondary-foreground hover:bg-secondary/80"
              disabled={isSubmitting}
            >
              キャンセル
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? '更新中...' : '更新'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
