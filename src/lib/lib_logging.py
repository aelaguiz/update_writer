import os
import sys
import json
import re
import dotenv
import logging
import prefect
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler
from rich.syntax import Syntax


dotenv.load_dotenv()

def set_console_logging_level(level):
    logging.getLogger().handlers[1].setLevel(level)

# Create a Rich console instance
console = Console()


def get_logger(level=logging.DEBUG):
    prefect_logger = prefect.logging.get_logger()
    prefect_logger.setLevel(level)

    return prefect_logger


def get_run_logger(level=logging.DEBUG):
    prefect_logger = prefect.logging.get_run_logger()
    prefect_logger.setLevel(level)

    return prefect_logger

# Configure logging
def setup_logging():
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Generate log file name
    script_name = os.path.basename(__file__).split('.')[0]
    args_safe = "_".join(re.sub(r'[^\w]', '', arg) for arg in sys.argv[1:])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/{script_name}_{args_safe}_{timestamp}.log"
    log_filename = f"logs/{script_name}.log"

    # Create loggers
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set the logger to debug level

    rich_handler = RichHandler(console=console, rich_tracebacks=True, markup=True)
    rich_handler.setLevel(logging.DEBUG)
    logger.addHandler(rich_handler)

    # Create file handler which logs even debug messages
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)

    # Create console handler with a higher log level
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.INFO)
    # ch_formatter = logging.Formatter('%(levelname)s - %(message)s')
    # ch.setFormatter(ch_formatter)
    # logger.addHandler(ch)
