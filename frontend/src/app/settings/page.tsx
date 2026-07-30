'use client';

import React, { useState } from 'react';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { updateSettings } from '../../services/api';
import { Settings, Save, RotateCcw, Sliders, Thermometer, ShieldCheck, Cpu } from 'lucide-react';

export default function SettingsPage() {
  const [lowMax, setLowMax] = useState<number>(2);
  const [medMax, setMedMax] = useState<number>(9);
  const [highMin, setHighMin] = useState<number>(10);
  const [mediumTemp, setMediumTemp] = useState<number>(24);
  const [highTemp, setHighTemp] = useState<number>(20);
  const [confThreshold, setConfThreshold] = useState<number>(0.25);

  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setStatusMessage(null);

    try {
      await updateSettings({
        low_occupancy_max: lowMax,
        medium_occupancy_max: medMax,
        high_occupancy_min: highMin,
        medium_temp: mediumTemp,
        high_temp: highTemp,
        confidence_threshold: confThreshold,
      });
      setStatusMessage(`Configuration saved! YOLO Confidence Threshold set to ${(confThreshold * 100).toFixed(0)}%.`);
    } catch (err: any) {
      setStatusMessage('Failed to update settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setLowMax(2);
    setMedMax(9);
    setHighMin(10);
    setMediumTemp(24);
    setHighTemp(20);
    setConfThreshold(0.25);
    setStatusMessage('Reset to factory default settings.');
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen">
      <Header title="Edge AI System Settings & Occupancy Thresholds" />

      <main className="flex-1 p-6 space-y-6">
        <form onSubmit={handleSave} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Settings Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Occupancy Rules & Threshold Config */}
            <div className="glass-panel p-6 space-y-5">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2 border-b border-white/10 pb-3">
                <Sliders className="w-4 h-4 text-blue-400" /> Classroom Occupancy Classification Rules
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* Low Occupancy Max */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-gray-300">LOW Occupancy Max</label>
                  <input
                    type="number"
                    value={lowMax}
                    onChange={(e) => setLowMax(Number(e.target.value))}
                    min={1}
                    max={10}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-gray-500">People count ≤ {lowMax} → LOW (AC OFF)</p>
                </div>

                {/* Medium Occupancy Max */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-gray-300">MEDIUM Occupancy Max</label>
                  <input
                    type="number"
                    value={medMax}
                    onChange={(e) => setMedMax(Number(e.target.value))}
                    min={2}
                    max={50}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-gray-500">People count ≤ {medMax} → MEDIUM</p>
                </div>

                {/* High Occupancy Min */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-gray-300">HIGH Occupancy Min</label>
                  <input
                    type="number"
                    value={highMin}
                    onChange={(e) => setHighMin(Number(e.target.value))}
                    min={3}
                    max={100}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-gray-500">People count ≥ {highMin} → HIGH</p>
                </div>
              </div>
            </div>

            {/* Smart AC Temperature Rules */}
            <div className="glass-panel p-6 space-y-5">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2 border-b border-white/10 pb-3">
                <Thermometer className="w-4 h-4 text-cyan-400" /> Smart Air Conditioner Target Temperatures
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Medium Occupancy Temperature */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-gray-300">MEDIUM Occupancy Temp (°C)</label>
                  <input
                    type="number"
                    value={mediumTemp}
                    onChange={(e) => setMediumTemp(Number(e.target.value))}
                    min={16}
                    max={30}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-cyan-500"
                  />
                  <p className="text-[11px] text-gray-500">Target cooling temp for 3–9 occupants</p>
                </div>

                {/* High Occupancy Temperature */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-gray-300">HIGH Occupancy Temp (°C)</label>
                  <input
                    type="number"
                    value={highTemp}
                    onChange={(e) => setHighTemp(Number(e.target.value))}
                    min={16}
                    max={30}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-cyan-500"
                  />
                  <p className="text-[11px] text-gray-500">Target cooling temp for 10+ occupants</p>
                </div>
              </div>
            </div>

            {/* AI Model Parameters */}
            <div className="glass-panel p-6 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2 border-b border-white/10 pb-3">
                <Cpu className="w-4 h-4 text-purple-400" /> YOLO11 Inference Sensitivity Threshold
              </h3>

              <div className="space-y-2">
                <div className="flex justify-between text-xs text-gray-300">
                  <span>Detection Sensitivity (Lower = Detects More Persons)</span>
                  <span className="font-mono text-cyan-400 font-bold">{(confThreshold * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min={0.05}
                  max={0.9}
                  step={0.05}
                  value={confThreshold}
                  onChange={(e) => setConfThreshold(Number(e.target.value))}
                  className="w-full accent-cyan-500 cursor-pointer"
                />
                <p className="text-[11px] text-gray-400">
                  If persons are not being detected in your video, lower this slider to 10%–20%.
                </p>
              </div>
            </div>

            {/* Submit & Reset Bar */}
            <div className="glass-panel p-4 flex items-center justify-between">
              <button
                type="button"
                onClick={handleReset}
                className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 text-xs font-medium transition-all flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" /> Reset Defaults
              </button>

              <button
                type="submit"
                disabled={saving}
                className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-glow transition-all flex items-center gap-1.5"
              >
                <Save className="w-4 h-4" /> {saving ? 'Saving...' : 'Save Settings'}
              </button>
            </div>

            {statusMessage && (
              <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-mono">
                {statusMessage}
              </div>
            )}
          </div>

          {/* Model & Device Info Sidebar */}
          <div className="space-y-6">
            <div className="glass-panel p-5 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2 border-b border-white/10 pb-3">
                <ShieldCheck className="w-4 h-4 text-emerald-400" /> Edge AI Engine Profile
              </h3>

              <div className="space-y-3 text-xs font-mono">
                <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1">
                  <span className="text-gray-400 text-[11px]">WEIGHT FILE</span>
                  <p className="text-white font-semibold">Teachable Machine</p>
                </div>

                <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1">
                  <span className="text-gray-400 text-[11px]">FRAMEWORK</span>
                  <p className="text-cyan-400 font-semibold">Teachable Machine</p>
                </div>

                <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1">
                  <span className="text-gray-400 text-[11px]">ACTIVE CLASSES</span>
                  <p className="text-emerald-400 font-semibold">Low, Medium, High Occupancy</p>
                </div>

                <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1">
                  <span className="text-gray-400 text-[11px]">COMPUTE ENVIRONMENT</span>
                  <p className="text-purple-400 font-semibold">Local Offline Edge Device</p>
                </div>
              </div>
            </div>
          </div>
        </form>
      </main>
    </div>
  );
}
