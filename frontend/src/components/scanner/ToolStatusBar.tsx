'use client';

import type { ToolStatus } from '@/lib/types';

interface Props {
  tools: ToolStatus[];
  installing: string | null;
  onInstall: (name: string) => void;
}

export default function ToolStatusBar({ tools, installing, onInstall }: Props) {
  return (
    <div className="glass-card-elevated p-4 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-accent-cyan via-accent-blue to-accent-purple" />
      <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-3">Tool Status</h3>
      <div className="flex gap-3 flex-wrap">
        {tools.map((tool) => (
          <div key={tool.name} className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
            tool.installed
              ? 'border-accent-green/20 bg-accent-green/5'
              : 'border-accent-red/20 bg-accent-red/5'
          }`}>
            <span className={`w-2 h-2 rounded-full ${tool.installed ? 'bg-accent-green' : 'bg-accent-red'}`} />
            <span className={`text-xs font-semibold ${tool.installed ? 'text-accent-green' : 'text-gray-400'}`}>
              {tool.name}
            </span>
            {tool.installed ? (
              <span className="text-[10px] text-gray-500 max-w-[120px] truncate">{tool.version || 'installed'}</span>
            ) : (
              <button
                onClick={() => onInstall(tool.name)}
                disabled={installing !== null}
                className="text-[10px] px-2 py-0.5 bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20 rounded hover:bg-accent-cyan/20 disabled:opacity-50"
              >
                {installing === tool.name ? 'Installing...' : 'Install'}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
