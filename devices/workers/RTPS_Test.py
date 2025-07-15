#!/usr/bin/env python3
from gi.repository import Gst, GstRtspServer, GLib
Gst.init(None)

from .worker import Worker

class TestFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self):
        super().__init__()
        self.set_launch((
            "shmsrc socket-path=/tmp/testshm do-timestamp=true is-live=true ! "
            "video/x-raw,format=I420,width=640,height=480,framerate=30/1 ! "
            "videoconvert ! "
            "x264enc tune=zerolatency bitrate=500 speed-preset=ultrafast ! "
            "rtph264pay name=pay0 pt=96"
        ))
        self.set_shared(True)

class Camera_RTPS(Worker):
    def __init__(self, device, name, DEBUG=False):
        super().__init__(device,name)
        self.DEBUG = DEBUG
        self.device = device

    def run(self):
        server = GstRtspServer.RTSPServer()
        mounts = server.get_mount_points()
        mounts.add_factory("/stream", TestFactory())

        res = server.attach(None)
        if not res:
            print("❌ Failed to attach RTSP server")
        else:
            print(f"✅ RTSP server running at rtsp://{self.device.ip}:8554/stream")

        GLib.MainLoop().run()

    def stop(self):
        self.is_stopped.value = True



        
