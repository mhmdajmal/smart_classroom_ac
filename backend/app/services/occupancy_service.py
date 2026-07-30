from backend.app.core.config import settings
from backend.app.core.logging import logger


class OccupancyService:
    """Service to evaluate classroom occupancy levels based on headcount."""

    def __init__(self):
        self.low_max = settings.LOW_OCCUPANCY_MAX
        self.medium_max = settings.MEDIUM_OCCUPANCY_MAX
        self.high_min = settings.HIGH_OCCUPANCY_MIN

    def update_thresholds(
        self,
        low_max: int = None,
        medium_max: int = None,
        high_min: int = None
    ):
        """Update occupancy thresholds dynamically."""
        if low_max is not None:
            self.low_max = low_max
        if medium_max is not None:
            self.medium_max = medium_max
        if high_min is not None:
            self.high_min = high_min

        logger.info(f"Occupancy thresholds updated: LOW <= {self.low_max}, MEDIUM <= {self.medium_max}, HIGH >= {self.high_min}")

    def evaluate_occupancy(self, people_count: int) -> str:
        """
        Evaluate occupancy level based on current people count.

        Rules:
        0 - 2  -> LOW
        3 - 9  -> MEDIUM
        10+    -> HIGH
        """
        if people_count <= self.low_max:
            return "LOW"
        elif people_count <= self.medium_max:
            return "MEDIUM"
        else:
            return "HIGH"


occupancy_service = OccupancyService()
