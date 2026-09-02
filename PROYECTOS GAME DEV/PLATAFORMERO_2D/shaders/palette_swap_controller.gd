## palette_swap_controller.gd
## Controlador para el shader palette_swap.gdshader
##
## === SETUP ===
## 1. Crear una imagen PNG de 2 filas (Nx2 px):
##    - Fila superior: los colores ORIGINALES del sprite (de izquierda a derecha)
##    - Fila inferior: los colores de REEMPLAZO correspondientes
##    Ejemplo para 4 colores -> imagen de 4x2 px.
##
## 2. Importar la imagen con Filter: Nearest y sin mipmaps.
##
## 3. Asignar ShaderMaterial con palette_swap.gdshader al Sprite2D.
##
## 4. En el Inspector del material, asignar la textura de paleta
##    a "Shader Params > Palette Texture".
##
## === USO ===
## Adjuntar este script al Sprite2D (o al nodo padre).
## Llamar swap_palette(nueva_paleta) para cambiar la paleta en runtime.
## Llamar reset_palette() para volver al aspecto original.
##
## === EJEMPLO RÁPIDO ===
## # Desde cualquier script:
## var sprite = $Sprite2D
## var controlador = sprite.get_node("PaletteSwapController")
## controlador.swap_palette(preload("res://assets/palettes/ice_palette.png"))

extends Node
class_name PaletteSwapController

@export var target_sprite: Sprite2D
@export var default_palette: Texture2D
@export var transition_duration: float = 0.3

var _tween: Tween

func _ready() -> void:
	if target_sprite == null:
		var parent = get_parent()
		if parent is Sprite2D:
			target_sprite = parent
		else:
			push_warning("PaletteSwapController: no se encontró Sprite2D target.")
			return

	if target_sprite.material == null or not target_sprite.material is ShaderMaterial:
		push_warning("PaletteSwapController: el sprite necesita un ShaderMaterial con palette_swap.gdshader.")
		return

	if default_palette:
		_get_mat().set_shader_parameter("palette_texture", default_palette)


func swap_palette(new_palette: Texture2D, instant: bool = false) -> void:
	var mat := _get_mat()
	if mat == null:
		return

	mat.set_shader_parameter("palette_texture", new_palette)

	if instant:
		mat.set_shader_parameter("mix_amount", 1.0)
	else:
		_animate_mix(0.0, 1.0)


func reset_palette(instant: bool = false) -> void:
	var mat := _get_mat()
	if mat == null:
		return

	if instant:
		mat.set_shader_parameter("mix_amount", 0.0)
		mat.set_shader_parameter("enabled", false)
	else:
		_animate_mix(1.0, 0.0)
		await get_tree().create_timer(transition_duration).timeout
		mat.set_shader_parameter("enabled", false)


func set_enabled(value: bool) -> void:
	var mat := _get_mat()
	if mat:
		mat.set_shader_parameter("enabled", value)


func _animate_mix(from: float, to: float) -> void:
	if _tween and _tween.is_running():
		_tween.kill()

	var mat := _get_mat()
	if mat == null:
		return

	mat.set_shader_parameter("enabled", true)
	mat.set_shader_parameter("mix_amount", from)
	_tween = create_tween()
	_tween.tween_method(
		func(val: float): mat.set_shader_parameter("mix_amount", val),
		from, to, transition_duration
	)


func _get_mat() -> ShaderMaterial:
	if target_sprite and target_sprite.material is ShaderMaterial:
		return target_sprite.material as ShaderMaterial
	return null
