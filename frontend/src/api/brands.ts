import apiClient from './client';
import type { Brand, PaginatedResponse } from '@/types';

export interface BrandParams {
  search?: string;
  style_tag?: string;
  price_range?: string;
  shipping_tier?: string;
  page?: number;
  per_page?: number;
}

export async function getBrands(params?: BrandParams): Promise<PaginatedResponse<Brand>> {
  const { data } = await apiClient.get<PaginatedResponse<Brand>>('/brands', { params });
  return data;
}

export async function getBrand(slug: string): Promise<Brand> {
  const { data } = await apiClient.get<Brand>(`/brands/${slug}`);
  return data;
}
