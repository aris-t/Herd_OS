# https://gstreamer.freedesktop.org/documentation/x264/index.html?gi-language=c#GstX264EncPreset

#!/usr/bin/env python3
from gi.repository import Gst, GLib
import datetime
import os
Gst.init(None)

from .worker import Worker

OUTPUT_DIR = os.path.join(os.getcwd(), "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class Camera_Recorder(Worker):
    def __init__(self, device, name, file_base= None, UPLOAD_ON_FINISH=True, DEBUG=False):
        super().__init__(device, name)
        self.DEBUG = DEBUG
        self.device = device
        self.UPLOAD_ON_FINISH = UPLOAD_ON_FINISH
        self.file_base = file_base

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if self.file_base is not None:
            self.imagename = os.path.join(OUTPUT_DIR, f"{timestamp}_{self.file_base}.png")
        else:
            self.imagename = os.path.join(OUTPUT_DIR, f"{timestamp}_{self.device.device_id}_output.png")

        # Create a new, dedicated GLib main context
        self.context = GLib.MainContext.new()

        # Create the main loop using that context
        self.loop = GLib.MainLoop(context=self.context)

        # Needed for early Termination
        self.pipeline = None

    def run(self):
        try:
            # Step 1: 
            self.context.push_thread_default()
            if GLib.MainContext.get_thread_default() == self.context:
                self.logger.info("✅ Thread default context matches self.context.")
            else:
                self.logger.warning("🚨 Thread default context does NOT match self.context.")

            # Step 2
            socket_path = "/tmp/testshm"
            if not os.path.exists(socket_path):
                self.logger.error(f"❌ Error: Socket path '{socket_path}' does not exist.")
                raise FileNotFoundError(f"Socket path '{socket_path}' does not exist.")

            pipeline_str = f"""
            shmsrc socket-path={socket_path} do-timestamp=true is-live=true !
            video/x-raw,format=I420,width=2304,height=1296,framerate=30/1 !
            videoconvert !
            pngenc snapshot=true !
            filesink location={self.imagename}
            """

            self.pipeline = Gst.parse_launch(pipeline_str)

            # Watch for bus messages to stop cleanly
            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self.on_message)

            self.pipeline.set_state(Gst.State.PLAYING)
            self.logger.info(f"Capturing Image to {self.imagename}...")

            # Run the main loop
            self.loop.run()
            self.logger.info("Main loop exited.")

        except Exception as e:
            self.logger.error(f"❌ Error in Camera_Recorder.run(): {e}")
            self.stop()
        finally:
            # Ensure cleanup happens
            self.context.pop_thread_default()
            self.stop()

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
        self.logger.info("Stopping the recorder gracefully...")

        self.context.push_thread_default()
        if GLib.MainContext.get_thread_default() == self.context:
            self.logger.info("✅ Thread default context matches self.context.")
        else:
            self.logger.warning("🚨 Thread default context does NOT match self.context.")

        def _shutdown():
            # Ensure we're running inside the correct GLib thread
            if GLib.MainContext.get_thread_default() == self.context:
                self.logger.info("🏠 Inside shutdown: correct thread context.")
            else:
                self.logger.warning("🚨 Inside shutdown: wrong thread context.")

            # Stop the pipeline safely
            if self.pipeline:
                self.logger.info("✅ Stopping GStreamer pipeline...")
                self.pipeline.set_state(Gst.State.NULL)
                self.pipeline = None
                self.logger.info("Recorder stopped.")

            # Quit the GLib loop
            if self.loop and self.loop.is_running():
                self.logger.info("🔁 Quitting main loop...")
                self.loop.quit()

            return False  # one-shot idle callback

        # Schedule shutdown on the correct context
        GLib.idle_add(_shutdown, context=self.context)

        # Poke the loop in case it's idle
        GLib.idle_add(lambda: None, context=self.context)

        # Upload can safely happen here in the current thread
        self.logger.info("✅ Gstreamer stop requested.")

        if self.UPLOAD_ON_FINISH and hasattr(self, 'imagename') and os.path.exists(self.imagename):
            self.logger.info(f"You may want to implement a upload for {self.imagename}...")

        return True

