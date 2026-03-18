# CCTV System - Implementation Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Dashboard (Browser)                 │
│              (Live Streams, Events, Alerts, Stats)          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Flask REST API (Port 5000)                     │
│        (API Gateway, Endpoints, Authentication)            │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│          CCTV Processor (Main Orchestration)                │
│  (Threading, Event Management, Alert Generation)           │
└────────┬──────────────┬──────────────┬─────────────────────┘
         │              │              │
    ┌────▼──┐      ┌────▼──┐      ┌────▼──┐
    │        │      │        │      │        │
    │ Camera │      │ Motion │      │Object  │
    │Manager │      │Detector│      │Detector│
    │ (Multi)│      │        │      │(YOLOv8)│
    │        │      │        │      │        │
    └────┬───┘      └────┬───┘      └───┬────┘
         │               │              │
    ┌────▼────────────────▼──────────────▼────┐
    │         SQLite Database                  │
    │  Events | Detections | Alerts | Stats   │
    └─────────────────────────────────────────┘
```

## Core Components

### 1. Camera Manager (`core/camera.py`)

**Purpose**: Manages camera streams with multi-threading

**Key Features**:

- Non-blocking frame capture using queues
- Thread-safe frame buffering
- FPS calculation and monitoring
- Support for frame rotation (for vertical cameras)
- Per-camera frame counting

**Design Decision**:

- Used background threads for capture to prevent blocking
- Queue-based buffering (maxsize=2) prevents memory buildup
- Each camera runs independently

```python
# Flow
CameraStream.start() → _capture_thread() → queue → get_frame()
```

### 2. Motion Detector (`core/motion_detector.py`)

**Purpose**: Detects movement in video frames

**Three Algorithms Implemented**:

1. **Background Subtraction (MOG2)** - Default
   - Adapts to light changes over time
   - Separates foreground/background
   - Best for static cameras

2. **Frame Difference**
   - Simple pixel-by-pixel comparison
   - Fast and lightweight
   - Good for high-speed detection

3. **Optical Flow**
   - Calculates motion direction/magnitude
   - Complex motion patterns
   - Higher CPU cost

**Design Decision**:

- Morphological operations (erode/dilate) reduce noise
- Contour filtering by area prevents false positives
- History tracking monitors motion trends

```python
# Flow
detect(frame) → preprocess → detect_motion → filter_contours → analyze_trend
```

### 3. Object Detector (`core/object_detector.py`)

**Purpose**: Detects and tracks objects using YOLOv8

**Components**:

- **ObjectDetector**: Single-frame detection
- **TrackedObject**: Tracks individual objects
- **MultiObjectTracker**: Associates detections across frames

**YOLOv8 Models**:

- `yolov8n` - Nano (fastest)
- `yolov8m` - Medium (default, balanced)
- `yolov8x` - X-Large (slowest, most accurate)

**Tracking Algorithm**:

- Centroid distance matching
- Frame age tracking to prevent ghost boxes
- Automatic track cleanup

**Design Decision**:

- Separate tracking from detection for extensibility
- Confidence threshold filtering reduces false positives
- Distance-based association simple but effective

```python
# Flow
detect(frame) → YOLOv8 → filter_by_confidence → match_to_tracks → update_tracks
```

### 4. Processor (`core/processor.py`)

**Purpose**: Main orchestration and event management

**Key Responsibilities**:

- Initializes all detectors
- Runs main processing loop in background thread
- Generates events and alerts
- Maintains system statistics
- Coordinates multi-camera processing

**Processing Pipeline**:

```
Get Frame → Motion Detection → Object Detection → Track Objects
    ↓              ↓                   ↓
Create Event    Generate Alert    Record Event
    ↓              ↓                   ↓
Update Stats    Notification      Database
```

**Design Decision**:

- Separate processing thread prevents UI blocking
- Event history stored in memory for recent access
- Statistics tracked per-camera
- Alert cooldown prevents spam

### 5. Flask API (`api/app.py`)

**Purpose**: RESTful API and web interface

**Endpoints Organized by Function**:

| Endpoint             | Purpose           |
| -------------------- | ----------------- |
| `/api/v1/status`     | System health     |
| `/api/v1/cameras/*`  | Camera management |
| `/api/v1/events`     | Event retrieval   |
| `/api/v1/detections` | Detection data    |
| `/api/v1/alerts`     | Alert management  |
| `/api/v1/stats/*`    | Statistics        |
| `/api/v1/control/*`  | System control    |
| `/api/v1/*/stream`   | Video streaming   |

**Authentication**:

- Optional API key authentication (configurable)
- CORS enabled for web access

**Design Decision**:

- RESTful design for simplicity
- MJPEG streaming for video (widely compatible)
- Decorator-based auth for flexibility

### 6. Web Dashboard (`web/`)

**Features**:

- Real-time camera feeds
- Live event table with filtering
- Alert notifications with severity
- System statistics
- Control buttons (Start/Stop/Restart)

**Technology Stack**:

- HTML5 (semantic markup)
- CSS3 (responsive design)
- Vanilla JavaScript (no dependencies)

**Auto-Refresh**: 5-second polling cycle

## Data Models (`models/data_models.py`)

**Core Classes**:

```python
Event          # Motion or detection event
Detection      # Individual object detection with bbox
Alert          # Notification (email/Slack/webhook)
Recording      # Video file metadata
CameraStats    # Per-camera statistics
```

**Design Decision**:

- Simple dataclasses for clarity
- `to_dict()` methods for JSON serialization
- Statistics tracked incrementally

## Configuration System

**Three Levels**:

1. **code defaults** (`config.py`) - Safe defaults
2. **YAML file** (`config.yaml`) - Deployment overrides
3. **Environment** (`.env`) - Secrets and API keys

**Load Order**:

```python
Config (defaults) → load_from_file() → environment variables
```

**Design Decision**:

- Centralized config for easy management
- YAML human-readable for configuration
- Environment variables for secrets

## Processing Pipeline Details

### Motion Detection Flow

```
Input Frame
    ↓
Preprocess (blur, morphology)
    ↓
Apply Detection Algorithm
    ↓
Filter by Min Area
    ↓
Calculate Motion Ratio
    ↓
Update History (for trend)
    ↓
Return: (detected, contours, ratio)
```

### Object Detection Flow

```
Input Frame
    ↓
YOLOv8 Inference
    ↓
Process Results (extract boxes)
    ↓
Filter by Confidence
    ↓
Filter by Target Classes
    ↓
Calculate Additional Properties (center, area, etc.)
    ↓
Match to Previous Tracks
    ↓
Return: Detection List
```

### Event Generation Flow

```
Motion/Detection Detected
    ↓
Create Event Object
    ↓
Update Camera Statistics
    ↓
Check Alert Enabled & Cooldown
    ↓
Create Alert Object
    ↓
Send Notification (async)
    ↓
Store in Database
```

## Performance Optimizations

### Frame Skipping

- Skip N frames between processing
- Reduces CPU load, slight latency increase
- Configurable: `PERFORMANCE.frame_skip`

### Multi-Threading

- Camera capture on dedicated threads (non-blocking)
- Detection on main thread (frame order preserved)
- Processing loop in background thread

### Memory Management

- Queue-based frame buffering (fixed size)
- Event history kept in memory (recent access)
- Older events stored in database
- Automatic cleanup on configurable interval

### Detection Optimization

- Confidence filtering reduces bad detections
- Area filtering removes noise in motion detection
- Optical flow only computed when needed
- GPU acceleration available for object detection

## Extension Points

### Custom Motion Detector

```python
class MyDetector(MotionDetector):
    def _detect_custom(self, frame):
        # Your algorithm
        return detected, contours, ratio
```

### Custom Object Detector

```python
class MyObjectDetector(ObjectDetector):
    def _process_results(self, results, frame):
        # Custom processing
        return detections
```

### Custom Alert Handler

```python
def send_email_alert(alert):
    # SMTP configuration and sending
    pass
```

## Testing Strategy

**Component Tests**:

- `test_system.py` - Integration tests
- Individual detector tests
- Camera availability tests
- API endpoint tests

**Manual Testing**:

- Open issue/alert triggers
- Monitor logs for errors
- Check statistics accuracy
- Verify frame rates

## Deployment Considerations

### Development Environment

```bash
python main.py
# Local access only, debug enabled
```

### Production (Desktop/Server)

```bash
# Change config.py:
DEBUG = False
WEB.ssl_enabled = True
DATABASE.type = "postgresql"

python main.py
```

### Raspberry Pi

```bash
# Use systemd service
make rpi-service

# Or run in screen session
screen -S cctv python main.py
```

### Docker

```bash
docker build -t cctv:latest .
docker run -d -p 5000:5000 --device /dev/video0 cctv:latest
```

## Monitoring & Maintenance

**Log Analysis**:

- Check for repeated errors
- Monitor detection performance
- Track FPS trends
- Analyze alert frequency

**Database Maintenance**:

- Auto-cleanup runs every hour
- Export old events before deletion
- Backup before major changes

**Performance Tuning**:

- Monitor CPU/memory with: `top`, `nvidia-smi`
- Adjust `frame_skip` if lagging
- Reduce resolution if network bandwidth limited

## Future Improvements

1. **Analytics**
   - Heat mapping (movement patterns)
   - Anomaly detection
   - Trend analysis

2. **Recognition**
   - Face recognition
   - Vehicle license plates
   - Custom object classes

3. **Integration**
   - MQTT for IoT integration
   - Cloud backup
   - Mobile app

4. **Performance**
   - Edge computing support
   - Distributed processing
   - Custom compiled models

---

**Document Version**: 1.0  
**Last Updated**: 2025  
**Status**: Complete & Production Ready
