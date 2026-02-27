import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Play, CheckCircle, XCircle, Clock, Loader2, Bot } from 'lucide-react';
import { getAgentJobs, triggerAgentResearch, getAgentBrands } from '@/api/agent';
import type { AgentJob } from '@/types';

const STATUS_CONFIG: Record<string, { color: string; icon: typeof Clock }> = {
  pending: { color: 'bg-yellow-100 text-yellow-700', icon: Clock },
  running: { color: 'bg-blue-100 text-blue-700', icon: Loader2 },
  completed: { color: 'bg-green-100 text-green-700', icon: CheckCircle },
  failed: { color: 'bg-red-100 text-red-700', icon: XCircle },
};

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  const Icon = config.icon;
  const isActive = status === 'running';
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full ${config.color}`}>
      <Icon size={12} className={isActive ? 'animate-spin' : ''} />
      {status}
    </span>
  );
}

function formatDuration(startedAt?: string, completedAt?: string): string {
  if (!startedAt) return '—';
  const start = new Date(startedAt).getTime();
  const end = completedAt ? new Date(completedAt).getTime() : Date.now();
  return `${((end - start) / 1000).toFixed(1)}s`;
}

function formatTokens(input?: number, output?: number): string {
  if (!input && !output) return '—';
  const total = (input || 0) + (output || 0);
  if (total > 1000) return `${(total / 1000).toFixed(1)}k`;
  return String(total);
}

function formatCost(cost?: number): string {
  if (!cost) return '—';
  return `$${cost.toFixed(4)}`;
}

const MODEL_OPTIONS = ['qwen3.5-plus', 'qwen-max', 'qwen-plus', 'qwen-plus-latest', 'qwen-turbo'];

export default function AdminAgentPage() {
  const [page, setPage] = useState(1);
  const [selectedBrand, setSelectedBrand] = useState('');
  const [selectedModel, setSelectedModel] = useState('qwen3.5-plus');
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const perPage = 20;

  const { data: brandsData } = useQuery({
    queryKey: ['agent-brands'],
    queryFn: getAgentBrands,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['admin-agent-jobs', page],
    queryFn: () => getAgentJobs({ page, per_page: perPage }),
    refetchInterval: (query) => {
      const jobs = query.state.data?.data;
      const hasActive = jobs?.some((j: AgentJob) =>
        ['pending', 'running'].includes(j.status)
      );
      return hasActive ? 3000 : false;
    },
  });

  const triggerMutation = useMutation({
    mutationFn: () => triggerAgentResearch({
      brand_slug: selectedBrand,
      model: selectedModel,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-agent-jobs'] });
    },
  });

  const brands = brandsData?.brands || [];
  const effectiveBrand = selectedBrand || (brands.length > 0 ? brands[0] : '');

  const totalPages = data ? Math.ceil(data.total / perPage) : 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-neutral-900">Agent Research</h1>
          <p className="text-sm text-neutral-500 mt-1">
            AI-powered brand research across all channels
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={effectiveBrand}
            onChange={(e) => setSelectedBrand(e.target.value)}
            className="px-3 py-2 text-sm border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
          >
            {brands.map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="px-3 py-2 text-sm border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
          >
            {MODEL_OPTIONS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <button
            onClick={() => {
              if (effectiveBrand) {
                setSelectedBrand(effectiveBrand);
                triggerMutation.mutate();
              }
            }}
            disabled={triggerMutation.isPending || !effectiveBrand}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 disabled:opacity-50 transition-colors"
          >
            {triggerMutation.isPending ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Play size={14} />
            )}
            Run Research
          </button>
        </div>
      </div>

      {triggerMutation.isError && (
        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          Failed to trigger research: {(triggerMutation.error as Error).message}
        </div>
      )}

      <div className="bg-white rounded-lg border border-neutral-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-100 bg-neutral-50">
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">ID</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Brand</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Model</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Status</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Tools</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Tokens</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Cost</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Started</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Duration</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {isLoading ? (
              <tr><td colSpan={9} className="px-4 py-8 text-center text-neutral-400">Loading...</td></tr>
            ) : data?.data.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-12 text-center">
                  <Bot size={32} className="mx-auto text-neutral-300 mb-2" />
                  <p className="text-neutral-400">No agent jobs yet</p>
                  <p className="text-xs text-neutral-300 mt-1">Select a brand and click "Run Research" to start</p>
                </td>
              </tr>
            ) : (
              data?.data.map((job) => (
                <tr
                  key={job.id}
                  onClick={() => navigate(`/admin/agent/${job.id}`)}
                  className="hover:bg-neutral-50 transition-colors cursor-pointer"
                >
                  <td className="px-4 py-3 font-mono text-xs text-neutral-500">#{job.id}</td>
                  <td className="px-4 py-3 text-neutral-700 font-medium">{job.brand_slug}</td>
                  <td className="px-4 py-3 text-neutral-500 text-xs">{job.model}</td>
                  <td className="px-4 py-3"><StatusBadge status={job.status} /></td>
                  <td className="px-4 py-3 text-neutral-600">{job.tool_calls ?? '—'}</td>
                  <td className="px-4 py-3 text-neutral-600 text-xs">
                    {formatTokens(job.total_input_tokens, job.total_output_tokens)}
                  </td>
                  <td className="px-4 py-3 text-neutral-600 text-xs">{formatCost(job.total_cost_usd)}</td>
                  <td className="px-4 py-3 text-xs text-neutral-400">
                    {job.started_at ? new Date(job.started_at).toLocaleString() : '—'}
                  </td>
                  <td className="px-4 py-3 text-xs text-neutral-400">
                    {formatDuration(job.started_at, job.completed_at)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-neutral-400">Page {page} of {totalPages}</p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-xs border border-neutral-200 rounded-lg disabled:opacity-30 hover:bg-neutral-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-xs border border-neutral-200 rounded-lg disabled:opacity-30 hover:bg-neutral-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
