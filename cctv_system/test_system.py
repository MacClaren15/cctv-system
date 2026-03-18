"""
Quick test script for CCTV System components
Run: python test_system.py
"""
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        import cv2
        logger.info(f"✓ OpenCV {cv2.__version__}")
    except ImportError as e:
        logger.error(f"✗ OpenCV: {e}")
        return False
    
    try:
        import numpy
        logger.info(f"✓ NumPy {numpy.__version__}")
    except ImportError as e:
        logger.error(f"✗ NumPy: {e}")
        return False
    
    try:
        import torch
        logger.info(f"✓ PyTorch {torch.__version__}")
    except ImportError as e:
        logger.warning(f"⚠ PyTorch not available: {e} (optional, may need Windows long path support)")
    
    try:
        from ultralytics import YOLO
        logger.info("✓ YOLOv8 (ultralytics)")
    except ImportError as e:
        logger.warning(f"⚠ YOLOv8 not available: {e} (optional, requires PyTorch)")
    
    try:
        from flask import Flask
        logger.info("✓ Flask")
    except ImportError as e:
        logger.error(f"✗ Flask: {e}")
        return False
    
    try:
        from config import config
        logger.info("✓ Config module")
    except ImportError as e:
        logger.error(f"✗ Config: {e}")
        return False
    
    try:
        from core.motion_detector import MotionDetector
        logger.info("✓ Motion Detector")
    except ImportError as e:
        logger.error(f"✗ Motion Detector: {e}")
        return False
    
    try:
        from core.object_detector import ObjectDetector
        logger.info("✓ Object Detector")
    except ImportError as e:
        logger.warning(f"⚠ Object Detector not available: {e} (requires ultralytics/torch)")
    
    try:
        from core.camera import CameraStream
        logger.info("✓ Camera Module")
    except ImportError as e:
        logger.error(f"✗ Camera Module: {e}")
        return False
    
    return True


def test_directories():
    """Test if required directories exist or can be created"""
    logger.info("\nTesting directories...")
    
    required_dirs = [
        "./data",
        "./data/logs",
        "./data/recordings",
        "./data/events"
    ]
    
    for directory in required_dirs:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ {directory}")
        except Exception as e:
            logger.error(f"✗ {directory}: {e}")
            return False
    
    return True


def test_configuration():
    """Test configuration loading"""
    logger.info("\nTesting configuration...")
    
    try:
        from config import config
        
        # Test basic config attributes
        assert hasattr(config, 'CAMERAS'), "Missing CAMERAS config"
        assert hasattr(config, 'MOTION_DETECTION'), "Missing MOTION_DETECTION config"
        assert hasattr(config, 'OBJECT_DETECTION'), "Missing OBJECT_DETECTION config"
        
        logger.info(f"✓ Configuration loaded")
        logger.info(f"  - Cameras: {len(config.CAMERAS)} configured")
        logger.info(f"  - Motion Detection: {config.MOTION_DETECTION['enabled']}")
        logger.info(f"  - Object Detection: {config.OBJECT_DETECTION['enabled']}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Configuration: {e}")
        return False


def test_motion_detector():
    """Test motion detector initialization"""
    logger.info("\nTesting motion detector...")
    
    try:
        from config import config
        from core.motion_detector import MotionDetector
        
        detector = MotionDetector(config.MOTION_DETECTION)
        logger.info(f"✓ Motion detector initialized")
        logger.info(f"  - Method: {detector.method}")
        logger.info(f"  - Sensitivity: {detector.sensitivity}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Motion detector: {e}")
        return False


def test_camera_availability():
    """Test if camera is available"""
    logger.info("\nTesting camera availability...")
    
    try:
        import cv2
        
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                logger.info(f"✓ Camera available (0x{frame.shape[0]}x{frame.shape[1]})")
                return True
            else:
                logger.warning("⚠ Camera found but can't read frames")
                return False
        else:
            logger.warning("⚠ Camera not available (you can still run without webcam)")
            return False
    
    except Exception as e:
        logger.warning(f"⚠ Camera test: {e}")
        return False


def test_api():
    """Test Flask API initialization"""
    logger.info("\nTesting API...")
    
    try:
        from api.app import create_app
        
        app = create_app()
        logger.info(f"✓ Flask app created")
        
        with app.test_client() as client:
            response = client.get('/api/v1/health')
            if response.status_code == 200:
                logger.info(f"✓ Health check endpoint working")
            else:
                logger.warning(f"⚠ Health check returned {response.status_code}")
        
        return True
    except Exception as e:
        logger.error(f"✗ API test: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("CCTV System Component Tests")
    logger.info("=" * 60)
    
    results = {
        "Imports": test_imports(),
        "Directories": test_directories(),
        "Configuration": test_configuration(),
        "Motion Detector": test_motion_detector(),
        "Camera": test_camera_availability(),
        "API": test_api(),
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status:8} {test_name}")
    
    logger.info("=" * 60)
    logger.info(f"Total: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("\n✓ All tests passed! System is ready to run.")
        logger.info("Start with: python main.py")
        return 0
    else:
        logger.warning(f"\n⚠ {total - passed} test(s) failed. Check logs above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
