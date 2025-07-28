from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from typing import List, Optional

from pathlib import Path
from datetime import datetime
import time
import uvicorn
import psutil
import os
import json
import threading

from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from . import Worker

# ----------------------------------------
# Pydantic models
# ----------------------------------------
class DeviceRename(BaseModel):
    name: str

class VideoSettings(BaseModel):
    resolution: str
    framerate: str

class DeviceStatus(BaseModel):
    device_id: str
    name: str
    ip: str
    stream_fps: int
    uptime_sec: int
    camera_endpoint: Optional[str] = None
    build_path: Optional[str] = None

class LogEntry(BaseModel):
    time: str
    level: str
    msg: str
    error: Optional[str] = None
    raw: Optional[str] = None

class FileEntry(BaseModel):
    name: str
    size: Optional[str] = None
    modified: Optional[str] = None


# ----------------------------------------
# Functions
# ----------------------------------------
# Helper function to determine health status
def get_health_status(cpu_usage, memory_percent, temperature):
    """Determine overall health status based on metrics"""
    if cpu_usage > 80 or memory_percent > 85 or temperature > 80:
        return "Critical"
    elif cpu_usage > 60 or memory_percent > 75 or temperature > 70:
        return "Warning"
    else:
        return "Good"
    
# ----------------------------------------
# Sample Data
# ----------------------------------------
# In-memory storage (replace with actual database/file storage)
device_config = {
    "device_id": "DEV001",
    "name": "Camera Device 01",
    "stream_fps": 30,
    "camera_endpoint": "http://192.168.1.100:8080/stream",
    "start_time": time.time()
}

# Sample log entries
sample_logs = [
    {
        "time": "2025-01-21 10:30:15",
        "level": "INFO",
        "msg": "Device started successfully"
    },
    {
        "time": "2025-01-21 10:30:20",
        "level": "INFO",
        "msg": "Camera endpoint configured"
    },
    {
        "time": "2025-01-21 10:31:00",
        "level": "WARN",
        "msg": "Memory usage above 75%"
    },
    {
        "time": "2025-01-21 10:32:15",
        "level": "ERROR",
        "msg": "Network connection timeout",
        "error": "Connection timeout after 30 seconds"
    }
]

# Sample file entries
sample_files = [
    {
        "name": "config.json",
        "size": "2.1 KB",
        "modified": "2025-01-21 09:15:30"
    },
    {
        "name": "device_logs.txt",
        "size": "45.7 KB",
        "modified": "2025-01-21 10:32:15"
    },
    {
        "name": "video_stream.mp4",
        "size": "1.2 GB",
        "modified": "2025-01-21 10:30:00"
    },
    {
        "name": "settings.ini",
        "size": "512 B",
        "modified": "2025-01-20 16:45:22"
    }
]

# ----------------------------------------
# FastAPI Config Server
# ----------------------------------------
def create_config_api(device, build_path: Path):
    app = FastAPI(
        title="Device Configuration API",
        description="API for device configuration and monitoring",
        version="1.0.0"
    )

    # CORS middleware to allow React frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    ### Static Files for React Frontend
    app.mount("/static", StaticFiles(directory=build_path / "static"), name="static")

    @app.get("/")
    async def serve_root():
        return FileResponse(build_path / "index.html")

    ### Device Status Info and Health Endpoints
    @app.get("/status", response_model=DeviceStatus)
    async def get_status():
        """Get device status"""
        try:
            uptime = int(time.time() - device_config["start_time"])
            
            return DeviceStatus(
                device_id=device.device_id,
                name=device.name,
                ip=device.ip,
                stream_fps=device.target_framerate,
                uptime_sec=round(time.time() - device.boot_time),
                camera_endpoint=device.camera_endpoint,
                build_path=str(build_path),
            )
        except Exception as e:
            device.logger.error(f"Error getting status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get device status")
        
    @app.get("/health")
    async def get_health():
        """Get device health metrics"""
        try:
            # Get real system metrics using psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get temperature (may not work on all systems)
            temperature = 68  # Default/simulated value
            try:
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        # Get first available temperature sensor
                        for name, entries in temps.items():
                            if entries:
                                temperature = entries[0].current
                                break
            except:
                pass
            
            return {
                "cpu_usage": round(cpu_percent, 1),
                "memory_usage": {
                    "used_gb": round(memory.used / (1024**3), 1),
                    "total_gb": round(memory.total / (1024**3), 1),
                    "percent": round(memory.percent, 1)
                },
                "temperature": temperature,
                "disk_usage": {
                    "used_gb": round(disk.used / (1024**3), 1),
                    "total_gb": round(disk.total / (1024**3), 1),
                    "percent": round((disk.used / disk.total) * 100, 1)
                },
                "network_status": "Connected",
                "overall_status": get_health_status(cpu_percent, memory.percent, temperature),
                "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            device.logger.error(f"Error getting health metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to get health metrics")

    @app.get("/info")
    async def get_info():
        """Get additional device information"""
        try:
            return {
                "api_version": "1.0.0",
                "device_type": "Camera Device",
                "firmware_version": "1.2.3",
                "last_boot": datetime.fromtimestamp(device_config["start_time"]).strftime("%Y-%m-%d %H:%M:%S"),
                "supported_resolutions": [
                    "640x480",
                    "1280x720", 
                    "1920x1080",
                    "2560x1440",
                    "3840x2160"
                ],
                "supported_framerates": [15, 24, 30, 60, 120]
            }
        except Exception as e:
            device.logger.error(f"Error getting device info: {e}")
            raise HTTPException(status_code=500, detail="Failed to get device info")

    ### Device Control Endpoints
    @app.post("/restart")
    async def restart_device():
        """Restart the device"""
        try:
            device.logger.info("Device restart requested")
            # Here you would implement actual device restart logic
            # For simulation, we'll just reset the start time
            device_config["start_time"] = time.time()
            return {"message": "Device restart initiated"}
        except Exception as e:
            device.logger.error(f"Error restarting device: {e}")
            raise HTTPException(status_code=500, detail="Failed to restart device")

    ### Device Life Cycle Endpoints
    @app.post("/rename")
    async def rename_device(rename_data: DeviceRename):
        """Rename the device"""
        try:
            device_config["name"] = rename_data.name
            device.logger.info(f"Device renamed to: {rename_data.name}")
            return {"message": "Device renamed successfully", "name": rename_data.name}
        except Exception as e:
            device.logger.error(f"Error renaming device: {e}")
            raise HTTPException(status_code=500, detail="Failed to rename device")

    @app.post("/video-settings")
    async def update_video_settings(video_settings: VideoSettings):
        """Update video settings"""
        try:
            # Here you would typically update the actual video stream settings
            # For now, we'll just log the settings
            device.logger.info(f"Video settings updated: {video_settings.resolution} @ {video_settings.framerate} FPS")

            # Update stream FPS in device config if provided
            try:
                device_config["stream_fps"] = int(video_settings.framerate)
            except ValueError:
                pass
                
            return {
                "message": "Video settings updated successfully",
                "resolution": video_settings.resolution,
                "framerate": video_settings.framerate
            }
        except Exception as e:
            device.logger.error(f"Error updating video settings: {e}")
            raise HTTPException(status_code=500, detail="Failed to update video settings")

    ### File and Log Endpoints
    @app.get("/files", response_model=List[FileEntry])
    async def get_files():
        """List all files in TARGET_DIR with FileEntry fields"""
        try:
            TARGET_DIR = Path("./trials")
            files = []
            if TARGET_DIR.exists() and TARGET_DIR.is_dir():
                for file in TARGET_DIR.iterdir():
                    if file.is_file():
                        stat = file.stat()
                        size = f"{stat.st_size / 1024:.1f} KB" if stat.st_size < 1024**2 else f"{stat.st_size / (1024**2):.1f} MB" if stat.st_size < 1024**3 else f"{stat.st_size / (1024**3):.1f} GB"
                        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                        files.append(FileEntry(
                            name=file.name,
                            size=size,
                            modified=modified
                        ))
            return files
        except Exception as e:
            device.logger.error(f"Error getting files: {e}")
            raise HTTPException(status_code=500, detail="Failed to get files")

    # Invalid Format    
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

    return app

class Config_Controller(Worker):
    def __init__(self, device, name):
        super().__init__(device, name)
        self.device = device
        self.logger = device.logger
        self.build_path = Path(__file__).parent.parent.parent / "frontend" / "build"
        self.server = None
        self.server_thread = None

    def run(self):
        app = create_config_api(self.device, self.build_path)

        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        self.server = uvicorn.Server(config)

        def serve():
            self.logger.info("Starting config API server...")
            self.server.run()  # Blocking, but in thread

        self.server_thread = threading.Thread(target=serve)
        self.server_thread.start()

        # Main loop just waits for stop flag
        while not self.device.is_stopped.value:
            time.sleep(0.5)

        self.stop()

    def stop(self):
        self.is_stopped.value = True

        if self.server and not self.server.should_exit:
            self.logger.info("Stopping config API server...")
            self.server.should_exit = True

        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=5)
            self.logger.info("Config API server stopped.")

# ----------------------------------------

#     from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
# from pathlib import Path

# app = FastAPI()

# # Serve React build
# react_build_path = Path(__file__).parent / "frontend" / "build"
# app.mount("/", StaticFiles(directory=react_build_path, html=True), name="react")