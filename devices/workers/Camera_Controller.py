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
    def __init__(self, device, name, DEBUG=False, LETHAL=False, OVERWRITE_SHM=True,
                 camera_device=None, shm_path=None):
        super().__init__(device,name)
        self.OVERWRITE_SHM = OVERWRITE_SHM
        self.DEBUG = DEBUG
        self.LETHAL = LETHAL

        self.device = device

        self.camera_device = camera_device if camera_device else "/dev/video0"
        self.shm_path = "/tmp/testshm"

    def startup(self):
            self.logger.info(f"[{self.device.device_id}][{self.name}] Starting up...")

            # TODO fingerpint the camera and hardware

    def gstreamer_factory(self, mode, width=640, height=480, framerate=30, format="I420", shm_size=13442688, show_preview=False):
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
            # Preview 
            if show_preview:
                elements.append("t. ! queue ! autovideosink")
            pipeline_str = " ! ".join(elements)

        # Pi 5 Cam 3 Pipeline
        elif mode == "pi5_cam3":
            # TODO Make dynamic config work
            valid_cfgs = [
                    [1536, 864, [120.13]],
                    [2304, 1296, [56.03, 30.0]],  # 30.0 for HDR (typical)
                    [4608, 2592, [14.35]]
                ]
            
            # Add a timeoverlay element to inject a timestamp on each frame
            pipeline_str = (
                f"libcamerasrc af-mode=continuous ! "
                # f"libcamerasrc af-mode=continuous camera-name=\"{self.camera_device}\" ! "

                "videoconvert ! "
                
                f"textoverlay  halignment=center valignment=top text=\"{self.device.device_id}:{self.device.name}\" font-desc=\"Sans, 5\" ! "
                "clockoverlay  halignment=right valignment=top time-format=\"%D_%H:%M:%S\" font-desc=\"Sans, 5\" ! "
                "clockoverlay  halignment=left valignment=top time-format=\"%D_%H:%M:%S\" font-desc=\"Sans, 5\" ! "

                f"textoverlay  halignment=center valignment=bottom text=\"{self.device.device_id}:{self.device.name}\" font-desc=\"Sans, 5\" ! "
                "clockoverlay  halignment=right valignment=bottom time-format=\"%D_%H:%M:%S\" font-desc=\"Sans, 5\" ! "
                "clockoverlay  halignment=left valignment=bottom time-format=\"%D_%H:%M:%S\" font-desc=\"Sans, 5\" ! "

                "video/x-raw,width=2304,height=1296,framerate=30/1,format=I420 ! "

                "tee name=t "
                "t. ! queue leaky=downstream max-size-buffers=2 ! "
                # 3 × 4,480,896 = 13,442,688 bytes
                # shm_size = width * height * 3 // 2 * num_frames
                f"shmsink socket-path={self.shm_path} shm-size=13442688 sync=false wait-for-connection=false "
                "t. ! fakesink"
            )

        return pipeline_str

    def run(self):
        self.startup()
        pipeline_str = self.gstreamer_factory(mode="pi5_cam3")
        self.logger.info(f"[{self.device.device_id}][{self.name}] GStreamer Pipeline: {pipeline_str}")

        if os.path.exists(self.shm_path):
            if self.OVERWRITE_SHM:
                try:
                    os.remove(self.shm_path)
                    self.logger.info(f"🧹 OVERWRITING existing socket file: {self.shm_path}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to remove existing socket file: {e}")
                    self.health.value = 2
            else:
                self.logger.warning(f"Shared memory destination '{self.shm_path}' already exists. Aborting.")
                self.health.value = 2  # Error state
                return
        else:
            pipeline = Gst.parse_launch(pipeline_str)
            pipeline.set_state(Gst.State.PLAYING)

            self.logger.info("Camera is Ready and streaming...")
            self.device.camera_is_ready.value = True

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
                self.logger.info(f"🧹 Removed socket file: {self.shm_path}")
        except Exception as e:
            self.logger.info(f"⚠️ Failed to remove socket file: {e}")
        time.sleep(1)  # Give some time for the process to stop gracefully
        self.terminate()
