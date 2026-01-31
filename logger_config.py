import logging
import sys


class OnlyInfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO

def setup_logger():
    logger = logging.getLogger("BOT_LOG")
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    actions_handler = logging.FileHandler("actions.log", encoding='utf-8')
    actions_handler.setLevel(logging.INFO)
    actions_handler.addFilter(OnlyInfoFilter())
    actions_handler.setFormatter(formatter)

    errors_handler = logging.FileHandler("errors.log", encoding='utf-8')
    errors_handler.setLevel(logging.WARNING)
    errors_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(actions_handler)
        logger.addHandler(errors_handler)
        logger.addHandler(console_handler)

    logging.getLogger("aiogram").setLevel(logging.ERROR)
    logging.getLogger("apscheduler").setLevel(logging.ERROR)

    return logger

logger = setup_logger()