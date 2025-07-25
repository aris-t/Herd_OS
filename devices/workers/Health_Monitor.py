from .worker import Worker
import zenoh
import time


# ----------------------------------------
# Health Broadcaster
# ----------------------------------------
class Health_Monitor(Worker):
    def __init__(self, device, name, DEBUG=False, verbose=False):
        super().__init__(device, name)
        self.logger.info(f"Health INITIALIZED for device {self.device.device_id}")
        self.verbose = verbose

    def run(self):
        config = zenoh.Config()
        # Configure for local-only communication
        config.insert_json5("scouting/multicast/enabled", "false")
        config.insert_json5("scouting/gossip/enabled", "false")
        config.insert_json5("listen/endpoints", '["tcp/127.0.0.1:0"]')  # Only listen on localhost
        config.insert_json5("connect/endpoints", "[]")  # Don't connect to remote endpoints
        zenoh_client = zenoh.open(config)
        pub = zenoh_client.declare_publisher('local/health')

        self.logger.info("Health Publisher Running.")
        while not self.is_stopped.value:
            try:
                ping = f"{time.time()}, {self.device.device_id}, {self.device.name}, {self.device.ip}"
                pub.put(ping)
                if self.verbose:
                    self.logger.info(f"Health Ping: {ping}")
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Health Publisher Error: {e}")

    def kill(self):
        # If Health Conditions Fail Kill the Process
        self.logger.info("Health Monitor Stopping...")
        self.is_stopped.value = True
        # super().kill()
        self.logger.info("Health Monitor Stopped.")