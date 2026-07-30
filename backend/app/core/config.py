import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings and Configuration."""

    APP_NAME: str = "Teachable Machine Edge AI Smart Classroom"
    VERSION: str = "1.0.0"
    ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    MODEL_PATH: str = "keras_model.h5"
    LABELS_PATH: str = "labels.txt"
    UPLOAD_DIR: str = "uploads"
    LOG_DIR: str = "logs"

    # Threshold configurations
    LOW_OCCUPANCY_MAX: int = 2
    MEDIUM_OCCUPANCY_MAX: int = 9
    HIGH_OCCUPANCY_MIN: int = 10

    # AC Temperature Rules (°C)
    MEDIUM_TEMP: int = 24
    HIGH_TEMP: int = 20

    # Model settings
    CONFIDENCE_THRESHOLD: float = 0.25

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_model_path(self) -> Path:
        """Resolve full model file path."""
        p = Path(self.MODEL_PATH)
        if p.is_absolute() and p.exists():
            return p
        
        candidates = [
            self.ROOT_DIR / "models" / "keras_model.h5",
            self.ROOT_DIR / "models" / "best.pt",
            self.ROOT_DIR / "keras_model.h5",
            self.ROOT_DIR / "best.pt",
            self.ROOT_DIR / "keras.h5",
            self.ROOT_DIR / "model.h5",
            self.ROOT_DIR / p,
            self.BASE_DIR / p,
        ]

        for cand in candidates:
            if cand.exists():
                return cand

        return self.ROOT_DIR / "models" / "keras_model.h5"

    def get_best_pt_path(self) -> Path:
        """Resolve full YOLO best.pt model file path."""
        candidates = [
            self.ROOT_DIR / "models" / "best.pt",
            self.ROOT_DIR / "best.pt",
            self.ROOT_DIR / "models" / "keras_model.h5",
            self.ROOT_DIR / "keras_model.h5",
        ]
        for cand in candidates:
            if cand.exists():
                return cand
        return self.ROOT_DIR / "models" / "best.pt"

    def get_labels_path(self) -> Path:
        """Resolve full labels file path."""
        p = Path(self.LABELS_PATH)
        if p.is_absolute() and p.exists():
            return p
        
        candidates = [
            self.ROOT_DIR / "models" / "labels.txt",
            self.ROOT_DIR / "models" / "labels1.txt",
            self.ROOT_DIR / "labels.txt",
            self.ROOT_DIR / "labels1.txt",
            self.ROOT_DIR / "text1.txt",
            self.ROOT_DIR / p,
            self.BASE_DIR / p,
        ]

        for cand in candidates:
            if cand.exists():
                return cand

        return self.ROOT_DIR / "models" / "labels.txt"

    def get_upload_dir(self) -> Path:
        """Resolve full upload directory path."""
        p = Path(self.UPLOAD_DIR)
        if p.is_absolute():
            return p
        full_path = self.ROOT_DIR / p
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path

    def get_log_dir(self) -> Path:
        """Resolve full log directory path."""
        p = Path(self.LOG_DIR)
        if p.is_absolute():
            return p
        full_path = self.ROOT_DIR / p
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path


settings = Settings()
