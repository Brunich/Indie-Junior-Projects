extends Area2D

@export var speed: float = 180.0
@export var hp: int = 2

var _dir := Vector2.DOWN


func _ready() -> void:
	add_to_group("enemy")
	_dir = Vector2.DOWN.rotated(randf_range(-0.35, 0.35))
	area_entered.connect(_on_area_entered)
	body_entered.connect(_on_body_entered)


func _process(delta: float) -> void:
	position += _dir * speed * delta
	if global_position.y > 760.0:
		queue_free()


func _on_area_entered(area: Area2D) -> void:
	if area.is_in_group("bullet") and area.get("from_player") == true:
		take_hit()
		area.queue_free()


func take_hit() -> void:
	hp -= 1
	if hp <= 0:
		var root := get_tree().current_scene
		if root.has_method("add_score"):
			root.add_score(100)
		queue_free()


func _on_body_entered(body: Node) -> void:
	if body.is_in_group("player"):
		if body.has_method("take_hit"):
			body.take_hit()
		queue_free()
