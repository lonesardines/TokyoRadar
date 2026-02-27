import { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft, Bot, Clock, CheckCircle, XCircle, Loader2,
  ChevronDown, ChevronRight, Cpu, Wrench, DollarSign,
  Zap, MessageSquare, Hash, Package,
} from 'lucide-react';
import { getAgentJob, getAgentSession } from '@/api/agent';
import type { SessionEntry, SessionSummary } from '@/types';

const STATUS_CONFIG: Record<string, { color: string; icon: typeof Clock; bg: string }> = {
  pending: { color: 'text-yellow-700', icon: Clock, bg: 'bg-yellow-50 border-yellow-200' },
  running: { color: 'text-blue-700', icon: Loader2, bg: 'bg-blue-50 border-blue-200' },
  completed: { color: 'text-green-700', icon: CheckCircle, bg: 'bg-green-50 border-green-200' },
  failed: { color: 'text-red-700', icon: XCircle, bg: 'bg-red-50 border-red-200' },
};

function formatDuration(startedAt?: string, completedAt?: string): string {
  if (!startedAt) return '—';
  const start = new Date(startedAt).getTime();
  const end = completedAt ? new Date(completedAt).getTime() : Date.now();
  const secs = (end - start) / 1000;
  if (secs > 60) return `${(secs / 60).toFixed(1)}m`;
  return `${secs.toFixed(1)}s`;
}

function formatMs(ms: number): string {
  if (ms >= 60000) return `${(ms / 60000).toFixed(1)}m`;
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms)}ms`;
}

function formatTokenCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

function StatCard({ icon: Icon, label, value, sub }: {
  icon: typeof Clock;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="bg-white rounded-lg border border-neutral-200 p-3">
      <div className="flex items-center gap-2 text-neutral-400 mb-1">
        <Icon size={12} />
        <span className="text-[10px] uppercase tracking-wider font-medium">{label}</span>
      </div>
      <div className="text-lg font-semibold text-neutral-900">{value}</div>
      {sub && <div className="text-xs text-neutral-400 mt-0.5">{sub}</div>}
    </div>
  );
}

function SummaryStats({ summary }: { summary: Partial<SessionSummary> }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-6">
      <StatCard
        icon={Cpu}
        label="API Calls"
        value={String(summary.api_calls ?? 0)}
        sub={`${summary.tool_execs ?? 0} tool execs`}
      />
      <StatCard
        icon={Hash}
        label="Total Tokens"
        value={formatTokenCount(summary.total_tokens ?? 0)}
        sub={`${formatTokenCount(summary.total_input_tokens ?? 0)} in / ${formatTokenCount(summary.total_output_tokens ?? 0)} out`}
      />
      <StatCard
        icon={DollarSign}
        label="Total Cost"
        value={`$${(summary.total_cost_usd ?? 0).toFixed(4)}`}
      />
      <StatCard
        icon={Clock}
        label="LLM Latency"
        value={formatMs(summary.total_latency_ms ?? 0)}
        sub={`avg ${formatMs(summary.avg_latency_ms ?? 0)}`}
      />
      <StatCard
        icon={Wrench}
        label="Tool Time"
        value={formatMs(summary.total_tool_duration_ms ?? 0)}
      />
      <StatCard
        icon={Zap}
        label="Total Entries"
        value={String(summary.total_entries ?? 0)}
      />
    </div>
  );
}

function RequestMessages({ messages }: { messages: Array<{ role: string; content?: string; tool_call_id?: string }> }) {
  const [expanded, setExpanded] = useState(false);

  if (!messages || messages.length === 0) return null;

  // Show a compact preview: count of messages by role
  const roleCounts: Record<string, number> = {};
  for (const m of messages) {
    roleCounts[m.role] = (roleCounts[m.role] || 0) + 1;
  }
  const preview = Object.entries(roleCounts).map(([r, c]) => `${c} ${r}`).join(', ');

  return (
    <div className="mt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-neutral-400 hover:text-neutral-600"
      >
        <MessageSquare size={10} />
        Request Messages ({preview})
        {expanded ? <ChevronDown size={10} /> : <ChevronRight size={10} />}
      </button>
      {expanded && (
        <div className="mt-2 space-y-1.5 max-h-96 overflow-auto">
          {messages.map((msg, i) => (
            <div key={i} className={`rounded p-2 text-xs ${
              msg.role === 'system' ? 'bg-purple-50 border border-purple-100' :
              msg.role === 'user' ? 'bg-blue-50 border border-blue-100' :
              msg.role === 'assistant' ? 'bg-neutral-50 border border-neutral-100' :
              msg.role === 'tool' ? 'bg-green-50 border border-green-100' :
              'bg-neutral-50 border border-neutral-100'
            }`}>
              <div className="flex items-center gap-2 mb-1">
                <span className={`font-medium text-[10px] uppercase tracking-wider ${
                  msg.role === 'system' ? 'text-purple-500' :
                  msg.role === 'user' ? 'text-blue-500' :
                  msg.role === 'assistant' ? 'text-neutral-500' :
                  msg.role === 'tool' ? 'text-green-500' :
                  'text-neutral-500'
                }`}>
                  {msg.role}
                </span>
                {msg.tool_call_id && (
                  <span className="text-neutral-300 font-mono text-[10px]">{msg.tool_call_id}</span>
                )}
              </div>
              {msg.content && (
                <pre className="whitespace-pre-wrap text-neutral-600 overflow-auto max-h-48 text-[11px] leading-relaxed">
                  {msg.content}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ApiCallEntry({ entry, index }: { entry: SessionEntry; index: number }) {
  const [expanded, setExpanded] = useState(false);

  const promptTokens = entry.usage?.prompt_tokens || 0;
  const completionTokens = entry.usage?.completion_tokens || 0;
  const totalTokens = promptTokens + completionTokens;

  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
          <Cpu size={14} className="text-blue-600" />
        </div>
        <div className="w-px flex-1 bg-neutral-200 mt-1" />
      </div>
      <div className="flex-1 pb-4">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 text-sm font-medium text-blue-700 hover:text-blue-900 w-full text-left"
        >
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <span>API Call #{index + 1}</span>
          <span className="text-xs font-normal text-neutral-400 flex items-center gap-2 flex-wrap">
            <span>{entry.model}</span>
            {entry.latency_ms != null && <span>{formatMs(entry.latency_ms)}</span>}
            {totalTokens > 0 && <span>{formatTokenCount(totalTokens)} tok</span>}
            {entry.cost_usd != null && entry.cost_usd > 0 && <span>${entry.cost_usd.toFixed(4)}</span>}
            {entry.finish_reason && <span className="text-neutral-300">{entry.finish_reason}</span>}
          </span>
        </button>

        {/* Cumulative bar (always shown) */}
        {(entry.cumulative_input_tokens != null || entry.cumulative_cost_usd != null) && (
          <div className="flex items-center gap-3 mt-1 text-[10px] text-neutral-300 ml-5">
            {entry.cumulative_input_tokens != null && entry.cumulative_output_tokens != null && (
              <span>cumul: {formatTokenCount(entry.cumulative_input_tokens + entry.cumulative_output_tokens)} tok</span>
            )}
            {entry.cumulative_cost_usd != null && (
              <span>cumul cost: ${entry.cumulative_cost_usd.toFixed(4)}</span>
            )}
          </div>
        )}

        {expanded && (
          <div className="mt-2 space-y-3 ml-5">
            {/* Token breakdown */}
            {totalTokens > 0 && (
              <div className="flex items-center gap-4 text-xs text-neutral-500">
                <span className="bg-neutral-50 px-2 py-0.5 rounded">
                  Prompt: {formatTokenCount(promptTokens)}
                </span>
                <span className="bg-neutral-50 px-2 py-0.5 rounded">
                  Completion: {formatTokenCount(completionTokens)}
                </span>
                {entry.cost_usd != null && (
                  <span className="bg-neutral-50 px-2 py-0.5 rounded">
                    Cost: ${entry.cost_usd.toFixed(6)}
                  </span>
                )}
              </div>
            )}

            {/* Request messages */}
            {entry.request_messages && entry.request_messages.length > 0 && (
              <RequestMessages messages={entry.request_messages} />
            )}

            {/* Response content */}
            {entry.content && (
              <div>
                <div className="text-[10px] uppercase tracking-wider text-neutral-400 mb-1">Response Content</div>
                <div className="bg-blue-50 rounded-lg p-3 text-xs text-neutral-700 whitespace-pre-wrap max-h-64 overflow-auto leading-relaxed">
                  {entry.content}
                </div>
              </div>
            )}

            {/* Tool calls requested */}
            {entry.tool_calls && entry.tool_calls.length > 0 && (
              <div>
                <div className="text-[10px] uppercase tracking-wider text-neutral-400 mb-1">
                  Tool Calls Requested ({entry.tool_calls.length})
                </div>
                <div className="space-y-1.5">
                  {entry.tool_calls.map((tc, i) => (
                    <div key={i} className="bg-neutral-50 rounded p-2.5 text-xs border border-neutral-100">
                      <div className="flex items-center gap-2 mb-1">
                        <Wrench size={10} className="text-neutral-400" />
                        <span className="font-medium text-neutral-700">{tc.name}</span>
                        {tc.id && <span className="text-neutral-300 font-mono text-[10px]">{tc.id}</span>}
                      </div>
                      {tc.arguments && (
                        <pre className="text-neutral-500 overflow-auto max-h-40 text-[11px]">
                          {(() => {
                            try {
                              return JSON.stringify(JSON.parse(tc.arguments), null, 2);
                            } catch {
                              return tc.arguments;
                            }
                          })()}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ToolExecEntry({ entry }: { entry: SessionEntry }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
          <Wrench size={14} className="text-green-600" />
        </div>
        <div className="w-px flex-1 bg-neutral-200 mt-1" />
      </div>
      <div className="flex-1 pb-4">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 text-sm font-medium text-green-700 hover:text-green-900 w-full text-left"
        >
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <span>{entry.name || 'Tool'}</span>
          <span className="text-xs font-normal text-neutral-400">
            {entry.duration_ms != null ? formatMs(entry.duration_ms) : ''}
          </span>
        </button>

        {expanded && (
          <div className="mt-2 space-y-2 ml-5">
            {entry.input != null && (
              <div>
                <div className="text-[10px] uppercase tracking-wider text-neutral-400 mb-1">Input</div>
                <pre className="bg-neutral-50 rounded-lg p-3 text-[11px] text-neutral-600 overflow-auto max-h-48 border border-neutral-100">
                  {typeof entry.input === 'string'
                    ? entry.input
                    : JSON.stringify(entry.input, null, 2)}
                </pre>
              </div>
            )}
            {entry.output != null && (
              <div>
                <div className="text-[10px] uppercase tracking-wider text-neutral-400 mb-1">Output</div>
                <pre className="bg-green-50 rounded-lg p-3 text-[11px] text-neutral-600 overflow-auto max-h-48 border border-green-100">
                  {typeof entry.output === 'string'
                    ? entry.output
                    : JSON.stringify(entry.output, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function TimelineEntry({ entry, apiCallIndex }: { entry: SessionEntry; apiCallIndex: number }) {
  if (entry.type === 'api_call') {
    return <ApiCallEntry entry={entry} index={apiCallIndex} />;
  }
  return <ToolExecEntry entry={entry} />;
}

export default function AdminAgentSessionPage() {
  const { id } = useParams<{ id: string }>();
  const jobId = Number(id);

  const { data: job, isLoading: jobLoading } = useQuery({
    queryKey: ['agent-job', jobId],
    queryFn: () => getAgentJob(jobId),
    refetchInterval: (query) => {
      const j = query.state.data;
      return j && ['pending', 'running'].includes(j.status) ? 3000 : false;
    },
  });

  const isRunning = job?.status === 'running';

  const { data: session, isLoading: sessionLoading } = useQuery({
    queryKey: ['agent-session', jobId],
    queryFn: () => getAgentSession(jobId),
    enabled: !!job && job.status !== 'pending',
    refetchInterval: () => {
      if (!isRunning) return false;
      return 2000;  // poll every 2s while running for near-realtime feel
    },
  });

  if (jobLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 size={24} className="animate-spin text-neutral-400" />
      </div>
    );
  }

  if (!job) {
    return (
      <div className="text-center py-20">
        <p className="text-neutral-400">Job not found</p>
      </div>
    );
  }

  const statusConfig = STATUS_CONFIG[job.status] || STATUS_CONFIG.pending;
  const StatusIcon = statusConfig.icon;
  const finalText = job.result?.final_text as string | undefined;
  const hasSnapshot = job.status === 'completed' && job.result?.snapshot;

  // Compute apiCallIndex for each entry
  let apiCallCounter = 0;
  const entriesWithIndex = (session?.entries || []).map((entry) => {
    if (entry.type === 'api_call') {
      return { entry, apiCallIndex: apiCallCounter++ };
    }
    return { entry, apiCallIndex: -1 };
  });

  // Auto-scroll to bottom of timeline when new entries appear during running
  const timelineEndRef = useRef<HTMLDivElement>(null);
  const prevEntryCount = useRef(0);
  useEffect(() => {
    const currentCount = entriesWithIndex.length;
    if (isRunning && currentCount > prevEntryCount.current) {
      timelineEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    prevEntryCount.current = currentCount;
  }, [entriesWithIndex.length, isRunning]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <Link
          to="/admin/agent"
          className="inline-flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-900"
        >
          <ArrowLeft size={14} />
          Back to Agent Jobs
        </Link>
        {hasSnapshot && (
          <Link
            to={`/admin/agent/${job.id}/products`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 transition-colors"
          >
            <Package size={14} />
            View Products
          </Link>
        )}
      </div>

      {/* Job Overview Card */}
      <div className={`rounded-lg border p-5 mb-6 ${statusConfig.bg}`}>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <Bot size={20} className={statusConfig.color} />
            <div>
              <h1 className="text-lg font-bold text-neutral-900">
                Agent Job #{job.id} — {job.brand_slug}
              </h1>
              <div className="flex items-center gap-3 mt-1 text-sm text-neutral-500">
                <span>{job.model}</span>
                <span className="flex items-center gap-1">
                  <StatusIcon size={12} className={job.status === 'running' ? 'animate-spin' : ''} />
                  {job.status}
                </span>
                <span>Duration: {formatDuration(job.started_at, job.completed_at)}</span>
              </div>
            </div>
          </div>
          <div className="text-right text-sm text-neutral-500 space-y-0.5">
            {job.started_at && (
              <div className="text-xs">Started: {new Date(job.started_at).toLocaleString()}</div>
            )}
            {job.completed_at && (
              <div className="text-xs">Completed: {new Date(job.completed_at).toLocaleString()}</div>
            )}
            <div className="text-xs">Created: {new Date(job.created_at).toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* Summary Stats from Session */}
      {session?.summary && <SummaryStats summary={session.summary} />}

      {/* Errors */}
      {job.errors && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-sm font-medium text-red-700 mb-2">Errors</h3>
          <pre className="text-xs text-red-600 whitespace-pre-wrap overflow-auto max-h-48">
            {JSON.stringify(job.errors, null, 2)}
          </pre>
        </div>
      )}

      {/* Result Text */}
      {finalText && (
        <div className="mb-6">
          <h2 className="text-sm font-medium text-neutral-700 mb-2">Research Result</h2>
          <div className="bg-white rounded-lg border border-neutral-200 p-4 text-sm text-neutral-700 whitespace-pre-wrap max-h-[32rem] overflow-auto leading-relaxed">
            {finalText}
          </div>
        </div>
      )}

      {/* Full Result JSON (if has fields beyond final_text) */}
      {job.result && Object.keys(job.result).length > (finalText ? 1 : 0) && (
        <div className="mb-6">
          <details>
            <summary className="text-sm font-medium text-neutral-500 cursor-pointer hover:text-neutral-700">
              Full Result JSON
            </summary>
            <pre className="mt-2 bg-white rounded-lg border border-neutral-200 p-4 text-xs text-neutral-600 overflow-auto max-h-64">
              {JSON.stringify(job.result, null, 2)}
            </pre>
          </details>
        </div>
      )}

      {/* Session Timeline */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <h2 className="text-sm font-medium text-neutral-700">
            Session Timeline
          </h2>
          {isRunning && (
            <span className="inline-flex items-center gap-1.5 text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
              </span>
              Live
            </span>
          )}
        </div>

        {sessionLoading && entriesWithIndex.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={20} className="animate-spin text-neutral-400" />
          </div>
        ) : entriesWithIndex.length > 0 ? (
          <div className="bg-white rounded-lg border border-neutral-200 p-4">
            {entriesWithIndex.map(({ entry, apiCallIndex }, i) => (
              <TimelineEntry key={i} entry={entry} apiCallIndex={apiCallIndex} />
            ))}
            {isRunning && (
              <div className="flex gap-3 items-center pt-2">
                <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
                  <Loader2 size={14} className="animate-spin text-blue-400" />
                </div>
                <span className="text-sm text-neutral-400">Agent is working...</span>
              </div>
            )}
            <div ref={timelineEndRef} />
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-neutral-200 p-8 text-center text-neutral-400 text-sm">
            {job.status === 'pending'
              ? 'Session will appear once the job starts running...'
              : isRunning
                ? <span className="flex items-center justify-center gap-2"><Loader2 size={14} className="animate-spin" /> Waiting for first event...</span>
                : 'No session data available'}
          </div>
        )}
      </div>
    </div>
  );
}
