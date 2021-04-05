#version 330

uniform vec2 screen_pos;

in vec4 gl_FragCoord;

out vec4 fragColor;

void main() {
	vec2 pos = gl_FragCoord.xy + screen_pos + vec2(0, 84);
	float x = floor(pos.x/96 + pos.y/48);
	float y = floor(pos.y/48 - pos.x/96);

	vec2 XYColorPos = vec2(x, y)/vec2(19);
	if (0 <= x && x <= 19 && 0 <= y && y<=19)
	{
		fragColor = vec4(XYColorPos, 0, 0.5);
	}
	else
	{
		fragColor = vec4(0);
	}

}
