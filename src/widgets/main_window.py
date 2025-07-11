from PyQt6.QtWidgets import (
    QWidget, QMainWindow, QLayout, QHBoxLayout, QGridLayout, QMenuBar, QStatusBar
)
from PyQt6.QtGui import QAction, QKeySequence
from widgets.map_panel import MapPanel2D
from modules.map_engine import MapEngine2D
from loguru import logger

class MainAppWindow(QMainWindow):
    def __init__(self, engine_2d: MapEngine2D, title: str ="Main Window", size: tuple[int, int] = (800, 600)):
        super().__init__()
        self._engine = engine_2d
        self._layout : QLayout = None
        self._menuBar: QMenuBar = None
        self._statusBar : QStatusBar = None
        self._container : QWidget = None
        self.children : dict[str, QWidget] = {}
        self.setWindowTitle(title)
        self.resize(size[0], size[1])
        self.initUI()
        self.show()
    
    def add_children(self, name: str, widget: QWidget): 
        # TODO: implement richer control over layout
        self.children[name] = widget
        self._layout.addWidget(widget)
        
    def initUI(self):
        self._menuBar = self.menuBar()
        
        # Add Edit Menu for Undo/Redo
        edit_menu = self._menuBar.addMenu("Edit")
        
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        self._statusBar = self.statusBar()
        
        # self._toolBar = QToolBar()
        # self.addToolBar(self._toolBar)
        
        container = QWidget()
        self._container = container
        self._layout = QHBoxLayout(container)
        self.setCentralWidget(container)
        
        map_panel = MapPanel2D()
        self.add_children("map", map_panel)
        self.children["map"].init_panel(self._engine)
        self._engine.map_panel = map_panel

    def undo(self):
        self._engine.history_manager.undo()
        self._engine.map_panel.update()

    def redo(self):
        self._engine.history_manager.redo()
        self._engine.map_panel.update()
