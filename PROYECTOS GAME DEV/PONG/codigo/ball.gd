extends CharacterBody2D

signal scored(side: String)

@export var speed: float = 460.0
var velocity_vec: Vector2 = Vector2.ZERO


func _ready() -> void:
	add_to_group("ball")
	reset_ball(Vector2.RIGHT if randf() > 0.5 else Vector2.LEFT)


func reset_ball(direction: Vector2) -> void:
	var angle := randf_range(-0.35, 0.35)
	velocity_vec = direction.normalized().rotated(angle) * speed


func _physics_process(delta: float) -> void:
	var collision := move_and_collide(velocity_vec * delta)
	if not collision:
		return

	var normal := collision.get_normal()
	var collider := collision.get_collider()

	if collider.is_in_group("paddle"):
		velocity_vec = velocity_vec.bounce(normal)
		var paddle := collider as Node2D
		var offset := (global_position.y - paddle.global_position.y) / 70.0
		velocity_vec.y += offset * 140.0
		velocity_vec = velocity_vec.normalized() * speed
	elif collider.is_in_group("wall"):
		velocity_vec = velocity_vec.bounce(normal)
	elif collider.is_in_group("goal"):
		scored.emit(collider.name)
		global_position = Vector2(640, 360)
		await get_tree().create_timer(0.5).timeout
		reset_ball(Vector2.RIGHT if collider.name == "GoalLeft" else Vector2.LEFT)
