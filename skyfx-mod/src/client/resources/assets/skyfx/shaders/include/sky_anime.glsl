// SkyFX "Anime Wolken" - a bright cel-shaded summer sky with drifting, boiling cumulus clouds,
// streaky cirrus and a flock of birds (needs skyfx_common.glsl).

vec3 skyfx_animeCel(float light, float bottom) {
	vec3 shadow = vec3(0.56, 0.63, 0.88);
	vec3 mid = vec3(0.95, 0.96, 1.00);
	vec3 warm = vec3(1.00, 0.86, 0.80);
	vec3 c = mix(shadow, mid, smoothstep(0.32, 0.40, light));
	c = mix(c, warm, smoothstep(0.70, 0.78, light));
	return mix(c, vec3(0.50, 0.58, 0.82), clamp(bottom, 0.0, 1.0) * 0.6);
}

// Towering cumulus banks standing on the horizon.
vec4 skyfx_animeBank(vec3 dir, float t, vec3 sunDir, vec3 horizonColor) {
	float el = asin(clamp(dir.y, -1.0, 1.0));
	if (el > 0.6 || el < -0.08) return vec4(0.0);
	float azRaw = atan(dir.z, dir.x);
	float az = azRaw + t * 0.0035;
	vec2 ring = vec2(cos(az), sin(az));
	float profile = 0.08 + 0.32 * pow(skyfx_fbm3(vec3(ring * 1.4, 2.7), 4), 1.5);
	float boil = t * 0.012;
	float puff = skyfx_fbm3(vec3(ring * 3.2, el * 7.0 - boil), 5) + (skyfx_fbm3(vec3(ring * 11.0, el * 26.0 - boil * 2.0), 3) - 0.5) * 0.35;
	float density = (profile - el) * 5.0 + (puff - 0.5) * 1.6;
	float mask = smoothstep(0.0, 0.05, density);
	if (mask <= 0.0) return vec4(0.0);
	float puffUp = skyfx_fbm3(vec3(ring * 3.2, (el + 0.03) * 7.0 - boil), 5) + (skyfx_fbm3(vec3(ring * 11.0, (el + 0.03) * 26.0 - boil * 2.0), 3) - 0.5) * 0.35;
	float densityUp = (profile - el - 0.03) * 5.0 + (puffUp - 0.5) * 1.6;
	float sunAz = atan(sunDir.z, sunDir.x);
	float light = clamp(1.0 - densityUp * 1.2, 0.0, 1.0) * (0.72 + 0.28 * cos(azRaw - sunAz));
	float bottom = 1.0 - smoothstep(0.0, 0.07, el + (puff - 0.5) * 0.06);
	vec3 c = skyfx_animeCel(light, bottom);
	c = mix(c, horizonColor, 0.30 * (1.0 - smoothstep(0.0, 0.10, el)));
	return vec4(c, mask);
}

// Puffy cumulus drifting overhead.
vec4 skyfx_animeCumulus(vec3 dir, float t, vec3 sunDir) {
	if (dir.y < 0.03) return vec4(0.0);
	vec2 uv = dir.xz / (dir.y + 0.12) * 0.9;
	vec2 wind = vec2(1.0, 0.35) * t * 0.018;
	float evolve = t * 0.008;
	float d = skyfx_fbm3(vec3(uv + wind, evolve) * 1.1, 5);
	float cover = 0.56;
	float mask = smoothstep(0.0, 0.25, (d - cover) * 9.0) * smoothstep(0.03, 0.20, dir.y);
	if (mask <= 0.0) return vec4(0.0);
	vec2 toSun = normalize(sunDir.xz + vec2(1e-4)) * 0.09;
	float dl = skyfx_fbm3(vec3(uv + wind + toSun, evolve) * 1.1, 5);
	float light = clamp(0.62 + (d - dl) * 7.0 - (d - cover) * 1.3, 0.0, 1.0);
	vec3 c = skyfx_animeCel(light, clamp((d - cover) * 3.0, 0.0, 1.0) * 0.5);
	return vec4(c, mask);
}

float skyfx_animeCirrus(vec3 dir, float t) {
	if (dir.y < 0.02) return 0.0;
	vec2 uv = dir.xz / (dir.y + 0.2) * 0.6;
	vec2 q = skyfx_rot(0.5) * uv;
	q = vec2(q.x * 0.35, q.y * 3.0) + vec2(t * 0.012, 0.0);
	float c = skyfx_fbm2(q + vec2(skyfx_fbm2(q * 0.5, 3) * 1.5, 0.0), 5);
	return smoothstep(0.55, 0.78, c) * smoothstep(0.02, 0.25, dir.y) * 0.45;
}

float skyfx_segment(vec2 p, vec2 a, vec2 b) {
	vec2 pa = p - a;
	vec2 ba = b - a;
	float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
	return length(pa - ba * h);
}

// A small flock gliding around the sky, flapping their wings.
float skyfx_birds(vec3 dir, float t) {
	float acc = 0.0;
	for (int k = 0; k < 6; k++) {
		float fk = float(k);
		float az = mod(t * 0.018 + fk * 0.045 + sin(fk * 3.1) * 0.02, SKYFX_TAU);
		float el = 0.30 + 0.025 * sin(fk * 1.7) + 0.012 * sin(t * 0.5 + fk) + fk * 0.006;
		vec3 c = vec3(cos(az) * cos(el), sin(el), sin(az) * cos(el));
		if (dot(dir, c) < 0.995) continue;
		vec3 e1 = normalize(cross(c, vec3(0.0, 1.0, 0.0)));
		vec3 e2 = cross(e1, c);
		vec2 p = vec2(dot(dir, e1), dot(dir, e2)) / (0.0075 - fk * 0.0004);
		float flap = sin(t * 9.0 + fk * 2.1);
		float wingY = 0.32 * flap + 0.12;
		float d = min(skyfx_segment(p, vec2(0.0), vec2(1.0, wingY)), skyfx_segment(p, vec2(0.0), vec2(-1.0, wingY)));
		acc = max(acc, 1.0 - smoothstep(0.07, 0.17, d));
	}
	return acc;
}

vec3 skyfx_anime(vec3 dir, float t) {
	float y = dir.y;
	vec3 sunDir = normalize(vec3(-0.55, 0.32, 0.62));
	vec3 zenith = vec3(0.10, 0.34, 0.82);
	vec3 middle = vec3(0.30, 0.60, 0.96);
	vec3 horizon = vec3(0.72, 0.89, 1.00);
	vec3 col = mix(horizon, middle, smoothstep(0.0, 0.22, y));
	col = mix(col, zenith, smoothstep(0.22, 0.85, y));
	if (y < 0.0) {
		col = mix(vec3(0.48, 0.74, 0.94), vec3(0.18, 0.44, 0.76), smoothstep(0.0, 0.4, -y));
		col = mix(col, horizon, exp(y * 40.0) * 0.6);
	}

	// soft anime sun with slowly turning light rays
	float sd = max(dot(dir, sunDir), 0.0);
	vec3 se1 = normalize(cross(sunDir, vec3(0.0, 1.0, 0.0)));
	vec3 se2 = cross(se1, sunDir);
	float rayAngle = atan(dot(dir, se2), dot(dir, se1));
	float rays = pow(0.5 + 0.5 * sin(rayAngle * 18.0 + t * 0.15) * sin(rayAngle * 7.0 - t * 0.1), 3.0);
	col += vec3(1.0, 0.95, 0.82) * (smoothstep(0.9993, 0.9997, sd) * 1.5 + pow(sd, 64.0) * 0.35 + pow(sd, 6.0) * 0.12 + rays * pow(sd, 16.0) * 0.10);

	col = mix(col, vec3(1.0, 0.96, 0.98), skyfx_animeCirrus(dir, t));
	vec4 cumulus = skyfx_animeCumulus(dir, t, sunDir);
	col = mix(col, cumulus.rgb, cumulus.a);
	vec4 bank = skyfx_animeBank(dir, t, sunDir, horizon);
	col = mix(col, bank.rgb, bank.a);
	col = mix(col, vec3(0.16, 0.20, 0.32), skyfx_birds(dir, t) * 0.85);
	return col;
}
