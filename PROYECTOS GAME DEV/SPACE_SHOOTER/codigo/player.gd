extends CharacterBody2D

@export var speed: float = 420.0
@export var fire_cooldown: float = 0.18

var _cooldown := 0.0
@onready var bullet_scene: PackedScene = preload("res://scenes/bullet.tscn")


func _ready() -> void:
	add_to_group("player")


func _physics_process(delta: float) -> void:
	_cooldown = maxf(_cooldown - delta, 0.0)
	var dir := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	velocity = dir * speed
	move_and_slide()
	position.x = clampf(position.x, 40.0, 1240.0)
	position.y = clampf(position.y, 40.0, 680.0)

	if Input.is_action_pressed("shoot") and _cooldown <= 0.0:
		_shoot()
		_cooldown = fire_cooldown


func _shoot() -> void:
	var bullet := bullet_scene.instantiate() as Area2D
	bullet.global_position = global_position + Vector2(0, -28)
	bullet.direction = Vector2.UP
	bullet.from_player = true
	get_tree().current_scene.add_child(bullet)


func take_hit() -> void:
	if get_tree().current_scene.has_method("game_over"):
		get_tree().current_scene.game_over()
