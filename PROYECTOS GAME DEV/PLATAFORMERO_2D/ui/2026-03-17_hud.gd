## ============================================================
## hud.gd — Heads Up Display del Plataformero
## Bruno Salas | UANL Monterrey | 2026
## ============================================================
## Nodo: CanvasLayer con hijos Label para score, vidas, round
## Conexión con GameManager para actualizaciones en tiempo real

extends CanvasLayer
class_name HUD

# ---- REFERENCIAS ----
@onready var label_score: Label = $MarginContainer/HBox/LabelScore
@onready var label_lives: Label = $MarginContainer/HBox/LabelLives
@onready var label_round: Label = $MarginContainer/HBox/LabelRound
@onready var label_dialogue: Label = $DialoguePanel/DialogueLabel
@onready var dialogue_panel: Panel = $DialoguePanel

# ---- PROPIEDADES ----
var _local_player_id: int = 1

func _ready() -> void:
	# Obtener ID del jugador local
	var nm = get_node_or_null("/root/NetworkManager")
	if nm:
		_local_player_id = nm.get_unique_id()

	# Conectar señales del GameManager
	var gm = get_node_or_null("/root/GameManager")
	if gm:
		if gm.has_signal("score_changed"):
			gm.score_changed.connect(_on_score_changed)
		if gm.has_signal("lives_changed"):
			gm.lives_changed.connect(_on_lives_changed)
		if gm.has_signal("round_changed"):
			gm.round_changed.connect(_on_round_changed)

	# Conectar señales del DialogueManager
	var dm = get_node_or_null("/root/DialogueManager")
	if dm:
		if dm.has_signal("dialogue_started"):
			dm.dialogue_started.connect(_on_dialogue_started)
		if dm.has_signal("dialogue_ended"):
			dm.dialogue_ended.connect(_on_dialogue_ended)

	# Ocultar panel de diálogo al inicio
	dialogue_panel.modulate.a = 0.0

	# Inicializar valores
	_update_score(0)
	_update_lives(3)
	_update_round(1)

func _on_score_changed(player_id: int, score: int) -> void:
	## Solo actualiza el HUD si es el jugador local
	if player_id == _local_player_id or player_id == 1:
		_update_score(score)

func _on_lives_changed(player_id: int, lives: int) -> void:
	if player_id == _local_player_id or player_id == 1:
		_update_lives(lives)

func _on_round_changed(round_num: int) -> void:
	_update_round(round_num)

func _on_dialogue_started(character: String, text: String) -> void:
	## Muestra un diálogo en el panel
	if label_dialogue:
		var speaker_name = character.to_upper()
		label_dialogue.text = "[%s]\n%s" % [speaker_name, text]

	# Fade in del panel
	var tween = create_tween()
	tween.set_trans(Tween.TRANS_SINE)
	tween.tween_property(dialogue_panel, "modulate:a", 1.0, 0.3)

func _on_dialogue_ended() -> void:
	## Oculta el panel de diálogo
	var tween = create_tween()
	tween.set_trans(Tween.TRANS_SINE)
	tween.tween_property(dialogue_panel, "modulate:a", 0.0, 0.5)

func _update_score(score: int) -> void:
	if label_score:
		label_score.text = "Score: %d" % score

func _update_lives(lives: int) -> void:
	if label_lives:
		label_lives.text = "❤️ x%d" % lives

func _update_round(round_num: int) -> void:
	if label_round:
		label_round.text = "Round: %d" % round_num

func show_message(text: String, duration: float = 2.0, color: Color = Color.WHITE) -> void:
	## Muestra un mensaje temporal en el HUD
	var msg_label = Label.new()
	msg_label.text = text
	msg_label.add_theme_font_size_override("font_size", 24)
	msg_label.add_theme_color_override("font_color", color)
	msg_label.anchor_left = 0.5
	msg_label.anchor_top = 0.5
	msg_label.offset_left = -100
	msg_label.offset_top = -50

	add_child(msg_label)

	var tween = create_tween()
	tween.set_parallel(true)
	tween.tween_property(msg_label, "modulate:a", 0.0, duration)
	tween.tween_property(msg_label, "position:y", msg_label.position.y - 50, duration)

	await tween.finished
	msg_label.queue_free()

func pulse_score() -> void:
	## Efecto visual cuando se suma puntos
	if label_score:
		var original_scale = label_score.scale
		var tween = create_tween()
		tween.set_trans(Tween.TRANS_BACK)
		tween.tween_property(label_score, "scale", original_scale * 1.2, 0.1)
		tween.tween_property(label_score, "scale", original_scale, 0.1)
