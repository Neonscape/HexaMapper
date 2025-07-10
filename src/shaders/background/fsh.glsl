#version 330 core

// fragment shader for 2D background

in vec4 vColor; // Interpolated color from vertex shader
out vec4 FragColor;

void main()
{
    FragColor = vColor;
}