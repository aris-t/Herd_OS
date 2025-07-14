import time
import os

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GObject, GLib

import zenoh
from .worker import Worker

Gst.init(None)

class Camera_Controller(Worker):
    def __init__(self, device, name, DEBUG=False):
        super().__init__(device, name)
        self.DEBUG = DEBUG
        self.device = device
        self.port = 8554
        self.logger.info("Camera controller initialized with RTSP + record + display")

    def broadcast_status(self, publisher):
        stream_uri = f"rtsp://{self.device.ip}:{self.port}/stream"
        self.logger.debug(f"Broadcasting RTSP stream URL: {stream_uri}")
        publisher.put(stream_uri)
        return True

    def run(self):
        # Setup Zenoh
        config = zenoh.Config()
        self.zenoh_client = zenoh.open(config)
        self.pub = self.zenoh_client.declare_publisher('camera/declare')

        # Setup output file path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        trials_dir = os.path.join(base_dir, "trials")
        os.makedirs(trials_dir, exist_ok=True)
        output_file = os.path.join(trials_dir, f"output_{time.time()}.mkv")

        # Build pipeline
        if self.DEBUG:
            source = "videotestsrc pattern=ball"
        else:
            source = "v4l2src"

        pipeline_str = (
            f"{source} ! videoconvert ! tee name=t "
            # Branch 1: RTSP stream
            "t. ! queue ! x264enc tune=zerolatency bitrate=500 speed-preset=ultrafast ! "
            "rtph264pay config-interval=1 pt=96 name=pay0 "
            # Branch 2: Local file recording
            f"t. ! queue ! x264enc tune=zerolatency bitrate=500 speed-preset=ultrafast ! h264parse ! matroskamux ! filesink location={output_file} async=false sync=false "
            # Branch 3: Local display
            "t. ! queue ! videoconvert ! autovideosink sync=false"
        )

        try:
            self.pipeline = Gst.parse_launch(pipeline_str)
            self.pipeline.set_state(Gst.State.PLAYING)

            bus = self.pipeline.get_bus()
            bus.add_signal_watch()

            def on_message(bus, message):
                if message.type == Gst.MessageType.EOS:
                    self.logger.info("End of stream")
                    if hasattr(self, 'main_loop') and self.main_loop.is_running():
                        self.main_loop.quit()
                elif message.type == Gst.MessageType.ERROR:
                    err, debug = message.parse_error()
                    self.logger.error(f"Error from {message.src.get_name()}: {err}")
                    self.logger.error(f"Debug: {debug}")
                    if hasattr(self, 'main_loop') and self.main_loop.is_running():
                        self.main_loop.quit()
                return True

            bus.connect("message", on_message)

        except Exception as e:
            self.logger.error(f"Pipeline error: {e}")
            return

        self.logger.info(f"RTSP-style pipeline ready. Recording to: {output_file}")
        GLib.timeout_add(2000, self.broadcast_status, self.pub)

        try:
            self.main_loop = GLib.MainLoop()
            while not self.is_stopped.value:
                time.sleep(1)
            else:
                self.main_loop.run()
        except KeyboardInterrupt:
            self.logger.warning("Stopping...")
        finally:
            if self.pipeline:
                self.logger.info("Sending EOS...")
                self.pipeline.send_event(Gst.Event.new_eos())

                # Wait for EOS or ERROR
                while True:
                    msg = bus.timed_pop_filtered(
                        Gst.SECOND * 5,
                        Gst.MessageType.EOS | Gst.MessageType.ERROR
                    )
                    if msg:
                        break

                self.logger.info("Shutting down pipeline...")
                self.pipeline.set_state(Gst.State.NULL)
