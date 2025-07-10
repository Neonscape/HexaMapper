#version 330 core

// vertex shader for 2D map background

// now uses vertical gradient by default

layout (location = 0) in vec2 aPos; // Vertex position (screen space)
out vec4 vColor; // Output color to fragment shader

uniform vec4 topColor;
uniform vec4 bottomColor;
uniform float viewportHeight; // Height of the viewport in pixels

void main()
{
    // Map the Y position (0 to viewportHeight) to a 0-1 range for gradient interpolation
    // If aPos.y is 0 (bottom), gradient_factor is 0. If aPos.y is viewportHeight (top), gradient_factor is 1.
    float gradient_factor = aPos.y / viewportHeight; 
    vColor = mix(bottomColor, topColor, gradient_factor);
    gl_Position = vec4(aPos.x * 2.0 / viewportHeight - 1.0, 
                       aPos.y * 2.0 / viewportHeight - 1.0, 0.0, 1.0); // Directly to clip space
}