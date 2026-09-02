## ============================================================
## checkpoint.gd — Sistema de Checkpoints
## Bruno Salas | UANL Monterrey | 2026
## ============================================================
## Guarda posición de spawn, respawn al morir
## Conexión con GameManager para persistencia

extends Area2D
class_name Checkpoint

# ---- PROPIEDADES ----
@export var checkpoint_id: int = 0
@export var is_active: bool = false

# ---- SEÑALES ----
signal checkpoint_activated(checkpoint_id: int, spawn_pos: Vector2)

@onready var sprite = $Sprite2D
@onready var collision = $CollisionShape2D

var _activated: bool = false
var _particles: GPUParticles2D

func _ready() -> void:
	area_entered.connect(_on_area_entered)
	_create_particles()
	_update_visual()

func _on_area_entered(area: Area2D) -> void:
	if _activated:
		return

	# Solo el authority puede activar checkpoints en multiplayer
	if not is_multiplayer_authority():
		return

	var player = area.get_parent() if area.is_in_group("player_hitbox") else null
	if not player:
		return

	activate.rpc_id(1)  # Notificar al servidor

@rpc("authority", "call_local", "reliable")
func activate() -> void:
	_activated = true
	_update_visual()
	checkpoint_activated.emit(checkpoint_id, global_position)

	# Notificar al GameManager
	var gm = get_node_or_null("/root/GameManager")
	if gm and gm.has_method("set_active_checkpoint"):
		gm.set_active_checkpoint(checkpoint_id, global_position)

	# Efecto visual: explosión de partículas + twinkle
	_play_activation_effect()

func _update_visual() -> void:
	## Cambia color según estado
	if _activated:
		sprite.self_modulate = Color.GREEN
		sprite.scale = Vector2.ONE * 1.2
	else:
		sprite.self_modulate = Color.WHITE
		sprite.scale = Vector2.ONE

func _create_particles() -> void:
	## Crea sistema de partículas para animación
	_particles = GPUParticles2D.new()
	add_child(_particles)

	# Configuración básica (simplificada sin .tres)
	_particles.amount = 8
	_particles.lifetime = 0.5
	_particles.speed_scale = 1.0

func _play_activation_effect() -> void:
	## Efecto visual de activación
	var tween = create_tween()
	tween.set_parallel(true)
	tween.set_trans(Tween.TRANS_BOUNCE)
	tween.set_ease(Tween.EASE_OUT)

	# Bounce en escala
	tween.tween_property(sprite, "scale", Vector2.ONE * 1.3, 0.4)

	# Parpadeo
	var t2 = create_tween()
	for i in range(4):
		t2.tween_callback(func(): sprite.self_modulate = Color.YELLOW)
		t2.tween_callback(func(): sprite.self_modulate = Color.GREEN)

	# Sonido (si AudioManager existe)
	var am = get_node_or_null("/root/AudioManager")
	if am and am.has_method("play_sfx"):
		am.play_sfx("checkpoint")

func respawn_player(player: CharacterBody2D) -> void:
	## Coloca al jugador en la posición del checkpoint
	if not is_multiplayer_authority():
		return

	player.global_position = global_position + Vector2(0, -32)  # Offset para no superponerlo
	player.velocity = Vector2.ZERO

	# Notificar en el HUD
	var gm = get_node_or_null("/root/GameManager")
	if gm and gm.has_signal("player_respawned"):
		gm.player_respawned.emit(player.name)
