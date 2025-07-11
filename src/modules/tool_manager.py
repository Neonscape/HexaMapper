from PyQt6.QtCore import QEvent
from modules.tools.base_tool import ToolBase

class ToolManager:
    """
    Manages the application's tools, allowing registration, activation,
    and dispatching of mouse events to the active tool.
    """
    def __init__(self, map_engine = None):
        """
        Initializes the ToolManager.

        :param map_engine: The MapEngine2D instance to interact with.
        :type map_engine: MapEngine2D, optional
        """
        self.map_engine = map_engine
        self.tools: dict[str, ToolBase] = {}
        self.active_tool: ToolBase | None = None

    def register_tool(self, name: str, tool: ToolBase):
        """
        Registers a tool with the manager.

        :param name: The unique name for the tool.
        :type name: str
        :param tool: The tool instance to register.
        :type tool: ToolBase
        """
        self.tools[name] = tool
        
    def get_active_tool(self):
        """
        Returns the currently active tool.

        :return: The active tool instance, or None if no tool is active.
        :rtype: ToolBase | None
        """
        return self.active_tool

    def set_active_tool(self, name: str):
        """
        Sets the active tool by its registered name. Deactivates the current tool
        and activates the new one.

        :param name: The name of the tool to activate.
        :type name: str
        """
        if self.active_tool:
            self.active_tool.deactivate()
        
        if name in self.tools:
            self.active_tool = self.tools[name]
            self.active_tool.activate()
        else:
            self.active_tool = None

    def handle_mouse_press(self, event: QEvent):
        """
        Dispatches a mouse press event to the active tool.

        :param event: The mouse press event.
        :type event: QEvent
        """
        if self.active_tool:
            self.active_tool.mouse_press(event)

    def handle_mouse_move(self, event: QEvent):
        """
        Dispatches a mouse move event to the active tool.

        :param event: The mouse move event.
        :type event: QEvent
        """
        if self.active_tool:
            self.active_tool.mouse_move(event)

    def handle_mouse_release(self, event: QEvent):
        """
        Dispatches a mouse release event to the active tool.

        :param event: The mouse release event.
        :type event: QEvent
        """
        if self.active_tool:
            self.active_tool.mouse_release(event)

tool_manager = ToolManager()
