from loguru import logger
from typing import Any, Literal, Annotated
from pydantic import BaseModel, BeforeValidator
from colorzero import Color
import yaml

def validate_color(v: Any) -> Color:
    if isinstance(v, Color):
        return v
    if isinstance(v, str):
        try:
            return Color(v)
        except ValueError:
            raise ValueError(f"Invalid color: {v}")
    
    # TODO: Add support for other color formats, such as lists, etc.
    
    raise ValueError(f"Color must be a `colorzero.Color` object or a color string, not {type(v)}: {v}")

ParsedColor = Annotated[Color, BeforeValidator(validate_color)]

class BackgroundConfig(BaseModel):
    mode: Literal["gradient", "solid"] = "gradient"
    solid_color: ParsedColor = Color("#333333FF")
    grad_color_0: ParsedColor = Color("#495766FF")
    grad_color_1: ParsedColor = Color("#60656bFF")

class HexMapEngineConfig(BaseModel):
    chunk_size: int = 16
    data_dimensions: int = 4
    hex_radius: float = 1
    hex_height: float = 0.5
    
class HexMapCustomConfig(BaseModel):
    outline_color: ParsedColor = Color("#9999996A")
    default_cell_color: ParsedColor = Color("#888888FF")
    outline_width: float = 2.0
    
class HexMapViewConfig(BaseModel):
    min_zoom: float = 0.01
    max_zoom: float = 5.0
    

class ApplicationConfig(BaseModel):
    background: BackgroundConfig = BackgroundConfig()
    hex_map_engine: HexMapEngineConfig = HexMapEngineConfig()
    hex_map_custom: HexMapCustomConfig = HexMapCustomConfig()
    hex_map_view: HexMapViewConfig = HexMapViewConfig()
    
