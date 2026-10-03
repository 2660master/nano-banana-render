// SkyFX galaxy block aura: the block becomes a translucent window into deep space (needs skyfx_common.glsl).
// dir is the view direction through the pixel, so the star field stays put like a portal.

vec4 skyfx_galaxyAura(vec3 dir, float t, vec3 tint) {
	vec3 d = skyfx_rotY(dir, t * 0.03);
	vec3 col = vec3(0.025, 0.012, 0.07);
	float n = skyfx_fbm3(d * 3.2 + vec3(0.0, t * 0.04, 0.0), 5);
	float wisps = pow(1.0 - abs(2.0 * skyfx_fbm3(d * 5.0 - vec3(t * 0.03), 4) - 1.0), 5.0);
	col += mix(vec3(0.18, 0.06, 0.38), vec3(0.20, 0.32, 0.85), smoothstep(0.35, 0.75, n)) * smoothstep(0.3, 0.8, n) * 0.9;
	col += mix(tint, vec3(0.85, 0.55, 1.0), 0.5) * wisps * 0.35;
	col += skyfx_starLayer(d, 70.0, 0.35, t, 1.4);
	col += skyfx_starLayer(skyfx_rotX(d, 1.3), 160.0, 0.45, t * 1.4, 1.0);
	col += skyfx_starLayer(skyfx_rotY(d, 2.1), 340.0, 0.5, t * 0.8, 0.6);
	return vec4(skyfx_tonemap(col), 0.86);
}
