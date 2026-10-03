// SkyFX "Stormzee" - a dark sea of churning storm clouds with lightning, a swirling vortex overhead,
// a cold moon and a huge crescent planet (needs skyfx_common.glsl).

vec3 skyfx_storm(vec3 dir, float t) {
	float y = dir.y;
	float el = asin(clamp(y, -1.0, 1.0));
	float azRaw = atan(dir.z, dir.x);
	vec3 moon = normalize(vec3(-0.30, 0.36, -0.88));
	float moonAz = atan(moon.z, moon.x);

	vec3 zenith = vec3(0.010, 0.020, 0.048);
	vec3 horizon = vec3(0.09, 0.16, 0.26);
	vec3 col = mix(horizon, zenith, pow(clamp(y, 0.0, 1.0), 0.6));
	col += skyfx_stars(dir, t, 0.55) * smoothstep(0.12, 0.45, y);

	// a huge crescent planet, lit from behind, slowly sliding across the sky
	vec3 pc = skyfx_rotY(normalize(vec3(0.55, 0.62, -0.56)), t * 0.0025) * 3.0;
	float pr = 1.15;
	vec3 pcn = normalize(pc);
	vec3 pside = normalize(cross(pcn, vec3(0.0, 1.0, 0.0)));
	vec3 lp = normalize(pcn * 0.45 - pside * 0.85 - vec3(0.0, 0.25, 0.0));
	vec3 pn;
	float ph = skyfx_sphere(dir, pc, pr, pn);
	if (ph > 0.0) {
		float crescent = smoothstep(-0.02, 0.35, dot(pn, lp));
		float rim = pow(1.0 - max(dot(pn, -dir), 0.0), 2.5);
		float bands = 0.65 + 0.35 * sin(dot(pn, vec3(0.0, 1.0, 0.0)) * 18.0 + skyfx_fbm3(pn * 3.0 + t * 0.01, 3) * 5.0);
		vec3 surface = vec3(0.02, 0.03, 0.055) + vec3(0.50, 0.66, 0.88) * crescent * bands;
		col = surface + vec3(0.40, 0.62, 0.95) * rim * (0.15 + crescent) * 0.8;
	} else if (dot(dir, pc) > 0.0) {
		float dist = skyfx_rayPointDistance(dir, pc);
		vec3 toRay = normalize(dir * dot(dir, pc) - pc);
		float side = smoothstep(-0.3, 0.6, dot(toRay, lp));
		col += vec3(0.40, 0.60, 0.95) * exp(-(dist - pr) / 0.07) * (0.15 + side) * 0.75;
	}

	// cold moon with a wide halo and an anamorphic streak
	float md = max(dot(dir, moon), 0.0);
	col += vec3(0.80, 0.88, 1.00) * (pow(md, 3000.0) * 8.0 + pow(md, 120.0) * 0.5 + pow(md, 10.0) * 0.07);
	vec3 mr = normalize(cross(moon, vec3(0.0, 1.0, 0.0)));
	vec3 mu = cross(mr, moon);
	col += vec3(0.60, 0.75, 1.00) * exp(-abs(dot(dir, mu)) * 300.0) * exp(-abs(dot(dir, mr)) * 5.0) * step(0.0, dot(dir, moon)) * 0.35;

	// rotating storm vortex straight overhead
	if (y > 0.42) {
		vec2 p = dir.xz / y;
		float r = length(p);
		float a = atan(p.y, p.x);
		float spiral = a + t * 0.05 + log(r + 0.05) * 2.2;
		float n = skyfx_fbm3(vec3(vec2(cos(spiral), sin(spiral)) * 1.6, r * 2.0 - t * 0.03), 5);
		float arms = 0.5 + 0.5 * sin(spiral * 3.0 + n * 3.0);
		float density = smoothstep(0.35, 0.75, n * 0.7 + arms * 0.45) * smoothstep(0.42, 0.75, y);
		vec3 vortex = mix(vec3(0.07, 0.11, 0.19), vec3(0.55, 0.65, 0.80), smoothstep(0.5, 0.95, n + arms * 0.2));
		col = mix(col, vortex, density * 0.9);
		col += vec3(0.20, 0.30, 0.50) * exp(-r * 6.0) * 0.3 * smoothstep(0.42, 0.75, y);
	}

	// sea of clouds below the horizon, flowing towards the viewer
	if (y < 0.03) {
		vec2 fp = dir.xz / (max(-y, 0.0) + 0.04) * 0.5;
		vec2 flow = vec2(t * 0.02, t * 0.008);
		float f = skyfx_fbm3(vec3(fp + flow, t * 0.01), 5);
		float fl = skyfx_fbm3(vec3(fp + flow + normalize(moon.xz) * 0.06, t * 0.01), 5);
		float lit = clamp(0.5 + (f - fl) * 6.0, 0.0, 1.0);
		vec3 sea = mix(vec3(0.03, 0.05, 0.09), vec3(0.25, 0.33, 0.46), smoothstep(0.35, 0.75, f));
		sea += vec3(0.25, 0.32, 0.42) * lit * smoothstep(0.5, 0.8, f) * 0.6;
		sea = mix(sea, horizon * 0.9, exp(-max(-y, 0.0) * 18.0) * 0.8);
		col = mix(col, sea, 1.0 - smoothstep(0.0, 0.03, y));
	}

	// lightning: strobing flashes somewhere in the storm, sometimes with a visible bolt
	float flash = 0.0;
	float bolt = 0.0;
	for (int k = 0; k < 2; k++) {
		float fk = float(k);
		float period = 3.1 + fk * 1.9;
		float tt = t / period + fk * 0.5;
		float id = floor(tt);
		float since = fract(tt) * period;
		vec3 h = skyfx_hash33(vec3(id, fk, 9.1));
		if (h.z > 0.65) continue;
		float flicker = exp(-since * 6.0) + 0.7 * exp(-abs(since - 0.18) * 30.0) + 0.5 * exp(-abs(since - 0.33) * 25.0);
		if (flicker < 0.01) continue;
		float faz = h.x * SKYFX_TAU;
		float fel = 0.04 + h.y * 0.18;
		vec3 fdir = vec3(cos(faz) * cos(fel), sin(fel), sin(faz) * cos(fel));
		float ang = acos(clamp(dot(dir, fdir), -1.0, 1.0));
		flash += flicker * exp(-ang * ang / 0.02);
		float below = fel - el;
		if (h.y > 0.3 && below > 0.0 && below < 0.22) {
			float daz = azRaw - faz;
			daz = atan(sin(daz), cos(daz));
			float jag = (skyfx_fbm2(vec2(el * 40.0, id * 3.1 + fk), 4) - 0.5) * 0.06 + (skyfx_noise2(vec2(el * 150.0, id)) - 0.5) * 0.01;
			float dx = abs(daz * cos(el) - jag);
			bolt += flicker * exp(-dx / 0.0012) * (1.0 - below / 0.22);
		}
	}

	// towering cumulonimbus around the horizon, moonlit on top and lit from inside by the flashes
	if (el > -0.1 && el < 0.65) {
		float az = azRaw + t * 0.006;
		vec2 ring = vec2(cos(az), sin(az));
		float profile = 0.10 + 0.32 * pow(skyfx_fbm3(vec3(ring * 1.2, 5.3), 4), 1.4);
		float churn = t * 0.02;
		float puff = skyfx_fbm3(vec3(ring * 3.0, el * 6.5 - churn), 5) + (skyfx_fbm3(vec3(ring * 10.0, el * 24.0 - churn * 2.0), 3) - 0.5) * 0.45;
		float density = (profile - el) * 5.5 + (puff - 0.5) * 1.8;
		float mask = smoothstep(0.0, 0.08, density);
		if (mask > 0.0) {
			float puffUp = skyfx_fbm3(vec3(ring * 3.0, (el + 0.035) * 6.5 - churn), 5) + (skyfx_fbm3(vec3(ring * 10.0, (el + 0.035) * 24.0 - churn * 2.0), 3) - 0.5) * 0.45;
			float densityUp = (profile - el - 0.035) * 5.5 + (puffUp - 0.5) * 1.8;
			float topLight = clamp(1.0 - densityUp * 1.1, 0.0, 1.0);
			float moonSide = 0.55 + 0.45 * max(cos(azRaw - moonAz), 0.0);
			vec3 cloud = mix(vec3(0.035, 0.055, 0.10), vec3(0.20, 0.28, 0.40), smoothstep(0.1, 0.6, topLight));
			cloud = mix(cloud, vec3(0.62, 0.74, 0.90), smoothstep(0.75, 0.98, topLight) * moonSide);
			cloud += vec3(0.70, 0.80, 1.00) * flash * 1.2 * clamp(density * 0.5 + 0.5, 0.0, 1.0);
			col = mix(col, cloud, mask);
		}
	}

	// thin streaky layers sliding past each other at different speeds
	if (el > -0.03 && el < 0.32) {
		float streaks = 0.0;
		for (int k = 0; k < 4; k++) {
			float fk = float(k);
			float e0 = 0.02 + fk * 0.055;
			float direction = mod(fk, 2.0) < 0.5 ? 1.0 : -1.0;
			float a2 = azRaw + t * (0.01 + fk * 0.006) * direction;
			vec2 r2 = vec2(cos(a2), sin(a2));
			float wave = (skyfx_noise2(r2 * 2.0 + fk * 4.0) - 0.5) * 0.05;
			float dd = (el - e0 - wave) / (0.004 + 0.004 * fk);
			float pieces = smoothstep(0.35, 0.70, skyfx_fbm2(r2 * 6.0 + vec2(fk * 3.0, 0.0), 4));
			streaks += exp(-dd * dd) * pieces * (0.8 - fk * 0.12);
		}
		col = mix(col, vec3(0.55, 0.68, 0.85), clamp(streaks, 0.0, 1.0) * 0.6);
	}

	col += vec3(0.70, 0.80, 1.00) * (flash * 0.12 + bolt * 2.5);
	return col;
}
