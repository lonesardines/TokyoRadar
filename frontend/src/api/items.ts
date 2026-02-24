import apiClient from './client';
import type { ItemDetail, PaginatedResponse, Item } from '@/types';

export interface ItemParams {
  brand_slug?: string;
  search?: string;
  item_type?: string;
  season_code?: string;
  in_stock?: boolean;
  page?: number;
  per_page?: number;
}

export async function getItems(params?: ItemParams): Promise<PaginatedResponse<Item>> {
  const { data } = await apiClient.get<PaginatedResponse<Item>>('/items', { params });
  return data;
}

export async function getItem(id: number): Promise<ItemDetail> {
  const { data } = await apiClient.get<ItemDetail>(`/items/${id}`);
  return data;
}
