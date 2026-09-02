## water_reflection_controller.gd
## Controlador para el shader de agua con reflejo.
##
## ── SETUP ──
## 1. Agrega un ColorRect (o Sprite2D) como hijo de tu escena de nivel.
## 2. Redimensiónalo para cubrir la zona de agua.
## 3. Asigna un ShaderMaterial con water_reflection.gdshader.
## 4. Adjunta este script al mismo nodo.
## 5. (Opcional) Ajusta exported vars desde el Inspector.
##
## ── EJEMPLO DE USO ──
## Para agitar el agua cuando el jugador cae:
##   water_node.splash(player.global_position.x)

extends Node2D

@export var idle_amplitude: float = 0.01
@export var splash_amplitude: float = 0.04
@export var splash_duration: float = 0.6

@onready var material_ref: ShaderMaterial = material if material is ShaderMaterial else null

func _ready() -> void:
	# Intentar obtener el material del padre si este nodo es auxiliar
	if material_ref == null and get_parent() and get_parent().has_method("get"):
		var parent_mat = get_parent().get("material")
		if parent_mat is ShaderMaterial:
			material_ref = parent_mat
	if material_ref:
		material_ref.set_shader_parameter("wave_amplitude", idle_amplitude)

## Llama esta función cuando el jugador caiga al agua.
## center_x: posición X del impacto (no se usa aún, reservado para futuro).
func splash(_center_x: float = 0.0) -> void:
	if material_ref == null:
		return
	material_ref.set_shader_parameter("wave_amplitude", splash_amplitude)
	var tween = create_tween()
	tween.tween_method(_set_amplitude, splash_amplitude, idle_amplitude, splash_duration)
	tween.set_ease(Tween.EASE_OUT)
	tween.set_trans(Tween.TRANS_SINE)

func _set_amplitude(value: float) -> void:
	if material_ref:
		material_ref.set_shader_parameter("wave_amplitude", value)
