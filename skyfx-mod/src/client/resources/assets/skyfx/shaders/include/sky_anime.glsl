// SkyFX "Anime Wolken" - a bright summer sky with big cel-shaded cumulus clouds built from round puffs, slowly
// drifting and breathing, plus streaky cirrus, a soft sun and a flock of birds (needs skyfx_common.glsl).

const vec3 SKYFX_CLOUD_LIT = vec3(1.00, 0.985, 0.96);
const vec3 SKYFX_CLOUD_WARM = vec3(1.00, 0.86, 0.80);
const vec3 SKYFX_CLOUD_MID = vec3(0.86, 0.90, 0.99);
const vec3 SKYFX_CLOUD_SHADOW = vec3(0.62, 0.70, 0.92);
const vec3 SKYFX_CLOUD_DEEP = vec3(0.50, 0.58, 0.84);

// Signed distance to one cumulus cloud: a union of round puffs piled into a mound with a flat base.
// Also returns (in puff) the normal of the front-most puff at p.
float skyfx_cumulusSd(vec2 p, float seed, float t, out vec3 puff) {
	float sd = 1e5;
	float bestZ = -1e5;
	puff = vec3(0.0, 0.0, 1.0);
	for (int i = 0; i < 22; i++) {
		float fi = float(i);
		vec3 h = skyfx_hash33(vec3(seed * 7.31, fi * 1.93, 2.7));
		float x = h.x * 2.0 - 1.0;
		float mound = 1.0 - x * x;
		float r = mix(0.10, 0.30, h.z * h.z) * (0.6 + 0.4 * mound);
		float y = r * 0.5 + mound * h.y * 0.75;
		r *= 1.0 + 0.05 * sin(t * 0.35 + fi * 1.7 + seed * 3.0);
		vec2 d = p - vec2(x, y);
		float dist = length(d);
		sd = min(sd, dist - r);
		if (dist < r) {
			float nz = sqrt(max(1.0 - dist * dist / (r * r), 0.0));
			float z = nz * r + y * 0.35 + r * 0.4;
			if (z > bestZ) {
				bestZ = z;
				puff = vec3(d / r, nz);
			}
		}
	}
	return max(sd, 0.03 - p.y);
}

// One cel-shaded cumulus cloud. p: local coordinates (x right, y up; the cloud spans x -1.2..1.2, y 0..~1.3).
// light2: direction towards the light in the same 2D space. Returns colour and coverage.
vec4 skyfx_cumulus(vec2 p, float seed, float t, vec2 light2, float px) {
	vec3 puff;
	float sd = skyfx_cumulusSd(p, seed, t, puff);
	float coverage = 1.0 - smoothstep(-px, px, sd);
	if (coverage <= 0.0) return vec4(0.0);
	vec3 unused;
	// is there open sky a little way towards the light? then this part of the cloud faces the sun
	float towardsLight = skyfx_cumulusSd(p + light2 * 0.11, seed, t, unused);
	float height = clamp(p.y / 1.1, 0.0, 1.0);
	float w = max(px * 1.5, 0.01);
	float lit = smoothstep(-0.015 - w, -0.015 + w, towardsLight);
	float shade = smoothstep(0.12 - w * 4.0, 0.12 + w * 4.0, height + puff.y * 0.08);
	vec3 col = mix(SKYFX_CLOUD_SHADOW, SKYFX_CLOUD_MID, shade);
	col = mix(col, SKYFX_CLOUD_LIT, max(lit, smoothstep(0.55, 0.62, height + dot(puff.xy, light2) * 0.15) * 0.8));
	col = mix(col, SKYFX_CLOUD_WARM, lit * smoothstep(0.3, 0.7, height) * smoothstep(0.2, 0.7, dot(puff.xy, light2)));
	col = mix(col, SKYFX_CLOUD_DEEP, (1.0 - smoothstep(0.0, 0.1, height)) * 0.5 * (1.0 - lit));
	// soft contour where one puff overlaps the next
	col *= 1.0 - (1.0 - smoothstep(0.0, 0.35, puff.z)) * 0.10 * (1.0 - lit);
	return vec4(col, coverage);
}

// Low, pale cloud banks far away on the horizon, for depth.
vec4 skyfx_animeHaze(vec3 dir, float t, vec3 horizonColor) {
	float el = asin(clamp(dir.y, -1.0, 1.0));
	if (el > 0.2 || el < -0.05) return vec4(0.0);
	float az = atan(dir.z, dir.x) + t * 0.002;
	vec2 ring = vec2(cos(az), sin(az));
	float profile = 0.025 + 0.07 * skyfx_fbm3(vec3(ring * 2.0, 1.3), 4);
	float puff = skyfx_fbm3(vec3(ring * 9.0, el * 30.0 - t * 0.01), 4);
	float density = (profile - el) * 30.0 + (puff - 0.5) * 2.0;
	float px = max(fwidth(density), 1e-3);
	float mask = smoothstep(-px, px, density);
	vec3 c = mix(vec3(0.80, 0.86, 0.98), vec3(0.97, 0.97, 1.0), smoothstep(0.3, 0.8, puff + el * 4.0));
	return vec4(mix(c, horizonColor, 0.35), mask * 0.9);
}

float skyfx_animeCirrus(vec3 dir, float t) {
	if (dir.y < 0.02) return 0.0;
	vec2 uv = dir.xz / (dir.y + 0.2) * 0.6;
	vec2 q = skyfx_rot(0.5) * uv;
	q = vec2(q.x * 0.35, q.y * 4.0) + vec2(t * 0.012, 0.0);
	float c = skyfx_fbm2(q + vec2(skyfx_fbm2(q * 0.5, 3) * 1.5, 0.0), 6);
	float streak = smoothstep(0.58, 0.8, c) * (0.6 + 0.4 * skyfx_noise2(q * vec2(2.0, 18.0)));
	return streak * smoothstep(0.02, 0.25, dir.y) * 0.25;
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
	vec3 zenith = vec3(0.09, 0.32, 0.82);
	vec3 middle = vec3(0.28, 0.58, 0.96);
	vec3 horizon = vec3(0.72, 0.89, 1.00);
	vec3 col = mix(horizon, middle, smoothstep(0.0, 0.22, y));
	col = mix(col, zenith, smoothstep(0.22, 0.85, y));
	if (y < 0.0) {
		col = mix(vec3(0.48, 0.74, 0.94), vec3(0.18, 0.44, 0.76), smoothstep(0.0, 0.4, -y));
		col = mix(col, horizon, exp(y * 40.0) * 0.6);
	}

	// soft anime sun with a few slowly turning light rays
	float sd = max(dot(dir, sunDir), 0.0);
	vec3 se1 = normalize(cross(sunDir, vec3(0.0, 1.0, 0.0)));
	vec3 se2 = cross(se1, sunDir);
	float rayAngle = atan(dot(dir, se2), dot(dir, se1));
	float rays = pow(0.5 + 0.5 * sin(rayAngle * 14.0 + t * 0.12) * sin(rayAngle * 5.0 - t * 0.08), 4.0);
	col += vec3(1.0, 0.96, 0.85) * (smoothstep(0.9993, 0.9996, sd) * 1.4 + pow(sd, 90.0) * 0.4 + pow(sd, 6.0) * 0.10 + rays * pow(sd, 22.0) * 0.08);

	col = mix(col, vec3(1.0, 0.97, 0.99), skyfx_animeCirrus(dir, t));

	float el = asin(clamp(y, -1.0, 1.0));
	float az = atan(dir.z, dir.x);
	vec4 haze = skyfx_animeHaze(dir, t, horizon);
	col = mix(col, haze.rgb, haze.a);

	// the light comes from the sun's side in screen space: right/up of the cloud when the sun is to the right
	float sunAz = atan(sunDir.z, sunDir.x);

	// big cumulus clouds standing on the horizon, drifting slowly around it
	if (el > -0.06 && el < 0.75) {
		for (int k = 0; k < 11; k++) {
			float fk = float(k);
			vec3 h = skyfx_hash33(vec3(fk, 8.1, 4.4));
			float big = step(0.72, h.y);
			float size = mix(0.17, 0.27, h.x) + big * 0.17;
			float cAz = fk * (SKYFX_TAU / 11.0) + (h.z - 0.5) * 0.4 + t * (0.0035 + 0.002 * h.x);
			float dAz = atan(sin(az - cAz), cos(az - cAz));
			vec2 p = vec2(dAz * cos(el), el + 0.015) / size;
			if (abs(p.x) > 1.45 || p.y > 1.7 || p.y < -0.1) continue;
			float side = clamp(sin(sunAz - cAz) * 1.5, -1.0, 1.0);
			vec4 cloud = skyfx_cumulus(p, fk + 1.0, t, normalize(vec2(-side, 0.9)), fwidth(p.x) * 1.2);
			cloud.rgb = mix(cloud.rgb, horizon, 0.12 * (1.0 - smoothstep(0.0, 0.6, p.y)));
			col = mix(col, cloud.rgb, cloud.a);
		}
	}

	// smaller puffy clouds floating higher up
	if (el > 0.2 && el < 1.1) {
		for (int k = 0; k < 8; k++) {
			float fk = float(k);
			vec3 h = skyfx_hash33(vec3(fk, 2.2, 9.9));
			float cEl = 0.32 + h.y * 0.55;
			float size = mix(0.07, 0.12, h.z);
			float cAz = fk * (SKYFX_TAU / 8.0) + h.x + t * (0.006 + 0.003 * h.z);
			float dAz = atan(sin(az - cAz), cos(az - cAz));
			vec2 p = vec2(dAz * cos(el), el - cEl) / size;
			if (abs(p.x) > 1.45 || p.y > 1.7 || p.y < -0.1) continue;
			float side = clamp(sin(sunAz - cAz) * 1.5, -1.0, 1.0);
			vec4 cloud = skyfx_cumulus(p, fk + 31.0, t, normalize(vec2(-side, 0.9)), fwidth(p.x) * 1.2);
			col = mix(col, cloud.rgb, cloud.a);
		}
	}

	col = mix(col, vec3(0.16, 0.20, 0.32), skyfx_birds(dir, t) * 0.85);
	return col;
}
