import logging
from logging.handlers import RotatingFileHandler
import os
import dotenv
dotenv.load_dotenv()


def get_log_level():
    log_level_string = os.environ.get("LOG_LEVEL","DEBUG").upper()
    print(f" Log Level string : {log_level_string}")
    log_level = getattr(logging, log_level_string, logging.DEBUG)
    print(f" Log Level: {log_level}")
    return log_level

def get_logger(executing_script:str):
    
    os.umask(0o002)
    # Create a logger
    if(not executing_script):
        executing_script = __name__
        
    logger = logging.getLogger(executing_script)
    logger.setLevel(get_log_level())
    # Create a rotating file handler
    file_handler = RotatingFileHandler(os.environ.get("LOG_FILE","app.log"), maxBytes=1024*1024, backupCount=5)
    file_handler.setLevel(get_log_level())
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s')
    # Add the formatter to the file handler
    file_handler.setFormatter(formatter)
    # Add the file handler to the logger
    logger.addHandler(file_handler)
    return logger


