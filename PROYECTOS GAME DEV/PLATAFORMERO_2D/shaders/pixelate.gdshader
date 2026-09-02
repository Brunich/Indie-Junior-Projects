// pixelate.gdshader
// Efecto pixelado — útil para transiciones de escena o efecto "retro boost".
// Aplica a un ColorRect o CanvasLayer que cubra toda la pantalla,
// o a un Sprite2D con ShaderMaterial.
//
// USO:
//   1. Crea un ShaderMaterial y asigna este shader.
//   2. Ajusta 'pixel_size' — valores altos = más pixelado (rango sugerido: 1.0 a 32.0).
//   3. Para transiciones: anima 'pixel_size' de 1.0 → 20.0 → 1.0 con un Tween.
//
// NOTA: Para que funcione correctamente en un ColorRect que cubra la pantalla,
//       activa "Use Parent Material" y asegúrate de pasar la textura de la escena.
//       Alternativa más simple: usar en un Sprite2D con la textura que quieras pixelar.

shader_type canvas_item;

/// Tamaño del "píxel" en la pantalla. 1.0 = sin efecto. 16.0 = muy pixelado.
uniform float pixel_size: hint_range(1.0, 64.0, 0.5) = 4.0;

void fragment() {
	// Obtiene el tamaño del texel (1 / resolución de la textura)
	vec2 texel = TEXTURE_PIXEL_SIZE;

	// Redondea las coordenadas UV al grid de 'pixel_size' texels
	vec2 uv = UV;
	uv = floor(uv / (texel * pixel_size)) * (texel * pixel_size);

	COLOR = texture(TEXTURE, uv);
}
