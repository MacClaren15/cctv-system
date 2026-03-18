"""
Camera Management Module
Handles camera initialization and frame capture
"""
import cv2
import numpy as np
import threading
import logging
from typing import Optional, Dict, Tuple
from queue import Queue, Empty
import time

logger = logging.getLogger(__name__)


class CameraStream:
    """Manages a single camera stream"""
    
    def __init__(self, camera_id: int, config: dict):
        """
        Initialize camera stream
        
        Args:
            camera_id: Camera index (0, 1, etc.)
            config: Camera configuration dictionary
        """
        self.camera_id = camera_id
        self.name = config.get("name", f"camera_{camera_id}")
        self.enabled = config.get("enabled", True)
        self.resolution = config.get("resolution", [1280, 720])
        self.fps = config.get("fps", 30)
        self.rotation = config.get("rotation", 0)
        
        self.cap = None
        self.frame_queue = Queue(maxsize=2)
        self.is_running = False
        self.thread = None
        self.last_frame = None
        self.frame_count = 0
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0
        
        self._initialize_camera()
    
    def _initialize_camera(self) -> bool:
        """Initialize camera capture"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_id}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            logger.info(f"Camera {self.camera_id} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing camera {self.camera_id}: {e}")
            return False
    
    def start(self) -> None:
        """Start capturing frames in background thread"""
        if self.is_running:
            logger.warning(f"Camera {self.camera_id} is already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_thread, daemon=True)
        self.thread.start()
        logger.info(f"Camera {self.camera_id} capture thread started")
    
    def _capture_thread(self) -> None:
        """Capture frames in background thread"""
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.warning(f"Failed to read frame from camera {self.camera_id}")
                    continue
                
                # Apply rotation if needed
                if self.rotation != 0:
                    frame = self._rotate_frame(frame, self.rotation)
                
                self.last_frame = frame
                self.frame_count += 1
                
                # Update FPS counter
                self.fps_counter += 1
                current_time = time.time()
                elapsed = current_time - self.fps_timer
                
                if elapsed >= 1.0:
                    self.current_fps = self.fps_counter / elapsed
                    self.fps_counter = 0
                    self.fps_timer = current_time
                
                # Try to put frame in queue (non-blocking)
                try:
                    self.frame_queue.put_nowait((frame, time.time()))
                except:
                    # Queue is full, remove oldest frame
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait((frame, time.time()))
                    except:
                        pass
                
            except Exception as e:
                logger.error(f"Error in capture thread for camera {self.camera_id}: {e}")
                continue
    
    def get_frame(self, timeout: float = 1.0) -> Optional[Tuple[np.ndarray, float]]:
        """
        Get latest frame from queue
        
        Args:
            timeout: Queue timeout in seconds
            
        Returns:
            Tuple of (frame, timestamp) or None if no frame available
        """
        try:
            return self.frame_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get latest captured frame (may be old if thread is slow)"""
        return self.last_frame
    
    def _rotate_frame(self, frame: np.ndarray, angle: int) -> np.ndarray:
        """Rotate frame"""
        if angle == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame
    
    def stop(self) -> None:
        """Stop capturing frames"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
        
        logger.info(f"Camera {self.camera_id} stopped")
    
    def get_info(self) -> Dict:
        """Get camera information"""
        return {
            "camera_id": self.camera_id,
            "name": self.name,
            "enabled": self.enabled,
            "resolution": self.resolution,
            "fps": self.fps,
            "current_fps": round(self.current_fps, 2),
            "frame_count": self.frame_count,
            "is_running": self.is_running
        }


class MultiCameraManager:
    """Manages multiple camera streams"""
    
    def __init__(self, cameras_config: Dict):
        """
        Initialize camera manager
        
        Args:
            cameras_config: Dictionary of camera configurations
        """
        self.cameras: Dict[str, CameraStream] = {}
        self.active_cameras = []
        
        for camera_name, config in cameras_config.items():
            if config.get("enabled", True):
                camera_index = config.get("camera_index", 0)
                camera = CameraStream(camera_index, config)
                self.cameras[camera_name] = camera
                self.active_cameras.append(camera_name)
        
        logger.info(f"Initialized {len(self.active_cameras)} cameras")
    
    def start_all(self) -> None:
        """Start all camera streams"""
        for camera in self.cameras.values():
            if camera.enabled:
                camera.start()
    
    def start_camera(self, camera_name: str) -> bool:
        """Start specific camera"""
        if camera_name in self.cameras:
            self.cameras[camera_name].start()
            return True
        return False
    
    def get_frame(self, camera_name: str) -> Optional[Tuple[np.ndarray, float]]:
        """
        Get frame from specific camera
        
        Args:
            camera_name: Name of the camera
            
        Returns:
            Tuple of (frame, timestamp) or None
        """
        if camera_name in self.cameras:
            return self.cameras[camera_name].get_frame()
        return None
    
    def get_all_frames(self) -> Dict[str, Tuple[np.ndarray, float]]:
        """
        Get frames from all active cameras
        
        Returns:
            Dictionary of {camera_name: (frame, timestamp)}
        """
        frames = {}
        for camera_name in self.active_cameras:
            frame_data = self.get_frame(camera_name)
            if frame_data:
                frames[camera_name] = frame_data
        return frames
    
    def stop_all(self) -> None:
        """Stop all camera streams"""
        for camera in self.cameras.values():
            camera.stop()
    
    def stop_camera(self, camera_name: str) -> bool:
        """Stop specific camera"""
        if camera_name in self.cameras:
            self.cameras[camera_name].stop()
            return True
        return False
    
    def get_camera_info(self, camera_name: str) -> Optional[Dict]:
        """Get information about specific camera"""
        if camera_name in self.cameras:
            return self.cameras[camera_name].get_info()
        return None
    
    def get_all_camera_info(self) -> Dict[str, Dict]:
        """Get information about all cameras"""
        return {
            name: camera.get_info()
            for name, camera in self.cameras.items()
        }
    
    def get_active_camera_names(self) -> list:
        """Get list of active camera names"""
        return self.active_cameras
