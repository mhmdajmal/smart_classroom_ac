import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger


class SmartACService:
    """Simulates intelligent Air Conditioner response based on classroom occupancy."""

    def __init__(self):
        self.power = "OFF"
        self.temperature: Optional[int] = None
        self.mode = "OFF"
        self.fan_speed = "OFF"
        self.occupancy_level = "LOW"
        
        self.medium_temp = settings.MEDIUM_TEMP
        self.high_temp = settings.HIGH_TEMP

        self.last_changed = datetime.now().isoformat()
        self.start_running_time = None
        self.total_running_seconds = 0.0

        self.history: List[Dict[str, Any]] = []

    def update_temperature_settings(self, medium_temp: int = None, high_temp: int = None):
        """Update target temperature settings."""
        if medium_temp is not None:
            self.medium_temp = medium_temp
        if high_temp is not None:
            self.high_temp = high_temp
        logger.info(f"AC Temperature settings updated: MEDIUM={self.medium_temp}°C, HIGH={self.high_temp}°C")

    def process_occupancy(self, occupancy_level: str) -> Dict[str, Any]:
        """
        Update Smart AC state based on current occupancy level.

        Rules:
        - LOW:    Power=OFF, Temp=None, Fan=OFF, Mode=OFF
        - MEDIUM: Power=ON,  Temp=24°C, Fan=MED, Mode=ECO
        - HIGH:   Power=ON,  Temp=20°C, Fan=HIGH, Mode=COOL
        """
        previous_power = self.power
        previous_temp = self.temperature

        self.occupancy_level = occupancy_level
        now = datetime.now()

        if occupancy_level == "LOW":
            self.power = "OFF"
            self.temperature = None
            self.mode = "OFF"
            self.fan_speed = "OFF"
            if previous_power == "ON":
                if self.start_running_time:
                    self.total_running_seconds += (now.timestamp() - self.start_running_time)
                    self.start_running_time = None
        elif occupancy_level == "MEDIUM":
            self.power = "ON"
            self.temperature = self.medium_temp
            self.mode = "ECO"
            self.fan_speed = "MED"
            if previous_power == "OFF":
                self.start_running_time = now.timestamp()
        elif occupancy_level == "HIGH":
            self.power = "ON"
            self.temperature = self.high_temp
            self.mode = "COOL"
            self.fan_speed = "HIGH"
            if previous_power == "OFF":
                self.start_running_time = now.timestamp()

        # Update last changed timestamp if state mutated
        if self.power != previous_power or self.temperature != previous_temp:
            self.last_changed = now.strftime("%Y-%m-%d %H:%M:%S")
            log_msg = f"AC State Changed -> Power: {self.power}, Temp: {self.temperature if self.temperature else '--'}°C, Mode: {self.mode}, Fan: {self.fan_speed} (Occupancy: {occupancy_level})"
            logger.info(log_msg)
            
            # Record in history timeline
            self.history.append({
                "timestamp": self.last_changed,
                "power": self.power,
                "temperature": self.temperature,
                "mode": self.mode,
                "fan_speed": self.fan_speed,
                "occupancy_level": occupancy_level
            })

        return self.get_status()

    def get_current_runtime(self) -> float:
        """Calculate total cumulative AC running time in seconds."""
        current_active = 0.0
        if self.power == "ON" and self.start_running_time is not None:
            current_active = time.time() - self.start_running_time
        return self.total_running_seconds + current_active

    def get_status(self) -> Dict[str, Any]:
        """Return current Smart AC status dictionary."""
        return {
            "power": self.power,
            "temperature": self.temperature,
            "mode": self.mode,
            "fan_speed": self.fan_speed,
            "occupancy_level": self.occupancy_level,
            "running_time_seconds": round(self.get_current_runtime(), 1),
            "last_changed": self.last_changed
        }

    def reset_stats(self):
        """Reset AC statistics for a new video session."""
        self.power = "OFF"
        self.temperature = None
        self.mode = "OFF"
        self.fan_speed = "OFF"
        self.occupancy_level = "LOW"
        self.start_running_time = None
        self.total_running_seconds = 0.0
        self.last_changed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.clear()


ac_service = SmartACService()
