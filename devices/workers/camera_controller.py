import time
import os
import threading
from contextlib import contextmanager

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GObject, GLib, GstRtspServer

import zenoh
from .worker import Worker

Gst.init(None)

class Camera_Controller(Worker):
    def __init__(self, device, name, DEBUG=False):
        super().__init__(device, name)
        self.DEBUG = DEBUG
        self.device = device
        self.port = 8554

        self.pipeline = None
        self.main_loop = None
        self.zenoh_client = None
        self.pub = None
        self.rtsp_server = None
        
        self.main_loop_thread = None
        self.output_file = None
        self._setup_lock = threading.Lock()
        self.logger.info("Camera controller initialized with RTSP + record + display")

    def broadcast_status(self, publisher):
        """Broadcast the RTSP stream URL periodically"""
        if self.is_stopped.value:
            return False  # Stop the timeout
        
        stream_uri = f"rtsp://{self.device.ip}:{self.port}/stream"
        self.logger.debug(f"Broadcasting RTSP stream URL: {stream_uri}")
        try:
            publisher.put(stream_uri)
        except Exception as e:
            self.logger.error(f"Failed to broadcast status: {e}")
        return True  # Continue the timeout

    def _setup_zenoh(self):
        """Initialize Zenoh client and publisher"""
        config = zenoh.Config()
        self.zenoh_client = zenoh.open(config)
        self.pub = self.zenoh_client.declare_publisher('camera/declare')
        self.logger.info("Zenoh client initialized")

    def _setup_output_file(self):
        """Create output directory and file path"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        trials_dir = os.path.join(base_dir, "trials")
        os.makedirs(trials_dir, exist_ok=True)
        self.output_file = os.path.join(trials_dir, f"output_{time.time()}.mkv")
        self.logger.info(f"Output file will be: {self.output_file}")

    def _setup_rtsp_server(self):
        """Setup RTSP server with proper pipeline"""
        source = "videotestsrc pattern=ball" if self.DEBUG else "v4l2src"
        
        rtsp_pipeline = (
            f"{source} ! videoconvert ! x264enc tune=zerolatency bitrate=500 speed-preset=ultrafast ! "
            "rtph264pay name=pay0 pt=96"
        )

        factory = GstRtspServer.RTSPMediaFactory()
        factory.set_launch(rtsp_pipeline)
        factory.set_shared(True)

        self.rtsp_server = GstRtspServer.RTSPServer()
        self.rtsp_server.set_service(str(self.port))
        
        mounts = self.rtsp_server.get_mount_points()
        mounts.add_factory("/stream", factory)

        if not self.rtsp_server.attach(None):
            raise RuntimeError("Failed to attach RTSP server")
        
        self.logger.info(f"RTSP server attached on port {self.port}")

    def _setup_local_pipeline(self):
        """Setup local recording and display pipeline"""
        source = "videotestsrc pattern=ball" if self.DEBUG else "v4l2src"
        
        pipeline_str = (
            f"{source} ! tee name=t "
            "t. ! queue ! videoconvert ! autovideosink sync=false "
            f"t. ! queue ! videoconvert ! x264enc tune=zerolatency bitrate=500 speed-preset=ultrafast ! "
            f"h264parse ! matroskamux ! filesink location={self.output_file} async=false sync=false"
        )

        self.pipeline = Gst.parse_launch(pipeline_str)
        if not self.pipeline:
            raise RuntimeError("Failed to create pipeline")

        # Setup bus message handling
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_bus_message)
        
        self.logger.info("Local pipeline created")

    def _on_bus_message(self, bus, message):
        """Handle GStreamer bus messages"""
        msg_type = message.type
        
        if msg_type == Gst.MessageType.EOS:
            self.logger.info("End of stream received")
            self._stop_main_loop()
            
        elif msg_type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            self.logger.error(f"Pipeline error from {message.src.get_name()}: {err}")
            if debug:
                self.logger.error(f"Debug info: {debug}")
            self._stop_main_loop()
            
        elif msg_type == Gst.MessageType.STATE_CHANGED:
            if message.src == self.pipeline:
                old_state, new_state, pending = message.parse_state_changed()
                self.logger.debug(f"Pipeline state changed from {old_state.value_nick} to {new_state.value_nick}")
                
        elif msg_type == Gst.MessageType.WARNING:
            warn, debug = message.parse_warning()
            self.logger.warning(f"Pipeline warning: {warn}")
            
        return True

    def _stop_main_loop(self):
        """Safely stop the main loop"""
        if self.main_loop and self.main_loop.is_running():
            self.main_loop.quit()

    def _main_loop_thread_func(self):
        """Run the GLib main loop in a separate thread"""
        self.main_loop = GLib.MainLoop()
        
        # Start broadcasting status
        GLib.timeout_add(2000, self.broadcast_status, self.pub)
        
        self.logger.info("Starting GLib main loop")
        try:
            self.main_loop.run()
        except Exception as e:
            self.logger.error(f"Main loop error: {e}")
        finally:
            self.logger.info("Main loop stopped")

    @contextmanager
    def _pipeline_context(self):
        """Context manager for pipeline state management"""
        try:
            # Start pipeline
            ret = self.pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                raise RuntimeError("Failed to start pipeline")
            
            self.logger.info("Pipeline started successfully")
            yield
            
        finally:
            # Clean shutdown
            if self.pipeline:
                self.logger.info("Stopping pipeline...")
                self.pipeline.send_event(Gst.Event.new_eos())
                
                # Wait for EOS with timeout
                bus = self.pipeline.get_bus()
                msg = bus.timed_pop_filtered(
                    Gst.SECOND * 5,
                    Gst.MessageType.EOS | Gst.MessageType.ERROR
                )
                
                if msg:
                    if msg.type == Gst.MessageType.ERROR:
                        err, debug = msg.parse_error()
                        self.logger.error(f"Error during shutdown: {err}")
                
                self.pipeline.set_state(Gst.State.NULL)
                self.logger.info("Pipeline stopped")

    def cleanup(self):
        """Clean up all resources"""
        with self._setup_lock:
            # Stop main loop
            if self.main_loop_thread and self.main_loop_thread.is_alive():
                self._stop_main_loop()
                self.main_loop_thread.join(timeout=5)
                if self.main_loop_thread.is_alive():
                    self.logger.warning("Main loop thread did not stop gracefully")

            # Clean up Zenoh
            if self.pub:
                self.pub.undeclare()
                self.pub = None
            if self.zenoh_client:
                self.zenoh_client.close()
                self.zenoh_client = None

            # RTSP server cleanup is automatic when process ends
            self.rtsp_server = None
            
            self.logger.info("Cleanup completed")



    def run(self):
        try:
            with self._setup_lock:
                # Setup all components
                self._setup_zenoh()
                self._setup_output_file()
                self._setup_rtsp_server()
                self._setup_local_pipeline()

                # Start the main loop in a separate thread
                self.main_loop_thread = threading.Thread(
                    target=self._main_loop_thread_func,
                    daemon=True
                )
                self.main_loop_thread.start()

            # Run pipeline in context manager
            with self._pipeline_context():
                self.logger.info(f"RTSP server running at rtsp://{self.device.ip}:{self.port}/stream")
                self.logger.info(f"Recording to: {self.output_file}")
                
                # Main monitoring loop
                while not self.is_stopped.value:
                    time.sleep(1)
                    
                    # Check if main loop thread died
                    if not self.main_loop_thread.is_alive():
                        self.logger.error("Main loop thread died unexpectedly")
                        break
                        
                    # Optional: Check if file is being written
                    if self.output_file and os.path.exists(self.output_file):
                        size = os.path.getsize(self.output_file)
                        if size > 0:
                            self.logger.debug(f"Recording file size: {size} bytes")

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Fatal error in camera controller: {e}")
            raise
        finally:
            self.cleanup()

    def __del__(self):
        """Ensure cleanup on deletion"""
        self.cleanup()