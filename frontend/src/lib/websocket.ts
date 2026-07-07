import { supabase } from '@/lib/supabase';

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ||
  (process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL.replace(/^http/, 'ws')
    : 'ws://localhost:8000');

export class MeetingWSClient {
  private ws: WebSocket | null = null;
  private meetingId: string;
  private onMessageCallback: (data: any) => void;
  private reconnectAttempts = 0;
  private maxReconnects = 3;

  constructor(meetingId: string, onMessage: (data: any) => void) {
    this.meetingId = meetingId;
    this.onMessageCallback = onMessage;
  }

  async connect(): Promise<void> {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token || '';
    const url = `${WS_BASE_URL}/api/ws/meeting/${this.meetingId}?token=${token}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log(`[WS] Connected for meeting ${this.meetingId}`);
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.onMessageCallback(data);
      } catch (err) {
        console.error('[WS] Error parsing message:', err);
      }
    };

    this.ws.onclose = (event) => {
      console.log(`[WS] Closed for meeting ${this.meetingId}:`, event.code, event.reason);
      // Suppress noisy dev overlay – do NOT re-throw
    };

    this.ws.onerror = () => {
      // Intentionally suppress – onerror fires before onclose and the
      // error object is an empty Event in browsers, not useful.
      // onclose will fire right after with the real info.
    };
  }

  startExecution(): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: 'start' }));
      return true;
    }
    return false;
  }

  sendInterrupt(feedback: string): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: 'interrupt', feedback }));
      return true;
    }
    return false;
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
