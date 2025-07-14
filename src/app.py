import sys
from PyQt6.QtWidgets import QApplication, QToolBar
from PyQt6.QtCore import Qt
from widgets.main_window import MainAppWindow
from modules.map_engine import MapEngine2D
from modules.icon_manager import icon_manager
from modules.tool_manager import ToolManager, tool_manager # Import ToolManager class and instance
from modules.tools.draw_tool import DrawTool # Import DrawTool

app = QApplication(sys.argv)

# Initialize icons before creating the main window
icon_manager.init_icons()

engine = MapEngine2D()

# Set map_engine for the global tool_manager instance
tool_manager.map_engine = engine 

# Register tools
draw_tool = DrawTool(map_engine=engine)
tool_manager.register_tool("draw_tool", draw_tool)

window = MainAppWindow(engine, tool_manager) # Pass tool_manager to MainAppWindow

def startup_tasks():
    """
    Performs any tasks required at application startup.
    """
    pass

def shutdown_tasks():
    """
    Performs any tasks required at application shutdown.
    """
    pass

def run():
    """
    Runs the main application loop.
    """
    startup_tasks()
    sys.exit(app.exec())
    shutdown_tasks()
    
if __name__ == "__main__":
    run()
