import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://dummy.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'dummy-key';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// If using dummy credentials, mock the auth methods for local testing
if (supabaseUrl === 'https://dummy.supabase.co') {
  let mockUser = null;
  const mockSession = { access_token: 'dummy-token', user: { id: '00000000-0000-0000-0000-000000000000', email: 'test@example.com' } };
  const listeners: Array<(event: string, session: any) => void> = [];

  const notifyListeners = (event: string) => {
    listeners.forEach(cb => cb(event, mockUser ? mockSession : null));
  };

  supabase.auth.signUp = async () => {
    mockUser = mockSession.user;
    notifyListeners('SIGNED_IN');
    return { data: { user: mockUser, session: mockSession }, error: null } as any;
  };
  supabase.auth.signInWithPassword = async () => {
    mockUser = mockSession.user;
    notifyListeners('SIGNED_IN');
    return { data: { user: mockUser, session: mockSession }, error: null } as any;
  };
  supabase.auth.signOut = async () => {
    mockUser = null;
    notifyListeners('SIGNED_OUT');
    return { error: null };
  };
  supabase.auth.getSession = async () => {
    return { data: { session: mockUser ? mockSession : null }, error: null } as any;
  };
  supabase.auth.onAuthStateChange = (callback) => {
    listeners.push(callback);
    setTimeout(() => callback('INITIAL_SESSION', mockUser ? mockSession as any : null), 10);
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
