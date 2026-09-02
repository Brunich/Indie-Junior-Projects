## chromatic_aberration_controller.gd
## Controlador para el shader de aberración cromática.
##
## === SETUP ===
## 1. Asigna chromatic_aberration.gdshader como ShaderMaterial en tu Sprite2D.
## 2. Adjunta este script al nodo Sprite2D (o al nodo padre que tenga acceso).
## 3. Llama  trigger_aberration()  cuando el jugador reciba daño.
##
## === EJEMPLO EN EL PLAYER ===
##   func _on_hit():
##       $Sprite2D.get_node("chromatic_aberration_controller").trigger_aberration()
##   — o directamente si este script está en el Sprite2D —
##       trigger_aberration()

extends Node

## Nodo Sprite2D que tiene el ShaderMaterial con el shader de aberración.
@export var target_sprite: Sprite2D

## Intensidad máxima del efecto (en píxeles de offset).
@export var max_intensity: float = 3.0

## Duración del efecto en segundos.
@export var duration: float = 0.15

## Si es true, el efecto pulsa (sube y baja). Si es false, solo decae.
@export var pulse: bool = true

var _tween: Tween


func _ready() -> void:
	# Si no se asigna un target, intenta usar el padre.
	if target_sprite == null and get_parent() is Sprite2D:
		target_sprite = get_parent() as Sprite2D


## Dispara el efecto de aberración cromática.
func trigger_aberration() -> void:
	if target_sprite == null:
		push_warning("chromatic_aberration_controller: no hay Sprite2D asignado.")
		return

	var mat := target_sprite.material as ShaderMaterial
	if mat == null:
		push_warning("chromatic_aberration_controller: el Sprite2D no tiene ShaderMaterial.")
		return

	# Cancelar tween anterior si existe.
	if _tween and _tween.is_valid():
		_tween.kill()

	_tween = create_tween()

	if pulse:
		# Sube rápido a max_intensity, luego baja a 0.
		var half := duration * 0.3
		_tween.tween_method(_set_intensity.bind(mat), 0.0, max_intensity, half)
		_tween.tween_method(_set_intensity.bind(mat), max_intensity, 0.0, duration - half)
	else:
		# Arranca en max y decae a 0.
		mat.set_shader_parameter("intensity", max_intensity)
		_tween.tween_method(_set_intensity.bind(mat), max_intensity, 0.0, duration)


func _set_intensity(value: float, mat: ShaderMaterial) -> void:
	mat.set_shader_parameter("intensity", value)
