from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QSurfaceFormat
from OpenGL.GL import *
from modules.map_engine import MapEngine2D
from modules.event_handlers import MapPanel2DEventHandler


class MapPanel2D(QOpenGLWidget):
    """
    A QOpenGLWidget subclass that serves as the main display panel for the 2D hex map.
    It handles OpenGL rendering, mouse interactions, and integrates with the MapEngine2D.
    """
    def __init__(self, engine: MapEngine2D, parent=None):
        """
        Initializes the MapPanel2D.

        :param engine: The MapEngine2D instance to associate with this panel.
        :type engine: MapEngine2D
        :param parent: The parent widget, defaults to None.
        :type parent: QWidget, optional
        """
        super().__init__(parent)
        self.engine = engine
        self.last_mouse_pos = None
        
        self._configure_opengl()
        self.setMouseTracking(True)
        
        # The event handler is responsible for all user interaction with the map
        self.event_handler = MapPanel2DEventHandler(self.engine)
        self.installEventFilter(self.event_handler)

    def _configure_opengl(self):
        """
        Sets up the desired OpenGL format for the widget.
        """
        format = QSurfaceFormat()
        format.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
        format.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile) 
        format.setVersion(4, 1) 
        format.setSamples(8) # Enable MSAA
        self.setFormat(format)

    def initializeGL(self):
        """
        Initializes the OpenGL rendering context.
        This function is called once before the first call to paintGL() or resizeGL().
        """
        self.makeCurrent()
        
        # Compile shaders now that we have a valid OpenGL context
        self.engine.shader_manager.compile_all_programs()
        
        self.engine.init_engine()
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_MULTISAMPLE) # Enable MSAA

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
        
        # self.engine.draw_gradient_background()
        
        self.engine.update_and_render_chunks()
        
        if self.event_handler.last_mouse_pos:
            pos = self.event_handler.last_mouse_pos
            mouse_world_pos = self.engine.screen_to_world((pos.x(), pos.y()))
            self.engine.draw_tool_visual_aid(mouse_world_pos)
        
        
        
        

        
