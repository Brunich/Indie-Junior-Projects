## screen_shake.gd
## Agita la cámara al recibir daño usando Tween.
## Adjunta este script a tu Camera2D en la escena del jugador.
##
## USO BÁSICO:
##   # Desde cualquier nodo con referencia a la cámara:
##   $Camera2D.shake(0.3, 8.0)
##   # O desde el mismo nodo si este script está en la Camera2D:
##   shake(0.3, 8.0)
##
## USO RECOMENDADO (señal desde el Player):
##   # En player.gd, al recibir daño:
##   get_node("Camera2D").shake(0.25, 10.0)
##
## PARÁMETROS:
##   duration  - duración total del shake en segundos (ej: 0.3)
##   intensity - desplazamiento máximo en píxeles (ej: 8.0)

extends Camera2D

@export var default_duration: float = 0.3
@export var default_intensity: float = 8.0

var _shake_tween: Tween = null
var _shake_intensity: float = 0.0


func shake(duration: float = default_duration, intensity: float = default_intensity) -> void:
	# Cancela cualquier shake anterior
	if _shake_tween and _shake_tween.is_valid():
		_shake_tween.kill()

	_shake_intensity = intensity
	offset = Vector2.ZERO

	_shake_tween = create_tween()
	_shake_tween.set_trans(Tween.TRANS_SINE)
	_shake_tween.set_ease(Tween.EASE_OUT)

	# Anima la intensidad de 'intensity' a 0 durante 'duration' segundos
	_shake_tween.tween_method(_apply_shake, intensity, 0.0, duration)
	_shake_tween.tween_callback(_reset_offset)


func _apply_shake(current_intensity: float) -> void:
	_shake_intensity = current_intensity
	offset = Vector2(
		randf_range(-_shake_intensity, _shake_intensity),
		randf_range(-_shake_intensity, _shake_intensity)
	)


func _reset_offset() -> void:
	offset = Vector2.ZERO
	_shake_intensity = 0.0
