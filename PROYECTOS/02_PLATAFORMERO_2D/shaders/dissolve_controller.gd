## dissolve_controller.gd
## Controlador para el shader dissolve.gdshader
##
## USO:
##   1. Adjuntar este script al nodo que tiene el Sprite con el ShaderMaterial.
##   2. Asegurarse de que el Sprite hijo se llame "Sprite2D" (o cambiar la referencia).
##   3. Llamar dissolve() para disolver, y appear() para reaparecer.
##
## Ejemplo desde otro script (ej. enemy.gd al morir):
##   $DissolveController.dissolve()
##   await $DissolveController.dissolve_finished
##   queue_free()

extends Node

signal dissolve_finished
signal appear_finished

@export var sprite_path : NodePath = "Sprite2D"
@export var duration : float = 0.6
@export var edge_color : Color = Color(1.0, 0.8, 0.2, 1.0)

var _sprite : CanvasItem
var _tween : Tween


func _ready() -> void:
	_sprite = get_node_or_null(sprite_path)
	if _sprite == null:
		# Intentar buscar primer hijo CanvasItem
		for child in get_parent().get_children():
			if child is Sprite2D or child is AnimatedSprite2D:
				_sprite = child
				break

	if _sprite and _sprite.material is ShaderMaterial:
		_sprite.material.set_shader_parameter("edge_color", edge_color)


## Disuelve el sprite de visible a invisible.
func dissolve() -> void:
	if _sprite == null or not _sprite.material is ShaderMaterial:
		push_warning("DissolveController: No se encontró sprite con ShaderMaterial.")
		dissolve_finished.emit()
		return

	_kill_tween()
	_sprite.material.set_shader_parameter("dissolve_amount", 0.0)
	_tween = create_tween()
	_tween.tween_property(
		_sprite.material,
		"shader_parameter/dissolve_amount",
		1.0,
		duration
	).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_QUAD)
	_tween.finished.connect(func(): dissolve_finished.emit())


## Reaparece el sprite de invisible a visible.
func appear() -> void:
	if _sprite == null or not _sprite.material is ShaderMaterial:
		push_warning("DissolveController: No se encontró sprite con ShaderMaterial.")
		appear_finished.emit()
		return

	_kill_tween()
	_sprite.material.set_shader_parameter("dissolve_amount", 1.0)
	_tween = create_tween()
	_tween.tween_property(
		_sprite.material,
		"shader_parameter/dissolve_amount",
		0.0,
		duration
	).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUAD)
	_tween.finished.connect(func(): appear_finished.emit())


func _kill_tween() -> void:
	if _tween and _tween.is_running():
		_tween.kill()
