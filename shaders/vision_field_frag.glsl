#version 420

const float MaxDist = 16;
const float PI =  6.28318;

uniform vec2 playerPos;
uniform vec2 screenPos;

in vec4 gl_FragCoord;

out vec4 fragColor;

void main() {
    vec2 pos = gl_FragCoord.xy + screenPos + vec2(0, 84);
	float x = floor(pos.x/96 + pos.y/48);
	float y = floor(pos.y/48 - pos.x/96);

    vec2 diff = playerPos - vec2(x, y);
    float dist = min(length(diff) / MaxDist, 1);
    float mathed_dist = clamp(cos(dist * PI), 0, 1);
    fragColor = vec4(vec3(-mathed_dist), dist);
}