## shockwave_controller.gd — Controlador para shockwave.gdshader
## ================================================================
## SETUP:
##   1. Crea un CanvasLayer (layer alto, ej. 100) llamado "ShockwaveLayer"
##   2. Agrega un ColorRect hijo que cubra toda la pantalla
##   3. Asigna un ShaderMaterial con shockwave.gdshader al ColorRect
##   4. Adjunta este script al ColorRect
##
## USO DESDE CUALQUIER NODO:
##   # Obtener referencia al controlador
##   @onready var shockwave = $ShockwaveLayer/ColorRect
##
##   # Disparar onda desde posición global (ej. al recibir daño)
##   shockwave.trigger(global_position)
##
##   # Disparar con parámetros custom (ej. explosión más fuerte)
##   shockwave.trigger(global_position, 0.08, 0.6)
## ================================================================
extends ColorRect

## Fuerza máxima de la distorsión
@export var default_force: float = 0.04
## Radio máximo que alcanza la onda
@export var default_max_radius: float = 0.5
## Duración de la expansión en segundos
@export var expand_duration: float = 0.4

var _tween: Tween = null


func _ready() -> void:
	# Asegura que inicia sin efecto visible
	_reset()


## Dispara la onda de choque desde una posición global.
## force_override y max_radius_override permiten ajustar por caso.
func trigger(global_pos: Vector2, force_override: float = -1.0, max_radius_override: float = -1.0) -> void:
	# Cancelar onda anterior si aún corre
	if _tween and _tween.is_running():
		_tween.kill()

	var viewport_size = get_viewport_rect().size
	# Convertir posición global → UV normalizado (0-1)
	var uv_center = global_pos / viewport_size
	uv_center = uv_center.clamp(Vector2.ZERO, Vector2.ONE)

	var final_force = force_override if force_override > 0.0 else default_force
	var final_radius = max_radius_override if max_radius_override > 0.0 else default_max_radius

	var mat = material as ShaderMaterial
	mat.set_shader_parameter("center", uv_center)
	mat.set_shader_parameter("force", final_force)
	mat.set_shader_parameter("size", 0.0)

	# Animar: expandir el radio y desvanecer la fuerza
	_tween = create_tween().set_parallel(true)
	_tween.tween_method(_set_size, 0.0, final_radius, expand_duration)\
		.set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUAD)
	_tween.tween_method(_set_force, final_force, 0.0, expand_duration)\
		.set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
	_tween.chain().tween_callback(_reset)


func _set_size(value: float) -> void:
	(material as ShaderMaterial).set_shader_parameter("size", value)


func _set_force(value: float) -> void:
	(material as ShaderMaterial).set_shader_parameter("force", value)


func _reset() -> void:
	var mat = material as ShaderMaterial
	if mat:
		mat.set_shader_parameter("force", 0.0)
		mat.set_shader_parameter("size", 0.0)
