from collections import deque
import os
import sys
import time
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import cv2
import numpy as np
import h5py

os.environ['KERAS_BACKEND'] = 'torch'
try:
    import keras
    HAS_KERAS = True
except ImportError:
    HAS_KERAS = False

from backend.app.core.config import settings
from backend.app.core.logging import logger


class TeachableMachineService:
    """
    Local Edge AI Inference Service for Google Teachable Machine Keras H5 Models
    with sliding-window probability smoothing and state transition hysteresis.
    """

    def __init__(self):
        self.model = None
        self.is_loaded = False
        self.labels: List[str] = []
        self.raw_labels: List[str] = []
        self.model_path = settings.get_model_path()
        self.labels_path = settings.get_labels_path()
        
        # Occupancy state smoothing: Immediate LOW transition + 1.5s change gap
        self.smoothed_occupancy = "LOW"
        self.state_hold_until = 0.0

        self._load_labels()
        self._load_model()

    def _load_labels(self):
        """Read and parse class labels from text1.txt / labels1.txt / labels.txt."""
        try:
            if not self.labels_path.exists():
                logger.error(f"Labels file not found at: {self.labels_path}")
                self.labels = ["Low Occupancy", "Medium Occupancy", "High Occupancy"]
                return

            labels = []
            raw_labels = []
            with open(self.labels_path, "r", encoding="utf-8") as f:
                for line in f:
                    clean = line.strip()
                    if not clean:
                        continue
                    raw_labels.append(clean)
                    parts = clean.split(" ", 1)
                    name = parts[1].strip() if len(parts) > 1 and parts[0].isdigit() else clean

                    if "low" in name.lower():
                        formatted = "Low Occupancy"
                    elif "middle" in name.lower() or "medium" in name.lower():
                        formatted = "Medium Occupancy"
                    elif "high" in name.lower():
                        formatted = "High Occupancy"
                    else:
                        formatted = name.title()
                    labels.append(formatted)

            self.labels = labels if labels else ["Low Occupancy", "Medium Occupancy", "High Occupancy"]
            self.raw_labels = raw_labels
            logger.info(f"Loaded class labels from {self.labels_path.name}: {self.labels}")
        except Exception as e:
            logger.error(f"Failed to load labels file: {e}")
            self.labels = ["Low Occupancy", "Medium Occupancy", "High Occupancy"]

    def _load_model(self):
        """Load Teachable Machine Keras H5 model."""
        try:
            if not HAS_KERAS:
                logger.error("Keras package not installed.")
                self.is_loaded = False
                return

            if not self.model_path.exists():
                logger.error(f"Keras H5 model file not found at: {self.model_path}")
                self.is_loaded = False
                return

            logger.info(f"Loading Teachable Machine Keras model from {self.model_path}...")

            num_classes = len(self.labels) if self.labels else 3
            base = keras.applications.MobileNetV2(
                input_shape=(224, 224, 3),
                alpha=0.35,
                include_top=False,
                weights='imagenet',
                pooling='avg'
            )
            x = base.output
            fc1 = keras.layers.Dense(100, activation='relu', name='dense_Dense1')(x)
            fc2 = keras.layers.Dense(num_classes, activation='softmax', use_bias=False, name='dense_Dense2')(fc1)

            self.model = keras.Model(inputs=base.input, outputs=fc2)

            # Load classification head weights from H5
            with h5py.File(str(self.model_path), 'r') as f:
                weights_group = f['model_weights']
                head = weights_group['sequential_3']
                d1_w = np.array(head['dense_Dense1']['kernel:0'])
                d1_b = np.array(head['dense_Dense1']['bias:0'])
                d2_w = np.array(head['dense_Dense2']['kernel:0'])

                self.model.get_layer('dense_Dense1').set_weights([d1_w, d1_b])
                self.model.get_layer('dense_Dense2').set_weights([d2_w])

            self.is_loaded = True
            logger.info("Teachable Machine Keras H5 model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load Keras H5 model: {e}")
            self.is_loaded = False

    def predict_frame(
        self,
        frame: np.ndarray,
        frame_number: int = 1,
        total_frames: int = 1,
        conf_threshold: Optional[float] = None
    ) -> Tuple[np.ndarray, str, float, List[float], int, float]:
        """
        Process video frame using Pure Teachable Machine classification (Ultra-Fast Edge AI).
        """
        start_time = time.perf_counter()

        if not self.is_loaded or self.model is None:
            self._load_model()

        if not self.is_loaded or self.model is None:
            annotated = frame.copy()
            cv2.putText(annotated, "Keras H5 Model Not Loaded", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            return annotated, "LOW", 0.0, [0.0, 0.0, 0.0], 0, 0.0

        annotated_frame = frame.copy()

        # 1. Preprocess & Run Teachable Machine Keras H5 inference
        resized = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = (rgb.astype(np.float32) / 127.5) - 1.0
        input_data = np.expand_dims(normalized, axis=0)

        preds = self.model(input_data)
        if hasattr(preds, 'detach'):
            output_data = preds.detach().cpu().numpy()[0]
        elif hasattr(preds, 'numpy'):
            output_data = preds.numpy()[0]
        else:
            output_data = np.array(preds)[0]

        pred_idx = int(np.argmax(output_data))
        confidence = float(output_data[pred_idx])

        predicted_label = self.labels[pred_idx] if pred_idx < len(self.labels) else f"Class {pred_idx}"

        raw_state = "LOW"
        if "high" in predicted_label.lower():
            raw_state = "HIGH"
        elif "middle" in predicted_label.lower() or "medium" in predicted_label.lower():
            raw_state = "MEDIUM"

        now_time = time.time()
        # Immediate LOW transition + 1.5s transition hold gap
        if raw_state == "LOW":
            self.smoothed_occupancy = "LOW"
            self.state_hold_until = now_time + 1.5  # 1.5s gap before allowing status change
        else:
            if now_time >= self.state_hold_until:
                self.smoothed_occupancy = raw_state

        occupancy_level = self.smoothed_occupancy

        # Standard clean headcount mapping per occupancy level
        if occupancy_level == "LOW":
            people_count = 1
        elif occupancy_level == "MEDIUM":
            people_count = 5
        else:
            people_count = 12

        end_time = time.perf_counter()
        proc_time_ms = (end_time - start_time) * 1000.0
        fps = 1000.0 / proc_time_ms if proc_time_ms > 0 else 30.0

        # 3. Draw high-contrast HUD card
        self._draw_hud_overlay(
            annotated_frame,
            predicted_label=predicted_label,
            people_count=people_count,
            confidence=confidence * 100.0,
            fps=fps,
            frame_num=frame_number,
            total_frames=total_frames,
            proc_time=proc_time_ms,
            occupancy_level=occupancy_level
        )

        return annotated_frame, occupancy_level, confidence, output_data.tolist(), people_count, proc_time_ms

    def _draw_hud_overlay(
        self,
        frame: np.ndarray,
        predicted_label: str,
        people_count: int,
        confidence: float,
        fps: float,
        frame_num: int,
        total_frames: int,
        proc_time: float,
        occupancy_level: str
    ):
        """Draw high-contrast glassmorphic HUD banner overlay onto frame."""
        h, w, _ = frame.shape
        overlay = frame.copy()
        
        banner_h = 55
        cv2.rectangle(overlay, (0, 0), (w, banner_h), (15, 20, 28), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        # Color coding accent
        if occupancy_level == "LOW":
            accent_color = (0, 220, 0)      # Green BGR
        elif occupancy_level == "MEDIUM":
            accent_color = (0, 215, 255)    # Amber BGR
        else:
            accent_color = (50, 50, 255)    # Red BGR

        # Left indicator bar
        cv2.rectangle(frame, (0, 0), (10, banner_h), accent_color, -1)

        text_color = (255, 255, 255)

        hud_1 = f"HUMANS: ~{people_count} ({occupancy_level})"
        hud_2 = f"CONF: {confidence:.1f}%"
        hud_3 = f"FPS: {fps:.1f}"
        hud_4 = f"FRAME: {frame_num}/{total_frames}"

        cv2.putText(frame, hud_1, (22, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.60, accent_color, 2, cv2.LINE_AA)
        cv2.putText(frame, hud_2, (410, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.55, text_color, 1, cv2.LINE_AA)
        cv2.putText(frame, hud_3, (550, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(frame, hud_4, (670, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)


tflite_service = TeachableMachineService()
