"""
Object Detection Module
Detects objects using YOLOv8
"""
import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
import logging
from ultralytics import YOLO
from pathlib import Path

logger = logging.getLogger(__name__)


class ObjectDetector:
    """Detects objects in video frames using YOLOv8"""
    
    def __init__(self, config: dict):
        """
        Initialize object detector
        
        Args:
            config: Configuration dictionary with object detection settings
        """
        self.enabled = config.get("enabled", True)
        self.model_name = config.get("model", "yolov8m")
        self.confidence_threshold = config.get("confidence_threshold", 0.5)
        self.iou_threshold = config.get("iou_threshold", 0.45)
        self.device = config.get("device", "cpu")
        self.target_classes = config.get("classes", ["person", "car"])
        
        self.model = None
        self.class_names = {}
        self.detections = []
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Load YOLOv8 model"""
        try:
            self.model = YOLO(f"{self.model_name}.pt")
            self.model.to(self.device)
            
            # Get class names
            self.class_names = self.model.names
            
            # Verify target classes exist
            available_classes = list(self.class_names.values())
            self.target_classes = [
                c for c in self.target_classes 
                if c in available_classes
            ]
            
            if not self.target_classes:
                self.target_classes = list(available_classes)
            
            logger.info(f"Loaded YOLOv8 model: {self.model_name} on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            self.enabled = False
    
    def detect(self, frame: np.ndarray) -> Dict[str, any]:
        """
        Detect objects in frame
        
        Args:
            frame: Input video frame
            
        Returns:
            Dictionary containing detection results
        """
        if not self.enabled or self.model is None or frame is None:
            return {
                "detected": False,
                "detections": [],
                "frame_shape": (0, 0, 0) if frame is None else frame.shape
            }
        
        try:
            # Run inference
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                verbose=False
            )
            
            # Process detections
            detections = self._process_results(results, frame)
            self.detections = detections
            
            return {
                "detected": len(detections) > 0,
                "detections": detections,
                "frame_shape": frame.shape,
                "detection_count": len(detections)
            }
            
        except Exception as e:
            logger.error(f"Error in object detection: {e}")
            return {
                "detected": False,
                "detections": [],
                "frame_shape": frame.shape
            }
    
    def _process_results(self, results, frame: np.ndarray) -> List[Dict]:
        """
        Process YOLO results
        
        Args:
            results: YOLOv8 results object
            frame: Input frame for reference
            
        Returns:
            List of detection dictionaries
        """
        detections = []
        
        if results[0].boxes is None or len(results[0].boxes) == 0:
            return detections
        
        for box in results[0].boxes:
            # Get bounding box coordinates
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            
            # Get confidence and class
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = self.class_names.get(class_id, "Unknown")
            
            # Filter by target classes
            if class_name not in self.target_classes:
                continue
            
            # Calculate additional properties
            width = x2 - x1
            height = y2 - y1
            center_x = x1 + width // 2
            center_y = y1 + height // 2
            area = width * height
            
            detection = {
                "class": class_name,
                "confidence": confidence,
                "bbox": {
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2),
                    "width": int(width),
                    "height": int(height)
                },
                "center": {
                    "x": int(center_x),
                    "y": int(center_y)
                },
                "area": int(area)
            }
            
            detections.append(detection)
        
        return detections
    
    def draw_detections(self, frame: np.ndarray, detections: Optional[List[Dict]] = None) -> np.ndarray:
        """
        Draw detections on frame
        
        Args:
            frame: Input frame
            detections: List of detections (uses self.detections if None)
            
        Returns:
            Frame with drawn detections
        """
        if detections is None:
            detections = self.detections
        
        output = frame.copy()
        
        for detection in detections:
            bbox = detection["bbox"]
            x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
            
            # Draw bounding box
            color = (0, 255, 0) if detection["confidence"] > 0.7 else (0, 165, 255)
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{detection['class']}: {detection['confidence']:.2f}"
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            
            cv2.rectangle(
                output,
                (x1, y1 - text_size[1] - 5),
                (x1 + text_size[0], y1),
                color,
                -1
            )
            cv2.putText(
                output,
                label,
                (x1, y1 - 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
        
        return output
    
    def get_detections_by_class(self, class_name: str) -> List[Dict]:
        """Get detections filtered by class name"""
        return [d for d in self.detections if d["class"] == class_name]
    
    def get_high_confidence_detections(self, threshold: float = 0.7) -> List[Dict]:
        """Get detections with high confidence"""
        return [d for d in self.detections if d["confidence"] > threshold]
    
    def reset(self) -> None:
        """Reset detector state"""
        self.detections = []


class TrackedObject:
    """Represents a tracked object across frames"""
    
    def __init__(self, object_id: int, initial_detection: Dict):
        """Initialize tracked object"""
        self.id = object_id
        self.class_name = initial_detection["class"]
        self.detections = [initial_detection]
        self.last_update = 0
        self.frames_since_update = 0
    
    def update(self, detection: Dict) -> None:
        """Update tracked object with new detection"""
        self.detections.append(detection)
        self.last_update = 0
        self.frames_since_update = 0
    
    def age_update(self) -> None:
        """Increment frames since last update"""
        self.frames_since_update += 1
        self.last_update += 1
    
    def get_trajectory(self) -> List[Tuple[int, int]]:
        """Get trajectory as list of center points"""
        return [
            (d["center"]["x"], d["center"]["y"]) 
            for d in self.detections
        ]
    
    def is_stale(self, max_frames: int = 30) -> bool:
        """Check if object should be removed (not updated)"""
        return self.frames_since_update > max_frames


class MultiObjectTracker:
    """Tracks multiple objects across frames"""
    
    def __init__(self, config: dict, max_distance: float = 50):
        """
        Initialize multi-object tracker
        
        Args:
            config: Configuration dictionary
            max_distance: Maximum distance for object association
        """
        self.config = config
        self.max_distance = max_distance
        self.tracked_objects: Dict[int, TrackedObject] = {}
        self.next_id = 0
    
    def update(self, detections: List[Dict]) -> Dict[int, TrackedObject]:
        """
        Update tracker with new detections
        
        Args:
            detections: List of detected objects
            
        Returns:
            Dictionary of tracked objects
        """
        # Age all tracked objects
        for obj in self.tracked_objects.values():
            obj.age_update()
        
        # Match new detections to existing tracks
        matched_indices = self._match_detections(detections)
        
        # Update matched tracks
        for det_idx, track_idx in matched_indices:
            obj = self.tracked_objects[track_idx]
            obj.update(detections[det_idx])
        
        # Create new tracks for unmatched detections
        for det_idx, detection in enumerate(detections):
            if det_idx not in [m[0] for m in matched_indices]:
                self.tracked_objects[self.next_id] = TrackedObject(self.next_id, detection)
                self.next_id += 1
        
        # Remove stale tracks
        stale_ids = [
            obj_id for obj_id, obj in self.tracked_objects.items()
            if obj.is_stale()
        ]
        for obj_id in stale_ids:
            del self.tracked_objects[obj_id]
        
        return self.tracked_objects
    
    def _match_detections(self, detections: List[Dict]) -> List[Tuple[int, int]]:
        """
        Match detections to tracked objects using centroid distance
        
        Returns:
            List of (detection_index, track_id) tuples
        """
        matched = []
        
        for det_idx, detection in enumerate(detections):
            best_distance = float('inf')
            best_track_id = None
            
            det_center = detection["center"]
            det_point = (det_center["x"], det_center["y"])
            
            for track_id, obj in self.tracked_objects.items():
                if obj.frames_since_update > 10:  # Don't match old tracks
                    continue
                
                track_center = obj.detections[-1]["center"]
                track_point = (track_center["x"], track_center["y"])
                
                # Calculate Euclidean distance
                distance = np.sqrt(
                    (det_point[0] - track_point[0]) ** 2 +
                    (det_point[1] - track_point[1]) ** 2
                )
                
                if distance < self.max_distance and distance < best_distance:
                    best_distance = distance
                    best_track_id = track_id
            
            if best_track_id is not None:
                matched.append((det_idx, best_track_id))
        
        return matched
    
    def reset(self) -> None:
        """Reset tracker"""
        self.tracked_objects.clear()
        self.next_id = 0
