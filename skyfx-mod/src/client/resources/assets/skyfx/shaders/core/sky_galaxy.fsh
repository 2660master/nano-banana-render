#version 330

#moj_import <minecraft:dynamictransforms.glsl>
#moj_import <skyfx:skyfx_common.glsl>
#moj_import <skyfx:sky_galaxy.glsl>

in vec3 skyDir;

out vec4 fragColor;

// SkyFX passes its parameters through the DynamicTransforms block:
// ColorModulator = (animation time in seconds, brightness, palette, unused)
void main() {
    vec3 dir = normalize(skyDir);
    vec3 col = skyfx_galaxy(dir, ColorModulator.x) * ColorModulator.y;
    fragColor = vec4(skyfx_tonemap(col), 1.0);
}
