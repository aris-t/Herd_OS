#!/usr/bin/python3
# TODO Make sure running as root user

import os
import struct
import smbus2
import time
import gpiod
import signal
import sys
import pathlib
from subprocess import call

import zenoh

from utils.setup_logger import setup_logger
logger = setup_logger("service_battery_monitor")

# Paths
CONFIG_PATH = pathlib.Path.home() / "Herd_OS" / "device.cfg"
LOGGER_PATH = pathlib.Path.home() / "Herd_OS" / "logs.txt"
HOSTNAME = os.uname().nodename

# User-configurable variables
SHUTDOWN_THRESHOLD = 3  # Number of consecutive failures required for shutdown
SLEEP_TIME = 60  # Time in seconds to wait between failure checks
AC_SHUTDOWN = False  # Whether to shutdown on AC power loss
ON_BATTERY = False  # Whether the system is currently on battery power
Loop = True  # Service runs continuously

config = zenoh.Config()
# Configure for local-only communication
config.insert_json5("scouting/multicast/enabled", "false")
config.insert_json5("scouting/gossip/enabled", "false")
config.insert_json5("listen/endpoints", '["tcp/127.0.0.1:0"]')  # Only listen on localhost
config.insert_json5("connect/endpoints", "[]")  # Don't connect to remote endpoints
zenoh_client = zenoh.open(config)
pub = zenoh_client.declare_publisher('local/battery')

def readVoltage(bus):
    read = bus.read_word_data(address, 2) # reads word data (16 bit)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0] # big endian to little endian
    voltage = swapped * 1.25 / 1000 / 16 # convert to understandable voltage
    return voltage

def readCapacity(bus):
    read = bus.read_word_data(address, 4) # reads word data (16 bit)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0] # big endian to little endian
    capacity = swapped / 256 # convert to 1-100% scale
    return capacity

def get_battery_status(voltage):
    if 3.87 <= voltage <= 4.2:
        return "Full"
    elif 3.7 <= voltage < 3.87:
        return "High"
    elif 3.55 <= voltage < 3.7:
        return "Medium"
    elif 3.4 <= voltage < 3.55:
        return "Low"
    elif voltage < 3.4:
        return "Critical"
    else:
        return "Unknown"

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info('Service shutdown requested')
    sys.exit(0)

# Set up signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    bus = smbus2.SMBus(1)
    address = 0x36
    PLD_PIN = 6
    chip = gpiod.Chip('gpiochip0') # since kernel release 6.6.45 you have to use 'gpiochip0' - before it was 'gpiochip4'
    pld_line = chip.get_line(PLD_PIN)
    pld_line.request(consumer="PLD", type=gpiod.LINE_REQ_DIR_IN)

    while True:
        failure_counter = 0

        battery_message = {
            "hostname": HOSTNAME,
            "voltage": readVoltage(bus),
            "capacity": readCapacity(bus),
            "status": get_battery_status(readVoltage(bus)),
            "ac_power": pld_line.get_value(),
            "failure_counter": 0
        }
        pub.put(battery_message)

        for _ in range(SHUTDOWN_THRESHOLD):
            ac_power_state = pld_line.get_value()
            voltage = readVoltage(bus)
            battery_status = get_battery_status(voltage)
            capacity = readCapacity(bus)
            logger.info(f"Capacity: {capacity:.2f}% ({battery_status}), AC Power State: {'Plugged in' if ac_power_state == 1 else 'Unplugged'}, Voltage: {voltage:.2f}V")
            
            if ac_power_state == 0:
                logger.warning("UPS is unplugged or AC power loss detected.")
                ON_BATTERY = True

                if AC_SHUTDOWN:
                    logger.warning("AC power loss shutdown TRUE, initiating shutdown.")
                    failure_counter += 1

                if capacity < 20:
                    logger.warning("Battery level critical.")
                    failure_counter += 1
                if voltage < 3.20:
                    logger.warning("Battery voltage critical.")
                    failure_counter += 1
            else:
                ON_BATTERY = False
                failure_counter = 0
                break

            if failure_counter < SHUTDOWN_THRESHOLD:
                time.sleep(SLEEP_TIME) 

        if failure_counter >= SHUTDOWN_THRESHOLD:
            shutdown_reason = ""
            if capacity < 20:
                shutdown_reason = "due to critical battery level."
            elif voltage < 3.20:
                shutdown_reason = "due to critical battery voltage."
            elif ac_power_state == 0:
                shutdown_reason = "due to AC power loss or UPS unplugged."

            shutdown_message = f"Critical condition met {shutdown_reason} Initiating shutdown."
            logger.critical(shutdown_message)
            call("sudo nohup shutdown -h now", shell=True)
        else:
            #logger.info("System operating within normal parameters. No action required.")
            if Loop:
                time.sleep(SLEEP_TIME)
            else:
                break  # Exit the main loop instead of calling exit(0)

except KeyboardInterrupt:
    logger.info("Service interrupted by user")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
finally:
    logger.info("Battery monitor service stopped")

