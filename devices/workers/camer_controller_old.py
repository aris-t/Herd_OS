import time

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gst, GObject, GLib

import zenoh
from .worker import Worker
import os

# ----------------------------------------
# Camera Controller
# ----------------------------------------
Gst.init(None)

class Camera_Controller(Worker):
    def __init__(self, device, name, DEBUG=False):
        super().__init__(device,name)
        self.DEBUG = DEBUG
        self.device = device
        self.multicast_ip = device.multicast_ip
        self.port = device.port

    def broadcast_status(self, publisher):
        msg = f"udp://{self.multicast_ip}:{self.port}"
        self.logger.debug("Stream active")
        publisher.put(msg)
        return True

    def run(self):
        config = zenoh.Config()
        self.zenoh_client = zenoh.open(config)
        self.pub = self.zenoh_client.declare_publisher('camera/declare')

        # Initialize pipeline string for streaming and recording to file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        trials_dir = os.path.join(base_dir, "trials")
        if not os.path.exists(trials_dir):
            os.makedirs(trials_dir)
        output_file = os.path.join(trials_dir, f"output_{time.time()}.mkv")  # Absolute path to output file

        if self.DEBUG:
            # Hardwareless testing mode: stream and save to file
            pipeline_str = (
                "videotestsrc pattern=ball ! "
                "videoconvert ! "
                "tee name=t "

                # Branch 1: UDP multicast stream
                "t. ! queue ! video/x-raw,width=640,height=480,framerate=30/1 ! "
                "x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! "
                "rtph264pay config-interval=1 pt=96 ! "
                f"udpsink host={self.multicast_ip} port={self.port} auto-multicast=true "

                # Branch 2: Save to file (valid MP4)
                "t. ! queue ! video/x-raw,width=640,height=480,framerate=30/1 ! "
                "x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! "
                "h264parse ! matroskamux ! "
                "filesink location={} async=false sync=false ".format(output_file) +

                # Branch 3: Visual output
                "t. ! queue ! autovideosink"
            )
        else:
            # Real camera pipeline (replace videotestsrc with actual camera src if needed)
            pipeline_str = (
            "videotestsrc ! "
            "videoconvert ! "
            "tee name=t "
            "t. ! queue ! video/x-raw,width=640,height=480,framerate=30/1 ! "
            "x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! "
            "rtph264pay config-interval=1 pt=96 ! "
            f"udpsink host={self.multicast_ip} port={self.port} auto-multicast=true "
            "t. ! queue ! x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! "
            "mp4mux ! filesink location={}".format(output_file)
            )

        try:
            pipeline = Gst.parse_launch(pipeline_str)
            pipeline.set_state(Gst.State.PLAYING)

            # Handle messages
            bus = pipeline.get_bus()
            bus.add_signal_watch()

            def on_message(bus, message):
                if message.type == Gst.MessageType.EOS:
                    self.logger.info("End of stream")
                    # Graceful shutdown: stop main loop
                    if hasattr(self, 'main_loop') and self.main_loop.is_running():
                        self.main_loop.quit()
                elif message.type == Gst.MessageType.ERROR:
                    err, debug = message.parse_error()
                    self.logger.error(f"Error received from element {message.src.name}: {err.message}")
                    self.logger.error(f"Debugging information: {debug if debug else 'none'}")
                    # Graceful shutdown on error
                    if hasattr(self, 'main_loop') and self.main_loop.is_running():
                        self.main_loop.quit()
                return True

            bus.connect("message", on_message)

        except Exception as e:
            self.logger.error(f"Failed to start GStreamer pipeline: {e}")
            return

        self.logger.info(f"Publishing stream to udp://{self.multicast_ip}:{self.port}")
        GLib.timeout_add(2000, self.broadcast_status, self.pub)

        try:
            loop = GObject.MainLoop()
            while not self.is_stopped.value:
                time.sleep(1)
            else:
                loop.run()
        except KeyboardInterrupt:
            self.logger.warning("Stopping camera stream...")
        finally:
            if pipeline:
                self.logger.info("Sending EOS...")
                pipeline.send_event(Gst.Event.new_eos())

                # Wait for EOS or ERROR
                while True:
                    msg = bus.timed_pop_filtered(
                        Gst.SECOND * 5,
                        Gst.MessageType.EOS | Gst.MessageType.ERROR
                    )
                    if msg:
                        if msg.type == Gst.MessageType.ERROR:
                            err, debug = msg.parse_error()
                            self.logger.error(f"Error during EOS wait: {err}, {debug}")
                        break

                self.logger.info("Shutting down pipeline...")
                pipeline.set_state(Gst.State.NULL)