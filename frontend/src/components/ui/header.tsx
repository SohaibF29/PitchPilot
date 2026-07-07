'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '../auth/auth-provider';
import { supabase } from '@/lib/supabase';
import { ThemeToggle } from './theme-toggle';

export function Header() {
  const { user, loading } = useAuth();

  const handleSignOut = async () => {
    try {
      await supabase.auth.signOut();
    } catch (e) {
      console.warn('Sign out error:', e);
    } finally {
      window.location.href = '/';
    }
  };

  return (
    <header className="border-b border-gray-200 dark:border-gray-800 bg-background/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between transition-colors duration-300">
      <div className="flex items-center gap-3">
        <Link href="/" className="text-2xl font-bold tracking-wide bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] bg-clip-text text-transparent">
          ✈️ PitchPilot
        </Link>
      </div>
      <nav className="flex items-center gap-6">
        <Link href="/" className="text-sm font-semibold text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
          Home
        </Link>
        {user && (
          <Link href="/settings/api-keys" className="text-sm font-semibold text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
            API Keys
          </Link>
        )}
        {!loading && (
          <>
            {user ? (
              <button onClick={handleSignOut} className="text-sm font-semibold text-red-500 hover:text-red-600 transition-colors">
                Sign Out
              </button>
            ) : (
              <Link href="/auth" className="text-sm font-semibold text-[#6366f1] hover:text-[#4f46e5] transition-colors">
                Sign In
              </Link>
            )}
          </>
        )}
        <ThemeToggle />
      </nav>
    </header>
  );
}
