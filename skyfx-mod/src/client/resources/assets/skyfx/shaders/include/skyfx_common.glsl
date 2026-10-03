// SkyFX shared shader library.
//
// This file is used by the in-game sky shaders AND by the HTML preview (preview/build-preview.mjs inlines it),
// so it must stay valid GLSL 3.30 as well as GLSL ES 3.00: explicit float literals, no implicit int -> float,
// and never call smoothstep() with edge0 >= edge1.

const float SKYFX_PI = 3.14159265;
const float SKYFX_TAU = 6.28318531;

// Hash functions after Dave Hoskins, "Hash without Sine" (MIT).
float skyfx_hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

float skyfx_hash13(vec3 p3) {
	p3 = fract(p3 * 0.1031);
	p3 += dot(p3, p3.zyx + 31.32);
	return fract((p3.x + p3.y) * p3.z);
}

vec3 skyfx_hash33(vec3 p3) {
	p3 = fract(p3 * vec3(0.1031, 0.1030, 0.0973));
	p3 += dot(p3, p3.yxz + 33.33);
	return fract((p3.xxy + p3.yxx) * p3.zyx);
}

float skyfx_noise2(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	float a = skyfx_hash12(i);
	float b = skyfx_hash12(i + vec2(1.0, 0.0));
	float c = skyfx_hash12(i + vec2(0.0, 1.0));
	float d = skyfx_hash12(i + vec2(1.0, 1.0));
	return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float skyfx_noise3(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	vec3 u = f * f * (3.0 - 2.0 * f);
	float n000 = skyfx_hash13(i);
	float n100 = skyfx_hash13(i + vec3(1.0, 0.0, 0.0));
	float n010 = skyfx_hash13(i + vec3(0.0, 1.0, 0.0));
	float n110 = skyfx_hash13(i + vec3(1.0, 1.0, 0.0));
	float n001 = skyfx_hash13(i + vec3(0.0, 0.0, 1.0));
	float n101 = skyfx_hash13(i + vec3(1.0, 0.0, 1.0));
	float n011 = skyfx_hash13(i + vec3(0.0, 1.0, 1.0));
	float n111 = skyfx_hash13(i + vec3(1.0, 1.0, 1.0));
	return mix(
		mix(mix(n000, n100, u.x), mix(n010, n110, u.x), u.y),
		mix(mix(n001, n101, u.x), mix(n011, n111, u.x), u.y),
		u.z
	);
}

float skyfx_fbm2(vec2 p, int octaves) {
	float value = 0.0;
	float amplitude = 0.5;
	mat2 rot = mat2(0.8, -0.6, 0.6, 0.8);
	for (int i = 0; i < 8; i++) {
		if (i >= octaves) break;
		value += amplitude * skyfx_noise2(p);
		p = rot * p * 2.03 + vec2(17.1, 9.7);
		amplitude *= 0.5;
	}
	return value;
}

float skyfx_fbm3(vec3 p, int octaves) {
	float value = 0.0;
	float amplitude = 0.5;
	for (int i = 0; i < 8; i++) {
		if (i >= octaves) break;
		value += amplitude * skyfx_noise3(p);
		p = vec3(p.y * 1.6 + p.z * 1.2, p.z * 1.6 - p.x * 1.2, p.x * 1.6 + p.y * 1.2) * 1.03 + vec3(5.2, 1.3, 7.7);
		amplitude *= 0.5;
	}
	return value;
}

mat2 skyfx_rot(float a) {
	float c = cos(a);
	float s = sin(a);
	return mat2(c, s, -s, c);
}

vec3 skyfx_rotY(vec3 v, float a) {
	float c = cos(a);
	float s = sin(a);
	return vec3(c * v.x + s * v.z, v.y, -s * v.x + c * v.z);
}

vec3 skyfx_rotX(vec3 v, float a) {
	float c = cos(a);
	float s = sin(a);
	return vec3(v.x, c * v.y - s * v.z, s * v.y + c * v.z);
}

// Rodrigues rotation of v around a unit axis.
vec3 skyfx_rotAxis(vec3 v, vec3 axis, float a) {
	float c = cos(a);
	float s = sin(a);
	return v * c + cross(axis, v) * s + axis * dot(axis, v) * (1.0 - c);
}

vec3 skyfx_hsv2rgb(vec3 c) {
	vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0);
	return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

// Soft shoulder: identity below 0.8, smooth roll-off above so bright cores never clip harshly.
vec3 skyfx_tonemap(vec3 c) {
	c = max(c, vec3(0.0));
	vec3 over = max(c - 0.8, vec3(0.0));
	return min(c, vec3(0.8)) + 0.2 * (1.0 - exp(-over / 0.2));
}

// One layer of twinkling stars on the unit sphere. Stars never shrink below ~1 pixel so they do not shimmer.
vec3 skyfx_starLayer(vec3 dir, float scale, float density, float t, float brightness) {
	vec3 p = dir * scale;
	vec3 cell = floor(p);
	vec3 f = fract(p) - 0.5;
	vec3 h = skyfx_hash33(cell);
	if (skyfx_hash13(cell * 1.37 + 11.0) > density) {
		return vec3(0.0);
	}
	vec3 offset = (h - 0.5) * 0.7;
	float d = length(f - offset);
	float pixel = max(length(fwidth(p)), 1e-4);
	float size = 0.03 + 0.09 * h.z * h.z * h.z;
	float drawSize = max(size, pixel * 0.9);
	float energy = (size * size) / (drawSize * drawSize);
	float core = 1.0 - smoothstep(0.0, drawSize, d);
	float glow = exp(-d * d / (drawSize * drawSize * 6.0)) * 0.25;
	float twinkle = 0.6 + 0.4 * sin(t * (1.3 + 3.7 * h.x) + h.y * SKYFX_TAU);
	vec3 tint = mix(vec3(0.62, 0.74, 1.0), vec3(1.0, 0.82, 0.62), h.y);
	tint = mix(tint, vec3(1.0), 0.35);
	return tint * (core + glow) * energy * twinkle * brightness * (0.6 + 1.6 * h.z);
}

vec3 skyfx_stars(vec3 dir, float t, float brightness) {
	vec3 s = skyfx_starLayer(dir, 110.0, 0.22, t, 1.0);
	s += skyfx_starLayer(skyfx_rotY(dir, 1.7), 260.0, 0.30, t * 1.3, 0.7);
	s += skyfx_starLayer(skyfx_rotX(dir, 0.9), 520.0, 0.35, t * 0.8, 0.45);
	return s * brightness;
}

// A few shooting stars that streak across the upper sky every couple of seconds.
vec3 skyfx_meteors(vec3 dir, float t, float chance, vec3 color) {
	vec3 acc = vec3(0.0);
	for (int k = 0; k < 3; k++) {
		float fk = float(k);
		float period = 6.0 + fk * 2.7;
		float tt = t / period + fk * 0.37;
		float id = floor(tt);
		float phase = fract(tt);
		vec3 h = skyfx_hash33(vec3(id, fk * 7.1, 3.7));
		float life = 0.16;
		if (h.z > chance || phase > life) continue;
		float prog = phase / life;
		float az = h.x * SKYFX_TAU;
		float el = 0.45 + h.y * 0.75;
		vec3 start = vec3(cos(az) * cos(el), sin(el), sin(az) * cos(el));
		vec3 side = normalize(cross(start, vec3(0.0, 1.0, 0.0)));
		vec3 tangent = normalize(side * (h.x > 0.5 ? 1.0 : -1.0) - vec3(0.0, 0.45, 0.0));
		tangent = normalize(tangent - start * dot(tangent, start));
		float travel = 0.55;
		vec3 head = normalize(start + tangent * (prog * travel));
		vec3 tail = normalize(start + tangent * max(prog * travel - 0.16, 0.0));
		vec3 pa = dir - tail;
		vec3 ba = head - tail;
		float along = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-6), 0.0, 1.0);
		float d = length(pa - ba * along);
		float fade = sin(prog * SKYFX_PI);
		float w = 0.0016;
		acc += color * fade * (exp(-d * d / (w * w)) * along * along * 2.2 + exp(-d * d / (w * w * 24.0)) * along * 0.18);
	}
	return acc;
}

// Ray (from the origin) / sphere intersection. Returns the hit distance or -1; n receives the surface normal.
float skyfx_sphere(vec3 rd, vec3 center, float radius, out vec3 n) {
	float b = dot(rd, center);
	float c = dot(center, center) - radius * radius;
	float h = b * b - c;
	n = vec3(0.0, 1.0, 0.0);
	if (h < 0.0) return -1.0;
	float hit = b - sqrt(h);
	if (hit < 0.0) return -1.0;
	n = normalize(rd * hit - center);
	return hit;
}

// Distance from the ray (from the origin) to a point, used for atmosphere / glow halos.
float skyfx_rayPointDistance(vec3 rd, vec3 p) {
	return length(p - rd * max(dot(rd, p), 0.0));
}
