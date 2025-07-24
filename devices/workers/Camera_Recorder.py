#!/usr/bin/env python3
from gi.repository import Gst, GLib
import datetime
import os
Gst.init(None)

from .worker import Worker
from .Upload_Service import upload_file_in_chunks
import os

class Camera_Recorder(Worker):
    def __init__(self, device, name, UPLOAD_ON_FINISH=True, DEBUG=False):
        super().__init__(device, name)
        self.DEBUG = DEBUG
        self.device = device
        self.loop = GLib.MainLoop()
        self.UPLOAD_ON_FINISH = UPLOAD_ON_FINISH

        # Needed for early Termination
        self.pipeline = None

    def run(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trials")
        os.makedirs(output_dir, exist_ok=True)
        self.filename = os.path.join(output_dir, f"output_{timestamp}.mkv")

        socket_path = "/tmp/testshm"
        if not os.path.exists(socket_path):
            print(f"❌ Error: Socket path '{socket_path}' does not exist.")
            return

        pipeline_str = f"""
        shmsrc socket-path={socket_path} do-timestamp=true is-live=true !
        video/x-raw,format=I420,width=2304,height=1296,framerate=30/1 !
        tee name=t

        t. ! queue ! videoconvert ! fakesink sync=false async=false

        t. ! queue ! videoconvert !
        x264enc tune=zerolatency bitrate=500 speed-preset=ultrafast !
        matroskamux !
        filesink location={self.filename} sync=false
        """

        self.pipeline = Gst.parse_launch(pipeline_str)

        # Watch for bus messages to stop cleanly
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

        self.pipeline.set_state(Gst.State.PLAYING)
        self.logger.info(f"🎥 Recording to {self.filename}...")
        self.loop.run()

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            self.logger.error(f"❌ GStreamer Error: {err}, {debug}")
            self.stop()
        elif t == Gst.MessageType.EOS:
            self.logger.info("✅ End of Stream")
            self.stop()

    def stop(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline.get_bus().remove_signal_watch()
            self.pipeline = None
        if self.loop.is_running():
            self.loop.quit()
        self.logger.info("Recorder stopped.")
        
        # Upload the recorded file if enabled
        self.logger.info(f"Upload status: {self.UPLOAD_ON_FINISH}, "
                         f"File exists: {hasattr(self, 'filename')}, "
                         f"File path: {os.path.exists(self.filename)}")
        if self.UPLOAD_ON_FINISH and hasattr(self, 'filename') and os.path.exists(self.filename):
            self.logger.info(f"📤 Uploading {self.filename}...")
            upload_file_in_chunks(self.filename)

        self.is_stopped.value = True
        self.logger.info("Recorder process request terminate.")
        self.terminate()
