## ============================================================
## hit_flash_controller.gd — Automatiza el efecto hit flash
## Bruno Salas | UANL Monterrey | 2026
## ============================================================
## Nodo hijo del CharacterBody2D (player/enemigo)
## Requiere que Sprite2D tenga hit_flash.gdshader asignado

extends Node
class_name HitFlashController

# ---- PROPIEDADES ----
@export var flash_duration: float = 0.12
@export var sprite_path: NodePath = ^"../Sprite2D"
@export var flash_intensity: float = 1.0

@onready var _sprite: Sprite2D = get_node(sprite_path)

var _flashing: bool = false

func _ready() -> void:
	if not _sprite:
		push_error("HitFlashController: No se encontró Sprite2D en %s" % sprite_path)
		return

	# Verificar que el material existe y es ShaderMaterial
	if not _sprite.material or not _sprite.material is ShaderMaterial:
		push_warning("HitFlashController: Sprite2D no tiene ShaderMaterial con hit_flash.gdshader")

func flash() -> void:
	## Activa el efecto de flash durante flash_duration
	if _flashing or not _sprite or not _sprite.material:
		return

	_flashing = true

	# Activar el flash en el shader
	_sprite.material.set_shader_parameter("flash", true)
	_sprite.material.set_shader_parameter("flash_intensity", flash_intensity)

	await get_tree().create_timer(flash_duration).timeout

	# Desactivar el flash
	_sprite.material.set_shader_parameter("flash", false)
	_flashing = false

func flash_rapid(count: int = 3, interval: float = 0.08) -> void:
	## Flash rápido repetido (útil para daño mayor)
	for i in count:
		flash()
		await get_tree().create_timer(interval).timeout
