import { supabase } from '@/lib/supabase';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function apiRequest<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const { data } = await supabase.auth.getSession();
  if (data.session) {
    headers['Authorization'] = `Bearer ${data.session.access_token}`;
  }

  const finalHeaders = {
    ...headers,
    ...(options.headers || {}),
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers: finalHeaders,
    });

    if (!response.ok) {
      let errorMsg = 'An error occurred during the API request.';
      try {
        const errData = await response.json();
        errorMsg = errData.error?.message || errorMsg;
      } catch {}
      throw new Error(errorMsg);
    }

    // Handle empty 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  } catch (err: any) {
    console.warn(`API request failed for ${path}:`, err.message);
    // Suppress Next.js dev error overlays on network failures for GET requests
    if ((path === '/api/meetings' || path === '/api/keys') && (!options.method || options.method === 'GET')) {
      return [] as any;
    }
    if (path === '/api/health') {
      return { status: 'offline' } as any;
    }
    throw new Error(err.message || 'Connection refused: Backend server is offline.');
  }
}

export const api = {
  getMeetings: () => apiRequest<any[]>('/api/meetings'),
  getMeeting: (id: string) => apiRequest<any>(`/api/meetings/${id}`),
  deleteMeeting: (id: string) => apiRequest<void>(`/api/meetings/${id}`, { method: 'DELETE' }),
  createMeeting: (title: string, pitchText: str) =>
    apiRequest<any>('/api/meetings', {
      method: 'POST',
      body: JSON.stringify({ title, pitch_text: pitchText }),
    }),
  clarifyPitch: (title: string, pitchText: str) =>
    apiRequest<{ is_ambiguous: boolean; questions: string[] }>('/api/meetings/clarify', {
      method: 'POST',
      body: JSON.stringify({ title, pitch_text: pitchText }),
    }),
  executeMeeting: (id: string) =>
    apiRequest<any>(`/api/meetings/${id}/execute`, {
      method: 'POST',
    }),
  generateReport: (meetingId: string) =>
    apiRequest<any>(`/api/reports/${meetingId}`, {
      method: 'POST',
    }),
  getKeys: () => apiRequest<any[]>('/api/keys'),
  saveKey: (provider: string, apiKey: str) =>
    apiRequest<any>('/api/keys', {
      method: 'POST',
      body: JSON.stringify({ provider, api_key: apiKey }),
    }),
  saveSessionKey: (provider: string, apiKey: str) =>
    apiRequest<any>('/api/keys/session', {
      method: 'POST',
      body: JSON.stringify({ provider, api_key: apiKey }),
    }),
  deleteKey: (provider: string) =>
    apiRequest<any>(`/api/keys/${provider}`, {
      method: 'DELETE',
    }),
  checkHealth: () => apiRequest<any>('/api/health'),
};
type str = string;
