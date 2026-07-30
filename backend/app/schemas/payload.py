from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DetectionBox(BaseModel):
    """Detection bounding box details."""
    bbox: List[float] = Field(..., description="[x1, y1, x2, y2]")
    confidence: float
    class_id: int
    class_name: str


class FramePrediction(BaseModel):
    """Inference result for a single processed frame."""
    frame_number: int
    total_frames: int
    people_count: int
    occupancy_level: str
    ac_power: str
    ac_temperature: Optional[int] = None
    confidence_avg: float
    fps: float
    processing_time_ms: float
    timestamp: str


class ACStatusSchema(BaseModel):
    """Smart AC State simulation details."""
    power: str = Field(..., description="OFF or ON")
    temperature: Optional[int] = Field(None, description="Temperature in Celsius or None when OFF")
    mode: str = Field("ECO", description="Cooling mode: OFF, ECO, or COOL")
    fan_speed: str = Field("OFF", description="OFF, LOW, MED, HIGH")
    occupancy_level: str
    running_time_seconds: float
    last_changed: str


class DashboardState(BaseModel):
    """Live state payload for dashboard sync."""
    is_processing: bool
    current_video: Optional[str] = None
    people_count: int
    occupancy_level: str
    ac_status: ACStatusSchema
    fps: float
    confidence_avg: float
    processing_time_ms: float
    current_frame: int
    total_frames: int
    progress_percentage: float
    edge_status: Dict[str, Any]


class OccupancyDistribution(BaseModel):
    """Distribution counts for occupancy levels."""
    low: int
    medium: int
    high: int


class StatisticsResponse(BaseModel):
    """Aggregated processing statistics."""
    total_frames_processed: int
    avg_people_count: float
    max_people_count: int
    min_people_count: int
    avg_fps: float
    avg_confidence: float
    avg_processing_time_ms: float
    occupancy_distribution: OccupancyDistribution
    total_ac_runtime_seconds: float
    avg_ac_temperature: float
    ac_state_counts: Dict[str, int]


class SettingsUpdate(BaseModel):
    """Request payload to update occupancy thresholds and AC settings."""
    low_occupancy_max: Optional[int] = Field(None, ge=1, le=10)
    medium_occupancy_max: Optional[int] = Field(None, ge=2, le=50)
    high_occupancy_min: Optional[int] = Field(None, ge=3, le=100)
    medium_temp: Optional[int] = Field(None, ge=16, le=30)
    high_temp: Optional[int] = Field(None, ge=16, le=30)
    confidence_threshold: Optional[float] = Field(None, ge=0.1, le=1.0)


class ControlCommand(BaseModel):
    """Command payload for video processing control."""
    command: str = Field(..., description="pause, resume, stop, remove")


class VideoUploadResponse(BaseModel):
    """Response payload for video upload."""
    message: str
    filename: str
    file_path: str
    file_size_bytes: int
    duration_seconds: float
    total_frames: int
    fps: float
    resolution: str
