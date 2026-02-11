'use client';

import { useState } from 'react';
import type { MindmapTechnique } from '@/lib/types';

interface Props {
  techniques: MindmapTechnique[];
}

export default function TechniquePanel({ techniques }: Props) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  if (techniques.length === 0) return null;

  const copyAllPayloads = () => {
    const all = techniques.flatMap((t) => t.payloads).join('\n');
    navigator.clipboard.writeText(all);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-gray-500 uppercase tracking-wider">Techniques</span>
        <button
          onClick={copyAllPayloads}
          className="text-[10px] px-2 py-0.5 text-accent-cyan border border-accent-cyan/20 rounded hover:bg-accent-cyan/10 transition-colors"
        >
          Copy All Payloads
        </button>
      </div>

      {techniques.map((tech, idx) => {
        const isExpanded = expandedIdx === idx;
        return (
          <div key={idx} className="border border-border-dark rounded-lg bg-bg-primary/30">
            <button
              onClick={() => setExpandedIdx(isExpanded ? null : idx)}
              className="w-full flex items-center gap-2 px-3 py-2 text-left"
            >
              <span className="text-gray-500 text-xs">{isExpanded ? '▾' : '▸'}</span>
              <span className="text-sm text-gray-200 font-semibold flex-1">{tech.name}</span>
              <span className="text-[10px] text-gray-500">{tech.payloads.length} payloads</span>
            </button>

            {isExpanded && (
              <div className="px-3 pb-3 space-y-3 border-t border-border-dark pt-2">
                <p className="text-xs text-gray-400">{tech.description}</p>

                {/* Payloads */}
                <div>
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider">Payloads</span>
                  <div className="mt-1 space-y-1">
                    {tech.payloads.map((payload, pi) => (
                      <div key={pi} className="flex items-center gap-2 group">
                        <code className="flex-1 text-xs text-accent-green bg-bg-primary px-2 py-1 rounded font-mono break-all">
                          {payload}
                        </code>
                        <button
                          onClick={() => navigator.clipboard.writeText(payload)}
                          className="text-[10px] text-gray-600 hover:text-accent-cyan opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                        >
                          copy
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Tools */}
                <div>
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider">Tools</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {tech.tools.map((tool) => (
                      <span key={tool} className="text-[10px] px-2 py-0.5 bg-accent-purple/10 text-accent-purple rounded border border-accent-purple/20">
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>

                {/* References */}
                {tech.references.length > 0 && (
                  <div>
                    <span className="text-[10px] text-gray-500 uppercase tracking-wider">References</span>
                    <div className="mt-1 space-y-0.5">
                      {tech.references.map((ref, ri) => (
                        <a
                          key={ri}
                          href={ref}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block text-[10px] text-accent-blue hover:text-accent-cyan truncate transition-colors"
                        >
                          {ref}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
