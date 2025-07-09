import os
from datetime import datetime

from .device import Device
from .workers import Camera_Controller
from utils.setup_logger import setup_logger

# # ----------------------------------------
# # Device
# # ----------------------------------------

class Camera(Device):
    def __init__(self):
        super().__init__()

        self.multicast_ip = "239.255.12.42"
        self.port = 5555
        self.camera_endpoint = f"udp://{self.multicast_ip}:{self.port}"
        self.target_framerate = 30
        self.target_resolution = "640x480"
        self.target_bitrate = 4000

        self.processes = [
            Camera_Controller(self, "Camera_Controller", DEBUG=True)
        ]

    def __setup__(self):
        self.logger.info("Setting up device...")

    # Device Specific Methods
    def start_trial(self, config=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trial_dir = os.path.join("trials", f"trial_{timestamp}")
        os.makedirs(trial_dir, exist_ok=True)

        if config:
            with open(os.path.join(trial_dir, "config.txt"), "w") as f:
                f.write(str(config))
        with open(os.path.join(trial_dir, "started.txt"), "w") as f:
            f.write(f"Trial started at {timestamp}\n")
        self.logger.info(f"Trial started at {trial_dir}")

    def stop_trial(self):
        self.logger.info("Trial stopped.")
