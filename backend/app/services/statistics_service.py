from typing import List, Dict, Any
import numpy as np
from backend.app.schemas.payload import StatisticsResponse, OccupancyDistribution
from backend.app.services.ac_service import ac_service


class StatisticsService:
    """Service to track, aggregate, and compute processing statistics."""

    def __init__(self):
        self.frame_records: List[Dict[str, Any]] = []

    def add_frame_record(
        self,
        frame_number: int,
        people_count: int,
        occupancy_level: str,
        confidence_avg: float,
        fps: float,
        processing_time_ms: float,
        ac_power: str,
        ac_temp: Any
    ):
        """Record frame metrics for aggregation."""
        self.frame_records.append({
            "frame_number": frame_number,
            "people_count": people_count,
            "occupancy_level": occupancy_level,
            "confidence_avg": confidence_avg,
            "fps": fps,
            "processing_time_ms": processing_time_ms,
            "ac_power": ac_power,
            "ac_temp": ac_temp
        })

    def get_statistics(self) -> StatisticsResponse:
        """Compute aggregated statistics across all processed frames."""
        if not self.frame_records:
            return StatisticsResponse(
                total_frames_processed=0,
                avg_people_count=0.0,
                max_people_count=0,
                min_people_count=0,
                avg_fps=0.0,
                avg_confidence=0.0,
                avg_processing_time_ms=0.0,
                occupancy_distribution=OccupancyDistribution(low=0, medium=0, high=0),
                total_ac_runtime_seconds=round(ac_service.get_current_runtime(), 1),
                avg_ac_temperature=0.0,
                ac_state_counts={"OFF": 0, "ON": 0}
            )

        counts = [r["people_count"] for r in self.frame_records]
        fps_list = [r["fps"] for r in self.frame_records]
        conf_list = [r["confidence_avg"] for r in self.frame_records if r["confidence_avg"] > 0]
        proc_list = [r["processing_time_ms"] for r in self.frame_records]
        temps = [r["ac_temp"] for r in self.frame_records if r["ac_temp"] is not None]

        occupancy_levels = [r["occupancy_level"] for r in self.frame_records]
        low_cnt = occupancy_levels.count("LOW")
        med_cnt = occupancy_levels.count("MEDIUM")
        high_cnt = occupancy_levels.count("HIGH")

        ac_powers = [r["ac_power"] for r in self.frame_records]
        ac_off_cnt = ac_powers.count("OFF")
        ac_on_cnt = ac_powers.count("ON")

        return StatisticsResponse(
            total_frames_processed=len(self.frame_records),
            avg_people_count=round(float(np.mean(counts)), 2),
            max_people_count=int(np.max(counts)),
            min_people_count=int(np.min(counts)),
            avg_fps=round(float(np.mean(fps_list)), 2),
            avg_confidence=round(float(np.mean(conf_list)), 4) if conf_list else 0.0,
            avg_processing_time_ms=round(float(np.mean(proc_list)), 2),
            occupancy_distribution=OccupancyDistribution(
                low=low_cnt,
                medium=med_cnt,
                high=high_cnt
            ),
            total_ac_runtime_seconds=round(ac_service.get_current_runtime(), 1),
            avg_ac_temperature=round(float(np.mean(temps)), 1) if temps else 0.0,
            ac_state_counts={"OFF": ac_off_cnt, "ON": ac_on_cnt}
        )

    def get_timeline(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return frame history timeline for real-time charting."""
        return self.frame_records[-limit:]

    def clear(self):
        """Reset statistics records."""
        self.frame_records.clear()


statistics_service = StatisticsService()
