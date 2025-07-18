from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import time, uvicorn

from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from devices.workers.worker import Worker

# ----------------------------------------
# FastAPI Config Server
# ----------------------------------------
def create_config_api(device, build_path: Path):
    app = FastAPI(title="Device Config API")

    class ConfigUpdate(BaseModel):
        name: Optional[str] = None
        stream_fps: Optional[int] = None
        enabled: Optional[bool] = None
        camera_endpoint: Optional[str] = None

    # Informational Endpoints
    @app.get("/status")
    def get_status():
        device_info = {
            "device_id": device.device_id,
            "ip": device.ip,
            "name": device.name,
            "stream_fps": device.target_framerate,
            "camera_endpoint": device.camera_endpoint,
            "uptime_sec": round(time.time() - device.boot_time),
            "build_path": str(build_path),
        }
        device.logger.info(f"Status: {device_info}")
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
        
    @app.get("/files")
    def get_files():
        files = []
        base_dir = Path("./trials")
        for file in base_dir.glob("*.mkv"):
            files.append({"name": file.name, "size": file.stat().st_size})
        return {"files": files}

    # Control Endpoints
    @app.post("/restart")
    def restart():
        device.logger.info("Restart requested.")
        return {"message": "Device restarting..."}

    # Config Update Endpoints
    @app.post("/rename")
    def rename(cfg: ConfigUpdate):
        device.logger.info(f"Received payload: {cfg.model_dump()}")
        device.name = cfg.name
        return {"message": "Device renaming..."}
    

    # Trial Control Endpoints
    @app.post("/start_trial")
    def start_trial(cfg: ConfigUpdate):
        device.logger.info(f"Trial starting with config: {cfg}")
        return {"message": "Trial starting..."}

    @app.post("/stop_trial")
    def stop_trial():
        device.logger.info("Trial stop requested.")
        return {"message": "Trial stopped."}

    # Serve React frontend if available
    if build_path.exists():
        app.mount("/", StaticFiles(directory=build_path, html=True), name="frontend")
    else:
        device.logger.warning(f"React frontend not found: {build_path}")

    return app


class Config_Controller(Worker):
    def __init__(self, device, name):
        super().__init__(device, name)
        self.device = device
        self.logger = device.logger

        self.build_path = Path(__file__).parent.parent.parent / "frontend" / "build"

    def run(self):
        app = create_config_api(self.device, self.build_path)
        self.logger.info("Starting config API server...")
        uvicorn.run(app, host="0.0.0.0", port=8000)

# ----------------------------------------

#     from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
# from pathlib import Path

# app = FastAPI()

# # Serve React build
# react_build_path = Path(__file__).parent / "frontend" / "build"
# app.mount("/", StaticFiles(directory=react_build_path, html=True), name="react")