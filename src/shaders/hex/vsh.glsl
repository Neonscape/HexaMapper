#version 330 core

// vertex shader for 2D hexagon map view

layout (location = 0) in vec2 aPos; 
layout (location = 1) in vec2 aInstancePos;
layout (location = 2) in vec4 aInstanceColor;

out vec4 vColor;

uniform mat4 projection;
uniform mat4 view;
uniform vec4 color;  // Added color uniform
uniform int drawMode;

const int DRAW_FILLED = 0;
const int DRAW_OUTLINE = 1;

void main()
{
    gl_Position = projection * view * vec4(aInstancePos + aPos, 0.0, 1.0);
    
    // Use instance color for filled hexagons, uniform for outlines
    vColor = (drawMode == DRAW_FILLED) ? aInstanceColor : color;
}