from typing import Literal
from math import sqrt
from PyQt6.QtGui import QMouseEvent, QWheelEvent
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from utils.helpers import load_program
from enum import Enum
from modules.chunk_engine import ChunkEngine
from loguru import logger

# TODO: refactor those constants to use configuration files

class DrawMode(Enum):
    DRAW_FILLED = 0
    DRAW_OUTLINE = 1

CHUNK_SIZE = 16
DATA_DIMENSIONS = 4 # 4 channels for a chunk: (r, g, b, a)
HEX_RADIUS = 1
HEX_HEIGHT = 0.5
OUTLINE_COLOR = [0.6, 0.6, 0.6, 0.4]
DEFAULT_CELL_COLOR = [0.5, 0.5, 0.5, 1]
OUTLINE_WIDTH = 2.0
MIN_ZOOM = 0.01
MAX_ZOOM = 5.0

# Define colors for the gradient background
TOP_BG_COLOR = [0.2, 0.2, 0.3, 1.0] # Dark gray-blue
BOTTOM_BG_COLOR = [0.6, 0.6, 0.6, 1.0] # Gray



        
# TODO: Dissect map draw / management logic from the display panel?
class MapPanel(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.mode : Literal['3D', '2D'] = "2D" # reserved for later 3D development
        self.data_manager : ChunkEngine = ChunkEngine()
        
        # Rendering properties
        self.hex_shader_program = None
        self.background_shader_program = None
        self.background_vao = None
        self.background_vbo = None
        self.hex_vbo = None                 # the geometry data for a single hexagon cell (using Instanced Rendering here)
        self.outline_vbo = None             # geometry data for outline
        self.chunk_buffers : dict[tuple[int, int], dict[str, int]] = {}             # chunk_coord -> instance_vbo_id, vao_id; used to store instance data for each chunk
        
        # Camera states
        self.camera_pos = QPointF(0.0, 0.0) # position of the camera
        self.camera_zoom = 0.1              # zoom level
        
        # Mouse states
        self.last_mouse_pos = QPointF()
        
        # Rendering properties
        self.background_color = [0.2, 0.2, 0.2, 1.0] # RGBA
        
        # OpenGL Attributes
        # TODO: refactor these to use configuration file...?
        # maybe we can construct a shader manager...?
        self.hex_vertex_shader_path = "./src/shaders/hex/vsh.glsl"
        self.hex_fragment_shader_path = "./src/shaders/hex/fsh.glsl"
        self.background_vertex_shader_path = "./src/shaders/background/vsh.glsl"
        self.background_fragment_shader_path = "./src/shaders/background/fsh.glsl"
        
    
    
    def initializeGL(self):
        
        # Prepare OpenGL environment and the canvas
        self.makeCurrent()
        glClearColor(*self.background_color)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # maybe we can have a more robust shader (file / program) management system?
        self.hex_shader_program = load_program(self.hex_vertex_shader_path, self.hex_fragment_shader_path)
        self.background_shader_program = load_program(self.background_vertex_shader_path, self.background_fragment_shader_path)
        
        if self.hex_shader_program is None:
            logger.error("Failed to compile hex shader. exitting...")
            exit(1)
        
        if self.background_shader_program is None:
            logger.error("Failed to compile background shader. exitting...")
            exit(1)
            
        self._create_shared_hex_geometry()
        self._create_background_quad_geometry()
            
    def _create_shared_hex_geometry(self) -> None:
        """Creates a hexagon geometry (vertices) using the triangle fan method
        to be shared around all instances.
        """
        filled_vertices = [(0.0, 0.0)]   # center vertex
                                        # this is for the filled hexagon coloring
        outline_vertices = []
        
        for i in range(6):
            angle = i * 60 * np.pi / 180
            x = HEX_RADIUS * np.cos(angle)
            y = HEX_RADIUS * np.sin(angle)
            filled_vertices.append((x, y))
            outline_vertices.append((x, y))
            
            
        # To close the loop for triangle fan
        filled_vertices.append(filled_vertices[1])
        
        geometry_data = np.array(filled_vertices, dtype=np.float32)
        outline_data = np.array(outline_vertices, dtype=np.float32)
        
        # create VBO for the filled hexagon geometry
        self.hex_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.hex_vbo)
        glBufferData(GL_ARRAY_BUFFER, geometry_data.nbytes, geometry_data, GL_STATIC_DRAW)
        
        # create VBO for outline geometry
        self.outline_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.outline_vbo)
        glBufferData(GL_ARRAY_BUFFER, outline_data.nbytes, outline_data, GL_STATIC_DRAW)
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
    
    def _create_background_quad_geometry(self) -> None:
        """Creates a full-screen quad for the background."""
        # Vertices for a quad covering the entire viewport, in pixel coordinates
        # These coordinates will be transformed to clip space in the vertex shader
        background_vertices = np.array([
            0.0, 0.0,  # Bottom-left
            self.width(), 0.0, # Bottom-right
            self.width(), self.height(), # Top-right
            0.0, self.height() # Top-left
        ], dtype=np.float32)

        self.background_vao = glGenVertexArrays(1)
        self.background_vbo = glGenBuffers(1)

        glBindVertexArray(self.background_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.background_vbo)
        glBufferData(GL_ARRAY_BUFFER, background_vertices.nbytes, background_vertices, GL_DYNAMIC_DRAW) # DYNAMIC_DRAW because size might change on resize

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        
    def _update_background_geometry(self, w:int, h: int) -> None:
        """Updates the background quad vertices based on new window dimensions."""
        background_vertices = np.array([
            0.0, 0.0,
            w, 0.0,
            w, h,
            0.0, h
        ], dtype=np.float32)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.background_vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, background_vertices.nbytes, background_vertices)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        
    # TODO: implement application style management & style file load

    def initUI(self):
        self.setStyleSheet("background-color: #333333;")


    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        if self.background_vbo is not None:
            self._update_background_geometry(w, h)
            
    def _draw_gradient_background(self):
        """
        Renders a gradient background using a full-screen quad and a dedicated shader.
        This should be called FIRST in paintGL.
        """
        glDisable(GL_DEPTH_TEST) # Ensure background is always behind everything
        
        glUseProgram(self.background_shader_program)
        
        # Pass colors and viewport height to the background shader
        glUniform4f(glGetUniformLocation(self.background_shader_program, "topColor"), *TOP_BG_COLOR)
        glUniform4f(glGetUniformLocation(self.background_shader_program, "bottomColor"), *BOTTOM_BG_COLOR)
        glUniform1f(glGetUniformLocation(self.background_shader_program, "viewportHeight"), float(self.height()))
        
        glBindVertexArray(self.background_vao)
        glDrawArrays(GL_QUADS, 0, 4) # Draw the quad
        glBindVertexArray(0)
        
        glUseProgram(0) # Deactivate background shader
        glEnable(GL_DEPTH_TEST) # Re-enable depth test for your main scene if needed

    def _draw_hex_chunk_filled(self, chunk_buffer: dict[str, int]):
        
        glUseProgram(self.hex_shader_program)
        
        proj_mat = self._create_projection_matrix()
        view_mat = self._create_view_matrix()
        glUniformMatrix4fv(glGetUniformLocation(self.hex_shader_program, "projection"), 1, GL_TRUE, proj_mat)
        glUniformMatrix4fv(glGetUniformLocation(self.hex_shader_program, "view"), 1, GL_TRUE, view_mat)
        
        color_loc = glGetUniformLocation(self.hex_shader_program, "color")
        mode_loc = glGetUniformLocation(self.hex_shader_program, "drawMode")
        
        glUniform1i(mode_loc, DrawMode.DRAW_FILLED.value)
        glUniform4f(color_loc, *DEFAULT_CELL_COLOR)
        glBindVertexArray(chunk_buffer["filled_vao"])
        glDrawArraysInstanced(GL_TRIANGLE_FAN, 0, 8, CHUNK_SIZE * CHUNK_SIZE)
        
        glBindVertexArray(0)
        glUseProgram(0)
    
    def _draw_hex_chunk_outline(self, chunk_buffer: dict[str, int]):

        glUseProgram(self.hex_shader_program)

        proj_mat = self._create_projection_matrix()
        view_mat = self._create_view_matrix()
        glUniformMatrix4fv(glGetUniformLocation(self.hex_shader_program, "projection"), 1, GL_TRUE, proj_mat)
        glUniformMatrix4fv(glGetUniformLocation(self.hex_shader_program, "view"), 1, GL_TRUE, view_mat)

        color_loc = glGetUniformLocation(self.hex_shader_program, "color")
        mode_loc = glGetUniformLocation(self.hex_shader_program, "drawMode")

        glUniform1i(mode_loc, DrawMode.DRAW_OUTLINE.value)
        glUniform4f(color_loc, *OUTLINE_COLOR)
        glLineWidth(OUTLINE_WIDTH)
        glBindVertexArray(chunk_buffer["outline_vao"])
        glDrawArraysInstanced(GL_LINE_LOOP, 0, 6, CHUNK_SIZE * CHUNK_SIZE)

        glBindVertexArray(0)
        glUseProgram(0)
        
        
        

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        
        self._draw_gradient_background()
        
        glUseProgram(self.hex_shader_program)
        
        dirty_chunks = self.data_manager.get_and_clear_dirty_chunks()
        
        for chunk_coord in dirty_chunks:
            logger.debug("Updating chunk instance buffer for dirty chunks...")
            self._update_chunk_instance_buffer(chunk_coord)
        
        # determine visible chunks
        visible_chunks = self._get_visible_chunks()
        
        for chunk_coord in visible_chunks:
            if chunk_coord not in self.chunk_buffers:
                logger.debug(f"Visible chunk {chunk_coord} not in chunk buffer, constructing buffer for it...")
                self._update_chunk_instance_buffer(chunk_coord)
            
            self._draw_hex_chunk_filled(self.chunk_buffers[chunk_coord])
            self._draw_hex_chunk_outline(self.chunk_buffers[chunk_coord])
        
    def _update_chunk_instance_buffer(self, chunk_coord: tuple[int, int]):
        """Generates instance data for a chunk (pos, color) and upload it to GPU."""
        logger.debug(f"Updating chunk instance buffer for chunk {chunk_coord}")
        
        if chunk_coord in self.chunk_buffers:
            buf = self.chunk_buffers[chunk_coord]
            instance_vbo_id, filled_vao_id, outline_vao_id = buf["instance_vbo"], buf["filled_vao"], buf["outline_vao"]
            glDeleteBuffers(1, [instance_vbo_id])
            glDeleteVertexArrays(1, [filled_vao_id])
            glDeleteVertexArrays(1, [outline_vao_id])
            
        chunk_data = self.data_manager.get_chunk_data(chunk_coord)
        # FIX: Ensure the numpy array has the correct float32 dtype for OpenGL
        instance_data = np.array(self._generate_chunk_instance_data(chunk_coord, chunk_data), dtype=np.float32)
        
        
        filled_vao = glGenVertexArrays(1)
        glBindVertexArray(filled_vao)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.hex_vbo)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        instance_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, instance_vbo)
        glBufferData(GL_ARRAY_BUFFER, instance_data.nbytes, instance_data, GL_STATIC_DRAW)
        
        stride = (2 + DATA_DIMENSIONS) * sizeof(GLfloat)
        # Position attribute
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribDivisor(1, 1)
        
        # Color attribute for the filled hexagon
        glVertexAttribPointer(2, DATA_DIMENSIONS, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * sizeof(GLfloat)))
        glEnableVertexAttribArray(2)
        glVertexAttribDivisor(2, 1)
        
        # Points for the outline to draw (x1, y1), (x2, y2), ...
        outline_vao = glGenVertexArrays(1)
        glBindVertexArray(outline_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.outline_vbo)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        # We only need the offset passed in the first step
        glBindBuffer(GL_ARRAY_BUFFER, instance_vbo)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribDivisor(1, 1)
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        
        logger.debug(f"Finished instance buffer update for chunk {chunk_coord}")
        self.chunk_buffers[chunk_coord] = {
            "filled_vao": filled_vao,
            "instance_vbo": instance_vbo,
            "outline_vao": outline_vao
        }

    def _generate_chunk_instance_data(self, chunk_coord: tuple[int, int], chunk_data: np.ndarray):
        """Generate data for a given chunk instance."""
        instance_data = []
        chunk_origin_x = chunk_coord[0] * CHUNK_SIZE
        chunk_origin_y = chunk_coord[1] * CHUNK_SIZE
        
        for lx in range(CHUNK_SIZE):
            for ly in range(CHUNK_SIZE):
                global_x = chunk_origin_x + lx
                global_y = chunk_origin_y + ly
                
                center_x, center_y = MapPanel.get_center_position_from_global_coord((global_x, global_y))
                color = chunk_data[lx, ly]
                
                instance_data.extend([center_x, center_y, *color])
                # FIX: Removed performance-hindering print statement
        return instance_data
    
    def _get_visible_chunks(self):
        """Return the coordinates of the visible chunks.

        Returns:
            _type_: _description_
        """
        tl_world = self._screen_to_world((0, 0))
        br_world = self._screen_to_world((self.width(), self.height()))
        
        min_gx, min_gy = MapPanel.global_pos_to_global_coord(tl_world)
        max_gx, max_gy = MapPanel.global_pos_to_global_coord(br_world)
        
        min_chunk_x, min_chunk_y, _, _ = MapPanel.global_coord_to_chunk_coord((min_gx, min_gy))
        max_chunk_x, max_chunk_y, _, _ = MapPanel.global_coord_to_chunk_coord((max_gx, max_gy))
        
        if min_chunk_x > max_chunk_x:
            min_chunk_x, max_chunk_x = max_chunk_x, min_chunk_x
        if min_chunk_y > max_chunk_y:
            min_chunk_y, max_chunk_y = max_chunk_y, min_chunk_y
        
        visible = set()
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_y in range(min_chunk_y, max_chunk_y + 1):
                visible.add((chunk_x, chunk_y))
        
        return visible
        

    
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
                center_pos = MapPanel.get_center_position_from_global_coord((cand_col, cand_row))
                dist_sq = (global_pos.x() - center_pos[0])**2 + (global_pos.y() - center_pos[1])**2
                candidates.append(((cand_col, cand_row), dist_sq))
        
        # Find the one with the minimum distance
        best_coord, _ = min(candidates, key=lambda item: item[1])
        return best_coord
        
        
    # helper functions: matrices
    
    def _create_projection_matrix(self):
        """Create projection matrix for the camera.
        The projection matrix transforms coordinates from view space (camera-oriented space)
        to Normalized Device Coordinates (NDCs).
        """
        w, h = self.width(), self.height()
        
        aspect = w / h if h > 0 else 1
        
        l, r = -aspect / self.camera_zoom, aspect / self.camera_zoom
        b, t = -1 / self.camera_zoom, 1 / self.camera_zoom
        
        return np.array([
            [2.0 / (r - l), 0, 0, -(r + l) / (r - l)],
            [0, 2.0 / (t - b), 0, -(t + b) / (t - b)],
            [0, 0, -1, 0],
            [0, 0, 0, 1]
        ])
    
    def _create_view_matrix(self):
        """Create view matrix for the camera.
        The view matrix transforms coordinates from world space to view space.
        """
        return np.array([
            [1, 0, 0, -self.camera_pos.x()],
            [0, 1, 0, -self.camera_pos.y()],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
    
    
    # helper functions: coordinates transform
    def _screen_to_world(self, screen_pos: tuple[float, float]):
        """Converts screen position to world position (for mouse actions).

        Args:
            screen_pos (tuple[float, float]): _description_
        """
        
        w, h = self.width(), self.height()
        ndc_x, ndc_y = ((screen_pos[0] / w) * 2 - 1, 1 - (screen_pos[1] / h) * 2)
        proj, view = self._create_projection_matrix(), self._create_view_matrix()
        inv_proj, inv_view = np.linalg.inv(proj), np.linalg.inv(view)
        world_pos = inv_view @ inv_proj @ np.array([ndc_x, ndc_y, 0, 1])
        return QPointF(world_pos[0], world_pos[1])
    
    def moveView(self, last_view_pos: QPointF, current_view_pos: QPointF):
        """moves the camera based on two view locations.

        Args:
            last_view_pos (QPointF): last position the cursor is on the screen
            current_view_pos (QPointF): current position the cursor is on the screen
        """
        
        delta_x = current_view_pos.x() - last_view_pos.x()
        delta_y = current_view_pos.y() - last_view_pos.y()
        
        w, h = self.width(), self.height()
        
        aspect = w / h if h > 0 else 1
        
        world_view_width = 2 * aspect / self.camera_zoom
        world_view_height = 2 / self.camera_zoom
        world_dx_per_pixel = world_view_width / w
        world_dy_per_pixel = world_view_height / h
        self.camera_pos.setX(self.camera_pos.x() - delta_x * world_dx_per_pixel)
        self.camera_pos.setY(self.camera_pos.y() + delta_y * world_dy_per_pixel)
        self.update()
        
    def zoom(self, isZoomingUp: bool):
        """Zooms in or out based on the zoom factor.

        Args:
            isZoomingUp (bool): True if zooming in, False if zooming out
        """
        if isZoomingUp:
            self.camera_zoom *= 1.1
        else:
            self.camera_zoom /= 1.1
            
        self.camera_zoom = max(MIN_ZOOM, min(self.camera_zoom, MAX_ZOOM))
        self.update()
        
        

    
    # mouse events
    
    def mousePressEvent(self, event: QMouseEvent):
        self.last_mouse_pos = event.position()

    def mouseMoveEvent(self, event: QMouseEvent):
        current_pos = event.position()
        
        # Pan the camera with the left mouse button
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta_screen_x = current_pos.x() - self.last_mouse_pos.x()
            delta_screen_y = current_pos.y() - self.last_mouse_pos.y()

            w, h = self.width(), self.height()
            aspect = w / h if h > 0 else 1

            # 获取当前投影矩阵定义的视景体世界尺寸
            world_view_width = 2 * aspect / self.camera_zoom
            world_view_height = 2 / self.camera_zoom

            # 计算每个像素对应的世界单位
            # 屏幕X轴正方向与世界X轴正方向一致
            world_dx_per_pixel = world_view_width / w
            # 屏幕Y轴向下，世界Y轴向上，所以这里需要一个负号或在计算delta_screen_y时反转
            world_dy_per_pixel = world_view_height / h

            # 摄像机应向鼠标拖动方向的反方向移动
            # 比如鼠标向右（delta_screen_x > 0），摄像机应向左（camera_pos.x 减小）
            # 鼠标向下（delta_screen_y > 0），摄像机应向上（camera_pos.y 增大，因为世界Y轴向上）
            self.camera_pos.setX(self.camera_pos.x() - delta_screen_x * world_dx_per_pixel)
            self.camera_pos.setY(self.camera_pos.y() + delta_screen_y * world_dy_per_pixel) # 注意这里是 +

            self.update()
    
        # Paint cells with the right mouse button
        elif event.buttons() & Qt.MouseButton.RightButton:
            world_pos = self._screen_to_world((current_pos.x(), current_pos.y()))
            grid_coord = MapPanel.global_pos_to_global_coord(world_pos)
            
            # Generate a random color
            random_color = np.random.rand(4).astype(np.float32)
            random_color[3] = 1.0  # Keep alpha at 1.0
            
            self.data_manager.set_cell_data(grid_coord, random_color)
            self.update()
            
        self.last_mouse_pos = current_pos

    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
        self.camera_zoom *= zoom_factor
        self.camera_zoom = max(0.01, min(self.camera_zoom, 5.0))
        self.update()
