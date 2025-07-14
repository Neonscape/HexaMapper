from modules.tools.base_tool import ToolBase
from pydantic import BaseModel

class EraserToolSettings(BaseModel):
    radius: float = 1.0

class EraserTool(ToolBase):
    """
    A tool for erasing cells on the hex map.
    (Currently a placeholder).
    """
    def __init__(self, map_engine):
        super().__init__(map_engine)
        self.settings = EraserToolSettings()

    def get_visual_aid_info(self):
        return {
            "shape": "circle",
            "radius": self.settings.radius,
            "color": (1.0, 0.0, 0.0, 0.5) # Red for erase
        }
