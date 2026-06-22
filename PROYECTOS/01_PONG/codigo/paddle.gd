extends CharacterBody2D

@export var speed: float = 420.0
@export_enum("p1", "p2", "cpu") var control_scheme: String = "p1"
@export var clamp_min_y: float = 40.0
@export var clamp_max_y: float = 680.0

var _cpu_target_y: float = 360.0


func _physics_process(delta: float) -> void:
	var axis := _read_axis(delta)
	velocity = Vector2(0.0, axis * speed)
	move_and_slide()
	position.y = clampf(position.y, clamp_min_y, clamp_max_y)


func _read_axis(delta: float) -> float:
	match control_scheme:
		"p1":
			return Input.get_axis("p1_down", "p1_up")
		"p2":
			return Input.get_axis("p2_down", "p2_up")
		"cpu":
			var ball := get_tree().get_first_node_in_group("ball") as Node2D
			if ball:
				_cpu_target_y = ball.global_position.y
			return signf(_cpu_target_y - global_position.y)
	return 0.0
