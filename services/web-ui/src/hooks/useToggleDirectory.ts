/**
 * 監視対象ディレクトリ有効/無効切り替えフック
 *
 * React Queryの楽観的更新を実装
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toggleDirectory } from '@/api/directories';
import { directoriesKeys } from './useDirectories';
import type { Directory } from '@/types/directory';

/**
 * 監視対象ディレクトリ有効/無効切り替え
 *
 * @returns React Queryのミューテーション結果
 */
export const useToggleDirectory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: toggleDirectory,
    onMutate: async (id: number) => {
      // 進行中のクエリをキャンセル
      await queryClient.cancelQueries({ queryKey: directoriesKeys.list() });

      // 現在のデータを保存（ロールバック用）
      const previousDirectories = queryClient.getQueryData<Directory[]>(
        directoriesKeys.list()
      );

      // 楽観的更新: enabled を反転
      if (previousDirectories) {
        const toggledDirectories = previousDirectories.map((dir) =>
          dir.id === id
            ? {
                ...dir,
                enabled: !dir.enabled,
                updated_at: new Date().toISOString(),
              }
            : dir
        );

        queryClient.setQueryData<Directory[]>(
          directoriesKeys.list(),
          toggledDirectories
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
