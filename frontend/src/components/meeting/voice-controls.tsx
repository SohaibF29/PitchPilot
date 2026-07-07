import React, { useState } from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { motion } from 'motion/react';

interface VoiceControlsProps {
  meetingId: string;
  onTranscriptReceived: (role: string, text: string) => void;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  meetingId,
  onTranscriptReceived,
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  const toggleConnection = () => {
    setIsConnected(!isConnected);
    setIsRecording(!isConnected);
    // In actual implementation, this will initialize web RTC / WebSocket voice connection
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  return (
    <Card className="flex flex-col items-center justify-center p-6 text-center space-y-6">
      <div className="relative">
        {isConnected && isRecording && !isMuted && (
          <motion.div
            className="absolute -inset-4 bg-indigo-500/10 rounded-full blur-md"
            animate={{ scale: [1, 1.25, 1], opacity: [0.3, 0.6, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        )}

        <button
          onClick={toggleConnection}
          className={`w-20 h-20 rounded-full flex items-center justify-center text-4xl border-2 transition-all duration-300 ${
            isConnected
              ? 'bg-indigo-600 border-indigo-400 text-white shadow-lg shadow-indigo-500/25'
              : 'bg-slate-100 dark:bg-gray-800 border-slate-200 dark:border-gray-700 text-slate-500 dark:text-gray-400 hover:border-slate-300 dark:hover:border-gray-500'
          }`}
        >
          {isConnected ? '🎙️' : '🔇'}
        </button>
      </div>

      <div className="space-y-1">
        <h4 className="font-bold text-foreground">
          {isConnected ? 'Voice Session Active' : 'Start Voice Room'}
        </h4>
        <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xs">
          {isConnected
            ? 'Speaking directly to the boardroom. Speak naturally.'
            : 'Initiate a low-latency real-time voice call directly with the AI board members.'}
        </p>
      </div>

      {isConnected && (
        <div className="flex gap-4 w-full">
          <Button
            variant={isMuted ? 'primary' : 'outline'}
            onClick={toggleMute}
            className="flex-1 py-2 text-xs"
          >
            {isMuted ? '🎤 Unmute Mic' : '🔕 Mute Mic'}
          </Button>
          <Button variant="danger" onClick={toggleConnection} className="flex-1 py-2 text-xs">
            Disconnect
          </Button>
        </div>
      )}
    </Card>
  );
};
export default VoiceControls;
