import logging
from rich.logging import RichHandler

# ----------------------------------------
# Logger Setup
# ----------------------------------------
def setup_logger(name: str, logger_path: str = './logs.txt') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # File formatter (no color)
    formatter = logging.Formatter('[PID:%(process)d] %(message)s')
    fh = logging.FileHandler(logger_path)
    fh.setFormatter(formatter)

    class PIDRichHandler(RichHandler):
        def emit(self, record):
            # Format message for rich console output with markup
            message = record.getMessage()
            record.message = f"[PID:[cyan]{record.process}[/cyan]] {message}"
            record.msg = record.message
            record.args = ()
            super().emit(record)

    ch = PIDRichHandler(
        markup=True,
        show_time=True,
        show_level=True,
        show_path=True,
        log_time_format="[%Y-%m-%d %H:%M:%S]"
    )

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
