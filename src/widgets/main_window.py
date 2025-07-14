from PyQt6.QtWidgets import (
    QWidget, QMainWindow, QLayout, QHBoxLayout, QMenuBar, QStatusBar
)
from PyQt6.QtGui import QAction, QKeySequence
from widgets.map_panel import MapPanel2D
from widgets.toolbar import CustomToolbar
from modules.map_engine import MapEngine2D
from modules.tool_manager import ToolManager
from modules.icon_manager import IconManager

class MainAppWindow(QMainWindow):
    def __init__(self, engine: MapEngine2D, tool_manager: ToolManager, icon_manager: IconManager, title: str ="HexaMapper", size: tuple[int, int] = (1200, 800)):
        super().__init__()
        self.engine = engine
        self.tool_manager = tool_manager
        self.icon_manager = icon_manager

        self.map_panel: MapPanel2D | None = None
        
        self.setWindowTitle(title)
        self.resize(size[0], size[1])
        self._init_ui()

    def get_map_panel(self) -> MapPanel2D:
        return self.map_panel
        
    def _init_ui(self):
        # --- Menu Bar ---
        menu_bar = self.menuBar()
        edit_menu = menu_bar.addMenu("Edit")
        
        undo_action = QAction(self.icon_manager.get_icon("undo"), "Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction(self.icon_manager.get_icon("redo"), "Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        # --- Status Bar ---
        self.statusBar()
        
        # --- Toolbar ---
        toolbar = CustomToolbar("Tools", self.icon_manager)
        self.addToolBar(toolbar)

        # Register tools to the toolbar
        toolbar.register_tool_btn(
            name="draw",
            tooltip="Draw Tool",
            callback=lambda: self.tool_manager.set_active_tool("draw")
        )
        toolbar.register_tool_btn(
            name="erase",
            tooltip="Eraser Tool",
            callback=lambda: self.tool_manager.set_active_tool("erase")
        )
        
        # --- Central Widget ---
        container = QWidget(self)
        layout = QHBoxLayout(container)
        self.setCentralWidget(container)
        
        self.map_panel = MapPanel2D(self.engine, container)
        layout.addWidget(self.map_panel)

    def undo(self):
        self.engine.history_manager.undo()
        self.map_panel.update()

    def redo(self):
        self.engine.history_manager.redo()
        self.map_panel.update()
