import apiClient from './client';
import type { PaginatedResponse, AgentJob, SessionData } from '@/types';

export interface AgentJobTriggerParams {
  brand_slug: string;
  model?: string;
}

export async function triggerAgentResearch(params: AgentJobTriggerParams): Promise<AgentJob> {
  const { data } = await apiClient.post<AgentJob>('/admin/agent-jobs', params);
  return data;
}

export interface AgentJobParams {
  status?: string;
  brand_slug?: string;
  page?: number;
  per_page?: number;
}

export async function getAgentJobs(params?: AgentJobParams): Promise<PaginatedResponse<AgentJob>> {
  const { data } = await apiClient.get<PaginatedResponse<AgentJob>>('/admin/agent-jobs', { params });
  return data;
}

export async function getAgentJob(id: number): Promise<AgentJob> {
  const { data } = await apiClient.get<AgentJob>(`/admin/agent-jobs/${id}`);
  return data;
}

export async function getAgentSession(id: number): Promise<SessionData> {
  const { data } = await apiClient.get<SessionData>(`/admin/agent-jobs/${id}/session`);
  return data;
}

export async function getAgentBrands(): Promise<{ brands: string[] }> {
  const { data } = await apiClient.get<{ brands: string[] }>('/admin/agent-brands');
  return data;
}
