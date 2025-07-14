from modules.schema import *
from loguru import logger
import yaml

app_config = ApplicationConfig()

config_path = "config/config.yml"

def load_config():
    """
    Loads the application configuration from a YAML file.
    If the file is not found or parsing fails, default configuration values are used.
    """
    global app_config
    logger.info(f"Loading config from {config_path}...")
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            app_config = ApplicationConfig(**config)
    except FileNotFoundError:
        logger.error(f"Config file not found at {config_path}! Factory defaults will be used.")
        app_config = ApplicationConfig()
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file at {config_path}! Factory defaults will be used: {e}")
        app_config = ApplicationConfig()
    
load_config()
