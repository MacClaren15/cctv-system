"""
Motion Detection Module
Detects movement in video frames using various algorithms
"""
import cv2
import numpy as np
from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


class MotionDetector:
    """Detects motion in video frames"""
    
    def __init__(self, config: dict):
        """
        Initialize motion detector
        
        Args:
            config: Configuration dictionary with motion detection settings
        """
        self.enabled = config.get("enabled", True)
        self.method = config.get("method", "background_subtraction")
        self.sensitivity = config.get("sensitivity", 0.3)
        self.min_area = config.get("min_area", 500)
        self.blur_kernel = config.get("blur_kernel", 21)
        self.dilate_kernel = config.get("dilate_kernel", 11)
        self.erode_kernel = config.get("erode_kernel", 9)
        
        # Initialize background subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True
        )
        
        self.previous_frame = None
        self.motion_detected = False
        self.motion_contours = []
        
    def detect(self, frame: np.ndarray) -> Tuple[bool, List[np.ndarray], float]:
        """
        Detect motion in frame
        
        Args:
            frame: Input video frame
            
        Returns:
            Tuple of (motion_detected, contours, sensitivity_ratio)
        """
        if not self.enabled or frame is None:
            return False, [], 0.0
        
        try:
            if self.method == "background_subtraction":
                return self._detect_background_subtraction(frame)
            elif self.method == "frame_diff":
                return self._detect_frame_difference(frame)
            elif self.method == "optical_flow":
                return self._detect_optical_flow(frame)
            else:
                logger.warning(f"Unknown detection method: {self.method}")
                return False, [], 0.0
                
        except Exception as e:
            logger.error(f"Error in motion detection: {e}")
            return False, [], 0.0
    
    def _detect_background_subtraction(self, frame: np.ndarray) -> Tuple[bool, List[np.ndarray], float]:
        """
        Detect motion using background subtraction
        """
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)
        
        # Apply morphological operations
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, 
            (self.erode_kernel, self.erode_kernel)
        )
        fg_mask = cv2.erode(fg_mask, kernel, iterations=1)
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(
            fg_mask, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter contours by area
        significant_contours = [
            c for c in contours 
            if cv2.contourArea(c) > self.min_area
        ]
        
        # Calculate motion ratio
        motion_pixels = cv2.countNonZero(fg_mask)
        total_pixels = frame.shape[0] * frame.shape[1]
        motion_ratio = motion_pixels / total_pixels if total_pixels > 0 else 0
        
        motion_detected = len(significant_contours) > 0 or motion_ratio > self.sensitivity
        self.motion_contours = significant_contours
        self.motion_detected = motion_detected
        
        return motion_detected, significant_contours, motion_ratio
    
    def _detect_frame_difference(self, frame: np.ndarray) -> Tuple[bool, List[np.ndarray], float]:
        """
        Detect motion using frame difference
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (self.blur_kernel, self.blur_kernel), 0)
        
        if self.previous_frame is None:
            self.previous_frame = blurred
            return False, [], 0.0
        
        # Calculate absolute difference
        frame_diff = cv2.absdiff(self.previous_frame, blurred)
        
        # Apply threshold
        _, thresh = cv2.threshold(
            frame_diff, 
            int(255 * self.sensitivity), 
            255, 
            cv2.THRESH_BINARY
        )
        
        # Apply morphological operations
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, 
            (self.dilate_kernel, self.dilate_kernel)
        )
        thresh = cv2.dilate(thresh, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(
            thresh, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter contours
        significant_contours = [
            c for c in contours 
            if cv2.contourArea(c) > self.min_area
        ]
        
        # Calculate motion ratio
        motion_pixels = cv2.countNonZero(thresh)
        total_pixels = frame.shape[0] * frame.shape[1]
        motion_ratio = motion_pixels / total_pixels if total_pixels > 0 else 0
        
        self.previous_frame = blurred
        self.motion_contours = significant_contours
        self.motion_detected = len(significant_contours) > 0
        
        return self.motion_detected, significant_contours, motion_ratio
    
    def _detect_optical_flow(self, frame: np.ndarray) -> Tuple[bool, List[np.ndarray], float]:
        """
        Detect motion using optical flow
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.previous_frame is None:
            self.previous_frame = gray
            return False, [], 0.0
        
        # Calculate optical flow
        flow = cv2.calcOpticalFlowFarneback(
            self.previous_frame, 
            gray, 
            None, 
            0.5, 
            3, 
            15, 
            3, 
            5, 
            1.2, 
            0
        )
        
        # Calculate magnitude of flow
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        
        # Apply threshold
        _, thresh = cv2.threshold(
            (mag * 255 / mag.max()).astype(np.uint8), 
            int(255 * self.sensitivity), 
            255, 
            cv2.THRESH_BINARY
        )
        
        # Find contours
        contours, _ = cv2.findContours(
            thresh, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter contours
        significant_contours = [
            c for c in contours 
            if cv2.contourArea(c) > self.min_area
        ]
        
        # Calculate motion ratio
        motion_ratio = np.mean(mag) / 255.0 if mag.size > 0 else 0
        
        self.previous_frame = gray
        self.motion_contours = significant_contours
        self.motion_detected = len(significant_contours) > 0 or motion_ratio > self.sensitivity
        
        return self.motion_detected, significant_contours, motion_ratio
    
    def draw_contours(self, frame: np.ndarray, contours: Optional[List] = None, color: Tuple = (0, 255, 0)) -> np.ndarray:
        """
        Draw motion contours on frame
        
        Args:
            frame: Input frame
            contours: List of contours (uses self.motion_contours if None)
            color: Color of contours in BGR format
            
        Returns:
            Frame with drawn contours
        """
        if contours is None:
            contours = self.motion_contours
        
        output = frame.copy()
        cv2.drawContours(output, contours, -1, color, 2)
        return output
    
    def reset(self) -> None:
        """Reset detector state"""
        self.previous_frame = None
        self.motion_detected = False
        self.motion_contours = []
        if hasattr(self, 'bg_subtractor'):
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                detectShadows=True
            )


class AdvancedMotionDetector(MotionDetector):
    """Enhanced motion detector with additional features"""
    
    def __init__(self, config: dict):
        """Initialize advanced motion detector"""
        super().__init__(config)
        self.motion_history = []
        self.max_history = 30
    
    def detect_with_history(self, frame: np.ndarray) -> dict:
        """
        Detect motion with historical context
        
        Returns:
            Dictionary with detection results and history
        """
        motion_detected, contours, ratio = self.detect(frame)
        
        # Update history
        self.motion_history.append({
            "detected": motion_detected,
            "ratio": ratio,
            "contours_count": len(contours)
        })
        
        if len(self.motion_history) > self.max_history:
            self.motion_history.pop(0)
        
        # Calculate trend
        recent_history = self.motion_history[-10:]
        motion_trend = sum(1 for h in recent_history if h["detected"]) / len(recent_history)
        
        return {
            "motion_detected": motion_detected,
            "contours": contours,
            "motion_ratio": ratio,
            "motion_trend": motion_trend,
            "history_length": len(self.motion_history)
        }
