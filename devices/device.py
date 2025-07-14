import time
import uuid
import socket
from pathlib import Path
import json

from .workers import IFF, Config_Controller
from utils.setup_logger import setup_logger

from multiprocessing import Manager, Lock, Value

CONFIG_PATH = Path("device.cfg")

class Device:
    def __init__(self, DEBUG=False):
        self.device_id = f"dev-{uuid.uuid4().hex[:6]}"
        self.logger = setup_logger(self.device_id)

        self.DEBUG = DEBUG  # Set to True for verbose logging during development
        self.boot_time = time.time()
        self.ip = self.check_ip()
        self.port = 5555

        # Control and health values
        self.is_stopped = Value('b', False)  # Shared flag to signal processes to stop
        self._initialized = False

        # Shared memory manager for inter-process communication
        self.manager = Manager()
        self.lock = Lock()
        self.shared_data = self.manager.dict({
            'device_name': "Device Template",
        })

        # Required base processes
        self._processes = [
            IFF(self, "IFF"),
            Config_Controller(self, "ConfigAPI"),
        ]

    def __setup__(self):
        self.logger.info("Setting up device...")

    @property
    def process_list(self):
        processes = getattr(self, "processes", [])
        if not isinstance(processes, list):
            raise TypeError("Child must define `processes` as a list.")
        return self._processes + processes

    def start(self):
        print(f"\n\nStarting {len(self.process_list)} processes...")
        for process in self.process_list:
            process.start()
        self.logger.info("Device started.")

    def stop(self):
        for process in self.process_list:
            self.is_stopped.value = True  # Signal processes to stop
            process.stop()
        self.logger.info("Device stopped.")

    # Logistics and Utility Methods

    def check_ip(self):
        try:
            # Create a dummy socket connection to determine the outbound interface
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))  # Doesn't actually send data
                ip = s.getsockname()[0]
            self.logger.info(f"📡 IP Self-Check: {ip}")
        except Exception as e:
            self.logger.warning(f"⚠️ IP Self-Check failed: {e}")
            ip = "0.0.0.0"
        return ip

    # Zenoh command managment

    # Device Lifecycle
    @property
    def name(self):
        """Get name from device.cfg JSON file"""
        with self.lock:
            try:
                if CONFIG_PATH.exists():
                    with CONFIG_PATH.open("r") as f:
                        data = json.load(f)
                        name = str(data.get("device_name", "unknown"))
                        return name
                else:
                    return "unknown"
            except Exception as e:
                self.logger.warning(f"Failed to get device name from device.cfg: {e}")
                return "unknown"
        
    @name.setter
    def name(self, value):
        """Safely update only the device_name property in device.cfg JSON file"""
        with self.lock:
            data = {}
            # Read existing config if it exists
            if CONFIG_PATH.exists():
                try:
                    with CONFIG_PATH.open("r") as f:
                        data = json.load(f)
                except Exception as e:
                    self.logger.warning(f"Failed to read device.cfg: {e}")
            old_name = data.get('device_name', 'unknown')
            # Only update the device_name property
            if data.get('device_name') != value:
                data['device_name'] = value
                try:
                    # Write back the updated config (preserving other keys)
                    with CONFIG_PATH.open("w") as f:
                        json.dump(data, f, indent=2)
                    self.logger.info(f"SETTER FIRED: Device renamed from '{old_name}' to '{value}'")
                except Exception as e:
                    self.logger.warning(f"Failed to write device.cfg: {e}")
                self._on_name_changed(old_name, value)
            else:
                self.logger.info("Device name unchanged; no write performed.")
    
    def _on_name_changed(self, old_name, new_name):
        """Called whenever name changes"""
        if self.DEBUG:
            self.logger.info(f"Name change event: {old_name} -> {new_name}")
