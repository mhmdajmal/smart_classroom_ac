import axios from 'axios';
import {
  DashboardState,
  StatisticsData,
  FrameTimelineRecord,
  SettingsPayload,
  UploadResponse,
} from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export const uploadVideo = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const startInference = async (): Promise<{ message: string; video: string }> => {
  const response = await api.post('/predict');
  return response.data;
};

export const controlProcessing = async (command: 'pause' | 'resume' | 'stop' | 'remove') => {
  const response = await api.post('/control', { command });
  return response.data;
};

export const fetchDashboard = async (): Promise<DashboardState> => {
  const response = await api.get<DashboardState>('/dashboard');
  return response.data;
};

export const fetchStatistics = async (): Promise<StatisticsData> => {
  const response = await api.get<StatisticsData>('/statistics');
  return response.data;
};

export const fetchTimeline = async (limit = 100): Promise<FrameTimelineRecord[]> => {
  const response = await api.get<FrameTimelineRecord[]>(`/timeline?limit=${limit}`);
  return response.data;
};

export const fetchLogs = async (lines = 200) => {
  const response = await api.get<{ total_lines: number; logs: string[] }>(`/logs?lines=${lines}`);
  return response.data;
};

export const downloadLogsUrl = `${API_BASE_URL}/api/logs?download=true`;

export const updateSettings = async (settings: SettingsPayload) => {
  const response = await api.post('/settings', settings);
  return response.data;
};

export const fetchHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getStreamUrl = (): string => {
  return `${API_BASE_URL}/api/stream`;
};
