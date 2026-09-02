shader_type canvas_item;

// Palette Swap Shader para pixel art 2D
// Intercambia colores del sprite usando una textura de paleta (1xN).
// Fila 0 = colores originales, Fila 1 = colores de reemplazo.
// Ideal para: variantes de enemigos, power-ups, temas de mundo.

uniform sampler2D palette_texture : filter_nearest, repeat_disable;
uniform float tolerance : hint_range(0.0, 0.15, 0.005) = 0.02;
uniform float mix_amount : hint_range(0.0, 1.0) = 1.0;
uniform bool enabled = true;

void fragment() {
	vec4 original = texture(TEXTURE, UV);

	if (!enabled || original.a < 0.01) {
		COLOR = original;
		return;
	}

	// Leer tamaño de la paleta
	ivec2 pal_size = textureSize(palette_texture, 0);
	int num_colors = pal_size.x;

	vec4 result = original;

	for (int i = 0; i < num_colors; i++) {
		// Fila 0 (y=0.25): color original a buscar
		vec2 uv_from = vec2((float(i) + 0.5) / float(num_colors), 0.25);
		vec4 color_from = texture(palette_texture, uv_from);

		// Comparar con tolerancia (para pixel art basta con poca)
		if (distance(original.rgb, color_from.rgb) < tolerance) {
			// Fila 1 (y=0.75): color de reemplazo
			vec2 uv_to = vec2((float(i) + 0.5) / float(num_colors), 0.75);
			vec4 color_to = texture(palette_texture, uv_to);

			result = vec4(mix(original.rgb, color_to.rgb, mix_amount), original.a);
			break;
		}
	}

	COLOR = result;
}
