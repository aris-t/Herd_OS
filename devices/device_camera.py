from datetime import datetime
from .device import Device
from .workers import Camera_Controller
from .workers import Camera_Recorder
from .workers import Camera_RTPS

from multiprocessing import Value
import time

# -----------------------------------------------------------------------
# Camera Device Class
# -----------------------------------------------------------------------
class Camera(Device):
    def __init__(self, logger=None, DEBUG=False, cameras=None):
        super().__init__(logger=logger, DEBUG=DEBUG)

        # Control flags
        self.recorders = []

        # Health Flags
        self._health_camera_is_ready = Value('b', False)
        self._health_in_trial = Value('b', False)
        self._health_is_passive = Value('b', False)
        self._health_is_recording = Value('b', False)
        self._health_is_streaming = Value('b', False)

        # Multi Camera Support
        # TODO need to add discovery for multiple cameras, manual for now
        if cameras is None:
            self.cameras = [0]
        else:
            if isinstance(cameras, list):
                self.cameras = cameras
            else:
                raise ValueError(f"cameras must be a list of integers, got: {cameras}")

        # Processes
        # TODO Need to include LETHAL flag for critical processes that fail to start
        self.processes = []

        for camera in self.cameras:
            camera_worker = Camera_Controller(self, f"Camera_Controller_{camera}", DEBUG=self.DEBUG, camera_device=camera, LETHAL=True)
            rtps_worker = Camera_RTPS(self, f"Camera_RTPS_{camera}", DEBUG=self.DEBUG, camera_device=camera)
            self.processes.append(camera_worker)
            self.processes.append(rtps_worker)

        self.commands = {
            "start_recorder": lambda **properties: self.start_recorder(),
            "stop_recorder": lambda **properties: self.stop_recorder(),
            "start_trial": lambda **properties: self.start_trial(properties.get('trial_name', None)),
            "stop_trial": lambda **properties: self.stop_trial(),
        }

    def __setup__(self):
        self.logger.info("Setting up device...")

# -----------------------------------------------------------------------
# Device Specific Methods
# -----------------------------------------------------------------------

    def start_recorder(self, file_base=None, timer=None):
        if not self._health_is_recording.value:
            self._health_is_recording.value = True
            self.logger.info("Starting recorder(s)...")

            for camera in self.cameras:
                self.logger.info(f"Creating recorder for camera {camera}...")
                recorder = Camera_Recorder(self, f"Camera_Recorder_{camera}", camera_device=camera, file_base=file_base)
                self.processes.append(recorder)
                self.recorders.append(recorder)
            for recorder in self.recorders:
                recorder.start()
            self.logger.info(f"{len(self.recorders)} started successfully.")

        else:
            self.logger.warning("Recorder is already running.")

    def stop_recorder(self):
        if self._health_is_recording.value and self.recorders:
            self._health_is_recording.value = False
            self.logger.info("Stopping recorder...")

            for recorder in self.recorders:
                recorder.stand_down()

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

# -----------------------------------------------------------------------
# Use Specific Methods
# -----------------------------------------------------------------------
    # Trial Camera
    def start_trial(self, trial_name):
        if not trial_name:
            trial_name = "trial_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger.info(f"Starting trial: {trial_name} at {timestamp}")
        if not self._health_in_trial.value:
            self._health_in_trial.value = True
            self.logger.info("Starting trial camera...")
            if not self._health_is_recording.value:
                self.start_recorder(file_base=f"{trial_name}_{self.name}")
            else:
                self.logger.warning("Recorder is already running), skipping start.")
                self.stop_trial()

    def stop_trial(self, trial_name=None, trial_id=None):
        self.logger.info("Trial stopped.")
        self.stop_recorder()
        self._health_in_trial.value = False

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
