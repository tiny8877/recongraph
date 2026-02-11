'use client';

import type { DashboardStats } from '@/lib/types';

interface Props {
  stats: DashboardStats;
}

const cards = [
  { key: 'total_subdomains', label: 'Subdomains', color: 'text-accent-blue', gradient: 'from-accent-blue to-accent-cyan', icon: '◉' },
  { key: 'total_urls', label: 'URLs', color: 'text-accent-green', gradient: 'from-accent-green to-accent-teal', icon: '◆' },
  { key: 'total_params', label: 'Parameters', color: 'text-accent-yellow', gradient: 'from-accent-yellow to-accent-orange', icon: '●' },
  { key: 'total_findings', label: 'Findings', color: 'text-accent-red', gradient: 'from-accent-red to-accent-orange', icon: '★' },
] as const;

export default function StatsCards({ stats }: Props) {
  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map((card) => (
        <div key={card.key} className="glass-card-elevated p-4 card-hover-lift relative overflow-hidden">
          <div className={`absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r ${card.gradient}`} />
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-500 text-xs uppercase tracking-wider">{card.label}</span>
            <span className={`${card.color} text-xl`}>{card.icon}</span>
          </div>
          <div className={`text-3xl font-bold ${card.color}`}>
            {(stats[card.key] || 0).toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  );
}
