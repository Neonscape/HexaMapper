from utils.color import RGBAColor
from utils.color import RGBAColor
from widgets.map_panel import MapPanel2D
from modules.shader_manager import shader_manager as sm
from modules.config import app_config as conf
from modules.chunk_engine import ChunkEngine
from modules.history_manager import HistoryManager
from modules.tool_manager import tool_manager as tm
from modules.tools.draw_tool import DrawTool
from OpenGL.GL import *
from PyQt6.QtCore import QPointF
import numpy as np
from enum import Enum
from modules.map_helpers import *
from loguru import logger

class DrawMode(Enum):
    DRAW_FILLED = 0
    DRAW_OUTLINE = 1

class Camera2D:
    pos: QPointF = QPointF(0.0, 0.0)
    zoom: float = 0.1
    

class MapEngine2D:
    def __init__(self, map_panel: MapPanel2D = None):
        self.map_panel = map_panel
        self.chunk_manager : ChunkEngine = ChunkEngine()
        self.history_manager = HistoryManager()
        self.tool_manager = tm
        tm.map_engine = self
        sm.register_program("hex_shader", conf.hex_map_shaders.unit.vertex, conf.hex_map_shaders.unit.fragment)
        sm.register_program("bg_shader", conf.hex_map_shaders.background.vertex, conf.hex_map_shaders.background.fragment)
        sm.register_program("cursor_shader", conf.hex_map_shaders.cursor.vertex, conf.hex_map_shaders.cursor.fragment)
        self.chunk_buffers: dict[tuple[int, int], dict[str, int]] = {}
        self.camera = Camera2D()
        self._register_tools()

    def _register_tools(self):
        self.tool_manager.register_tool("draw", DrawTool(self))
        self.tool_manager.set_active_tool("draw")
        
    def init_engine(self):
        self._create_geometry()
        
    def _create_geometry(self):
        """creates the shared geometries (hex, background quad) for instanced rendering.
        """
        
        # Shared 2D hexagon geometries
        
        filled_vertices = [(0.0, 0.0)]
        
        outline_vertices = []
        
        for i in range(6):
            angle = i * 60 * np.pi / 180
            x = conf.hex_map_engine.hex_radius * np.cos(angle)
            y = conf.hex_map_engine.hex_radius * np.sin(angle)
            filled_vertices.append((x, y))
            outline_vertices.append((x, y))
            
            
        # To close the loop for triangle fan
        filled_vertices.append(filled_vertices[1])
        
        geometry_data = np.array(filled_vertices, dtype=np.float32)
        outline_data = np.array(outline_vertices, dtype=np.float32)
        
        hex_vbo = sm.add_vbo("hex_filled")
        glBindBuffer(GL_ARRAY_BUFFER, hex_vbo)
        glBufferData(GL_ARRAY_BUFFER, geometry_data.nbytes, geometry_data, GL_STATIC_DRAW)
        
        outline_vbo = sm.add_vbo("hex_outline")
        glBindBuffer(GL_ARRAY_BUFFER, outline_vbo)
        glBufferData(GL_ARRAY_BUFFER, outline_data.nbytes, outline_data, GL_STATIC_DRAW)
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        
        # Background quad
        
        w, h = self.map_panel.width(), self.map_panel.height()
        
        bg_vertices = np.array([
            0.0, 0.0,
            w, 0.0,
            w, h,
            0.0, 0.0,
            w, h,
            0.0, h
            ], dtype=np.float32)
        
        bg_vao = sm.add_vao("bg_quad")
        bg_vbo = sm.add_vbo("bg_quad")
        
        glBindVertexArray(bg_vao)
        glBindBuffer(GL_ARRAY_BUFFER, bg_vbo)
        glBufferData(GL_ARRAY_BUFFER, bg_vertices.nbytes, bg_vertices, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), None)
        glEnableVertexAttribArray(0)
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        # Cursor quad
        cursor_vertices = np.array([
            -1.0, -1.0,
            1.0, -1.0,
            1.0, 1.0,
            -1.0, -1.0,
            1.0, 1.0,
            -1.0, 1.0
        ], dtype=np.float32)

        cursor_vao = sm.add_vao("cursor_quad")
        cursor_vbo = sm.add_vbo("cursor_quad")

        glBindVertexArray(cursor_vao)
        glBindBuffer(GL_ARRAY_BUFFER, cursor_vbo)
        glBufferData(GL_ARRAY_BUFFER, cursor_vertices.nbytes, cursor_vertices, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), None)
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def update_background(self, w: float, h: float):
        """update the background based on new panel size.
        """
        
        background_vertices = np.array([
            0.0, 0.0,
            w, 0.0,
            w, h,
            0.0, h
        ], dtype=np.float32)
        
        glBindBuffer(GL_ARRAY_BUFFER, sm.get_vbo("bg_quad"))
        glBufferSubData(GL_ARRAY_BUFFER, 0, background_vertices.nbytes, background_vertices)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        
    def draw_gradient_background(self):
        
        glDisable(GL_DEPTH_TEST)
        
        pg = sm.get_program("bg_shader")
        glUseProgram(pg)
        glUniform4f(glGetUniformLocation(pg, "topColor"), *(conf.background.grad_color_0))
        glUniform4f(glGetUniformLocation(pg, "bottomColor"), *(conf.background.grad_color_1))
        glUniform1f(glGetUniformLocation(pg, "viewportHeight"), float(self.map_panel.height()))
        
        glBindVertexArray(sm.get_vao("bg_quad"))
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        
        glUseProgram(0)
        glEnable(GL_DEPTH_TEST)
        
    def draw_hex_chunk_filled(self, chunk_buffer: dict[str, int]):
        
        pg = sm.get_program("hex_shader")
        glUseProgram(pg)
        
        proj_mat = self._create_projection_matrix()
        view_mat = self._create_view_matrix()
        
        glUniformMatrix4fv(glGetUniformLocation(pg, "projection"), 1, GL_TRUE, proj_mat)
        glUniformMatrix4fv(glGetUniformLocation(pg, "view"), 1, GL_TRUE, view_mat)
        
        color_loc = glGetUniformLocation(pg, "color")
        mode_loc = glGetUniformLocation(pg, "drawMode")
        
        glUniform1i(mode_loc, DrawMode.DRAW_FILLED.value)
        glUniform4f(color_loc, *(conf.hex_map_custom.default_cell_color))
        
        glBindVertexArray(chunk_buffer["filled_vao"])
        glDrawArraysInstanced(GL_TRIANGLE_FAN, 0, 8, conf.hex_map_engine.chunk_size ** 2)
        
        glBindVertexArray(0)
        glUseProgram(0)
        
    def draw_hex_chunk_outline(self, chunk_buffer: dict[str, int]):

        pg = sm.get_program("hex_shader")
        glUseProgram(pg)
        
        proj_mat = self._create_projection_matrix()
        view_mat = self._create_view_matrix()
        
        glUniformMatrix4fv(glGetUniformLocation(pg, "projection"), 1, GL_TRUE, proj_mat)
        glUniformMatrix4fv(glGetUniformLocation(pg, "view"), 1, GL_TRUE, view_mat)
        
        color_loc = glGetUniformLocation(pg, "color")
        mode_loc = glGetUniformLocation(pg, "drawMode")
        
        glUniform1i(mode_loc, DrawMode.DRAW_OUTLINE.value)
        glUniform4f(color_loc, *(conf.hex_map_custom.outline_color))
        glLineWidth(conf.hex_map_custom.outline_width)
        glBindVertexArray(chunk_buffer["outline_vao"])
        glDrawArraysInstanced(GL_LINE_LOOP, 0, 6, conf.hex_map_engine.chunk_size ** 2)
        
        glBindVertexArray(0)
        glUseProgram(0)
    
    def update_and_render_chunks(self):
        dirty_chunks = self.chunk_manager.get_and_clear_dirty_chunks()
        
        for chunk_coord in dirty_chunks:
            logger.debug("Updating chunk instance buffer for dirty chunks...")
            self._update_chunk_instance_buffer(chunk_coord)
                
                
        visible_chunks = self._get_visible_chunks()
        for chunk_coord in visible_chunks:
            if chunk_coord not in self.chunk_buffers:
                logger.debug(f"Visible chunk {chunk_coord} not in chunk buffer, constructing buffer for it...")
                self._update_chunk_instance_buffer(chunk_coord)
            self.draw_hex_chunk_filled(self.chunk_buffers[chunk_coord])
            self.draw_hex_chunk_outline(self.chunk_buffers[chunk_coord])

    def draw_tool_visual_aid(self, mouse_world_pos: QPointF):
        tool = self.tool_manager.get_active_tool()
        if not tool:
            return

        visual_aid_info = tool.get_visual_aid_info()
        if not visual_aid_info:
            return

        shape = visual_aid_info.get("shape")
        if shape == "circle":
            pg = sm.get_program("cursor_shader")
            glUseProgram(pg)

            proj_mat = self._create_projection_matrix()
            view_mat = self._create_view_matrix()

            glUniformMatrix4fv(glGetUniformLocation(pg, "projection"), 1, GL_TRUE, proj_mat)
            glUniformMatrix4fv(glGetUniformLocation(pg, "view"), 1, GL_TRUE, view_mat)

            radius = visual_aid_info.get("radius", 1.0) * conf.hex_map_engine.hex_radius
            color = visual_aid_info.get("color", (1.0, 1.0, 1.0, 1.0))
            
            glUniform2f(glGetUniformLocation(pg, "center_pos"), mouse_world_pos.x(), mouse_world_pos.y())
            glUniform1f(glGetUniformLocation(pg, "radius"), radius)
            glUniform4f(glGetUniformLocation(pg, "color"), *color)
            glUniform1f(glGetUniformLocation(pg, "thickness"), 0.05) # TODO: make this configurable

            glBindVertexArray(sm.get_vao("cursor_quad"))
            glDrawArrays(GL_TRIANGLES, 0, 6)

            glBindVertexArray(0)
            glUseProgram(0)

    def _update_chunk_instance_buffer(self, chunk_coord: tuple[int, int]):
        """Generates instance data for a chunk (pos, color) and upload it to GPU."""
        logger.debug(f"Updating chunk instance buffer for chunk {chunk_coord}")
        
        DATA_DIMENSIONS = conf.hex_map_engine.data_dimensions
        
        if chunk_coord in self.chunk_buffers:
            buf = self.chunk_buffers[chunk_coord]
            instance_vbo_id, filled_vao_id, outline_vao_id = buf["instance_vbo"], buf["filled_vao"], buf["outline_vao"]
            glDeleteBuffers(1, [instance_vbo_id])
            glDeleteVertexArrays(1, [filled_vao_id])
            glDeleteVertexArrays(1, [outline_vao_id])
            
        chunk_data = self.chunk_manager.get_chunk_data(chunk_coord)
        # FIX: Ensure the numpy array has the correct float32 dtype for OpenGL
        instance_data = np.array(self._generate_chunk_instance_data(chunk_coord, chunk_data), dtype=np.float32)
        
        
        filled_vao = glGenVertexArrays(1)
        glBindVertexArray(filled_vao)
        
        glBindBuffer(GL_ARRAY_BUFFER, sm.get_vbo("hex_filled"))
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
        glBindBuffer(GL_ARRAY_BUFFER, sm.get_vbo("hex_outline"))
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
        
        CHUNK_SIZE = conf.hex_map_engine.chunk_size
        
        instance_data = []
        chunk_origin_x = chunk_coord[0] * CHUNK_SIZE
        chunk_origin_y = chunk_coord[1] * CHUNK_SIZE
        
        for lx in range(CHUNK_SIZE):
            for ly in range(CHUNK_SIZE):
                global_x = chunk_origin_x + lx
                global_y = chunk_origin_y + ly
                
                center_x, center_y = get_center_position_from_global_coord((global_x, global_y))
                color = chunk_data[lx, ly]
                
                instance_data.extend([center_x, center_y, *color])
                # FIX: Removed performance-hindering print statement
        return instance_data
    
    # helper functions: matrices
    
    def _create_projection_matrix(self):
        """Create projection matrix for the camera.
        The projection matrix transforms coordinates from view space (camera-oriented space)
        to Normalized Device Coordinates (NDCs).
        """
        w, h = self.map_panel.width(), self.map_panel.height()
        
        aspect = w / h if h > 0 else 1
        
        l, r = -aspect / self.camera.zoom, aspect / self.camera.zoom
        b, t = -1 / self.camera.zoom, 1 / self.camera.zoom
        
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
            [1, 0, 0, -self.camera.pos.x()],
            [0, 1, 0, -self.camera.pos.y()],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
    
    def _get_visible_chunks(self):
        """Return the coordinates of the visible chunks.

        Returns:
            _type_: _description_
        """
        tl_world = self._screen_to_world((0, 0))
        br_world = self._screen_to_world((self.map_panel.width(), self.map_panel.height()))
        
        min_gx, min_gy = global_pos_to_global_coord(tl_world)
        max_gx, max_gy = global_pos_to_global_coord(br_world)
        
        min_chunk_x, min_chunk_y, _, _ = global_coord_to_chunk_coord((min_gx, min_gy))
        max_chunk_x, max_chunk_y, _, _ = global_coord_to_chunk_coord((max_gx, max_gy))
        
        if min_chunk_x > max_chunk_x:
            min_chunk_x, max_chunk_x = max_chunk_x, min_chunk_x
        if min_chunk_y > max_chunk_y:
            min_chunk_y, max_chunk_y = max_chunk_y, min_chunk_y
        
        visible = set()
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_y in range(min_chunk_y, max_chunk_y + 1):
                visible.add((chunk_x, chunk_y))
        
        return visible
    
    def _screen_to_world(self, screen_pos: tuple[float, float]):
        """Converts screen position to world position (for mouse actions).

        Args:
            screen_pos (tuple[float, float]): _description_
        """
        
        w, h = self.map_panel.width(), self.map_panel.height()
        ndc_x, ndc_y = ((screen_pos[0] / w) * 2 - 1, 1 - (screen_pos[1] / h) * 2)
        proj, view = self._create_projection_matrix(), self._create_view_matrix()
        inv_proj, inv_view = np.linalg.inv(proj), np.linalg.inv(view)
        world_pos = inv_view @ inv_proj @ np.array([ndc_x, ndc_y, 0, 1])
        return QPointF(world_pos[0], world_pos[1])
    
    def move_view(self, last_view_pos: QPointF, current_view_pos: QPointF):
        """moves the camera based on two view locations.

        Args:
            last_view_pos (QPointF): last position the cursor is on the screen
            current_view_pos (QPointF): current position the cursor is on the screen
        """
        
        delta_x = current_view_pos.x() - last_view_pos.x()
        delta_y = current_view_pos.y() - last_view_pos.y()
        
        w, h = self.map_panel.width(), self.map_panel.height()
        
        aspect = w / h if h > 0 else 1
        
        world_view_width = 2 * aspect / self.camera.zoom
        world_view_height = 2 / self.camera.zoom
        world_dx_per_pixel = world_view_width / w
        world_dy_per_pixel = world_view_height / h
        self.camera.pos.setX(self.camera.pos.x() - delta_x * world_dx_per_pixel)
        self.camera.pos.setY(self.camera.pos.y() + delta_y * world_dy_per_pixel)
        self.map_panel.update()
        
    def zoom(self, zooming_up: bool):
        """Zooms in or out based on the zoom factor.

        Args:
            zooming_up (bool): True if zooming in, False if zooming out
        """
        
        MIN_ZOOM = conf.hex_map_view.min_zoom
        MAX_ZOOM = conf.hex_map_view.max_zoom
        
        if zooming_up:
            self.camera.zoom *= 1.1
        else:
            self.camera.zoom /= 1.1
            
        self.camera.zoom = max(MIN_ZOOM, min(self.camera.zoom, MAX_ZOOM))
        self.map_panel.update()
