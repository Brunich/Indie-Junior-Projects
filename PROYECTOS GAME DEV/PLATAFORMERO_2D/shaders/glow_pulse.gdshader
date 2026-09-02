shader_type canvas_item;

// ── Glow Pulse Shader para Plataformero 2D ──
// Efecto de brillo pulsante para coleccionables, power-ups, monedas, etc.
// Da un aura luminosa que crece y decrece rítmicamente.
//
// Cómo usar:
//   1. Selecciona tu Sprite2D del coleccionable
//   2. En Inspector > Material > asigna un nuevo ShaderMaterial
//   3. En ShaderMaterial > Shader > carga este archivo .gdshader
//   4. Ajusta glow_color al color deseado del brillo

uniform vec4 glow_color : source_color = vec4(1.0, 0.85, 0.2, 1.0); // Dorado por defecto
uniform float glow_intensity : hint_range(0.0, 3.0) = 1.2;
uniform float pulse_speed : hint_range(0.5, 8.0) = 2.5;
uniform float glow_radius : hint_range(0.5, 4.0) = 1.5;
uniform bool enabled = true;

void fragment() {
	vec4 col = texture(TEXTURE, UV);

	if (!enabled || col.a < 0.01) {
		COLOR = col;
		return;
	}

	// Factor de pulso senoidal (0.0 a 1.0)
	float pulse = (sin(TIME * pulse_speed) + 1.0) * 0.5;

	// Detectar bordes: si hay un píxel transparente adyacente, es borde
	float px = TEXTURE_PIXEL_SIZE.x * glow_radius;
	float py = TEXTURE_PIXEL_SIZE.y * glow_radius;

	float a_left  = texture(TEXTURE, UV + vec2(-px, 0.0)).a;
	float a_right = texture(TEXTURE, UV + vec2( px, 0.0)).a;
	float a_up    = texture(TEXTURE, UV + vec2(0.0, -py)).a;
	float a_down  = texture(TEXTURE, UV + vec2(0.0,  py)).a;

	float edge = step(0.01, col.a) * (1.0 - min(min(a_left, a_right), min(a_up, a_down)));

	// Mezclar glow en bordes + leve glow general
	float glow_factor = edge * pulse * glow_intensity + pulse * 0.15 * glow_intensity;
	vec3 final_rgb = mix(col.rgb, glow_color.rgb, glow_factor);

	COLOR = vec4(final_rgb, col.a);
}
