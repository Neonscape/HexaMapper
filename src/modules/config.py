from schema import *
import yaml

is_config_loaded = False

app_config = ApplicationConfig()

config_path = "config/config.yml"

def load_config():
    global app_config
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            app_config = ApplicationConfig(**config)
            is_config_loaded = True
    except FileNotFoundError:
        logger.error(f"Config file not found at {config_path}! Factory defaults will be used.")
        app_config = ApplicationConfig()
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file at {config_path}! Factory defaults will be used: {e}")
        app_config = ApplicationConfig()
    
load_config()