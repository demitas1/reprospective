/**
 * 監視対象ディレクトリ追加フック
 *
 * React Queryの楽観的更新（Optimistic Update）を実装
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createDirectory } from '@/api/directories';
import { directoriesKeys } from './useDirectories';
import type { DirectoryCreate, Directory } from '@/types/directory';

/**
 * 監視対象ディレクトリ追加
 *
 * @returns React Queryのミューテーション結果
 */
export const useAddDirectory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createDirectory,
    onMutate: async (newDirectory: DirectoryCreate) => {
      // 進行中のクエリをキャンセル（楽観的更新との競合を防ぐ）
      await queryClient.cancelQueries({ queryKey: directoriesKeys.list() });

      // 現在のデータを保存（ロールバック用）
      const previousDirectories = queryClient.getQueryData<Directory[]>(
        directoriesKeys.list()
      );

      // 楽観的更新: 一時的なディレクトリを追加
      if (previousDirectories) {
        const optimisticDirectory: Directory = {
          id: Date.now(), // 一時的なID
          directory_path: newDirectory.directory_path,
          enabled: newDirectory.enabled ?? true,
          display_name: newDirectory.display_name ?? null,
          description: newDirectory.description ?? null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          created_by: newDirectory.created_by ?? 'api',
          updated_by: 'api',
        };

        queryClient.setQueryData<Directory[]>(
          directoriesKeys.list(),
          [...previousDirectories, optimisticDirectory]
        );
      }

      // ロールバック用のコンテキストを返す
      return { previousDirectories };
    },
    onError: (err, newDirectory, context) => {
      // エラー発生時: 楽観的更新をロールバック
      if (context?.previousDirectories) {
        queryClient.setQueryData(directoriesKeys.list(), context.previousDirectories);
      }
    },
    onSuccess: () => {
      // 成功時: サーバーから最新データを再取得
      queryClient.invalidateQueries({ queryKey: directoriesKeys.list() });
    },
  });
};
