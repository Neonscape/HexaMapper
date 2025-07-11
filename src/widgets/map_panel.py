from math import sqrt
from PyQt6.QtCore import QPointF
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from modules import event_handlers
from modules.config import app_config as cf
from modules.shader_manager import shader_manager as sm
from modules.event_handlers import MapPanel2DEventHandler

HEX_RADIUS = cf.hex_map_engine.hex_radius
CHUNK_SIZE = cf.hex_map_engine.chunk_size


class MapPanel2D(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.engine = None
        self.event_handler = None
        self.installEventFilter(self.event_handler)
        

    def initializeGL(self):
        # Prepare OpenGL environment and the canvas
        self.makeCurrent()
        
        # TODO: Refactor for more OpenGL Widgets
        sm.compile_all_programs()
        
        self.engine.init_engine()
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
    def init_panel(self, engine):
        self.engine = engine
        self.event_handler = MapPanel2DEventHandler(self.engine)
        self.installEventFilter(self.event_handler)
        
    # TODO: implement application style management & style file load

    def initUI(self):
        self.setStyleSheet("background-color: #333333;")

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.engine.update_background(w, h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        
        # self.engine.draw_gradient_background()
        self.engine.update_and_render_chunks()
