import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# Initialize camera settings
offset_x, offset_y = 0.0, 0.0
last_x, last_y = 0, 0
dragging = False
window_size = (800, 600)
world_height = 10.0  # Fixed world height visible in the viewport

def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Black background
    glEnable(GL_DEPTH_TEST)
    update_projection()

def update_projection():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    
    aspect_ratio = window_size[0] / window_size[1]
    world_width = world_height * aspect_ratio
    
    # Set orthogonal projection centered at (offset_x, offset_y)
    left = offset_x - world_width / 2
    right = offset_x + world_width / 2
    bottom = offset_y - world_height / 2
    top = offset_y + world_height / 2
    
    glOrtho(left, right, bottom, top, -10.0, 10.0)
    glMatrixMode(GL_MODELVIEW)

def draw_grid():
    glColor3f(0.3, 0.3, 0.3)  # Grid color (dark gray)
    glLineWidth(1.0)
    
    # Draw grid lines
    glBegin(GL_LINES)
    for x in range(-10, 11, 1):
        glVertex3f(x, -10, 0)
        glVertex3f(x, 10, 0)
    for y in range(-10, 11, 1):
        glVertex3f(-10, y, 0)
        glVertex3f(10, y, 0)
    glEnd()
    
    # Draw thicker axes
    glLineWidth(2.0)
    glBegin(GL_LINES)
    # X-axis (red)
    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(-10, 0, 0)
    glVertex3f(10, 0, 0)
    # Y-axis (green)
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(0, -10, 0)
    glVertex3f(0, 10, 0)
    glEnd()

def main():
    global offset_x, offset_y, last_x, last_y, dragging, window_size
    
    pygame.init()
    pygame.display.set_mode(window_size, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("2D Orthogonal Camera Drag")
    
    init()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            
            # Handle mouse events for dragging
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    dragging = True
                    last_x, last_y = event.pos
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False
            
            elif event.type == pygame.MOUSEMOTION and dragging:
                x, y = event.pos
                # Convert mouse movement to world coordinates
                aspect_ratio = window_size[0] / window_size[1]
                world_width = world_height * aspect_ratio
                dx = (x - last_x) * (world_width / window_size[0])
                dy = -(y - last_y) * (world_height / window_size[1])  # Invert Y axis
                
                offset_x -= dx
                offset_y -= dy
                last_x, last_y = x, y
                update_projection()
        
        # Clear buffers and draw scene
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        draw_grid()
        pygame.display.flip()
        pygame.time.wait(10)

if __name__ == "__main__":
    main()