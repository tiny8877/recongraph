'use client';

import { useState, useMemo } from 'react';
import type { MindmapAttackType } from '@/lib/types';
import ParameterNode from './ParameterNode';
import TechniquePanel from './TechniquePanel';

interface Props {
  branch: MindmapAttackType;
  searchQuery: string;
}

export default function AttackTypeBranch({ branch, searchQuery }: Props) {
  const [expanded, setExpanded] = useState(false);

  const filteredParams = useMemo(() => {
    if (!searchQuery) return branch.parameters;
    const q = searchQuery.toLowerCase();
    return branch.parameters.filter((p) => p.name.toLowerCase().includes(q));
  }, [branch.parameters, searchQuery]);

  // Hide entire branch if search yields no results
  if (searchQuery && filteredParams.length === 0) return null;

  const severityColor =
    branch.severity >= 8
      ? 'text-red-400'
      : branch.severity >= 5
        ? 'text-orange-400'
        : 'text-yellow-400';

  const severityBg =
    branch.severity >= 8
      ? 'bg-red-500/10 border-red-500/20'
      : branch.severity >= 5
        ? 'bg-orange-500/10 border-orange-500/20'
        : 'bg-yellow-500/10 border-yellow-500/20';

  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-bg-hover/50 transition-colors"
      >
        {/* Color indicator */}
        <div className="w-1 h-8 rounded-full shrink-0" style={{ backgroundColor: branch.color }} />

        {/* Attack type name */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold" style={{ color: branch.color }}>
              {branch.attack_type}
            </span>
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${severityBg} ${severityColor}`}>
              {branch.severity}/10
            </span>
          </div>
          <p className="text-[10px] text-gray-500 mt-0.5 truncate">{branch.description}</p>
        </div>

        {/* Param count */}
        <div className="text-right shrink-0">
          <span className="text-lg font-bold text-gray-300">{filteredParams.length}</span>
          <p className="text-[10px] text-gray-500">params</p>
        </div>

        {/* Expand icon */}
        <span className="text-gray-500 text-sm shrink-0">{expanded ? '▾' : '▸'}</span>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-border-dark px-4 py-3 space-y-4">
          {/* Parameters section */}
          {filteredParams.length > 0 && (
            <div className="space-y-2">
              <span className="text-[10px] text-gray-500 uppercase tracking-wider">
                Parameters ({filteredParams.length})
              </span>
              <div className="space-y-1">
                {filteredParams.map((param) => (
                  <ParameterNode key={param.name} param={param} />
                ))}
              </div>
            </div>
          )}

          {/* Techniques section */}
          <TechniquePanel techniques={branch.techniques} />
        </div>
      )}
    </div>
  );
}
