/**
 * 監視対象ディレクトリ更新フック
 *
 * React Queryの楽観的更新を実装
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateDirectory } from '@/api/directories';
import { directoriesKeys } from './useDirectories';
import type { Directory, DirectoryUpdate } from '@/types/directory';

/**
 * 更新パラメータ型
 */
interface UpdateDirectoryParams {
  id: number;
  data: DirectoryUpdate;
}

/**
 * 監視対象ディレクトリ更新
 *
 * @returns React Queryのミューテーション結果
 */
export const useUpdateDirectory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: UpdateDirectoryParams) => updateDirectory(id, data),
    onMutate: async ({ id, data }: UpdateDirectoryParams) => {
      // 進行中のクエリをキャンセル
      await queryClient.cancelQueries({ queryKey: directoriesKeys.list() });

      // 現在のデータを保存（ロールバック用）
      const previousDirectories = queryClient.getQueryData<Directory[]>(
        directoriesKeys.list()
      );

      // 楽観的更新: ディレクトリを更新
      if (previousDirectories) {
        const updatedDirectories = previousDirectories.map((dir) =>
          dir.id === id
            ? {
                ...dir,
                ...data,
                updated_at: new Date().toISOString(),
              }
            : dir
        );

        queryClient.setQueryData<Directory[]>(
          directoriesKeys.list(),
          updatedDirectories
        );
      }

      return { previousDirectories };
    },
    onError: (err, variables, context) => {
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
