import React from 'react';
import './globals.css';
import { AnimatedBackground } from '@/components/ui/animated-background';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { AuthProvider } from '@/components/auth/auth-provider';
import { Header } from '@/components/ui/header';

export const metadata = {
  title: 'PitchPilot — AI Boardroom Startup Assessment',
  description: 'Evaluate your startup idea with an elite courtroom of AI advisors.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <script dangerouslySetInnerHTML={{
          __html: `
            try {
              let theme = localStorage.getItem('theme');
              if (theme === 'dark') {
                document.documentElement.classList.add('dark');
              } else {
                document.documentElement.classList.remove('dark');
              }
            } catch (e) {}
          `
        }} />
      </head>
      <body className="bg-transparent text-foreground min-h-screen relative transition-colors duration-300">
        <AuthProvider>
          <AnimatedBackground />
          <Header />
          <main className="max-w-7xl mx-auto px-6 py-8 relative z-10">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
