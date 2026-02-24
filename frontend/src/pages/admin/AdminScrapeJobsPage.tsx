import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, RefreshCw, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react';
import { getScrapeJobs, triggerScrape, getSupportedBrands } from '@/api/admin';
import type { ScrapeJob } from '@/types';

const STATUS_CONFIG: Record<string, { color: string; icon: typeof Clock }> = {
  pending: { color: 'bg-yellow-100 text-yellow-700', icon: Clock },
  scraping: { color: 'bg-blue-100 text-blue-700', icon: Loader2 },
  validating: { color: 'bg-blue-100 text-blue-700', icon: Loader2 },
  storing: { color: 'bg-blue-100 text-blue-700', icon: Loader2 },
  completed: { color: 'bg-green-100 text-green-700', icon: CheckCircle },
  failed: { color: 'bg-red-100 text-red-700', icon: XCircle },
};

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  const Icon = config.icon;
  const isActive = ['scraping', 'validating', 'storing'].includes(status);
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full ${config.color}`}>
      <Icon size={12} className={isActive ? 'animate-spin' : ''} />
      {status}
    </span>
  );
}

export default function AdminScrapeJobsPage() {
  const [page, setPage] = useState(1);
  const [selectedBrand, setSelectedBrand] = useState('nanamica');
  const queryClient = useQueryClient();
  const perPage = 20;

  const { data: supportedBrands } = useQuery({
    queryKey: ['supported-brands'],
    queryFn: getSupportedBrands,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['admin-scrape-jobs', page],
    queryFn: () => getScrapeJobs({ page, per_page: perPage }),
    refetchInterval: (query) => {
      const jobs = query.state.data?.data;
      const hasActive = jobs?.some((j: ScrapeJob) =>
        ['pending', 'scraping', 'validating', 'storing'].includes(j.status)
      );
      return hasActive ? 3000 : false;
    },
  });

  const triggerMutation = useMutation({
    mutationFn: triggerScrape,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-scrape-jobs'] });
    },
  });

  const totalPages = data ? Math.ceil(data.total / perPage) : 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-neutral-900">Scrape Jobs</h1>
          <p className="text-sm text-neutral-500 mt-1">
            Manage brand product scraping
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={selectedBrand}
            onChange={(e) => setSelectedBrand(e.target.value)}
            className="px-3 py-2 text-sm border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
          >
            {(supportedBrands?.brands || ['nanamica']).map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
          <button
            onClick={() => triggerMutation.mutate(selectedBrand)}
            disabled={triggerMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 disabled:opacity-50 transition-colors"
          >
            {triggerMutation.isPending ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Play size={14} />
            )}
            Trigger Scrape
          </button>
        </div>
      </div>

      {triggerMutation.isError && (
        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          Failed to trigger scrape: {(triggerMutation.error as Error).message}
        </div>
      )}

      <div className="bg-white rounded-lg border border-neutral-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-100 bg-neutral-50">
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">ID</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Source</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Status</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Found</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Stored</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Flagged</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Started</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Duration</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {isLoading ? (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-neutral-400">Loading...</td></tr>
            ) : data?.data.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center">
                  <RefreshCw size={32} className="mx-auto text-neutral-300 mb-2" />
                  <p className="text-neutral-400">No scrape jobs yet</p>
                  <p className="text-xs text-neutral-300 mt-1">Click "Trigger Scrape" to start</p>
                </td>
              </tr>
            ) : (
              data?.data.map((job) => (
                <tr key={job.id} className="hover:bg-neutral-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-neutral-500">#{job.id}</td>
                  <td className="px-4 py-3 text-neutral-600">{job.source}</td>
                  <td className="px-4 py-3"><StatusBadge status={job.status} /></td>
                  <td className="px-4 py-3 text-neutral-600">{job.items_found ?? '—'}</td>
                  <td className="px-4 py-3 text-neutral-600">{job.items_stored ?? '—'}</td>
                  <td className="px-4 py-3">
                    {job.items_flagged != null && job.items_flagged > 0 ? (
                      <span className="text-amber-600 font-medium">{job.items_flagged}</span>
                    ) : (
                      <span className="text-neutral-400">{job.items_flagged ?? '—'}</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-neutral-400">
                    {job.started_at ? new Date(job.started_at).toLocaleString() : '—'}
                  </td>
                  <td className="px-4 py-3 text-xs text-neutral-400">
                    {job.started_at && job.completed_at
                      ? `${((new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()) / 1000).toFixed(1)}s`
                      : '—'}
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
