import logging
import sys

class ColoredFormatter(logging.Formatter):
    # ANSI escape color codes
    TIME_COLOR = "\x1b[36m"     # Cyan
    NAME_COLOR = "\x1b[34m"     # Blue
    RESET = "\x1b[0m"
    
    LEVEL_COLORS = {
        logging.DEBUG: "\x1b[35m",     # Magenta
        logging.INFO: "\x1b[32m",      # Green
        logging.WARNING: "\x1b[33m",   # Yellow
        logging.ERROR: "\x1b[31m",     # Red
        logging.CRITICAL: "\x1b[1;31m" # Bold Red
    }
    
    def format(self, record):
        # Get color for the log level
        lvl_color = self.LEVEL_COLORS.get(record.levelno, self.RESET)
        
        # Save original values
        orig_asctime = getattr(record, "asctime", None)
        orig_levelname = record.levelname
        orig_name = record.name
        
        # Format properties with color codes
        record.asctime = f"{self.TIME_COLOR}{self.formatTime(record, self.datefmt)}{self.RESET}"
        record.levelname = f"{lvl_color}{record.levelname:<8}{self.RESET}"
        record.name = f"{self.NAME_COLOR}{record.name}{self.RESET}"
        
        # Format message
        result = super().format(record)
        
        # Restore values to prevent side-effects
        if orig_asctime is not None:
            record.asctime = orig_asctime
        record.levelname = orig_levelname
        record.name = orig_name
        
        return result

def setup_logging():
    """
    Configures the standard Python logging library with colored output.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s"))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Reset existing handlers to prevent duplicates and force custom format
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    
    # Configure framework logging levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("google").setLevel(logging.WARNING)

setup_logging()

