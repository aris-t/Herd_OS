import logging
from rich.logging import RichHandler

# ----------------------------------------
# Logger Setup
# ----------------------------------------
def setup_logger(name: str, logger_path: str = './logs.txt') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create formatter for file handler
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    # File handler with traditional formatting
    fh = logging.FileHandler(logger_path)
    fh.setFormatter(formatter)

    # Console handler with Rich formatting
    ch = RichHandler(
        show_time=True,
        show_level=True,
        show_path=True,
        log_time_format="[%Y-%m-%d %H:%M:%S]"
    )

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger