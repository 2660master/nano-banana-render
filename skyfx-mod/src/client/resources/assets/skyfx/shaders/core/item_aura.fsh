#version 330

#moj_import <minecraft:dynamictransforms.glsl>
#moj_import <minecraft:globals.glsl>

// SkyFX item aura: InSampler holds only the held item(s). Everything just outside their silhouette gets a crisp
// coloured outline plus a soft glow. ColorModulator = (colour, strength), ModelOffset = (outline px, glow px, time).

uniform sampler2D InSampler;

in vec2 texCoord;

out vec4 fragColor;

float coverage(vec2 uv) {
    vec4 c = texture(InSampler, uv);
    return max(c.a, step(0.004, max(c.r, max(c.g, c.b))));
}

void main() {
    if (coverage(texCoord) > 0.5) {
        discard;
    }
    vec2 px = 1.0 / ScreenSize;
    float width = ModelOffset.x;
    float glow = ModelOffset.y;
    float edge = 0.0;
    float soft = 0.0;
    for (int i = 0; i < 24; i++) {
        float a = float(i) * 0.26179939;
        vec2 d = vec2(cos(a), sin(a)) * px;
        edge = max(edge, coverage(texCoord + d * width));
        edge = max(edge, coverage(texCoord + d * width * 0.5));
        soft += coverage(texCoord + d * (width + glow * 0.45)) * 0.6 + coverage(texCoord + d * (width + glow)) * 0.4;
    }
    soft /= 24.0;
    float alpha = max(edge, clamp(soft * 2.4, 0.0, 1.0) * 0.7) * ColorModulator.a;
    if (alpha <= 0.002) {
        discard;
    }
    vec3 color = mix(ColorModulator.rgb, vec3(1.0), edge * 0.12);
    fragColor = vec4(color, alpha);
}
