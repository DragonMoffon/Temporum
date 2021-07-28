#version 330

uniform sampler2D vision_map;
uniform vec4 cast_pos_resoultion;

in vec2 frag_uv;

out vec4 frag_color;

void main() {
    vec4 location = texture(vision_map, frag_uv);
    vec2 pos = cast_pos_resoultion.xy/cast_pos_resoultion.zw;
    if (location.r + location.g + location.b + location.a == 0)
    {
        frag_color = vec4(1);
    }
    else if (pos == frag_uv)
    {
        frag_color = vec4(pos, 0, 1);
    }
    else
    {
        frag_color = vec4(vec3(1), 0);
    }
}
