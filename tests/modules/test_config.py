import pytest
from unittest.mock import patch, mock_open
from modules.config import load_config
from modules.schema import ApplicationConfig

# Mock the get_resource_path to ensure consistent file path resolution
@patch("modules.config.get_resource_path", return_value="/mock/path/config.yml")
@patch("modules.config.config_path", "/mock/path/config.yml") # Patch the module-level variable
def test_load_config_success(mock_get_resource_path):
    """Test that load_config successfully loads a valid YAML file."""
    mock_yaml_content = """
    app_name: HexaMapper
    version: 1.0.0
    background:
        mode: gradient
        solid_color: "#333333FF"
        grad_color_0: "#495766FF"
        grad_color_1: "#60656bFF"
    hex_map_engine:
        chunk_size: 16
        data_dimensions: 4
        hex_radius: 1.0
        hex_height: 0.5
    hex_map_custom:
        outline_color: "#FFFFFFFF"
        default_cell_color: "#888888FF"
        outline_width: 2.0
    hex_map_view:
        min_zoom: 0.01
        max_zoom: 5.0
    hex_map_shaders:
        unit:
            vertex: "src/shaders/hex/vsh.glsl"
            fragment: "src/shaders/hex/fsh.glsl"
        background:
            vertex: "src/shaders/background/vsh.glsl"
            fragment: "src/shaders/background/fsh.glsl"
        cursor:
            vertex: "src/shaders/cursor/vsh.glsl"
            fragment: "src/shaders/cursor/fsh.glsl"
    """
    with patch("builtins.open", mock_open(read_data=mock_yaml_content)) as mock_file:
        config = load_config()
        assert isinstance(config, ApplicationConfig)
        assert config.app_name == "HexaMapper"
        assert config.hex_map_engine.chunk_size == 16
        mock_file.assert_called_once_with("/mock/path/config.yml", "r")

@patch("modules.config.get_resource_path", return_value="/mock/path/config.yml")
def test_load_config_file_not_found(mock_get_resource_path):
    """Test that load_config returns None when the config file is not found."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        config = load_config()
        assert config is None

@patch("modules.config.get_resource_path", return_value="/mock/path/config.yml")
def test_load_config_yaml_error(mock_get_resource_path):
    """Test that load_config returns None when there's a YAML parsing error."""
    mock_invalid_yaml_content = """
    app_name: HexaMapper
    invalid_key: [
    """ # Malformed YAML
    with patch("builtins.open", mock_open(read_data=mock_invalid_yaml_content)):
        config = load_config()
        assert config is None

@patch("modules.config.get_resource_path", return_value="/mock/path/config.yml")
def test_load_config_schema_validation_error(mock_get_resource_path):
    """Test that load_config returns None when config data doesn't match schema."""
    mock_invalid_schema_content = """
    app_name: HexaMapper
    version: 1.0.0
    hex_map_engine:
        chunk_size: "invalid_type" # This should cause a ValidationError
        data_dimensions: 4
    """
    with patch("builtins.open", mock_open(read_data=mock_invalid_schema_content)):
        config = load_config()
        assert config is None
