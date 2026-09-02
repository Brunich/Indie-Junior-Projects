## parallax_scroll.gdshader
## Godot 4 — shader_type canvas_item
## Desplazamiento procedural de fondo tipo parallax para plataformero 2D pixel art.
##
## USO:
##   1. Agrega un TextureRect (o Sprite2D) como fondo en tu escena.
##   2. En Inspector > Material, crea un ShaderMaterial.
##   3. Asigna este shader al ShaderMaterial.
##   4. Asigna tu textura de fondo en el parámetro "bg_texture".
##   5. Controla scroll_offset desde GDScript (ver parallax_scroll_controller.gd).
##
## OPTIMIZACIÓN PIXEL ART:
##   - Usa filter_nearest en la textura para mantener el aspecto pixelado.
##   - Activa "Repeat" en Import settings de la textura para que se repita correctamente.

shader_type canvas_item;

/// Textura de fondo (debe tener Repeat activado en Import settings)
uniform sampler2D bg_texture : repeat_enable, filter_nearest;

/// Desplazamiento acumulado del scroll (se actualiza desde GDScript cada frame)
uniform vec2 scroll_offset = vec2(0.0, 0.0);

/// Velocidad de parallax relativa: 1.0 = igual que la cámara, 0.5 = mitad (más lento = más lejos)
uniform float parallax_speed : hint_range(0.0, 1.0) = 0.5;

/// Cuántas veces se repite la textura en pantalla (tile scale)
uniform vec2 tile_scale = vec2(1.0, 1.0);

void fragment() {
	// Ajustamos el UV base con tile_scale para controlar el tamaño del tile
	vec2 uv = UV * tile_scale;

	// Aplicamos el desplazamiento de parallax escalado por la velocidad relativa
	// El efecto: capas con parallax_speed bajo se mueven más lento = parecen más lejanas
	uv += scroll_offset * parallax_speed;

	// Muestreamos la textura con repeat (el fmod/fract lo maneja el sampler con repeat_enable)
	COLOR = texture(bg_texture, uv);
}
