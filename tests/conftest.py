import sys
import os
import pytest

# Add the 'src' directory to sys.path so that modules can be imported directly
# as if 'src' were the root of the project.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

@pytest.fixture(scope="session")
def app_config():
    """
    Fixture to load the application configuration.
    This can be used by tests that need access to the config.
    """
    from modules.config import load_config
    config = load_config()
    if not config:
        pytest.fail("Failed to load application configuration.")
    return config

# You can add more fixtures here as needed, e.g., for mock objects,
# database connections, or common setup/teardown.
