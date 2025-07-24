import signal
import sys
import pathlib
import zenoh
import time
import socket
import logging
import json

CONFIG_PATH = pathlib.Path.home() / "Herd_OS" / "device.cfg"
LOGGER_PATH = pathlib.Path.home() / "Herd_OS" / "logs.txt"
HOSTNAME = socket.gethostname()

IFF_PING_S = 1  # seconds between IFF pings

def setup_logger(name: str, logger_path: str = './logs.txt') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    fh = logging.FileHandler(logger_path)
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info('Service shutdown requested')
    sys.exit(0)

class IFF_Device_Prototype:  
    def __init__(self, config):
        self.device_id = config.get('device_id', 'unknown')
        self.name = config.get('device_name', 'Unnamed_IFF')
        self.hostname = HOSTNAME
        self.ip = self.check_ip()

    def listen(self):
        """Placeholder for listening logic"""
        logger.info(f"Listening on {self.ip}:{self.port}")

    def ping(self):
        ping_message = {
            "device_id": self.device_id,
            "name": self.name,
            "ip": self.ip,
            "hostname": self.hostname,
            "timestamp": time.time()
        }
        return ping_message

    def check_ip(self):
        try:
            # Create a dummy socket connection to determine the outbound interface
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))  # Doesn't actually send data
                ip = s.getsockname()[0]
            logger.info(f"📡 IP Self-Check: {ip}")
        except Exception as e:
            logger.warning(f"⚠️ IP Self-Check failed: {e}")
            ip = "0.0.0.0"
        return ip

#----------------------------------------------------
# Run
#----------------------------------------------------
# Set up logging
logger = setup_logger("IFF_service", LOGGER_PATH)

# Set up Zenoh 
config = zenoh.Config()
zenoh_client = zenoh.open(config)
pub = zenoh_client.declare_publisher('device/IFF')

# Set up signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Get device configuration
with open(CONFIG_PATH, 'r') as f:
    device_config = json.load(f)

device = IFF_Device_Prototype(device_config)

while True:
    ping = device.ping()
    pub.put(ping)
    logger.info(f"IFF Ping: {ping}")

    time.sleep(IFF_PING_S)  # Adjust the sleep time as needed