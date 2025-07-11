from loguru import logger
from typing import Any, Literal, Annotated
from pydantic import BaseModel, BeforeValidator
from utils.color import RGBAColor as Color

class ShaderConfig(BaseModel):
    """
    Configuration schema for a pair of vertex and fragment shaders.
    """
    vertex: str
    fragment: str

class BackgroundConfig(BaseModel):
    """
    Configuration schema for the application's background.
    Supports gradient or solid color backgrounds.
    """
    mode: Literal["gradient", "solid"] = "gradient"
    solid_color: Color = Color("#333333FF")
    grad_color_0: Color = Color("#495766FF")
    grad_color_1: Color = Color("#60656bFF")

class HexMapEngineConfig(BaseModel):
    """
    Configuration schema for the core hex map engine parameters.
    """
    chunk_size: int = 16
    data_dimensions: int = 4
    hex_radius: float = 1
    hex_height: float = 0.5
    
class HexMapCustomConfig(BaseModel):
    """
    Configuration schema for custom visual properties of the hex map.
    """
    outline_color: Color = Color("#9999996A")
    default_cell_color: Color = Color("#888888FF")
    outline_width: float = 2.0
    
class HexMapViewConfig(BaseModel):
    """
    Configuration schema for the hex map's view properties, such as zoom limits.
    """
    min_zoom: float = 0.01
    max_zoom: float = 5.0
    
class HexMapShaderConfig(BaseModel):
    """
    Configuration schema for paths to various hex map related shaders.
    """
    unit: ShaderConfig = ShaderConfig(vertex="src/shaders/hex/vsh.glsl", fragment="src/shaders/hex/fsh.glsl")
    background:ShaderConfig = ShaderConfig(vertex="src/shaders/background/vsh.glsl", fragment="src/shaders/background/fsh.glsl")
    cursor: ShaderConfig = ShaderConfig(vertex="src/shaders/cursor/vsh.glsl", fragment="src/shaders/cursor/fsh.glsl")
    

class ApplicationConfig(BaseModel):
    """
    The main application configuration schema, combining all sub-configurations.
    """
    background: BackgroundConfig = BackgroundConfig()
    hex_map_engine: HexMapEngineConfig = HexMapEngineConfig()
    hex_map_custom: HexMapCustomConfig = HexMapCustomConfig()
    hex_map_view: HexMapViewConfig = HexMapViewConfig()
    hex_map_shaders: HexMapShaderConfig = HexMapShaderConfig()
