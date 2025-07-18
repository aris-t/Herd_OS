from .worker import Worker
import zenoh
import time

# ----------------------------------------
# IFF Broadcaster
# ----------------------------------------
class IFF(Worker):
    def __init__(self, device, name):
        super().__init__(device, name)
        self.logger.info(f"IFF INITIALIZED for device {self.device.device_id}")

    def run(self):
        config = zenoh.Config()
        self.zenoh_client = zenoh.open(config)
        self.pub = self.zenoh_client.declare_publisher('global/IFF')

        self.logger.info("IFF Publisher Running.")
        while not self.is_stopped.value:
            try:
                ping = f"{time.time()}, {self.device.device_id}, {self.device.name}, {self.device.ip}"
                self.pub.put(ping)
                self.logger.info(f"IFF Ping: {ping}")
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"IFF Publisher Error: {e}")

# TODO Failsafe IFF

# if __name__ == "__main__":
#     from devices.device import Device
#     import sys
#     import signal

#     from utils.setup_logger import setup_logger
                    
#     # ----------------------------------------
#     # Signal Handling
#     # ----------------------------------------
#     logger = setup_logger("Main")
#     devices = []

#     def signal_handler(sig, frame):
#         logger.info("Ctrl+C detected. Ending all processes...")
#         for device in devices:
#             device.stop()
#         sys.exit(0)

#     signal.signal(signal.SIGINT, signal_handler)

#     # ----------------------------------------
#     # Launch
#     # ----------------------------------------

#     logger.warning("Well this is odd... Looks like we are in fail safe mode, starting IFF declaration.")

#     class IFFfailsafe(Device):
#         def __init__(self):
#             super().__init__()

#             self.multicast_ip = "239.255.42.42"
#             self.port = 5555
#             self.camera_endpoint = f"udp://{self.multicast_ip}:{self.port}"
#             self.target_framerate = 30
#             self.target_resolution = "640x480"
#             self.target_bitrate = 4000

#             # Control flags
#             self.recorders = []
#             self.is_recording = False

#             self.processes = [
#                 Camera_Controller(self, "Camera_Controller", DEBUG=True),
#                 Camera_RTPS(self, "Camera_RTPS", DEBUG=True)
#             ]

#         def __setup__(self):
#             self.logger.info("Setting up device...")

#         # Device Specific Methods
#         def start_recorder(self):
#             if not self.is_recording:
#                 self.is_recording = True
#                 self.logger.info("Starting recorder...")

#                 recorder = Camera_Recorder(self, "Camera_Recorder", DEBUG=True)
#                 self.processes.append(recorder)
#                 self.recorders.append(recorder)
#                 recorder.start()
#             else:
#                 self.logger.warning("Recorder is already running.")

#         def stop_recorder(self):
#             if self.is_recording and self.recorders:
#                 self.is_recording = False
#                 self.logger.info("Stopping recorder...")

#                 for recorder in self.recorders:
#                     self.logger.info("Stopping recorder process...")
#                     recorder.stop()
#                     recorder.join(timeout=5)
#             else:
#                 self.logger.warning("No recorder is running.")

#         # Use Specific Methods for Camera Device
#         def start_trial(self, config=None):
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             trial_dir = os.path.join("trials", f"trial_{timestamp}")
#             os.makedirs(trial_dir, exist_ok=True)

#             if config:
#                 with open(os.path.join(trial_dir, "config.txt"), "w") as f:
#                     f.write(str(config))
#             with open(os.path.join(trial_dir, "started.txt"), "w") as f:
#                 f.write(f"Trial started at {timestamp}\n")
#             self.logger.info(f"Trial started at {trial_dir}")

#         def stop_trial(self):
#             self.logger.info("Trial stopped.")