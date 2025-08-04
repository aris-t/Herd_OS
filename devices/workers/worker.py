from multiprocessing import Process, Value
import time

class Worker(Process):
    def __init__(self, device, name, DEBUG=False, LETHAL=False):
        super().__init__()
        self.device = device
        self.logger = device.logger

        self.DEBUG = DEBUG
        self.LETHAL = LETHAL
        
        self.name = name

        self.is_stopped = self.device.is_stopped

        self._health_ = Value("i", 0)  # Health status: 0=OK, 1=Warning, 2=Error

    def run(self):
        while not self.is_stopped.value:
            time.sleep(1)
            self.logger.info(f"Process {self.name} is running")

    def stop(self):
        if not self.is_stopped.value:
            self.is_stopped.value = True

        self.logger.info(f"[{self.device.device_id}][{self.name}] Stopping ...")
        
        time.sleep(1)  # Give some time for the process to stop gracefully
        self.terminate()
        self.logger.info(f"Process {self.name} has ended")

    def get_health_values(self):
        health_values = {
            k: v
            for k, v in vars(self).items()
            if k.startswith('_health_')
        }
        self.logger.info(f"Health Values for {self.name}:")
        for key, value in health_values.items():
            # Handle Synchronized wrapper types (multiprocessing.Value, etc.)
            if hasattr(value, "value"):
                self.logger.info(f"{key}: {value.value}")
            else:
                self.logger.info(f"{key}: {value}")
        return health_values

    def kill_device(self):
        if self.LETHAL:
            self.device.stop()
