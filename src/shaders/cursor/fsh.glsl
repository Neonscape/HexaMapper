#version 450 core

out vec4 FragColor;

in vec2 v_uv;

uniform vec4 color;
uniform float thickness;

void main()
{
    float dist = length(v_uv);
    if (dist > 1.0 || dist < 1.0 - thickness) {
        discard;
    }
    FragColor = color;
}
