import logging.config
import yaml

def get_logger(name):
    with open("config/logging.conf", "r") as f:
        logging.config.fileConfig(f)
    return logging.getLogger(name)