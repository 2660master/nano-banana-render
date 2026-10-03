#version 330

#moj_import <minecraft:dynamictransforms.glsl>

// SkyFX palm tree block aura: the five neon palm trees drift slowly across every face of the block, over a dark,
// see-through backdrop tinted with the aura colour. ColorModulator = (time, aura colour r, g, b).

uniform sampler2D Sampler0;

in vec2 texCoord0;

out vec4 fragColor;

void main() {
    float t = ColorModulator.x;
    vec3 tint = ColorModulator.yzw;
    vec2 uv = texCoord0 + vec2(t * 0.03, 0.0);
    vec3 palms = texture(Sampler0, uv).rgb;
    float glow = max(palms.r, max(palms.g, palms.b));
    // soft sunset backdrop: a hint of the aura colour at the top, dark at the bottom (v = 0 is the top)
    vec3 back = mix(tint * 0.35 + vec3(0.06, 0.02, 0.10), vec3(0.03, 0.02, 0.08), smoothstep(0.0, 1.0, texCoord0.y));
    fragColor = vec4(back + palms * 1.15, clamp(0.45 + glow * 0.6, 0.0, 0.95));
}
