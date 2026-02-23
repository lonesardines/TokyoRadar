import apiClient from './client';
import type { ProxyService, PaginatedResponse } from '@/types';

export async function getProxyServices(): Promise<ProxyService[]> {
  const { data } = await apiClient.get<PaginatedResponse<ProxyService>>('/proxy-services');
  return data.data;
}

export async function getProxyService(slug: string): Promise<ProxyService> {
  const { data } = await apiClient.get<ProxyService>(`/proxy-services/${slug}`);
  return data;
}
