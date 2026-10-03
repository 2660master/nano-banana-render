#version 330

#moj_import <minecraft:fog.glsl>
#moj_import <minecraft:globals.glsl>
#moj_import <minecraft:dynamictransforms.glsl>
#moj_import <skyfx:skyfx_common.glsl>
#moj_import <skyfx:skyfx_glint.glsl>

// SkyFX rainbow glint: the vanilla glint shader, recoloured with a scrolling rainbow.

uniform sampler2D Sampler0;

in float sphericalVertexDistance;
in float cylindricalVertexDistance;
in vec2 texCoord0;

out vec4 fragColor;

void main() {
    vec4 color = texture(Sampler0, texCoord0) * ColorModulator;
    if (color.a < 0.1) {
        discard;
    }
    float fade = (1.0f - total_fog_value(sphericalVertexDistance, cylindricalVertexDistance, FogEnvironmentalStart, FogEnvironmentalEnd, FogRenderDistanceStart, FogRenderDistanceEnd)) * GlintAlpha;
    vec3 rainbow = skyfx_rainbowGlint(color.rgb, texCoord0, GameTime);
    fragColor = vec4(rainbow * fade, color.a);
}
