// world_lighting.gdshader
// ─────────────────────────────────────────────────────────────────────────────
// Screen-space post-processing shader applied to a full-screen CanvasLayer.
// Mimics the warm, slightly vignette-lit look of Pokémon Gamma Emerald:
//   • Color temperature shift (warm highlights, cool shadows)
//   • Subtle vignette that focuses attention on the center
//   • Contrast / saturation boost
//   • Animated scanline dust (very subtle, toggleable)
// ─────────────────────────────────────────────────────────────────────────────
shader_type canvas_item;

// ── Color grading ─────────────────────────────────────────────────────────────
uniform float contrast      : hint_range(0.5, 2.0)  = 1.12;
uniform float saturation    : hint_range(0.0, 3.0)  = 1.18;
uniform float brightness    : hint_range(0.5, 1.5)  = 1.02;

// Warm highlight / cool shadow split-tone
uniform vec3  highlight_tint : source_color = vec3(1.04, 0.98, 0.90);  // warm
uniform vec3  shadow_tint    : source_color = vec3(0.88, 0.92, 1.05);  // cool-blue

// ── Vignette ─────────────────────────────────────────────────────────────────
uniform float vignette_strength : hint_range(0.0, 1.0) = 0.38;
uniform float vignette_radius   : hint_range(0.3, 1.5) = 0.75;
uniform float vignette_softness : hint_range(0.1, 1.0) = 0.55;

// ── Ambient light blob (faux global illumination) ────────────────────────────
uniform bool  ambient_enabled   = true;
uniform vec2  ambient_center    = vec2(0.5, 0.42);  // UV space
uniform vec4  ambient_color     : source_color = vec4(1.0, 0.97, 0.88, 1.0);
uniform float ambient_radius    : hint_range(0.0, 2.0) = 0.6;
uniform float ambient_intensity : hint_range(0.0, 0.5) = 0.12;

// ── Scanline / pixel grain (subtle retro feel) ────────────────────────────────
uniform bool  grain_enabled     = false;
uniform float grain_strength    : hint_range(0.0, 0.05) = 0.012;
uniform float time_speed        : hint_range(0.0, 5.0)  = 1.0;

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────
float luma(vec3 c) {
	return dot(c, vec3(0.299, 0.587, 0.114));
}

vec3 saturation_adjust(vec3 col, float s) {
	float grey = luma(col);
	return mix(vec3(grey), col, s);
}

float rand(vec2 co) {
	return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

// ─────────────────────────────────────────────────────────────────────────────
void fragment() {
	vec4 src = texture(TEXTURE, UV);
	vec3 col = src.rgb;

	// ── Brightness / Contrast ─────────────────────────────────────────────
	col = (col - 0.5) * contrast + 0.5;
	col = clamp(col * brightness, 0.0, 1.0);

	// ── Saturation ───────────────────────────────────────────────────────
	col = saturation_adjust(col, saturation);

	// ── Split-tone ───────────────────────────────────────────────────────
	float l = luma(col);
	vec3  tint = mix(shadow_tint, highlight_tint, smoothstep(0.2, 0.8, l));
	col = col * tint;

	// ── Ambient light blob ────────────────────────────────────────────────
	if (ambient_enabled) {
		float dist  = distance(UV, ambient_center);
		float light = (1.0 - smoothstep(0.0, ambient_radius, dist)) * ambient_intensity;
		col = col + ambient_color.rgb * light;
	}

	// ── Vignette ─────────────────────────────────────────────────────────
	vec2  centered = UV - vec2(0.5);
	float dist_vig = length(centered / vec2(1.0, 0.85));   // slightly elliptical
	float vig      = smoothstep(vignette_radius - vignette_softness,
	                            vignette_radius + vignette_softness, dist_vig);
	col = mix(col, col * (1.0 - vignette_strength), vig);

	// ── Grain ─────────────────────────────────────────────────────────────
	if (grain_enabled) {
		float g = rand(UV + fract(TIME * time_speed)) * 2.0 - 1.0;
		col += g * grain_strength;
	}

	col = clamp(col, 0.0, 1.0);
	COLOR = vec4(col, src.a);
}
