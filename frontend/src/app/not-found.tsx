'use client';

import React from 'react';
import Link from 'next/link';
import { Cpu, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#090d16] flex flex-col items-center justify-center p-6 text-center">
      <div className="glass-panel p-8 max-w-md w-full space-y-6 border border-white/10 relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute -top-10 -left-10 w-32 h-32 rounded-full bg-blue-500/20 blur-2xl pointer-events-none" />

        <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mx-auto text-blue-400 shadow-glow">
          <Cpu className="w-7 h-7" />
        </div>

        <div className="space-y-2">
          <h1 className="text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400 font-mono">
            404
          </h1>
          <h2 className="text-lg font-bold text-white tracking-tight">Page Not Found</h2>
          <p className="text-xs text-gray-400">
            The requested telemetry endpoint or workspace route does not exist on this Edge AI system.
          </p>
        </div>

        <Link
          href="/"
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-glow transition-all w-full"
        >
          <ArrowLeft className="w-4 h-4" /> Return to Dashboard
        </Link>
      </div>
    </div>
  );
}
