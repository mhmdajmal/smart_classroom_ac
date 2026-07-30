'use client';

import React, { useState, useEffect } from 'react';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { useQuery } from '@tanstack/react-query';
import { fetchDashboard } from '../../services/api';
import { Terminal, Filter, Zap } from 'lucide-react';

interface TerminalEntry {
  id: string;
  time: string;
  level: 'LOW' | 'MEDIUM' | 'HIGH';
  peopleCount: number;
  acTemp: number | string;
  acMode: string;
  fps: number;
  message: string;
}

export default function LogsPage() {
  const [filter, setFilter] = useState<'ALL' | 'LOW' | 'MEDIUM' | 'HIGH'>('ALL');
  const [terminalLogs, setTerminalLogs] = useState<TerminalEntry[]>([]);

  const { data: dashboard } = useQuery({
    queryKey: ['dashboard-logs'],
    queryFn: fetchDashboard,
    refetchInterval: 1000,
  });

  useEffect(() => {
    if (!dashboard || !dashboard.current_video || !dashboard.is_processing) return;

    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];
    const occLevel = (dashboard.occupancy_level ?? 'LOW') as 'LOW' | 'MEDIUM' | 'HIGH';
    const count = dashboard.people_count ?? 0;
    const temp = dashboard.ac_status?.temperature ?? 24;
    const mode = dashboard.ac_status?.mode ?? 'ECO';
    const fps = dashboard.fps ?? 30.0;

    let msg = `OCCUPANCY STATE: ${occLevel} | Headcount: ${count} Person(s) | AC Target: ${temp}°C (${mode} Mode) | Inference: ${fps.toFixed(1)} FPS`;

    const newEntry: TerminalEntry = {
      id: `${Date.now()}-${Math.random()}`,
      time: timeStr,
      level: occLevel,
      peopleCount: count,
      acTemp: temp,
      acMode: mode,
      fps: fps,
      message: msg,
    };

    setTerminalLogs((prev) => {
      if (prev.length > 0 && prev[0].level === occLevel && prev[0].peopleCount === count && prev[0].time === timeStr) {
        return prev;
      }
      return [newEntry, ...prev.slice(0, 199)];
    });
  }, [dashboard]);

  const filteredLogs = terminalLogs.filter((log) => {
    if (filter === 'ALL') return true;
    return log.level === filter;
  });

  const getLevelBadge = (level: string) => {
    switch (level) {
      case 'LOW':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'HIGH':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
      default:
        return 'bg-blue-500/20 text-cyan-400 border-blue-500/30';
    }
  };

  const isVideoActive = Boolean(dashboard?.current_video && dashboard?.is_processing);

  return (
    <div className="flex-1 flex flex-col min-h-screen">
      <Header title="Real-Time Terminal Occupancy Monitor" />

      <main className="flex-1 p-6 space-y-6">
        {/* Terminal Controls Header */}
        <div className="glass-panel p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-cyan-400 animate-pulse" />
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                Real-Time Terminal Updates <span className={`text-xs font-mono px-2 py-0.5 rounded border ${
                  isVideoActive ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-gray-500/10 text-gray-400 border-gray-500/20'
                }`}>{isVideoActive ? 'LIVE STREAM ACTIVE' : 'IDLE - NO VIDEO PROCESSING'}</span>
              </h3>
              <p className="text-xs text-gray-400">Classroom occupancy state updates (LOW, MEDIUM, HIGH)</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Filter Pills */}
            <div className="flex items-center gap-1 bg-white/5 p-1 rounded-xl border border-white/10 text-xs">
              <Filter className="w-3.5 h-3.5 text-gray-400 ml-1.5" />
              {(['ALL', 'LOW', 'MEDIUM', 'HIGH'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-3 py-1 rounded-lg font-mono font-medium transition-all ${
                    filter === f
                      ? f === 'LOW' ? 'bg-emerald-600 text-white' : f === 'MEDIUM' ? 'bg-amber-600 text-white' : f === 'HIGH' ? 'bg-rose-600 text-white' : 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>

            <button
              onClick={() => setTerminalLogs([])}
              className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 text-xs font-mono transition-all"
            >
              Clear Terminal
            </button>
          </div>
        </div>

        {/* Real-time Terminal Output Window */}
        <div className="glass-panel p-5 bg-black/90 border border-cyan-500/20 rounded-2xl font-mono text-xs overflow-x-auto h-[600px] space-y-2 relative shadow-2xl">
          <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-3 text-[11px] text-gray-500">
            <span>&gt;_ LOCAL TERMINAL CONSOLE — SMART CLASSROOM OCCUPANCY ENGINE</span>
            <span className={`flex items-center gap-1 ${isVideoActive ? 'text-emerald-400' : 'text-gray-500'}`}>
              <span className={`w-2 h-2 rounded-full ${isVideoActive ? 'bg-emerald-400 animate-ping' : 'bg-gray-500'}`}></span> {isVideoActive ? 'STREAMING ACTIVE' : 'STANDBY'}
            </span>
          </div>

          {filteredLogs.length === 0 ? (
            <div className="h-full flex items-center justify-center text-gray-500 flex-col gap-2">
              <Zap className="w-6 h-6 text-cyan-400" />
              <span>{isVideoActive ? 'Waiting for real-time terminal updates...' : 'No video processing active. Upload a video in Video Workbench to view terminal updates.'}</span>
            </div>
          ) : (
            filteredLogs.map((log) => (
              <div key={log.id} className="flex items-center gap-3 hover:bg-white/5 px-3 py-1.5 rounded-lg border border-transparent hover:border-white/5 transition-all">
                <span className="text-gray-500 text-[11px] font-mono select-none">[{log.time}]</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border font-mono ${getLevelBadge(log.level)}`}>
                  {log.level}
                </span>
                <span className="text-gray-200 text-xs font-mono">
                  {log.message}
                </span>
              </div>
            ))
          )}
        </div>
      </main>
    </div>
  );
}
