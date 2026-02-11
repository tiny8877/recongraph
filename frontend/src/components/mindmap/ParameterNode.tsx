'use client';

import { useState } from 'react';
import type { MindmapParameter } from '@/lib/types';

interface Props {
  param: MindmapParameter;
}

export default function ParameterNode({ param }: Props) {
  const [expanded, setExpanded] = useState(false);

  const riskColor =
    param.risk_score >= 8
      ? 'text-red-400 bg-red-500/20 border-red-500/30'
      : param.risk_score >= 5
        ? 'text-orange-400 bg-orange-500/20 border-orange-500/30'
        : 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30';

  return (
    <div className="border border-border-dark rounded-lg bg-bg-primary/50 hover:bg-bg-primary/80 transition-colors">
      {/* Header row */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-3 py-2 text-left"
      >
        <span className="text-gray-500 text-xs">{expanded ? '▾' : '▸'}</span>
        <span className="font-mono text-sm text-accent-cyan flex-1 truncate">{param.name}</span>
        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${riskColor}`}>
          {param.risk_score}/10
        </span>
        <span className="text-[10px] text-gray-500">{param.urls.length} URL{param.urls.length !== 1 ? 's' : ''}</span>
      </button>

      {/* Expanded details */}
      {expanded && (
        <div className="px-3 pb-3 space-y-2 border-t border-border-dark pt-2">
          {/* Sample value */}
          {param.sample_value && (
            <div>
              <span className="text-[10px] text-gray-500 uppercase tracking-wider">Sample Value</span>
              <p className="text-xs text-gray-400 font-mono mt-0.5 break-all">{param.sample_value}</p>
            </div>
          )}

          {/* Attack types */}
          <div className="flex flex-wrap gap-1">
            {param.attack_types.map((at) => (
              <span key={at} className="text-[10px] px-1.5 py-0.5 bg-accent-red/10 text-accent-red rounded border border-accent-red/20">
                {at}
              </span>
            ))}
          </div>

          {/* URLs */}
          <div>
            <span className="text-[10px] text-gray-500 uppercase tracking-wider">Found In</span>
            <div className="mt-1 space-y-1 max-h-40 overflow-y-auto">
              {param.urls.map((url, i) => (
                <div key={i} className="flex items-center gap-2 group">
                  <p className="text-xs text-gray-400 font-mono truncate flex-1" title={url.full_url}>
                    {url.full_url}
                  </p>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      navigator.clipboard.writeText(url.full_url);
                    }}
                    className="text-[10px] text-gray-600 hover:text-accent-cyan opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                    title="Copy URL"
                  >
                    copy
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
