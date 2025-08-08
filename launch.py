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
_shutdown_triggered = False  # Global guard

def signal_handler(sig, frame):
    global _shutdown_triggered

    if _shutdown_triggered:
        logger.warning("Shutdown already in progress... ignoring signal.")
        return
    _shutdown_triggered = True

    logger.info("Ctrl+C detected. Ending all processes...")

    for device in devices:
        try:
            device.stop()
        except Exception as e:
            logger.warning(f"Error during shutdown: {e}")

    # Optional: give time for logs to flush
    time.sleep(2)

    # DO NOT raise the signal again — just exit cleanly
    sys.exit(0)

# Register signal only once
signal.signal(signal.SIGINT, signal_handler)

# ----------------------------------------
# Launch
# ----------------------------------------
if __name__ == "__main__":
    camera = Camera(logger=logger, cameras=[0, 1], DEBUG=2)
    devices = [
        camera
    ]
    for device in devices:
        device.start()

    time.sleep(10)  # Allow some time for devices to initialize
    # camera.put_command("start_recorder", None)
    # time.sleep(5)  # Allow some time for the recorder to start
    camera.get_health_values()
    # time.sleep(5)  # Allow some time for the recorder to start
    # camera.put_command("stop_recorder", None)
    # time.sleep(5)  # Allow some time for the recorder to stop

    # time.sleep(5)
    # camera.start_recorder()
    # time.sleep(20)
    # camera.stop_recorder()
    # time.sleep(5)
    # camera.start_recorder()
    # time.sleep(20)
    # camera.stop_recorder()
