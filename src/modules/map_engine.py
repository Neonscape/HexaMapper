from __future__ import annotations
from typing import TYPE_CHECKING
from utils.color import RGBAColor
from modules.shader_manager import ShaderManager
from modules.config import ApplicationConfig
from modules.chunk_engine import ChunkLayer, ChunkEngine
from modules.history_manager import HistoryManager
from modules.tool_manager import ToolManager
from modules.tools.draw_tool import DrawTool
from OpenGL.GL import *
from qtpy.QtCore import QPointF, Signal, QObject  # 添加Signal导入
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
    

class MapEngine2D(QObject):
    transform_changed = Signal(float, float, float)  # pan_x, pan_y, zoom
    
    """
    The core 2D map rendering engine responsible for managing map data,
    OpenGL drawing operations, camera control, and tool interactions.
    """
    def __init__(self, config: ApplicationConfig, chunk_engine: ChunkEngine, history_manager: HistoryManager, shader_manager: ShaderManager):
        """
        Initializes the MapEngine2D.
        """
        super().__init__()
        self.config = config
        self.chunk_engine = chunk_engine
        self.history_manager = history_manager
        self.shader_manager = shader_manager
        
        self.map_panel: MapPanel2D | None = None # Set later via set_map_panel
        self.tool_manager: ToolManager | None = None # Set later via set_tool_manager

        self.shader_manager.register_program("hex_shader", self.config.hex_map_shaders.unit.vertex, self.config.hex_map_shaders.unit.fragment, ["projection", "view", "color", "drawMode"])
        self.shader_manager.register_program("bg_shader", self.config.hex_map_shaders.background.vertex, self.config.hex_map_shaders.background.fragment, ["topColor", "bottomColor", "viewportHeight"])
        self.shader_manager.register_program("cursor_shader", self.config.hex_map_shaders.cursor.vertex, self.config.hex_map_shaders.cursor.fragment, ["projection", "view", "center_pos", "radius", "color", "thickness"])
        
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
        
    def draw_gradient_background(self, width: float = None, height: float = None):
        """
        Draws a gradient background using the background shader.
        
        :param width: The width of the background. If None, use the current map panel width.
        :type width: float, optional
        :param height: The height of the background. If None, use the current map panel height.
        :type height: float, optional
        """
        if width is None:
            width = self.map_panel.width()
        if height is None:
            height = self.map_panel.height()
        
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        
        
        pg = self.shader_manager.get_program("bg_shader")
        glUseProgram(pg)
        uniforms = self.shader_manager.get_uniforms("bg_shader")
        glUniform4f(uniforms["topColor"], *(self.config.background.grad_color_0))
        glUniform4f(uniforms["bottomColor"], *(self.config.background.grad_color_1))
        glUniform1f(uniforms["viewportHeight"], float(height))
        
        # Create a temporary quad for the background of the given size
        vertices = np.array([
            0.0, 0.0,
            width, 0.0,
            width, height,
            0.0, height
        ], dtype=np.float32)
        
        # Create temporary VAO and VBO
        temp_vao = glGenVertexArrays(1)
        temp_vbo = glGenBuffers(1)
        
        glBindVertexArray(temp_vao)
        glBindBuffer(GL_ARRAY_BUFFER, temp_vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), None)
        glEnableVertexAttribArray(0)
        
        glDrawArrays(GL_TRIANGLES, 0, 6)
        
        glBindVertexArray(0)
        glDeleteVertexArrays(1, [temp_vao])
        glDeleteBuffers(1, [temp_vbo])
        
        glUseProgram(0)
        
        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)
        
        
    def render_scene(self, proj_mat, view_mat, chunks_to_render):
        """
        Renders a scene with a given projection and view matrix.
        """
        pg = self.shader_manager.get_program("hex_shader")
        glUseProgram(pg)
        
        uniforms = self.shader_manager.get_uniforms("hex_shader")

        glUniformMatrix4fv(uniforms["projection"], 1, GL_TRUE, proj_mat)
        glUniformMatrix4fv(uniforms["view"], 1, GL_TRUE, view_mat)

        for chunk_coord in chunks_to_render:
            if chunk_coord not in self.chunk_buffers:
                self._update_chunk_instance_buffer(chunk_coord)
            
            chunk_buffer = self.chunk_buffers[chunk_coord]

            # Draw filled hexes
            glUniform1i(uniforms["drawMode"], DrawMode.DRAW_FILLED.value)
            glUniform4f(uniforms["color"], *(self.config.hex_map_custom.default_cell_color))
            glBindVertexArray(chunk_buffer["filled_vao"])
            glDrawArraysInstanced(GL_TRIANGLE_FAN, 0, 8, self.config.hex_map_engine.chunk_size ** 2)

            # Draw outlines
            glUniform1i(uniforms["drawMode"], DrawMode.DRAW_OUTLINE.value)
            glUniform4f(uniforms["color"], *(self.config.hex_map_custom.outline_color))
            glLineWidth(self.config.hex_map_custom.outline_width)
            glBindVertexArray(chunk_buffer["outline_vao"])
            glDrawArraysInstanced(GL_LINE_LOOP, 0, 6, self.config.hex_map_engine.chunk_size ** 2)

        glBindVertexArray(0)
        glUseProgram(0)

    def update_and_render_chunks(self):
        """
        Updates dirty chunks and renders all visible chunks to the screen.
        """
        dirty_chunks = self.chunk_engine.get_and_clear_dirty_chunks()
        for chunk_coord in dirty_chunks:
            self._update_chunk_instance_buffer(chunk_coord)
        
        visible_chunks = self._get_visible_chunks()
        proj_mat = self._create_projection_matrix()
        view_mat = self._create_view_matrix()
        
        self.render_scene(proj_mat, view_mat, visible_chunks)

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
            
            uniforms = self.shader_manager.get_uniforms("cursor_shader")

            glUniformMatrix4fv(uniforms["projection"], 1, GL_TRUE, proj_mat)
            glUniformMatrix4fv(uniforms["view"], 1, GL_TRUE, view_mat)

            radius = visual_aid_info.get("radius", 1.0) * self.config.hex_map_engine.hex_radius
            color = visual_aid_info.get("color", (1.0, 1.0, 1.0, 1.0))
            
            glUniform2f(uniforms["center_pos"], mouse_world_pos.x(), mouse_world_pos.y())
            glUniform1f(uniforms["radius"], radius)
            glUniform4f(uniforms["color"], *color)
            glUniform1f(uniforms["thickness"], 0.05) # TODO: make this configurable

            glBindVertexArray(self.shader_manager.get_vao("cursor_quad"))
            glDrawArrays(GL_TRIANGLES, 0, 6)

            glBindVertexArray(0)
            glUseProgram(0)

    # map_engine.py:MapEngine2D

    def _update_chunk_instance_buffer(self, chunk_coord: tuple[int, int]):
        """
        高效地创建或更新一个Chunk的实例VBO。
        - 如果Chunk首次出现，则为其创建并分配GPU资源（VAO和VBO）。
        - 如果Chunk已存在，则仅使用glBufferSubData更新其VBO内容。
        - 根据设计，GPU资源一旦创建将永不销死。
        """
        
        # 步骤1：准备当前帧需要渲染的实例数据
        chunk_data = self.chunk_engine.get_chunk_data(chunk_coord)
        instance_data = np.array(self._generate_chunk_instance_data(chunk_coord, chunk_data), dtype=np.float32)
        
        # 步骤2：检查这个Chunk的GPU资源是否已经创建
        if chunk_coord not in self.chunk_buffers:
            # --- Chunk首次出现，执行“创建”逻辑 ---
            # 这个代码块只会在一个新区块首次被绘制时执行一次。
            
            # 定义实例数据相关的常量
            # 因为大小固定，我们可以直接使用当前生成的数据大小
            buffer_size = instance_data.nbytes
            stride = (2 + self.config.hex_map_engine.data_dimensions) * sizeof(GLfloat)
    
            # 创建VAO和VBO
            filled_vao = glGenVertexArrays(1)
            outline_vao = glGenVertexArrays(1)
            instance_vbo = glGenBuffers(1)
    
            # ---- 设置 "filled_vao" ----
            glBindVertexArray(filled_vao)
            
            # 绑定六边形形状的顶点VBO
            glBindBuffer(GL_ARRAY_BUFFER, self.shader_manager.get_vbo("hex_filled"))
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            
            # 绑定实例数据VBO（包含所有六边形的位置和颜色）
            glBindBuffer(GL_ARRAY_BUFFER, instance_vbo)
            # **关键点1：分配并上传初始数据**
            # 使用 GL_DYNAMIC_DRAW 表示我们期望这个缓冲区的内容会频繁更新。
            glBufferData(GL_ARRAY_BUFFER, buffer_size, instance_data, GL_DYNAMIC_DRAW)
            
            # 设置实例属性指针 (位置和颜色)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            glEnableVertexAttribArray(1)
            glVertexAttribDivisor(1, 1) # 每1个实例更新一次此属性
            
            glVertexAttribPointer(2, self.config.hex_map_engine.data_dimensions, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * sizeof(GLfloat)))
            glEnableVertexAttribArray(2)
            glVertexAttribDivisor(2, 1)
    
            # ---- 设置 "outline_vao" (与上面类似) ----
            glBindVertexArray(outline_vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.shader_manager.get_vbo("hex_outline"))
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            
            glBindBuffer(GL_ARRAY_BUFFER, instance_vbo) # 复用同一个实例VBO
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            glEnableVertexAttribArray(1)
            glVertexAttribDivisor(1, 1)
            
            # 将新创建的GPU对象句柄保存起来，供后续更新使用
            self.chunk_buffers[chunk_coord] = {
                "filled_vao": filled_vao,
                "outline_vao": outline_vao,
                "instance_vbo": instance_vbo
            }
            
            # 解绑所有对象，这是一个好习惯
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glBindVertexArray(0)
            
            # 注意：由于我们已经在创建时上传了数据，所以对于新区块无需再次更新。
            # 函数到此可以直接结束。
            return
    
        # --- 如果代码执行到这里，说明Chunk已经存在，执行“更新”逻辑 ---
        
        # **关键点2：高效更新缓冲区内容**
        # 从字典中获取已存在的VBO ID
        instance_vbo_id = self.chunk_buffers[chunk_coord]["instance_vbo"]
        glBindBuffer(GL_ARRAY_BUFFER, instance_vbo_id)
        
        # 使用 glBufferSubData 仅更新VBO中的数据，这非常快。
        # 它的作用就像内存中的 memcpy。
        glBufferSubData(GL_ARRAY_BUFFER, 0, instance_data.nbytes, instance_data)
    
        # 解绑，防止意外修改
        glBindBuffer(GL_ARRAY_BUFFER, 0)
    
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
        self.transform_changed.emit(self.camera.pos.x(), self.camera.pos.y(), self.camera.zoom)
        
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
        self.transform_changed.emit(self.camera.pos.x(), self.camera.pos.y(), self.camera.zoom)
