'use client';

import { useState, useEffect } from 'react';
import { checkHealth } from '@/lib/api';

export default function ServerStatus() {
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    const check = async () => {
      const result = await checkHealth();
      setStatus(result && result.status === 'ok' ? 'online' : 'offline');
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-1.5 px-2 py-1">
      <span className={`w-2 h-2 rounded-full ${
        status === 'online' ? 'bg-accent-green animate-pulse' :
        status === 'offline' ? 'bg-accent-red' : 'bg-gray-500'
      }`} />
      <span className="text-[9px] text-gray-500">
        {status === 'online' ? 'Online' : status === 'offline' ? 'Offline' : '...'}
      </span>
    </div>
  );
}
