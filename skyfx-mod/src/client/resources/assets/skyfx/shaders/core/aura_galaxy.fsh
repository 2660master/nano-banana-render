#version 330

#moj_import <minecraft:dynamictransforms.glsl>
#moj_import <skyfx:skyfx_common.glsl>
#moj_import <skyfx:aura_galaxy.glsl>

in vec3 viewDir;

out vec4 fragColor;

// ColorModulator = (time, edge colour r, g, b)
void main() {
    fragColor = skyfx_galaxyAura(normalize(viewDir), ColorModulator.x, ColorModulator.yzw);
}
