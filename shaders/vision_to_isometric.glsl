#version 330

#define N = 50

uniform vec4 screen_pos_resolution;
uniform sampler2D vision_tiles;

in vec4 gl_FragCoord;
in vec2 frag_uv;

out vec4 fragColor;

void main() {
	vec2 pos = floor((gl_FragCoord.xy + screen_pos_resolution.xy + vec2(0, 84))/3)*3;
	float x = pos.x/96 - pos.y/48 + screen_pos_resolution.z/2 + 1;
	float y = - pos.x/96- pos.y/48 + screen_pos_resolution.w/2 + 1;

	vec2 euclideanPos = vec2(x, y)/screen_pos_resolution.zw;
	vec4 vision = texelFetch(vision_tiles, ivec2(x, y), 0);
	fragColor = vec4(vec3(0), 1);
	if (vision.x > 0)
	{
		fragColor = vec4(0, 0, 0, vision.g*0.8);
	}
}