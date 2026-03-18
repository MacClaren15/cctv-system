"""
Database Models
Defines data structures for events, detections, and system logs
"""
from datetime import datetime
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Event:
    """Represents a motion or detection event"""
    
    def __init__(self, event_id: int, event_type: str, camera_name: str, 
                 timestamp: datetime, details: Optional[Dict] = None):
        """
        Initialize event
        
        Args:
            event_id: Unique event identifier
            event_type: Type of event (motion, detection)
            camera_name: Name of the camera
            timestamp: Event timestamp
            details: Additional event details
        """
        self.id = event_id
        self.event_type = event_type
        self.camera_name = camera_name
        self.timestamp = timestamp
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "camera_name": self.camera_name,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }
    
    def __repr__(self) -> str:
        return f"Event(id={self.id}, type={self.event_type}, camera={self.camera_name})"


class Detection:
    """Represents an object detection"""
    
    def __init__(self, detection_id: int, event_id: int, class_name: str,
                 confidence: float, bbox: Dict[str, int], timestamp: datetime):
        """
        Initialize detection
        
        Args:
            detection_id: Unique detection identifier
            event_id: ID of the event that triggered this detection
            class_name: Detected object class
            confidence: Detection confidence score
            bbox: Bounding box coordinates
            timestamp: Detection timestamp
        """
        self.id = detection_id
        self.event_id = event_id
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert detection to dictionary"""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "class": self.class_name,
            "confidence": self.confidence,
            "bbox": self.bbox,
            "timestamp": self.timestamp.isoformat()
        }
    
    def __repr__(self) -> str:
        return f"Detection(id={self.id}, class={self.class_name}, confidence={self.confidence:.2f})"


class SystemLog:
    """Represents a system log entry"""
    
    def __init__(self, log_id: int, level: str, module: str, message: str,
                 timestamp: datetime):
        """
        Initialize system log
        
        Args:
            log_id: Unique log identifier
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            module: Module that generated the log
            message: Log message
            timestamp: Log timestamp
        """
        self.id = log_id
        self.level = level
        self.module = module
        self.message = message
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log to dictionary"""
        return {
            "id": self.id,
            "level": self.level,
            "module": self.module,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }


class Alert:
    """Represents a system alert"""
    
    def __init__(self, alert_id: int, event_id: int, alert_type: str,
                 severity: str, message: str, timestamp: datetime):
        """
        Initialize alert
        
        Args:
            alert_id: Unique alert identifier
            event_id: ID of the event that triggered this alert
            alert_type: Type of alert (motion, detection, system)
            severity: Alert severity (low, medium, high)
            message: Alert message
            timestamp: Alert timestamp
        """
        self.id = alert_id
        self.event_id = event_id
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.timestamp = timestamp
        self.sent = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "sent": self.sent
        }


class Recording:
    """Represents a video recording"""
    
    def __init__(self, recording_id: int, camera_name: str, event_id: Optional[int],
                 start_time: datetime, file_path: str):
        """
        Initialize recording
        
        Args:
            recording_id: Unique recording identifier
            camera_name: Name of the camera
            event_id: ID of event that triggered recording (if any)
            start_time: Recording start time
            file_path: Path to recording file
        """
        self.id = recording_id
        self.camera_name = camera_name
        self.event_id = event_id
        self.start_time = start_time
        self.end_time = None
        self.file_path = file_path
        self.file_size = 0
        self.duration = 0
    
    def mark_complete(self, end_time: datetime, file_size: int) -> None:
        """Mark recording as complete"""
        self.end_time = end_time
        self.file_size = file_size
        self.duration = (end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert recording to dictionary"""
        return {
            "id": self.id,
            "camera_name": self.camera_name,
            "event_id": self.event_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "duration": self.duration
        }


class CameraStats:
    """Tracks statistics for a camera"""
    
    def __init__(self, camera_name: str):
        """
        Initialize camera statistics
        
        Args:
            camera_name: Name of the camera
        """
        self.camera_name = camera_name
        self.total_frames = 0
        self.motion_events = 0
        self.detection_events = 0
        self.total_detections = 0
        self.detections_by_class = {}
        self.uptime_start = datetime.now()
    
    def record_frame(self) -> None:
        """Record that a frame was processed"""
        self.total_frames += 1
    
    def record_motion_event(self) -> None:
        """Record a motion event"""
        self.motion_events += 1
    
    def record_detection(self, class_name: str) -> None:
        """Record an object detection"""
        self.total_detections += 1
        self.detections_by_class[class_name] = \
            self.detections_by_class.get(class_name, 0) + 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary"""
        uptime = (datetime.now() - self.uptime_start).total_seconds()
        return {
            "camera_name": self.camera_name,
            "total_frames": self.total_frames,
            "motion_events": self.motion_events,
            "detection_events": self.detection_events,
            "total_detections": self.total_detections,
            "detections_by_class": self.detections_by_class,
            "uptime_seconds": uptime
        }
