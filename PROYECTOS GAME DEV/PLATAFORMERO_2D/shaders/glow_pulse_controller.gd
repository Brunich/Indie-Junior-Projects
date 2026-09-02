## glow_pulse_controller.gd
## Controlador para el shader de brillo pulsante en coleccionables.
##
## ── SETUP ──
## 1. Adjunta este script al Sprite2D de tu coleccionable.
## 2. El Sprite2D debe tener ShaderMaterial con glow_pulse.gdshader.
## 3. Llama collect() cuando el jugador lo recoja para el efecto de "burst".
##
## ── EJEMPLO DE USO ──
## En tu escena de coleccionable:
##   func _on_body_entered(body):
##       if body.is_in_group("player"):
##           $Sprite2D.get_node("glow_pulse_controller").collect()
##           # O directamente:
##           # glow_controller.collect()

extends Node

@export var burst_intensity: float = 3.0
@export var burst_duration: float = 0.3
@export var normal_intensity: float = 1.2

@onready var sprite: Node = get_parent()
var material_ref: ShaderMaterial = null

func _ready() -> void:
	if sprite and sprite.get("material") is ShaderMaterial:
		material_ref = sprite.get("material")
		material_ref.set_shader_parameter("glow_intensity", normal_intensity)

## Llama esto al recoger el coleccionable.
## Produce un destello intenso antes de desaparecer.
func collect() -> void:
	if material_ref == null:
		return
	# Burst de brillo
	material_ref.set_shader_parameter("glow_intensity", burst_intensity)
	material_ref.set_shader_parameter("pulse_speed", 12.0) # Pulso rápido

	var tween = create_tween()
	tween.tween_property(sprite, "modulate:a", 0.0, burst_duration)
	tween.set_ease(Tween.EASE_OUT)
	tween.set_trans(Tween.TRANS_QUAD)
	tween.tween_callback(sprite.queue_free)

## Habilita/deshabilita el efecto glow desde código.
func set_glow_enabled(value: bool) -> void:
	if material_ref:
		material_ref.set_shader_parameter("enabled", value)
