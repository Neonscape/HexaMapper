from PyQt6.QtCore import QEvent
from modules.tools.base_tool import ToolBase

class ToolManager:
    def __init__(self, map_engine):
        self.map_engine = map_engine
        self.tools: dict[str, ToolBase] = {}
        self.active_tool: ToolBase | None = None

    def register_tool(self, name: str, tool: ToolBase):
        self.tools[name] = tool

    def set_active_tool(self, name: str):
        if self.active_tool:
            self.active_tool.deactivate()
        
        if name in self.tools:
            self.active_tool = self.tools[name]
            self.active_tool.activate()
        else:
            self.active_tool = None

    def handle_mouse_press(self, event: QEvent):
        if self.active_tool:
            self.active_tool.mouse_press(event)

    def handle_mouse_move(self, event: QEvent):
        if self.active_tool:
            self.active_tool.mouse_move(event)

    def handle_mouse_release(self, event: QEvent):
        if self.active_tool:
            self.active_tool.mouse_release(event)
