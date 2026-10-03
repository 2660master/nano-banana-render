// SkyFX "Noorderlicht" - a polar night with swirling aurora curtains (needs skyfx_common.glsl).
// palette: 0 = green, 1 = pink, 2 = blue, 3 = rainbow, 4 = custom colour

vec3 skyfx_auroraPalette(float h, float palette, float hueShift, vec3 custom) {
	if (palette > 3.5) {
		// custom colour: the chosen colour at the bottom, fading to a lighter, slightly hue-shifted tip
		vec3 tip = mix(custom, custom.brg, 0.35) * 0.8 + 0.1;
		return mix(custom, tip, smoothstep(0.3, 1.0, h));
	}
	if (palette < 0.5) {
		vec3 c = mix(vec3(0.10, 1.00, 0.42), vec3(0.05, 0.85, 0.65), smoothstep(0.0, 0.45, h));
		return mix(c, vec3(0.62, 0.22, 0.95), smoothstep(0.45, 1.0, h));
	} else if (palette < 1.5) {
		vec3 c = mix(vec3(1.00, 0.28, 0.62), vec3(0.85, 0.30, 0.95), smoothstep(0.0, 0.5, h));
		return mix(c, vec3(0.35, 0.35, 1.00), smoothstep(0.5, 1.0, h));
	} else if (palette < 2.5) {
		vec3 c = mix(vec3(0.15, 0.75, 1.00), vec3(0.20, 0.55, 1.00), smoothstep(0.0, 0.5, h));
		return mix(c, vec3(0.70, 0.30, 1.00), smoothstep(0.5, 1.0, h));
	}
	return skyfx_hsv2rgb(vec3(fract(hueShift + h * 0.35), 0.75, 1.0));
}

vec4 skyfx_auroraCurtains(vec3 dir, float t, float palette, vec3 custom) {
	vec4 acc = vec4(0.0);
	if (dir.y <= 0.0) return acc;
	const int STEPS = 36;
	float jitter = skyfx_hash12(floor(dir.xz * 2048.0)) * 0.45;
	float drift = t * 0.012;
	for (int i = 0; i < STEPS; i++) {
		float fi = (float(i) + jitter) / float(STEPS);
		float height = 1.0 + fi * 1.7;
		vec2 p = dir.xz * (height / (dir.y + 0.035));
		vec2 q = skyfx_rot(drift) * p * 0.25;
		float n1 = skyfx_noise2(q * 1.25 + vec2(t * 0.045, -t * 0.03));
		float n2 = skyfx_noise2(q * 2.9 - vec2(t * 0.10, t * 0.065));
		// two meandering curtains that fold and curl over time
		float curveA = sin(q.x * 1.15 + t * 0.19 + n1 * 4.2) * 0.65 + (n2 - 0.5) * 1.1;
		float dA = q.y - 1.25 - curveA;
		float curveB = sin(q.x * 0.75 - t * 0.15 + n2 * 3.4 + 2.0) * 0.85 + (n1 - 0.5) * 1.2;
		float dB = q.y + 0.85 - curveB;
		float band = exp(-dA * dA * 20.0) + 0.75 * exp(-dB * dB * 14.0);
		// fine vertical rays rippling along the curtains
		float rays = 0.30 + 0.70 * skyfx_noise2(vec2(q.x * 9.5 + n1 * 5.0, t * 0.9 + fi * 0.4));
		rays *= rays;
		float vertical = exp(-fi * 2.3) * (1.0 + 1.5 * exp(-fi * 14.0));
		float intensity = band * rays * vertical;
		vec3 col = skyfx_auroraPalette(fi, palette, t * 0.03 + q.x * 0.08, custom);
		acc.rgb += col * intensity;
		acc.a += intensity;
	}
	float horizonFade = smoothstep(0.0, 0.10, dir.y);
	float breathe = 0.82 + 0.18 * sin(t * 0.63) * sin(t * 0.29 + 1.3);
	acc.rgb *= 5.0 / float(STEPS) * horizonFade * breathe;
	acc.a *= 5.0 / float(STEPS) * horizonFade;
	return acc;
}

vec3 skyfx_aurora(vec3 dir, float t, float palette, vec3 custom) {
	float y = dir.y;
	vec3 zenith = vec3(0.004, 0.012, 0.040);
	vec3 horizon = vec3(0.030, 0.085, 0.140);
	vec3 col = mix(horizon, zenith, pow(clamp(y, 0.0, 1.0), 0.55));
	if (y < 0.0) {
		col = mix(horizon, vec3(0.008, 0.018, 0.032), clamp(-y * 3.0, 0.0, 1.0));
	}
	// faint milky band behind everything
	float milky = exp(-pow(dot(dir, normalize(vec3(0.35, 0.55, -0.76))) * 4.0, 2.0));
	milky *= 0.5 + 0.5 * skyfx_fbm3(dir * 4.0, 4);
	col += vec3(0.05, 0.07, 0.11) * milky * smoothstep(0.0, 0.25, y);

	col += skyfx_stars(dir, t, 1.0) * smoothstep(-0.02, 0.18, y);

	vec4 aurora = skyfx_auroraCurtains(dir, t, palette, custom);
	col = col * (1.0 - clamp(aurora.a * 0.2, 0.0, 0.6)) + aurora.rgb;

	// green airglow hugging the horizon, reflecting the aurora
	vec3 glowColor = skyfx_auroraPalette(0.05, palette, t * 0.03, custom);
	col += glowColor * 0.05 * exp(-abs(y) * 9.0);

	// a meteor shower: six independent streams of shooting stars, some tinted by the aurora
	col += skyfx_meteors(dir, t, 0.85, vec3(0.80, 0.95, 1.00));
	col += skyfx_meteors(dir, t * 1.37 + 11.0, 0.85, vec3(1.00, 0.95, 0.85));
	col += skyfx_meteors(dir, t * 0.81 + 23.0, 0.85, mix(vec3(0.85, 0.95, 1.0), glowColor, 0.5));
	col += skyfx_meteors(dir, t * 1.73 + 37.0, 0.75, vec3(0.75, 0.90, 1.00));
	col += skyfx_meteors(dir, t * 2.11 + 51.0, 0.70, mix(vec3(1.0), glowColor, 0.3));
	col += skyfx_meteors(dir, t * 0.63 + 67.0, 0.80, vec3(0.90, 0.92, 1.00));
	return col;
}
