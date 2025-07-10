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
    
    # helper functions: cell-transform
    
    @staticmethod
    def get_center_position_from_global_coord(global_coord: tuple[int, int]) -> tuple[float, float]:
        """Finds the world position of the given cell at the global coord.

        Args:
            global_coord (tuple[int, int]): _description_

        Returns:
            tuple[float, float]: _description_
        """
        col, row = global_coord
        # odd-q vertical layout
        x = HEX_RADIUS * 3 / 2 * col
        y = HEX_RADIUS * sqrt(3) * (row + 0.5 * (col % 2))
        return (x, y)
        
    @staticmethod
    def global_coord_to_chunk_coord(global_coord: tuple[int, int]) -> tuple[int, int, int, int]:
        """Finds which chunk the given cell is in and where is it in the chunk.

        Args:
            global_coord (tuple[int, int]): the global coord of the cell

        Returns:
            tuple[int, int, int, int]: [chunk_x, chunk_y, local_x, local_y]
        """
        return (global_coord[0] // CHUNK_SIZE,
                global_coord[1] // CHUNK_SIZE,
                global_coord[0] % CHUNK_SIZE,
                global_coord[1] % CHUNK_SIZE)
        
    @staticmethod
    def global_pos_to_global_coord(global_pos: QPointF) -> tuple[int, int]:
        """Finds the global coord of the cell at the given world position."""
        # CORRECTED: Use proper horizontal scaling factor (1.5 * HEX_RADIUS)
        col_approx = global_pos.x() / (1.5 * HEX_RADIUS)
        
        # CORRECTED: Use proper vertical scaling factor (sqrt(3) * HEX_RADIUS)
        row_approx = global_pos.y() / (sqrt(3) * HEX_RADIUS)
        
        col = round(col_approx)
        row = round(row_approx)
        
        # Find the coordinates of the three closest hex centers
        candidates = []
        for r_offset in range(-1, 2):
            for c_offset in range(-1, 2):
                cand_row = row + r_offset
                cand_col = col + c_offset
                center_pos = MapPanel2D.get_center_position_from_global_coord((cand_col, cand_row))
                dist_sq = (global_pos.x() - center_pos[0])**2 + (global_pos.y() - center_pos[1])**2
                candidates.append(((cand_col, cand_row), dist_sq))
        
        # Find the one with the minimum distance
        best_coord, _ = min(candidates, key=lambda item: item[1])
        return best_coord
