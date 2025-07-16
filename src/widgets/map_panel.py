from qtpy.QtOpenGLWidgets import QOpenGLWidget
from qtpy.QtGui import QSurfaceFormat
from qtpy.QtCore import QPointF
from OpenGL.GL import *
import numpy as np
from modules.map_engine import MapEngine2D
from modules.event_handlers import MapPanel2DEventHandler
from modules.map_helpers import global_coord_to_chunk_coord, global_pos_to_global_coord, get_center_position_from_global_coord


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
        format.setSamples(4) # Enable MSAA
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

    def export_to_image(self):
        self.makeCurrent()  # Ensure OpenGL context is current
        try:
            # Save original viewport
            original_viewport = glGetIntegerv(GL_VIEWPORT)
            
            hex_radius = self.engine.config.hex_map_engine.hex_radius
            chunk_size = self.engine.config.hex_map_engine.chunk_size
            
            # ----------------------------------------------------------------------
            # 1. Decide which cells have to appear in the image
            # ----------------------------------------------------------------------
            hex_height = hex_radius * np.sqrt(3.0)          # distance between two rows
            hex_width  = 2.0 * hex_radius                     # distance between two columns
            
            cells = []
            
            min_x_world = None
            max_x_world = None
            min_y_world = None
            max_y_world = None

            if not self.engine.chunk_engine.modified_cells:
                # No edits – export the current viewport
                tl_world = self.engine.screen_to_world((0, 0))
                br_world = self.engine.screen_to_world((self.width(), self.height()))
                
                min_x_world, min_y_world = tl_world.x(), tl_world.y()
                max_x_world, max_y_world = br_world.x(), br_world.y()
                
                min_x_world, max_x_world = sorted((min_x_world, max_x_world))
                min_y_world, max_y_world = sorted((min_y_world, max_y_world))

                min_gx, min_gy = global_pos_to_global_coord(tl_world, hex_radius)
                max_gx, max_gy = global_pos_to_global_coord(br_world, hex_radius)

                # Ensure correct ordering
                min_gx, max_gx = sorted((min_gx, max_gx))
                min_gy, max_gy = sorted((min_gy, max_gy))

                _cells = [(x, y)
                         for x in range(min_gx - 1, max_gx + 2)
                         for y in range(min_gy - 1, max_gy + 2)]
                
                for cell in _cells:
                    pos = get_center_position_from_global_coord(cell, hex_radius)
                    if (min_x_world <= pos[0] <= max_x_world and
                            min_y_world <= pos[1] <= max_y_world):
                        cells.append(cell)
                
            else:
                gpos = [get_center_position_from_global_coord((c[0], c[1]), hex_radius) for c in self.engine.chunk_engine.modified_cells]
                min_x_world = min(c[0] for c in gpos)
                max_x_world = max(c[0] for c in gpos)
                min_y_world = min(c[1] for c in gpos)
                max_y_world = max(c[1] for c in gpos)
                
                min_x_world, max_x_world = sorted((min_x_world, max_x_world))
                min_y_world, max_y_world = sorted((min_y_world, max_y_world))
                
                min_gx, min_gy = global_pos_to_global_coord(QPointF(min_x_world, min_y_world), hex_radius)
                max_gx, max_gy = global_pos_to_global_coord(QPointF(max_x_world, max_y_world), hex_radius)
                
                min_gx, max_gx = sorted((min_gx, max_gx))
                min_gy, max_gy = sorted((min_gy, max_gy))
                
                _cells = [(x, y)
                         for x in range(min_gx - 1, max_gx + 2)
                         for y in range(min_gy - 1, max_gy + 2)]
                
                for cell in _cells:
                    pos = get_center_position_from_global_coord(cell, hex_radius)
                    if (min_x_world <= pos[0] <= max_x_world and
                            min_y_world <= pos[1] <= max_y_world):
                        cells.append(cell)

            # ----------------------------------------------------------------------
            # 3. Determine final image size
            # ----------------------------------------------------------------------
            world_width  = max_x_world - min_x_world
            world_height = max_y_world - min_y_world

            scale_factor = min(1.0, 100.0 / max(world_width, world_height))

            max_cell_size = 40
            min_cell_size = 15
            pixel_per_hex = max(min_cell_size,
                                min(max_cell_size, int(max_cell_size * scale_factor)))

            pixels_per_world_unit = pixel_per_hex / hex_width
            width  = max(1, int(world_width  * pixels_per_world_unit))
            height = max(1, int(world_height * pixels_per_world_unit))
            
            fbo = glGenFramebuffers(1)
            texture = glGenTextures(1)
            
            try:
                glBindFramebuffer(GL_FRAMEBUFFER, fbo)
                glBindTexture(GL_TEXTURE_2D, texture)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0)

                if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
                    raise RuntimeError("Framebuffer is not complete!")

                glViewport(0, 0, width, height)
                
                # Clear to transparent instead of using gradient background
                glClearColor(0, 0, 0, 0)
                glClear(GL_COLOR_BUFFER_BIT)

                # Create projection matrix for the export region
                proj_mat = self._create_ortho_matrix(
                    min_x_world, max_x_world, 
                    min_y_world, max_y_world, 
                    -1, 1
                )
            
                view_mat = np.identity(4, dtype=np.float32)
                
                chunks_to_render = set()
                chunk_x_min = float('inf')
                chunk_x_max = -float('inf')
                chunk_y_min = float('inf')
                chunk_y_max = -float('inf')
                for x, y in cells:
                    chunk_x, chunk_y, _, _ = global_coord_to_chunk_coord(
                        (x, y), self.engine.config.hex_map_engine.chunk_size
                    )
                    if chunk_x < chunk_x_min: chunk_x_min = chunk_x
                    if chunk_x > chunk_x_max: chunk_x_max = chunk_x
                    if chunk_y < chunk_y_min: chunk_y_min = chunk_y
                    if chunk_y > chunk_y_max: chunk_y_max = chunk_y
                    
                chunk_x_min = int(chunk_x_min)
                chunk_x_max = int(chunk_x_max)
                chunk_y_min = int(chunk_y_min)
                chunk_y_max = int(chunk_y_max)
                
                for chunk_x in range(chunk_x_min, chunk_x_max + 1):
                    for chunk_y in range(chunk_y_min, chunk_y_max + 1):
                        chunks_to_render.add((chunk_x, chunk_y))
                        if (chunk_x, chunk_y) not in self.engine.chunk_buffers:
                            self.engine._update_chunk_instance_buffer((chunk_x, chunk_y))
                
                # Apply the view matrix to center on export region
                self.engine.render_scene(proj_mat, view_mat, chunks_to_render)

                pixels = glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
            finally:
                # Clean up resources
                glBindFramebuffer(GL_FRAMEBUFFER, 0)
                glDeleteFramebuffers(1, [fbo])
                glDeleteTextures(1, [texture])
            
            # Restore original viewport
            glViewport(*original_viewport)
            
            return pixels, width, height
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Export failed: {str(e)}")
        finally:
            self.doneCurrent()  # Release OpenGL context

    def _create_ortho_matrix(self, left, right, bottom, top, near, far):
        return np.array([
            [2 / (right - left), 0, 0, -(right + left) / (right - left)],
            [0, 2 / (top - bottom), 0, -(top + bottom) / (top - bottom)],
            [0, 0, -2 / (far - near), -(far + near) / (far - near)],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        