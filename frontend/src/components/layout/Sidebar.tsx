'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import ServerStatus from './ServerStatus';

const navItems = [
  { href: '/', label: 'Dashboard', icon: '⬡' },
  { href: '/scanner', label: 'Scanner', icon: '▶' },
  { href: '/graph', label: 'Attack Map', icon: '⚔' },
  { href: '/upload', label: 'Upload', icon: '⬆' },
  { href: '/projects', label: 'Projects', icon: '◧' },
  { href: '/analysis', label: 'Analysis', icon: '⚡' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-16 bg-bg-secondary border-r border-border-dark flex flex-col items-center py-4 z-50">
      {/* Logo */}
      <div className="mb-8">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan via-accent-blue to-accent-purple flex items-center justify-center text-bg-primary font-bold text-lg shadow-lg shadow-accent-cyan/20">
          R
        </div>
      </div>

      {/* Nav Items */}
      <nav className="flex flex-col gap-2 flex-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg transition-all duration-200 group relative ${
                isActive
                  ? 'bg-accent-cyan/10 text-accent-cyan neon-text border-l-2 border-accent-cyan'
                  : 'text-gray-500 hover:text-accent-cyan hover:bg-bg-hover'
              }`}
              title={item.label}
            >
              {item.icon}
              {/* Tooltip */}
              <span className="absolute left-14 px-2 py-1 bg-bg-card border border-border-dark rounded text-xs text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Server Status */}
      <ServerStatus />
      <div className="text-[10px] text-gray-600">v1.2</div>
      <div className="text-[8px] text-gray-600 mt-1 leading-tight text-center">
        Built by<br />
        <span className="text-accent-cyan">noobie-boy</span>
      </div>
    </aside>
  );
}
