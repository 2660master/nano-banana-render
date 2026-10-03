// SkyFX "Galaxy" - deep space with violet nebulae, a rotating spiral galaxy, orbiting planets and
// tumbling asteroids (needs skyfx_common.glsl).

// 3D cellular crater field: bowls below 0, raised rims above 0.
float skyfx_craters(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	float h = 0.0;
	for (int z = -1; z <= 1; z++) {
		for (int y = -1; y <= 1; y++) {
			for (int x = -1; x <= 1; x++) {
				vec3 g = vec3(float(x), float(y), float(z));
				vec3 r = skyfx_hash33(i + g);
				if (r.y < 0.4) continue;
				float radius = 0.22 + 0.3 * r.x;
				float k = length(g + r - f) / radius;
				if (k < 1.0) h += (k * k - 1.0) * 0.7;
				h += exp(-(k - 1.0) * (k - 1.0) * 18.0) * 0.45;
			}
		}
	}
	return h;
}

vec3 skyfx_planetRock(vec3 n, vec3 l, vec3 axis, float spin, float t) {
	vec3 q = skyfx_rotAxis(n, axis, spin);
	vec3 lq = skyfx_rotAxis(l, axis, spin);
	float base = skyfx_fbm3(q * 2.2, 5);
	float h = skyfx_craters(q * 3.5);
	float hl = skyfx_craters(q * 3.5 + lq * 0.05);
	float bump = clamp((h - hl) * 2.5, -1.0, 1.0);
	vec3 albedo = mix(vec3(0.30, 0.29, 0.36), vec3(0.68, 0.66, 0.76), base);
	albedo *= 0.85 + 0.25 * clamp(h, -1.0, 1.0);
	float ndl = dot(n, l);
	float diffuse = clamp(ndl + bump * 0.35, 0.0, 1.0) * smoothstep(-0.15, 0.25, ndl);
	vec3 col = albedo * (0.05 + 1.45 * diffuse);
	// glowing violet fissures that pulse, strongest on the night side
	float v = abs(skyfx_fbm3(q * 3.0 + 11.0, 4) - 0.5);
	float vein = 1.0 - smoothstep(0.0, 0.035, v);
	float veinGlow = exp(-v * 40.0) * 0.35;
	float pulse = 0.55 + 0.45 * sin(t * 1.7 + base * 12.0);
	col += vec3(0.82, 0.50, 1.0) * (vein + veinGlow) * pulse * (0.45 + 1.0 * (1.0 - diffuse));
	return col;
}

vec3 skyfx_planetIce(vec3 n, vec3 l, vec3 axis, float spin) {
	vec3 q = skyfx_rotAxis(n, axis, spin);
	float base = skyfx_fbm3(q * 4.0 + 3.0, 4);
	float h = skyfx_craters(q * 5.0 + 2.0);
	vec3 albedo = mix(vec3(0.55, 0.70, 0.88), vec3(0.92, 0.96, 1.0), base) * (0.9 + 0.15 * clamp(h, -1.0, 1.0));
	float diffuse = clamp(dot(n, l), 0.0, 1.0);
	return albedo * (0.03 + 1.1 * diffuse);
}

vec3 skyfx_planetLava(vec3 n, vec3 l, vec3 axis, float spin, float t) {
	vec3 q = skyfx_rotAxis(n, axis, spin);
	float base = skyfx_fbm3(q * 3.0 + 7.0, 5);
	vec3 albedo = mix(vec3(0.35, 0.10, 0.08), vec3(0.75, 0.35, 0.20), base);
	float diffuse = clamp(dot(n, l), 0.0, 1.0);
	vec3 col = albedo * (0.04 + 1.0 * diffuse);
	float crack = 1.0 - smoothstep(0.0, 0.04, abs(skyfx_fbm3(q * 4.0 + 1.0, 4) - 0.5));
	col += vec3(1.0, 0.45, 0.12) * crack * (0.6 + 0.4 * sin(t * 2.3 + base * 9.0));
	return col;
}

vec3 skyfx_planetGas(vec3 n, vec3 l, vec3 axis, float spin, float t) {
	float lat = dot(n, axis);
	vec3 q = skyfx_rotAxis(n, axis, spin);
	float swirl = skyfx_fbm3(q * 3.0 + vec3(0.0, t * 0.02, 0.0), 4);
	float bands = 0.5 + 0.5 * sin(lat * 22.0 + swirl * 4.0);
	vec3 c = mix(vec3(0.86, 0.62, 0.55), vec3(0.55, 0.45, 0.82), bands);
	c = mix(c, vec3(0.96, 0.88, 0.86), smoothstep(0.68, 0.92, swirl));
	float diffuse = clamp(dot(n, l), 0.0, 1.0);
	return c * (0.03 + 1.1 * diffuse);
}

// Planetary ring through 'center' with normal 'axis'. Returns rgba and writes the hit distance (or -1).
vec4 skyfx_ring(vec3 rd, vec3 center, vec3 axis, float rIn, float rOut, vec3 l, out float hit) {
	hit = -1.0;
	float denom = dot(rd, axis);
	if (abs(denom) < 1e-5) return vec4(0.0);
	float tt = dot(center, axis) / denom;
	if (tt <= 0.0) return vec4(0.0);
	float r = length(rd * tt - center);
	if (r < rIn || r > rOut) return vec4(0.0);
	float x = (r - rIn) / (rOut - rIn);
	float bands = 0.55 + 0.45 * sin(x * 60.0) * sin(x * 13.0 + 1.0);
	float gap = smoothstep(0.52, 0.55, x) * (1.0 - smoothstep(0.58, 0.61, x));
	float alpha = bands * (1.0 - gap * 0.9) * smoothstep(0.0, 0.05, x) * (1.0 - smoothstep(0.92, 1.0, x));
	vec3 col = mix(vec3(0.70, 0.62, 0.86), vec3(0.96, 0.86, 0.80), bands) * (0.45 + 0.55 * abs(dot(l, axis)));
	hit = tt;
	return vec4(col, alpha * 0.85);
}

// An irregular tumbling rock. Returns the hit distance (or -1) and writes its colour.
float skyfx_asteroid(vec3 rd, vec3 pos, float radius, float seed, float t, vec3 l, out vec3 col) {
	col = vec3(0.0);
	float b = dot(rd, pos);
	if (b <= 0.0) return -1.0;
	vec3 perp = rd * b - pos;
	float dist = length(perp);
	if (dist > radius * 1.45) return -1.0;
	vec3 fwd = normalize(pos);
	vec3 e1 = normalize(cross(fwd, vec3(0.0, 1.0, 0.0)));
	vec3 e2 = cross(e1, fwd);
	vec2 lp = vec2(dot(perp, e1), dot(perp, e2));
	float ang = atan(lp.y, lp.x) + t * (0.3 + seed * 0.5);
	vec2 rim = vec2(cos(ang), sin(ang));
	float shape = radius * (0.74 + 0.48 * skyfx_noise2(rim * 1.7 + seed * 13.0));
	if (dist > shape) return -1.0;
	float k = dist / shape;
	vec3 n = normalize(perp / shape - fwd * sqrt(max(1.0 - k * k, 0.0)));
	float bumps = skyfx_noise3(vec3(rim * k * 4.0, seed * 7.0)) * 0.6 + skyfx_noise3(vec3(rim * k * 11.0, seed * 3.0)) * 0.4;
	float diffuse = clamp(dot(n, l) + (bumps - 0.5) * 0.5, 0.0, 1.0);
	col = mix(vec3(0.33, 0.31, 0.38), vec3(0.66, 0.64, 0.74), bumps) * (0.05 + 1.05 * diffuse);
	return b - sqrt(max(shape * shape - dist * dist, 0.0));
}

vec3 skyfx_nebula(vec3 dir, float t) {
	vec3 p = skyfx_rotY(dir, t * 0.003) * 2.0;
	vec3 warp = vec3(
		skyfx_fbm3(p + vec3(0.0, t * 0.010, 0.0), 4),
		skyfx_fbm3(p + vec3(5.2, 1.3, t * 0.012), 4),
		skyfx_fbm3(p + vec3(2.1, t * 0.008, 7.7), 4)
	);
	vec3 q = p * 1.5 + warp * 2.0;
	float n = skyfx_fbm3(q, 6);
	float ridge = 1.0 - abs(2.0 * skyfx_fbm3(q * 1.7 + 5.0, 5) - 1.0);
	float filaments = pow(ridge, 7.0);
	float region = smoothstep(0.30, 0.70, skyfx_fbm3(dir * 0.9 + 3.0, 3));
	float gas = smoothstep(0.38, 0.85, n) * region;
	float dust = smoothstep(0.50, 0.68, skyfx_fbm3(q * 2.6 + 11.0, 4)) * region;
	vec3 violet = vec3(0.32, 0.10, 0.60);
	vec3 pink = vec3(0.95, 0.32, 0.78);
	vec3 blue = vec3(0.22, 0.42, 1.00);
	vec3 col = mix(violet, blue, smoothstep(0.40, 0.80, warp.y));
	col = mix(col, pink, smoothstep(0.55, 0.80, warp.x) * 0.7);
	vec3 neb = col * gas * 0.95 + mix(pink, vec3(1.0, 0.88, 1.0), 0.5) * filaments * gas * 1.3;
	return neb * (1.0 - dust * 0.75);
}

// The brightest stars, each with a soft glow and four diffraction spikes.
vec3 skyfx_brightStars(vec3 dir, float t) {
	vec3 acc = vec3(0.0);
	for (int i = 0; i < 30; i++) {
		vec3 h = skyfx_hash33(vec3(float(i), 3.3, 7.1));
		vec3 s = normalize(skyfx_hash33(vec3(float(i), 9.7, 1.3)) * 2.0 - 1.0);
		if (dot(dir, s) < 0.993) continue;
		vec3 e1 = normalize(cross(s, abs(s.y) < 0.9 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0)));
		vec3 e2 = cross(s, e1);
		vec2 p = vec2(dot(dir, e1), dot(dir, e2)) * 420.0;
		float r = length(p);
		float twinkle = 0.75 + 0.25 * sin(t * (1.0 + h.x * 2.0) + h.y * SKYFX_TAU);
		float spikes = exp(-abs(p.x) * 1.3) * exp(-abs(p.y) * 0.07) + exp(-abs(p.y) * 1.3) * exp(-abs(p.x) * 0.07);
		vec3 tint = mix(vec3(0.70, 0.80, 1.00), vec3(1.00, 0.78, 0.95), h.z);
		acc += tint * (exp(-r * r * 0.35) * 2.2 + exp(-r * 0.3) * 0.22 + spikes * 0.35) * twinkle * (0.5 + h.z);
	}
	return acc;
}

vec3 skyfx_milkyBand(vec3 dir, float t) {
	vec3 axis = normalize(vec3(0.25, 0.85, 0.45));
	vec3 d = skyfx_rotAxis(dir, axis, t * 0.004);
	float h = dot(dir, axis);
	float band = exp(-h * h * 22.0);
	float detail = skyfx_fbm3(d * 6.0, 5);
	float dust = smoothstep(0.45, 0.65, skyfx_fbm3(d * 9.0 + 4.0, 4));
	vec3 col = mix(vec3(0.35, 0.28, 0.55), vec3(0.85, 0.78, 1.0), detail) * band * (0.35 + 0.65 * detail);
	col *= 1.0 - dust * 0.75 * band;
	col += skyfx_starLayer(d, 700.0, 0.6 * band, t, 0.9 * band);
	return col * 0.5;
}

vec3 skyfx_spiralGalaxy(vec3 dir, vec3 center, vec3 axis, float size, float t) {
	if (dot(dir, center) <= 0.0) return vec3(0.0);
	float denom = dot(dir, axis);
	if (abs(denom) < 1e-4) return vec3(0.0);
	float hit = dot(center, axis) / denom;
	if (hit <= 0.0) return vec3(0.0);
	vec3 local = dir * hit - center;
	vec3 u = normalize(cross(axis, vec3(0.0, 1.0, 0.0)));
	vec3 v = cross(axis, u);
	vec2 p = vec2(dot(local, u), dot(local, v)) / size;
	float r = length(p);
	if (r > 1.6) return vec3(0.0);
	float spin = t * 0.035;
	float a = atan(p.y, p.x);
	float arms = 0.5 + 0.5 * cos(2.0 * (a - spin) + log(r + 0.02) * 4.5);
	arms = arms * arms * arms;
	float dust = skyfx_fbm2(skyfx_rot(spin) * p * 6.0, 4);
	float fall = exp(-r * 2.6);
	float core = exp(-r * r * 60.0);
	vec3 armColor = mix(vec3(0.45, 0.35, 0.95), vec3(0.95, 0.75, 1.0), arms);
	vec3 col = armColor * arms * fall * (0.55 + 0.6 * dust) * 1.4;
	col += vec3(1.0, 0.92, 0.85) * (core * 2.5 + exp(-r * 8.0) * 0.35);
	return col * (1.0 - smoothstep(0.9, 1.6, r));
}

vec3 skyfx_galaxy(vec3 dir, float t) {
	vec3 sun = normalize(vec3(-0.30, 0.60, 0.50));

	// background: black void with violet glows, the galactic band, nebulae and stars
	vec3 col = vec3(0.004, 0.003, 0.012);
	col += vec3(0.14, 0.08, 0.30) * pow(max(dot(dir, normalize(vec3(0.6, 0.5, -0.6))), 0.0), 3.0) * 0.6;
	col += vec3(0.10, 0.06, 0.24) * pow(max(dot(dir, normalize(vec3(-0.8, -0.1, -0.3))), 0.0), 4.0) * 0.5;
	col += skyfx_milkyBand(dir, t);
	col += skyfx_nebula(dir, t);
	col += skyfx_stars(dir, t, 1.5);
	col += skyfx_brightStars(dir, t);
	col += skyfx_spiralGalaxy(dir, normalize(vec3(-0.55, 0.62, -0.56)), normalize(vec3(0.35, 0.55, 0.76)), 0.16, t);
	float sd = max(dot(dir, sun), 0.0);
	col += vec3(1.0, 0.92, 1.0) * (pow(sd, 3000.0) * 8.0 + pow(sd, 220.0) * 0.6 + pow(sd, 12.0) * 0.05);

	float best = 1e9;
	vec3 n;
	vec3 objCol;
	float hit;

	// big cratered planet with glowing fissures, slowly orbiting across the sky
	vec3 c0 = skyfx_rotY(normalize(vec3(0.62, 0.40, -0.67)), t * 0.0035);
	float r0 = 0.20;
	vec3 axis0 = normalize(vec3(0.2, 1.0, 0.1));
	hit = skyfx_sphere(dir, c0, r0, n);
	if (hit > 0.0) {
		best = hit;
		col = skyfx_planetRock(n, sun, axis0, t * 0.02, t);
		col += vec3(0.55, 0.35, 0.95) * pow(1.0 - max(dot(n, -dir), 0.0), 3.0) * 0.35;
	}

	// icy moon orbiting the big planet, passing in front of and behind it
	vec3 bu = normalize(cross(axis0, c0));
	vec3 moonPos = c0 + 0.34 * (cos(t * 0.09) * bu + sin(t * 0.09) * normalize(-c0 + axis0 * 0.25));
	hit = skyfx_sphere(dir, moonPos, 0.035, n);
	if (hit > 0.0 && hit < best) {
		best = hit;
		col = skyfx_planetIce(n, sun, axis0, t * 0.05);
	}

	// ringed gas giant on a wide orbit
	vec3 gasAxis = normalize(vec3(0.25, 1.0, -0.2));
	vec3 c1 = skyfx_rotAxis(normalize(vec3(-0.70, 0.32, -0.45)), normalize(vec3(0.2, 1.0, -0.1)), t * 0.012) * 1.6;
	hit = skyfx_sphere(dir, c1, 0.12, n);
	if (hit > 0.0 && hit < best) {
		best = hit;
		col = skyfx_planetGas(n, sun, gasAxis, t * 0.03, t);
	}

	// small lava world drifting the other way
	vec3 c2 = skyfx_rotAxis(normalize(vec3(0.30, 0.18, 0.95)), normalize(vec3(-0.1, 1.0, 0.2)), -t * 0.02) * 1.3;
	hit = skyfx_sphere(dir, c2, 0.05, n);
	if (hit > 0.0 && hit < best) {
		best = hit;
		col = skyfx_planetLava(n, sun, normalize(vec3(0.0, 1.0, 0.3)), t * 0.04, t);
	}

	// asteroid belt around the big planet
	vec3 beltAxis = normalize(vec3(0.25, 1.0, 0.15));
	vec3 beltU = normalize(cross(beltAxis, vec3(0.0, 0.0, 1.0)));
	vec3 beltW = cross(beltAxis, beltU);
	for (int k = 0; k < 14; k++) {
		float fk = float(k);
		vec3 h = skyfx_hash33(vec3(fk, 4.2, 9.7));
		float phi = h.x * SKYFX_TAU + t * (0.025 + 0.025 * h.y);
		float radius = 0.40 + 0.22 * h.z;
		vec3 pos = c0 + radius * (cos(phi) * beltU + sin(phi) * beltW) + beltAxis * (h.y - 0.5) * 0.06;
		hit = skyfx_asteroid(dir, pos, 0.008 + 0.014 * h.z, h.x, t, sun, objCol);
		if (hit > 0.0 && hit < best) {
			best = hit;
			col = objCol;
		}
	}

	// loose rocks drifting through the foreground
	for (int k = 0; k < 9; k++) {
		float fk = float(k);
		vec3 h = skyfx_hash33(vec3(fk, 1.7, 3.3));
		vec3 base = normalize(vec3(h.x - 0.5, h.y * 0.9 - 0.15, h.z - 0.5));
		vec3 driftAxis = normalize(vec3(h.z - 0.5, 1.0, h.x - 0.5));
		vec3 pos = skyfx_rotAxis(base, driftAxis, t * (0.006 + 0.01 * h.y)) * 0.7;
		hit = skyfx_asteroid(dir, pos, 0.010 + 0.018 * h.y, h.z + 2.0, t, sun, objCol);
		if (hit > 0.0 && hit < best) {
			best = hit;
			col = objCol;
		}
	}

	// translucent rings, drawn over whatever is behind them
	float ringHit;
	vec4 ring = skyfx_ring(dir, c1, gasAxis, 0.12 * 1.35, 0.12 * 2.3, sun, ringHit);
	if (ringHit > 0.0 && ringHit < best) {
		col = mix(col, ring.rgb, ring.a);
	}

	// violet atmosphere halo around the big planet
	float d0 = skyfx_rayPointDistance(dir, c0);
	if (d0 > r0 && dot(dir, c0) > 0.0) {
		vec3 toRay = normalize(dir * dot(dir, c0) - c0);
		float lit = 0.35 + 0.65 * smoothstep(-0.4, 0.8, dot(toRay, sun));
		col += vec3(0.55, 0.36, 0.98) * exp(-(d0 - r0) / (r0 * 0.12)) * lit * 0.55;
	}

	col += skyfx_meteors(dir, t, 0.7, vec3(0.90, 0.80, 1.00));
	return col;
}
