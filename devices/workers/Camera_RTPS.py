#!/usr/bin/env python3

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib

Gst.init(None)

from .worker import Worker

class TestFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, camera_device=None, shm_base=None):
        super().__init__()

        if camera_device is not None:
            try:
                self.camera_device = int(camera_device)
            except (ValueError, TypeError):
                raise ValueError(f"camera_device must be int, 0, 1, ..., got: {camera_device}")
        else:
            self.camera_device = 0

        if shm_base is None:
            self.shm_base = "/tmp/pi_cam_shm_"
        else:
            self.logger.warning(f"Using custom shm_base: {shm_base}")

        self.shm_path = f"/tmp/pi_cam_shm_{self.camera_device}"


        self.set_launch((
            f"shmsrc socket-path={self.shm_path} do-timestamp=true is-live=true ! "
            "video/x-raw,format=I420,width=2304,height=1296,framerate=30/1 ! "
            "videoconvert ! "
            "x264enc tune=zerolatency bitrate=10000 speed-preset=ultrafast ! "
            "rtph264pay name=pay0 pt=96"
        ))

        self.set_shared(True)

class Camera_RTPS(Worker):
    def __init__(self, device, name, DEBUG=False, LETHAL=False):
        super().__init__(device,name)
        self.DEBUG = DEBUG
        self.LETHAL = LETHAL

        self.device = device
        self.server = None
        self.main_loop = None

    def run(self):
        while self.device.camera_is_ready.value is False:
            self.logger.info("Waiting for camera to be ready...")
            GLib.timeout_add_seconds(1, lambda: None)
        
        self.server = GstRtspServer.RTSPServer()
        # self.server.set_service(str(self.port))  # Set custom port
        mounts = self.server.get_mount_points()
        mounts.add_factory("/stream", TestFactory())

        res = self.server.attach(None)
        
        if not res:
            self.logger.info("❌ Failed to attach RTSP server")
            return
        else:
            self.logger.info(f"✅ RTSP server running at rtsp://{self.device.ip}:8554/stream")

        self.main_loop = GLib.MainLoop()
        
        # Check periodically if we should stop
        def check_stop():
            if self.is_stopped.value:
                self.main_loop.quit()
                return False  # Don't repeat
            return True  # Continue checking
        
        GLib.timeout_add_seconds(1, check_stop)
        self.main_loop.run()

    def stop(self):
        self.logger.info(f"[{self.device.device_id}][{self.name}] Stopping RTSP server...")
        self.is_stopped.value = True
        
        # Stop the main loop if it's running
        if self.main_loop and self.main_loop.is_running():
            self.main_loop.quit()
        
        # Clean up the server
        if self.server:
            # Remove all mount points
            mounts = self.server.get_mount_points()
            mounts.remove_factory("/stream")
            self.server = None
        
        self.logger.info(f"[{self.device.device_id}][{self.name}] RTSP server stopped")

# RX gst-launch-1.0 -v rtspsrc location=rtsp://192.168.1.50:8554/stream latency=50 protocols=tcp ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink

        
