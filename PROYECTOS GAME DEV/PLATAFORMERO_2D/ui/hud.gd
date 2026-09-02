## hud.gd — HUD del plataformero 2D
## Muestra score, vidas y ronda en pantalla durante el juego.
## Se conecta a GameManager mediante señales (nunca polling en _process).
extends CanvasLayer

# ── Referencias a nodos ──────────────────────────────────────────────────────
@onready var label_score: Label  = $TopHBox/LabelScore
@onready var label_lives: Label  = $TopHBox/LabelLives
@onready var label_round: Label  = $TopHBox/LabelRound

# ── Ciclo de vida ─────────────────────────────────────────────────────────────
func _ready() -> void:
	# Usamos get_node_or_null para que el HUD no crashee si GameManager no existe
	var gm := get_node_or_null("/root/GameManager")
	if gm:
		if gm.has_signal("score_changed"):
			gm.score_changed.connect(_on_score_changed)
		if gm.has_signal("lives_changed"):
			gm.lives_changed.connect(_on_lives_changed)
		if gm.has_signal("round_changed"):
			gm.round_changed.connect(_on_round_changed)
		# Valores iniciales para no mostrar ceros al comenzar
		_refresh_all(gm)
	else:
		push_warning("HUD: GameManager no encontrado en /root/GameManager")

# ── Helpers ───────────────────────────────────────────────────────────────────

## Actualiza todos los labels de una vez con el estado actual del GameManager.
func _refresh_all(gm: Node) -> void:
	var my_id := _get_my_id()
	if gm.has_method("get_score"):
		label_score.text = "Score: %d" % gm.get_score(my_id)
	if gm.has_method("get_lives"):
		label_lives.text = "❤️ x%d" % gm.get_lives(my_id)
	if gm.has_method("get_round"):
		label_round.text = "Ronda: %d" % gm.get_round()

## Devuelve el ID del jugador local.
## En modo offline retorna 1; en red usa NetworkManager si está disponible.
func _get_my_id() -> int:
	var nm := get_node_or_null("/root/NetworkManager")
	if nm and nm.has_method("get_my_id"):
		return nm.get_my_id()
	return 1

# ── Callbacks de señales ──────────────────────────────────────────────────────

## Actualiza el score solo si el evento es del jugador local.
func _on_score_changed(player_id: int, score: int) -> void:
	if player_id == _get_my_id():
		label_score.text = "Score: %d" % score

## Actualiza las vidas solo si el evento es del jugador local.
func _on_lives_changed(player_id: int, lives: int) -> void:
	if player_id == _get_my_id():
		label_lives.text = "❤️ x%d" % lives

## Actualiza el número de ronda (global, no por jugador).
func _on_round_changed(round_number: int) -> void:
	label_round.text = "Ronda: %d" % round_number
