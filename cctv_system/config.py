"""
Configuration Management for CCTV System
Handles loading and managing application settings
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Main configuration class"""
    
    # Application Settings
    APP_NAME = "CCTV Motion Detection System"
    VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Camera Settings
    CAMERAS = {
        "camera_1": {
            "enabled": True,
            "camera_index": 0,
            "resolution": [1280, 720],
            "fps": 30,
            "rotation": 0
        },
        "camera_2": {
            "enabled": False,
            "camera_index": 1,
            "resolution": [1280, 720],
            "fps": 30,
            "rotation": 0
        }
    }
    
    # Motion Detection Settings
    MOTION_DETECTION = {
        "enabled": True,
        "method": "background_subtraction",  # Options: background_subtraction, frame_diff, optical_flow
        "sensitivity": 0.3,  # 0.1 - 1.0 (lower = more sensitive)
        "min_area": 500,  # Minimum contour area to detect motion
        "blur_kernel": 21,
        "dilate_kernel": 11,
        "erode_kernel": 9
    }
    
    # Object Detection Settings
    OBJECT_DETECTION = {
        "enabled": True,
        "model": "yolov8m",  # yolov8n, yolov8s, yolov8m, yolov8l, yolov8x
        "confidence_threshold": 0.5,
        "iou_threshold": 0.45,
        "device": "cpu",  # "cpu" or "cuda"
        "classes": ["person", "car", "truck", "bus", "bicycle", "motorcycle"]
    }
    
    # Event Recording Settings
    RECORDING = {
        "enabled": True,
        "record_on_motion": True,
        "record_on_detection": True,
        "pre_recording_seconds": 10,
        "post_recording_seconds": 30,
        "output_format": "mp4",
        "codec": "h264",
        "quality": 85,
        "storage_path": "./data/recordings"
    }
    
    # Alert Settings
    ALERTS = {
        "enabled": True,
        "motion_alert": True,
        "detection_alert": True,
        "alert_cooldown": 60,  # Seconds between alerts
        "email_enabled": False,
        "email_recipients": ["admin@example.com"],
        "slack_enabled": False,
        "slack_webhook": ""
    }
    
    # Web Interface Settings
    WEB = {
        "host": "0.0.0.0",
        "port": 5000,
        "debug": DEBUG,
        "secret_key": os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
        "ssl_enabled": False,
        "cert_path": "",
        "key_path": ""
    }
    
    # Database Settings
    DATABASE = {
        "type": "sqlite",
        "host": "localhost",
        "port": 5432,
        "name": "cctv_system.db",
        "path": "./data/cctv_system.db",
        "log_events": True,
        "retention_days": 30
    }
    
    # Logging Settings
    LOGGING = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "./data/logs/cctv_system.log",
        "max_bytes": 10485760,  # 10MB
        "backup_count": 10
    }
    
    # Performance Settings
    PERFORMANCE = {
        "max_threads": 4,
        "frame_skip": 1,  # Process every Nth frame
        "buffer_size": 100,
        "cleanup_interval": 3600  # Seconds
    }
    
    # API Settings
    API = {
        "version": "v1",
        "enable_auth": False,
        "api_key": os.getenv("API_KEY", "default-api-key"),
        "rate_limit": 1000  # Requests per hour
    }
    
    @classmethod
    def load_from_file(cls, config_file: str) -> "Config":
        """Load configuration from YAML file"""
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)
                cls._update_from_dict(config_data)
        return cls
    
    @classmethod
    def _update_from_dict(cls, config_dict: Dict[str, Any]) -> None:
        """Update configuration from dictionary"""
        for key, value in config_dict.items():
            if hasattr(cls, key):
                attr = getattr(cls, key)
                if isinstance(attr, dict) and isinstance(value, dict):
                    attr.update(value)
                else:
                    setattr(cls, key, value)
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        config_dict = {}
        for key in dir(cls):
            if not key.startswith("_") and key.isupper():
                config_dict[key] = getattr(cls, key)
        return config_dict


# Default configuration instance
config = Config()
