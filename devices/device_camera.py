import os
from datetime import datetime
from .device import Device
from .workers import Camera_Controller
from .workers import Camera_Recorder  # Ensure this import is correct based on your file structure
from .workers import Camera_RTPS  # Ensure this import is correct based on your file structure

from multiprocessing import Value
import time

# # ----------------------------------------
# # Device
# # ----------------------------------------

class Camera(Device):
    def __init__(self, logger=None, DEBUG=False):
        super().__init__(logger=logger, DEBUG=DEBUG)

        self.multicast_ip = "239.255.42.42"
        self.port = 5555
        self.camera_endpoint = f"udp://{self.multicast_ip}:{self.port}"
        self.target_framerate = 30
        self.target_resolution = "640x480"
        self.target_bitrate = 4000

        # Control flags

        self.recorders = []

        # Health Flags
        self.camera_is_ready = Value('b', False)
        self.in_trial = Value('b', False)
        self.is_passive = Value('b', False)
        self.is_recording = Value('b', False)
        self.is_streaming = Value('b', False)

        # TODO Need to include LETHAL flag for critical processes that fail to start
        self.processes = [
            Camera_Controller(self, "Camera_Controller", DEBUG=True, LETHAL=True),
            Camera_RTPS(self, "Camera_RTPS", DEBUG=True)
        ]

        self.commands = {
            "start_recorder": lambda parameter: self.start_recorder(),
            "stop_recorder": lambda parameter: self.stop_recorder(),
            "start_trial": lambda trial_name: self.start_trial(trial_name),
            "stop_trial": lambda parameter: self.stop_trial(),
        }

    def __setup__(self):
        self.logger.info("Setting up device...")

    # Device Specific Methods
    def start_recorder(self,file_base=None, timer=None):
        if not self.is_recording.value:
            self.is_recording.value = True
            self.logger.info("Starting recorder...")

            recorder = Camera_Recorder(self, "Camera_Recorder", file_base=file_base)
            self.processes.append(recorder)
            self.recorders.append(recorder)
            recorder.start()
        else:
            self.logger.warning("Recorder is already running.")

    def stop_recorder(self):
        if self.is_recording.value and self.recorders:
            self.is_recording.value = False
            self.logger.info("Stopping recorder...")

            for recorder in self.recorders:
                self.logger.info("Stopping recorder process...")
                try:
                    # First try graceful stop
                    returned = recorder.stop()
                    self.logger.info(f"Manager: Recorder stopped gracefully: {returned}")
                    
                    if not recorder.is_alive():
                        self.logger.info("Recorder process is confirmed dead.")
                    else:
                        self.logger.warning("Recorder process is still alive after stop attempt.")
                    
                    # Wait for process to terminate gracefully
                    recorder.join(timeout=0.5)
                    
                    # If still alive, force terminate
                    if recorder.is_alive():
                        self.logger.warning("Recorder didn't stop gracefully, terminating...")
                        recorder.terminate()
                        recorder.join(timeout=0.5)
                        
                    # Final check - kill if necessary
                    if recorder.is_alive():
                        self.logger.error("Force killing recorder process...")
                        recorder.kill()
                        recorder.join()
                    else:
                        self.logger.info("✅ Its dead Jim... ✅")
                        
                except Exception as e:
                    self.logger.error(f"Error stopping recorder: {e}")

            # Clear the recorders list
            self.recorders.clear()
            
            # Remove stopped recorders from processes list
            self.processes = [p for p in self.processes if not isinstance(p, Camera_Recorder) or p.is_alive()]
        
        else:
            self.logger.warning("No recorder is running.")

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

    ### Use Specific Methods for Camera Device
    # Trial Camera
    def start_trial(self, trial_name):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_recorder(file_base=f"{trial_name}_{self.name}")

    def stop_trial(self):
        self.logger.info("Trial stopped.")
        self.stop_recorder()

    # Passive Camera
    def start_passive(self):
        self.logger.info("Starting passive camera...")
        while not self.is_stopped.value or self.is_passive.value:
            self.start_recorder(file_base=f"passive_{self.name}")
            time.sleep(120)  # Record for 2 minutes
            self.stop_recorder()

    def stop_passive(self):
        self.logger.info("Stopping passive camera...")
        self.is_passive.value = False
