import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.style import Style

# Define SUCCESS level between INFO and WARNING
SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kwargs)

logging.Logger.success = success

def setup_logger(name: str, logger_path: str = './logs.txt') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(process)d] %(message)s')
    fh = logging.FileHandler(logger_path)
    fh.setFormatter(formatter)

    class PIDRichHandler(RichHandler):
        def emit(self, record):
            message = record.getMessage()
            record.message = f"[{record.process}]{message}"
            record.msg = record.message
            record.args = ()
            super().emit(record)

    ch = PIDRichHandler(
        markup=True,
        show_time=True,
        show_level=True,
        show_path=True,
        log_time_format="[%H:%M:%S]"
    )

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
