'use client';

import React from 'react';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import MetricCard from '../../components/dashboard/MetricCard';
import RealtimeChart from '../../components/dashboard/RealtimeChart';
import { useQuery } from '@tanstack/react-query';
import { fetchStatistics, fetchTimeline } from '../../services/api';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
} from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import {
  BarChart3,
  Users,
  Timer,
  Gauge,
  Sparkles,
  Thermometer,
  Zap,
  TrendingUp,
} from 'lucide-react';

ChartJS.register(ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

export default function StatisticsPage() {
  const { data: stats } = useQuery({
    queryKey: ['statistics'],
    queryFn: fetchStatistics,
    refetchInterval: 2000,
  });

  const { data: timeline = [] } = useQuery({
    queryKey: ['timeline'],
    queryFn: () => fetchTimeline(100),
    refetchInterval: 2000,
  });

  // Doughnut Data for Occupancy Distribution
  const doughnutData = {
    labels: ['LOW (0-2)', 'MEDIUM (3-9)', 'HIGH (10+)'],
    datasets: [
      {
        data: [
          stats?.occupancy_distribution.low ?? 0,
          stats?.occupancy_distribution.medium ?? 0,
          stats?.occupancy_distribution.high ?? 0,
        ],
        backgroundColor: ['#10b981', '#f59e0b', '#f43f5e'],
        borderColor: 'rgba(17, 24, 39, 0.8)',
        borderWidth: 2,
      },
    ],
  };

  // Bar Data for AC State Breakdown
  const acBarData = {
    labels: ['AC OFF', 'AC ON (Cooling)'],
    datasets: [
      {
        label: 'Frames Count',
        data: [stats?.ac_state_counts.OFF ?? 0, stats?.ac_state_counts.ON ?? 0],
        backgroundColor: ['#f43f5e', '#10b981'],
        borderRadius: 8,
      },
    ],
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen">
      <Header title="Edge AI Performance & Classroom Occupancy Analytics" />

      <main className="flex-1 p-6 space-y-6">
        {/* Metric Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="People Count Prediction"
            value={stats?.avg_people_count ?? 0}
            subtitle={`Min: ${stats?.min_people_count ?? 0} • Max: ${stats?.max_people_count ?? 0}`}
            icon={Users}
            color="blue"
          />

          <MetricCard
            title="Average FPS"
            value={`${stats?.avg_fps ?? 0} FPS`}
            subtitle="Processing Performance"
            icon={Gauge}
            color="purple"
          />

          <MetricCard
            title="YOLO Confidence"
            value={stats?.avg_confidence ? `${(stats.avg_confidence * 100).toFixed(1)}%` : '0.0%'}
            subtitle="Mean Person Detection Score"
            icon={Sparkles}
            color="emerald"
          />

          <MetricCard
            title="AC Runtime"
            value={`${stats?.total_ac_runtime_seconds ?? 0}s`}
            subtitle={`Avg Temp: ${stats?.avg_ac_temperature ? `${stats.avg_ac_temperature}°C` : '--'}`}
            icon={Zap}
            color="amber"
          />
        </div>

        {/* Detailed Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RealtimeChart
            timelineData={timeline}
            title="Classroom People Count Trend"
            dataKey="people_count"
            color="#3b82f6"
            unit="People"
          />

          <RealtimeChart
            timelineData={timeline}
            title="Inference Processing Time (Latency)"
            dataKey="processing_time_ms"
            color="#f59e0b"
            unit="ms"
          />
        </div>

        {/* Breakdown & Distribution Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Occupancy Doughnut */}
          <div className="glass-panel p-5 space-y-3">
            <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" /> Occupancy Distribution
            </h4>
            <div className="h-48 flex items-center justify-center">
              <Doughnut
                data={doughnutData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { position: 'bottom', labels: { color: '#9ca3af', font: { size: 10 } } },
                  },
                }}
              />
            </div>
          </div>

          {/* AC Operational Bar Chart */}
          <div className="glass-panel p-5 space-y-3">
            <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" /> Smart AC Power Operational Breakdown
            </h4>
            <div className="h-48 flex items-center justify-center">
              <Bar
                data={acBarData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: {
                    x: { ticks: { color: '#9ca3af' } },
                    y: { ticks: { color: '#9ca3af' }, beginAtZero: true },
                  },
                }}
              />
            </div>
          </div>

          {/* Statistical Metrics Table */}
          <div className="glass-panel p-5 space-y-3">
            <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-cyan-400" /> System Metrics Summary
            </h4>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1.5 border-b border-white/10 text-gray-400">
                <span>Total Frames Analyzed</span>
                <span className="text-white font-bold">{stats?.total_frames_processed ?? 0}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-white/10 text-gray-400">
                <span>Peak Classroom Occupancy</span>
                <span className="text-rose-400 font-bold">{stats?.max_people_count ?? 0} People</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-white/10 text-gray-400">
                <span>Minimum Occupancy</span>
                <span className="text-emerald-400 font-bold">{stats?.min_people_count ?? 0} People</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-white/10 text-gray-400">
                <span>Average Processing Latency</span>
                <span className="text-amber-400 font-bold">{stats?.avg_processing_time_ms ?? 0} ms</span>
              </div>
              <div className="flex justify-between py-1.5 text-gray-400">
                <span>Mean AC Target Temperature</span>
                <span className="text-cyan-400 font-bold">
                  {stats?.avg_ac_temperature ? `${stats.avg_ac_temperature}°C` : '--'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <Footer />
      </main>
    </div>
  );
}
