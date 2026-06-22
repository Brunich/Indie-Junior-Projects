extends Area2D

@export var speed: float = 700.0
var direction: Vector2 = Vector2.UP
var from_player: bool = true


func _ready() -> void:
	add_to_group("bullet")
	area_entered.connect(_on_area_entered)


func _process(delta: float) -> void:
	position += direction * speed * delta
	if global_position.y < -20.0 or global_position.y > 740.0:
		queue_free()


func _on_area_entered(area: Area2D) -> void:
	if from_player and area.is_in_group("enemy"):
		if area.has_method("take_hit"):
			area.take_hit()
		queue_free()
