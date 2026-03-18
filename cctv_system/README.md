# Computer Vision CCTV Motion Detection System

A robust, real-time video surveillance system for detecting human and object movement with advanced computer vision capabilities.

## Features

✨ **Core Capabilities**

- **Real-time Motion Detection** - Multiple detection algorithms (background subtraction, frame difference, optical flow)
- **Object Detection & Classification** - YOLOv8-based detection for persons, vehicles, and more
- **Multi-Camera Support** - Handle multiple camera streams simultaneously
- **Object Tracking** - Track detected objects across frames
- **Event Logging** - Comprehensive event database with timestamps and details
- **Alert System** - Configurable alerts with cooldown periods

🎯 **Web Dashboard**

- Live multi-camera streaming with annotations
- Real-time event monitoring
- Statistical analysis and trends
- System control panel
- Alert management

🔧 **API Features**

- RESTful API for integration
- Video streaming endpoints
- Event filtering and retrieval
- System statistics and analytics
- Camera control via API

📊 **Performance & Reliability**

- Multi-threaded frame capture
- Configurable frame skipping for optimization
- Automatic logging with file rotation
- Database persistence for events and detections

## System Architecture

```
cctv_system/
├── config.py                 # Configuration management
├── main.py                   # Entry point
├── core/
│   ├── camera.py            # Camera stream management
│   ├── motion_detector.py   # Motion detection algorithms
│   ├── object_detector.py   # Object detection & tracking
│   └── processor.py         # Main orchestration
├── models/
│   └── data_models.py       # Data structures
├── api/
│   └── app.py               # Flask REST API
├── web/
│   ├── templates/           # HTML templates
│   │   └── dashboard.html
│   └── static/              # CSS and JavaScript
│       ├── styles.css
│       └── script.js
└── data/                    # Runtime data storage
    ├── logs/
    ├── recordings/
    └── cctv_system.db
```

## Installation

### Prerequisites

- Python 3.8+
- OpenCV 4.8+
- PyTorch 2.0+
- CUDA (optional, for GPU acceleration)

### Setup Environment

1. **Clone/Navigate to Project**

```bash
cd cctv_system
```

2. **Create Virtual Environment**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Create Data Directories**

```bash
python -c "from pathlib import Path; Path('./data').mkdir(exist_ok=True); Path('./data/logs').mkdir(exist_ok=True); Path('./data/recordings').mkdir(exist_ok=True)"
```

## Quick Start

### Basic Usage

```bash
python main.py
```

This will:

- Initialize CCTV processor
- Start camera streams
- Launch web dashboard on `http://localhost:5000`

### Configuration

Edit `config.py` to customize:

```python
# Camera settings
CAMERAS = {
    "camera_1": {
        "enabled": True,
        "camera_index": 0,
        "resolution": [1280, 720],
        "fps": 30
    }
}

# Motion detection sensitivity
MOTION_DETECTION = {
    "sensitivity": 0.3,  # 0.1 (very sensitive) to 1.0 (not sensitive)
    "min_area": 500      # Minimum pixels to detect motion
}

# Object detection
OBJECT_DETECTION = {
    "model": "yolov8m",
    "classes": ["person", "car", "truck"]
}
```

## API Endpoints

### System Control

- `GET /api/v1/status` - System status
- `POST /api/v1/control/start` - Start system
- `POST /api/v1/control/stop` - Stop system
- `POST /api/v1/control/restart` - Restart system

### Camera Management

- `GET /api/v1/cameras` - List all cameras
- `GET /api/v1/cameras/<name>` - Camera info
- `GET /api/v1/cameras/<name>/stream` - Live video stream

### Event & Detection APIs

- `GET /api/v1/events` - Recent events
- `POST /api/v1/events/filter` - Filter events
- `GET /api/v1/detections` - Recent detections
- `GET /api/v1/detections/by-class` - Detections by class

### Statistics

- `GET /api/v1/stats/cameras` - Camera statistics
- `GET /api/v1/stats/summary` - System summary

## Motion Detection Algorithms

### 1. Background Subtraction (MOG2)

- Default method for static cameras
- Adapts to lighting changes
- Best for most scenarios

### 2. Frame Difference

- Fast optical flow alternative
- Good for detecting rapid movement
- Lower computational cost

### 3. Optical Flow

- Detects motion direction and magnitude
- Best for complex motion patterns
- Higher computational cost

## Object Detection

Uses **YOLOv8** for real-time object detection:

- **yolov8n** - Nano (fastest, least accurate)
- **yolov8s** - Small
- **yolov8m** - Medium (default, balanced)
- **yolov8l** - Large
- **yolov8x** - X-Large (slowest, most accurate)

Detectable classes: person, car, truck, bus, bicycle, motorcycle, etc.

## Performance Optimization

### For Raspberry Pi 5

```python
MOTION_DETECTION = {"sensitivity": 0.5}
OBJECT_DETECTION = {"model": "yolov8n", "device": "cpu"}
PERFORMANCE = {"frame_skip": 3, "max_threads": 2}
```

### For High-Performance Systems

```python
OBJECT_DETECTION = {"model": "yolov8x", "device": "cuda"}
PERFORMANCE = {"frame_skip": 1, "max_threads": 8}
```

## Logging

Logs are saved to `./data/logs/cctv_system.log` with:

- Automatic file rotation (10MB max)
- 10 backup files retained
- Configurable log levels

## Database

SQLite database stores:

- Events (motion and detection)
- Detections with bounding boxes
- Alerts and notifications
- System logs
- Camera statistics

Auto-retention: Events older than 30 days are archived.

## Docker Deployment

Build Docker image:

```bash
docker build -t cctv-system .
```

Run container:

```bash
docker run -p 5000:5000 --device /dev/video0 cctv-system
```

## Troubleshooting

### Camera Not Opening

- Check camera is connected and not in use
- Verify camera index in config (0 = default webcam)
- Try: `ls /dev/video*` (Linux) or Device Manager (Windows)

### Low FPS

- Reduce resolution or frame rate
- Enable frame skipping: `frame_skip: 2-3`
- Use `yolov8n` model for object detection
- Disable object detection if not needed

### High CPU Usage

- Reduce detection frequency
- Use faster model (yolov8n)
- Increase frame skip
- Reduce resolution

### Memory Leaks

- Check event buffer isn't growing indefinitely
- Verify database cleanup is running
- Monitor with: `python -m memory_profiler main.py`

## Advanced Features

### Custom Motion Detection

Implement your own detector:

```python
from core.motion_detector import MotionDetector

class CustomDetector(MotionDetector):
    def detect(self, frame):
        # Your custom detection logic
        return motion_detected, contours, ratio
```

### Email Alerts

Configure in `config.py`:

```python
ALERTS = {
    "email_enabled": True,
    "email_recipients": ["admin@example.com"],
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587
}
```

### Slack Integration

```python
ALERTS = {
    "slack_enabled": True,
    "slack_webhook": "https://hooks.slack.com/..."
}
```

## Performance Metrics

Typical performance on Raspberry Pi 5:

- **Resolution**: 1280x720 @ 15 FPS
- **Latency**: 100-200ms
- **CPU Usage**: 60-80%
- **Memory**: 300MB

On modern desktop (GPU):

- **Resolution**: 1920x1080 @ 30 FPS
- **Latency**: 20-50ms
- **GPU Usage**: 40-60%
- **Memory**: 2-3GB

## Contributing

Contributions welcome! Areas for improvement:

- Additional detection algorithms
- Database optimization
- Web UI enhancements
- Mobile app
- Cloud integration

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review logs in `./data/logs/`
3. Open an issue on GitHub
4. Check documentation at `/docs`

## Roadmap

- [ ] Multi-scene activity detection
- [ ] Anomaly detection
- [ ] Person identification/faces
- [ ] Heat mapping
- [ ] Mobile app
- [ ] Cloud backup
- [ ] Advanced analytics dashboard
- [ ] ML model training tools

---

**Version**: 1.0.0  
**Last Updated**: 2025  
**Maintainer**: CCTV Team
