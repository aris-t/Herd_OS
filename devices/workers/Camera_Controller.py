import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

import time
from .worker import Worker
import os
import glob
import subprocess

Gst.init(None)

class Camera_Controller(Worker):
    def __init__(self, device, name, DEBUG=False, OVERWRITE_SHM=True):
        super().__init__(device,name)
        self.OVERWRITE_SHM = OVERWRITE_SHM
        self.DEBUG = DEBUG
        self.device = device

        self.shm_path = "/tmp/testshm"

    def startup(self):
            self.logger.info(f"[{self.device.device_id}][{self.name}] Starting up...")
            # Check for available video devices (e.g., /dev/video*)
            video_devices = glob.glob('/dev/video*')
            device_info = []

            for dev in video_devices:
                info = {"device": dev, "type": "Unknown", "make": "Unknown"}
                try:
                    # Try to get device info using v4l2-ctl if available
                    result = subprocess.run(
                        ["v4l2-ctl", "--device", dev, "--all"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    if result.returncode == 0:
                        output = result.stdout
                        if "usb" in output.lower():
                            info["type"] = "USB Camera"
                        elif "platform" in output.lower():
                            info["type"] = "Webcam"
                        # Try to extract card/make info
                        for line in output.splitlines():
                            if "Card type" in line or "card type" in line:
                                info["make"] = line.split(":", 1)[-1].strip()
                            elif "Driver name" in line and info["make"] == "Unknown":
                                info["make"] = line.split(":", 1)[-1].strip()
                    else:
                        info["type"] = "Unknown"
                except Exception as e:
                    self.logger.warning(f"Could not get info for {dev}: {e}")
                device_info.append(info)

            self.logger.info(f"Detected video devices: {device_info}")
            return device_info

    def gstreamer_factory(self, width=640, height=480, framerate=30, format="I420", show_preview=True):
        # Build pipeline elements as a list for clarity and flexibility
        elements = [
            "videotestsrc is-live=true pattern=ball",
            f"video/x-raw, width={width}, height={height}, framerate={framerate}/1",
            "tee name=t",
            "t. ! queue leaky=downstream max-size-buffers=2",
            f"videoconvert ! video/x-raw, format={format}",
            f"shmsink socket-path={self.shm_path} shm-size=10000000 sync=false wait-for-connection=false"
        ]
        if show_preview:
            elements.append("t. ! queue ! autovideosink")
        pipeline_str = " ! ".join(elements)
        return pipeline_str

    def run(self):

        self.startup()
        pipeline_str = self.gstreamer_factory()

        if os.path.exists(self.shm_path):
            if self.OVERWRITE_SHM:
                try:
                    os.remove(self.shm_path)
                    print(f"🧹 OVERWRITING existing socket file: {self.shm_path}")
                except Exception as e:
                    print(f"⚠️ Failed to remove existing socket file: {e}")
                    self.health.value = 2
            else:
                print(f"Shared memory destination '{self.shm_path}' already exists. Aborting.")
                self.health.value = 2  # Error state
                return
        else:
            pipeline = Gst.parse_launch(pipeline_str)
            pipeline.set_state(Gst.State.PLAYING)

            # Keep running until user interrupts
            try:
                loop = GObject.MainLoop()
                loop.run()
            except KeyboardInterrupt:
                pass
            finally:
                pipeline.set_state(Gst.State.NULL)

    def stop(self):
        self.is_stopped.value = True
        self.logger.info(f"[{self.device.device_id}][{self.name}] Stopping ...")
        # Attempt to clean up the shared memory socket file
        try:
            if os.path.exists(self.shm_path):
                os.remove(self.shm_path)
                print(f"🧹 Removed socket file: {self.shm_path}")
        except Exception as e:
            print(f"⚠️ Failed to remove socket file: {e}")
        time.sleep(1)  # Give some time for the process to stop gracefully
        self.terminate()
