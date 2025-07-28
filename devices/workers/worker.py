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

        self.health = Value("i", 0)  # Health status: 0=OK, 1=Warning, 2=Error

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

    def kill_device(self):
        if self.LETHAL:
            self.device.stop()
