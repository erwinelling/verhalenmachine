import logging, logging.handlers
import os

HOME_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
print HOME_DIR
LOG_FILE = os.path.join(HOME_DIR, "verhalenmachine.log")

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    fh = logging.handlers.RotatingFileHandler(
                  LOG_FILE, maxBytes=5000000, backupCount=5)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
