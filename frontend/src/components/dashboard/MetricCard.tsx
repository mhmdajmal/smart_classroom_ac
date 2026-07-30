'use client';

import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'blue' | 'emerald' | 'amber' | 'rose' | 'purple' | 'cyan';
  badge?: string;
  badgeColor?: string;
}

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'blue',
  badge,
  badgeColor = 'bg-blue-500/20 text-blue-400 border-blue-500/30',
}: MetricCardProps) {
  const colorMap = {
    blue: 'from-blue-500/20 to-blue-600/5 text-blue-400 border-blue-500/30',
    emerald: 'from-emerald-500/20 to-emerald-600/5 text-emerald-400 border-emerald-500/30',
    amber: 'from-amber-500/20 to-amber-600/5 text-amber-400 border-amber-500/30',
    rose: 'from-rose-500/20 to-rose-600/5 text-rose-400 border-rose-500/30',
    purple: 'from-purple-500/20 to-purple-600/5 text-purple-400 border-purple-500/30',
    cyan: 'from-cyan-500/20 to-cyan-600/5 text-cyan-400 border-cyan-500/30',
  };

  return (
    <div className="glass-panel-interactive p-5 relative overflow-hidden group">
      {/* Dynamic Background Glow Gradient */}
      <div
        className={`absolute -right-6 -bottom-6 w-24 h-24 rounded-full bg-gradient-to-br ${colorMap[color]} blur-xl opacity-40 group-hover:opacity-70 transition-opacity`}
      />

      <div className="flex items-center justify-between mb-3 relative z-10">
        <span className="text-xs font-medium text-gray-400 tracking-wider uppercase">
          {title}
        </span>
        <div className={`p-2.5 rounded-xl bg-white/5 border border-white/10 ${colorMap[color].split(' ')[2]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="relative z-10 flex items-baseline justify-between">
        <div className="text-2xl font-bold text-white tracking-tight font-mono">
          {value}
        </div>
        {badge && (
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-semibold border ${badgeColor}`}
          >
            {badge}
          </span>
        )}
      </div>

      {subtitle && (
        <div className="mt-2 text-[11px] text-gray-400 relative z-10">
          {subtitle}
        </div>
      )}
    </div>
  );
}
