## ============================================================
## screen_transition_controller.gd — Controla transiciones de escena
## Bruno Salas | UANL Monterrey | 2026
## ============================================================
## Añadir como Autoload (singleton) o nodo en un CanvasLayer de la escena raíz.
## Requiere un ColorRect hijo con screen_transition.gdshader asignado.
##
## Uso:
##   TransitionController.fade_out()                          # fade a negro
##   await TransitionController.fade_out()                    # espera hasta completar
##   await TransitionController.change_scene("res://...")     # transición completa
##
## Estructura de nodo recomendada:
##   CanvasLayer (layer=10)
##     └─ ScreenTransitionController (este script)
##                └─ ColorRect (full-screen, ShaderMaterial con screen_transition.gdshader)

extends Node
class_name ScreenTransitionController

# ---- PROPIEDADES ----
@export var color_rect_path: NodePath = ^"ColorRect"
@export var transition_color: Color = Color(0.0, 0.0, 0.0, 1.0)
@export var default_duration: float = 0.5

@onready var _rect: ColorRect = get_node(color_rect_path)

var _tween: Tween = null

func _ready() -> void:
	if not _rect:
		push_error("ScreenTransitionController: No se encontró ColorRect en '%s'" % color_rect_path)
		return
	if not _rect.material or not _rect.material is ShaderMaterial:
		push_warning("ScreenTransitionController: ColorRect no tiene ShaderMaterial con screen_transition.gdshader")
		return

	_rect.material.set_shader_parameter("transition_color", transition_color)
	_rect.material.set_shader_parameter("progress", 0.0)
	# Asegurarse de que el ColorRect cubra toda la pantalla
	_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE


func fade_out(duration: float = default_duration) -> void:
	## Cubre la pantalla (progress 0→1). Await para esperar a que termine.
	await _animate_progress(0.0, 1.0, duration)


func fade_in(duration: float = default_duration) -> void:
	## Descubre la pantalla (progress 1→0). Await para esperar a que termine.
	await _animate_progress(1.0, 0.0, duration)


func change_scene(path: String, duration: float = default_duration) -> void:
	## Hace fade out → cambia escena → fade in de forma automática.
	## Await para esperar a que la transición completa termine.
	await fade_out(duration)
	get_tree().change_scene_to_file(path)
	await get_tree().process_frame  # espera un frame para que la escena cargue
	await fade_in(duration)


func set_color(color: Color) -> void:
	## Cambia el color de la transición en tiempo real
	transition_color = color
	if _get_mat():
		_get_mat().set_shader_parameter("transition_color", color)


func set_progress(value: float) -> void:
	## Controla manualmente el progreso (0.0 = transparente, 1.0 = cubierto)
	if _get_mat():
		_get_mat().set_shader_parameter("progress", clampf(value, 0.0, 1.0))


# ---- INTERNAL ----
func _animate_progress(from: float, to: float, duration: float) -> void:
	if not _get_mat():
		return
	if _tween:
		_tween.kill()
	_tween = create_tween()
	_tween.set_ease(Tween.EASE_IN_OUT)
	_tween.set_trans(Tween.TRANS_SINE)
	_tween.tween_method(set_progress, from, to, duration)
	await _tween.finished


func _get_mat() -> ShaderMaterial:
	if _rect and _rect.material and _rect.material is ShaderMaterial:
		return _rect.material as ShaderMaterial
	return null
