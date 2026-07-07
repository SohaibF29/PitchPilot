'use client';

import React, { useEffect, useRef, useState } from 'react';

interface StreamingTextProps {
  text: string;
  speed?: number; // ms per word
  className?: string;
  onComplete?: () => void;
}

export const StreamingText: React.FC<StreamingTextProps> = ({
  text,
  speed = 28,
  className = '',
  onComplete,
}) => {
  const [displayed, setDisplayed] = useState('');
  const indexRef = useRef(0);
  const prevTextRef = useRef('');
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // If text grew (new content appended), only stream the new part
    if (text.startsWith(prevTextRef.current)) {
      const newPart = text.slice(prevTextRef.current.length);
      const words = newPart.split(' ');
      let wordIdx = 0;

      if (timerRef.current) clearInterval(timerRef.current);

      timerRef.current = setInterval(() => {
        if (wordIdx < words.length) {
          setDisplayed(prev => prev + (prev && words[wordIdx] ? ' ' : '') + words[wordIdx]);
          wordIdx++;
        } else {
          if (timerRef.current) clearInterval(timerRef.current);
          prevTextRef.current = text;
          onComplete?.();
        }
      }, speed);
    } else {
      // Text was reset entirely
      setDisplayed('');
      indexRef.current = 0;
      prevTextRef.current = '';
      const words = text.split(' ');
      let wordIdx = 0;

      if (timerRef.current) clearInterval(timerRef.current);

      timerRef.current = setInterval(() => {
        if (wordIdx < words.length) {
          setDisplayed(prev => prev + (prev ? ' ' : '') + words[wordIdx]);
          wordIdx++;
        } else {
          if (timerRef.current) clearInterval(timerRef.current);
          prevTextRef.current = text;
          onComplete?.();
        }
      }, speed);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text]);

  return (
    <span className={className}>
      {displayed}
      <span className="inline-block w-0.5 h-4 bg-indigo-400 ml-0.5 animate-pulse align-middle" />
    </span>
  );
};

export default StreamingText;
