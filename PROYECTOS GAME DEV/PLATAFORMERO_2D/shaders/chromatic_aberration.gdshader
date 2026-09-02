shader_type canvas_item;

// Chromatic Aberration — efecto de daño/glitch para pixel art 2D
// Separa los canales RGB para simular distorsión cromática.
// Úsalo en un Sprite2D con ShaderMaterial asignado.
//
// Uso rápido:
//   material.set_shader_parameter("intensity", 2.0)  -> activa
//   material.set_shader_parameter("intensity", 0.0)  -> desactiva
//
// Para pixel art se recomienda intensity entre 1.0 y 3.0 (pocos píxeles de offset).

uniform float intensity : hint_range(0.0, 10.0, 0.1) = 0.0;
uniform vec2 direction = vec2(1.0, 0.0); // dirección del desplazamiento

void fragment() {
	vec2 tex_size = TEXTURE_PIXEL_SIZE; // tamaño de un píxel en UV
	vec2 offset = direction * intensity * tex_size;

	float r = texture(TEXTURE, UV + offset).r;
	float g = texture(TEXTURE, UV).g;
	float b = texture(TEXTURE, UV - offset).b;
	float a = texture(TEXTURE, UV).a;

	COLOR = vec4(r, g, b, a);
}
