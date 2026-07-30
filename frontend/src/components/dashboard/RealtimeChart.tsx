'use client';

import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { FrameTimelineRecord } from '../../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface RealtimeChartProps {
  timelineData: FrameTimelineRecord[];
  title: string;
  dataKey: 'people_count' | 'fps' | 'processing_time_ms' | 'ac_temp';
  color?: string;
  unit?: string;
}

export default function RealtimeChart({
  timelineData,
  title,
  dataKey,
  color = '#3b82f6',
  unit = '',
}: RealtimeChartProps) {
  const labels = timelineData.map((d) => `#${d.frame_number}`);
  const values = timelineData.map((d) => (d[dataKey] !== null ? d[dataKey] : 0));

  const data = {
    labels,
    datasets: [
      {
        label: `${title} (${unit})`,
        data: values,
        borderColor: color,
        backgroundColor: `${color}15`,
        borderWidth: 2,
        tension: 0.35,
        fill: true,
        pointRadius: 1.5,
        pointHoverRadius: 5,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: '#111827',
        titleColor: '#f3f4f6',
        bodyColor: '#38bdf8',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
        ticks: {
          color: '#6b7280',
          font: { size: 10 },
          maxTicksLimit: 8,
        },
      },
      y: {
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
        ticks: {
          color: '#6b7280',
          font: { size: 10 },
        },
        beginAtZero: true,
      },
    },
  };

  return (
    <div className="glass-panel p-5 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-gray-300 tracking-wider uppercase">
          {title}
        </h4>
        {values.length > 0 && (
          <span className="text-xs font-mono font-bold text-cyan-400">
            Current: {values[values.length - 1]} {unit}
          </span>
        )}
      </div>

      <div className="h-44 w-full">
        {timelineData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-gray-500 font-mono">
            Awaiting Frame Timeline Data...
          </div>
        ) : (
          <Line data={data} options={options} />
        )}
      </div>
    </div>
  );
}
