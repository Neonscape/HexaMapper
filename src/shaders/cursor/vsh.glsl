#version 450 core

layout (location = 0) in vec2 aPos;

uniform mat4 projection;
uniform mat4 view;

uniform vec2 center_pos;
uniform float radius;

out vec2 v_uv;

void main()
{
    v_uv = aPos;
    vec2 world_pos = aPos * radius + center_pos;
    gl_Position = projection * view * vec4(world_pos, 0.0, 1.0);
}
