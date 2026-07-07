import React from 'react';
import { Card } from '../ui/card';
import { MeetingMetrics } from '@/types/meeting';

interface MetricsPanelProps {
  metrics: MeetingMetrics;
  currentNode: string | null;
  retryCount: number;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({
  metrics,
  currentNode,
  retryCount,
}) => {
  const getProgressPercent = () => {
    if (metrics.agents_total === 0) return 0;
    return (metrics.agents_completed / metrics.agents_total) * 100;
  };

  const formatNodeName = (node: string | null) => {
    if (!node) return 'Idle';
    return node
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <Card className="space-y-6">
      <h3 className="text-foreground font-bold text-lg tracking-wide border-b border-slate-200 dark:border-gray-800 pb-3">
        📊 Performance Diagnostics
      </h3>

      {/* Execution Node & Status */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-100/50 dark:bg-gray-900/40 p-3 rounded-lg border border-slate-200/50 dark:border-gray-800/35">
          <span className="text-slate-500 dark:text-slate-400 text-xxs font-bold uppercase tracking-wider block">Active Node</span>
          <span className="text-indigo-600 dark:text-indigo-400 text-sm font-semibold mt-1 block">
            {formatNodeName(currentNode)}
          </span>
        </div>
        <div className="bg-slate-100/50 dark:bg-gray-900/40 p-3 rounded-lg border border-slate-200/50 dark:border-gray-800/35">
          <span className="text-slate-500 dark:text-slate-400 text-xxs font-bold uppercase tracking-wider block">Retries</span>
          <span
            className={`text-sm font-semibold mt-1 block ${
              retryCount > 0 ? 'text-[#f59e0b]' : 'text-slate-500 dark:text-slate-400'
            }`}
          >
            {retryCount} attempts
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs font-semibold">
          <span className="text-slate-500 dark:text-slate-400">Boardroom Consensus</span>
          <span className="text-indigo-600 dark:text-indigo-400">{metrics.agents_completed}/{metrics.agents_total} Complete</span>
        </div>
        <div className="w-full bg-slate-200/60 dark:bg-gray-900/60 rounded-full h-2 overflow-hidden border border-slate-300/20 dark:border-gray-800/20">
          <div
            className="bg-[#6366f1] h-full rounded-full transition-all duration-500 ease-out"
            style={{ width: `${getProgressPercent()}%` }}
          />
        </div>
      </div>

      {/* Diagnostic Values Grid */}
      <div className="space-y-4 pt-2">
        <div className="flex justify-between items-center text-sm border-b border-slate-200 dark:border-gray-800/40 pb-2">
          <span className="text-slate-500 dark:text-slate-400">Total Latency</span>
          <span className="text-foreground font-mono">
            {metrics.total_latency_ms > 0
              ? `${(metrics.total_latency_ms / 1000).toFixed(2)}s`
              : '0.00s'}
          </span>
        </div>

        <div className="flex justify-between items-center text-sm border-b border-slate-200 dark:border-gray-800/40 pb-2">
          <span className="text-slate-500 dark:text-slate-400">Total Tokens</span>
          <span className="text-foreground font-mono">{metrics.total_tokens.toLocaleString()}</span>
        </div>

        <div className="flex justify-between items-center text-sm border-b border-slate-200 dark:border-gray-800/40 pb-2">
          <span className="text-slate-500 dark:text-slate-400">Input / Output Tokens</span>
          <span className="text-slate-500 dark:text-slate-400 font-mono text-xs">
            {metrics.prompt_tokens.toLocaleString()} / {metrics.completion_tokens.toLocaleString()}
          </span>
        </div>

        <div className="flex justify-between items-center text-sm border-b border-slate-200 dark:border-gray-800/40 pb-2">
          <span className="text-slate-500 dark:text-slate-400">Estimated Cost</span>
          <span className="text-[#10b981] font-mono font-semibold">
            ${metrics.estimated_cost.toFixed(6)}
          </span>
        </div>

        <div className="flex justify-between items-center text-sm">
          <span className="text-slate-500 dark:text-slate-400">LLM Engine</span>
          <span className="text-slate-500 dark:text-slate-400 font-semibold">{metrics.model || 'gpt-4o'}</span>
        </div>
      </div>
    </Card>
  );
};
export default MetricsPanel;
