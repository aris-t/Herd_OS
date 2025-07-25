import os
from datetime import datetime
from .device import Device
from .workers import Camera_Controller
from .workers import Camera_Recorder  # Ensure this import is correct based on your file structure
from .workers import Camera_RTPS  # Ensure this import is correct based on your file structure

# # ----------------------------------------
# # Device
# # ----------------------------------------

class Camera(Device):
    def __init__(self):
        super().__init__()

        self.multicast_ip = "239.255.42.42"
        self.port = 5555
        self.camera_endpoint = f"udp://{self.multicast_ip}:{self.port}"
        self.target_framerate = 30
        self.target_resolution = "640x480"
        self.target_bitrate = 4000

        # Control flags
        self.recorders = []
        self.is_recording = False

        # TODO Need to include LETHAL flag for critical processes that fail to start
        self.processes = [
            Camera_Controller(self, "Camera_Controller", DEBUG=True),
            Camera_RTPS(self, "Camera_RTPS", DEBUG=True)
        ]

        self.commands = {
            "start_recorder": lambda parameter: self.start_recorder(),
            "stop_recorder": lambda parameter: self.stop_recorder(),
        }

    def __setup__(self):
        self.logger.info("Setting up device...")

    # Device Specific Methods
    def start_recorder(self, timer=None, chunk_time=False):
        if not self.is_recording:
            self.is_recording = True
            self.logger.info("Starting recorder...")

            recorder = Camera_Recorder(self, "Camera_Recorder", DEBUG=True)
            self.processes.append(recorder)
            self.recorders.append(recorder)
            recorder.start()
        else:
            self.logger.warning("Recorder is already running.")

    def stop_recorder(self):
        if self.is_recording and self.recorders:
            self.is_recording = False
            self.logger.info("Stopping recorder...")

            for recorder in self.recorders:
                self.logger.info("Stopping recorder process...")
                try:
                    # First try graceful stop
                    recorder.stop()
                    
                    # Wait for process to terminate gracefully
                    recorder.join(timeout=10)
                    
                    # If still alive, force terminate
                    if recorder.is_alive():
                        self.logger.warning("Recorder didn't stop gracefully, terminating...")
                        recorder.terminate()
                        recorder.join(timeout=5)
                        
                    # Final check - kill if necessary
                    if recorder.is_alive():
                        self.logger.error("Force killing recorder process...")
                        recorder.kill()
                        recorder.join()
                        
                except Exception as e:
                    self.logger.error(f"Error stopping recorder: {e}")

            # Clear the recorders list
            self.recorders.clear()
            
            # Remove stopped recorders from processes list
            self.processes = [p for p in self.processes if not isinstance(p, Camera_Recorder) or p.is_alive()]
        
        else:
            self.logger.warning("No recorder is running.")

    # Cleanup Methods
    def cleanup_all_processes(self):
        """Clean up all processes including recorders"""
        self.stop_recorder()
        
        for process in self.processes:
            if process.is_alive():
                try:
                    process.stop()
                    process.join(timeout=5)
                    if process.is_alive():
                        process.terminate()
                        process.join()
                except Exception as e:
                    self.logger.error(f"Error cleaning up process {process.name}: {e}")

    # Use Specific Methods for Camera Device
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
