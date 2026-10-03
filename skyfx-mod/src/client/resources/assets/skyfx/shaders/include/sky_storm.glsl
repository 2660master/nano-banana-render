// SkyFX "Stormzee" - a sea of churning storm clouds under a gigantic moon: constant lightning, rain curtains,
// a swirling vortex overhead, a crescent planet and a pirate ship sailing over the clouds (needs skyfx_common.glsl).

float skyfx_box2(vec2 p, vec2 b) {
	vec2 d = abs(p) - b;
	return length(max(d, vec2(0.0))) + min(max(d.x, d.y), 0.0);
}

float skyfx_seg2(vec2 p, vec2 a, vec2 b) {
	vec2 pa = p - a;
	vec2 ba = b - a;
	float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
	return length(pa - ba * h);
}

// Signed distance to a three-masted pirate ship in "ship space" (hull from x = -0.9 to 0.95, deck near y = 0.05).
// Returns the distance in x and an id in y: 1 hull, 2 sails, 3 masts/rigging.
vec2 skyfx_ship(vec2 q, float t) {
	// hull: a curved keel rising to a high stern castle and a raised bow
	float x = q.x;
	float keel = -0.20 + 0.30 * pow(clamp((x + 0.05) / 0.95, 0.0, 1.0), 2.0) + 0.14 * pow(clamp((-0.05 - x) / 0.85, 0.0, 1.0), 3.0);
	float deck = 0.05 + 0.14 * (1.0 - smoothstep(-0.68, -0.52, x)) + 0.06 * smoothstep(0.55, 0.85, x);
	float hull = max(max(keel - q.y, q.y - deck), max(-0.9 - x, x - 0.95));
	float d = hull;
	float id = 1.0;

	// masts, bowsprit and rigging
	float masts = min(min(skyfx_box2(q - vec2(-0.35, 0.50), vec2(0.014, 0.47)), skyfx_box2(q - vec2(0.10, 0.58), vec2(0.016, 0.55))),
			skyfx_box2(q - vec2(0.52, 0.44), vec2(0.013, 0.40)));
	masts = min(masts, skyfx_seg2(q, vec2(0.85, 0.12), vec2(1.22, 0.34)) - 0.008);
	float rig = min(min(skyfx_seg2(q, vec2(0.10, 1.12), vec2(1.20, 0.33)), skyfx_seg2(q, vec2(0.10, 1.12), vec2(-0.86, 0.22))),
			min(skyfx_seg2(q, vec2(-0.35, 0.96), vec2(-0.86, 0.22)), skyfx_seg2(q, vec2(0.52, 0.83), vec2(1.10, 0.29)))) - 0.003;
	masts = min(masts, rig);
	if (masts < d) {
		d = masts;
		id = 3.0;
	}

	// billowing square sails, bulging with the wind
	float sails = 1e5;
	for (int i = 0; i < 3; i++) {
		float fi = float(i);
		float mx = i == 0 ? -0.35 : (i == 1 ? 0.10 : 0.52);
		float top = i == 1 ? 1.02 : (i == 0 ? 0.88 : 0.76);
		for (int k = 0; k < 2; k++) {
			float fk = float(k);
			float h0 = 0.22 + fk * (top - 0.22) * 0.52;
			float h1 = h0 + (top - 0.22) * 0.44;
			float w = 0.20 - fk * 0.05 - (i == 2 ? 0.03 : 0.0);
			vec2 sp = q - vec2(mx, (h0 + h1) * 0.5);
			float s01 = clamp((q.y - h0) / (h1 - h0), 0.0, 1.0);
			sp.x -= 0.035 * sin(s01 * SKYFX_PI) * (1.0 + 0.25 * sin(t * 1.3 + fi * 2.0 + fk));
			sails = min(sails, skyfx_box2(sp, vec2(w, (h1 - h0) * 0.5)));
		}
	}
	// waving flag on the main mast
	vec2 fp = q - vec2(0.10, 1.16);
	fp.y -= 0.025 * sin(fp.x * 18.0 - t * 6.0) * smoothstep(0.0, 0.16, fp.x);
	sails = min(sails, max(skyfx_box2(fp - vec2(0.08, 0.0), vec2(0.08, 0.035)), -fp.x));
	if (sails < d) {
		d = sails;
		id = 2.0;
	}
	return vec2(d, id);
}

vec3 skyfx_storm(vec3 dir, float t) {
	float y = dir.y;
	float el = asin(clamp(y, -1.0, 1.0));
	float azRaw = atan(dir.z, dir.x);
	vec3 moon = normalize(vec3(-0.30, 0.30, -0.90));
	float moonAz = atan(moon.z, moon.x);
	float moonRadius = 0.30;

	vec3 zenith = vec3(0.010, 0.020, 0.048);
	vec3 horizon = vec3(0.09, 0.16, 0.26);
	vec3 col = mix(horizon, zenith, pow(clamp(y, 0.0, 1.0), 0.6));
	col += skyfx_stars(dir, t, 0.55) * smoothstep(0.12, 0.45, y);

	// lightning: several strobing storm cells, often with a visible forked bolt
	float flash = 0.0;
	float bolt = 0.0;
	for (int k = 0; k < 4; k++) {
		float fk = float(k);
		float period = 1.7 + fk * 0.9;
		float tt = t / period + fk * 0.37;
		float id = floor(tt);
		float since = fract(tt) * period;
		vec3 h = skyfx_hash33(vec3(id, fk, 9.1));
		if (h.z > 0.8) continue;
		float flicker = exp(-since * 7.0) + 0.8 * exp(-abs(since - 0.16) * 32.0) + 0.6 * exp(-abs(since - 0.31) * 26.0) + 0.4 * exp(-abs(since - 0.52) * 30.0);
		if (flicker < 0.01) continue;
		float faz = h.x * SKYFX_TAU;
		float fel = 0.03 + h.y * 0.2;
		vec3 fdir = vec3(cos(faz) * cos(fel), sin(fel), sin(faz) * cos(fel));
		float ang = acos(clamp(dot(dir, fdir), -1.0, 1.0));
		flash += flicker * exp(-ang * ang / 0.025);
		float below = fel - el;
		if (h.y > 0.2 && below > -0.01 && below < 0.26) {
			float daz = azRaw - faz;
			daz = atan(sin(daz), cos(daz)) * cos(el);
			float jag = (skyfx_fbm2(vec2(el * 38.0, id * 3.1 + fk), 4) - 0.5) * 0.07 + (skyfx_noise2(vec2(el * 160.0, id)) - 0.5) * 0.012;
			float main = exp(-abs(daz - jag) / 0.0011);
			// a fork splitting off halfway down
			float forkStart = 0.08 + h.x * 0.06;
			float fork = 0.0;
			if (below > forkStart) {
				float side = (h.z > 0.4 ? 1.0 : -1.0) * (below - forkStart) * 0.35;
				fork = exp(-abs(daz - jag - side - (skyfx_noise2(vec2(el * 90.0, id + 7.0)) - 0.5) * 0.02) / 0.0009) * 0.7;
			}
			bolt += flicker * (main + fork) * (1.0 - below / 0.26);
		}
	}
	float sheet = 0.5 + 0.5 * sin(t * 0.7);
	col += vec3(0.25, 0.32, 0.48) * flash * 0.25;

	// a huge crescent planet, lit from behind, slowly sliding across the sky
	vec3 pc = skyfx_rotY(normalize(vec3(0.62, 0.55, -0.56)), t * 0.0025) * 3.0;
	float pr = 0.95;
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

	// the gigantic moon: cratered, slowly turning, with a huge cold halo
	vec3 mn;
	float mh = skyfx_sphere(dir, moon, sin(moonRadius), mn);
	vec3 mlight = normalize(moon * -0.2 + normalize(vec3(-0.9, 0.35, 0.3)));
	float md = max(dot(dir, moon), 0.0);
	float halo = exp(-max(acos(clamp(md, -1.0, 1.0)) - moonRadius, 0.0) * 9.0);
	col += vec3(0.55, 0.68, 0.95) * halo * 0.35 + vec3(0.30, 0.40, 0.65) * pow(md, 6.0) * 0.15;
	if (mh > 0.0) {
		vec3 mq = skyfx_rotY(mn, t * 0.01);
		float maria = smoothstep(0.44, 0.60, skyfx_fbm3(mq * 1.7 + 3.0, 5));
		float detail = skyfx_fbm3(mq * 7.0, 4);
		float pits = 1.0 - smoothstep(0.0, 0.06, abs(skyfx_fbm3(mq * 4.5 + 9.0, 3) - 0.5));
		vec3 albedo = mix(vec3(0.84, 0.87, 0.94), vec3(0.46, 0.51, 0.62), maria);
		albedo *= (0.88 + 0.22 * detail) * (1.0 - 0.18 * pits);
		float lit = smoothstep(-0.25, 0.45, dot(mn, mlight));
		float limb = pow(max(dot(mn, -dir), 0.0), 0.35);
		vec3 moonCol = albedo * (0.10 + 1.15 * lit) * limb;
		moonCol += vec3(0.55, 0.70, 1.0) * pow(1.0 - max(dot(mn, -dir), 0.0), 3.0) * 0.4;
		col = moonCol;
	}

	// rotating storm vortex straight overhead
	if (y > 0.40) {
		vec2 p = dir.xz / y;
		float r = length(p);
		float a = atan(p.y, p.x);
		float spiral = a + t * 0.07 + log(r + 0.05) * 2.4;
		float n = skyfx_fbm3(vec3(vec2(cos(spiral), sin(spiral)) * 1.6, r * 2.0 - t * 0.05), 5);
		float arms = 0.5 + 0.5 * sin(spiral * 3.0 + n * 3.0);
		float density = smoothstep(0.35, 0.75, n * 0.7 + arms * 0.45) * smoothstep(0.40, 0.72, y);
		vec3 vortex = mix(vec3(0.07, 0.11, 0.19), vec3(0.55, 0.65, 0.80), smoothstep(0.5, 0.95, n + arms * 0.2));
		vortex += vec3(0.6, 0.7, 1.0) * flash * 0.6;
		col = mix(col, vortex, density * 0.9);
		col += vec3(0.20, 0.30, 0.50) * exp(-r * 6.0) * 0.3 * smoothstep(0.40, 0.72, y);
	}

	// ragged clouds drifting in front of the moon
	if (y > 0.0 && y < 0.75) {
		vec2 cp = dir.xz / (y + 0.25) * 1.4 + vec2(t * 0.035, t * 0.01);
		float c = skyfx_fbm3(vec3(cp, t * 0.02), 5);
		float m = smoothstep(0.55, 0.72, c) * smoothstep(0.0, 0.12, y) * (1.0 - smoothstep(0.5, 0.75, y));
		float edge = smoothstep(0.55, 0.62, c) - smoothstep(0.62, 0.75, c);
		vec3 cc = mix(vec3(0.05, 0.07, 0.12), vec3(0.14, 0.19, 0.28), c);
		cc += vec3(0.55, 0.68, 0.95) * edge * halo * 0.9 + vec3(0.6, 0.7, 1.0) * flash * 0.5;
		col = mix(col, cc, m * 0.85);
	}

	// sea of clouds below the horizon, flowing towards the viewer
	if (y < 0.03) {
		vec2 fp = dir.xz / (max(-y, 0.0) + 0.04) * 0.5;
		vec2 flow = vec2(t * 0.03, t * 0.012);
		float f = skyfx_fbm3(vec3(fp + flow, t * 0.015), 5);
		float fl = skyfx_fbm3(vec3(fp + flow + normalize(moon.xz) * 0.06, t * 0.015), 5);
		float lit = clamp(0.5 + (f - fl) * 6.0, 0.0, 1.0);
		vec3 sea = mix(vec3(0.03, 0.05, 0.09), vec3(0.25, 0.33, 0.46), smoothstep(0.35, 0.75, f));
		sea += vec3(0.30, 0.38, 0.52) * lit * smoothstep(0.5, 0.8, f) * 0.6;
		sea += vec3(0.6, 0.7, 1.0) * flash * 0.35 * f;
		sea = mix(sea, horizon * 0.9, exp(-max(-y, 0.0) * 18.0) * 0.8);
		col = mix(col, sea, 1.0 - smoothstep(0.0, 0.03, y));
	}

	// towering cumulonimbus around the horizon, moonlit on top and lit from inside by the flashes
	float towerMask = 0.0;
	if (el > -0.1 && el < 0.7) {
		float az = azRaw + t * 0.009;
		vec2 ring = vec2(cos(az), sin(az));
		float profile = 0.12 + 0.36 * pow(skyfx_fbm3(vec3(ring * 1.2, 5.3), 4), 1.4);
		float churn = t * 0.03;
		float puff = skyfx_fbm3(vec3(ring * 3.0, el * 6.5 - churn), 5) + (skyfx_fbm3(vec3(ring * 10.0, el * 24.0 - churn * 2.0), 3) - 0.5) * 0.45;
		float density = (profile - el) * 5.5 + (puff - 0.5) * 1.8;
		towerMask = smoothstep(0.0, 0.08, density);
		if (towerMask > 0.0) {
			float puffUp = skyfx_fbm3(vec3(ring * 3.0, (el + 0.035) * 6.5 - churn), 5) + (skyfx_fbm3(vec3(ring * 10.0, (el + 0.035) * 24.0 - churn * 2.0), 3) - 0.5) * 0.45;
			float densityUp = (profile - el - 0.035) * 5.5 + (puffUp - 0.5) * 1.8;
			float topLight = clamp(1.0 - densityUp * 1.1, 0.0, 1.0);
			float moonSide = 0.55 + 0.45 * max(cos(azRaw - moonAz), 0.0);
			vec3 cloud = mix(vec3(0.035, 0.055, 0.10), vec3(0.20, 0.28, 0.40), smoothstep(0.1, 0.6, topLight));
			cloud = mix(cloud, vec3(0.66, 0.78, 0.95), smoothstep(0.75, 0.98, topLight) * moonSide);
			cloud += vec3(0.70, 0.80, 1.00) * flash * 1.4 * clamp(density * 0.5 + 0.5, 0.0, 1.0);
			col = mix(col, cloud, towerMask);
		}
	}

	// grey rain curtains hanging below the storm cells
	if (el > -0.06 && el < 0.16) {
		float raz = azRaw + t * 0.009;
		float cell = smoothstep(0.55, 0.75, skyfx_fbm2(vec2(cos(raz), sin(raz)) * 3.0 + 4.0, 3));
		float streak = skyfx_noise2(vec2(raz * 260.0 + el * 140.0, el * 6.0 + t * 7.0));
		float rain = cell * smoothstep(0.45, 0.85, streak) * (1.0 - smoothstep(0.04, 0.16, el)) * smoothstep(-0.06, -0.01, el);
		col = mix(col, vec3(0.16, 0.20, 0.27) + vec3(0.5, 0.6, 0.8) * flash * 0.3, rain * 0.45);
	}

	// thin streaky layers sliding past each other at different speeds
	if (el > -0.03 && el < 0.32) {
		float streaks = 0.0;
		for (int k = 0; k < 4; k++) {
			float fk = float(k);
			float e0 = 0.02 + fk * 0.055;
			float direction = mod(fk, 2.0) < 0.5 ? 1.0 : -1.0;
			float a2 = azRaw + t * (0.014 + fk * 0.008) * direction;
			vec2 r2 = vec2(cos(a2), sin(a2));
			float wave = (skyfx_noise2(r2 * 2.0 + fk * 4.0) - 0.5) * 0.05;
			float dd = (el - e0 - wave) / (0.004 + 0.004 * fk);
			float pieces = smoothstep(0.35, 0.70, skyfx_fbm2(r2 * 6.0 + vec2(fk * 3.0, 0.0), 4));
			streaks += exp(-dd * dd) * pieces * (0.8 - fk * 0.12);
		}
		col = mix(col, vec3(0.55, 0.68, 0.85), clamp(streaks, 0.0, 1.0) * 0.6);
	}

	// the pirate ship, rocking on the cloud sea and slowly sailing around the horizon
	float shipAz = -1.95 + t * 0.006;
	float daz = atan(sin(azRaw - shipAz), cos(azRaw - shipAz));
	if (abs(daz) < 0.42 && el > -0.12 && el < 0.3) {
		float scale = 0.17;
		vec2 q = vec2(daz * cos(el), el + 0.018 - 0.006 * sin(t * 0.9)) / scale;
		float roll = 0.05 * sin(t * 0.8) + 0.02 * sin(t * 1.9);
		q = skyfx_rot(roll) * q;
		vec2 s = skyfx_ship(q, t);
		float px = max(fwidth(q.x), 1e-4);
		float inside = 1.0 - smoothstep(-px, px, s.x);
		if (inside > 0.0) {
			vec3 shipCol = vec3(0.025, 0.03, 0.045);
			if (s.y > 1.5 && s.y < 2.5) {
				// sails catch the moonlight
				shipCol = mix(vec3(0.10, 0.12, 0.17), vec3(0.42, 0.48, 0.58), smoothstep(-0.8, 1.2, q.y) * (0.6 + 0.4 * max(cos(azRaw - moonAz), 0.0)));
			}
			// moonlit top edges of the hull
			if (s.y < 1.5) {
				vec2 sAbove = skyfx_ship(q + vec2(0.0, 0.02), t);
				shipCol += vec3(0.25, 0.32, 0.45) * smoothstep(0.0, 0.02, sAbove.x);
			}
			// glowing lantern windows at the stern
			for (int w = 0; w < 4; w++) {
				vec2 wp = q - vec2(-0.82 + float(w) * 0.07, 0.11);
				shipCol += vec3(1.0, 0.62, 0.25) * (1.0 - smoothstep(0.012, 0.022, length(wp))) * (0.85 + 0.15 * sin(t * 9.0 + float(w)));
			}
			shipCol += vec3(0.7, 0.8, 1.0) * flash * 0.4;
			col = mix(col, shipCol, inside);
		}
		// lantern glow on the sea around the ship
		col += vec3(1.0, 0.6, 0.25) * exp(-length(q - vec2(-0.72, 0.08)) * 6.0) * 0.08;
		// wisps of cloud rolling past the waterline
		float wl = (1.0 - smoothstep(-0.12, 0.02, q.y)) * smoothstep(-0.34, -0.2, q.y) * (1.0 - smoothstep(0.85, 1.2, abs(q.x)));
		float wisp = smoothstep(0.45, 0.7, skyfx_fbm2(vec2(q.x * 2.5 - t * 0.4, q.y * 6.0), 4));
		col = mix(col, vec3(0.22, 0.29, 0.40) + vec3(0.6, 0.7, 1.0) * flash * 0.3, clamp(wl * (0.25 + 0.75 * wisp), 0.0, 1.0) * 0.7);
	}

	col += vec3(0.70, 0.80, 1.00) * (flash * 0.10 * (0.6 + 0.4 * sheet) + bolt * 2.8);
	return col;
}
