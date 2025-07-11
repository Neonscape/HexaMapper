from math import sqrt
from PyQt6.QtCore import QPointF
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QSurfaceFormat
from OpenGL.GL import *
from OpenGL.GLU import *
from modules import event_handlers
from modules.config import app_config as cf
from modules.shader_manager import shader_manager as sm
from modules.event_handlers import MapPanel2DEventHandler

HEX_RADIUS = cf.hex_map_engine.hex_radius
CHUNK_SIZE = cf.hex_map_engine.chunk_size


class MapPanel2D(QOpenGLWidget):
    """
    A QOpenGLWidget subclass that serves as the main display panel for the 2D hex map.
    It handles OpenGL rendering, mouse interactions, and integrates with the MapEngine2D.
    """
    def __init__(self, parent=None):
        """
        Initializes the MapPanel2D.

        :param parent: The parent widget, defaults to None.
        :type parent: QWidget, optional
        """
        super().__init__(parent)
        self.initUI()
        self.engine = None
        self.event_handler = None
        # The event handler is installed in init_panel, so this line is redundant here.
        # self.installEventFilter(self.event_handler) 
        self.last_mouse_pos = None
        self.setMouseTracking(True)
        
        format = QSurfaceFormat()
        format.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
        # Or CompatibilityProfile, depending on your OpenGL usage
        format.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile) 
        # Request a modern OpenGL version if possible
        format.setVersion(4, 1) 
        # Request 8 samples for MSAA (common values: 2, 4, 8, 16)
        format.setSamples(8) 
        self.setFormat(format)
        

    def initializeGL(self):
        """
        Initializes the OpenGL rendering context.
        This function is called once before the first call to paintGL() or resizeGL().
        """
        # Prepare OpenGL environment and the canvas
        self.makeCurrent()
        
        sm.compile_all_programs()
        
        self.engine.init_engine()
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
    def init_panel(self, engine):
        """
        Initializes the map panel with the given map engine and sets up the event handler.

        :param engine: The MapEngine2D instance to associate with this panel.
        :type engine: MapEngine2D
        """
        self.engine = engine
        self.event_handler = MapPanel2DEventHandler(self.engine)
        self.installEventFilter(self.event_handler)
        
    def initUI(self):
        """
        Initializes the user interface components and styling for the panel.
        """
        self.setStyleSheet("background-color: #333333;")

    def resizeGL(self, w, h):
        """
        Resizes the OpenGL viewport when the widget is resized.

        :param w: The new width of the widget.
        :type w: int
        :param h: The new height of the widget.
        :type h: int
        """
        glViewport(0, 0, w, h)
        self.engine.update_background(w, h)

    def paintGL(self):
        """
        Paints the OpenGL content. This function is called whenever the widget needs to be updated.
        """
        glClear(GL_COLOR_BUFFER_BIT)
        
        self.engine.update_and_render_chunks()

        if self.last_mouse_pos:
            mouse_world_pos = self.engine._screen_to_world((self.last_mouse_pos.x(), self.last_mouse_pos.y()))
            self.engine.draw_tool_visual_aid(mouse_world_pos)

    def mouseMoveEvent(self, event):
        """
        Handles mouse move events to update the last mouse position and trigger repaints.

        :param event: The mouse event.
        :type event: QMouseEvent
        """
        self.last_mouse_pos = event.pos()
        super().mouseMoveEvent(event)
        self.update()
