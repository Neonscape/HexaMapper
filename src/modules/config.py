from modules.schema import *
from loguru import logger
import yaml

config_path = "config/config.yml"

def load_config() -> ApplicationConfig | None:
    """
    Loads the application configuration from a YAML file.
    If the file is not found or parsing fails, returns None.
    """
    logger.info(f"Loading config from {config_path}...")
    try:
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
            return ApplicationConfig(**config_data)
    except FileNotFoundError:
        logger.error(f"Config file not found at {config_path}! Cannot start application.")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file at {config_path}! Cannot start application: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading config: {e}")
        return None
