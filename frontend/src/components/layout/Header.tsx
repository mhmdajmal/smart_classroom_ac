'use client';

import React from 'react';
import { Activity, ShieldCheck, HardDrive, WifiOff } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { fetchHealth } from '../../services/api';

interface HeaderProps {
  title: string;
}

export default function Header({ title }: HeaderProps) {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 3000,
  });

  const isHealthy = health?.status === 'healthy';

  return (
    <header className="h-16 glass-panel flex items-center justify-between px-6 border-b border-white/10 rounded-none sticky top-0 z-30">
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">{title}</h2>
      </div>

      <div className="flex items-center gap-4 text-xs font-mono">
        {/* System Health */}
        <div
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border ${
            isHealthy
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
          }`}
        >
          {isHealthy ? (
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <Activity className="w-3.5 h-3.5 text-rose-400 animate-pulse" />
          )}
          <span>{isHealthy ? 'SYSTEM READY' : 'CHECK ENGINE'}</span>
        </div>
      </div>
    </header>
  );
}
