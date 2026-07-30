export interface ACStatus {
  power: 'OFF' | 'ON';
  temperature: number | null;
  mode: 'OFF' | 'ECO' | 'COOL';
  fan_speed: 'OFF' | 'LOW' | 'MED' | 'HIGH';
  occupancy_level: 'LOW' | 'MEDIUM' | 'HIGH';
  running_time_seconds: number;
  last_changed: string;
}

export interface EdgeStatus {
  cpu_usage_percent: number;
  memory_usage_percent: number;
  memory_used_mb: number;
  model_name: string;
  device: string;
  mode: string;
}

export interface DashboardState {
  is_processing: boolean;
  is_paused: boolean;
  current_video: string | null;
  people_count: number;
  occupancy_level: 'LOW' | 'MEDIUM' | 'HIGH';
  ac_status: ACStatus;
  fps: number;
  confidence_avg: number;
  processing_time_ms: number;
  current_frame: number;
  total_frames: number;
  progress_percentage: number;
  edge_status: EdgeStatus;
}

export interface OccupancyDistribution {
  low: number;
  medium: number;
  high: number;
}

export interface StatisticsData {
  total_frames_processed: number;
  avg_people_count: number;
  max_people_count: number;
  min_people_count: number;
  avg_fps: number;
  avg_confidence: number;
  avg_processing_time_ms: number;
  occupancy_distribution: OccupancyDistribution;
  total_ac_runtime_seconds: number;
  avg_ac_temperature: number;
  ac_state_counts: {
    OFF: number;
    ON: number;
  };
}

export interface FrameTimelineRecord {
  frame_number: number;
  people_count: number;
  occupancy_level: string;
  confidence_avg: number;
  fps: number;
  processing_time_ms: number;
  ac_power: string;
  ac_temp: number | null;
}

export interface SettingsPayload {
  low_occupancy_max?: number;
  medium_occupancy_max?: number;
  high_occupancy_min?: number;
  medium_temp?: number;
  high_temp?: number;
  confidence_threshold?: number;
}

export interface UploadResponse {
  message: string;
  filename: string;
  file_path: string;
  file_size_bytes: number;
  duration_seconds: number;
  total_frames: number;
  fps: number;
  resolution: string;
}
