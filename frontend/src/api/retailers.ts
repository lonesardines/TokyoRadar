import apiClient from './client';
import type { Retailer, PaginatedResponse } from '@/types';

export interface RetailerParams {
  shipping_tier?: string;
  page?: number;
  per_page?: number;
}

export async function getRetailers(params?: RetailerParams): Promise<PaginatedResponse<Retailer>> {
  const { data } = await apiClient.get<PaginatedResponse<Retailer>>('/retailers', { params });
  return data;
}

export async function getRetailer(slug: string): Promise<Retailer> {
  const { data } = await apiClient.get<Retailer>(`/retailers/${slug}`);
  return data;
}
