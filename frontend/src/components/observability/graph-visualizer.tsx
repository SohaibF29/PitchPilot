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

import { ArrowDown, Waypoints } from 'lucide-react';

export const GraphVisualizer: React.FC<GraphVisualizerProps> = ({
  activeNode,
  completedNodes,
}) => {
  return (
    <Card className="p-4 bg-slate-50/50 dark:bg-gray-900/20 border-slate-200/50 dark:border-gray-800/50">
      <div className="flex items-center gap-2 mb-4">
        <Waypoints size={16} className="text-indigo-500" />
        <h4 className="text-foreground font-bold text-sm tracking-wide">
          LangGraph Flow
        </h4>
      </div>

      <div className="flex flex-col gap-1">
        {NODES.map((node, idx) => {
          const isActive = activeNode === node.id;
          const isCompleted = completedNodes.includes(node.id);

          return (
            <React.Fragment key={node.id}>
              {/* Node Card */}
              <div
                className={`flex items-center justify-between p-2.5 rounded-lg border transition-all duration-300 ${
                  isActive
                    ? 'bg-[#6366f1]/10 border-[#6366f1]/50 text-[#6366f1] shadow-[0_0_12px_rgba(99,102,241,0.15)]'
                    : isCompleted
                    ? 'bg-[#10b981]/5 border-[#10b981]/30 text-[#10b981]'
                    : 'bg-white/50 dark:bg-gray-900/30 border-slate-200/50 dark:border-gray-800/50 text-slate-500 dark:text-slate-500'
                }`}
              >
                <div className="text-xs font-bold uppercase tracking-wider">{node.label}</div>
                <div className="text-xxs font-medium">
                  {isActive ? 'Executing...' : isCompleted ? 'Success' : 'Pending'}
                </div>
              </div>

              {/* Arrow Connector */}
              {idx < NODES.length - 1 && (
                <div className="flex justify-center -my-0.5 z-10 relative">
                  <div
                    className={`w-0.5 h-3 ${
                      isCompleted ? 'bg-[#10b981]' : 'bg-slate-200 dark:bg-gray-800'
                    }`}
                  />
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
