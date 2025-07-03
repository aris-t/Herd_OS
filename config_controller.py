from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from multiprocessing import Process
import time, uuid, uvicorn

# ----------------------------------------
# 🧠 Config API
# ----------------------------------------

class DeviceConfig:
    def __init__(self):
        self.device_id = f"dev-{uuid.uuid4().hex[:6]}"
        self.boot_time = time.time()
        self.settings = {
            "name": "Camera-Node-1",
            "stream_fps": 30,
            "enabled": True,
            "camera_endpoint": "udp://192.168.1.88:6000"
        }

# ----------------------------------------
# 📦 Config REST server as a child process
# ----------------------------------------

def create_config_api(config: DeviceConfig):
    app = FastAPI(title="Device Config API")

    class ConfigUpdate(BaseModel):
        name: Optional[str]
        stream_fps: Optional[int]
        enabled: Optional[bool]
        camera_endpoint: Optional[str]

    @app.get("/status")
    def get_status():
        return {
            "device_id": config.device_id,
            "uptime_sec": round(time.time() - config.boot_time),
            "heartbeat_age": "OK",
            "config": config.settings
        }

    @app.get("/config")
    def get_config():
        return config.settings

    @app.post("/config")
    def update_config(cfg: ConfigUpdate):
        for key, value in cfg.dict(exclude_unset=True).items():
            config.settings[key] = value
        return {"message": "Updated", "config": config.settings}

    @app.post("/restart")
    def restart():
        print("Simulated restart.")
        return {"message": "Device restarting..."}

    @app.get("/logs")
    def get_logs():
        return {
            "recent": [
                "[INFO] Camera started",
                "[WARN] Frame drop detected",
                "[INFO] Config updated"
            ]
        }

    return app

class ConfigController(Process):
    def __init__(self, config: DeviceConfig):
        super().__init__()
        self.config = config

    def run(self):
        app = create_config_api(self.config)
        uvicorn.run(app, host="0.0.0.0", port=8000)

# ----------------------------------------
# 🧠 Device (your top-level controller)
# ----------------------------------------

class Device:
    def __init__(self):
        self.config = DeviceConfig()
        self.config_api = ConfigController(self.config)

    def start(self):
        self.config_api.start()
        print(f"[{self.config.device_id}] Device started")

    def stop(self):
        self.config_api.terminate()
        print(f"[{self.config.device_id}] Device stopped")

# ----------------------------------------
# Run
# ----------------------------------------

if __name__ == "__main__":
    dev = Device()
    dev.start()


#     from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
# from pathlib import Path

# app = FastAPI()

# # Serve React build
# react_build_path = Path(__file__).parent / "frontend" / "build"
# app.mount("/", StaticFiles(directory=react_build_path, html=True), name="react")
