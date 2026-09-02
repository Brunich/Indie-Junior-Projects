## ============================================================
## MusicLayers.gd — Sistema de Stems Adaptativos
## Bruno Salas | UANL Monterrey | 2026
## ============================================================
## Autoload: añadir como MusicLayers en project.godot
##
## Inspiración: Hi-Fi Rush, Celeste, Hades — la música sube de
## intensidad según el estado del juego activando/desactivando
## capas (stems) de forma sincronizada con el BPM.
##
## Estructura de carpetas esperada:
##   res://audio/music/stems/explore/   — stem_bass.ogg, stem_melody.ogg, etc.
##   res://audio/music/stems/combat/
##   res://audio/music/stems/boss/
##   res://audio/music/stems/tense/
##
## Uso básico:
##   MusicLayers.set_state(MusicLayers.STATE_COMBAT)
##   MusicLayers.set_state(MusicLayers.STATE_EXPLORE)

extends Node

# ---------------------------------------------------------------------------
# ESTADOS DEL JUEGO
# ---------------------------------------------------------------------------
const STATE_MENU    := "menu"
const STATE_EXPLORE := "explore"   ## Exploración tranquila — solo bass + ambient
const STATE_TENSE   := "tense"     ## Enemigo cerca — agrega percusión suave
const STATE_COMBAT  := "combat"    ## Combate activo — capas completas
const STATE_BOSS    := "boss"      ## Jefe — máxima intensidad
const STATE_VICTORY := "victory"   ## Victoria / checkpoint
const STATE_SILENT  := "silent"    ## Sin música (cinemáticas, etc.)

# Orden de intensidad (útil para transiciones graduales)
const _STATE_INTENSITY: Dictionary = {
	STATE_MENU:    0,
	STATE_SILENT:  0,
	STATE_EXPLORE: 1,
	STATE_TENSE:   2,
	STATE_COMBAT:  3,
	STATE_BOSS:    4,
	STATE_VICTORY: 3,
}

# ---------------------------------------------------------------------------
# DEFINICIÓN DE CAPAS POR ESTADO
# Cada estado tiene un Array de diccionarios con:
#   path  → ruta al archivo .ogg
#   vol   → volumen objetivo en dB (0 = pleno, -80 = silencio)
#   bus   → bus de audio (por defecto "Music")
# ---------------------------------------------------------------------------
var _layer_definitions: Dictionary = {
	STATE_EXPLORE: [
		{ "id": "bass",    "path": "res://audio/music/stems/explore/stem_bass.ogg",    "vol": -3.0,  "bus": "Music" },
		{ "id": "ambient", "path": "res://audio/music/stems/explore/stem_ambient.ogg", "vol": -6.0,  "bus": "Music" },
	],
	STATE_TENSE: [
		{ "id": "bass",    "path": "res://audio/music/stems/explore/stem_bass.ogg",    "vol": -3.0,  "bus": "Music" },
		{ "id": "ambient", "path": "res://audio/music/stems/explore/stem_ambient.ogg", "vol": -12.0, "bus": "Music" },
		{ "id": "perc",    "path": "res://audio/music/stems/tense/stem_perc.ogg",      "vol": -6.0,  "bus": "Music" },
		{ "id": "strings", "path": "res://audio/music/stems/tense/stem_strings.ogg",   "vol": -9.0,  "bus": "Music" },
	],
	STATE_COMBAT: [
		{ "id": "bass",    "path": "res://audio/music/stems/combat/stem_bass.ogg",     "vol": -3.0,  "bus": "Music" },
		{ "id": "drums",   "path": "res://audio/music/stems/combat/stem_drums.ogg",    "vol":  0.0,  "bus": "Music" },
		{ "id": "lead",    "path": "res://audio/music/stems/combat/stem_lead.ogg",     "vol": -3.0,  "bus": "Music" },
		{ "id": "synth",   "path": "res://audio/music/stems/combat/stem_synth.ogg",    "vol": -6.0,  "bus": "Music" },
	],
	STATE_BOSS: [
		{ "id": "bass",    "path": "res://audio/music/stems/boss/stem_bass.ogg",       "vol": -2.0,  "bus": "Music" },
		{ "id": "drums",   "path": "res://audio/music/stems/boss/stem_drums.ogg",      "vol":  0.0,  "bus": "Music" },
		{ "id": "lead",    "path": "res://audio/music/stems/boss/stem_lead.ogg",       "vol": -2.0,  "bus": "Music" },
		{ "id": "brass",   "path": "res://audio/music/stems/boss/stem_brass.ogg",      "vol": -4.0,  "bus": "Music" },
		{ "id": "choir",   "path": "res://audio/music/stems/boss/stem_choir.ogg",      "vol": -6.0,  "bus": "Music" },
	],
	STATE_VICTORY: [
		{ "id": "fanfare", "path": "res://audio/music/stems/victory/stem_fanfare.ogg", "vol":  0.0,  "bus": "Music" },
	],
	STATE_MENU: [
		{ "id": "menu",    "path": "res://audio/music/stems/menu/stem_main.ogg",       "vol":  0.0,  "bus": "Music" },
	],
	STATE_SILENT: [],
}

# ---------------------------------------------------------------------------
# SEÑALES
# ---------------------------------------------------------------------------
signal state_changed(from_state: String, to_state: String)
signal layer_faded_in(layer_id: String)
signal layer_faded_out(layer_id: String)

# ---------------------------------------------------------------------------
# VARIABLES INTERNAS
# ---------------------------------------------------------------------------
## Tiempo de crossfade por defecto (segundos)
@export var fade_duration: float = 1.2
## Si es true, espera al siguiente beat para iniciar la transición
@export var sync_to_beat: bool = true
## BPM de referencia — se sincroniza con BeatSync si está disponible
@export var bpm: float = 120.0

var _current_state: String = STATE_SILENT
var _pending_state: String = ""

## Reproductores activos: { "layer_id" → AudioStreamPlayer }
var _active_players: Dictionary = {}
## Pool de reproductores reutilizables
var _player_pool: Array[AudioStreamPlayer] = []
const _POOL_SIZE := 10

var _beat_transition_queued: bool = false

# ---------------------------------------------------------------------------
# CICLO DE VIDA
# ---------------------------------------------------------------------------
func _ready() -> void:
	_init_pool()
	# Conectar con BeatSync si existe
	if has_node("/root/BeatSync"):
		BeatSync.on_beat.connect(_on_beat)

func _init_pool() -> void:
	for i in _POOL_SIZE:
		var p := AudioStreamPlayer.new()
		p.name = "StemPlayer_%d" % i
		p.bus = "Music"
		add_child(p)
		_player_pool.append(p)

# ---------------------------------------------------------------------------
# API PÚBLICA
# ---------------------------------------------------------------------------

## Cambia el estado musical del juego.
## Si sync_to_beat=true, la transición ocurrirá en el próximo beat.
## Ejemplo: MusicLayers.set_state(MusicLayers.STATE_COMBAT)
func set_state(new_state: String, force_immediate: bool = false) -> void:
	if new_state == _current_state:
		return
	if not _layer_definitions.has(new_state):
		push_warning("MusicLayers: estado '%s' no reconocido" % new_state)
		return

	if sync_to_beat and not force_immediate and has_node("/root/BeatSync"):
		_pending_state = new_state
		_beat_transition_queued = true
	else:
		_transition_to(new_state)

## Devuelve el estado actual
func get_state() -> String:
	return _current_state

## Cambia el volumen de una capa específica (para dinámicas en tiempo real).
## Ejemplo: MusicLayers.set_layer_volume("drums", -12.0, 0.3)
func set_layer_volume(layer_id: String, target_db: float, duration: float = 0.3) -> void:
	if not _active_players.has(layer_id):
		return
	var player: AudioStreamPlayer = _active_players[layer_id]
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(player, "volume_db", target_db, duration)

## Activa o desactiva una sola capa sin cambiar el estado global.
## Útil para reaccionar a hits on-beat (Hi-Fi Rush style).
func set_layer_active(layer_id: String, active: bool, duration: float = 0.2) -> void:
	if not _active_players.has(layer_id):
		return
	var player: AudioStreamPlayer = _active_players[layer_id]
	var target_db := _get_layer_target_db(layer_id) if active else -80.0
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tween.tween_property(player, "volume_db", target_db, duration)

## Silencia todo con fade
func silence(duration: float = 1.0) -> void:
	set_state(STATE_SILENT, true)

## Pausa / reanuda todos los stems (para pause menu)
func set_paused(paused: bool) -> void:
	for player in _active_players.values():
		(player as AudioStreamPlayer).stream_paused = paused

# ---------------------------------------------------------------------------
# TRANSICIÓN INTERNA
# ---------------------------------------------------------------------------
func _transition_to(new_state: String) -> void:
	var from_state := _current_state
	_current_state = new_state

	var new_defs: Array = _layer_definitions.get(new_state, [])
	var new_ids: Array[String] = []
	for def in new_defs:
		new_ids.append(def["id"])

	# 1. Fade out de capas que ya no pertenecen al nuevo estado
	var to_remove: Array[String] = []
	for layer_id in _active_players.keys():
		if layer_id not in new_ids:
			to_remove.append(layer_id)
	for layer_id in to_remove:
		_fade_out_layer(layer_id)

	# 2. Fade in de capas nuevas (o ajuste de volumen si ya estaban)
	for def in new_defs:
		var lid: String = def["id"]
		if _active_players.has(lid):
			# Ya existe: solo ajustar volumen objetivo
			_fade_layer_to(lid, def["vol"])
		else:
			# Nueva capa: iniciar desde silencio y fade in
			_fade_in_layer(def)

	state_changed.emit(from_state, new_state)

func _fade_in_layer(def: Dictionary) -> void:
	var path: String = def["path"]
	var stream := _load_safe(path)
	if stream == null:
		push_warning("MusicLayers: archivo no encontrado: %s" % path)
		return

	var player := _get_free_player()
	if player == null:
		push_warning("MusicLayers: pool agotado, no se pudo reproducir '%s'" % def["id"])
		return

	player.stream = stream
	player.bus = def.get("bus", "Music")
	player.volume_db = -80.0
	player.play()

	_active_players[def["id"]] = player

	var tween := create_tween()
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tween.tween_property(player, "volume_db", def["vol"], fade_duration)
	tween.finished.connect(func(): layer_faded_in.emit(def["id"]))

func _fade_out_layer(layer_id: String) -> void:
	var player: AudioStreamPlayer = _active_players[layer_id]
	_active_players.erase(layer_id)

	var tween := create_tween()
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	tween.tween_property(player, "volume_db", -80.0, fade_duration)
	tween.finished.connect(func():
		player.stop()
		_player_pool.append(player)
		layer_faded_out.emit(layer_id)
	)

func _fade_layer_to(layer_id: String, target_db: float) -> void:
	var player: AudioStreamPlayer = _active_players[layer_id]
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(player, "volume_db", target_db, fade_duration)

# ---------------------------------------------------------------------------
# BEAT SYNC — esperar al siguiente beat para transicionar
# ---------------------------------------------------------------------------
func _on_beat(_beat_number: int) -> void:
	if _beat_transition_queued and _pending_state != "":
		_beat_transition_queued = false
		var state := _pending_state
		_pending_state = ""
		_transition_to(state)

# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------
func _get_free_player() -> AudioStreamPlayer:
	if _player_pool.is_empty():
		# Crear uno extra si el pool se agotó
		push_warning("MusicLayers: pool agotado, creando reproductor adicional")
		var extra := AudioStreamPlayer.new()
		extra.bus = "Music"
		add_child(extra)
		return extra
	return _player_pool.pop_back()

func _get_layer_target_db(layer_id: String) -> float:
	## Devuelve el dB objetivo definido para la capa en el estado actual
	var defs: Array = _layer_definitions.get(_current_state, [])
	for def in defs:
		if def["id"] == layer_id:
			return def["vol"]
	return 0.0

func _load_safe(path: String) -> AudioStream:
	if ResourceLoader.exists(path):
		return load(path) as AudioStream
	return null

# ---------------------------------------------------------------------------
# DEBUG
# ---------------------------------------------------------------------------

## Imprime el estado actual y las capas activas (útil en desarrollo)
func debug_print() -> void:
	print("=== MusicLayers DEBUG ===")
	print("Estado: %s" % _current_state)
	if _active_players.is_empty():
		print("  (sin capas activas)")
	for lid in _active_players.keys():
		var p: AudioStreamPlayer = _active_players[lid]
		print("  [%s] vol=%.1f dB | playing=%s" % [lid, p.volume_db, p.playing])
	print("=========================")
