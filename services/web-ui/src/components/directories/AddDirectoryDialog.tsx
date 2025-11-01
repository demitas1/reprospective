/**
 * ディレクトリ追加ダイアログ
 *
 * React Hook Form + Zodバリデーションを使用
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
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
import { useAddDirectory } from '@/hooks/useAddDirectory';
import { directoryCreateSchema, type DirectoryCreateFormData } from '@/lib/validators';
import { useState } from 'react';

interface AddDirectoryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const AddDirectoryDialog = ({ open, onOpenChange }: AddDirectoryDialogProps) => {
  const addMutation = useAddDirectory();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
    setValue,
  } = useForm<DirectoryCreateFormData>({
    resolver: zodResolver(directoryCreateSchema),
    defaultValues: {
      directory_path: '',
      enabled: true,
      display_name: '',
      description: '',
    },
  });

  const enabled = watch('enabled');

  const onSubmit = async (data: DirectoryCreateFormData) => {
    setIsSubmitting(true);
    try {
      await addMutation.mutateAsync({
        directory_path: data.directory_path,
        enabled: data.enabled,
        display_name: data.display_name || undefined,
        description: data.description || undefined,
      });
      reset();
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to add directory:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogClose onClick={handleClose} />
        <DialogHeader>
          <DialogTitle>監視対象ディレクトリを追加</DialogTitle>
          <DialogDescription>
            新しい監視対象ディレクトリを登録します
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* ディレクトリパス */}
          <div className="space-y-2">
            <Label htmlFor="directory_path">
              ディレクトリパス <span className="text-red-500">*</span>
            </Label>
            <Input
              id="directory_path"
              placeholder="/home/user/projects"
              {...register('directory_path')}
            />
            {errors.directory_path && (
              <p className="text-sm text-red-500">{errors.directory_path.message}</p>
            )}
          </div>

          {/* 表示名 */}
          <div className="space-y-2">
            <Label htmlFor="display_name">表示名（任意）</Label>
            <Input
              id="display_name"
              placeholder="プロジェクトディレクトリ"
              {...register('display_name')}
            />
            {errors.display_name && (
              <p className="text-sm text-red-500">{errors.display_name.message}</p>
            )}
          </div>

          {/* 説明 */}
          <div className="space-y-2">
            <Label htmlFor="description">説明（任意）</Label>
            <Textarea
              id="description"
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
            <Label htmlFor="enabled">監視を有効化</Label>
            <Switch
              id="enabled"
              checked={enabled}
              onCheckedChange={(checked) => setValue('enabled', checked)}
            />
          </div>

          {/* エラーメッセージ */}
          {addMutation.isError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
              追加に失敗しました:{' '}
              {addMutation.error instanceof Error
                ? addMutation.error.message
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
              {isSubmitting ? '追加中...' : '追加'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
