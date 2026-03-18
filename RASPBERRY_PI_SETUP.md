# Raspberry Pi Setup Guide

## Clone Repository on Raspberry Pi

```bash
# SSH into your Raspberry Pi
ssh pi@raspberrypi.local
# or
ssh pi@192.168.x.x  # Use your Pi's IP address

# Go to your project directory
cd ~
mkdir -p projects
cd projects

# Clone the repository
git clone https://github.com/MacClaren15/cctv-system.git
cd cctv-system
```

## Install System Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and build tools
sudo apt install -y python3 python3-pip python3-venv git

# Install OpenCV dependencies
sudo apt install -y libatlas-base-dev libjasper-dev libharfbuzz0b libwebp6 \
  libtiff5 libharfbuzz-icu0 libopenjp2-7 libjasper1 libhdf5-dev libharfbuzz0b

# Install FFmpeg (for video processing)
sudo apt install -y ffmpeg

# (Optional) Install camera module support
sudo apt install -y python3-picamera2
```

## Create Virtual Environment

```bash
cd ~/projects/cctv-system/cctv_system

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

## Install Python Dependencies

```bash
# Install core packages (without torch/ultralytics to save space)
pip install -r requirements-updated.txt

# Or minimal install:
pip install opencv-python numpy scipy Flask Flask-CORS \
  Flask-RESTful Flask-SQLAlchemy SQLAlchemy python-dotenv \
  Pillow requests pyyaml pytest pytest-cov
```

## Test the System

```bash
# Run tests
python test_system.py

# Expected output: 5/6 tests pass (camera test may skip if no USB camera)
```

## Start the CCTV System

```bash
# Make sure venv is activated
source venv/bin/activate

# Start the system
python main.py
```

The web dashboard will be available at:
```
http://raspberrypi.local:5000
# or
http://192.168.x.x:5000  # Your Pi's IP
```

## Auto-start on Boot (Optional)

### Option 1: Using systemd Service

```bash
# Copy the service file
sudo cp cctv-system.service /etc/systemd/system/

# Edit the service file
sudo nano /etc/systemd/system/cctv-system.service
```

Update these lines in the service file:
```ini
User=pi
WorkingDirectory=/home/pi/projects/cctv-system/cctv_system
ExecStart=/home/pi/projects/cctv-system/cctv_system/venv/bin/python main.py
```

Then:
```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable cctv-system
sudo systemctl start cctv-system

# Check status
sudo systemctl status cctv-system

# View logs
sudo journalctl -u cctv-system -f
```

### Option 2: Crontab Auto-start

```bash
crontab -e

# Add this line at the end:
@reboot cd /home/pi/projects/cctv-system/cctv_system && source venv/bin/activate && python main.py >> logs/startup.log 2>&1 &
```

## Connect Camera to Raspberry Pi

### USB Webcam
```bash
# Simply plug in USB camera
# System will auto-detect at index 0
lsusb  # Verify camera is detected
```

### Pi Camera Module v2/HQ

```bash
# Install libcamera support
sudo apt install -y python3-libcamera

# Enable camera in raspi-config
sudo raspi-config
# Navigate to: 3 Interface Options → I1 Camera → Enable

# Test camera
libcamera-hello -t 5

# Update config.yaml to use camera:
# CAMERAS:
#   - id: 0
#     name: pi_camera
#     source: "libcamera"  # or camera index
```

## Configuration on Pi

Edit `config.yaml`:

```bash
nano config.yaml
```

Key settings for Pi:
```yaml
CAMERAS:
  - id: 0
    name: pi_camera
    source: 0  # 0 for USB, "libcamera" for Pi Camera

MOTION_DETECTION:
  enabled: true
  method: background_subtraction  # MOG2 is fastest
  sensitivity: 0.3

OBJECT_DETECTION:
  enabled: false  # Disable on Pi (needs torch/ultralytics)

WEB:
  host: 0.0.0.0  # Accessible from all IPs
  port: 5000
  debug: false    # Production mode
```

## Performance Tips for Pi

```python
# In config.py, reduce frame resolution for better performance:
CAMERAS = [
    {
        'id': 0,
        'name': 'pi_camera',
        'source': 0,
        'resolution': (640, 480),   # Lower resolution = better FPS
        'fps': 15,                   # Reduce frame rate
        'buffer_size': 1
    }
]

# Motion detection settings
MOTION_DETECTION = {
    'enabled': True,
    'method': 'background_subtraction',  # Fastest algorithm
    'sensitivity': 0.3,
    'threshold': 1000                    # Adjust if needed
}
```

## Troubleshooting on Pi

### Low FPS / Slow Performance
```bash
# Check CPU temperature
vcgencmd measure_temp

# Reduce resolution in config
# Method: background_subtraction is fastest

# Disable object detection (requires torch)
```

### Camera Not Detected
```bash
# Check for USB camera
lsusb

# Check for Pi Camera
vcgencmd get_camera

# Test camera
raspistill -o test.jpg
# or
libcamera-hello -t 3
```

### Out of Memory
```bash
# Monitor memory usage
free -h

# Limit Flask workers
# Edit main.py to use single worker:
# app.run(host='0.0.0.0', port=5000, threaded=True)
```

### Port Already in Use
```bash
# Check what's using port 5000
sudo lsof -i :5000

# Kill process if needed
sudo kill -9 <PID>

# Or use different port in config.yaml
```

## Access from Remote

### Local Network
```
http://raspberrypi.local:5000
# or
http://192.168.x.x:5000  # Your Pi's IP
```

### Find Your Pi's IP
```bash
hostname -I
# or on your main computer:
ping raspberrypi.local
```

### Port Forwarding (Advanced)
For access outside your network:
```bash
# Use ngrok for free tunneling
pip install pyngrok
# Then in your app, use ngrok.connect(5000)
```

## Monitor System

### Check if running
```bash
ps aux | grep python
curl http://localhost:5000/api/v1/health
```

### View logs
```bash
tail -f data/logs/cctv_system.log
```

### Stop the system
```bash
# If running in foreground
Ctrl+C

# If running as service
sudo systemctl stop cctv-system
```

## Storage Considerations

Recordings take space. Monitor:
```bash
# Check disk space
df -h

# Check data folder size
du -sh ~/projects/cctv-system/cctv_system/data/

# Clean old recordings
find ./data/recordings -mtime +7 -delete  # Delete 7+ days old
```

## Next Steps

1. **Clone and setup**: See commands above
2. **Connect camera**: USB or Pi Camera Module
3. **Run tests**: `python test_system.py`
4. **Start system**: `python main.py`
5. **Access dashboard**: `http://raspberrypi.local:5000`
6. **Enable auto-start**: Use systemd service
7. **Monitor logs**: Check `data/logs/`

Your Raspberry Pi is ready to be a dedicated CCTV motion detection system! 🎉

---

## Quick Commands Summary

```bash
# Clone
git clone https://github.com/MacClaren15/cctv-system.git
cd cctv-system/cctv_system

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-updated.txt

# Test
python test_system.py

# Run
python main.py

# Access
http://raspberrypi.local:5000
```
