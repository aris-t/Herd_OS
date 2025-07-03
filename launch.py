import multiprocessing
import signal
import sys
import time
import uuid
import os
from datetime import datetime

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gst, GObject, GLib

import zenoh
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
import uvicorn

from worker import Worker

#TODO
# Add rich logging for better log formatting and colorization

# ----------------------------------------
# Logger Setup
# ----------------------------------------
import logging

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    fh = logging.FileHandler('./logs.txt')
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger


# ----------------------------------------
# Signal Handling
# ----------------------------------------
devices = []

def signal_handler(sig, frame):
    logger = setup_logger("Main")
    logger.info("Ctrl+C detected. Ending all processes...")
    for device in devices:
        device.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


# ----------------------------------------
# IFF Broadcaster
# ----------------------------------------
class IFF(Worker):
    def __init__(self, device, name):
        super().__init__(name)
        self.device = device
        self.logger = setup_logger(name)

    def run(self):
        config = zenoh.Config()
        self.zenoh_client = zenoh.open(config)
        self.pub = self.zenoh_client.declare_publisher('global/IFF')

        while not self.is_stopped:
            ping = f"{self.device.device_id},{self.device.name}"
            self.pub.put(ping)
            self.logger.info(f"IFF Ping: {ping}")
            time.sleep(1)


# ----------------------------------------
# Camera Controller
# ----------------------------------------
Gst.init(None)

class Camera_Controller(Worker):
    def __init__(self, device, name, DEBUG=False):
        super().__init__(name)
        self.DEBUG = DEBUG
        self.device = device
        self.logger = setup_logger(name)
        self.multicast_ip = "239.255.12.42"
        self.port = 5555

    def broadcast_status(self, publisher):
        msg = f"udp://{self.multicast_ip}:{self.port}"
        self.logger.debug("Stream active")
        publisher.put(msg)
        return True

    def run(self):
        config = zenoh.Config()
        self.zenoh_client = zenoh.open(config)
        self.pub = self.zenoh_client.declare_publisher('camera/declare')

        pipeline_str = (
            "videotestsrc ! "
            "videoconvert ! "
            "video/x-raw,width=640,height=480,framerate=30/1 ! "
            "x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! "
            "rtph264pay config-interval=1 pt=96 ! "
            f"udpsink host={self.multicast_ip} port={self.port} auto-multicast=true"
        )

        if not self.DEBUG:
            pipeline = Gst.parse_launch(pipeline_str)
            pipeline.set_state(Gst.State.PLAYING)

            self.logger.info(f"Publishing stream to udp://{self.multicast_ip}:{self.port}")
            GLib.timeout_add(2000, self.broadcast_status, self.pub)

            try:
                loop = GObject.MainLoop()
                loop.run()
            except KeyboardInterrupt:
                self.logger.warning("Stopping camera stream...")
                pipeline.set_state(Gst.State.NULL)
        else:
            self.logger.debug(f"Debug Mode: Pipeline would be: {pipeline_str}")
            while not self.is_stopped:
                self.broadcast_status(self.pub)
                time.sleep(1)


# ----------------------------------------
# FastAPI Config Server
# ----------------------------------------
def create_config_api(device):
    logger = setup_logger("ConfigAPI")
    app = FastAPI(title="Device Config API")

    class ConfigUpdate(BaseModel):
        name: Optional[str]
        stream_fps: Optional[int]
        enabled: Optional[bool]
        camera_endpoint: Optional[str]

    @app.get("/status")
    def get_status():
        device_info = {
            "device_id": device.device_id,
            "name": device.name,
            "stream_fps": device.target_framerate,
            "camera_endpoint": device.camera_endpoint,
            "uptime_sec": round(time.time() - device.boot_time)
        }
        logger.info(f"Status: {device_info}")
        return device_info

    @app.get("/logs")
    def get_logs():
        logs = []
        try:
            with open("./logs.txt", "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(" ", 2)
                    if len(parts) == 3:
                        time_, level, msg = parts
                        logs.append({
                            "time": time_,
                            "level": level,
                            "msg": msg
                        })
            return JSONResponse(content=logs)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Log file not found.")

    @app.post("/restart")
    def restart():
        logger.info("Restart requested.")
        return {"message": "Device restarting..."}

    @app.post("/rename")
    def rename(cfg: ConfigUpdate):
        logger.info(f"Renaming to {cfg.name}")
        return {"message": "Device renaming..."}

    @app.post("/start_trial")
    def start_trial(cfg: ConfigUpdate):
        logger.info(f"Trial starting with config: {cfg}")
        return {"message": "Trial starting..."}

    @app.post("/stop_trial")
    def stop_trial():
        logger.info("Trial stop requested.")
        return {"message": "Trial stopped."}

    build_path = Path(__file__).parent / "frontend" / "build"
    if build_path.exists():
        app.mount("/", StaticFiles(directory=build_path, html=True), name="frontend")
    else:
        logger.warning("React frontend not found.")

    return app


class ConfigController(Worker):
    def __init__(self, device, name):
        super().__init__(name)
        self.device = device
        self.logger = setup_logger(name)

    def run(self):
        app = create_config_api(self.device)
        self.logger.info("Starting config API server...")
        uvicorn.run(app, host="0.0.0.0", port=8000)


# ----------------------------------------
# Device
# ----------------------------------------
class Camera:
    def __init__(self):
        self.device_id = f"dev-{uuid.uuid4().hex[:6]}"
        self.boot_time = time.time()
        self.ip = "0.0.0.0"
        self.name = "Camera-Node-1"
        
        self.multicast_ip = "239.255.12.42"
        self.port = 5555
        self.camera_endpoint = f"udp://{self.multicast_ip}:{self.port}"
        self.target_framerate = 30
        self.target_resolution = "1920x1080"
        self.target_bitrate = 4000
        self.logger = setup_logger("Device")

        self.processes = [
            IFF(self, "IFF"),
            ConfigController(self, "ConfigAPI"),
            Camera_Controller(self, "Camera", DEBUG=True)
        ]

    def __setup__(self):
        self.logger.info("Setting up device...")

    def start(self):
        for process in self.processes:
            process.start()
        self.logger.info("Device started.")

    def stop(self):
        for process in self.processes:
            process.stop()
        self.logger.info("Device stopped.")

    def start_trial(self, config=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trial_dir = os.path.join("trials", f"trial_{timestamp}")
        os.makedirs(trial_dir, exist_ok=True)

        if config:
            with open(os.path.join(trial_dir, "config.txt"), "w") as f:
                f.write(str(config))
        with open(os.path.join(trial_dir, "started.txt"), "w") as f:
            f.write(f"Trial started at {timestamp}\n")
        self.logger.info(f"Trial started at {trial_dir}")

    def stop_trial(self):
        self.logger.info("Trial stopped.")


# ----------------------------------------
# Launch
# ----------------------------------------
if __name__ == "__main__":
    devices = [Camera()]
    for device in devices:
        device.start()
