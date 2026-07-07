import React from 'react';
import { motion } from 'motion/react';

interface Agent {
  name: string;
  role: string;
  avatar: string;
  key: string;
}

const AGENTS: Agent[] = [
  { name: 'Moderator', role: 'Agenda & Briefing', avatar: '🎙️', key: 'moderator' },
  { name: 'Market Analyst', role: 'TAM/SAM/SOM & SWOT', avatar: '📈', key: 'market_analyst' },
  { name: 'Product Manager', role: 'MVP & Roadmap', avatar: '📦', key: 'product_manager' },
  { name: 'Finance Advisor', role: 'Unit Economics', avatar: '💰', key: 'finance_advisor' },
  { name: 'Technical Architect', role: 'Tech Stack & Security', avatar: '🛠️', key: 'technical_architect' },
  { name: 'Moderator Review', role: 'Critique & Iteration', avatar: '⚖️', key: 'moderator_review' },
];

interface AgentGridProps {
  activeAgent: string | null;
  completedAgents: string[];
  selectedAgent: string | null;
  onSelectAgent: (agentKey: string | null) => void;
}

export const AgentGrid: React.FC<AgentGridProps> = ({
  activeAgent,
  completedAgents,
  selectedAgent,
  onSelectAgent,
}) => {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
      {AGENTS.map((agent) => {
        const isActive = activeAgent === agent.key;
        const isCompleted = completedAgents.includes(agent.key);
        const isSelected = selectedAgent === agent.key;
        const isClickable = isCompleted || isActive;

        let statusText = 'Idle';
        let ringColor = 'border-gray-200 dark:border-gray-700/30';
        if (isActive) { statusText = 'Analyzing…'; ringColor = 'border-[#6366f1]'; }
        else if (isCompleted) { statusText = 'Complete'; ringColor = 'border-[#10b981]'; }

        return (
          <motion.div
            key={agent.key}
            whileHover={isClickable ? { scale: 1.04, y: -2 } : {}}
            whileTap={isClickable ? { scale: 0.97 } : {}}
            onClick={() => isClickable && onSelectAgent(isSelected ? null : agent.key)}
            className={[
              'relative overflow-hidden rounded-xl p-4 flex flex-col items-center text-center transition-all duration-200 select-none',
              isClickable ? 'cursor-pointer' : 'cursor-default',
              isSelected
                ? 'ring-2 ring-[#6366f1] shadow-lg shadow-indigo-500/20'
                : '',
              'glass-panel',
            ].join(' ')}
          >
            {isActive && (
              <motion.div
                className="absolute inset-0 bg-[#6366f1]/5 pointer-events-none"
                animate={{ opacity: [0.1, 0.25, 0.1] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            )}

            {/* Completed check mark */}
            {isCompleted && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute top-2 right-2 w-4 h-4 rounded-full bg-[#10b981] flex items-center justify-center"
              >
                <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 12 12" stroke="currentColor" strokeWidth={2}>
                  <path d="M2 6l3 3 5-5" />
                </svg>
              </motion.div>
            )}

            {/* Avatar pulse ring */}
            <div className="relative mb-3 mt-1">
              {isActive && (
                <motion.div
                  className="absolute -inset-2 rounded-full bg-[#6366f1]/20 blur-sm"
                  animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.9, 0.5] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              )}
              <div className={`w-14 h-14 rounded-full flex items-center justify-center text-2xl border-2 bg-slate-100 dark:bg-gray-900 ${ringColor} transition-all duration-300`}>
                {agent.avatar}
              </div>
            </div>

            <h4 className="text-foreground font-bold text-xs leading-tight">{agent.name}</h4>
            <p className="text-slate-500 dark:text-slate-400 text-xxs mt-0.5 leading-tight">{agent.role}</p>

            <div className="mt-3">
              <span className={`px-2 py-0.5 rounded-full text-xxs font-semibold tracking-wide ${
                isActive
                  ? 'bg-[#6366f1]/20 text-[#6366f1] animate-pulse'
                  : isCompleted
                  ? 'bg-[#10b981]/15 text-[#10b981]'
                  : 'bg-slate-200/50 dark:bg-gray-800/40 text-slate-500 dark:text-slate-400'
              }`}>
                {statusText}
              </span>
            </div>

            {isClickable && (
              <p className="text-xxs text-slate-400 dark:text-slate-600 mt-1.5">
                {isSelected ? 'Click to close' : 'Click to view'}
              </p>
            )}
          </motion.div>
        );
      })}
    </div>
  );
};

export default AgentGrid;
