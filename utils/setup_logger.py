import logging
from rich.logging import RichHandler

# ----------------------------------------
# Logger Setup
# ----------------------------------------
def setup_logger(name: str, logger_path: str = './logs.txt') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    # Replace StreamHandler with RichHandler for rich formatting in the console
    ch = RichHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler(logger_path)
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
