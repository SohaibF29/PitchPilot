import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://dummy.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'dummy-key';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// If using dummy credentials, mock the auth methods for local testing
if (supabaseUrl === 'https://dummy.supabase.co') {
  let mockUser = typeof window !== 'undefined' && sessionStorage.getItem('mockUser') 
    ? JSON.parse(sessionStorage.getItem('mockUser') as string) 
    : null;
    
  const mockSession = { access_token: 'dummy-token', user: { id: '00000000-0000-0000-0000-000000000000', email: 'test@example.com' } };
  const getMockSession = () => mockUser ? { ...mockSession, user: mockUser } : null;

  const setMockUser = (user: any) => {
    mockUser = user;
    if (typeof window !== 'undefined') {
      if (user) sessionStorage.setItem('mockUser', JSON.stringify(user));
      else sessionStorage.removeItem('mockUser');
    }
  };

  const listeners: Array<(event: string, session: any) => void> = [];

  const notifyListeners = (event: string) => {
    listeners.forEach(cb => cb(event, getMockSession()));
  };

  supabase.auth.signUp = async () => {
    setMockUser(mockSession.user);
    notifyListeners('SIGNED_IN');
    return { data: { user: mockUser, session: getMockSession() }, error: null } as any;
  };
  supabase.auth.signInWithPassword = async () => {
    setMockUser(mockSession.user);
    notifyListeners('SIGNED_IN');
    return { data: { user: mockUser, session: getMockSession() }, error: null } as any;
  };
  supabase.auth.signOut = async () => {
    setMockUser(null);
    notifyListeners('SIGNED_OUT');
    return { error: null };
  };
  supabase.auth.getSession = async () => {
    return { data: { session: getMockSession() }, error: null } as any;
  };
  supabase.auth.onAuthStateChange = (callback: any) => {
    listeners.push(callback);
    setTimeout(() => callback('INITIAL_SESSION', getMockSession()), 10);
    return { 
      data: { 
        subscription: { 
          unsubscribe: () => {
            const idx = listeners.indexOf(callback);
            if (idx > -1) listeners.splice(idx, 1);
          } 
        } 
      } 
    } as any;
  };
}
