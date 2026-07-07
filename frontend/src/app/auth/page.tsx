'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { Card, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function AuthPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      if (isLogin) {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
        router.push('/');
      } else {
        const { error } = await supabase.auth.signUp({
          email,
          password,
        });
        if (error) throw error;
        // On success, go directly to API keys page for setup
        router.push('/settings/api-keys?onboarding=true');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh]">
      <section className="text-center space-y-4 max-w-lg mx-auto pt-8 mb-12">
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-foreground">
          Welcome to{' '}
          <span className="bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] bg-clip-text text-transparent">
            PitchPilot
          </span>
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm">
          Sign in to access the AI Boardroom and persist your API credentials securely.
        </p>
      </section>

      <div className="w-full max-w-md">
        <Card>
          <CardTitle className="mb-6">{isLogin ? 'Sign In' : 'Create Account'}</CardTitle>
          
          {error && (
            <div className="bg-red-950/20 border border-red-900/35 text-red-500 p-3 rounded-lg text-xs mb-4">
              {error}
            </div>
          )}
          
          {message && (
            <div className="bg-emerald-950/20 border border-emerald-900/35 text-emerald-500 p-3 rounded-lg text-xs mb-4">
              {message}
            </div>
          )}

          <form onSubmit={handleAuth} className="space-y-5">
            <div className="space-y-2">
              <label className="text-xxs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-inputBg border border-inputBorder rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 text-foreground transition-colors duration-200"
                placeholder="you@example.com"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-xxs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-inputBg border border-inputBorder rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 text-foreground transition-colors duration-200"
                placeholder="••••••••"
              />
            </div>

            <Button type="submit" disabled={loading} className="w-full py-2.5">
              {loading ? 'Authenticating...' : isLogin ? 'Sign In' : 'Sign Up'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError(null);
                setMessage(null);
              }}
              className="text-xs text-indigo-500 hover:text-indigo-600 transition-colors"
            >
              {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
}
