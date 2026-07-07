'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Card, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/components/auth/auth-provider';
import { ConfirmModal } from '@/components/ui/confirm-modal';

let cachedMeetings: any[] | null = null;

export default function LandingPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [meetings, setMeetings] = useState<any[]>(cachedMeetings || []);
  const [title, setTitle] = useState('');
  const [pitch, setPitch] = useState('');
  const [isLoading, setIsLoading] = useState(!cachedMeetings);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [clarificationQuestions, setClarificationQuestions] = useState<string[]>([]);
  const [clarificationAnswers, setClarificationAnswers] = useState('');

  const [modalConfig, setModalConfig] = useState<{ isOpen: boolean; title: string; description: string; isAlert: boolean; onConfirm: () => void; idToDelete?: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch past pitches and check backend health
  useEffect(() => {
    const fetchHistory = async () => {
      if (!user) return;
      if (!cachedMeetings) setIsLoading(true);
      try {
        const data = await api.getMeetings();
        cachedMeetings = data;
        setMeetings(data);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    const verifyHealth = async () => {
      try {
        const res = await api.checkHealth();
        if (res.status === 'offline') {
          setBackendOnline(false);
        } else {
          setBackendOnline(true);
        }
      } catch (err) {
        setBackendOnline(false);
      }
    };

    fetchHistory();
    verifyHealth();
  }, [user]);

  const handleStartPitch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !pitch) return;

    setIsSubmitting(true);
    try {
      if (clarificationQuestions.length === 0) {
        // Step 1: Check for ambiguity
        const res = await api.clarifyPitch(title, pitch);
        if (res.is_ambiguous && res.questions && res.questions.length > 0) {
          setClarificationQuestions(res.questions);
          setIsSubmitting(false);
          return;
        }
      }

      // Step 2: Proceed with meeting creation
      let finalPitch = pitch;
      if (clarificationQuestions.length > 0 && clarificationAnswers) {
        finalPitch += '\n\n--- Founder Clarifications ---\n' + clarificationAnswers;
      }
      
      const data = await api.createMeeting(title, finalPitch);
      if (cachedMeetings) {
        cachedMeetings = [data, ...cachedMeetings];
      }
      router.push(`/meetings/new?id=${data.id}`);
    } catch (err) {
      console.error(err);
      setModalConfig({
        isOpen: true,
        title: 'Error',
        description: 'Failed to submit pitch.',
        isAlert: true,
        onConfirm: () => setModalConfig(null)
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const confirmDeleteMeeting = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setModalConfig({
      isOpen: true,
      title: 'Delete Session',
      description: 'Are you sure you want to delete this session? This cannot be undone.',
      isAlert: false,
      onConfirm: () => performDeleteMeeting(id),
      idToDelete: id
    });
  };

  const performDeleteMeeting = async (id: string) => {
    setIsDeleting(true);
    try {
      await api.deleteMeeting(id);
      const filtered = meetings.filter(m => m.id !== id);
      setMeetings(filtered);
      cachedMeetings = filtered;
      setModalConfig(null);
    } catch (err: any) {
      setModalConfig({
        isOpen: true,
        title: 'Error',
        description: `Failed to delete meeting: ${err.message}`,
        isAlert: true,
        onConfirm: () => setModalConfig(null)
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className={`space-y-12 ${!user && !authLoading ? 'flex flex-col justify-center min-h-[75vh]' : ''}`}>
      <ConfirmModal
        isOpen={!!modalConfig?.isOpen}
        title={modalConfig?.title || ''}
        description={modalConfig?.description || ''}
        isAlert={modalConfig?.isAlert}
        isLoading={isDeleting}
        confirmText={modalConfig?.isAlert ? 'OK' : 'Delete'}
        onConfirm={() => modalConfig?.onConfirm()}
        onCancel={() => setModalConfig(null)}
      />
      
      {/* Hero Section */}
      <section className="text-center space-y-4 max-w-3xl mx-auto pt-8">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-foreground">
          Pitch to the{' '}
          <span className="bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] bg-clip-text text-transparent">
            AI Boardroom
          </span>
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-lg">
          Submit your startup concept to an elite committee of virtual advisors. Get real-time,
          unbiased critiques on product, market size, finance, and system architecture.
        </p>
      </section>

      {backendOnline === false && (
        <div className="max-w-3xl mx-auto bg-red-950/20 border border-red-900/35 text-red-600 dark:text-red-300 p-4 rounded-lg text-sm text-center">
          ⚠️ <strong>Backend Offline:</strong> The PitchPilot backend server is offline or unreachable. Please start the backend service (run <code>python app/main.py</code> or <code>docker-compose up</code>) to execute boardroom meetings and analyze your pitch.
        </div>
      )}
      {backendOnline === true && (
        <div className="max-w-3xl mx-auto bg-emerald-950/15 border border-emerald-900/30 text-emerald-600 dark:text-emerald-300 p-3 rounded-lg text-xs text-center flex items-center justify-center gap-2">
          <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          Boardroom Connection Established: AI agents ready.
        </div>
      )}

      {authLoading ? (
        <div className="flex justify-center items-center py-12">
          <span className="w-8 h-8 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
        </div>
      ) : !user ? (
        <div className="flex justify-center mt-12">
          <Button onClick={() => router.push('/auth')} className="px-8 py-4 text-lg">
            Sign In or Sign Up to Get Started
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Pitch Input Form */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardTitle>Submit Your Pitch</CardTitle>
              <form onSubmit={handleStartPitch} className="space-y-6 mt-4">
                {clarificationQuestions.length > 0 ? (
                  <div className="space-y-4">
                    <div className="bg-indigo-50 border border-indigo-200 dark:bg-indigo-950/30 dark:border-indigo-800/50 p-4 rounded-xl">
                      <h3 className="text-sm font-bold text-indigo-900 dark:text-indigo-300 mb-2">Wait! We need some clarity before starting the boardroom:</h3>
                      <ul className="list-disc pl-5 text-sm text-indigo-800 dark:text-indigo-200 space-y-1">
                        {clarificationQuestions.map((q, idx) => (
                          <li key={idx}>{q}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="space-y-2 mt-4">
                      <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                        Your Clarifications
                      </label>
                      <textarea
                        required
                        rows={4}
                        placeholder="Answer the questions above..."
                        value={clarificationAnswers}
                        onChange={(e) => setClarificationAnswers(e.target.value)}
                        className="w-full bg-inputBg border border-inputBorder rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-indigo-500 text-foreground transition-colors duration-200"
                      />
                    </div>
                    <div className="flex gap-3 pt-2">
                      <Button type="button" variant="secondary" onClick={() => { setClarificationQuestions([]); setClarificationAnswers(''); }} className="w-1/3">
                        Cancel
                      </Button>
                      <Button type="submit" disabled={isSubmitting} className="w-2/3">
                        {isSubmitting ? (
                          <div className="flex items-center justify-center gap-2">
                            <span className="w-5 h-5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                            <span>Entering Boardroom...</span>
                          </div>
                        ) : (
                          '🚀 Submit Clarifications'
                        )}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                        Startup Title
                      </label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. Uber for Pets"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className="w-full bg-inputBg border border-inputBorder rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-indigo-500 text-foreground transition-colors duration-200"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                        Startup Description / Pitch Text
                      </label>
                      <textarea
                        required
                        rows={8}
                        placeholder="Describe your business model, customer pain points, core solutions, target users, and technical strategy..."
                        value={pitch}
                        onChange={(e) => setPitch(e.target.value)}
                        className="w-full bg-inputBg border border-inputBorder rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-indigo-500 text-foreground transition-colors duration-200"
                      />
                    </div>

                    <Button type="submit" disabled={isSubmitting} className="w-full py-3">
                      {isSubmitting ? (
                        <div className="flex items-center justify-center gap-2">
                          <span className="w-5 h-5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                          <span>Checking pitch for clarity...</span>
                        </div>
                      ) : (
                        '🚀 Submit Startup Pitch'
                      )}
                    </Button>
                  </>
                )}
              </form>
            </Card>
          </div>

          {/* History Sidebar */}
          <div className="space-y-6">
            <Card className="h-full">
              <CardTitle>History & Reports</CardTitle>
              <div className="mt-4 space-y-4 max-h-[400px] overflow-y-auto pr-2 scrollbar-thin">
                {isLoading ? (
                  <div className="text-center py-6 text-slate-500 dark:text-slate-400 text-sm">Loading historical data...</div>
                ) : meetings.length === 0 ? (
                  <div className="text-center py-6 text-slate-500 dark:text-slate-400 text-sm">No historical audits found.</div>
                ) : (
                  meetings.map((meeting) => (
                    <div
                      key={meeting.id}
                      onClick={() => router.push(`/meetings/new?id=${meeting.id}`)}
                      className="p-3 bg-card border border-cardBorder rounded-lg hover:border-indigo-500/50 cursor-pointer transition-all duration-200 flex justify-between items-start group"
                    >
                      <div className="overflow-hidden mr-2">
                        <h5 className="font-bold text-sm text-foreground truncate">{meeting.title}</h5>
                        <p className="text-xxs text-slate-500 dark:text-slate-400 mt-1">
                          {new Date(meeting.created_at).toLocaleDateString()} &bull;{' '}
                          <span className="capitalize">{meeting.status}</span>
                        </p>
                      </div>
                      <button
                        onClick={(e) => confirmDeleteMeeting(meeting.id, e)}
                        className="text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/50 transition-colors p-1.5 rounded-md shrink-0 flex items-center justify-center"
                        title="Delete Session"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                      </button>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
