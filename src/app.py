import sys
from PyQt6.QtWidgets import QApplication
from widgets.main_window import MainAppWindow
from modules.map_engine import MapEngine2D
from modules.icon_manager import IconManager
from modules.tool_manager import ToolManager
from modules.shader_manager import ShaderManager
from modules.history_manager import HistoryManager
from modules.chunk_engine import ChunkEngine
from modules.config import load_config
from modules.tools.draw_tool import DrawTool
from modules.tools.eraser_tool import EraserTool

def run():
    """
    Initializes and runs the main application.
    This function orchestrates the creation of all major components
    and injects dependencies where needed.
    """
    app = QApplication(sys.argv)

    # --- Configuration ---
    config = load_config()
    if not config:
        sys.exit(1) # Exit if config fails to load

    # --- Manager Initialization ---
    icon_manager = IconManager()
    shader_manager = ShaderManager()
    history_manager = HistoryManager()
    chunk_engine = ChunkEngine(config=config)
    
    # The map engine is a central component that needs several managers
    map_engine = MapEngine2D(
        config=config,
        chunk_engine=chunk_engine,
        history_manager=history_manager,
        shader_manager=shader_manager
    )
    
    # The tool manager needs the map engine to pass to tools
    tool_manager = ToolManager(map_engine=map_engine)
    map_engine.set_tool_manager(tool_manager)

    # --- Tool Registration ---
    # Tools are instantiated with a reference to the map engine
    draw_tool = DrawTool(map_engine)
    eraser_tool = EraserTool(map_engine)
    tool_manager.register_tool("draw", draw_tool)
    tool_manager.register_tool("erase", eraser_tool)
    tool_manager.set_active_tool("draw") # Set a default tool

    # --- UI Initialization ---
    # The main window needs access to various managers to wire up the UI
    window = MainAppWindow(
        engine=map_engine,
        tool_manager=tool_manager,
        icon_manager=icon_manager
    )

    # --- Final Steps ---
    # The map engine needs a reference to the map panel widget, which is created inside the main window.
    # This is a bit of a workaround for the circular dependency between engine and panel.
    map_engine.set_map_panel(window.get_map_panel())

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()
