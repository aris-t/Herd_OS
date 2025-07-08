import multiprocessing
import time

class Worker(multiprocessing.Process):
    def __init__(self, device, name):
        super().__init__()
        self.device = device
        self.logger = device.logger
        
        self.name = name
        self.is_stopped = self.device.is_stopped

    def run(self):
        while not self.is_stopped:
            time.sleep(1)
            print(f"Process {self.name} is running")

    def stop(self):
        print(f"[{self.device_id}] Stopping ...")
        self.is_stopped = True
        time.sleep(1)  # Give some time for the process to stop gracefully
        self.terminate()
        print(f"Process {self.name} has ended")