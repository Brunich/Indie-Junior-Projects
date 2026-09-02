## ============================================================
## powerup.gd — Sistema de Power-ups del Plataformero
## Bruno Salas | UANL Monterrey | 2026
## ============================================================
## Tres tipos de power-ups con efectos dinámicos
## - SPEED_BOOST: +50% velocidad por 8 segundos
## - SHIELD: 1 hit de protección
## - DOUBLE_JUMP: +1 salto aire por 10 segundos

extends Area2D
class_name PowerUp

# ---- TIPOS DE POWER-UPS ----
enum PowerUpType { SPEED_BOOST, SHIELD, DOUBLE_JUMP }

@export var power_up_type: PowerUpType = PowerUpType.SPEED_BOOST
@export var effect_duration: float = 8.0
@export var spin_speed: float = 2.0

# ---- SEÑALES ----
signal collected(player: Node2D, power_type: PowerUpType)

@onready var sprite = $Sprite2D
@onready var collision = $CollisionShape2D

var _rotation_angle: float = 0.0
var _collected: bool = false

func _ready() -> void:
	area_entered.connect(_on_area_entered)
	_set_visual_by_type()

func _process(delta: float) -> void:
	if not _collected:
		_rotation_angle += spin_speed * delta
		rotation = _rotation_angle

func _on_area_entered(area: Area2D) -> void:
	if _collected:
		return

	# Verificar que sea el player (en multiplayer solo el authority puede recoger)
	if not is_multiplayer_authority():
		return

	var player = area.get_parent() if area.is_in_group("player_hitbox") else null
	if not player:
		return

	_collected = true
	_apply_effect_to_player(player)
	collected.emit(player, power_up_type)
	_disappear()

func _set_visual_by_type() -> void:
	## Ajusta el color del sprite según el tipo
	match power_up_type:
		PowerUpType.SPEED_BOOST:
			sprite.modulate = Color.YELLOW
			name = "PowerUp_SpeedBoost"
		PowerUpType.SHIELD:
			sprite.modulate = Color.BLUE
			name = "PowerUp_Shield"
		PowerUpType.DOUBLE_JUMP:
			sprite.modulate = Color.MAGENTA
			name = "PowerUp_DoubleJump"

func _apply_effect_to_player(player: Node) -> void:
	## Aplica el efecto del power-up al jugador
	match power_up_type:
		PowerUpType.SPEED_BOOST:
			_apply_speed_boost(player)
		PowerUpType.SHIELD:
			_apply_shield(player)
		PowerUpType.DOUBLE_JUMP:
			_apply_double_jump(player)

func _apply_speed_boost(player: Node) -> void:
	## +50% velocidad durante effect_duration
	if not player.has_method("add_speed_boost"):
		return

	var original_speed = player.run_speed
	player.run_speed *= 1.5

	# Efecto visual: parpadeo
	var tween = create_tween()
	tween.set_parallel(true)
	tween.set_trans(Tween.TRANS_SINE)

	await tween.tween_callback(func(): player.modulate = Color.YELLOW).finished
	tween.tween_callback(func(): player.modulate = Color.WHITE)

	await get_tree().create_timer(effect_duration).timeout
	player.run_speed = original_speed

func _apply_shield(player: Node) -> void:
	## Otorga 1 escudo de protección
	if not player.has_method("add_shield"):
		return

	player.add_shield()

	# Efecto visual: aura azul
	var shield_visual = CanvasItem.new()
	add_child(shield_visual)
	shield_visual.modulate = Color.BLUE
	shield_visual.self_modulate.a = 0.3

func _apply_double_jump(player: Node) -> void:
	## +1 salto en el aire
	if not player.has_method("add_air_jump"):
		return

	player.add_air_jump()

	# Efecto visual: brillo magenta
	var tween = create_tween()
	tween.tween_property(player, "self_modulate", Color.MAGENTA, 0.2)
	tween.tween_property(player, "self_modulate", Color.WHITE, 0.2)

func _disappear() -> void:
	## Anima la desaparición del power-up
	var tween = create_tween()
	tween.set_trans(Tween.TRANS_BACK)
	tween.set_ease(Tween.EASE_IN)

	tween.tween_property(self, "scale", Vector2.ZERO, 0.3)
	tween.tween_property(self, "modulate:a", 0.0, 0.2)

	await tween.finished
	queue_free()
