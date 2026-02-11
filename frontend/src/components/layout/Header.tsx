'use client';

import { useState } from 'react';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
  const [search, setSearch] = useState('');

  return (
    <header className="h-14 bg-bg-secondary/80 backdrop-blur-sm border-b border-border-dark flex items-center justify-between px-6">
      <div>
        <h1 className="text-lg font-semibold gradient-text-cyan">{title}</h1>
        {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        <div className="relative">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search..."
            className="w-64 h-8 bg-bg-card border border-border-dark rounded-lg px-3 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-accent-cyan/50 transition-colors"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 text-xs">
            /
          </span>
        </div>
      </div>
    </header>
  );
}
