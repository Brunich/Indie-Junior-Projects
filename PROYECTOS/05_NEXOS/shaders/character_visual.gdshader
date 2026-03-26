// character_visual.gdshader
// ─────────────────────────────────────────────────────────────────────────────
// All-in-one 2D character shader inspired by Pokémon Gamma Emerald's look:
//   • Crisp pixel-art sampling (no blur)
//   • 4-color palette swap for skins
//   • Thick outline (configurable color & width)
//   • Soft drop-shadow with blur & offset
//   • Rim / edge highlight for a slightly 3-D feel
//   • Hit-flash overlay (set hit_amount 0→1 in code)
// ─────────────────────────────────────────────────────────────────────────────
shader_type canvas_item;
render_mode unshaded;

// ── Palette Swap ─────────────────────────────────────────────────────────────
uniform bool  palette_enabled   = true;
uniform vec4  src_primary       : source_color = vec4(1.0, 0.0, 0.0, 1.0);
uniform vec4  src_secondary     : source_color = vec4(0.8, 0.0, 0.0, 1.0);
uniform vec4  src_accent        : source_color = vec4(0.5, 0.0, 0.0, 1.0);
uniform vec4  src_dark          : source_color = vec4(0.1, 0.0, 0.0, 1.0);

uniform vec4  dst_primary       : source_color = vec4(1.0, 0.0, 0.0, 1.0);
uniform vec4  dst_secondary     : source_color = vec4(0.8, 0.0, 0.0, 1.0);
uniform vec4  dst_accent        : source_color = vec4(0.5, 0.0, 0.0, 1.0);
uniform vec4  dst_dark          : source_color = vec4(0.1, 0.0, 0.0, 1.0);
uniform float palette_threshold : hint_range(0.0, 0.3) = 0.08;

// ── Outline ───────────────────────────────────────────────────────────────────
uniform bool  outline_enabled   = true;
uniform vec4  outline_color     : source_color = vec4(0.05, 0.02, 0.08, 1.0);
uniform float outline_width     : hint_range(0.5, 6.0) = 2.0;

// ── Drop Shadow ───────────────────────────────────────────────────────────────
uniform bool  shadow_enabled    = true;
uniform vec4  shadow_color      : source_color = vec4(0.0, 0.0, 0.0, 0.45);
uniform vec2  shadow_offset     = vec2(3.0, 4.0);   // pixels
uniform float shadow_softness   : hint_range(0.0, 8.0) = 2.5;

// ── Rim Highlight ─────────────────────────────────────────────────────────────
uniform bool  rim_enabled       = true;
uniform vec4  rim_color         : source_color = vec4(1.0, 0.95, 0.8, 0.35);
uniform float rim_sharpness     : hint_range(1.0, 20.0) = 6.0;
uniform vec2  light_direction   = vec2(-0.5, -1.0);  // normalized in code

// ── Hit Flash ─────────────────────────────────────────────────────────────────
uniform float hit_amount        : hint_range(0.0, 1.0) = 0.0;
uniform vec4  hit_color         : source_color = vec4(1.0, 1.0, 1.0, 1.0);

// ── Overall Tint ──────────────────────────────────────────────────────────────
uniform vec4  overall_tint      : source_color = vec4(1.0, 1.0, 1.0, 1.0);

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────
vec4 sample_pixel(sampler2D tex, vec2 uv) {
	// Point sampling keeps pixel art crisp
	return texture(tex, uv);
}

float alpha_at(sampler2D tex, vec2 uv) {
	if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) return 0.0;
	return texture(tex, uv).a;
}

// Swap a pixel colour if it matches one of the four palette slots
vec4 apply_palette(vec4 col) {
	if (!palette_enabled) return col;
	float t = palette_threshold;
	if (distance(col.rgb, src_primary.rgb)   < t) return vec4(dst_primary.rgb,   col.a);
	if (distance(col.rgb, src_secondary.rgb) < t) return vec4(dst_secondary.rgb, col.a);
	if (distance(col.rgb, src_accent.rgb)    < t) return vec4(dst_accent.rgb,    col.a);
	if (distance(col.rgb, src_dark.rgb)      < t) return vec4(dst_dark.rgb,      col.a);
	return col;
}

// ─────────────────────────────────────────────────────────────────────────────
void fragment() {
	vec2 tex_size   = vec2(textureSize(TEXTURE, 0));
	vec2 pixel_size = TEXTURE_PIXEL_SIZE;   // 1/tex_size

	// ── Drop shadow (render first / behind everything) ────────────────────
	float shadow_alpha = 0.0;
	if (shadow_enabled) {
		vec2 shadow_uv = UV - shadow_offset * pixel_size;
		if (shadow_softness < 0.5) {
			shadow_alpha = alpha_at(TEXTURE, shadow_uv);
		} else {
			// Simple box blur over a cross kernel
			float steps  = ceil(shadow_softness);
			float total  = 0.0;
			float weight = 0.0;
			for (float dx = -steps; dx <= steps; dx++) {
				for (float dy = -steps; dy <= steps; dy++) {
					float w = max(0.0, steps + 1.0 - length(vec2(dx, dy)));
					total  += alpha_at(TEXTURE, shadow_uv + vec2(dx, dy) * pixel_size) * w;
					weight += w;
				}
			}
			shadow_alpha = total / max(weight, 0.0001);
		}
	}

	// ── Main sprite colour ────────────────────────────────────────────────
	vec4 col = sample_pixel(TEXTURE, UV);
	col      = apply_palette(col);

	// ── Outline ───────────────────────────────────────────────────────────
	float outline_alpha = 0.0;
	if (outline_enabled && col.a < 0.5) {
		float w = outline_width;
		float oa = 0.0;
		oa = max(oa, alpha_at(TEXTURE, UV + vec2( w,  0) * pixel_size));
		oa = max(oa, alpha_at(TEXTURE, UV + vec2(-w,  0) * pixel_size));
		oa = max(oa, alpha_at(TEXTURE, UV + vec2( 0,  w) * pixel_size));
		oa = max(oa, alpha_at(TEXTURE, UV + vec2( 0, -w) * pixel_size));
		oa = max(oa, alpha_at(TEXTURE, UV + vec2( w,  w) * pixel_size) * 0.7);
		oa = max(oa, alpha_at(TEXTURE, UV + vec2(-w,  w) * pixel_size) * 0.7);
		oa = max(oa, alpha_at(TEXTURE, UV + vec2( w, -w) * pixel_size) * 0.7);
		oa = max(oa, alpha_at(TEXTURE, UV + vec2(-w, -w) * pixel_size) * 0.7);
		outline_alpha = oa;
	}

	// ── Rim highlight ─────────────────────────────────────────────────────
	if (rim_enabled && col.a > 0.5) {
		vec2 light_dir = normalize(light_direction);
		// Sample gradient: alpha drop-off in the light direction → edge pixel
		float edge = alpha_at(TEXTURE, UV - light_dir * pixel_size);
		edge = 1.0 - edge;                        // 1 = edge facing light
		edge = pow(clamp(edge, 0.0, 1.0), rim_sharpness);
		col.rgb = mix(col.rgb, rim_color.rgb, edge * rim_color.a);
	}

	// ── Hit flash ─────────────────────────────────────────────────────────
	if (hit_amount > 0.0 && col.a > 0.5) {
		col.rgb = mix(col.rgb, hit_color.rgb, hit_amount * hit_color.a);
	}

	// ── Compose layers: shadow → outline → sprite ─────────────────────────
	vec4 result = vec4(0.0);

	// Shadow layer
	if (shadow_enabled) {
		vec4 sh = shadow_color;
		sh.a   *= shadow_alpha * (1.0 - col.a);   // shadow only where sprite is transparent
		result  = mix(result, sh, sh.a);
	}

	// Outline layer
	if (outline_alpha > 0.0) {
		result = mix(result, outline_color, outline_alpha * (1.0 - col.a));
	}

	// Sprite layer
	result = mix(result, col * overall_tint, col.a);

	COLOR = result;
}
