/**
 * 監視対象ディレクトリ削除フック
 *
 * React Queryの楽観的更新を実装
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteDirectory } from '@/api/directories';
import { directoriesKeys } from './useDirectories';
import type { Directory } from '@/types/directory';

/**
 * 監視対象ディレクトリ削除
 *
 * @returns React Queryのミューテーション結果
 */
export const useDeleteDirectory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDirectory,
    onMutate: async (id: number) => {
      // 進行中のクエリをキャンセル
      await queryClient.cancelQueries({ queryKey: directoriesKeys.list() });

      // 現在のデータを保存（ロールバック用）
      const previousDirectories = queryClient.getQueryData<Directory[]>(
        directoriesKeys.list()
      );

      // 楽観的更新: ディレクトリを削除
      if (previousDirectories) {
        const filteredDirectories = previousDirectories.filter((dir) => dir.id !== id);

        queryClient.setQueryData<Directory[]>(
          directoriesKeys.list(),
          filteredDirectories
        );
      }

      return { previousDirectories };
    },
    onError: (err, id, context) => {
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
