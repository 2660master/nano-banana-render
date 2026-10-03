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

// Approximate signed distance to a triangle (either winding).
float skyfx_tri(vec2 p, vec2 a, vec2 b, vec2 c) {
	float w = sign((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x));
	vec2 e0 = b - a;
	vec2 e1 = c - b;
	vec2 e2 = a - c;
	float d0 = dot(p - a, normalize(vec2(e0.y, -e0.x))) * w;
	float d1 = dot(p - b, normalize(vec2(e1.y, -e1.x))) * w;
	float d2 = dot(p - c, normalize(vec2(e2.y, -e2.x))) * w;
	return max(max(d0, d1), d2);
}

// Hull outline of the ship: keel and deck heights at x (hull from x = -0.9 to 0.95).
vec2 skyfx_hullYs(float x) {
	float keel = -0.20 + 0.30 * pow(clamp((x + 0.05) / 0.95, 0.0, 1.0), 2.0) + 0.14 * pow(clamp((-0.05 - x) / 0.85, 0.0, 1.0), 3.0);
	float deck = 0.05 + 0.14 * (1.0 - smoothstep(-0.68, -0.52, x)) + 0.06 * smoothstep(0.55, 0.85, x);
	return vec2(keel, deck);
}

// Jolly Roger: white skull and crossbones on the black flag, in flag space (centre at the origin). <0 is white.
float skyfx_jollyRoger(vec2 f) {
	float skull = min(length(f - vec2(0.0, 0.012)) - 0.020, skyfx_box2(f - vec2(0.0, -0.010), vec2(0.011, 0.008)));
	skull = max(skull, -(length(vec2(abs(f.x) - 0.008, f.y - 0.012)) - 0.0055));
	skull = max(skull, -skyfx_box2(f - vec2(0.0, 0.002), vec2(0.0018, 0.003)));
	float bones = min(skyfx_seg2(f, vec2(-0.034, -0.040), vec2(0.034, 0.012)), skyfx_seg2(f, vec2(-0.034, 0.012), vec2(0.034, -0.040))) - 0.0045;
	return min(skull, bones);
}

// Signed distance to a three-masted pirate ship in "ship space" (hull from x = -0.9 to 0.95, deck near y = 0.05).
// Returns the distance in x and an id in y: 1 hull, 2 sails, 3 masts/rigging, 4 gold trim/railing, 5 black flag.
vec2 skyfx_ship(vec2 q, float t) {
	// hull: a curved keel rising to a high stern castle and a raised bow, with a rudder and a figurehead
	float x = q.x;
	vec2 ys = skyfx_hullYs(x);
	float hull = max(max(ys.x - q.y, q.y - ys.y), max(-0.9 - x, x - 0.95));
	hull = min(hull, skyfx_box2(q - vec2(-0.915, -0.02), vec2(0.03, 0.12)));
	hull = min(hull, length((q - vec2(0.975, 0.16)) * vec2(1.0, 0.75)) - 0.035);
	float d = hull;
	float id = 1.0;

	// railing along the deck: a top rail on little posts, a stern lantern pole and the stern gallery
	float railY = ys.y + 0.055;
	float rail = max(abs(q.y - railY) - 0.006, max(-0.88 - x, x - 0.92));
	float posts = max(abs(fract(x * 16.0) - 0.5) / 16.0 - 0.0045, max(q.y - railY, ys.y - 0.01 - q.y));
	rail = min(rail, max(posts, max(-0.88 - x, x - 0.92)));
	rail = min(rail, skyfx_box2(q - vec2(-0.86, 0.33), vec2(0.006, 0.07)));
	if (rail < d) {
		d = rail;
		id = 4.0;
	}

	// masts with yards (cross spars), a crow's nest, bowsprit and the rigging
	float masts = min(min(skyfx_box2(q - vec2(-0.35, 0.50), vec2(0.014, 0.47)), skyfx_box2(q - vec2(0.10, 0.58), vec2(0.016, 0.55))),
			skyfx_box2(q - vec2(0.52, 0.44), vec2(0.013, 0.40)));
	masts = min(masts, skyfx_seg2(q, vec2(0.85, 0.12), vec2(1.22, 0.34)) - 0.008);
	masts = min(masts, skyfx_box2(q - vec2(0.10, 0.93), vec2(0.055, 0.025)));
	float rig = min(min(skyfx_seg2(q, vec2(0.10, 1.12), vec2(1.20, 0.33)), skyfx_seg2(q, vec2(0.10, 1.12), vec2(-0.86, 0.22))),
			min(skyfx_seg2(q, vec2(-0.35, 0.96), vec2(-0.86, 0.22)), skyfx_seg2(q, vec2(0.52, 0.83), vec2(1.10, 0.29))));
	float shrouds = 1e5;
	for (int i = 0; i < 3; i++) {
		float mx = i == 0 ? -0.35 : (i == 1 ? 0.10 : 0.52);
		float top = i == 1 ? 1.02 : (i == 0 ? 0.88 : 0.76);
		float w = 0.22 - (i == 2 ? 0.03 : 0.0);
		// shrouds: a rope ladder from the deck edge up to the mast, with ratlines across
		float deckY = skyfx_hullYs(mx).y + 0.05;
		vec2 lo = vec2(mx - w * 0.9, deckY);
		vec2 hi = vec2(mx - 0.01, top * 0.82);
		float shroud = min(skyfx_seg2(q, lo, hi), skyfx_seg2(q, lo + vec2(0.07, 0.0), hi));
		float sh01 = clamp((q.y - deckY) / (hi.y - deckY), 0.0, 1.0);
		float sx0 = mix(lo.x, hi.x, sh01);
		float sx1 = mix(lo.x + 0.07, hi.x, sh01);
		float ratline = max(abs(fract(q.y * 22.0) - 0.5) / 22.0, max(sx0 - x, x - sx1));
		ratline = max(ratline, max(deckY - q.y, q.y - hi.y));
		shrouds = min(shrouds, min(shroud, ratline));
		// yards: a spar on top of each sail and a boom below the lower one
		for (int k = 0; k < 2; k++) {
			float fk = float(k);
			float h1 = 0.22 + fk * (top - 0.22) * 0.52 + (top - 0.22) * 0.44;
			float sw = 0.20 - fk * 0.05 - (i == 2 ? 0.03 : 0.0);
			masts = min(masts, skyfx_box2(q - vec2(mx, h1 + 0.008), vec2(sw + 0.03, 0.006)));
		}
		masts = min(masts, skyfx_box2(q - vec2(mx, 0.212), vec2(w - 0.01, 0.005)));
	}
	masts = min(masts, rig - 0.0028);
	if (masts < d) {
		d = masts;
		id = 3.0;
	}

	// billowing square sails, bulging with the wind, plus two triangular jibs on the bowsprit
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
			// the foot of the sail curves up and is a bit ragged
			sp.y += 0.025 * (1.0 - pow(clamp(sp.x / w, -1.0, 1.0), 2.0)) * (1.0 - s01);
			float sail = skyfx_box2(sp, vec2(w, (h1 - h0) * 0.5));
			float notch = skyfx_hash12(vec2(floor(q.x * 60.0), fi * 7.0 + fk)) * 0.014;
			sail = max(sail, notch - (sp.y + (h1 - h0) * 0.5));
			sails = min(sails, sail);
		}
	}
	// jibs hang from the forestay down to the bowsprit
	sails = min(sails, skyfx_tri(q, vec2(0.607, 0.749), vec2(1.071, 0.317), vec2(0.66, 0.24)));
	sails = min(sails, skyfx_tri(q, vec2(0.810, 0.560), vec2(1.170, 0.310), vec2(0.90, 0.25)));
	if (sails < d) {
		d = sails;
		id = 2.0;
	}

	// the shrouds hang on the side of the ship, in front of the sails
	shrouds -= 0.0025;
	if (shrouds < d) {
		d = shrouds;
		id = 3.0;
	}

	// the black Jolly Roger flag waving on top of the main mast
	vec2 fp = q - vec2(0.10, 1.13);
	fp.y -= 0.025 * sin(fp.x * 18.0 - t * 6.0) * smoothstep(0.0, 0.22, fp.x);
	float flag = max(skyfx_box2(fp - vec2(0.11, 0.0), vec2(0.11, 0.06)), -fp.x);
	if (flag < d) {
		d = flag;
		id = 5.0;
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
	if (abs(daz) < 0.5 && el > -0.14 && el < 0.4) {
		float scale = 0.24;
		vec2 q = vec2(daz * cos(el), el + 0.022 - 0.008 * sin(t * 0.9)) / scale;
		float roll = 0.05 * sin(t * 0.8) + 0.02 * sin(t * 1.9);
		q = skyfx_rot(roll) * q;
		vec2 s = skyfx_ship(q, t);
		float px = max(fwidth(q.x), 1e-4);
		float inside = 1.0 - smoothstep(-px, px, s.x);
		float moonLit = 0.6 + 0.4 * max(cos(azRaw - moonAz), 0.0);
		vec3 lantern = vec3(1.0, 0.62, 0.25);
		float flicker = 0.85 + 0.15 * sin(t * 9.0) * sin(t * 5.3 + 1.0);
		if (inside > 0.0) {
			vec3 shipCol = vec3(0.025, 0.03, 0.045);
			if (s.y < 1.5) {
				// dark wooden hull with plank lines, a gold stripe, gun ports and the lit stern windows
				vec2 ys = skyfx_hullYs(q.x);
				float hy = (q.y - ys.x) / max(ys.y - ys.x, 0.05);
				vec3 wood = mix(vec3(0.045, 0.030, 0.026), vec3(0.11, 0.075, 0.055), smoothstep(0.0, 1.0, hy));
				float plank = abs(fract(q.y * 28.0 + 0.3 * skyfx_hash12(vec2(floor(q.x * 5.0), 1.0))) - 0.5);
				wood *= 0.75 + 0.25 * smoothstep(0.05, 0.18, plank);
				float seam = abs(fract(q.x * 5.0 + floor(q.y * 28.0) * 0.37) - 0.5);
				wood *= 0.85 + 0.15 * smoothstep(0.0, 0.03, seam);
				shipCol = wood * (0.8 + 0.6 * moonLit);
				float stripe = 1.0 - smoothstep(0.004, 0.004 + px, abs(q.y - (ys.y - 0.045)));
				shipCol = mix(shipCol, vec3(0.55, 0.40, 0.16) * moonLit, stripe * step(-0.88, q.x));
				// a row of gun ports, a few glowing from the lanterns inside, each with a cannon muzzle
				float portY = mix(ys.x, ys.y, 0.42);
				float cell = floor((q.x + 0.6) / 0.115);
				vec2 pp = vec2(fract((q.x + 0.6) / 0.115) - 0.5, (q.y - portY) / 0.115);
				if (cell >= 0.0 && cell < 12.0) {
					float port = skyfx_box2(pp, vec2(0.17, 0.17));
					float portMask = 1.0 - smoothstep(0.0, px / 0.115, port);
					float lit = step(0.45, skyfx_hash12(vec2(cell, 3.0)));
					vec3 portCol = mix(vec3(0.01, 0.01, 0.012), lantern * 0.8 * flicker, lit);
					float muzzle = 1.0 - smoothstep(0.08, 0.08 + px / 0.115, length(pp));
					portCol = mix(portCol, vec3(0.03, 0.03, 0.035), muzzle);
					shipCol = mix(shipCol, portCol, portMask);
					float frame = (1.0 - smoothstep(0.0, px / 0.115 * 1.5, abs(port - 0.03))) * (1.0 - portMask);
					shipCol = mix(shipCol, vec3(0.30, 0.22, 0.10) * moonLit, frame * 0.8);
				}
				// stern castle windows in two rows
				for (int w = 0; w < 4; w++) {
					for (int r = 0; r < 2; r++) {
						vec2 wp = q - vec2(-0.83 + float(w) * 0.065, 0.10 + float(r) * 0.07);
						float win = skyfx_box2(wp, vec2(0.018, 0.022));
						shipCol = mix(shipCol, lantern * (0.9 + 0.1 * sin(t * 7.0 + float(w * 3 + r))) * flicker, 1.0 - smoothstep(0.0, px, win));
					}
				}
				// moonlit top edges
				vec2 sAbove = skyfx_ship(q + vec2(0.0, 0.02), t);
				shipCol += vec3(0.25, 0.32, 0.45) * smoothstep(0.0, 0.02, sAbove.x) * moonLit;
			} else if (s.y < 2.5) {
				// sails catch the moonlight, with seams, a patch and the shadow of the yard above
				shipCol = mix(vec3(0.10, 0.12, 0.17), vec3(0.46, 0.50, 0.58), smoothstep(-0.8, 1.2, q.y) * moonLit);
				float seams = abs(fract(q.x * 26.0) - 0.5);
				shipCol *= 0.88 + 0.12 * smoothstep(0.0, 0.12, seams);
				vec2 patchP = q - vec2(0.16, 0.48);
				shipCol *= 1.0 - 0.18 * (1.0 - smoothstep(0.0, px, skyfx_box2(patchP, vec2(0.035, 0.03))));
				shipCol *= 0.85 + 0.15 * skyfx_fbm2(q * 9.0 + vec2(t * 0.2, 0.0), 3);
				// big faded skull painted on the main sail
				float sk = skyfx_jollyRoger((q - vec2(0.12, 0.42)) * 0.32);
				shipCol = mix(shipCol, vec3(0.06, 0.06, 0.08), (1.0 - smoothstep(0.0, px * 0.32, sk)) * 0.55);
			} else if (s.y < 3.5) {
				shipCol = vec3(0.035, 0.03, 0.035) + vec3(0.06, 0.07, 0.09) * moonLit * smoothstep(0.0, 1.2, q.y);
			} else if (s.y < 4.5) {
				// gold railing and the lantern pole
				shipCol = vec3(0.30, 0.22, 0.10) * moonLit;
			} else {
				// the Jolly Roger: black flag, white skull and crossbones
				vec2 fp = q - vec2(0.10, 1.13);
				fp.y -= 0.025 * sin(fp.x * 18.0 - t * 6.0) * smoothstep(0.0, 0.22, fp.x);
				float shade = 0.75 + 0.25 * sin(fp.x * 18.0 - t * 6.0 + 1.2);
				shipCol = vec3(0.012, 0.012, 0.016) * shade;
				float jr = skyfx_jollyRoger((fp - vec2(0.11, 0.0)) * 0.9);
				shipCol = mix(shipCol, vec3(0.85, 0.85, 0.80) * shade * moonLit, 1.0 - smoothstep(0.0, px * 0.9, jr));
			}
			shipCol += vec3(0.7, 0.8, 1.0) * flash * 0.4;
			col = mix(col, shipCol, inside);
		}
		// the stern lantern on its pole, with a soft halo, and lantern glow on the sea around the ship
		float lampD = length(q - vec2(-0.86, 0.41));
		col = mix(col, vec3(1.0, 0.85, 0.55), 1.0 - smoothstep(0.018, 0.018 + px, lampD));
		col += lantern * exp(-lampD * 22.0) * 0.6 * flicker;
		col += lantern * exp(-length(q - vec2(-0.72, 0.08)) * 6.0) * 0.08;
		// wisps of cloud rolling past the waterline, and foam at the bow
		float wl = (1.0 - smoothstep(-0.12, 0.02, q.y)) * smoothstep(-0.34, -0.2, q.y) * (1.0 - smoothstep(0.85, 1.2, abs(q.x)));
		float wisp = smoothstep(0.45, 0.7, skyfx_fbm2(vec2(q.x * 2.5 - t * 0.4, q.y * 6.0), 4));
		col = mix(col, vec3(0.22, 0.29, 0.40) + vec3(0.6, 0.7, 1.0) * flash * 0.3, clamp(wl * (0.25 + 0.75 * wisp), 0.0, 1.0) * 0.7);
		float foam = exp(-length((q - vec2(0.92, -0.08)) * vec2(1.4, 5.0)) * 4.0) * smoothstep(0.4, 0.75, skyfx_fbm2(q * 14.0 - vec2(t * 1.5, 0.0), 3));
		col = mix(col, vec3(0.55, 0.62, 0.72), clamp(foam, 0.0, 1.0) * 0.8);
	}

	col += vec3(0.70, 0.80, 1.00) * (flash * 0.10 * (0.6 + 0.4 * sheet) + bolt * 2.8);
	return col;
}
