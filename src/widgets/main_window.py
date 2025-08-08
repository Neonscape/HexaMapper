from qtpy.QtWidgets import (
    QWidget, QMainWindow, QHBoxLayout, QMessageBox, QFileDialog, QLabel
)
from qtpy.QtGui import QAction, QKeySequence
from modules.chunk_engine import ChunkEngine
from modules.file_manager import FileManager
from widgets.layer_panel import LayerPanel
from widgets.map_panel import MapPanel2D
from widgets.toolbar import CustomToolbar
from modules.map_engine import MapEngine2D
from modules.tool_manager import ToolManager
from modules.icon_manager import IconManager

class MainAppWindow(QMainWindow):
    def __init__(self, chunk_engine: ChunkEngine, map_engine: MapEngine2D, tool_manager: ToolManager, icon_manager: IconManager, file_manager: FileManager, title: str ="HexaMapper", size: tuple[int, int] = (1200, 800)):
        super().__init__()
        self.chunk_engine = chunk_engine
        self.map_engine = map_engine
        self.tool_manager = tool_manager
        self.icon_manager = icon_manager
        self.file_manager = file_manager

        self.map_panel: MapPanel2D | None = None
        self.fps_label: QLabel | None = None
        self.current_filepath: str | None = None
        
        self.setWindowTitle(title)
        self.resize(size[0], size[1])
        self._init_ui()

    def get_map_panel(self) -> MapPanel2D:
        return self.map_panel
        
    def _init_ui(self):
        # --- Menu Bar ---
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("File")
        
        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_map)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_map)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_map)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_map_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export as PNG...", self)
        export_action.triggered.connect(self.export_map)
        file_menu.addAction(export_action)
        
        # Edit Menu
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
        toolbar.register_tool(
            tool=self.tool_manager.get_tool("draw"),
            name="draw",
            tooltip="Draw Tool",
            callback=lambda: self.tool_manager.set_active_tool("draw")
        )
        toolbar.register_tool(
            tool=self.tool_manager.get_tool("erase"),
            name="erase",
            tooltip="Eraser Tool",
            callback=lambda: self.tool_manager.set_active_tool("erase")
        )
        toolbar.register_tool(
            tool=self.tool_manager.get_tool("dropper"),
            name="pipe",
            tooltip="Dropper Tool",
            callback=lambda: self.tool_manager.set_active_tool("dropper")
        )
        toolbar.finalize()
        
        # --- Central Widget ---
        container = QWidget(self)
        layout = QHBoxLayout(container)
        self.setCentralWidget(container)
        
        self.map_panel = MapPanel2D(self.map_engine, container)
        layout.addWidget(self.map_panel, 8)
        
        self.layer_panel = LayerPanel(self.icon_manager, self.chunk_engine, self.map_engine, container)
        layout.addWidget(self.layer_panel, 1)

    def undo(self):
        self.map_engine.history_manager.undo()
        self.map_panel.update()

    def redo(self):
        self.map_engine.history_manager.redo()
        self.map_panel.update()

    def new_map(self):
        if not self._prompt_save_if_needed():
            return
        self.map_engine.chunk_engine.reset()
        self.map_engine.history_manager.clear()
        self.current_filepath = None
        self.map_panel.update()
        self.layer_panel.layer_entry_container.build_entries()

    def open_map(self):
        if not self._prompt_save_if_needed():
            return
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Map", "", "HexaMapper Files (*.hmap)")
        if filepath:
            self.file_manager.load_map(filepath)
            self.current_filepath = filepath
            self.map_engine.history_manager.clear()
            self.map_panel.update()
            self.layer_panel.layer_entry_container.build_entries()

    def save_map(self):
        if self.current_filepath:
            self.file_manager.save_map(self.current_filepath)
            self.map_engine.history_manager.clear()
        else:
            self.save_map_as()

    def save_map_as(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Map As", "", "HexaMapper Files (*.hmap)")
        if filepath:
            self.file_manager.save_map(filepath)
            self.current_filepath = filepath
            self.map_engine.history_manager.clear()

    def export_map(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Export as PNG", "", "PNG Image (*.png)")
        if filepath:
            self.file_manager.export_map_as_png(filepath)

    def _prompt_save_if_needed(self) -> bool:
        if (len(self.map_engine.history_manager.undo_stack) == 0 and len(self.map_engine.history_manager.redo_stack) == 0):
            return True

        msg_box = QMessageBox()
        msg_box.setText("You have unsaved changes.")
        msg_box.setInformativeText("Do you want to save your changes?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Save)
        ret = msg_box.exec()

        if ret == QMessageBox.StandardButton.Save:
            self.save_map()
            return True
        elif ret == QMessageBox.StandardButton.Discard:
            return True
        else:
            return False
        
    def closeEvent(self, a0):
        ret = self._prompt_save_if_needed()
        if ret:
            a0.accept()
        else:
            a0.ignore()
