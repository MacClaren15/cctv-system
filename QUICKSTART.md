# CCTV System - Quick Start Guide

## 🎯 Project Overview

Your Computer Vision CCTV Motion Detection System is now ready! This is a production-grade surveillance system with real-time motion and object detection using YOLOv8.

## 📁 Project Structure

```
cctv_system/
├── config.py                 # ⚙️ Configuration settings
├── main.py                   # 🚀 Entry point
├── requirements.txt          # 📦 Dependencies
├── test_system.py           # 🧪 System tests
│
├── core/                     # 🎬 Core modules
│   ├── camera.py           # Camera stream management
│   ├── motion_detector.py   # Motion detection algorithms
│   ├── object_detector.py   # YOLOv8 object detection
│   └── processor.py         # Main orchestration
│
├── models/                   # 📊 Data structures
│   └── data_models.py       # Events, Detections, Alerts
│
├── api/                      # 🔌 REST API
│   └── app.py               # Flask application
│
├── web/                      # 🌐 Web Interface
│   ├── templates/           # HTML templates
│   │   └── dashboard.html
│   └── static/              # CSS & JavaScript
│       ├── styles.css
│       └── script.js
│
├── data/                     # 💾 Runtime data
│   ├── logs/               # System logs
│   ├── recordings/         # Video recordings
│   └── events/             # Event data
│
├── Dockerfile               # 🐳 Docker configuration
├── Makefile                 # ⚡ Build commands
└── README.md               # 📚 Full documentation
```

## ⚡ Quick Start (5 minutes)

### 1️⃣ Install Dependencies

```bash
cd cctv_system

# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# macOS/Linux
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Verify Installation

```bash
python test_system.py
```

You should see:

```
✓ OpenCV 4.8.1.78
✓ NumPy 1.24.3
✓ PyTorch 2.1.0
✓ YOLOv8 (ultralytics)
✓ Flask
... (more checks)
```

### 3️⃣ Run the System

```bash
python main.py
```

Output:

```
Starting CCTV Motion Detection System v1.0.0
Initializing CCTV processor...
Starting CCTV system...
Creating Flask application...
Starting web server on 0.0.0.0:5000
CCTV System is running!
Access dashboard at: http://localhost:5000
```

### 4️⃣ Access the Dashboard

Open your browser: **http://localhost:5000**

## 🎮 Key Features Ready to Use

### Motion Detection

- ✅ Background subtraction (default)
- ✅ Frame difference detection
- ✅ Optical flow detection
- ✅ Sensitivity adjustment (0.1-1.0)
- ✅ Customizable minimum area threshold

### Object Detection

- ✅ YOLOv8 detection (persons, cars, trucks, etc.)
- ✅ Confidence scoring
- ✅ Object tracking across frames
- ✅ Multiple class support
- ✅ GPU acceleration ready

### Multi-Camera Support

- ✅ Handle multiple cameras simultaneously
- ✅ Per-camera configuration
- ✅ Individual stream control
- ✅ Per-camera statistics

### Web Dashboard

- ✅ Live multi-camera view
- ✅ Real-time event monitoring
- ✅ Alert management
- ✅ System control panel
- ✅ Statistics and trends

### REST API

- ✅ Complete API documentation in code
- ✅ Video streaming endpoints
- ✅ Event filtering and search
- ✅ System statistics
- ✅ Control endpoints

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Add second camera
CAMERAS = {
    "camera_1": {"enabled": True, "camera_index": 0, ...},
    "camera_2": {"enabled": True, "camera_index": 1, ...}
}

# Adjust motion sensitivity
MOTION_DETECTION = {
    "sensitivity": 0.2,  # Lower = more sensitive
    "min_area": 300
}

# Change object detection model
OBJECT_DETECTION = {
    "model": "yolov8x",  # Slower but more accurate
    "device": "cuda"     # Use GPU if available
}
```

## 📊 API Endpoints

All endpoints support JSON responses:

```bash
# Get system status
curl http://localhost:5000/api/v1/status

# Get cameras info
curl http://localhost:5000/api/v1/cameras

# Stream from camera
curl http://localhost:5000/api/v1/cameras/camera_1/stream

# Get recent events
curl http://localhost:5000/api/v1/events

# Get detections
curl http://localhost:5000/api/v1/detections

# Get alerts
curl http://localhost:5000/api/v1/alerts

# Get statistics
curl http://localhost:5000/api/v1/stats/summary
```

## 🚀 Advanced Usage

### Enable GPU Acceleration

```python
# In config.py
OBJECT_DETECTION = {
    "device": "cuda",  # NVIDIA GPU
    "model": "yolov8l" # Larger model for GPU
}
```

### Configure Email Alerts

```python
ALERTS = {
    "email_enabled": True,
    "email_recipients": ["admin@example.com"],
    "smtp_server": "smtp.gmail.com"
}
```

### Optimize for Raspberry Pi

```python
# In config.py
MOTION_DETECTION = {"sensitivity": 0.5}
OBJECT_DETECTION = {"model": "yolov8n"}
PERFORMANCE = {"frame_skip": 3}
```

### Use Docker

```bash
docker build -t cctv-system .
docker run -p 5000:5000 --device /dev/video0 cctv-system
```

### Install as Systemd Service (Raspberry Pi)

```bash
make rpi-service
# System will start automatically on boot
```

## 🧪 Testing

Run test suite:

```bash
python test_system.py
```

Test individual components:

```python
python -c "from core.motion_detector import MotionDetector; print('✓ OK')"
python -c "from core.object_detector import ObjectDetector; print('✓ OK')"
```

## 📝 Logging

Logs are automatically saved to:

- `./data/logs/cctv_system.log` - Main system log
- File rotation every 10MB (10 backups kept)
- Configurable log level in `config.py`

View logs:

```bash
make logs
# or
tail -f ./data/logs/cctv_system.log
```

## 🔍 Database

SQLite database at `./data/cctv_system.db` stores:

- Events (motion + detection)
- Object detections with attributes
- Alerts and notifications
- Camera statistics
- System logs

Auto-cleanup: Events older than 30 days removed

## 🐛 Troubleshooting

### Camera Not Opening

```bash
# Linux - check available cameras
ls /dev/video*

# Check camera index in config.py
# Default is 0 (first camera)
```

### No Motion Detected

- Lower `sensitivity` (default 0.3)
- Lower `min_area` (default 500)
- Change method to `frame_diff` for faster detection

### High CPU Usage

- Increase `frame_skip` (process every Nth frame)
- Use smaller model: `yolov8n` instead of `yolov8m`
- Reduce resolution in camera config
- Disable object detection if not needed

### Can't Access Dashboard

- Check port 5000 is available
- Try: http://127.0.0.1:5000
- Check firewall settings

## 📚 Full Documentation

See [README.md](README.md) for:

- Detailed feature documentation
- Performance benchmarks
- Architecture overview
- Advanced configuration
- Integration examples
- Contributing guidelines

## 💡 Next Steps

1. **Test with your camera** - Adjust sensitivity settings
2. **Configure alerts** - Set up email/Slack notifications
3. **Monitor statistics** - Track detection trends
4. **Optimize performance** - Tune for your hardware
5. **Deploy** - Run as service on Raspberry Pi

## 🤝 Need Help?

- Check logs: `tail -f ./data/logs/cctv_system.log`
- Run diagnostics: `python test_system.py`
- Review code comments for detailed explanations
- Check API endpoints documentation in `api/app.py`

## 🎉 You're All Set!

Your CCTV System is ready for deployment. Start detecting motion and objects with AI!

```bash
python main.py
```

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Created**: 2025
