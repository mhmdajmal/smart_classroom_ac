import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Query
from fastapi.responses import StreamingResponse, FileResponse

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.payload import (
    DashboardState,
    StatisticsResponse,
    SettingsUpdate,
    ControlCommand,
    VideoUploadResponse
)
from backend.app.services.video_processor import video_processor
from backend.app.services.statistics_service import statistics_service
from backend.app.services.occupancy_service import occupancy_service
from backend.app.services.ac_service import ac_service
from backend.app.services.tflite_service import tflite_service

router = APIRouter(prefix="/api", tags=["Smart Classroom Edge AI"])


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """
    Upload classroom video for local edge AI inference.

    Accepts MP4, AVI, MOV, MKV files.
    Saves file to uploads/ directory.
    """
    allowed_extensions = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(allowed_extensions)}"
        )

    clean_filename = Path(file.filename).name.replace(" ", "_")
    upload_dir = settings.get_upload_dir()
    save_path = upload_dir / clean_filename

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = save_path.stat().st_size
        logger.info(f"Uploaded video saved: {clean_filename} ({file_size} bytes)")

        # Load video into processor and start worker thread
        metadata = video_processor.set_video(save_path, clean_filename)
        video_processor.start_processing()

        return VideoUploadResponse(
            message="Video uploaded successfully and loaded for Edge AI processing.",
            filename=metadata["filename"],
            file_path=metadata["file_path"],
            file_size_bytes=file_size,
            duration_seconds=metadata["duration_seconds"],
            total_frames=metadata["total_frames"],
            fps=metadata["fps"],
            resolution=metadata["resolution"]
        )
    except Exception as e:
        logger.error(f"Video upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process uploaded video: {str(e)}")


@router.post("/predict")
async def trigger_prediction():
    """
    Trigger Teachable Machine classification inference on the uploaded classroom video.
    """
    if not video_processor.current_video_path:
        raise HTTPException(status_code=400, detail="No uploaded video found. Please upload a video first.")

    success = video_processor.start_processing()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to start video inference worker thread.")

    return {
        "message": "Inference started successfully on local edge device.",
        "video": video_processor.current_filename,
        "status": "processing"
    }


@router.post("/control")
async def control_processing(cmd: ControlCommand):
    """
    Control processing playback state (pause, resume, stop, remove).
    """
    command = cmd.command.lower()
    if command == "pause":
        video_processor.pause_processing()
        return {"message": "Processing paused"}
    elif command == "resume":
        video_processor.resume_processing()
        return {"message": "Processing resumed"}
    elif command == "stop":
        video_processor.stop_processing()
        return {"message": "Processing stopped"}
    elif command == "remove":
        video_processor.remove_video()
        return {"message": "Video removed"}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown command: '{command}'")


@router.get("/stream")
async def video_stream():
    """
    HTTP MJPEG Live video stream displaying real-time Teachable Machine predictions and HUD.
    """
    return StreamingResponse(
        video_processor.get_live_frame(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/dashboard", response_model=DashboardState)
async def get_dashboard():
    """
    Returns live edge telemetry state for dashboard UI components.
    """
    return video_processor.get_dashboard_state()


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """
    Returns aggregated analytics, average people count, FPS, confidence, and AC runtime.
    """
    return statistics_service.get_statistics()


@router.get("/timeline")
async def get_timeline(limit: int = Query(100, ge=10, le=1000)):
    """
    Returns frame history timeline for real-time dashboard charts.
    """
    return statistics_service.get_timeline(limit=limit)


@router.get("/logs")
async def get_logs(lines: int = Query(200, ge=10, le=2000), download: bool = False):
    """
    Retrieve application inference & system log entries or download raw log file.
    """
    log_file = settings.get_log_dir() / "app.log"

    if download:
        if log_file.exists():
            return FileResponse(
                path=log_file,
                filename="smart_classroom_edge.log",
                media_type="text/plain"
            )
        raise HTTPException(status_code=404, detail="Log file not found.")

    log_lines = []
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
            log_lines = [line.strip() for line in all_lines[-lines:]]

    return {
        "total_lines": len(log_lines),
        "log_file": str(log_file),
        "logs": log_lines
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint verifying system resources and Teachable Machine TFLite model status.
    """
    model_loaded = tflite_service.is_loaded
    return {
        "status": "healthy" if model_loaded else "degraded",
        "model_loaded": model_loaded,
        "model_path": str(tflite_service.model_path),
        "labels_path": str(tflite_service.labels_path),
        "environment": settings.ENV,
        "device": "Local Edge Computer",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION
    }


@router.get("/status")
async def get_status():
    """
    Returns current processing pipeline status summary.
    """
    return {
        "is_processing": video_processor.is_processing,
        "is_paused": video_processor.is_paused,
        "current_video": video_processor.current_filename,
        "current_frame": video_processor.current_frame_idx,
        "total_frames": video_processor.total_frames,
        "people_count": video_processor.latest_people_count,
        "occupancy_level": video_processor.latest_occupancy
    }


@router.post("/settings")
async def update_settings(update: SettingsUpdate):
    """
    Dynamically adjust low/medium/high occupancy thresholds & AC temperature rules.
    """
    occupancy_service.update_thresholds(
        low_max=update.low_occupancy_max,
        medium_max=update.medium_occupancy_max,
        high_min=update.high_occupancy_min
    )
    
    ac_service.update_temperature_settings(
        medium_temp=update.medium_temp,
        high_temp=update.high_temp
    )

    if update.confidence_threshold:
        settings.CONFIDENCE_THRESHOLD = update.confidence_threshold
        logger.info(f"Confidence threshold set to {update.confidence_threshold}")

    return {
        "message": "Settings updated successfully.",
        "current_thresholds": {
            "low_max": occupancy_service.low_max,
            "medium_max": occupancy_service.medium_max,
            "high_min": occupancy_service.high_min
        },
        "ac_temps": {
            "medium_temp": ac_service.medium_temp,
            "high_temp": ac_service.high_temp
        },
        "confidence_threshold": settings.CONFIDENCE_THRESHOLD
    }
