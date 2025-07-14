from __future__ import annotations
from typing import TYPE_CHECKING
from utils.color import RGBAColor
from modules.shader_manager import ShaderManager
from modules.config import ApplicationConfig
from modules.chunk_engine import ChunkEngine
from modules.history_manager import HistoryManager
from modules.tool_manager import ToolManager
from modules.tools.draw_tool import DrawTool
from OpenGL.GL import *
from PyQt6.QtCore import QPointF
import numpy as np
from enum import Enum
from modules.map_helpers import get_center_position_from_global_coord, global_coord_to_chunk_coord, global_pos_to_global_coord
from loguru import logger

if TYPE_CHECKING:
    from widgets.map_panel import MapPanel2D

class DrawMode(Enum):
    """
    Enum for specifying the drawing mode for hexagons.
    """
    DRAW_FILLED = 0
    DRAW_OUTLINE = 1

class Camera2D:
    """
    Represents a 2D camera with position and zoom level.
    """
    pos: QPointF = QPointF(0.0, 0.0)
    zoom: float = 0.1
    

class MapEngine2D:
    """
    The core 2D map rendering engine responsible for managing map data,
    OpenGL drawing operations, camera control, and tool interactions.
    """
    def __init__(self, config: ApplicationConfig, chunk_engine: ChunkEngine, history_manager: HistoryManager, shader_manager: ShaderManager):
        """
        Initializes the MapEngine2D.
        """
        self.config = config
        self.chunk_engine = chunk_engine
        self.history_manager = history_manager
        self.shader_manager = shader_manager
        
        self.map_panel: MapPanel2D | None = None # Set later via set_map_panel
        self.tool_manager: ToolManager | None = None # Set later via set_tool_manager

        self.shader_manager.register_program("hex_shader", self.config.hex_map_shaders.unit.vertex, self.config.hex_map_shaders.unit.fragment)
        self.shader_manager.register_program("bg_shader", self.config.hex_map_shaders.background.vertex, self.config.hex_map_shaders.background.fragment)
        self.shader_manager.register_program("cursor_shader", self.config.hex_map_shaders.cursor.vertex, self.config.hex_map_shaders.cursor.fragment)
        
        self.chunk_buffers: dict[tuple[int, int], dict[str, int]] = {}
        self.camera = Camera2D()

    def set_map_panel(self, map_panel: MapPanel2D):
        """
        Sets the map panel reference.
        """
        self.map_panel = map_panel

    def set_tool_manager(self, tool_manager: ToolManager):
        """
        Sets the tool manager reference.
        """
        self.tool_manager = tool_manager
        
    def init_engine(self):
        """
        Initializes the OpenGL engine by creating shared geometries.
        """
        self._create_geometry()
        
    def _create_geometry(self):
        """
        Creates the shared geometries (hex, background quad, cursor quad) for instanced rendering.
        These geometries are uploaded to the GPU as VBOs and VAOs.
        """
        
        # Shared 2D hexagon geometries
        filled_vertices = [(0.0, 0.0)]
        outline_vertices = []
        
        for i in range(6):
            angle = i * 60 * np.pi / 180
            x = self.config.hex_map_engine.hex_radius * np.cos(angle)
            y = self.config.hex_map_engine.hex_radius * np.sin(angle)
            filled_vertices.append((x, y))
            outline_vertices.append((x, y))
            
        # To close the loop for triangle fan
        filled_vertices.append(filled_vertices[1])
        
        geometry_data = np.array(filled_vertices, dtype=np.float32)
        outline_data = np.array(outline_vertices, dtype=np.float32)
        
        hex_vbo = self.shader_manager.add_vbo("hex_filled")
        glBindBuffer(GL_ARRAY_BUFFER, hex_vbo)
        glBufferData(GL_ARRAY_BUFFER, geometry_data.nbytes, geometry_data, GL_STATIC_DRAW)
        
        outline_vbo = self.shader_manager.add_vbo("hex_outline")
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
        
        bg_vao = self.shader_manager.add_vao("bg_quad")
        bg_vbo = self.shader_manager.add_vbo("bg_quad")
        
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

        cursor_vao = self.shader_manager.add_vao("cursor_quad")
        cursor_vbo = self.shader_manager.add_vbo("cursor_quad")

        glBindVertexArray(cursor_vao)
        glBindBuffer(GL_ARRAY_BUFFER, cursor_vbo)
        glBufferData(GL_ARRAY_BUFFER, cursor_vertices.nbytes, cursor_vertices, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), None)
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def update_background(self, w: float, h: float):
        """
        Updates the background quad's geometry based on the new panel size.

        :param w: New width of the map panel.
        :type w: float
        :param h: New height of the map panel.
        :type h: float
        """
        
        background_vertices = np.array([
            0.0, 0.0,
            w, 0.0,
            w, h,
            0.0, h
        ], dtype=np.float32)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.shader_manager.get_vbo("bg_quad"))
        glBufferSubData(GL_ARRAY_BUFFER, 0, background_vertices.nbytes, background_vertices)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        
    def draw_gradient_background(self):
        """
        Draws a gradient background using the background shader.
        """
        
        glDisable(GL_DEPTH_TEST)
        
        pg = self.shader_manager.get_program("bg_shader")
        glUseProgram(pg)
        glUniform4f(glGetUniformLocation(pg, "topColor"), *(self.config.background.grad_color_0))
        glUniform4f(glGetUniformLocation(pg, "bottomColor"), *(self.config.background.grad_color_1))
        glUniform1f(glGetUniformLocation(pg, "viewportHeight"), float(self.map_panel.height()))
        
        glBindVertexArray(self.shader_manager.get_vao("bg_quad"))
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        
        glUseProgram(0)
        glEnable(GL_DEPTH_TEST)
        
    def draw_hex_chunk_filled(self, chunk_buffer: dict[str, int]):
        """
        Draws the filled hexagons for a given chunk.

        :param chunk_buffer: Dictionary containing OpenGL buffer IDs for the chunk.
        :type chunk_buffer: dict[str, int]
        """
        
        pg = self.shader_manager.get_program("hex_shader")
        glUseProgram(pg)
        
        proj_mat = self._create_projection_matrix()
        view_mat = self._create_view_matrix()
        
        glUniformMatrix4fv(glGetUniformLocation(pg, "projection"), 1, GL_TRUE, proj_mat)
        glUniformMatrix4fv(glGetUniformLocation(pg, "view"), 1, GL_TRUE, view_mat)
        
        color_loc = glGetUniformLocation(pg, "color")
        mode_loc = glGetUniformLocation(pg, "drawMode")
        
        glUniform1i(mode_loc, DrawMode.DRAW_FILLED.value)
        glUniform4f(color_loc, *(self.config.hex_map_custom.default_cell_color))
        
        glBindVertexArray(chunk_buffer["filled_vao"])
        glDrawArraysInstanced(GL_TRIANGLE_FAN, 0, 8, self.config.hex_map_engine.chunk_size ** 2)
        
        glBindVertexArray(0)
        glUseProgram(0)
        
    def draw_hex_chunk_outline(self, chunk_buffer: dict[str, int]):
        """
        Draws the outlines of hexagons for a given chunk.

        :param chunk_buffer: Dictionary containing OpenGL buffer IDs for the chunk.
        :type chunk_buffer: dict[str, int]
        """

        pg = self.shader_manager.get_program("hex_shader")
        glUseProgram(pg)
        
        proj_mat = self._create_projection_matrix()
        view_mat = self._create_view_matrix()
        
        glUniformMatrix4fv(glGetUniformLocation(pg, "projection"), 1, GL_TRUE, proj_mat)
        glUniformMatrix4fv(glGetUniformLocation(pg, "view"), 1, GL_TRUE, view_mat)
        
        color_loc = glGetUniformLocation(pg, "color")
        mode_loc = glGetUniformLocation(pg, "drawMode")
        
        glUniform1i(mode_loc, DrawMode.DRAW_OUTLINE.value)
        glUniform4f(color_loc, *(self.config.hex_map_custom.outline_color))
        glLineWidth(self.config.hex_map_custom.outline_width)
        glBindVertexArray(chunk_buffer["outline_vao"])
        glDrawArraysInstanced(GL_LINE_LOOP, 0, 6, self.config.hex_map_engine.chunk_size ** 2)
        
        glBindVertexArray(0)
        glUseProgram(0)
    
    def update_and_render_chunks(self):
        """
        Updates dirty chunks and renders all visible chunks.
        """
        dirty_chunks = self.chunk_engine.get_and_clear_dirty_chunks()
        
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
        """
        Draws a visual aid for the active tool, such as a circle for the draw tool.

        :param mouse_world_pos: The current mouse position in world coordinates.
        :type mouse_world_pos: QPointF
        """
        tool = self.tool_manager.get_active_tool()
        if not tool:
            return

        visual_aid_info = tool.get_visual_aid_info()
        if not visual_aid_info:
            return

        shape = visual_aid_info.get("shape")
        if shape == "circle":
            pg = self.shader_manager.get_program("cursor_shader")
            glUseProgram(pg)

            proj_mat = self._create_projection_matrix()
            view_mat = self._create_view_matrix()

            glUniformMatrix4fv(glGetUniformLocation(pg, "projection"), 1, GL_TRUE, proj_mat)
            glUniformMatrix4fv(glGetUniformLocation(pg, "view"), 1, GL_TRUE, view_mat)

            radius = visual_aid_info.get("radius", 1.0) * self.config.hex_map_engine.hex_radius
            color = visual_aid_info.get("color", (1.0, 1.0, 1.0, 1.0))
            
            glUniform2f(glGetUniformLocation(pg, "center_pos"), mouse_world_pos.x(), mouse_world_pos.y())
            glUniform1f(glGetUniformLocation(pg, "radius"), radius)
            glUniform4f(glGetUniformLocation(pg, "color"), *color)
            glUniform1f(glGetUniformLocation(pg, "thickness"), 0.05) # TODO: make this configurable

            glBindVertexArray(self.shader_manager.get_vao("cursor_quad"))
            glDrawArrays(GL_TRIANGLES, 0, 6)

            glBindVertexArray(0)
            glUseProgram(0)

    def _update_chunk_instance_buffer(self, chunk_coord: tuple[int, int]):
        """
        Generates instance data (position, color) for a given chunk and uploads it to the GPU.

        :param chunk_coord: The (x, y) coordinates of the chunk.
        :type chunk_coord: tuple[int, int]
        """
        logger.debug(f"Updating chunk instance buffer for chunk {chunk_coord}")
        
        DATA_DIMENSIONS = self.config.hex_map_engine.data_dimensions
        
        if chunk_coord in self.chunk_buffers:
            buf = self.chunk_buffers[chunk_coord]
            instance_vbo_id, filled_vao_id, outline_vao_id = buf["instance_vbo"], buf["filled_vao"], buf["outline_vao"]
            glDeleteBuffers(1, [instance_vbo_id])
            glDeleteVertexArrays(1, [filled_vao_id])
            glDeleteVertexArrays(1, [outline_vao_id])
            
        chunk_data = self.chunk_engine.get_chunk_data(chunk_coord)
        # Ensure the numpy array has the correct float32 dtype for OpenGL
        instance_data = np.array(self._generate_chunk_instance_data(chunk_coord, chunk_data), dtype=np.float32)
        
        
        filled_vao = glGenVertexArrays(1)
        glBindVertexArray(filled_vao)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.shader_manager.get_vbo("hex_filled"))
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
        glBindBuffer(GL_ARRAY_BUFFER, self.shader_manager.get_vbo("hex_outline"))
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
        """
        Generates instance data (center position and color) for all cells within a given chunk.

        :param chunk_coord: The (x, y) coordinates of the chunk.
        :type chunk_coord: tuple[int, int]
        :param chunk_data: The NumPy array containing cell data for the chunk.
        :type chunk_data: np.ndarray
        :return: A list of interleaved position and color data for instanced rendering.
        :rtype: list
        """
        
        chunk_size = self.config.hex_map_engine.chunk_size
        
        instance_data = []
        chunk_origin_x = chunk_coord[0] * chunk_size
        chunk_origin_y = chunk_coord[1] * chunk_size
        
        for lx in range(chunk_size):
            for ly in range(chunk_size):
                global_x = chunk_origin_x + lx
                global_y = chunk_origin_y + ly
                
                center_x, center_y = get_center_position_from_global_coord((global_x, global_y), self.config.hex_map_engine.hex_radius)
                color = chunk_data[lx, ly]
                
                instance_data.extend([center_x, center_y, *color])
        return instance_data
    
    def _create_projection_matrix(self):
        """
        Creates the projection matrix for the camera.

        The projection matrix transforms coordinates from view space (camera-oriented space)
        to Normalized Device Coordinates (NDCs).

        :return: A 4x4 NumPy array representing the projection matrix.
        :rtype: np.ndarray
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
        """
        Creates the view matrix for the camera.

        The view matrix transforms coordinates from world space to view space.

        :return: A 4x4 NumPy array representing the view matrix.
        :rtype: np.ndarray
        """
        return np.array([
            [1, 0, 0, -self.camera.pos.x()],
            [0, 1, 0, -self.camera.pos.y()],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
    
    def _get_visible_chunks(self):
        """
        Calculates and returns the coordinates of the chunks currently visible in the viewport.

        :return: A set of (chunk_x, chunk_y) tuples for visible chunks.
        :rtype: set[tuple[int, int]]
        """
        tl_world = self.screen_to_world((0, 0))
        br_world = self.screen_to_world((self.map_panel.width(), self.map_panel.height()))
        
        min_gx, min_gy = global_pos_to_global_coord(tl_world, self.config.hex_map_engine.hex_radius)
        max_gx, max_gy = global_pos_to_global_coord(br_world, self.config.hex_map_engine.hex_radius)
        
        min_chunk_x, min_chunk_y, _, _ = global_coord_to_chunk_coord((min_gx, min_gy), self.config.hex_map_engine.chunk_size)
        max_chunk_x, max_chunk_y, _, _ = global_coord_to_chunk_coord((max_gx, max_gy), self.config.hex_map_engine.chunk_size)
        
        if min_chunk_x > max_chunk_x:
            min_chunk_x, max_chunk_x = max_chunk_x, min_chunk_x
        if min_chunk_y > max_chunk_y:
            min_chunk_y, max_chunk_y = max_chunk_y, min_chunk_y
        
        visible = set()
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_y in range(min_chunk_y, max_chunk_y + 1):
                visible.add((chunk_x, chunk_y))
        
        return visible
    
    def screen_to_world(self, screen_pos: tuple[float, float]):
        """
        Converts a screen position (pixel coordinates) to a world position.

        This is useful for translating mouse input coordinates into the 2D world space
        of the map.

        :param screen_pos: A tuple (x, y) representing the screen coordinates.
        :type screen_pos: tuple[float, float]
        :return: A QPointF representing the corresponding world coordinates.
        :rtype: QPointF
        """
        
        w, h = self.map_panel.width(), self.map_panel.height()
        ndc_x, ndc_y = ((screen_pos[0] / w) * 2 - 1, 1 - (screen_pos[1] / h) * 2)
        proj, view = self._create_projection_matrix(), self._create_view_matrix()
        inv_proj, inv_view = np.linalg.inv(proj), np.linalg.inv(view)
        world_pos = inv_view @ inv_proj @ np.array([ndc_x, ndc_y, 0, 1])
        return QPointF(world_pos[0], world_pos[1])
    
    def move_view(self, last_view_pos: QPointF, current_view_pos: QPointF):
        """
        Moves the camera view based on the difference between two screen positions.

        This is typically used for panning the map.

        :param last_view_pos: The previous screen position of the cursor.
        :type last_view_pos: QPointF
        :param current_view_pos: The current screen position of the cursor.
        :type current_view_pos: QPointF
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
        """
        Adjusts the camera's zoom level.

        :param zooming_up: True to zoom in (increase zoom level), False to zoom out (decrease zoom level).
        :type zooming_up: bool
        """
        
        min_zoom = self.config.hex_map_view.min_zoom
        max_zoom = self.config.hex_map_view.max_zoom
        
        if zooming_up:
            self.camera.zoom *= 1.1
        else:
            self.camera.zoom /= 1.1
            
        self.camera.zoom = max(min_zoom, min(self.camera.zoom, max_zoom))
        self.map_panel.update()
