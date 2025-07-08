import signal
import sys
import time

from devices.device_camera import Camera
from utils.setup_logger import setup_logger

#TODO
# Add rich logging for better log formatting and colorization

# ----------------------------------------
# Signal Handling
# ----------------------------------------
devices = []

def signal_handler(sig, frame):
    logger = setup_logger("Main")
    logger.info("Ctrl+C detected. Ending all processes...")
    for device in devices:
        device.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ----------------------------------------
# Launch
# ----------------------------------------
if __name__ == "__main__":
    devices = [
        Camera()
        ]
    for device in devices:
        device.start()
