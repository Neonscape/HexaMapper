#version 330 core

// fragment shader for 2D hexagon map view

out vec4 FragColor;
in vec4 vColor;

void main()
{
    FragColor = vColor;
}