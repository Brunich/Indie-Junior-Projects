// hit_effect.gdshader
// ─────────────────────────────────────────────────────────────────────────────
// Damage / heal flash with an optional chromatic-aberration burst.
// Drive hit_progress from 0→1 via a tween in code.
// ─────────────────────────────────────────────────────────────────────────────
shader_type canvas_item;

/// 0 = no effect, 1 = full flash. Animate this via Tween.
uniform float hit_progress  : hint_range(0.0, 1.0) = 0.0;

/// Color of the flash (white for damage, green for heal, gold for power-up)
uniform vec4  flash_color   : source_color = vec4(1.0, 1.0, 1.0, 1.0);

/// How much the sprite expands outward during the flash (pixel units)
uniform float burst_scale   : hint_range(0.0, 0.3) = 0.06;

/// Chromatic aberration on impact (splits RGB channels)
uniform float chroma_strength : hint_range(0.0, 0.05) = 0.018;

void fragment() {
	if (hit_progress <= 0.0) {
		COLOR = texture(TEXTURE, UV);
		return;
	}

	// Ease-out curve: fast in, slow out
	float t  = 1.0 - pow(1.0 - hit_progress, 3.0);

	// Scale UV outward from center (punch effect)
	vec2  center  = vec2(0.5);
	vec2  scaled  = (UV - center) / (1.0 + burst_scale * t) + center;

	// Chromatic aberration: shift R and B channels slightly
	float chroma  = chroma_strength * t;
	vec2  offset  = normalize(UV - center) * chroma;

	float r = texture(TEXTURE, scaled + offset).r;
	float g = texture(TEXTURE, scaled).g;
	float b = texture(TEXTURE, scaled - offset).b;
	float a = texture(TEXTURE, scaled).a;

	vec4 col = vec4(r, g, b, a);

	// Flash overlay – fade over the hit_progress curve
	col.rgb  = mix(col.rgb, flash_color.rgb, t * flash_color.a);

	// Slight brightness boost at peak
	col.rgb += t * 0.15;

	COLOR = clamp(col, 0.0, 1.0);
}
