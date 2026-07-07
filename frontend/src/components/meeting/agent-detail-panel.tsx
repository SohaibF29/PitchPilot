'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Card } from '../ui/card';
import { StreamingText } from '../ui/streaming-text';

interface AgentDetailPanelProps {
  agentKey: string;
  content: string;
  isStreaming?: boolean;
}

const AGENT_META: Record<string, { name: string; avatar: string; color: string; bgColor: string }> = {
  moderator: { name: 'Moderator', avatar: '🎙️', color: '#6366f1', bgColor: 'rgba(99,102,241,0.08)' },
  market_analyst: { name: 'Market Analyst', avatar: '📈', color: '#0ea5e9', bgColor: 'rgba(14,165,233,0.08)' },
  product_manager: { name: 'Product Manager', avatar: '📦', color: '#8b5cf6', bgColor: 'rgba(139,92,246,0.08)' },
  finance_advisor: { name: 'Finance Advisor', avatar: '💰', color: '#10b981', bgColor: 'rgba(16,185,129,0.08)' },
  technical_architect: { name: 'Technical Architect', avatar: '🛠️', color: '#f59e0b', bgColor: 'rgba(245,158,11,0.08)' },
  moderator_review: { name: 'Moderator Review', avatar: '⚖️', color: '#ef4444', bgColor: 'rgba(239,68,68,0.08)' },
  user_feedback: { name: 'Your Feedback', avatar: '✍️', color: '#64748b', bgColor: 'rgba(100,116,139,0.08)' },
};

// ── Specialised section renderers ───────────────────────────────────────

const SWOTGrid: React.FC<{ swot: { strengths?: string[]; weaknesses?: string[]; opportunities?: string[]; threats?: string[] } }> = ({ swot }) => {
  const cells = [
    { label: 'Strengths', items: swot.strengths || [], color: '#10b981', bg: 'rgba(16,185,129,0.07)' },
    { label: 'Weaknesses', items: swot.weaknesses || [], color: '#ef4444', bg: 'rgba(239,68,68,0.07)' },
    { label: 'Opportunities', items: swot.opportunities || [], color: '#f59e0b', bg: 'rgba(245,158,11,0.07)' },
    { label: 'Threats', items: swot.threats || [], color: '#6366f1', bg: 'rgba(99,102,241,0.07)' },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 mt-3">
      {cells.map(cell => (
        <div key={cell.label} className="rounded-xl p-3" style={{ backgroundColor: cell.bg, border: `1px solid ${cell.color}22` }}>
          <p className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: cell.color }}>{cell.label}</p>
          {cell.items.length > 0 ? (
            <ul className="space-y-1">
              {cell.items.map((item, i) => (
                <li key={i} className="text-xs text-slate-700 dark:text-slate-300 flex gap-1.5">
                  <span style={{ color: cell.color }}>•</span> {item}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-500">—</p>
          )}
        </div>
      ))}
    </div>
  );
};

const RatingBadge: React.FC<{ value: number; max?: number }> = ({ value, max = 10 }) => {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  const color = pct >= 70 ? '#10b981' : pct >= 40 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 rounded-full bg-slate-200 dark:bg-gray-700 overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.9, ease: 'easeOut' }}
        />
      </div>
      <span className="text-sm font-bold" style={{ color }}>{value?.toFixed(1)}/{max}</span>
    </div>
  );
};

const TechBadges: React.FC<{ stack: string }> = ({ stack }) => {
  const tags = stack.split(/[,;\n]+/).map(t => t.trim()).filter(Boolean);
  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {tags.map((tag, i) => (
        <span key={i} className="px-2.5 py-1 rounded-full text-xs font-semibold" style={{ backgroundColor: 'rgba(99,102,241,0.12)', color: '#6366f1' }}>
          {tag}
        </span>
      ))}
    </div>
  );
};

const MetricCard: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="rounded-xl p-3 text-center" style={{ backgroundColor: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)' }}>
    <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">{label}</p>
    <p className="text-base font-bold text-emerald-600 dark:text-emerald-400">{value || '—'}</p>
  </div>
);

// ── Structured renderers per agent ─────────────────────────────────────

const renderModeratorOutput = (data: any) => (
  <div className="space-y-4">
    {data.executive_summary && (
      <div>
        <p className="text-xs font-bold text-indigo-500 uppercase tracking-widest mb-1">Executive Summary</p>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{data.executive_summary}</p>
      </div>
    )}
    {data.key_questions && (
      <div>
        <p className="text-xs font-bold text-indigo-500 uppercase tracking-widest mb-1">Key Questions</p>
        {Array.isArray(data.key_questions) ? (
          <ul className="space-y-1">
            {data.key_questions.map((q: string, i: number) => (
              <li key={i} className="text-sm text-slate-700 dark:text-slate-300 flex gap-2">
                <span className="text-indigo-400 font-bold">{i + 1}.</span> {q}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-700 dark:text-slate-300">{String(data.key_questions)}</p>
        )}
      </div>
    )}
    {data.agenda && (
      <div>
        <p className="text-xs font-bold text-indigo-500 uppercase tracking-widest mb-1">Agenda</p>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{typeof data.agenda === 'string' ? data.agenda : JSON.stringify(data.agenda)}</p>
      </div>
    )}
  </div>
);

const renderMarketAnalystOutput = (data: any) => (
  <div className="space-y-4">
    {data.tam_sam_som && (
      <div>
        <p className="text-xs font-bold text-sky-500 uppercase tracking-widest mb-1">TAM / SAM / SOM</p>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{data.tam_sam_som}</p>
      </div>
    )}
    {data.market_rating !== undefined && (
      <div>
        <p className="text-xs font-bold text-sky-500 uppercase tracking-widest mb-2">Market Rating</p>
        <RatingBadge value={parseFloat(String(data.market_rating))} />
      </div>
    )}
    {data.competitor_analysis && (
      <div>
        <p className="text-xs font-bold text-sky-500 uppercase tracking-widest mb-1">Competitor Analysis</p>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{data.competitor_analysis}</p>
      </div>
    )}
    {data.swot_analysis && (
      <div>
        <p className="text-xs font-bold text-sky-500 uppercase tracking-widest mb-1">SWOT Analysis</p>
        <SWOTGrid swot={data.swot_analysis} />
      </div>
    )}
    {data.detailed_market_review && (
      <div>
        <p className="text-xs font-bold text-sky-500 uppercase tracking-widest mb-1">Detailed Review</p>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{data.detailed_market_review}</p>
      </div>
    )}
  </div>
);

const renderProductManagerOutput = (data: any) => (
  <div className="space-y-4">
    {data.mvp_scope && (
      <div>
        <p className="text-xs font-bold text-violet-500 uppercase tracking-widest mb-1">MVP Scope</p>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{data.mvp_scope}</p>
      </div>
    )}
    {data.product_rating !== undefined && (
      <div>
        <p className="text-xs font-bold text-violet-500 uppercase tracking-widest mb-2">Product–Market Fit Rating</p>
        <RatingBadge value={parseFloat(String(data.product_rating))} />
      </div>
    )}
    {data.roadmap && (
      <div>
        <p className="text-xs font-bold text-violet-500 uppercase tracking-widest mb-1">Roadmap</p>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{typeof data.roadmap === 'string' ? data.roadmap : JSON.stringify(data.roadmap)}</p>
      </div>
    )}
    {data.go_to_market && (
      <div>
        <p className="text-xs font-bold text-violet-500 uppercase tracking-widest mb-1">Go-to-Market Strategy</p>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{data.go_to_market}</p>
      </div>
    )}
  </div>
);

const renderFinanceAdvisorOutput = (data: any) => {
  const metricFields = ['arpu', 'ltv', 'cac', 'churn_rate', 'gross_margin'];
  const foundMetrics = metricFields.filter(f => data[f] !== undefined);

  return (
    <div className="space-y-4">
      {foundMetrics.length > 0 && (
        <div>
          <p className="text-xs font-bold text-emerald-500 uppercase tracking-widest mb-2">Key Metrics</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {foundMetrics.map(f => (
              <MetricCard key={f} label={f.toUpperCase().replace('_', ' ')} value={String(data[f])} />
            ))}
          </div>
        </div>
      )}
      {data.revenue_model && (
        <div>
          <p className="text-xs font-bold text-emerald-500 uppercase tracking-widest mb-1">Revenue Model</p>
          <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{data.revenue_model}</p>
        </div>
      )}
      {data.financial_rating !== undefined && (
        <div>
          <p className="text-xs font-bold text-emerald-500 uppercase tracking-widest mb-2">Financial Rating</p>
          <RatingBadge value={parseFloat(String(data.financial_rating))} />
        </div>
      )}
      {data.funding_requirements && (
        <div>
          <p className="text-xs font-bold text-emerald-500 uppercase tracking-widest mb-1">Funding Requirements</p>
          <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{data.funding_requirements}</p>
        </div>
      )}
    </div>
  );
};

const renderTechnicalArchitectOutput = (data: any) => (
  <div className="space-y-4">
    {data.tech_stack && (
      <div>
        <p className="text-xs font-bold text-amber-500 uppercase tracking-widest mb-1">Recommended Tech Stack</p>
        <TechBadges stack={data.tech_stack} />
      </div>
    )}
    {data.technical_rating !== undefined && (
      <div>
        <p className="text-xs font-bold text-amber-500 uppercase tracking-widest mb-2">Technical Feasibility</p>
        <RatingBadge value={parseFloat(String(data.technical_rating))} />
      </div>
    )}
    {data.scalability && (
      <div>
        <p className="text-xs font-bold text-amber-500 uppercase tracking-widest mb-1">Scalability Assessment</p>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{data.scalability}</p>
      </div>
    )}
    {data.security_considerations && (
      <div>
        <p className="text-xs font-bold text-amber-500 uppercase tracking-widest mb-1">Security Considerations</p>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{data.security_considerations}</p>
      </div>
    )}
    {data.implementation_risks && (
      <div>
        <p className="text-xs font-bold text-amber-500 uppercase tracking-widest mb-1">Implementation Risks</p>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{typeof data.implementation_risks === 'string' ? data.implementation_risks : JSON.stringify(data.implementation_risks)}</p>
      </div>
    )}
  </div>
);

const renderModeratorReview = (data: any) => {
  const decision = data.decision || 'APPROVED';
  const isRevise = decision === 'REVISE';
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span className={`px-4 py-1.5 rounded-full text-sm font-bold tracking-wide ${isRevise ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
          {isRevise ? '🔁 REVISE' : '✅ APPROVED'}
        </span>
        {data.iteration_count !== undefined && (
          <span className="text-xs text-slate-500">Iteration #{data.iteration_count}</span>
        )}
      </div>
      {data.feedback && (
        <div>
          <p className="text-xs font-bold text-red-400 uppercase tracking-widest mb-1">Feedback</p>
          <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{data.feedback}</p>
        </div>
      )}
      {data.strengths_noted && (
        <div>
          <p className="text-xs font-bold text-emerald-500 uppercase tracking-widest mb-1">Strengths Noted</p>
          <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{data.strengths_noted}</p>
        </div>
      )}
    </div>
  );
};

const renderUserFeedback = (data: any) => (
  <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(100,116,139,0.08)', border: '1px solid rgba(100,116,139,0.25)' }}>
    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Your Steering Feedback</p>
    <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed italic">"{data.feedback}"</p>
  </div>
);

const renderGenericOutput = (data: any) => (
  <div className="space-y-3">
    {Object.entries(data).map(([key, val]) => {
      if (val === null || val === undefined) return null;
      const label = key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
      return (
        <div key={key} className="border-l-2 border-indigo-500/30 pl-3">
          <p className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-0.5">{label}</p>
          {typeof val === 'object' ? (
            <pre className="text-xs text-slate-600 dark:text-slate-400 whitespace-pre-wrap">{JSON.stringify(val, null, 2)}</pre>
          ) : (
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{String(val)}</p>
          )}
        </div>
      );
    })}
  </div>
);

// ── Main component ──────────────────────────────────────────────────────

export const AgentDetailPanel: React.FC<AgentDetailPanelProps> = ({
  agentKey,
  content,
  isStreaming = false,
}) => {
  const meta = AGENT_META[agentKey] || { name: agentKey, avatar: '🤖', color: '#6366f1', bgColor: 'rgba(99,102,241,0.08)' };
  const [showRaw, setShowRaw] = useState(false);

  let parsed: any = null;
  try {
    if (content) {
      const cleanContent = content.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      parsed = JSON.parse(cleanContent);
    }
  } catch {
    // not JSON – treat as plaintext
  }

  const renderStructured = () => {
    if (!parsed) return null;
    switch (agentKey) {
      case 'moderator': return renderModeratorOutput(parsed);
      case 'market_analyst': return renderMarketAnalystOutput(parsed);
      case 'product_manager': return renderProductManagerOutput(parsed);
      case 'finance_advisor': return renderFinanceAdvisorOutput(parsed);
      case 'technical_architect': return renderTechnicalArchitectOutput(parsed);
      case 'moderator_review': return renderModeratorReview(parsed);
      case 'user_feedback': return renderUserFeedback(parsed);
      default: return renderGenericOutput(parsed);
    }
  };

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={agentKey}
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.15 }}
      >
        <Card className="overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between mb-5 pb-4 border-b border-slate-200/50 dark:border-gray-700/40">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full flex items-center justify-center text-xl" style={{ backgroundColor: meta.bgColor }}>
                {meta.avatar}
              </div>
              <div>
                <h3 className="font-bold text-foreground text-base">{meta.name}</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {isStreaming ? (
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: meta.color }} />
                      Deliberating…
                    </span>
                  ) : content ? 'Analysis complete' : 'Waiting…'}
                </p>
              </div>
            </div>
            {parsed && (
              <button
                onClick={() => setShowRaw(r => !r)}
                className="text-xs px-3 py-1.5 rounded-lg font-semibold transition-colors duration-200"
                style={{
                  backgroundColor: showRaw ? `${meta.color}20` : 'transparent',
                  color: meta.color,
                  border: `1px solid ${meta.color}33`,
                }}
              >
                {showRaw ? 'Structured' : 'Raw JSON'}
              </button>
            )}
          </div>

          {/* Body */}
          {!content ? (
            <div className="flex items-center justify-center py-12 text-slate-400">
              <span className="text-sm">Waiting for agent to complete…</span>
            </div>
          ) : isStreaming ? (
            <div className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-mono whitespace-pre-wrap">
              <StreamingText text={content.replace(/```json\n?|```\n?/g, '')} speed={10} />
            </div>
          ) : showRaw ? (
            <pre className="text-xs text-slate-600 dark:text-slate-300 whitespace-pre-wrap overflow-x-auto font-mono bg-slate-50 dark:bg-gray-900/50 p-4 rounded-xl">
              {content}
            </pre>
          ) : (
            <div>
              {renderStructured() || (
                <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">{content}</p>
              )}
            </div>
          )}
        </Card>
      </motion.div>
    </AnimatePresence>
  );
};

export default AgentDetailPanel;
