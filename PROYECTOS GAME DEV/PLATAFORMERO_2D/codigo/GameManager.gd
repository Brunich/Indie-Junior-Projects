## ============================================================
## GameManager.gd — Autoload: estado global del juego
## Bruno Salas | UANL Monterrey | 2026
## ============================================================
## Maneja: score, vidas, ronda, pausa, transición de escenas
## Funciona tanto offline como con red (consulta NetworkManager)
## ============================================================

extends Node

# ---- SEÑALES ----
signal score_changed(player_id: int, new_score: int)
signal lives_changed(player_id: int, lives_remaining: int)
signal round_changed(new_round: int)
signal game_paused(is_paused: bool)
signal game_over(winner_id: int)

# ---- CONFIGURACIÓN ----
@export var starting_lives: int   = 3
@export var max_rounds: int       = 3

# ---- ESTADO ----
var scores: Dictionary   = {}  # { player_id: score }
var lives: Dictionary    = {}  # { player_id: lives }
var current_round: int   = 1
var is_paused: bool      = false


func _ready() -> void:
	var net = get_node_or_null("/root/NetworkManager")
	if net:
		net.game_started.connect(_on_game_started)
		net.player_disconnected.connect(_on_player_disconnected)


func _on_game_started() -> void:
	var net = get_node_or_null("/root/NetworkManager")
	if not net:
		_init_player(1)
		return
	for pid in net.players:
		_init_player(pid)


func _init_player(player_id: int) -> void:
	scores[player_id] = 0
	lives[player_id] = starting_lives


# ---- SCORE ----
@rpc("any_peer", "call_local", "reliable")
func add_score(player_id: int, points: int) -> void:
	if not scores.has(player_id):
		scores[player_id] = 0
	scores[player_id] += points
	emit_signal("score_changed", player_id, scores[player_id])


func get_score(player_id: int) -> int:
	return scores.get(player_id, 0)


func get_leading_player() -> int:
	var best_id = -1
	var best_score = -1
	for pid in scores:
		if scores[pid] > best_score:
			best_score = scores[pid]
			best_id = pid
	return best_id


# ---- VIDAS ----
@rpc("authority", "call_local", "reliable")
func remove_life(player_id: int) -> void:
	if not lives.has(player_id):
		return
	lives[player_id] = max(0, lives[player_id] - 1)
	emit_signal("lives_changed", player_id, lives[player_id])

	if lives[player_id] <= 0:
		_check_game_over()


func _check_game_over() -> void:
	var alive_players = []
	for pid in lives:
		if lives[pid] > 0:
			alive_players.append(pid)

	if alive_players.size() == 1:
		emit_signal("game_over", alive_players[0])
	elif alive_players.is_empty():
		emit_signal("game_over", -1)  # empate


# ---- PAUSA ----
func toggle_pause() -> void:
	is_paused = not is_paused
	get_tree().paused = is_paused
	emit_signal("game_paused", is_paused)


# ---- TRANSICIONES DE ESCENA ----
func load_scene(path: String) -> void:
	get_tree().change_scene_to_file(path)


func _on_player_disconnected(player_id: int) -> void:
	scores.erase(player_id)
	lives.erase(player_id)
