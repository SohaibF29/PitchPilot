import React, { useRef, useEffect } from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { TranscriptEntry } from '@/types/meeting';

interface ChatPanelProps {
  transcript: TranscriptEntry[];
  status: string;
  onStart: () => void;
  isExecuting: boolean;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  transcript,
  status,
  onStart,
  isExecuting,
}) => {
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Auto scroll transcript panel
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript]);

  const formatAgentName = (role: string) => {
    return role
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const renderMessageContent = (role: string, content: string) => {
    if (role === 'user') return <p className="whitespace-pre-wrap">{content}</p>;
    
    // Parse structured JSON from agent nodes
    try {
      const parsed = JSON.parse(content);
      return (
        <div className="space-y-4">
          {Object.entries(parsed).map(([key, val]) => {
            if (typeof val === 'object' && val !== null) return null; // handle arrays/objects separately
            const sectionTitle = key
              .split('_')
              .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
              .join(' ');
            return (
              <div key={key} className="border-l-2 border-indigo-500/35 pl-3">
                <h5 className="text-indigo-600 dark:text-indigo-300 text-xs font-bold uppercase tracking-wider">{sectionTitle}</h5>
                <p className="text-slate-700 dark:text-gray-300 text-sm mt-1 leading-relaxed">{String(val)}</p>
              </div>
            );
          })}
        </div>
      );
    } catch {
      return <p className="text-slate-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed text-sm">{content}</p>;
    }
  };

  return (
    <Card className="flex flex-col h-[550px]">
      {/* Scrollable messages container */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-6 pr-2 mb-4 scrollbar-thin"
      >
        {transcript.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500 dark:text-slate-400">
            <span className="text-4xl mb-3">💬</span>
            <p className="text-sm">The courtroom is idle. Press Start to initiate analysis.</p>
          </div>
        ) : (
          transcript.map((entry, idx) => {
            const isUser = entry.role === 'user';
            return (
              <div
                key={idx}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
              >
                {/* Header */}
                <span className="text-xs text-slate-500 dark:text-slate-400 mb-1 px-1">
                  {isUser ? 'You (Pitch)' : formatAgentName(entry.role)}
                </span>
                
                {/* Bubble */}
                <div
                  className={`max-w-[85%] rounded-xl p-4 ${
                    isUser
                      ? 'bg-indigo-500/10 dark:bg-indigo-600/20 border border-indigo-500/20 text-indigo-950 dark:text-indigo-100'
                      : 'bg-slate-100/80 dark:bg-gray-800/40 border border-slate-200/50 dark:border-gray-700/20 text-slate-800 dark:text-slate-200'
                  }`}
                >
                  {renderMessageContent(entry.role, entry.content)}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Start Analysis Button */}
      {status === 'created' && (
        <div className="pt-4 border-t border-slate-200 dark:border-gray-800/50 flex justify-center">
          <Button
            onClick={onStart}
            disabled={isExecuting}
            className="w-full py-3 text-base flex items-center justify-center gap-2"
          >
            {isExecuting ? 'Courtroom Deliberating...' : '🚀 Start Boardroom Analysis'}
          </Button>
        </div>
      )}
    </Card>
  );
};
export default ChatPanel;
