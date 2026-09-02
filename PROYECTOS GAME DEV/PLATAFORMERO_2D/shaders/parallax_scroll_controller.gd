## parallax_scroll_controller.gd
## Controlador para parallax_scroll.gdshader en Godot 4
##
## SETUP:
##   - Adjunta este script al TextureRect (o Sprite2D) que tenga el ShaderMaterial
##     con parallax_scroll.gdshader asignado.
##   - Asigna la referencia a la cámara (camera_node) en el Inspector o en código.
##
## ESTRUCTURA RECOMENDADA DE ESCENA:
##   World
##   ├── Camera2D          ← la cámara del jugador
##   ├── BG_Layer_Far      ← TextureRect con este script, parallax_speed = 0.2
##   ├── BG_Layer_Mid      ← TextureRect con este script, parallax_speed = 0.5
##   ├── BG_Layer_Near     ← TextureRect con este script, parallax_speed = 0.8
##   └── Player

extends TextureRect  # Cambia a Sprite2D si usas Sprite2D

## Referencia a la cámara — asigna en el Inspector o usa get_node()
@export var camera_node: Camera2D

## Velocidad de parallax de esta capa (sobreescribe el uniform del shader si se usa esta propiedad)
## 0.0 = estático, 1.0 = sigue la cámara exacto, 0.5 = parallax medio
@export var parallax_speed: float = 0.5

## Si true, también hace scroll vertical (útil para cielos con nubes)
@export var scroll_vertical: bool = false

# Posición de la cámara en el frame anterior para calcular el delta
var _last_camera_pos: Vector2 = Vector2.ZERO

# Acumulador del offset de scroll (se manda al shader)
var _scroll_offset: Vector2 = Vector2.ZERO

func _ready() -> void:
	# Intentar encontrar la cámara automáticamente si no fue asignada
	if camera_node == null:
		camera_node = get_viewport().get_camera_2d()

	if camera_node:
		_last_camera_pos = camera_node.global_position

	# Sincroniza el parallax_speed con el uniform del shader
	if material and material is ShaderMaterial:
		(material as ShaderMaterial).set_shader_parameter("parallax_speed", parallax_speed)


func _process(_delta: float) -> void:
	if camera_node == null or not (material is ShaderMaterial):
		return

	# Delta de movimiento de la cámara este frame
	var cam_delta: Vector2 = camera_node.global_position - _last_camera_pos
	_last_camera_pos = camera_node.global_position

	# Acumulamos el offset — dividido entre el tamaño de la textura para normalizar a UV
	var tex_size: Vector2 = get_texture_size()
	if tex_size.x > 0 and tex_size.y > 0:
		_scroll_offset.x += cam_delta.x / tex_size.x
		if scroll_vertical:
			_scroll_offset.y += cam_delta.y / tex_size.y

	# Enviamos el offset acumulado al shader
	(material as ShaderMaterial).set_shader_parameter("scroll_offset", _scroll_offset)


## Reinicia el scroll (útil al cambiar de escena o hacer respawn)
func reset_scroll() -> void:
	_scroll_offset = Vector2.ZERO
	if material is ShaderMaterial:
		(material as ShaderMaterial).set_shader_parameter("scroll_offset", Vector2.ZERO)


## Helper para obtener el tamaño de la textura asignada
func get_texture_size() -> Vector2:
	if texture:
		return Vector2(texture.get_width(), texture.get_height())
	return Vector2(256.0, 256.0)  # fallback
