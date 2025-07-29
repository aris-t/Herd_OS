import os
from datetime import datetime
from .device import Device

from multiprocessing import Value
import time

# # ----------------------------------------
# # Device
# # ----------------------------------------

class Master_Server(Device):
    def __init__(self, logger=None, DEBUG=False):
        super().__init__(logger=logger, DEBUG=DEBUG)

        # Control flags

        # Health Flags

        # TODO Need to include LETHAL flag for critical processes that fail to start
        self.processes = []

        self.commands = {}

    def __setup__(self):
        pass

    # Device Specific Methods

    ### Use Specific Methods for Camera Device
    # Trial Camera
    def start_trial(self, trial_name):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def stop_trial(self):
        self.logger.info("Trial stopped.")
        self.stop_recorder()
