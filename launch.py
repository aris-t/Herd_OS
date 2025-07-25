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
logger = setup_logger("Main")
devices = []

def signal_handler(sig, frame):
    logger.info("Ctrl+C detected. Ending all processes...")
    for device in devices:
        device.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ----------------------------------------
# Launch
# ----------------------------------------
if __name__ == "__main__":
    camera = Camera(logger=logger)
    devices = [
        camera
    ]
    for device in devices:
        device.start()

    time.sleep(10)  # Allow some time for devices to initialize
    camera.put_command("start_recorder", None)
    time.sleep(10)  # Allow some time for the recorder to start
    camera.put_command("stop_recorder", None)
    time.sleep(5)  # Allow some time for the recorder to stop

    # time.sleep(5)
    # camera.start_recorder()
    # time.sleep(20)
    # camera.stop_recorder()
    # time.sleep(5)
    # camera.start_recorder()
    # time.sleep(20)
    # camera.stop_recorder()
