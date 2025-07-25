import logging
import os
from rich.logging import RichHandler

# ----------------------------------------
# Logger Setup
# ----------------------------------------
def setup_logger(name: str, logger_path: str = './logs.txt') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create formatter for file handler, including PID
    formatter = logging.Formatter('%(asctime)s %(levelname)s [PID:%(process)d] %(message)s')

    # File handler with traditional formatting
    fh = logging.FileHandler(logger_path)
    fh.setFormatter(formatter)

    # Console handler with Rich formatting, including PID in message
    class PIDRichHandler(RichHandler):
        def emit(self, record):
            record.msg = f"[PID:{record.process}] {record.msg}"
            super().emit(record)

    ch = PIDRichHandler(
        show_time=True,
        show_level=True,
        show_path=True,
        log_time_format="[%Y-%m-%d %H:%M:%S]"
    )

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger