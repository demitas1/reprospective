/**
 * 監視対象ディレクトリAPI
 *
 * API Gateway (/api/v1/directories/) とのインターフェース
 */

import { apiClient } from './client';
import type { Directory, DirectoryCreate, DirectoryUpdate } from '@/types/directory';

/**
 * APIエンドポイント
 */
const DIRECTORIES_ENDPOINT = '/api/v1/directories/';

/**
 * 全ディレクトリ取得
 *
 * GET /api/v1/directories/
 *
 * @returns 監視対象ディレクトリのリスト
 */
export const getDirectories = async (): Promise<Directory[]> => {
  const response = await apiClient.get<Directory[]>(DIRECTORIES_ENDPOINT);
  return response.data;
};

/**
 * ディレクトリ詳細取得
 *
 * GET /api/v1/directories/{id}
 *
 * @param id - ディレクトリID
 * @returns 監視対象ディレクトリ
 */
export const getDirectory = async (id: number): Promise<Directory> => {
  const response = await apiClient.get<Directory>(`${DIRECTORIES_ENDPOINT}${id}`);
  return response.data;
};

/**
 * ディレクトリ作成
 *
 * POST /api/v1/directories/
 *
 * @param data - 作成するディレクトリデータ
 * @returns 作成された監視対象ディレクトリ
 */
export const createDirectory = async (data: DirectoryCreate): Promise<Directory> => {
  const response = await apiClient.post<Directory>(DIRECTORIES_ENDPOINT, data);
  return response.data;
};

/**
 * ディレクトリ更新（完全更新）
 *
 * PUT /api/v1/directories/{id}
 *
 * @param id - ディレクトリID
 * @param data - 更新するディレクトリデータ
 * @returns 更新された監視対象ディレクトリ
 */
export const updateDirectory = async (
  id: number,
  data: DirectoryUpdate
): Promise<Directory> => {
  const response = await apiClient.put<Directory>(`${DIRECTORIES_ENDPOINT}${id}`, data);
  return response.data;
};

/**
 * ディレクトリ有効/無効切り替え（部分更新）
 *
 * PATCH /api/v1/directories/{id}/toggle
 *
 * @param id - ディレクトリID
 * @returns 更新された監視対象ディレクトリ
 */
export const toggleDirectory = async (id: number): Promise<Directory> => {
  const response = await apiClient.patch<Directory>(
    `${DIRECTORIES_ENDPOINT}${id}/toggle`
  );
  return response.data;
};

/**
 * ディレクトリ削除
 *
 * DELETE /api/v1/directories/{id}
 *
 * @param id - ディレクトリID
 * @returns void
 */
export const deleteDirectory = async (id: number): Promise<void> => {
  await apiClient.delete(`${DIRECTORIES_ENDPOINT}${id}`);
};
