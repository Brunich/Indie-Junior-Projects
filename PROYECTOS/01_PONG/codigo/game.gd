extends Node2D

@onready var score_label: Label = $UI/ScoreLabel
@onready var ball: CharacterBody2D = $Ball

var score_p1 := 0
var score_p2 := 0


func _ready() -> void:
	ball.scored.connect(_on_scored)
	_update_score()


func _on_scored(side: String) -> void:
	if side == "GoalLeft":
		score_p2 += 1
	else:
		score_p1 += 1
	_update_score()
	if score_p1 >= 7 or score_p2 >= 7:
		score_label.text = "Gana %s — R reiniciar" % ("J1" if score_p1 >= 7 else "J2 / CPU")
		set_process_input(true)


func _update_score() -> void:
	score_label.text = "%d  —  PONG  —  %d\nW/S vs Flechas · R reiniciar" % [score_p1, score_p2]


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept") or (event is InputEventKey and event.pressed and event.keycode == KEY_R):
		get_tree().reload_current_scene()
