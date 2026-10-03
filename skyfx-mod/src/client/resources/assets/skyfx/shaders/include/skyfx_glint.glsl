// SkyFX glint colours (needs skyfx_common.glsl). Shared by the glint core-shader overrides and the HTML preview.
// texColor: sample of the vanilla glint texture, uv: the scrolling glint texture coordinate,
// gameTime: the Globals GameTime uniform (0..1 every 24000 ticks).

vec3 skyfx_rainbowGlint(vec3 texColor, vec2 uv, float gameTime) {
	float strength = max(texColor.r, max(texColor.g, texColor.b));
	// Item glint coordinates only cover a small patch of the texture atlas (about 0.1 - 0.25 units),
	// so a high spatial frequency is needed to get the whole rainbow across one item.
	// 160 colour cycles per in-game day keeps the hue continuous when GameTime wraps around.
	float hue = fract((uv.x + uv.y) * 4.0 + gameTime * 160.0);
	vec3 rainbow = skyfx_hsv2rgb(vec3(hue, 0.85, 1.0));
	return rainbow * strength * 1.35;
}
