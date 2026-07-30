import time
from pathlib import Path
from typing import Tuple, List, Dict, Any
import cv2
import numpy as np
from ultralytics import YOLO
from backend.app.core.config import settings
from backend.app.core.logging import logger


class YoloInferenceService:
    """
    Pure Local Edge AI Inference Service using EXCLUSIVELY 'best.pt'.
    Strictly processes custom trained weights from best.pt.
    """

    HUMAN_KEYWORDS = {"person", "student", "teacher", "human", "people", "pupil", "man", "woman", "child"}

    def __init__(self):
        self.model = None
        self.is_loaded = False
        self.human_class_ids = [0, 1]
        self.model_path = settings.get_best_pt_path()
        self._load_model()

    def _load_model(self):
        """Load custom trained model weights exclusively from best.pt."""
        try:
            if not self.model_path.exists():
                logger.error(f"Custom model 'best.pt' not found at: {self.model_path}")
                self.is_loaded = False
                return

            logger.info(f"Loading PURE custom model exclusively from {self.model_path}...")
            self.model = YOLO(str(self.model_path))
            self.is_loaded = True

            # Inspect model's custom classes ({0: 'person', ...})
            if hasattr(self.model, "names") and isinstance(self.model.names, dict):
                self.human_class_ids = []
                for cid, cname in self.model.names.items():
                    name_str = str(cname).lower()
                    if any(k in name_str for k in self.HUMAN_KEYWORDS):
                        self.human_class_ids.append(int(cid))
                if not self.human_class_ids:
                    # Default to class 0 (person/human)
                    self.human_class_ids = [0]

            logger.info(f"PURE best.pt model loaded successfully! Human Class IDs: {self.human_class_ids} ({[self.model.names.get(i) for i in self.human_class_ids if hasattr(self.model, 'names')]})")
        except Exception as e:
            logger.error(f"Failed to load custom model best.pt: {str(e)}")
            self.is_loaded = False

    def predict_frame(
        self,
        frame: np.ndarray,
        frame_number: int = 1,
        total_frames: int = 1,
        conf_threshold: float = None
    ) -> Tuple[np.ndarray, int, float, List[Dict[str, Any]], float]:
        """
        Process a single video frame EXCLUSIVELY using custom trained 'best.pt' model.
        Detects person / human objects.
        """
        start_time = time.perf_counter()

        if not self.is_loaded or self.model is None:
            self._load_model()

        if not self.is_loaded or self.model is None:
            annotated = frame.copy()
            cv2.putText(annotated, "best.pt Model Not Loaded", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            return annotated, 0, 0.0, [], 0.0

        conf = conf_threshold if conf_threshold is not None else settings.CONFIDENCE_THRESHOLD

        # Run inference strictly using best.pt
        results = self.model.predict(
            source=frame,
            conf=conf,
            iou=settings.IOU_THRESHOLD,
            imgsz=640,
            verbose=False
        )

        detections = []
        confidences = []

        if len(results) > 0 and len(results[0].boxes) > 0:
            boxes = results[0].boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                cls_name = self.model.names.get(cls_id, "person") if hasattr(self.model, "names") else "person"
                name_str = str(cls_name).lower()

                # Match human classes (student, teacher, person, or class 0/1)
                is_human = (cls_id in self.human_class_ids) or (cls_id in [0, 1]) or any(k in name_str for k in self.HUMAN_KEYWORDS)
                if is_human:
                    score = float(box.conf[0].item())
                    xyxy = box.xyxy[0].cpu().numpy().tolist()
                    confidences.append(score)
                    detections.append({
                        "bbox": xyxy,
                        "confidence": score,
                        "class_id": cls_id,
                        "class_name": str(cls_name).capitalize()
                    })

        annotated_frame = frame.copy()
        self.draw_detections(annotated_frame, detections)

        people_count = len(detections)
        avg_confidence = float(np.mean(confidences)) if confidences else 0.0

        end_time = time.perf_counter()
        processing_time_ms = (end_time - start_time) * 1000.0
        fps = 1000.0 / processing_time_ms if processing_time_ms > 0 else 30.0

        # Draw HUD banner overlay
        self._draw_hud_overlay(
            annotated_frame,
            people_count=people_count,
            fps=fps,
            frame_num=frame_number,
            total_frames=total_frames,
            proc_time=processing_time_ms
        )

        return annotated_frame, people_count, avg_confidence, detections, processing_time_ms

    def draw_detections(self, frame: np.ndarray, detections: List[Dict[str, Any]]):
        """Draw bounding boxes and class labels onto frame."""
        for det in detections:
            xyxy = det["bbox"]
            conf = det["confidence"]
            cls_name = det["class_name"]

            x1, y1, x2, y2 = map(int, xyxy)
            box_color = (255, 191, 0)  # Glowing cyan/gold accent

            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
            label = f"{cls_name} {conf * 100:.0f}%"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - 22), (x1 + w + 6, y1), box_color, -1)
            cv2.putText(
                frame,
                label,
                (x1 + 3, y1 - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
                cv2.LINE_AA
            )

    def _draw_hud_overlay(
        self,
        frame: np.ndarray,
        people_count: int,
        fps: float,
        frame_num: int,
        total_frames: int,
        proc_time: float
    ):
        """Draw HUD metrics banner onto frame."""
        h, w, _ = frame.shape
        overlay = frame.copy()
        
        banner_h = 45
        cv2.rectangle(overlay, (0, 0), (w, banner_h), (15, 20, 28), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        text_color = (255, 255, 255)
        accent_color = (0, 220, 255)

        hud_text_1 = f"PEOPLE COUNT: {people_count}"
        hud_text_2 = f"FPS: {fps:.1f} ({proc_time:.1f}ms)"
        hud_text_3 = f"FRAME: {frame_num}/{total_frames}"

        cv2.putText(frame, hud_text_1, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, accent_color, 2, cv2.LINE_AA)
        cv2.putText(frame, hud_text_2, (260, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, text_color, 1, cv2.LINE_AA)
        cv2.putText(frame, hud_text_3, (470, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, text_color, 1, cv2.LINE_AA)


yolo_service = YoloInferenceService()
