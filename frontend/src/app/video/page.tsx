'use client';

import React, { useState, useCallback } from 'react';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { useDropzone } from 'react-dropzone';
import { useQuery } from '@tanstack/react-query';
import {
  uploadVideo,
  startInference,
  controlProcessing,
  fetchDashboard,
} from '../../services/api';
import {
  Upload,
  Play,
  Pause,
  RotateCcw,
  Trash2,
  CheckCircle2,
  Film,
  Users,
  Building2,
  Activity,
  Layers,
  Zap,
  Sparkles
} from 'lucide-react';

export default function VideoPage() {
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const { data: dashboard, refetch } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    refetchInterval: 200,
  });

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!acceptedFiles || acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const res = await uploadVideo(file);
      setUploadSuccess(`Video '${res.filename}' uploaded successfully (${res.resolution}, ${res.total_frames} frames).`);
      refetch();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to upload video file.');
    } finally {
      setUploading(false);
    }
  }, [refetch]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
    },
    maxFiles: 1,
  });

  const handleStartInference = async () => {
    try {
      await startInference();
      refetch();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to start inference.');
    }
  };

  const handleControl = async (cmd: 'pause' | 'resume' | 'stop' | 'remove') => {
    try {
      await controlProcessing(cmd);
      if (cmd === 'remove') {
        setUploadSuccess(null);
      }
      refetch();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || `Failed to execute ${cmd}.`);
    }
  };

  const isProcessing = dashboard?.is_processing ?? false;
  const isPaused = dashboard?.is_paused ?? false;
  const hasVideo = Boolean(dashboard?.current_video);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || '';
  const videoSrc = dashboard?.current_video ? `${apiBase}/uploads/${dashboard.current_video}` : '';

  return (
    <div className="flex-1 flex flex-col min-h-screen">
      <Header title="Classroom Video AI Inference Workbench" />

      <main className="flex-1 p-6 space-y-6">
        {/* Main Video Viewport Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Native HTML5 Video Player Container */}
          <div className="lg:col-span-2 space-y-4">
            {/* Active Video Status Panel */}
            <div className="glass-panel p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-2">
                  <Film className="w-4 h-4 text-cyan-400" /> Loaded Video Status
                </span>
                <span className={`text-xs font-mono px-2.5 py-0.5 rounded border ${
                  hasVideo ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-gray-500/10 text-gray-400 border-gray-500/20'
                }`}>
                  {hasVideo ? (isProcessing ? 'PROCESSING ACTIVE' : 'VIDEO LOADED') : 'NO VIDEO LOADED'}
                </span>
              </div>
              <p className="text-xs text-gray-300 font-mono">
                {hasVideo ? `Active File: ${dashboard?.current_video}` : 'No video file currently loaded. Upload a video to start inference.'}
              </p>
            </div>

            {/* Playback Control Bar */}
            <div className="glass-panel p-4 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                {!isProcessing && hasVideo && (
                  <button
                    onClick={handleStartInference}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs shadow-glow-emerald transition-all flex items-center gap-1.5"
                  >
                    <Play className="w-4 h-4" /> Start Inference Processing
                  </button>
                )}

                {isProcessing && !isPaused && (
                  <button
                    onClick={() => handleControl('pause')}
                    className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-medium text-xs shadow-glow transition-all flex items-center gap-1.5"
                  >
                    <Pause className="w-4 h-4" /> Pause Analysis
                  </button>
                )}

                {isProcessing && isPaused && (
                  <button
                    onClick={() => handleControl('resume')}
                    className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-glow transition-all flex items-center gap-1.5"
                  >
                    <Play className="w-4 h-4" /> Resume Analysis
                  </button>
                )}

                {hasVideo && (
                  <button
                    onClick={() => handleControl('stop')}
                    className="px-3.5 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 font-medium text-xs transition-all flex items-center gap-1.5"
                  >
                    <RotateCcw className="w-3.5 h-3.5 text-gray-400" /> Restart Analysis
                  </button>
                )}
              </div>

              {hasVideo && (
                <button
                  onClick={() => handleControl('remove')}
                  className="px-3.5 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 font-medium text-xs transition-all flex items-center gap-1.5"
                >
                  <Trash2 className="w-3.5 h-3.5 text-rose-400" /> Remove Video
                </button>
              )}
            </div>

            {/* Frame Progress Bar */}
            {hasVideo && (
              <div className="glass-panel p-4 space-y-2">
                <div className="flex justify-between text-xs font-mono text-gray-300">
                  <span>Inference Progress: Frame {dashboard?.current_frame ?? 0} of {dashboard?.total_frames ?? 0}</span>
                  <span className="text-cyan-400 font-bold">{dashboard?.progress_percentage ?? 0}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400 h-full rounded-full transition-all duration-300"
                    style={{ width: `${dashboard?.progress_percentage ?? 0}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Right Panel: Video Upload & Live HUD Telemetry */}
          <div className="space-y-6">
            {/* Drag & Drop Upload Zone */}
            <div className="glass-panel p-5 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Upload className="w-4 h-4 text-blue-400" /> Upload Classroom Video
              </h3>

              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all duration-200 ${
                  isDragActive
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-white/15 hover:border-white/30 bg-white/5'
                }`}
              >
                <input {...getInputProps()} />
                <Upload className="w-8 h-8 text-blue-400 mx-auto mb-2 opacity-80" />
                <p className="text-xs font-medium text-gray-200">
                  {isDragActive ? 'Drop video file here...' : 'Drag & drop classroom video'}
                </p>
                <p className="text-[11px] text-gray-400 mt-1">
                  Supports MP4, AVI, MOV, MKV files
                </p>
              </div>

              {uploading && (
                <div className="text-xs text-cyan-400 font-mono flex items-center gap-2">
                  <Activity className="w-4 h-4 animate-spin" /> Uploading & inspecting video...
                </div>
              )}

              {uploadSuccess && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{uploadSuccess}</span>
                </div>
              )}

              {uploadError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                  {uploadError}
                </div>
              )}
            </div>

            {/* Live Telemetry Panel */}
            <div className="glass-panel p-5 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-purple-400" /> Real-time Telemetry
              </h3>

              <div className="space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10">
                  <span className="text-gray-400 flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5 text-blue-400" /> People Count
                  </span>
                  <span className="text-white font-bold text-sm">{dashboard?.people_count ?? 0}</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10">
                  <span className="text-gray-400 flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5 text-amber-400" /> Occupancy Level
                  </span>
                  <span className="text-amber-400 font-bold">{dashboard?.occupancy_level ?? 'LOW'}</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10">
                  <span className="text-gray-400 flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5 text-emerald-400" /> Smart AC Status
                  </span>
                  <span className="text-emerald-400 font-bold">
                    {dashboard?.ac_status.power ?? 'OFF'} {dashboard?.ac_status.temperature ? `(${dashboard.ac_status.temperature}°C)` : ''}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10">
                  <span className="text-gray-400 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> YOLO Confidence
                  </span>
                  <span className="text-cyan-400">
                    {dashboard?.confidence_avg ? `${(dashboard.confidence_avg * 100).toFixed(1)}%` : '0.0%'}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10">
                  <span className="text-gray-400">Inference Rate</span>
                  <span className="text-purple-400">{dashboard?.fps ?? 0.0} FPS</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <Footer />
      </main>
    </div>
  );
}
