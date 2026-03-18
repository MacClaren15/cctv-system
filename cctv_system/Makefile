# CCTV System Makefile

.PHONY: help install test run dev clean docker-build docker-run

help:
	@echo "CCTV Motion Detection System"
	@echo ""
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run system tests"
	@echo "  make test-motion   - Test motion detection"
	@echo "  make test-object   - Test object detection"
	@echo "  make run           - Run the system"
	@echo "  make dev           - Run in development mode"
	@echo "  make logs          - Tail the log file"
	@echo "  make clean         - Clean up data files"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container"
	@echo "  make venv          - Create Python virtual environment"

venv:
	python -m venv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  Windows: venv\Scripts\activate"
	@echo "  Linux/Mac: source venv/bin/activate"

install: venv
	pip install -r requirements.txt
	@echo "Dependencies installed successfully"

test:
	python test_system.py

test-motion:
	python -c "from core.motion_detector import MotionDetector; print('✓ Motion Detector OK')"

test-object:
	python -c "from core.object_detector import ObjectDetector; print('✓ Object Detector OK')"

run:
	python main.py

dev:
	python main.py --debug

logs:
	tail -f ./data/logs/cctv_system.log

clean:
	rm -rf ./data/logs/*
	rm -rf ./data/recordings/*
	rm -rf ./data/events/*
	rm -rf ./data/*.db
	@echo "Data files cleaned"

docker-build:
	docker build -t cctv-system:latest .

docker-run:
	docker run -p 5000:5000 --device /dev/video0:/dev/video0 cctv-system:latest

# Development utilities
lint:
	python -m pylint cctv_system/

format:
	python -m black cctv_system/

freeze-requirements:
	pip freeze > requirements.txt

# Raspberry Pi specific
rpi-install:
	sudo apt-get install python3-opencv python3-flask
	make install

rpi-run:
	python main.py

rpi-service:
	@echo "Creating systemd service for CCTV..."
	sudo cp cctv-system.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable cctv-system
	sudo systemctl start cctv-system
	sudo systemctl status cctv-system
