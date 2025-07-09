from pydantic import BaseModel
from colorzero import Color
from modules.config import app_config
from modules.tools.base_tool import ToolBase

class DrawToolSettings(BaseModel):
    radius: float = 1.0
    color: Color = app_config.hex_map_custom.default_cell_color
    
    


class DrawTool(ToolBase):
    def __init__(self, canvas: MapPanel):
        super().__init__(canvas)
        