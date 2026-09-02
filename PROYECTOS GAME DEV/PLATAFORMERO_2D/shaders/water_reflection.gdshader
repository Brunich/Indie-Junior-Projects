shader_type canvas_item;

// ── Water Reflection Shader para Plataformero 2D ──
// Crea un efecto de agua con distorsión ondulante y tinte azul.
// Uso: Asignar como ShaderMaterial a un Sprite2D/ColorRect que cubra
//      la zona de agua. El sprite debe tener Z-Index alto (ej: 1000)
//      para que refleje los objetos debajo.
//
// Cómo usar:
//   1. Crea un ColorRect o Sprite2D del tamaño de tu zona de agua
//   2. En Inspector > Material > asigna un nuevo ShaderMaterial
//   3. En ShaderMaterial > Shader > carga este archivo .gdshader
//   4. Ajusta los uniforms desde el Inspector

uniform float wave_speed : hint_range(0.5, 5.0) = 1.5;
uniform float wave_amplitude : hint_range(0.001, 0.05) = 0.01;
uniform float wave_frequency : hint_range(1.0, 30.0) = 10.0;
uniform vec4 water_tint : source_color = vec4(0.1, 0.3, 0.6, 0.45);
uniform float pixelation : hint_range(1.0, 16.0) = 4.0;
uniform bool enable_reflection = true;

void fragment() {
	vec2 uv = UV;

	// Pixelar las coordenadas para estilo pixel art
	vec2 pixel_size = TEXTURE_PIXEL_SIZE * pixelation;
	uv = floor(uv / pixel_size) * pixel_size;

	// Distorsión ondulante
	float wave = sin(uv.x * wave_frequency + TIME * wave_speed) * wave_amplitude;
	float wave2 = cos(uv.y * wave_frequency * 0.7 + TIME * wave_speed * 0.8) * wave_amplitude * 0.5;

	vec2 distorted_uv = uv + vec2(wave2, wave);

	// Reflejo vertical (voltea Y) si está habilitado
	vec2 reflect_uv = distorted_uv;
	if (enable_reflection) {
		reflect_uv.y = 1.0 - reflect_uv.y;
	}

	// Obtener color base con SCREEN_TEXTURE para reflejar lo que hay arriba
	vec4 base_col = texture(TEXTURE, reflect_uv);

	// Mezclar con tinte de agua
	vec4 final_color = mix(base_col, water_tint, water_tint.a);
	final_color.a = base_col.a * 0.8 + 0.2; // Semitransparente

	COLOR = final_color;
}
