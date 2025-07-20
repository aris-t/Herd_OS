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

            # TODO fingerpint the camera and hardware

    def gstreamer_factory(self, mode, width=640, height=480, framerate=30, format="I420", shm_size=10000000, show_preview=False):
        # Build pipeline elements as a list for clarity and flexibility
        # Debug Pipeline
        if mode == "debug":
            elements = [
                "videotestsrc is-live=true pattern=ball",
                f"video/x-raw, width={width}, height={height}, framerate={framerate}/1",
                "tee name=t",
                "t. ! queue leaky=downstream max-size-buffers=2",
                f"videoconvert ! video/x-raw, format={format}",
                f"shmsink socket-path={self.shm_path} shm-size={shm_size} sync=false wait-for-connection=false"
            ]

        # Pi 5 Cam 3 Pipeline
        elif mode == "pi5_cam3":
            elements = [
                "libcamerasrc",
                "videoconvert",
                "video/x-raw,width=640,height=480,framerate=30/1,format=I420",
                "tee name=t",
                "t. ! queue leaky=downstream max-size-buffers=2",
                "shmsink socket-path=/tmp/video.shm shm-size=100000000 sync=false wait-for-connection=false",
                "t. ! fakesink"
            ]

        # Preview 
        if show_preview:
            elements.append("t. ! queue ! autovideosink")
        pipeline_str = " ! ".join(elements)
        self.logger.info(f"[{self.device.device_id}][{self.name}] GStreamer Pipeline: {pipeline_str}")
        return pipeline_str

    def run(self):
        pipeline_str = (
        f"libcamerasrc ! videoconvert ! "
        "video/x-raw,width=640,height=480,framerate=30/1,format=I420 ! "
        "tee name=t "
        "t. ! queue leaky=downstream max-size-buffers=2 ! "
        f"shmsink socket-path={self.shm_path} shm-size=100000000 sync=false wait-for-connection=false "
        "t. ! fakesink"
        )

        self.startup()
        pipeline_str = pipeline_str
        self.logger.info(f"[{self.device.device_id}][{self.name}] GStreamer Pipeline: {pipeline_str}")

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
