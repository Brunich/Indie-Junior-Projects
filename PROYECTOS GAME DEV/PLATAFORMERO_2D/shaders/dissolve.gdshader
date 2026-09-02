shader_type canvas_item;

// Dissolve shader para pixel art 2D
// Usa un patrón de ruido procedural para disolver el sprite pixel a pixel.
// Ideal para: muerte de enemigos, despawn, teletransporte, transiciones.
//
// USO:
//   1. Crear un ShaderMaterial y asignar este shader.
//   2. Aplicar el material al Sprite2D / AnimatedSprite2D.
//   3. Animar "dissolve_amount" de 0.0 (visible) a 1.0 (invisible).
//
// Ejemplo rápido en GDScript:
//   var tween = create_tween()
//   tween.tween_property($Sprite.material, "shader_parameter/dissolve_amount", 1.0, 0.6)

uniform float dissolve_amount : hint_range(0.0, 1.0) = 0.0;
uniform vec4 edge_color : source_color = vec4(1.0, 0.8, 0.2, 1.0); // color del borde de disolución
uniform float edge_width : hint_range(0.0, 0.15) = 0.05;

// Función de ruido pseudo-aleatorio basada en UV (simple y rápida para pixel art)
float rand(vec2 co) {
	return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

void fragment() {
	vec4 tex = texture(TEXTURE, UV);

	// Generar valor de ruido por pixel
	float noise = rand(floor(UV * vec2(textureSize(TEXTURE, 0))));

	// Calcular disolución
	float threshold = dissolve_amount;

	if (tex.a > 0.0) {
		if (noise < threshold - edge_width) {
			// Pixel completamente disuelto
			discard;
		} else if (noise < threshold) {
			// Pixel en el borde — mostrar color de borde
			COLOR = vec4(edge_color.rgb, tex.a);
		} else {
			// Pixel normal
			COLOR = tex;
		}
	} else {
		COLOR = tex;
	}
}
