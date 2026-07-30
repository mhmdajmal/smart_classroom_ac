import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add backend directory to python import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.api.router import router
from backend.app.services.video_processor import video_processor
from backend.app.services.tflite_service import tflite_service

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Teachable Machine Edge AI Classroom Occupancy Classification & Smart AC Control System."
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file route for uploaded videos
upload_dir = settings.get_upload_dir()
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# Attach API Router
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Application startup initialization."""
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Model Path: {tflite_service.model_path}")
    logger.info(f"Labels Path: {tflite_service.labels_path}")
    logger.info(f"Upload Directory: {upload_dir}")
    logger.info(f"Log Directory: {settings.get_log_dir()}")
    logger.info("=" * 60)
    
    # Auto-start video stream processing loop on startup
    if video_processor.current_video_path and video_processor.current_video_path.exists():
        video_processor.start_processing()
        logger.info(f"Auto-started processing video stream: {video_processor.current_filename}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown cleanup."""
    logger.info("Shutting down Smart Classroom Edge AI service...")
    video_processor.stop_processing()
    logger.info("Cleanup completed successfully.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENV == "development")
    )
