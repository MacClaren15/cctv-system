"""
CCTV System Processor
Main orchestration module for the motion detection and object detection system
"""
import threading
import logging
import time
from datetime import datetime
from typing import Dict, Optional, List, Any
from collections import defaultdict

from config import config
from core.camera import MultiCameraManager, CameraStream
from core.motion_detector import AdvancedMotionDetector
from models.data_models import Event, Detection, Alert, CameraStats

# Try to import object detection modules (optional - requires ultralytics/torch)
try:
    from core.object_detector import ObjectDetector, MultiObjectTracker
    HAS_OBJECT_DETECTION = True
except ImportError:
    ObjectDetector = None
    MultiObjectTracker = None
    HAS_OBJECT_DETECTION = False

logger = logging.getLogger(__name__)


class CCTVProcessor:
    """Main CCTV system processor"""
    
    def __init__(self):
        """Initialize CCTV processor"""
        self.camera_manager = MultiCameraManager(config.CAMERAS)
        self.motion_detectors = {}
        self.object_detectors = {}
        self.object_trackers = {}
        self.camera_stats = {}
        
        self.events = []
        self.detections = []
        self.alerts = []
        
        self.last_alert_time = defaultdict(float)
        self.is_running = False
        self.processing_thread = None
        
        self._initialize_detectors()
        self._initialize_stats()
    
    def _initialize_detectors(self) -> None:
        """Initialize motion and object detectors for each camera"""
        for camera_name in self.camera_manager.get_active_camera_names():
            # Initialize motion detector
            self.motion_detectors[camera_name] = AdvancedMotionDetector(
                config.MOTION_DETECTION
            )
            
            # Initialize object detector (optional)
            if HAS_OBJECT_DETECTION and ObjectDetector is not None:
                try:
                    self.object_detectors[camera_name] = ObjectDetector(
                        config.OBJECT_DETECTION
                    )
                    
                    # Initialize object tracker
                    self.object_trackers[camera_name] = MultiObjectTracker(
                        config.OBJECT_DETECTION
                    )
                    logger.info(f"Object detection initialized for {camera_name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize object detection for {camera_name}: {e}")
                    self.object_detectors[camera_name] = None
                    self.object_trackers[camera_name] = None
            else:
                logger.info(f"Object detection disabled for {camera_name} (ultralytics/torch not available)")
                self.object_detectors[camera_name] = None
                self.object_trackers[camera_name] = None
            
            logger.info(f"Motion detection initialized for {camera_name}")
    
    def _initialize_stats(self) -> None:
        """Initialize statistics for each camera"""
        for camera_name in self.camera_manager.get_active_camera_names():
            self.camera_stats[camera_name] = CameraStats(camera_name)
    
    def start(self) -> None:
        """Start the CCTV system"""
        if self.is_running:
            logger.warning("CCTV system is already running")
            return
        
        self.is_running = True
        
        # Start camera streams
        self.camera_manager.start_all()
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self.processing_thread.start()
        
        logger.info("CCTV system started")
    
    def stop(self) -> None:
        """Stop the CCTV system"""
        if not self.is_running:
            logger.warning("CCTV system is not running")
            return
        
        self.is_running = False
        
        # Stop camera streams
        self.camera_manager.stop_all()
        
        # Wait for processing thread
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        
        logger.info("CCTV system stopped")
    
    def _processing_loop(self) -> None:
        """Main processing loop that runs in background thread"""
        frame_skip_counter = 0
        skip_frames = config.PERFORMANCE.get("frame_skip", 1)
        
        while self.is_running:
            try:
                # Skip frames if configured
                frame_skip_counter += 1
                if frame_skip_counter < skip_frames:
                    time.sleep(0.01)
                    continue
                
                frame_skip_counter = 0
                
                # Get frames from all cameras
                frames = self.camera_manager.get_all_frames()
                
                # Process each frame
                for camera_name, (frame, timestamp) in frames.items():
                    self._process_frame(camera_name, frame, timestamp)
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(0.1)
    
    def _process_frame(self, camera_name: str, frame, timestamp: float) -> None:
        """
        Process a single frame
        
        Args:
            camera_name: Name of the camera
            frame: Video frame
            timestamp: Frame timestamp
        """
        try:
            # Update stats
            self.camera_stats[camera_name].record_frame()
            
            # Motion detection
            motion_result = self.motion_detectors[camera_name].detect_with_history(frame)
            motion_detected = motion_result["motion_detected"]
            
            # Object detection (optional)
            objects_detected = False
            detections = []
            tracked_objects = []
            
            if self.object_detectors.get(camera_name) is not None:
                try:
                    detection_result = self.object_detectors[camera_name].detect(frame)
                    objects_detected = detection_result["detected"]
                    detections = detection_result["detections"]
                    
                    # Track objects
                    if objects_detected and self.object_trackers.get(camera_name) is not None:
                        tracked_objects = self.object_trackers[camera_name].update(detections)
                except Exception as e:
                    logger.warning(f"Object detection error for {camera_name}: {e}")
            
            # Handle motion event
            if motion_detected and config.MOTION_DETECTION.get("enabled", True):
                self._handle_motion_event(camera_name, motion_result, timestamp)
            
            # Handle detection event
            if objects_detected and config.OBJECT_DETECTION.get("enabled", True):
                self._handle_detection_event(
                    camera_name, 
                    detections, 
                    timestamp
                )
            
        except Exception as e:
            logger.error(f"Error processing frame from {camera_name}: {e}")
    
    def _handle_motion_event(self, camera_name: str, motion_result: Dict, timestamp: float) -> None:
        """Handle motion detection event"""
        try:
            event = Event(
                event_id=len(self.events) + 1,
                event_type="motion",
                camera_name=camera_name,
                timestamp=datetime.fromtimestamp(timestamp),
                details={
                    "motion_ratio": motion_result["motion_ratio"],
                    "motion_trend": motion_result["motion_trend"],
                    "contours_count": motion_result["contours_count"]
                }
            )
            
            self.events.append(event)
            self.camera_stats[camera_name].record_motion_event()
            
            # Generate alert if configured
            if config.ALERTS.get("motion_alert", True):
                self._generate_alert(
                    event.id,
                    "motion",
                    "high",
                    f"Motion detected on {camera_name}"
                )
            
            logger.debug(f"Motion event recorded: {event}")
            
        except Exception as e:
            logger.error(f"Error handling motion event: {e}")
    
    def _handle_detection_event(self, camera_name: str, detections: List[Dict], 
                                timestamp: float) -> None:
        """Handle object detection event"""
        try:
            if not detections:
                return
            
            event = Event(
                event_id=len(self.events) + 1,
                event_type="detection",
                camera_name=camera_name,
                timestamp=datetime.fromtimestamp(timestamp),
                details={
                    "detection_count": len(detections),
                    "classes": list(set(d["class"] for d in detections))
                }
            )
            
            self.events.append(event)
            
            # Record detections
            for detection_data in detections:
                detection = Detection(
                    detection_id=len(self.detections) + 1,
                    event_id=event.id,
                    class_name=detection_data["class"],
                    confidence=detection_data["confidence"],
                    bbox=detection_data["bbox"],
                    timestamp=datetime.fromtimestamp(timestamp)
                )
                
                self.detections.append(detection)
                self.camera_stats[camera_name].record_detection(detection.class_name)
            
            # Generate alert if configured
            if config.ALERTS.get("detection_alert", True):
                classes_str = ", ".join(event.details["classes"])
                self._generate_alert(
                    event.id,
                    "detection",
                    "medium",
                    f"Objects detected on {camera_name}: {classes_str}"
                )
            
            logger.debug(f"Detection event recorded: {event}")
            
        except Exception as e:
            logger.error(f"Error handling detection event: {e}")
    
    def _generate_alert(self, event_id: int, alert_type: str, severity: str,
                       message: str) -> None:
        """Generate an alert with cooldown"""
        try:
            # Check alert cooldown
            alert_key = f"{alert_type}_{message[:20]}"
            cooldown = config.ALERTS.get("alert_cooldown", 60)
            
            if time.time() - self.last_alert_time[alert_key] < cooldown:
                return
            
            self.last_alert_time[alert_key] = time.time()
            
            alert = Alert(
                alert_id=len(self.alerts) + 1,
                event_id=event_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                timestamp=datetime.now()
            )
            
            self.alerts.append(alert)
            logger.warning(f"Alert: {message}")
            
            # TODO: Send email/Slack alerts if configured
            
        except Exception as e:
            logger.error(f"Error generating alert: {e}")
    
    def get_frame_with_annotations(self, camera_name: str) -> Optional:
        """
        Get current frame with motion and object detection annotations
        
        Args:
            camera_name: Name of the camera
            
        Returns:
            Annotated frame or None
        """
        try:
            frame_data = self.camera_manager.get_frame(camera_name)
            if frame_data is None:
                return None
            
            frame, timestamp = frame_data
            
            # Draw motion contours
            motion_detector = self.motion_detectors[camera_name]
            frame = motion_detector.draw_contours(frame, color=(0, 255, 0))
            
            # Draw object detections (if available)
            object_detector = self.object_detectors.get(camera_name)
            if object_detector is not None:
                frame = object_detector.draw_detections(frame)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error getting annotated frame: {e}")
            return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "is_running": self.is_running,
            "total_events": len(self.events),
            "total_detections": len(self.detections),
            "total_alerts": len(self.alerts),
            "cameras": self.camera_manager.get_all_camera_info(),
            "stats": {
                name: stats.to_dict()
                for name, stats in self.camera_stats.items()
            }
        }
    
    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        """Get recent events"""
        return [event.to_dict() for event in self.events[-limit:]]
    
    def get_recent_detections(self, limit: int = 100) -> List[Dict]:
        """Get recent detections"""
        return [det.to_dict() for det in self.detections[-limit:]]
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts"""
        return [alert.to_dict() for alert in self.alerts[-limit:]]


# Global processor instance
processor = None


def initialize_processor() -> CCTVProcessor:
    """Initialize and return the global processor"""
    global processor
    if processor is None:
        processor = CCTVProcessor()
    return processor


def get_processor() -> CCTVProcessor:
    """Get the global processor instance"""
    global processor
    if processor is None:
        processor = CCTVProcessor()
    return processor
