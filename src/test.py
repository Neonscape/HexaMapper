import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QMouseEvent, QWheelEvent

# Make sure to install dependencies:
# pip install PyQt6 PyQt6-OpenGL PyOpenGL numpy

from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

# --- Constants ---
CHUNK_SIZE = 16  # Each chunk is a 16x16 grid of hexagons
HEX_VERTEX_COUNT = 7 # 6 vertices for the hexagon + 1 center for a triangle fan
DATA_DIMENSIONS = 4 # RGBA color

# --- GLSL Shaders (Updated for Instancing) ---
VERTEX_SHADER = """
#version 330 core
// Vertex data for a single hexagon at origin (0,0)
layout (location = 0) in vec2 aPos; 

// Per-instance data
layout (location = 1) in vec2 aInstancePos;   // Center position of the hexagon
layout (location = 2) in vec4 aInstanceColor; // Color of the hexagon

out vec4 vColor;

uniform mat4 projection;
uniform mat4 view;

void main()
{
    // Final position is the instance's center position + the vertex's offset from the center
    gl_Position = projection * view * vec4(aInstancePos + aPos, 0.0, 1.0);
    vColor = aInstanceColor;
}
"""

FRAGMENT_SHADER = """
#version 330 core
out vec4 FragColor;
in vec4 vColor;

void main()
{
    FragColor = vColor;
}
"""

class HexChunkManager:
    """
    Manages the world data on the Python side.
    This is the "Model" in a Model-View-Controller pattern.
    It knows nothing about OpenGL, only about the grid data.
    """
    def __init__(self):
        self.chunks = {}
        self.dirty_chunks = set()

    def _get_or_create_chunk(self, chunk_coord):
        if chunk_coord not in self.chunks:
            new_chunk = np.full((CHUNK_SIZE, CHUNK_SIZE, DATA_DIMENSIONS), 
                               [0.2, 0.2, 0.2, 1.0], dtype=np.float32)
            self.chunks[chunk_coord] = new_chunk
            # Note: We don't mark it dirty here automatically. The renderer will decide
            # when to build the buffer for the first time.
        return self.chunks[chunk_coord]

    def set_cell_data(self, global_x, global_y, data):
        chunk_coord = (global_x // CHUNK_SIZE, global_y // CHUNK_SIZE)
        local_x = global_x % CHUNK_SIZE
        local_y = global_y % CHUNK_SIZE
        chunk = self._get_or_create_chunk(chunk_coord)
        chunk[local_x, local_y] = data
        self.dirty_chunks.add(chunk_coord)

    def get_chunk_data(self, chunk_coord):
        return self._get_or_create_chunk(chunk_coord)

    def get_and_clear_dirty_chunks(self):
        dirty = list(self.dirty_chunks)
        self.dirty_chunks.clear()
        return dirty

class OpenGLWidget(QOpenGLWidget):
    """
    The main rendering widget, now using instanced rendering.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_manager = HexChunkManager()
        
        # --- Rendering State ---
        self.shader_program = None
        # VBO for a single hexagon's geometry (shared by all instances)
        self.hex_geometry_vbo = None 
        # Dict mapping chunk_coord -> (instance_VBO_id, VAO_id)
        self.chunk_buffers = {} 
        
        # --- Camera State ---
        self.camera_pos = QPointF(0.0, 0.0)
        self.zoom_level = 0.1
        
        # --- Mouse Interaction State ---
        self.last_mouse_pos = QPointF()

        # --- Hexagon Geometry ---
        self.HEX_WIDTH = np.sqrt(3)
        self.HEX_HEIGHT = 2.0
        
    def initializeGL(self):
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        self.shader_program = compileProgram(
            compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
            compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        )
        
        self._create_shared_hex_geometry()

        # This will mark the initial chunks as dirty, causing their buffers to be built on the first frame.
        for x in range(-5, 5):
            self.data_manager.set_cell_data(x, 0, [1, 0, 0, 1])
            self.data_manager.set_cell_data(0, x, [0, 1, 0, 1])

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.shader_program)
        
        # First, process any chunks that were explicitly modified (e.g., by painting)
        dirty_chunks = self.data_manager.get_and_clear_dirty_chunks()
        for chunk_coord in dirty_chunks:
            self._update_chunk_instance_buffer(chunk_coord)

        # Set up camera matrices
        proj_matrix = self._create_projection_matrix()
        view_matrix = self._create_view_matrix()
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, proj_matrix)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view_matrix)
        
        # Determine which chunks are visible
        visible_chunks = self._get_visible_chunk_coords()
        for chunk_coord in visible_chunks:
            # *** FIX: If a chunk is visible but doesn't have a buffer (i.e., it's a default
            # chunk we haven't processed yet), create its buffer on-the-fly.
            if chunk_coord not in self.chunk_buffers:
                self._update_chunk_instance_buffer(chunk_coord)
            
            # Now that we're sure the buffer exists, bind its VAO and draw.
            vao = self.chunk_buffers[chunk_coord][1]
            glBindVertexArray(vao)
            # Draw all hexagons in the chunk with a single instanced draw call
            glDrawArraysInstanced(GL_TRIANGLE_FAN, 0, HEX_VERTEX_COUNT, CHUNK_SIZE * CHUNK_SIZE)
            glBindVertexArray(0)

    def _create_shared_hex_geometry(self):
        """Creates a VBO for a single hexagon mesh at origin (0,0)."""
        unit_hex_vertices = [(0.0, 0.0)] # Center vertex for triangle fan
        for i in range(6):
            angle_rad = np.pi / 180 * (60 * i)
            unit_hex_vertices.append((np.cos(angle_rad), np.sin(angle_rad)))
        
        geometry_data = np.array(unit_hex_vertices, dtype=np.float32)
        
        self.hex_geometry_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.hex_geometry_vbo)
        glBufferData(GL_ARRAY_BUFFER, geometry_data.nbytes, geometry_data, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)


    def _update_chunk_instance_buffer(self, chunk_coord):
        """Generates instance data (pos, color) for a chunk and uploads it to a VBO."""
        print(f"update chunk instance buffer for coord {chunk_coord}")
        if chunk_coord in self.chunk_buffers:
            instance_vbo_id, vao_id = self.chunk_buffers[chunk_coord]
            glDeleteBuffers(1, [instance_vbo_id])
            glDeleteVertexArrays(1, [vao_id])

        chunk_data = self.data_manager.get_chunk_data(chunk_coord)
        instance_data = self._generate_chunk_instance_data(chunk_coord, chunk_data)
        instance_data_np = np.array(instance_data, dtype=np.float32)
        
        # Create VAO and the per-chunk instance VBO
        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)
        
        # 1. Bind the shared hexagon geometry VBO
        glBindBuffer(GL_ARRAY_BUFFER, self.hex_geometry_vbo)
        # Vertex attribute for position offset (aPos)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # 2. Create and bind the new instance data VBO
        instance_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, instance_vbo)
        glBufferData(GL_ARRAY_BUFFER, instance_data_np.nbytes, instance_data_np, GL_STATIC_DRAW)
        
        # Instance attribute for center position (aInstancePos)
        # Stride is 6 floats (pos_x, pos_y, r, g, b, a)
        stride = (2 + 4) * sizeof(GLfloat)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        # Instance attribute for color (aInstanceColor)
        glVertexAttribPointer(2, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * sizeof(GLfloat)))
        glEnableVertexAttribArray(2)

        # 3. Tell OpenGL this is per-instance data
        glVertexAttribDivisor(1, 1) # Update aInstancePos once per instance
        glVertexAttribDivisor(2, 1) # Update aInstanceColor once per instance
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        
        print(f"created chunk buffer for coord {chunk_coord}")
        
        self.chunk_buffers[chunk_coord] = (instance_vbo, vao)

    def _generate_chunk_instance_data(self, chunk_coord, chunk_data):
        """Creates a list of instance data [pos_x, pos_y, r, g, b, a] for a chunk."""
        instance_data = []
        chunk_origin_x = chunk_coord[0] * CHUNK_SIZE
        chunk_origin_y = chunk_coord[1] * CHUNK_SIZE

        for lx in range(CHUNK_SIZE):
            for ly in range(CHUNK_SIZE):
                global_x = chunk_origin_x + lx
                global_y = chunk_origin_y + ly
                
                center_x = global_x * self.HEX_WIDTH * 0.75
                center_y = global_y * self.HEX_HEIGHT + (global_x % 2) * (self.HEX_HEIGHT / 2)
                color = chunk_data[lx, ly]
                
                instance_data.extend([center_x, center_y, *color])
        return instance_data

    # --- Camera and Coordinate Transformation (Unchanged) ---
    def _create_projection_matrix(self):
        w, h = self.width(), self.height()
        aspect = w / h if h > 0 else 1
        left, right = -aspect / self.zoom_level, aspect / self.zoom_level
        bottom, top = -1.0 / self.zoom_level, 1.0 / self.zoom_level
        return np.array([
            [2.0 / (right - left), 0, 0, -(right + left) / (right - left)],
            [0, 2.0 / (top - bottom), 0, -(top + bottom) / (top - bottom)],
            [0, 0, -1, 0], [0, 0, 0, 1]
        ], dtype=np.float32)

    def _create_view_matrix(self):
        return np.array([
            [1, 0, 0, -self.camera_pos.x()],
            [0, 1, 0, -self.camera_pos.y()],
            [0, 0, 1, 0], [0, 0, 0, 1]
        ], dtype=np.float32)

    def _screen_to_world(self, screen_pos):
        w, h = self.width(), self.height()
        ndc_x = (2.0 * screen_pos.x() / w) - 1.0
        ndc_y = 1.0 - (2.0 * screen_pos.y() / h)
        proj, view = self._create_projection_matrix(), self._create_view_matrix()
        inv_proj, inv_view = np.linalg.inv(proj), np.linalg.inv(view)
        world_pos = inv_view @ inv_proj @ np.array([ndc_x, ndc_y, 0, 1])
        return QPointF(world_pos[0], world_pos[1])

    def _world_to_grid(self, world_pos):
        approx_x = round(world_pos.x() / (self.HEX_WIDTH * 0.75))
        approx_y_offset = (approx_x % 2) * (self.HEX_HEIGHT / 2)
        approx_y = round((world_pos.y() - approx_y_offset) / self.HEX_HEIGHT)
        return int(approx_x), int(approx_y)

    def _get_visible_chunk_coords(self):
        top_left_world = self._screen_to_world(QPointF(0, 0))
        bottom_right_world = self._screen_to_world(QPointF(self.width(), self.height()))
        min_gx, min_gy = self._world_to_grid(top_left_world)
        max_gx, max_gy = self._world_to_grid(bottom_right_world)
        min_cx, max_cx = (min_gx - 1) // CHUNK_SIZE, (max_gx + 1) // CHUNK_SIZE
        min_cy, max_cy = (min_gy - 1) // CHUNK_SIZE, (max_gy + 1) // CHUNK_SIZE
        visible = set()
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                visible.add((cx, cy))
        return visible

    # --- User Input Events (Unchanged) ---
    def mousePressEvent(self, event: QMouseEvent):
        self.last_mouse_pos = event.position()

    def mouseMoveEvent(self, event: QMouseEvent):
        delta = event.position() - self.last_mouse_pos
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.camera_pos -= QPointF(delta.x() / (self.width() / 2 * self.zoom_level),
                                     -delta.y() / (self.height() / 2 * self.zoom_level))
            self.update()
        elif event.buttons() & Qt.MouseButton.RightButton:
            world_pos = self._screen_to_world(event.position())
            grid_x, grid_y = self._world_to_grid(world_pos)
            random_color = np.random.rand(4).astype(np.float32)
            random_color[3] = 1.0
            self.data_manager.set_cell_data(grid_x, grid_y, random_color)
            self.update()
        self.last_mouse_pos = event.position()

    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
        self.zoom_level = max(0.01, min(self.zoom_level, 5.0))
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyOpenGL Infinite Hex Grid Demo (Instanced)")
        self.setGeometry(100, 100, 1280, 720)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.opengl_widget = OpenGLWidget()
        layout.addWidget(self.opengl_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
