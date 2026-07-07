import React from 'react';
import { Card } from '../ui/card';

interface GraphVisualizerProps {
  activeNode: string | null;  // Lowercase string (moderator, market_analyst, product_manager, finance_advisor, technical_architect)
  completedNodes: string[];   // Lowercase strings
}

const NODES = [
  { id: 'moderator', label: 'Moderator' },
  { id: 'market_analyst', label: 'Market Analyst' },
  { id: 'product_manager', label: 'Product Manager' },
  { id: 'finance_advisor', label: 'Finance Advisor' },
  { id: 'technical_architect', label: 'Technical Architect' },
];

export const GraphVisualizer: React.FC<GraphVisualizerProps> = ({
  activeNode,
  completedNodes,
}) => {
  return (
    <Card className="p-5">
      <h4 className="text-foreground font-bold text-sm tracking-wide mb-5">
        🗺️ LangGraph Orchestration Flow
      </h4>

      <div className="flex flex-col md:flex-row items-center justify-between gap-4 md:gap-2">
        {NODES.map((node, idx) => {
          const isActive = activeNode === node.id;
          const isCompleted = completedNodes.includes(node.id);

          return (
            <React.Fragment key={node.id}>
              {/* Node Card */}
              <div
                className={`flex-1 w-full md:w-auto text-center p-3 rounded-lg border transition-all duration-300 ${
                  isActive
                    ? 'bg-[#6366f1]/10 border-[#6366f1] text-[#6366f1] shadow-[0_0_12px_rgba(99,102,241,0.15)]'
                    : isCompleted
                    ? 'bg-[#10b981]/5 border-[#10b981]/50 text-[#10b981]'
                    : 'bg-slate-100/50 dark:bg-gray-900/30 border-slate-200 dark:border-gray-800 text-slate-500 dark:text-slate-500'
                }`}
              >
                <div className="text-xs font-bold uppercase tracking-wider">{node.label}</div>
                <div className="text-xxs mt-1">
                  {isActive ? 'Executing...' : isCompleted ? 'Success' : 'Pending'}
                </div>
              </div>

              {/* Arrow Connector */}
              {idx < NODES.length - 1 && (
                <div
                  className={`hidden md:block text-lg font-bold transition-colors duration-300 ${
                    isCompleted ? 'text-[#10b981]' : 'text-slate-300 dark:text-gray-800'
                  }`}
                >
                  ➜
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </Card>
  );
};
export default GraphVisualizer;
