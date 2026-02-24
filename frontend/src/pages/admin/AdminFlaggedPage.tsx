import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, ChevronDown, ChevronRight } from 'lucide-react';
import { getScrapeJobs } from '@/api/admin';
import type { ScrapeJob, ValidationFlagGroup } from '@/types';

function FlagBadge({ severity }: { severity: string }) {
  const color = severity === 'error'
    ? 'bg-red-100 text-red-700'
    : 'bg-amber-100 text-amber-700';
  return (
    <span className={`inline-block px-2 py-0.5 text-[10px] font-medium rounded ${color}`}>
      {severity}
    </span>
  );
}

function JobFlagGroup({ job }: { job: ScrapeJob }) {
  const [expanded, setExpanded] = useState(false);
  const flags = (job.flags || []) as ValidationFlagGroup[];

  if (flags.length === 0) return null;

  return (
    <div className="border border-neutral-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-white hover:bg-neutral-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <span className="text-sm font-medium text-neutral-900">
            Job #{job.id}
          </span>
          <span className="text-xs text-neutral-400">{job.source}</span>
          <span className="text-xs text-neutral-400">
            {job.completed_at ? new Date(job.completed_at).toLocaleDateString() : ''}
          </span>
        </div>
        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-amber-100 text-amber-700 rounded-full">
          <AlertTriangle size={10} />
          {flags.length} flagged
        </span>
      </button>
      {expanded && (
        <div className="border-t border-neutral-100">
          {flags.map((group, gi) => (
            <div key={gi} className="px-4 py-3 border-b border-neutral-50 last:border-0">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-medium text-neutral-800">{group.name}</span>
                <span className="text-xs text-neutral-400 font-mono">ID: {group.external_id}</span>
              </div>
              <div className="space-y-1.5 ml-4">
                {group.flags.map((flag, fi) => (
                  <div key={fi} className="flex items-center gap-2 text-xs">
                    <FlagBadge severity={flag.severity} />
                    <span className="text-neutral-500 font-mono">{flag.field}</span>
                    <span className="text-neutral-600">{flag.message}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function AdminFlaggedPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ['admin-flagged-jobs', page],
    queryFn: () => getScrapeJobs({ page, per_page: 50 }),
    select: (response) => ({
      ...response,
      data: response.data.filter(
        (j) => j.items_flagged != null && j.items_flagged > 0
      ),
    }),
  });

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-bold text-neutral-900">Flagged Items</h1>
        <p className="text-sm text-neutral-500 mt-1">
          Review validation flags from scrape jobs
        </p>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-neutral-400">Loading...</div>
      ) : data?.data.length === 0 ? (
        <div className="text-center py-12">
          <AlertTriangle size={32} className="mx-auto text-neutral-300 mb-2" />
          <p className="text-neutral-400">No flagged items</p>
          <p className="text-xs text-neutral-300 mt-1">All scraped items passed validation</p>
        </div>
      ) : (
        <div className="space-y-3">
          {data?.data.map((job) => (
            <JobFlagGroup key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  );
}
