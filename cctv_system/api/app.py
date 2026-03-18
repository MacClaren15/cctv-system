"""
REST API for CCTV System
Provides endpoints for monitoring and controlling the CCTV system
"""
from flask import Flask, jsonify, request, render_template, stream_with_context, \
    Response
from flask_cors import CORS
import cv2
import logging
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from config import config
from core.processor import get_processor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the project root directory
project_root = Path(__file__).parent.parent

# Create Flask app with correct template and static paths
app = Flask(
    __name__,
    template_folder=str(project_root / 'web' / 'templates'),
    static_folder=str(project_root / 'web' / 'static')
)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = config.WEB.get('secret_key', 'default-secret')
app.config['JSON_SORT_KEYS'] = False

# Get CCTV processor
processor = None


def require_auth(f):
    """Decorator to require authentication if enabled"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if config.API.get("enable_auth", False):
            api_key = request.headers.get("X-API-Key")
            if not api_key or api_key != config.API.get("api_key"):
                return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function


# ==================== STATUS ENDPOINTS ====================

@app.route('/api/v1/status', methods=['GET'])
@require_auth
def get_status():
    """Get system status"""
    try:
        status = processor.get_system_status()
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200


# ==================== CAMERA ENDPOINTS ====================

@app.route('/api/v1/cameras', methods=['GET'])
@require_auth
def get_cameras():
    """Get information about all cameras"""
    try:
        cameras = processor.camera_manager.get_all_camera_info()
        return jsonify({
            "total_cameras": len(cameras),
            "cameras": cameras
        }), 200
    except Exception as e:
        logger.error(f"Error getting cameras: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/cameras/<camera_name>', methods=['GET'])
@require_auth
def get_camera(camera_name):
    """Get information about specific camera"""
    try:
        camera_info = processor.camera_manager.get_camera_info(camera_name)
        if camera_info is None:
            return jsonify({"error": "Camera not found"}), 404
        return jsonify(camera_info), 200
    except Exception as e:
        logger.error(f"Error getting camera info: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/cameras/<camera_name>/start', methods=['POST'])
@require_auth
def start_camera(camera_name):
    """Start specific camera"""
    try:
        success = processor.camera_manager.start_camera(camera_name)
        if success:
            return jsonify({"message": f"Camera {camera_name} started"}), 200
        else:
            return jsonify({"error": "Camera not found"}), 404
    except Exception as e:
        logger.error(f"Error starting camera: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/cameras/<camera_name>/stop', methods=['POST'])
@require_auth
def stop_camera(camera_name):
    """Stop specific camera"""
    try:
        success = processor.camera_manager.stop_camera(camera_name)
        if success:
            return jsonify({"message": f"Camera {camera_name} stopped"}), 200
        else:
            return jsonify({"error": "Camera not found"}), 404
    except Exception as e:
        logger.error(f"Error stopping camera: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== FRAME STREAMING ====================

def generate_frames(camera_name: str):
    """Generate frames for video streaming"""
    while True:
        try:
            frame = processor.get_frame_with_annotations(camera_name)
            if frame is None:
                continue
            
            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                   + frame_bytes + b'\r\n')
        except Exception as e:
            logger.error(f"Error generating frames: {e}")
            break


@app.route('/api/v1/cameras/<camera_name>/stream')
@require_auth
def video_stream(camera_name):
    """Stream video from camera"""
    try:
        if camera_name not in processor.camera_manager.cameras:
            return "Camera not found", 404
        
        return Response(
            generate_frames(camera_name),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        logger.error(f"Error streaming video: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== EVENT ENDPOINTS ====================

@app.route('/api/v1/events', methods=['GET'])
@require_auth
def get_events():
    """Get recent events"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        events = processor.get_recent_events(limit)
        return jsonify({
            "total_events": len(processor.events),
            "recent_events": events
        }), 200
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/events/filter', methods=['POST'])
@require_auth
def filter_events():
    """Filter events by criteria"""
    try:
        data = request.get_json()
        event_type = data.get('type')
        camera_name = data.get('camera')
        days = data.get('days', 1)
        
        cutoff_time = datetime.now() - timedelta(days=days)
        
        filtered = [
            e for e in processor.events
            if (not event_type or e.event_type == event_type) and
               (not camera_name or e.camera_name == camera_name) and
               e.timestamp >= cutoff_time
        ]
        
        return jsonify({
            "total_matching": len(filtered),
            "events": [e.to_dict() for e in filtered]
        }), 200
    except Exception as e:
        logger.error(f"Error filtering events: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== DETECTION ENDPOINTS ====================

@app.route('/api/v1/detections', methods=['GET'])
@require_auth
def get_detections():
    """Get recent detections"""
    try:
        limit = request.args.get('limit', default=100, type=int)
        detections = processor.get_recent_detections(limit)
        return jsonify({
            "total_detections": len(processor.detections),
            "recent_detections": detections
        }), 200
    except Exception as e:
        logger.error(f"Error getting detections: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/detections/by-class', methods=['GET'])
@require_auth
def detections_by_class():
    """Get detections grouped by class"""
    try:
        from collections import defaultdict
        by_class = defaultdict(list)
        
        for detection in processor.detections:
            by_class[detection.class_name].append(detection.to_dict())
        
        return jsonify({
            "by_class": {k: v for k, v in by_class.items()}
        }), 200
    except Exception as e:
        logger.error(f"Error getting detections by class: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== ALERT ENDPOINTS ====================

@app.route('/api/v1/alerts', methods=['GET'])
@require_auth
def get_alerts():
    """Get recent alerts"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        alerts = processor.get_recent_alerts(limit)
        return jsonify({
            "total_alerts": len(processor.alerts),
            "recent_alerts": alerts
        }), 200
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== STATISTICS ENDPOINTS ====================

@app.route('/api/v1/stats/cameras', methods=['GET'])
@require_auth
def camera_stats():
    """Get camera statistics"""
    try:
        stats = {
            name: stats_obj.to_dict()
            for name, stats_obj in processor.camera_stats.items()
        }
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/stats/summary', methods=['GET'])
@require_auth
def stats_summary():
    """Get summary statistics"""
    try:
        total_frames = sum(s.total_frames for s in processor.camera_stats.values())
        total_motion = sum(s.motion_events for s in processor.camera_stats.values())
        total_objects = sum(s.total_detections for s in processor.camera_stats.values())
        
        return jsonify({
            "total_frames_processed": total_frames,
            "total_motion_events": total_motion,
            "total_objects_detected": total_objects,
            "total_events": len(processor.events),
            "total_alerts": len(processor.alerts)
        }), 200
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== CONTROL ENDPOINTS ====================

@app.route('/api/v1/control/start', methods=['POST'])
@require_auth
def control_start():
    """Start CCTV system"""
    try:
        if not processor.is_running:
            processor.start()
        return jsonify({"message": "CCTV system started"}), 200
    except Exception as e:
        logger.error(f"Error starting system: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/control/stop', methods=['POST'])
@require_auth
def control_stop():
    """Stop CCTV system"""
    try:
        if processor.is_running:
            processor.stop()
        return jsonify({"message": "CCTV system stopped"}), 200
    except Exception as e:
        logger.error(f"Error stopping system: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/control/restart', methods=['POST'])
@require_auth
def control_restart():
    """Restart CCTV system"""
    try:
        processor.stop()
        import time
        time.sleep(1)
        processor.start()
        return jsonify({"message": "CCTV system restarted"}), 200
    except Exception as e:
        logger.error(f"Error restarting system: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== WEB DASHBOARD ====================

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/camera/<camera_name>')
def camera_view(camera_name):
    """Single camera view"""
    return render_template('camera.html', camera_name=camera_name)


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


def create_app():
    """Create and configure Flask app"""
    global processor
    processor = get_processor()
    
    logger.info(f"Flask app created with config:")
    logger.info(f"  Host: {config.WEB.get('host')}")
    logger.info(f"  Port: {config.WEB.get('port')}")
    logger.info(f"  Debug: {config.WEB.get('debug')}")
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=config.WEB.get('host', '0.0.0.0'),
        port=config.WEB.get('port', 5000),
        debug=config.WEB.get('debug', False),
        threaded=True
    )
