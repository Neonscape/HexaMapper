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