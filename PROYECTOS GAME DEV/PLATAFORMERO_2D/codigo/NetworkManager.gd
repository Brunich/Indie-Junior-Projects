## ============================================================
## NetworkManager.gd — Autoload compartido para todos los proyectos
## Bruno Salas | UANL Monterrey | 2026
## ============================================================
##
## CÓMO REGISTRARLO EN GODOT 4:
##   Project > Project Settings > Autoload
##   Agrega este archivo con el nombre "NetworkManager"
##   Quedará disponible como /root/NetworkManager en toda la escena
##
## SOPORTA DOS MODOS:
##   - HOST: crea el servidor, espera jugadores
##   - CLIENT: se conecta al servidor del host
##   - LOCAL: sin red (modo offline, para desarrollo/testing)
##
## PARA JUEGO LOCAL (2 jugadores, mismo PC):
##   NetworkManager.start_local()
##
## PARA LAN / INTERNET:
##   Host:   NetworkManager.host_game(port)
##   Client: NetworkManager.join_game(ip, port)
## ============================================================

extends Node

# ---- CONSTANTES ----
const DEFAULT_PORT: int    = 7777
const MAX_PLAYERS: int     = 4
const SERVER_ID: int       = 1

# ---- SEÑALES ----
## Emitida cuando un jugador entra (incluye el servidor al hacer host)
signal player_connected(player_id: int, player_data: Dictionary)
## Emitida cuando un jugador se desconecta
signal player_disconnected(player_id: int)
## Emitida cuando la conexión al servidor falla (solo en clients)
signal connection_failed()
## Emitida cuando todos los jugadores están listos para empezar
signal all_players_ready()
## Emitida cuando el juego empieza oficialmente
signal game_started()

# ---- ESTADO DE LA SESIÓN ----
enum Mode { OFFLINE, HOST, CLIENT }
var mode: Mode = Mode.OFFLINE

## Diccionario de todos los jugadores conectados: { id: player_data }
var players: Dictionary = {}

## Datos del jugador local
var local_player_data: Dictionary = {
	"name":   "Player",
	"skin":   "default",   # nombre del skin seleccionado
	"color":  Color.BLUE,  # color del jugador (para UI)
	"ready":  false
}

var is_game_running: bool = false


# ==================================================================
# INICIALIZACIÓN
# ==================================================================
func _ready() -> void:
	# Conectar señales del sistema de red de Godot
	multiplayer.peer_connected.connect(_on_peer_connected)
	multiplayer.peer_disconnected.connect(_on_peer_disconnected)
	multiplayer.connected_to_server.connect(_on_connected_to_server)
	multiplayer.connection_failed.connect(_on_connection_failed)
	multiplayer.server_disconnected.connect(_on_server_disconnected)


# ==================================================================
# MODO OFFLINE (para desarrollo y testing sin red)
# Simula 2 jugadores locales usando el mismo teclado
# ==================================================================
func start_local(num_players: int = 2) -> void:
	mode = Mode.OFFLINE
	players.clear()

	for i in range(num_players):
		var pid = i + 1
		var data = local_player_data.duplicate()
		data["name"]  = "Jugador %d" % pid
		data["color"] = [Color.BLUE, Color.RED, Color.GREEN, Color.YELLOW][i]
		players[pid] = data
		emit_signal("player_connected", pid, data)

	print("[NetworkManager] Modo local — %d jugadores" % num_players)
	start_game()


# ==================================================================
# HOST — crear el servidor
# ==================================================================
func host_game(port: int = DEFAULT_PORT) -> Error:
	mode = Mode.HOST
	var peer = ENetMultiplayerPeer.new()
	var error = peer.create_server(port, MAX_PLAYERS)

	if error != OK:
		push_error("[NetworkManager] Error al crear servidor: %s" % error_string(error))
		return error

	multiplayer.multiplayer_peer = peer

	# El host se registra como jugador 1
	var my_data = local_player_data.duplicate()
	my_data["name"] = "Host"
	players[SERVER_ID] = my_data
	emit_signal("player_connected", SERVER_ID, my_data)

	print("[NetworkManager] Servidor iniciado en puerto %d" % port)
	return OK


# ==================================================================
# CLIENT — conectarse al host
# ==================================================================
func join_game(ip: String = "127.0.0.1", port: int = DEFAULT_PORT) -> Error:
	mode = Mode.CLIENT
	var peer = ENetMultiplayerPeer.new()
	var error = peer.create_client(ip, port)

	if error != OK:
		push_error("[NetworkManager] Error al conectar: %s" % error_string(error))
		return error

	multiplayer.multiplayer_peer = peer
	print("[NetworkManager] Conectando a %s:%d..." % [ip, port])
	return OK


# ==================================================================
# DESCONEXIÓN
# ==================================================================
func disconnect_from_game() -> void:
	if multiplayer.multiplayer_peer:
		multiplayer.multiplayer_peer.close()
		multiplayer.multiplayer_peer = null
	players.clear()
	is_game_running = false
	mode = Mode.OFFLINE
	print("[NetworkManager] Desconectado")


# ==================================================================
# SINCRONIZACIÓN DE DATOS DE JUGADOR
## Cuando un cliente se conecta, el host comparte los datos de todos
# ==================================================================
@rpc("authority", "call_local", "reliable")
func register_player(id: int, data: Dictionary) -> void:
	players[id] = data
	emit_signal("player_connected", id, data)
	print("[NetworkManager] Jugador registrado: %d — %s" % [id, data.get("name", "?")])


@rpc("any_peer", "call_local", "reliable")
func update_player_data(data: Dictionary) -> void:
	var sender_id = multiplayer.get_remote_sender_id()
	if sender_id == 0:
		sender_id = multiplayer.get_unique_id()
	players[sender_id] = data

	# Si todos están listos, avisar
	_check_all_ready()


func set_local_player_data(data: Dictionary) -> void:
	local_player_data.merge(data, true)
	# Sincronizar con el servidor si estamos conectados
	if multiplayer.multiplayer_peer:
		update_player_data.rpc(local_player_data)


# ==================================================================
# INICIO DEL JUEGO
# ==================================================================
func start_game() -> void:
	is_game_running = true
	emit_signal("game_started")
	print("[NetworkManager] ¡Juego iniciado!")


@rpc("authority", "call_local", "reliable")
func rpc_start_game() -> void:
	start_game()


func _check_all_ready() -> void:
	if players.is_empty():
		return
	for pid in players:
		if not players[pid].get("ready", false):
			return
	emit_signal("all_players_ready")
	# El servidor inicia el juego cuando todos están listos
	if multiplayer.is_server():
		rpc_start_game.rpc()


# ==================================================================
# UTILIDADES
# ==================================================================
func get_my_id() -> int:
	if mode == Mode.OFFLINE:
		return 1
	return multiplayer.get_unique_id()


func is_server() -> bool:
	if mode == Mode.OFFLINE or mode == Mode.HOST:
		return true
	return multiplayer.is_server()


func get_player_count() -> int:
	return players.size()


func get_player_data(player_id: int) -> Dictionary:
	return players.get(player_id, {})


## Devuelve el ID de autoridad para un nodo (el jugador que lo controla)
## Úsalo en CharacterBody2D: set_multiplayer_authority(NetworkManager.get_my_id())
func assign_authority_to_node(node: Node, player_id: int) -> void:
	node.set_multiplayer_authority(player_id)


# ==================================================================
# CALLBACKS DE LA RED
# ==================================================================
func _on_peer_connected(id: int) -> void:
	print("[NetworkManager] Peer conectado: %d" % id)

	# El servidor manda los datos de todos los jugadores actuales al nuevo
	if multiplayer.is_server():
		for existing_id in players:
			register_player.rpc_id(id, existing_id, players[existing_id])

		# Registrar al nuevo jugador con datos placeholder
		# (él actualizará sus datos con update_player_data)
		var new_data = { "name": "Jugador %d" % id, "skin": "default", "ready": false }
		players[id] = new_data
		register_player.rpc(id, new_data)


func _on_peer_disconnected(id: int) -> void:
	print("[NetworkManager] Peer desconectado: %d" % id)
	players.erase(id)
	emit_signal("player_disconnected", id)


func _on_connected_to_server() -> void:
	print("[NetworkManager] Conectado al servidor. Mi ID: %d" % multiplayer.get_unique_id())
	# Mandar mis datos al servidor
	update_player_data.rpc(local_player_data)


func _on_connection_failed() -> void:
	push_error("[NetworkManager] Falló la conexión al servidor")
	mode = Mode.OFFLINE
	emit_signal("connection_failed")


func _on_server_disconnected() -> void:
	print("[NetworkManager] El servidor se desconectó")
	disconnect_from_game()


# ==================================================================
# DEBUG — muestra estado de la red en consola
# ==================================================================
func print_status() -> void:
	print("=== NetworkManager Status ===")
	print("Modo: %s" % Mode.keys()[mode])
	print("Mi ID: %d" % get_my_id())
	print("Jugadores: %d" % players.size())
	for pid in players:
		print("  [%d] %s — skin: %s — ready: %s" % [
			pid,
			players[pid].get("name", "?"),
			players[pid].get("skin", "?"),
			players[pid].get("ready", false)
		])
	print("=============================")
