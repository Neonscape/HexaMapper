from loguru import logger
from typing import Any, Literal, Annotated
from pydantic import BaseModel, BeforeValidator
from utils.color import RGBAColor as Color

class ShaderConfig(BaseModel):
    vertex: str
    fragment: str

class BackgroundConfig(BaseModel):
    mode: Literal["gradient", "solid"] = "gradient"
    solid_color: Color = Color("#333333FF")
    grad_color_0: Color = Color("#495766FF")
    grad_color_1: Color = Color("#60656bFF")

class HexMapEngineConfig(BaseModel):
    chunk_size: int = 16
    data_dimensions: int = 4
    hex_radius: float = 1
    hex_height: float = 0.5
    
class HexMapCustomConfig(BaseModel):
    outline_color: Color = Color("#9999996A")
    default_cell_color: Color = Color("#888888FF")
    outline_width: float = 2.0
    
class HexMapViewConfig(BaseModel):
    min_zoom: float = 0.01
    max_zoom: float = 5.0
    
class HexMapShaderConfig(BaseModel):
    unit: ShaderConfig = ShaderConfig(vertex="src/shaders/hex/vsh.glsl", fragment="src/shaders/hex/fsh.glsl")
    background:ShaderConfig = ShaderConfig(vertex="src/shaders/background/vsh.glsl", fragment="src/shaders/background/fsh.glsl")
    

class ApplicationConfig(BaseModel):
    background: BackgroundConfig = BackgroundConfig()
    hex_map_engine: HexMapEngineConfig = HexMapEngineConfig()
    hex_map_custom: HexMapCustomConfig = HexMapCustomConfig()
    hex_map_view: HexMapViewConfig = HexMapViewConfig()
    hex_map_shaders: HexMapShaderConfig = HexMapShaderConfig()
    
