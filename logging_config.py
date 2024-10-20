import logging
import sys
import toml

# Load configuration from config.toml
with open('config.toml', 'r') as f:
    config = toml.load(f)

def setup_logging(console_level=logging.CRITICAL, file_level=logging.DEBUG, log_file='app.log'):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(threadName)s] - %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter('%(levelname)s - [%(threadName)s] - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler) 