import { useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api';
import { MeetingWSClient } from '@/lib/websocket';
import { Meeting, TranscriptEntry } from '@/types/meeting';

export function useMeeting(meetingId?: string) {
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [completedNodes, setCompletedNodes] = useState<string[]>([]);
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [agentOutputs, setAgentOutputs] = useState<Record<string, string>>({});
  const [agentActivities, setAgentActivities] = useState<Record<string, string>>({});
  const [streamingNode, setStreamingNode] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsClientRef = useRef<MeetingWSClient | null>(null);

  // 1. Fetch initial meeting data
  useEffect(() => {
    if (!meetingId) return;

    const fetchMeeting = async () => {
      try {
        const data = await api.getMeeting(meetingId);
        setMeeting(data);
        setTranscript(data.transcript || []);

        const completed = Object.keys(data.agent_outputs || {});
        setCompletedNodes(completed);

        // Pre-populate agent outputs for completed meetings
        const outputs: Record<string, string> = {};
        for (const [key, val] of Object.entries(data.agent_outputs || {})) {
          outputs[key] = (val as any).content || '';
        }
        setAgentOutputs(outputs);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch meeting info.');
      }
    };

    fetchMeeting();
  }, [meetingId]);

  // 2. Setup WebSocket client
  useEffect(() => {
    if (!meetingId) return;

    const ws = new MeetingWSClient(meetingId, (event) => {
      switch (event.type) {
        case 'meeting.started':
          setIsExecuting(true);
          setError(null);
          break;

        case 'connected':
          // WS handshake confirmed – nothing extra needed
          break;

        case 'agent.started':
          setActiveNode(event.agent);
          setStreamingNode(event.agent);
          break;

        case 'agent.completed':
          setTranscript((prev) => {
            const existing = prev.find(e => e.role === event.agent);
            if (existing) return prev.map(e => e.role === event.agent ? { ...e, content: event.content } : e);
            return [
              ...prev,
              {
                role: event.agent,
                content: event.content,
                timestamp: new Date().toISOString(),
                is_voice: false,
              },
            ];
          });

          setAgentOutputs((prev) => ({ ...prev, [event.agent]: event.content }));
          setCompletedNodes((prev) => [...new Set([...prev, event.agent])]);
          setStreamingNode(null);
          setActiveNode(null);
          setAgentActivities((prev) => {
            const next = { ...prev };
            delete next[event.agent];
            return next;
          });
          break;

        case 'agent.message':
          setAgentOutputs((prev) => {
            const existing = prev[event.agent] || '';
            return { ...prev, [event.agent]: existing + event.content };
          });
          break;

        case 'agent.activity':
          setAgentActivities((prev) => ({ ...prev, [event.agent]: event.activity }));
          break;

        case 'meeting.completed':
          setIsExecuting(false);
          setActiveNode(null);
          setStreamingNode(null);
          setMeeting((prev) =>
            prev ? { ...prev, status: 'completed', metrics: event.metrics } : prev
          );
          break;

        case 'meeting.error':
          setIsExecuting(false);
          setActiveNode(null);
          setStreamingNode(null);
          setError(event.error || 'Boardroom execution failed.');
          break;

        default:
          break;
      }
    });

    ws.connect();
    wsClientRef.current = ws;

    return () => {
      ws.disconnect();
    };
  }, [meetingId]);

  // 3. Auto-start if meeting is in 'created' state
  useEffect(() => {
    if (!meetingId || !meeting || meeting.status !== 'created' || isExecuting) return;
    if (Object.keys(meeting.agent_outputs || {}).length > 0) return; // Don't restart if we already have outputs
    if (!wsClientRef.current) return;

    let intervalId: ReturnType<typeof setInterval> | null = null;

    const attemptStart = () => {
      const success = wsClientRef.current?.startExecution();
      if (success && intervalId) clearInterval(intervalId);
    };

    attemptStart();
    intervalId = setInterval(attemptStart, 150);

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [meetingId, meeting, isExecuting]);

  const startAnalysis = () => {
    wsClientRef.current?.startExecution();
  };

  const sendSteering = (feedback: string): boolean => {
    return wsClientRef.current?.sendInterrupt(feedback) ?? false;
  };

  return {
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
    wsClient: wsClientRef.current,
  };
}
