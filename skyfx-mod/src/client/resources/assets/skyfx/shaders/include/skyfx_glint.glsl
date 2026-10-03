// SkyFX glint colours (needs skyfx_common.glsl). Shared by the glint core-shader overrides and the HTML preview.
// texColor: sample of the vanilla glint texture, uv: the scrolling glint texture coordinate,
// gameTime: the Globals GameTime uniform (0..1 every 24000 ticks).

vec3 skyfx_rainbowGlint(vec3 texColor, vec2 uv, float gameTime) {
	float strength = max(texColor.r, max(texColor.g, texColor.b));
	// 160 colour cycles per in-game day keeps the hue continuous when GameTime wraps around
	float hue = fract(uv.x * 0.35 + uv.y * 0.20 + gameTime * 160.0);
	vec3 rainbow = skyfx_hsv2rgb(vec3(hue, 0.85, 1.0));
	return rainbow * strength * 1.35;
}
