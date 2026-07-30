import os
import time
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Generator
import cv2
import numpy as np
import psutil

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.tflite_service import tflite_service
from backend.app.services.occupancy_service import occupancy_service
from backend.app.services.ac_service import ac_service
from backend.app.services.statistics_service import statistics_service


class VideoProcessorService:
    """Manager for video uploading, Teachable Machine TFLite inference execution with human bounding boxes, state control, and paced video streaming."""

    def __init__(self):
        self.is_processing = False
        self.is_paused = False
        self.should_stop = False
        self.current_video_path: Optional[Path] = None
        self.current_filename: Optional[str] = None
        
        self.current_frame_idx = 0
        self.total_frames = 0
        self.fps = 0.0
        self.video_duration = 0.0
        self.resolution = "0x0"

        # Frame pacing control (Target 60 FPS for smooth, fast video playback)
        self.target_fps = 60.0
        self.frame_delay = 1.0 / self.target_fps  # ~0.016s delay per frame

        self.latest_people_count = 0
        self.latest_occupancy = "LOW"
        self.latest_fps = 0.0
        self.latest_confidence = 0.0
        self.latest_proc_time = 0.0
        self.latest_frame_encoded: Optional[bytes] = None

        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Find sample video file
        upload_dir = settings.get_upload_dir()
        all_mp4s = list(settings.ROOT_DIR.glob("*.mp4")) + list(upload_dir.glob("*.mp4"))
        
        if all_mp4s:
            target_video = all_mp4s[0]
            try:
                self.set_video(target_video, target_video.name)
                self.start_processing()
                logger.info(f"Auto-loaded video stream: {target_video.name}")
            except Exception as e:
                logger.warning(f"Could not auto-load sample video: {str(e)}")

    def set_video(self, file_path: Path, filename: str) -> Dict[str, Any]:
        """Load video metadata and prepare for processing."""
        self.stop_processing()
        
        self.current_video_path = file_path
        self.current_filename = filename
        
        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
            logger.error(f"Cannot open video file: {file_path}")
            raise ValueError("Invalid video file")

        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.resolution = f"{w}x{h}"
        self.video_duration = self.total_frames / self.fps if self.fps > 0 else 0.0

        cap.release()
        
        # Reset state
        self.current_frame_idx = 0
        self.latest_people_count = 0
        self.latest_occupancy = "LOW"
        self.latest_fps = 0.0
        self.latest_confidence = 0.0
        self.latest_proc_time = 0.0
        self.latest_frame_encoded = None
        
        ac_service.reset_stats()
        statistics_service.clear()

        logger.info(f"Video loaded: {filename} ({self.total_frames} frames, {self.resolution}, {self.fps:.1f} FPS)")

        # Automatically start video processing worker for newly uploaded file
        self.start_processing()

        return {
            "filename": filename,
            "file_path": str(file_path),
            "total_frames": self.total_frames,
            "fps": self.fps,
            "duration_seconds": round(self.video_duration, 2),
            "resolution": self.resolution
        }

    def start_processing(self):
        """Start asynchronous frame-by-frame processing worker thread."""
        if not self.current_video_path or not self.current_video_path.exists():
            all_mp4s = list(settings.ROOT_DIR.glob("*.mp4")) + list(settings.get_upload_dir().glob("*.mp4"))
            if all_mp4s:
                self.current_video_path = all_mp4s[0]
                self.current_filename = all_mp4s[0].name
                cap = cv2.VideoCapture(str(all_mp4s[0]))
                if cap.isOpened():
                    self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    self.fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
                    cap.release()
            else:
                logger.warning("No valid video loaded to process.")
                return False

        if self.is_processing and self._thread and self._thread.is_alive():
            if self.is_paused:
                self.is_paused = False
                logger.info("Resumed video processing.")
            return True

        self.is_processing = True
        self.is_paused = False
        self.should_stop = False
        
        self._thread = threading.Thread(target=self._process_worker, daemon=True)
        self._thread.start()
        logger.info(f"Started video processing thread for {self.current_filename}")
        return True

    def pause_processing(self):
        """Pause video processing loop."""
        if self.is_processing:
            self.is_paused = True
            logger.info("Paused video processing.")

    def resume_processing(self):
        """Resume video processing loop."""
        if self.is_processing and self.is_paused:
            self.is_paused = False
            logger.info("Resumed video processing.")

    def stop_processing(self):
        """Stop video processing loop."""
        self.should_stop = True
        self.is_processing = False
        self.is_paused = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._thread = None
        logger.info("Stopped video processing.")

    def remove_video(self):
        """Stop processing and purge loaded video."""
        self.stop_processing()
        if self.current_video_path and self.current_video_path.exists():
            try:
                os.remove(self.current_video_path)
            except Exception as e:
                logger.error(f"Error removing video file: {str(e)}")
        
        self.current_video_path = None
        self.current_filename = None
        self.current_frame_idx = 0
        self.total_frames = 0
        self.latest_frame_encoded = None
        ac_service.reset_stats()
        statistics_service.clear()
        logger.info("Removed video file and reset processor state.")

    def _process_worker(self):
        """Native real-time video playback thread running at exact video FPS."""
        cap = cv2.VideoCapture(str(self.current_video_path))
        if not cap.isOpened():
            self.is_processing = False
            return

        cap_fps = float(cap.get(cv2.CAP_PROP_FPS))
        native_fps = cap_fps if (cap_fps > 0 and cap_fps < 120) else (self.fps if self.fps > 0 else 25.0)
        frame_interval = 1.0 / native_fps

        frame_num = 0
        start_time = time.perf_counter()

        while cap.isOpened() and not self.should_stop:
            if self.is_paused:
                time.sleep(0.05)
                start_time = time.perf_counter() - (frame_num * frame_interval)
                continue

            ret, raw_frame = cap.read()
            if not ret:
                logger.info("Reached end of video stream. Looping back to frame 1...")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_num = 0
                start_time = time.perf_counter()
                continue

            frame_num += 1
            self.current_frame_idx = frame_num

            # Dispatch AI inference asynchronously if worker is idle
            if not getattr(self, "_ai_busy", False):
                if not hasattr(self, "_ai_executor"):
                    import concurrent.futures
                    self._ai_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                self._ai_busy = True
                self._ai_executor.submit(self._run_ai_async, raw_frame.copy(), frame_num)

            # Overlay latest AI results onto current frame
            with self._lock:
                res = getattr(self, "_latest_ai_results", {})
                occ_level = res.get("occupancy_level", "LOW")
                conf_score = res.get("confidence", 0.0)
                people_count = res.get("people_count", 0)
                proc_time_ms = res.get("proc_time_ms", 1.0)
                pred_label = res.get("predicted_label", "Low Occupancy")
                
                annotated_frame = raw_frame.copy()
                tflite_service._draw_hud_overlay(
                    annotated_frame,
                    predicted_label=pred_label,
                    people_count=people_count,
                    confidence=conf_score * 100.0,
                    fps=native_fps,
                    frame_num=frame_num,
                    total_frames=self.total_frames,
                    proc_time=proc_time_ms,
                    occupancy_level=occ_level
                )

                ac_state = ac_service.process_occupancy(occ_level)
                statistics_service.add_frame_record(
                    frame_number=frame_num,
                    people_count=people_count,
                    occupancy_level=occ_level,
                    confidence_avg=conf_score,
                    fps=native_fps,
                    processing_time_ms=proc_time_ms,
                    ac_power=ac_state["power"],
                    ac_temp=ac_state["temperature"]
                )

                self.latest_people_count = people_count
                self.latest_occupancy = occ_level
                self.latest_fps = native_fps
                self.latest_confidence = conf_score
                self.latest_proc_time = proc_time_ms

                _, buffer = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                self.latest_frame_encoded = buffer.tobytes()

            # Exact real-time wall clock pacing
            target_elapsed = frame_num * frame_interval
            actual_elapsed = time.perf_counter() - start_time
            sleep_time = target_elapsed - actual_elapsed

            if sleep_time > 0:
                time.sleep(sleep_time)
            elif sleep_time < -frame_interval:
                # Catch up by grabbing frames if behind schedule
                skip_count = min(5, int(abs(sleep_time) / frame_interval))
                for _ in range(skip_count):
                    if not cap.grab():
                        break
                    frame_num += 1
                self.current_frame_idx = frame_num

        cap.release()
        self.is_processing = False
        logger.info(f"Video processing finished. Processed {frame_num} frames.")

    def _run_ai_async(self, frame: np.ndarray, frame_num: int):
        """Asynchronous AI prediction execution worker."""
        try:
            annotated_frame, occ_level, conf_score, probs, people_count, proc_time_ms = tflite_service.predict_frame(
                frame=frame,
                frame_number=frame_num,
                total_frames=self.total_frames
            )
            pred_idx = int(np.argmax(probs)) if len(probs) > 0 else 0
            label_name = tflite_service.labels[pred_idx] if pred_idx < len(tflite_service.labels) else occ_level

            with self._lock:
                self._latest_ai_results = {
                    "predicted_label": label_name,
                    "occupancy_level": occ_level,
                    "confidence": conf_score,
                    "people_count": people_count,
                    "proc_time_ms": proc_time_ms
                }
        except Exception as e:
            logger.warning(f"Async AI prediction error: {e}")
        finally:
            self._ai_busy = False

    def get_live_frame(self) -> Generator[bytes, None, None]:
        """MJPEG generator for live HTTP streaming video endpoint."""
        if not self.is_processing and self.current_video_path and self.current_video_path.exists():
            self.start_processing()

        while True:
            with self._lock:
                frame_bytes = self.latest_frame_encoded

            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                blank = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(blank, "No Video Active", (180, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                _, buffer = cv2.imencode('.jpg', blank)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

            stream_delay = 1.0 / (self.fps if self.fps > 0 else 25.0)
            time.sleep(stream_delay)  # Native video FPS stream refresh

    def get_dashboard_state(self) -> Dict[str, Any]:
        """Return structured dashboard telemetry payload."""
        if not self.is_processing and self.current_video_path and self.current_video_path.exists():
            self.start_processing()

        progress = (self.current_frame_idx / self.total_frames * 100.0) if self.total_frames > 0 else 0.0

        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        return {
            "is_processing": self.is_processing,
            "is_paused": self.is_paused,
            "current_video": self.current_filename,
            "people_count": self.latest_people_count,
            "occupancy_level": self.latest_occupancy,
            "ac_status": ac_service.get_status(),
            "fps": round(self.latest_fps, 1),
            "confidence_avg": round(self.latest_confidence, 4),
            "processing_time_ms": round(self.latest_proc_time, 1),
            "current_frame": self.current_frame_idx,
            "total_frames": self.total_frames,
            "progress_percentage": round(progress, 1),
            "edge_status": {
                "cpu_usage_percent": cpu_usage,
                "memory_usage_percent": memory.percent,
                "memory_used_mb": round(memory.used / (1024 * 1024), 1),
                "model_name": "Teachable Machine Edge AI Classifier",
                "device": "Local Edge Device",
                "mode": "Offline Local Inference"
            }
        }


video_processor = VideoProcessorService()
