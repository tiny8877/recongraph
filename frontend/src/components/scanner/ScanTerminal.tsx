'use client';

import { useRef, useEffect } from 'react';

interface Props {
  lines: string[];
  isRunning: boolean;
}

export default function ScanTerminal({ lines, isRunning }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [lines.length]);

  return (
    <div className="glass-card overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-border-dark">
        <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-accent-green animate-pulse' : 'bg-gray-600'}`} />
        <span className="text-[10px] text-gray-500 uppercase tracking-wider">Scan Output</span>
        <span className="text-[10px] text-gray-600 ml-auto">{lines.length} lines</span>
      </div>
      <div className="bg-bg-primary p-4 h-80 overflow-auto font-mono text-xs leading-relaxed">
        {lines.length === 0 ? (
          <span className="text-gray-600">Waiting for scan output...</span>
        ) : (
          lines.map((line, i) => (
            <div key={i} className="flex py-0.5">
              <span className="text-gray-700 select-none w-10 text-right pr-3 shrink-0">{i + 1}</span>
              <span className={
                line.startsWith('[!]') ? 'text-accent-red' :
                line.startsWith('[+]') ? 'text-accent-green' :
                line.startsWith('[*]') ? 'text-accent-cyan' :
                line.startsWith('[stderr]') ? 'text-accent-orange' :
                'text-gray-400'
              }>
                {line}
              </span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
