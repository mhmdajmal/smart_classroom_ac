'use client';

import React from 'react';
import Header from '../components/layout/Header';
import MetricCard from '../components/dashboard/MetricCard';
import RealtimeChart from '../components/dashboard/RealtimeChart';
import { useQuery } from '@tanstack/react-query';
import { fetchDashboard, fetchTimeline } from '../services/api';
import {
  Users,
  Building2,
  Thermometer,
  Zap,
  Sparkles,
  Timer,
  Film
} from 'lucide-react';

export default function Dashboard() {
  const { data: dashboard } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    refetchInterval: 200,
  });

  const { data: timeline = [] } = useQuery({
    queryKey: ['timeline'],
    queryFn: () => fetchTimeline(50),
    refetchInterval: 200,
  });

  const getOccupancyBadge = (level?: string) => {
    switch (level) {
      case 'LOW':
        return { color: 'emerald', badge: 'LOW (0-2)', bg: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' };
      case 'MEDIUM':
        return { color: 'amber', badge: 'MEDIUM (3-9)', bg: 'bg-amber-500/20 text-amber-400 border-amber-500/30' };
      case 'HIGH':
        return { color: 'rose', badge: 'HIGH (10+)', bg: 'bg-rose-500/20 text-rose-400 border-rose-500/30' };
      default:
        return { color: 'blue', badge: 'STANDBY', bg: 'bg-blue-500/20 text-blue-400 border-blue-500/30' };
    }
  };

  const occBadge = getOccupancyBadge(dashboard?.occupancy_level);

  return (
    <div className="flex-1 flex flex-col min-h-screen">
      <Header title="Edge AI Classroom Telemetry Dashboard" />

      <main className="flex-1 p-6 space-y-6">
        {/* Primary Metric Grid Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="People Count"
            value={dashboard?.people_count ?? 0}
            subtitle="Detected Person Objects"
            icon={Users}
            color="blue"
            badge={`${dashboard?.people_count ?? 0} Persons`}
          />

          <MetricCard
            title="Occupancy Level"
            value={dashboard?.occupancy_level ?? 'LOW'}
            subtitle="Classroom Capacity State"
            icon={Building2}
            color={occBadge.color as any}
            badge={occBadge.badge}
            badgeColor={occBadge.bg}
          />

          <MetricCard
            title="Smart AC Power"
            value={dashboard?.ac_status.power ?? 'OFF'}
            subtitle={`Target Temp: ${dashboard?.ac_status.temperature ? `${dashboard.ac_status.temperature}°C` : '--'}`}
            icon={Zap}
            color={dashboard?.ac_status.power === 'ON' ? 'emerald' : 'rose'}
            badge={dashboard?.ac_status.power === 'ON' ? 'COOLING ACTIVE' : 'POWER OFF'}
            badgeColor={dashboard?.ac_status.power === 'ON' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border-rose-500/30'}
          />

          <MetricCard
            title="AC Temperature"
            value={dashboard?.ac_status.temperature ? `${dashboard.ac_status.temperature}°C` : '--'}
            subtitle={`Fan: ${dashboard?.ac_status.fan_speed ?? 'OFF'} • Mode: ${dashboard?.ac_status.mode ?? 'OFF'}`}
            icon={Thermometer}
            color="cyan"
          />
        </div>

        {/* Real-time Charts & Live Stream */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Live AI Video Stream Preview Card with Bounding Boxes */}
            <div className="glass-panel p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-2">
                  <Film className="w-4 h-4 text-cyan-400" /> Live AI Video Feed & Telemetry Overlay (Teachable Machine)
                </span>
                <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  LIVE STREAM ACTIVE
                </span>
              </div>
              <div className="relative aspect-video bg-black/80 rounded-xl overflow-hidden border border-white/10 flex items-center justify-center">
                <img
                  src={`${process.env.NEXT_PUBLIC_API_URL || ''}/api/stream`}
                  alt="Live AI Stream"
                  className="w-full h-full object-contain rounded-xl"
                />
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {/* Video Processing Progress Card */}
            <div className="glass-panel p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                  Video Pipeline Progress
                </span>
                <span className="text-xs font-mono text-cyan-400">
                  {dashboard?.progress_percentage ?? 0}%
                </span>
              </div>
              <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-blue-500 to-cyan-400 h-full rounded-full transition-all duration-300"
                  style={{ width: `${dashboard?.progress_percentage ?? 0}%` }}
                />
              </div>
              <div className="flex justify-between text-[11px] text-gray-400 font-mono">
                <span>Frame: {dashboard?.current_frame ?? 0}</span>
                <span>Total: {dashboard?.total_frames ?? 0}</span>
              </div>
            </div>

            {/* Average Confidence Card */}
            <MetricCard
              title="Average Confidence"
              value={dashboard?.confidence_avg ? `${(dashboard.confidence_avg * 100).toFixed(1)}%` : '0.0%'}
              subtitle="YOLO Detection Certainty"
              icon={Sparkles}
              color="emerald"
            />

            {/* Classroom Headcount Timeline Chart under Average Confidence */}
            <RealtimeChart
              timelineData={timeline}
              title="Classroom Headcount Timeline"
              dataKey="people_count"
              color="#3b82f6"
              unit="People"
            />
          </div>
        </div>
      </main>
    </div>
  );
}
