export interface AgentOutput {
  agent_name: string;
  content: string;
  tokens_used: number;
  prompt_tokens: number;
  completion_tokens: number;
  latency_ms: number;
  model: string;
  retry_count: number;
  timestamp: string;
}

export interface TranscriptEntry {
  role: string;
  content: string;
  timestamp: string;
  is_voice: boolean;
}

export interface MeetingMetrics {
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_latency_ms: number;
  estimated_cost: number;
  total_retries: number;
  model: string;
  agents_completed: number;
  agents_total: number;
}

export interface Meeting {
  id: string;
  user_id: string | null;
  title: string;
  pitch_text: string;
  status: 'created' | 'in_progress' | 'completed' | 'failed' | 'interrupted';
  thread_id: string;
  agent_outputs: Record<string, AgentOutput>;
  transcript: TranscriptEntry[];
  metrics: MeetingMetrics;
  created_at: string;
  completed_at: string | null;
  updated_at: string;
}
