import apiClient from './client';
import type { PaginatedResponse, ScrapeJob } from '@/types';

export async function triggerScrape(brandSlug: string): Promise<ScrapeJob> {
  const { data } = await apiClient.post<ScrapeJob>('/admin/scrape-jobs', {
    brand_slug: brandSlug,
  });
  return data;
}

export interface ScrapeJobParams {
  status?: string;
  brand_slug?: string;
  page?: number;
  per_page?: number;
}

export async function getScrapeJobs(params?: ScrapeJobParams): Promise<PaginatedResponse<ScrapeJob>> {
  const { data } = await apiClient.get<PaginatedResponse<ScrapeJob>>('/admin/scrape-jobs', { params });
  return data;
}

export async function getScrapeJob(id: number): Promise<ScrapeJob> {
  const { data } = await apiClient.get<ScrapeJob>(`/admin/scrape-jobs/${id}`);
  return data;
}

export async function getSupportedBrands(): Promise<{ brands: string[] }> {
  const { data } = await apiClient.get<{ brands: string[] }>('/admin/supported-brands');
  return data;
}
