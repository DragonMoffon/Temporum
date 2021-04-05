#version 330

in vec2 in_pos;

void main() {
    // Set the position. (x, y, z, w)
    gl_Position = vec4(in_pos, 0, 1);
}
