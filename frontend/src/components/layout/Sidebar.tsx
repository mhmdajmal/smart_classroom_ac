'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Video, 
  BarChart3, 
  Terminal, 
  Settings, 
  Cpu,
  Sparkles
} from 'lucide-react';

const navigationItems = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Video Processing', href: '/video', icon: Video },
  { name: 'Statistics', href: '/statistics', icon: BarChart3 },
  { name: 'Logs', href: '/logs', icon: Terminal },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 glass-panel h-screen flex flex-col justify-between p-4 fixed left-0 top-0 z-40 border-r border-white/10 rounded-none">
      <div>
        {/* Brand Header */}
        <div className="flex items-center gap-3 px-3 py-4 border-b border-white/10 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-cyan-500 to-emerald-400 flex items-center justify-center shadow-glow">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-sm text-white tracking-wide flex items-center gap-1.5">
              Smart Classroom
            </h1>
            <p className="text-[11px] text-cyan-400 font-mono tracking-tight flex items-center gap-1">
              <Sparkles className="w-3 h-3 inline" /> EDGE AI SYSTEM
            </p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1.5">
          {navigationItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-gray-400'}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
