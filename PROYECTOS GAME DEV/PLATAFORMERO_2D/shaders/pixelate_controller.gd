## pixelate_controller.gd
## Controlador para el shader pixelate.gdshader.
## Adjunta este script al nodo Sprite2D o ColorRect que tenga el ShaderMaterial.
##
## USO TÍPICO — transición entre escenas:
##   1. Agrega un CanvasLayer (capa alta, ej: layer 10) en tu escena de UI.
##   2. Dentro del CanvasLayer, agrega un ColorRect que cubra toda la pantalla.
##   3. Asigna pixelate.gdshader como ShaderMaterial al ColorRect.
##   4. Adjunta este script al ColorRect.
##   5. Llama pixelate_in() antes de cambiar escena, y pixelate_out() al entrar.
##
## EJEMPLO RÁPIDO en cualquier nodo:
##   # Pixelar en 0.5s, luego despixelar:
##   $CanvasLayer/ColorRect.pixelate_transition(0.5)

extends Node  # Cambia a Sprite2D o ColorRect según tu nodo

@export var max_pixel_size: float = 24.0
@export var transition_duration: float = 0.4

var _mat: ShaderMaterial = null


func _ready() -> void:
	# Asume que el material del nodo padre es el ShaderMaterial con pixelate.gdshader
	if get_parent() and get_parent() is CanvasItem:
		_mat = get_parent().material as ShaderMaterial
	if _mat == null:
		push_warning("pixelate_controller: no se encontró ShaderMaterial en el nodo padre.")


## Pixela progresivamente (1 → max_pixel_size)
func pixelate_in(duration: float = transition_duration) -> void:
	if _mat == null:
		return
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tween.tween_method(_set_pixel_size, 1.0, max_pixel_size, duration)


## Despixela progresivamente (max_pixel_size → 1)
func pixelate_out(duration: float = transition_duration) -> void:
	if _mat == null:
		return
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_method(_set_pixel_size, max_pixel_size, 1.0, duration)


## Efecto completo: pixela y luego despixela (útil para transición de escena)
func pixelate_transition(duration: float = transition_duration) -> void:
	if _mat == null:
		return
	var half := duration / 2.0
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_QUAD)
	tween.tween_method(_set_pixel_size, 1.0, max_pixel_size, half).set_ease(Tween.EASE_IN)
	tween.tween_method(_set_pixel_size, max_pixel_size, 1.0, half).set_ease(Tween.EASE_OUT)


func _set_pixel_size(value: float) -> void:
	if _mat:
		_mat.set_shader_parameter("pixel_size", value)
