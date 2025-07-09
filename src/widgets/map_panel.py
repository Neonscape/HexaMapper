from ctypes import Union
from math import sqrt
from PyQt6.QtGui import QMouseEvent, QWheelEvent
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from utils.helpers import load_program
from loguru import logger

CHUNK_SIZE = 16
DATA_DIMENSIONS = 4 # 4 channels for a chunk: (r, g, b, a)
HEX_RADIUS = 1
HEX_HEIGHT = 0.5

class HexChunkManager:
    def __init__(self):
        self.chunks: dict[tuple[int, int], np.ndarray] = {}
        self.dirty_chunks : set[tuple[int, int]] = set()
        
    def _get_or_create_chunk(self, chunk_coord: tuple[int, int]) -> np.ndarray:
        """Get a chunk's information (and creates it when non-exist).

        Args:
            chunk_coord (tuple[int, int]): the coordinate of the chunk

        Returns:
            _type_: the chunk data
        """
        if chunk_coord not in self.chunks:
            self.chunks[chunk_coord] = np.full((CHUNK_SIZE, CHUNK_SIZE, DATA_DIMENSIONS), [0.5, 0.5, 0.5, 1], dtype=np.float32)
        return self.chunks[chunk_coord]
    
    
    def set_cell_data(self, global_coords: tuple[int, int], data: np.ndarray) -> None:
        """Change a cell's data.

        Args:
            global_coords (tuple[int, int]): the global coords of the cell
            data (np.ndarray): the data to write
        """
        logger.debug(f"Setting cell data at {global_coords} to {data}")
        chunk_x, chunk_y, local_x, local_y = MapPanel.global_coord_to_chunk_coord(global_coords)
        chunk_data = self._get_or_create_chunk((chunk_x, chunk_y))
        chunk_data[local_x, local_y] = data
        self.dirty_chunks.add((chunk_x, chunk_y))
        
        
    def get_chunk_data(self, chunk_coord: tuple[int, int]) -> np.ndarray:
        """Get a chunk's data.

        Args:
            chunk_coord (tuple[int, int]): the chunk's coordinate

        Returns:
            np.ndarray: the chunk's data
        """
        
        return self._get_or_create_chunk(chunk_coord=chunk_coord)
    
    def get_and_clear_dirty_chunks(self) -> list[tuple[int, int]]:
        """Get the dirty chunks and clear the dirty list.

        Returns:
            list[tuple[int, int]]: the dirty chunks
        """
        
        dirty = list(self.dirty_chunks)
        self.dirty_chunks.clear()
        return dirty
        
class MapPanel(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.mode : Union["2D", "3D"] = "2D"
        self.data_manager : HexChunkManager = HexChunkManager()
        
        # Rendering states
        self.shader_program = None
        self.hex_vbo = None                 # the geometry data for a single hexagon cell (using Instanced Rendering here)
        self.chunk_buffers : dict = {}             # chunk_coord -> instance_vbo_id, vao_id; used to store instance data for each chunk
        
        # Camera states
        self.camera_pos = QPointF(0.0, 0.0) # position of the camera
        self.camera_zoom = 0.1              # zoom level
        
        # Mouse states
        self.last_mouse_pos = QPointF()
        
        # Rendering properties
        self.background_color = [0.2, 0.2, 0.2, 1.0] # RGBA
        
        # OpenGL Attributes
        # TODO: refactor them to use configuration file
        self.vertex_shader_path = "./src/shaders/vertex_shader.glsl"
        self.fragment_shader_path = "./src/shaders/fragment_shader.glsl"
        
    
    
    def initializeGL(self):
        
        # Prepare OpenGL environment and the canvas
        self.makeCurrent()
        glClearColor(*self.background_color)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        self.shader_program = load_program(self.vertex_shader_path, self.fragment_shader_path)
        
        if self.shader_program is None:
            logger.error("Failed to initialize application. exitting...")
            exit(1)
            
        self._create_shared_hex_geometry()
            
    def _create_shared_hex_geometry(self) -> None:
        """Creates a hexagon geometry (vertices) using the triangle fan method
        to be shared around all instances.
        """
        unit_hex_indices = [(0.0, 0.0)] # center vertex
        
        for i in range(6):
            angle = i * 60 * np.pi / 180
            x = HEX_RADIUS * np.cos(angle)
            y = HEX_RADIUS * np.sin(angle)
            unit_hex_indices.append((x, y))
            
        # To close the loop for triangle fan
        unit_hex_indices.append(unit_hex_indices[1])
        
        geometry_data = np.array(unit_hex_indices, dtype=np.float32)
        
        # Pass the created geometry to the GPU
        self.hex_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.hex_vbo)
        glBufferData(GL_ARRAY_BUFFER, geometry_data.nbytes, geometry_data, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        
        

    def initUI(self):
        self.setStyleSheet("background-color: #333333;")


    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.shader_program)
        
        dirty_chunks = self.data_manager.get_and_clear_dirty_chunks()
        
        for chunk_coord in dirty_chunks:
            logger.debug("Updating chunk instance buffer for dirty chunks...")
            self._update_chunk_instance_buffer(chunk_coord)
            
        # construct transform matrices and pass them to the shader
        proj_mat = self._create_projection_matrix()
        view_mat = self._create_view_matrix()
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_TRUE, proj_mat)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_TRUE, view_mat)
        
        # determine visible chunks
        visible_chunks = self._get_visible_chunks()
        
        for chunk_coord in visible_chunks:
            if chunk_coord not in self.chunk_buffers:
                logger.debug(f"Visible chunk {chunk_coord} not in chunk buffer, constructing buffer for it...")
                self._update_chunk_instance_buffer(chunk_coord)
            
            # logger.debug(f"Drawing chunk {chunk_coord}")
            vao = self.chunk_buffers[chunk_coord][1]
            glBindVertexArray(vao)
            glDrawArraysInstanced(GL_TRIANGLE_FAN, 0, 8, CHUNK_SIZE * CHUNK_SIZE)
            glBindVertexArray(0)
        
    def _update_chunk_instance_buffer(self, chunk_coord: tuple[int, int]):
        """Generates instance data for a chunk (pos, color) and upload it to GPU."""
        logger.debug(f"Updating chunk instance buffer for chunk {chunk_coord}")
        
        if chunk_coord in self.chunk_buffers:
            instance_vbo_id, vao_id = self.chunk_buffers[chunk_coord]
            glDeleteBuffers(1, [instance_vbo_id])
            glDeleteVertexArrays(1, [vao_id])
            
        chunk_data = self.data_manager.get_chunk_data(chunk_coord)
        # FIX: Ensure the numpy array has the correct float32 dtype for OpenGL
        instance_data = np.array(self._generate_chunk_instance_data(chunk_coord, chunk_data), dtype=np.float32)
        
        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)
        
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
        
        # Color attribute
        glVertexAttribPointer(2, DATA_DIMENSIONS, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * sizeof(GLfloat)))
        glEnableVertexAttribArray(2)
        glVertexAttribDivisor(2, 1)
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        
        logger.debug(f"Finished instance buffer update for chunk {chunk_coord}")
        self.chunk_buffers[chunk_coord] = (instance_vbo, vao)

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
        world_pos = inv_view @ inv_proj @ np.array([ndc_x, ndc_y, 0, 1]).T
        return QPointF(world_pos[0], world_pos[1])
    
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

            logger.debug(f"Camera position: {self.camera_pos}")
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
