import logging

# ----------------------------------------
# Logger Setup
# ----------------------------------------
def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    fh = logging.FileHandler('./logs.txt')
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
