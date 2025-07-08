from .worker import Worker
import zenoh
import time

# ----------------------------------------
# IFF Broadcaster
# ----------------------------------------
class IFF(Worker):
    def __init__(self, device, name):
        super().__init__(device, name)
        self.logger.info(f"IFF INITIALIZED for device {self.device.device_id}")

    def run(self):
        config = zenoh.Config()
        self.zenoh_client = zenoh.open(config)
        self.pub = self.zenoh_client.declare_publisher('global/IFF')

        self.logger.info("IFF Publisher Running.")
        while not self.is_stopped.value:
            ping = f"{time.time()}, {self.device.device_id}, {self.device.name}, {self.device.ip}"
            self.pub.put(ping)
            self.logger.info(f"IFF Ping: {ping}")
            time.sleep(1)