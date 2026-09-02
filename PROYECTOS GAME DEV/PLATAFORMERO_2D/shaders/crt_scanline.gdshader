shader_type canvas_item;

// CRT Scanline Shader — efecto retro para pixel art 2D
// Aplica sobre un ColorRect que cubra toda la pantalla (CanvasLayer).
// Usa SCREEN_TEXTURE como fuente.

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;
uniform float scanline_strength : hint_range(0.0, 1.0) = 0.35;
uniform float scanline_frequency : hint_range(1.0, 600.0) = 180.0;
uniform float vignette_strength : hint_range(0.0, 1.0) = 0.25;
uniform float brightness_boost : hint_range(0.0, 0.5) = 0.08;
uniform float curvature : hint_range(0.0, 0.1) = 0.0;
uniform bool enabled = true;

// Distorsión de curvatura CRT (sutil)
vec2 curve_uv(vec2 uv) {
	uv = uv * 2.0 - 1.0;
	vec2 offset = abs(uv.yx) * curvature;
	uv = uv + uv * offset;
	uv = uv * 0.5 + 0.5;
	return uv;
}

void fragment() {
	if (!enabled) {
		COLOR = texture(screen_texture, SCREEN_UV);
		return;
	}

	// Curvatura opcional
	vec2 uv = (curvature > 0.001) ? curve_uv(SCREEN_UV) : SCREEN_UV;

	// Descartar píxeles fuera de pantalla cuando hay curvatura
	if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
		COLOR = vec4(0.0);
		return;
	}

	vec4 col = texture(screen_texture, uv);

	// Scanlines — oscurecen líneas alternas usando la coordenada Y en pantalla
	float scanline = sin(uv.y * scanline_frequency * PI) * 0.5 + 0.5;
	scanline = mix(1.0, scanline, scanline_strength);
	col.rgb *= scanline;

	// Brightness boost para compensar la pérdida por scanlines
	col.rgb += brightness_boost;

	// Viñeta — oscurece bordes de la pantalla
	vec2 vig_uv = uv * (1.0 - uv);
	float vignette = vig_uv.x * vig_uv.y * 15.0;
	vignette = clamp(pow(vignette, vignette_strength), 0.0, 1.0);
	col.rgb *= vignette;

	COLOR = col;
}
