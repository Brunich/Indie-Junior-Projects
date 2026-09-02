extends Node2D

@onready var hud: Label = $UI/HUD
@onready var player: CharacterBody2D = $Player

var score := 0
var spawn_timer := 0.0
@export var spawn_interval: float = 1.1

const ENEMY_SCENE := preload("res://scenes/enemy.tscn")


func _process(delta: float) -> void:
	if not player:
		return
	spawn_timer -= delta
	if spawn_timer <= 0.0:
		spawn_timer = spawn_interval
		var enemy := ENEMY_SCENE.instantiate() as Node2D
		enemy.global_position = Vector2(randf_range(80.0, 1200.0), -30.0)
		add_child(enemy)


func add_score(points: int) -> void:
	score += points
	hud.text = "Score: %d  |  WASD mover · Espacio disparar · R reiniciar" % score


func game_over() -> void:
	hud.text = "Game Over — Score: %d — R reiniciar" % score
	set_process(false)
	player.set_process(false)
	player.set_physics_process(false)


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_R:
		get_tree().reload_current_scene()
