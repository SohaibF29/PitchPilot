'use client';

import React, { Suspense, useState, useRef, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'motion/react';
import { useMeeting } from '@/hooks/use-meeting';
import { AgentGrid } from '@/components/meeting/agent-grid';
import { AgentDetailPanel } from '@/components/meeting/agent-detail-panel';
import { MetricsPanel } from '@/components/observability/metrics-panel';
import { GraphVisualizer } from '@/components/observability/graph-visualizer';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardTitle } from '@/components/ui/card';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ── Agent colour palette ───────────────────────────────────────────────
const AGENT_COLORS: Record<string, string> = {
  moderator: '#6366f1',
  market_analyst: '#0ea5e9',
  product_manager: '#8b5cf6',
  finance_advisor: '#10b981',
  technical_architect: '#f59e0b',
  moderator_review: '#ef4444',
  user_feedback: '#64748b',
};

const AGENT_LABELS: Record<string, string> = {
  moderator: 'Moderator',
  market_analyst: 'Market Analyst',
  product_manager: 'Product Manager',
  finance_advisor: 'Finance Advisor',
  technical_architect: 'Technical Architect',
  moderator_review: 'Moderator Review',
  user_feedback: 'Your Feedback',
};

// ── Transcript bubble component ────────────────────────────────────────
const TranscriptBubble: React.FC<{
  role: string;
  content: string;
  isLatest: boolean;
  isStreaming: boolean;
  onClick: () => void;
}> = ({ role, content, isLatest, isStreaming, onClick }) => {
  const color = AGENT_COLORS[role] || '#6366f1';
  const label = AGENT_LABELS[role] || role.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  const isUser = role === 'user';

  // Parse JSON content to extract a short preview
  let preview = content;
  try {
    const cleanContent = content.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    const parsed = JSON.parse(cleanContent);
    const firstVal = Object.values(parsed)[0];
    if (typeof firstVal === 'string') preview = firstVal.slice(0, 200) + (firstVal.length > 200 ? '…' : '');
    else if (parsed.feedback) preview = parsed.feedback;
    else preview = cleanContent.slice(0, 200) + (cleanContent.length > 200 ? '…' : '');
  } catch {
    const cleanContent = content.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    preview = cleanContent.slice(0, 200) + (cleanContent.length > 200 ? '…' : '');
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15 }}
      className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
    >
      <div className="flex items-center gap-2 mb-1.5 px-1">
        <div className="w-5 h-5 rounded-full flex items-center justify-center text-xs" style={{ backgroundColor: `${color}22` }}>
          <span style={{ color }}>●</span>
        </div>
        <span className="text-xs font-semibold" style={{ color }}>{label}</span>
        {isStreaming && (
          <span className="text-xs text-slate-400 animate-pulse">thinking…</span>
        )}
      </div>

      <button
        onClick={onClick}
        className={`max-w-[90%] text-left rounded-2xl px-4 py-3 transition-all duration-200 group ${
          isUser
            ? 'bg-indigo-500/10 border border-indigo-500/20 dark:bg-indigo-600/15'
            : 'bg-slate-100/70 dark:bg-gray-800/50 border border-slate-200/50 dark:border-gray-700/20 hover:border-[color:var(--c)] hover:shadow-md'
        }`}
        style={{ ['--c' as any]: `${color}44` }}
      >
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed line-clamp-3">{preview}</p>
        {content.length > 200 && (
          <span className="text-xs font-semibold mt-1 block" style={{ color }}>
            View full analysis →
          </span>
        )}
      </button>
    </motion.div>
  );
};

// ── Main dashboard ─────────────────────────────────────────────────────
function MeetingDashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const meetingId = searchParams.get('id') || '';

  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportReady, setReportReady] = useState(false);
  const [steeringInput, setSteeringInput] = useState('');
  const [steeringSent, setSteeringSent] = useState(false);

  const transcriptRef = useRef<HTMLDivElement | null>(null);

  const {
    meeting,
    activeNode,
    completedNodes,
    transcript,
    agentOutputs,
    agentActivities,
    streamingNode,
    isExecuting,
    error,
    startAnalysis,
    sendSteering,
  } = useMeeting(meetingId);

  // Auto-scroll transcript
  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcript]);

  // Auto-generate report once meeting completes
  useEffect(() => {
    if (meeting?.status === 'completed' && !reportReady && !isGeneratingReport) {
      handleGenerateReport();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meeting?.status]);

  const handleGenerateReport = async () => {
    if (!meetingId || isGeneratingReport) return;
    setIsGeneratingReport(true);
    try {
      await api.generateReport(meetingId);
      setReportReady(true);
      setError(null);
    } catch (err: any) {
      setError(`Failed to generate report: ${err.message}`);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const handleDownloadPDF = () => {
    window.open(`${API_BASE}/api/reports/${meetingId}/download`, '_blank');
  };

  const handleDeleteMeeting = async () => {
    if (!confirm('Are you sure you want to delete this session? This cannot be undone.')) return;
    try {
      await api.deleteMeeting(meetingId);
      router.push('/');
    } catch (err: any) {
      alert(`Failed to delete meeting: ${err.message}`);
    }
  };

  const handleSteering = () => {
    if (!steeringInput.trim()) return;
    const sent = sendSteering(steeringInput.trim());
    if (sent) {
      setSteeringInput('');
      setSteeringSent(true);
      setTimeout(() => setSteeringSent(false), 3000);
    }
  };

  if (!meetingId) {
    return (
      <div className="text-center py-12 text-slate-500 dark:text-slate-400">
        Invalid meeting context.
      </div>
    );
  }

  const isCompleted = meeting?.status === 'completed';
  const isFailed = meeting?.status === 'failed';

  return (
    <div className="space-y-6">
      {/* ── Page header ── */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <span className="text-xs font-bold text-[#6366f1] uppercase tracking-widest block">
            Active Session
          </span>
          <h2 className="text-2xl font-extrabold text-foreground mt-0.5">
            {meeting?.title || 'Boardroom Room'}
          </h2>
          <div className="flex items-center gap-2 mt-1">
            <span className={`w-2 h-2 rounded-full ${isCompleted ? 'bg-emerald-500' : isFailed ? 'bg-red-500' : isExecuting ? 'bg-indigo-500 animate-pulse' : 'bg-slate-400'}`} />
            <span className="text-xs text-slate-500 capitalize">
              {isCompleted ? 'Analysis complete' : isFailed ? 'Failed' : isExecuting ? 'Deliberating…' : meeting?.status || 'Loading'}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button variant="secondary" onClick={handleDeleteMeeting} className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 gap-2 border-red-200 dark:border-red-900/50">
            🗑️ Delete Session
          </Button>
          {isCompleted && (
            <>
              {isGeneratingReport && (
                <Button variant="secondary" disabled className="gap-2">
                  <span className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Generating AI Report…
                </Button>
              )}
              {reportReady && (
                <Button variant="primary" onClick={handleDownloadPDF} className="gap-2">
                  📥 Download PDF Report
                </Button>
              )}
              {!reportReady && !isGeneratingReport && (
                <Button variant="secondary" onClick={handleGenerateReport} className="gap-2">
                  📊 Compile Report
                </Button>
              )}
            </>
          )}
        </div>
      </div>

      {/* ── Error banner ── */}
      {error && (
        <div className="bg-red-950/20 border border-red-900/35 text-red-400 p-3 rounded-xl text-sm">
          ⚠️ {error}
        </div>
      )}

      {/* ── Report generation success banner ── */}
      <AnimatePresence>
        {reportReady && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="bg-emerald-950/20 border border-emerald-900/35 text-emerald-400 p-3 rounded-xl text-sm flex items-center justify-between"
          >
            <span>✅ AI-powered report with DALL·E infographic generated successfully!</span>
            <Button variant="primary" onClick={handleDownloadPDF} className="text-xs py-1.5 px-3">
              📥 Download
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Clickable agent grid ── */}
      <AgentGrid
        activeAgent={activeNode}
        completedAgents={completedNodes}
        selectedAgent={selectedAgent}
        onSelectAgent={setSelectedAgent}
      />

      {/* ── Main layout ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* ── Left panel: Transcript or Detail ── */}
        <div className="lg:col-span-2 space-y-4">
          <AnimatePresence mode="wait">
            {selectedAgent ? (
              <motion.div
                key="detail"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25 }}
              >
                <div className="flex items-center gap-3 mb-3">
                  <button
                    onClick={() => setSelectedAgent(null)}
                    className="flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-indigo-500 transition-colors"
                  >
                    ← Back to Transcript
                  </button>
                </div>
                <AgentDetailPanel
                  agentKey={selectedAgent}
                  content={agentOutputs[selectedAgent] || ''}
                  isStreaming={streamingNode === selectedAgent}
                />
              </motion.div>
            ) : (
              <motion.div
                key="transcript"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.25 }}
              >
                <Card className="flex flex-col" style={{ minHeight: 520 }}>
                  <CardTitle className="mb-4">Boardroom Transcript</CardTitle>

                  {/* Transcript feed */}
                  <div
                    ref={transcriptRef}
                    className="flex-1 overflow-y-auto space-y-5 pr-1 mb-4"
                    style={{ maxHeight: 440 }}
                  >
                    {transcript.length === 0 && !isExecuting ? (
                      <div className="h-64 flex flex-col items-center justify-center text-center text-slate-400">
                        <span className="text-4xl mb-3">💬</span>
                        <p className="text-sm">The boardroom is assembling…</p>
                      </div>
                    ) : (
                      <>
                        {transcript.map((entry, idx) => (
                          <TranscriptBubble
                            key={idx}
                            role={entry.role}
                            content={entry.content}
                            isLatest={idx === transcript.length - 1}
                            isStreaming={streamingNode === entry.role}
                            onClick={() => setSelectedAgent(entry.role)}
                          />
                        ))}

                        {/* Active thinking indicator */}
                        {activeNode && !transcript.find(t => t.role === activeNode) && (
                          <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex flex-col gap-1 px-1"
                          >
                            <div className="flex items-center gap-2">
                              <div className="w-5 h-5 rounded-full flex items-center justify-center text-xs"
                                style={{ backgroundColor: `${AGENT_COLORS[activeNode] || '#6366f1'}22` }}>
                                <span style={{ color: AGENT_COLORS[activeNode] || '#6366f1' }}>●</span>
                              </div>
                              <span className="text-xs font-semibold" style={{ color: AGENT_COLORS[activeNode] || '#6366f1' }}>
                                {AGENT_LABELS[activeNode] || activeNode}
                              </span>
                              <div className="flex gap-1">
                                {[0, 0.2, 0.4].map(delay => (
                                  <motion.div
                                    key={delay}
                                    className="w-1.5 h-1.5 rounded-full bg-indigo-400"
                                    animate={{ y: [0, -4, 0] }}
                                    transition={{ duration: 0.8, repeat: Infinity, delay }}
                                  />
                                ))}
                              </div>
                            </div>
                            
                            {agentActivities[activeNode] && (
                              <motion.div 
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                className="text-xs text-slate-500 dark:text-slate-400 ml-7 italic flex items-center gap-2"
                              >
                                <span className="w-3 h-3 border border-slate-400 border-t-transparent rounded-full animate-spin" />
                                {agentActivities[activeNode]}
                              </motion.div>
                            )}
                          </motion.div>
                        )}
                      </>
                    )}
                  </div>

                  {/* Start Analysis button (if not yet started) */}
                  {meeting?.status === 'created' && (
                    <div className="pt-3 border-t border-slate-200/50 dark:border-gray-800/50">
                      <Button onClick={startAnalysis} disabled={isExecuting} className="w-full py-3 text-base gap-2">
                        {isExecuting ? (
                          <>
                            <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                            Courtroom Deliberating…
                          </>
                        ) : (
                          '🚀 Start Boardroom Analysis'
                        )}
                      </Button>
                    </div>
                  )}
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* ── Right panel: Metrics + Steering ── */}
        <div className="space-y-5">
          <MetricsPanel
            metrics={
              meeting?.metrics || {
                total_tokens: 0,
                prompt_tokens: 0,
                completion_tokens: 0,
                total_latency_ms: 0,
                estimated_cost: 0.0,
                total_retries: 0,
                model: 'gpt-4o',
                agents_completed: completedNodes.length,
                agents_total: 6,
              }
            }
            currentNode={activeNode}
            retryCount={0}
          />

          {/* ── Steer Boardroom ── */}
          <Card>
            <CardTitle className="text-sm mb-3">
              ✍️ Steer the Boardroom
            </CardTitle>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 leading-relaxed">
              Send a directive to the active agents. They will incorporate your feedback into their ongoing analysis.
            </p>
            <textarea
              value={steeringInput}
              onChange={(e) => setSteeringInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.ctrlKey) handleSteering();
              }}
              disabled={!isExecuting}
              rows={3}
              placeholder={isExecuting ? 'e.g. Focus more on enterprise B2B market…' : 'Available during active analysis'}
              className="w-full bg-transparent border border-slate-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm text-foreground placeholder-slate-400 focus:outline-none focus:border-indigo-500 transition-colors resize-none disabled:opacity-40 disabled:cursor-not-allowed"
            />
            <div className="flex items-center justify-between mt-2">
              <span className="text-xs text-slate-400">Ctrl+Enter to send</span>
              <Button
                variant="primary"
                onClick={handleSteering}
                disabled={!isExecuting || !steeringInput.trim()}
                className="text-xs py-1.5 px-3"
              >
                {steeringSent ? '✅ Sent!' : '→ Steer'}
              </Button>
            </div>
          </Card>
        </div>
      </div>

      {/* ── Graph Visualizer Footer ── */}
      <GraphVisualizer activeNode={activeNode} completedNodes={completedNodes} />
    </div>
  );
}

export default function MeetingDashboard() {
  return (
    <Suspense fallback={
      <div className="text-center py-12 text-slate-400 animate-pulse">
        Loading boardroom…
      </div>
    }>
      <MeetingDashboardContent />
    </Suspense>
  );
}
