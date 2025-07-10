from PyQt6.QtWidgets import QWidget, QMainWindow, QLayout, QHBoxLayout, QGridLayout, QMenuBar, QStatusBar, QToolBar
from widgets.map_panel import MapPanel2D
from modules.map_engine import MapEngine2D
from loguru import logger

class MainAppWindow(QMainWindow):
    def __init__(self, engine_2d: MapEngine2D, title: str ="Main Window", size: tuple[int, int] = (800, 600)):
        super().__init__()
        self._engine = engine_2d
        self._layout : QLayout = None
        self._menuBar: QMenuBar = None
        self._toolBar : QToolBar = None
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
        self._menuNar = self.menuBar()
        
        self._statusBar = self.statusBar()
        
        self._toolBar = QToolBar()
        self.addToolBar(self._toolBar)
        
        container = QWidget()
        self._container = container
        self._layout = QHBoxLayout(container)
        self.setCentralWidget(container)
        
        map_panel = MapPanel2D()
        self.add_children("map", map_panel)
        self.children["map"].init_panel(self._engine)
        self._engine.map_panel = map_panel
