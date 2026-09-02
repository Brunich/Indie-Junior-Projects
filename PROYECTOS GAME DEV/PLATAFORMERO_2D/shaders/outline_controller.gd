## ============================================================
## outline_controller.gd — Controla el outline de sprites pixel art
## Bruno Salas | UANL Monterrey | 2026
## ============================================================
## Nodo hijo del CharacterBody2D (player/enemigo/interactuable)
## Requiere que Sprite2D tenga outline.gdshader asignado como ShaderMaterial
##
## Uso rápido:
##   $OutlineController.show_outline()          # muestra outline
##   $OutlineController.hide_outline()          # oculta outline
##   $OutlineController.set_color(Color.RED)    # cambia color
##   $OutlineController.pulse(2.0)              # parpadeo por N segundos

extends Node
class_name OutlineController

# ---- PROPIEDADES ----
@export var sprite_path: NodePath = ^"../Sprite2D"
@export var default_color: Color = Color(0.0, 0.0, 0.0, 1.0)
@export var outline_width: float = 1.0
@export var visible_on_ready: bool = false

@onready var _sprite: Sprite2D = get_node(sprite_path)

var _pulsing: bool = false

func _ready() -> void:
	if not _sprite:
		push_error("OutlineController: No se encontró Sprite2D en '%s'" % sprite_path)
		return
	if not _sprite.material or not _sprite.material is ShaderMaterial:
		push_warning("OutlineController: Sprite2D no tiene ShaderMaterial con outline.gdshader")
		return

	_sprite.material.set_shader_parameter("outline_color", default_color)
	_sprite.material.set_shader_parameter("outline_width", outline_width)
	_sprite.material.set_shader_parameter("show_outline", visible_on_ready)


func show_outline(color: Color = default_color) -> void:
	## Muestra el outline con el color especificado (o el default)
	if not _get_mat():
		return
	_get_mat().set_shader_parameter("outline_color", color)
	_get_mat().set_shader_parameter("show_outline", true)


func hide_outline() -> void:
	## Oculta el outline
	if not _get_mat():
		return
	_get_mat().set_shader_parameter("show_outline", false)


func set_color(color: Color) -> void:
	## Cambia el color del outline en tiempo real
	if not _get_mat():
		return
	default_color = color
	_get_mat().set_shader_parameter("outline_color", color)


func set_width(width: float) -> void:
	## Cambia el grosor del outline (0.5 – 3.0 recomendado para pixel art)
	if not _get_mat():
		return
	outline_width = clampf(width, 0.5, 3.0)
	_get_mat().set_shader_parameter("outline_width", outline_width)


func pulse(duration: float = 2.0, color: Color = Color.WHITE, interval: float = 0.25) -> void:
	## Parpadea el outline durante N segundos (útil para indicar interacción disponible)
	if _pulsing:
		return
	_pulsing = true
	var elapsed: float = 0.0
	var visible: bool = true

	while elapsed < duration:
		if visible:
			show_outline(color)
		else:
			hide_outline()
		visible = not visible
		await get_tree().create_timer(interval).timeout
		elapsed += interval

	hide_outline()
	_pulsing = false


func highlight_for(duration: float = 1.0, color: Color = Color.YELLOW) -> void:
	## Muestra el outline durante N segundos y luego lo oculta (para pick-ups, diálogos, etc.)
	show_outline(color)
	await get_tree().create_timer(duration).timeout
	hide_outline()


# ---- INTERNAL ----
func _get_mat() -> ShaderMaterial:
	if _sprite and _sprite.material and _sprite.material is ShaderMaterial:
		return _sprite.material as ShaderMaterial
	return null
