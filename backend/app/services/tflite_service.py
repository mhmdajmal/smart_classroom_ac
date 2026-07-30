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

# Optional YOLO detection for drawing human bounding boxes
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

from backend.app.core.config import settings
from backend.app.core.logging import logger


class TeachableMachineService:
    """
    Local Edge AI Inference Service for Google Teachable Machine Keras H5 Models,
    enhanced with human bounding box detection.
    """

    HUMAN_KEYWORDS = {"person", "student", "teacher", "human", "people", "man", "woman"}

    def __init__(self):
        self.model = None
        self.is_loaded = False
        self.labels: List[str] = []
        self.raw_labels: List[str] = []
        self.model_path = settings.get_model_path()
        self.labels_path = settings.get_labels_path()
        
        # Detector for human bounding boxes
        self.yolo_model = None
        self.hog_detector = None
        
        # Occupancy state smoothing & hold delay parameters
        self.smoothed_occupancy = "LOW"
        self.state_hold_until = 0.0
        self.consecutive_low_count = 0

        self._load_labels()
        self._load_model()
        self._init_human_detector()

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

    def _init_human_detector(self):
        """Initialize YOLO or OpenCV HOG person detector for drawing human bounding boxes."""
        # Check for best.pt weights
        best_pt_path = settings.get_best_pt_path()
        if HAS_YOLO and best_pt_path.exists():
            try:
                logger.info(f"Loading human detector from {best_pt_path}...")
                self.yolo_model = YOLO(str(best_pt_path))
                logger.info("Human detector (best.pt) loaded successfully!")
                return
            except Exception as e:
                logger.warning(f"Could not load best.pt: {e}")

        # Fallback to OpenCV HOG People Detector
        try:
            self.hog_detector = cv2.HOGDescriptor()
            self.hog_detector.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            logger.info("Initialized OpenCV HOG Human Bounding Box Detector.")
        except Exception as e:
            logger.warning(f"Could not initialize HOG detector: {e}")

    def detect_human_boxes(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect human bounding boxes in frame with high FPS optimization.

        Returns:
            List[Dict[str, Any]]: List of detection dicts with 'bbox' and 'confidence'.
        """
        if not hasattr(self, "_detection_counter"):
            self._detection_counter = 0
            self._last_detections = []

        self._detection_counter += 1
        if self._last_detections and (self._detection_counter % 2 != 1):
            return self._last_detections

        h, w = frame.shape[:2]
        small_frame = cv2.resize(frame, (640, 360)) if (w > 640 or h > 360) else frame
        scale_w = w / small_frame.shape[1]
        scale_h = h / small_frame.shape[0]

        detections = []
        
        # 1. Try YOLO detection
        if self.yolo_model is not None:
            try:
                results = self.yolo_model.predict(source=small_frame, conf=0.25, verbose=False, imgsz=320)
                if len(results) > 0 and len(results[0].boxes) > 0:
                    for box in results[0].boxes:
                        cls_id = int(box.cls[0].item())
                        cls_name = self.yolo_model.names.get(cls_id, "person") if hasattr(self.yolo_model, "names") else "person"
                        name_str = str(cls_name).lower()

                        if cls_id in [0, 1] or any(k in name_str for k in self.HUMAN_KEYWORDS):
                            conf = float(box.conf[0].item())
                            bx1, by1, bx2, by2 = box.xyxy[0].cpu().numpy().tolist()
                            detections.append({
                                "bbox": [bx1 * scale_w, by1 * scale_h, bx2 * scale_w, by2 * scale_h],
                                "confidence": conf,
                                "class_name": "Person"
                            })
                self._last_detections = detections
                return detections
            except Exception as e:
                logger.warning(f"YOLO detection error: {e}")

        # 2. Fallback to HOG detection on resized frame
        if self.hog_detector is not None:
            try:
                boxes, weights = self.hog_detector.detectMultiScale(small_frame, winStride=(8, 8), padding=(4, 4), scale=1.05)
                for i, (bx, by, bw, bh) in enumerate(boxes):
                    conf = float(weights[i]) if i < len(weights) else 0.85
                    x1, y1 = bx * scale_w, by * scale_h
                    x2, y2 = (bx + bw) * scale_w, (by + bh) * scale_h
                    detections.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": conf,
                        "class_name": "Person"
                    })
                self._last_detections = detections
            except Exception as e:
                logger.warning(f"HOG detection error: {e}")

        return detections

    def draw_human_boxes(self, frame: np.ndarray, detections: List[Dict[str, Any]]):
        """Draw glowing cyan bounding boxes around detected humans."""
        for det in detections:
            x1, y1, x2, y2 = map(int, det["bbox"])
            conf = det["confidence"]
            box_color = (255, 191, 0)  # Glowing cyan/amber BGR accent

            # Bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
            
            # Text tag
            label = f"Person {int(conf * 100)}%"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, max(0, y1 - 22)), (x1 + tw + 6, max(0, y1)), box_color, -1)
            cv2.putText(
                frame,
                label,
                (x1 + 3, max(12, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
                cv2.LINE_AA
            )

    def predict_frame(
        self,
        frame: np.ndarray,
        frame_number: int = 1,
        total_frames: int = 1,
        conf_threshold: Optional[float] = None
    ) -> Tuple[np.ndarray, str, float, List[float], int, float]:
        """
        Process video frame:
          - Detect human bounding boxes & draw rectangles on image
          - Run Teachable Machine TFLite classification
          - Overlay glassmorphism HUD card
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

        # 1. Detect & Draw Human Bounding Boxes
        human_detections = self.detect_human_boxes(annotated_frame)
        self.draw_human_boxes(annotated_frame, human_detections)
        people_count = len(human_detections)

        # 2. Preprocess & Run Teachable Machine Keras H5 inference
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

        # Determine Occupancy Level State (LOW, MEDIUM, HIGH) using model prediction & human headcount
        from backend.app.services.occupancy_service import occupancy_service
        count_occupancy = occupancy_service.evaluate_occupancy(people_count)

        raw_occupancy = "LOW"
        if "high" in predicted_label.lower() or count_occupancy == "HIGH":
            raw_occupancy = "HIGH"
        elif "middle" in predicted_label.lower() or "medium" in predicted_label.lower() or count_occupancy == "MEDIUM":
            raw_occupancy = "MEDIUM"

        now_time = time.time()
        # State Lock Logic:
        # Lock LOW state for 1.5 seconds when LOW is detected.
        # MEDIUM and HIGH update immediately without locking.
        if raw_occupancy == "LOW":
            self.smoothed_occupancy = "LOW"
            self.state_hold_until = now_time + 1.5  # Lock LOW state for 1.5 seconds
            self.consecutive_high_count = 0
        else:
            # Raw detection is MEDIUM or HIGH
            if now_time < self.state_hold_until:
                # LOW state is currently locked -> remain LOW
                pass
            else:
                # LOW lock expired -> update immediately to MEDIUM or HIGH (no lock on MEDIUM/HIGH)
                self.smoothed_occupancy = raw_occupancy

        occupancy_level = self.smoothed_occupancy

        end_time = time.perf_counter()
        proc_time_ms = (end_time - start_time) * 1000.0
        fps = 1000.0 / proc_time_ms if proc_time_ms > 0 else 30.0

        # 3. Draw glassmorphic HUD card
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

        hud_1 = f"HUMANS: {people_count} ({predicted_label})"
        hud_2 = f"CONF: {confidence:.1f}%"
        hud_3 = f"FPS: {fps:.1f}"
        hud_4 = f"FRAME: {frame_num}/{total_frames}"

        cv2.putText(frame, hud_1, (22, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.60, accent_color, 2, cv2.LINE_AA)
        cv2.putText(frame, hud_2, (410, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.55, text_color, 1, cv2.LINE_AA)
        cv2.putText(frame, hud_3, (550, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(frame, hud_4, (670, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)


tflite_service = TeachableMachineService()
