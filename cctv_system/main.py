"""
CCTV Motion Detection System - Main Entry Point
"""
import logging
import logging.handlers
import os
from pathlib import Path

from config import config
from core.processor import initialize_processor
from api.app import create_app


def setup_logging():
    """Configure logging"""
    log_dir = Path(config.LOGGING.get("file", "./data/logs")).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOGGING.get("level", "INFO")))
    
    # File handler with rotation
    log_file = config.LOGGING.get("file", "./data/logs/cctv_system.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=config.LOGGING.get("max_bytes", 10485760),
        backupCount=config.LOGGING.get("backup_count", 10)
    )
    file_handler.setLevel(getattr(logging, config.LOGGING.get("level", "INFO")))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.LOGGING.get("level", "INFO")))
    
    # Formatter
    formatter = logging.Formatter(config.LOGGING.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def setup_directories():
    """Create necessary directories"""
    directories = [
        "./data",
        "./data/logs",
        "./data/recordings",
        "./data/events"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def main():
    """Main entry point"""
    # Setup
    setup_directories()
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info(f"Starting {config.APP_NAME} v{config.VERSION}")
    logger.info("=" * 60)
    
    try:
        # Initialize CCTV processor
        logger.info("Initializing CCTV processor...")
        processor = initialize_processor()
        
        # Start CCTV system
        logger.info("Starting CCTV system...")
        processor.start()
        
        # Create and run Flask app
        logger.info("Creating Flask application...")
        app = create_app()
        
        logger.info(f"Starting web server on {config.WEB.get('host')}:{config.WEB.get('port')}")
        logger.info("=" * 60)
        logger.info("CCTV System is running!")
        logger.info("Access dashboard at: http://localhost:5000")
        logger.info("=" * 60)
        
        # Run Flask app
        app.run(
            host=config.WEB.get('host', '0.0.0.0'),
            port=config.WEB.get('port', 5000),
            debug=config.WEB.get('debug', False),
            use_reloader=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        if 'processor' in locals():
            processor.stop()
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        if 'processor' in locals():
            processor.stop()
        raise
    finally:
        logger.info("CCTV system stopped")


if __name__ == '__main__':
    main()
