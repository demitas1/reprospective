/**
 * 監視対象ディレクトリ一覧取得フック
 *
 * React Queryを使用してサーバー状態を管理
 */

import { useQuery } from '@tanstack/react-query';
import { getDirectories } from '@/api/directories';

/**
 * クエリキー
 */
export const directoriesKeys = {
  all: ['directories'] as const,
  lists: () => [...directoriesKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) =>
    [...directoriesKeys.lists(), { filters }] as const,
  details: () => [...directoriesKeys.all, 'detail'] as const,
  detail: (id: number) => [...directoriesKeys.details(), id] as const,
};

/**
 * 監視対象ディレクトリ一覧取得
 *
 * @returns React Queryのクエリ結果
 */
export const useDirectories = () => {
  return useQuery({
    queryKey: directoriesKeys.list(),
    queryFn: getDirectories,
    staleTime: 30000, // 30秒間はキャッシュを使用
    refetchOnWindowFocus: true, // ウィンドウフォーカス時に再取得
  });
};
