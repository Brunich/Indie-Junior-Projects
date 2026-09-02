## ============================================================
## AudioManager.gd — Gestor Central de Audio
## Bruno Salas | UANL Monterrey | 2026
## ============================================================
## Autoload: añadir como AudioManager en project.godot
## Maneja música, SFX con sistema de buses y pool de reproducción

extends Node

# ---- BUSES DE AUDIO ----
const BUS_MUSIC := "Music"
const BUS_SFX := "SFX"
const BUS_MASTER := "Master"

# ---- POOL DE SFX SIMULTÁNEOS ----
const SFX_POOL_SIZE := 8
var _sfx_pool: Array[AudioStreamPlayer] = []
var _sfx_index: int = 0

# ---- REPRODUCTOR DE MÚSICA ----
var _music_player: AudioStreamPlayer
var _current_music_stream: AudioStream = null

# ---- BIBLIOTECA DE SFX ----
var SFX_LIBRARY: Dictionary = {
	"jump": null,
	"land": null,
	"hurt": null,
	"death": null,
	"shoot": null,
	"coin": null,
	"checkpoint": null,
	"level_complete": null,
	"enemy_death": null,
	"power_up": null,
	"dash": null,
	"wall_slide": null,
}

var MUSIC_LIBRARY: Dictionary = {
	"menu": null,
	"level_01": null,
	"level_02": null,
	"boss_battle": null,
	"victory": null,
	"game_over": null,
}

func _ready() -> void:
	_setup_audio_buses()
	_setup_sfx_pool()
	_setup_music_player()

func _setup_audio_buses() -> void:
	## Asegura que los buses existan en AudioServer
	# En un proyecto real, estos se configurarían en audio_bus_layout.tres
	# Aquí solo verificamos que existan

	# Crear buses si no existen
	var bus_layout = AudioServer.get_bus_count()
	if not AudioServer.get_bus_index("Master") >= 0:
		AudioServer.add_bus(-1)
		AudioServer.set_bus_name(bus_layout, "Master")

	# Intenta obtener los índices; si no existen, usa el master por defecto
	if AudioServer.get_bus_index(BUS_MUSIC) < 0:
		push_warning("AudioManager: bus '%s' no configurado, usando Master" % BUS_MUSIC)

	if AudioServer.get_bus_index(BUS_SFX) < 0:
		push_warning("AudioManager: bus '%s' no configurado, usando Master" % BUS_SFX)

func _setup_sfx_pool() -> void:
	## Crea el pool de reproductores para SFX simultáneos
	for i in SFX_POOL_SIZE:
		var player := AudioStreamPlayer.new()
		player.name = "SFXPlayer_%d" % i

		# Asignar a bus SFX si existe
		if AudioServer.get_bus_index(BUS_SFX) >= 0:
			player.bus = BUS_SFX
		else:
			player.bus = "Master"

		add_child(player)
		_sfx_pool.append(player)

func _setup_music_player() -> void:
	## Configura el reproductor de música central
	_music_player = AudioStreamPlayer.new()
	_music_player.name = "MusicPlayer"

	if AudioServer.get_bus_index(BUS_MUSIC) >= 0:
		_music_player.bus = BUS_MUSIC
	else:
		_music_player.bus = "Master"

	add_child(_music_player)

## ==================== MÉTODOS PÚBLICOS ====================

func play_sfx(event: String, pitch: float = 1.0, volume_db: float = 0.0) -> void:
	## Reproduce un SFX por nombre de evento
	## Uso: AudioManager.play_sfx("jump")
	## Pitch: 1.0 = normal, 0.5 = mitad velocidad, 2.0 = doble velocidad
	var stream = SFX_LIBRARY.get(event)
	if not stream:
		push_warning("AudioManager: SFX '%s' no encontrado o sin asignar" % event)
		return

	# Obtener siguiente reproductor del pool
	var player := _sfx_pool[_sfx_index % SFX_POOL_SIZE]
	_sfx_index += 1

	player.stream = stream
	player.pitch_scale = pitch
	player.volume_db = volume_db
	player.play()

func play_music(music_key: String, fade_in: float = 1.0, fade_out: float = 0.5) -> void:
	## Cambia la música con fade suave
	## Uso: AudioManager.play_music("level_01")
	var stream = MUSIC_LIBRARY.get(music_key)
	if not stream:
		push_warning("AudioManager: Música '%s' no encontrada" % music_key)
		return

	# Fade out de música actual
	if _music_player.playing:
		var tween := create_tween()
		tween.set_trans(Tween.TRANS_SINE)
		tween.set_ease(Tween.EASE_IN)
		tween.tween_property(_music_player, "volume_db", -80.0, fade_out)
		await tween.finished
		_music_player.stop()

	# Establecer nueva música y fade in
	_music_player.stream = stream
	_music_player.volume_db = -80.0
	_music_player.play()

	var tween2 := create_tween()
	tween2.set_trans(Tween.TRANS_SINE)
	tween2.set_ease(Tween.EASE_OUT)
	tween2.tween_property(_music_player, "volume_db", 0.0, fade_in)

	_current_music_stream = stream

func stop_music(fade_out: float = 1.0) -> void:
	## Detiene la música actual con fade
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_SINE)
	tween.tween_property(_music_player, "volume_db", -80.0, fade_out)
	await tween.finished
	_music_player.stop()

func set_bus_volume(bus_name: String, volume_db: float) -> void:
	## Cambia el volumen de un bus de audio
	## Rango típico: -80 (silencio) a 0 (máximo)
	var bus_idx = AudioServer.get_bus_index(bus_name)
	if bus_idx >= 0:
		AudioServer.set_bus_volume_db(bus_idx, volume_db)

func set_master_volume(volume_db: float) -> void:
	## Volumen maestro
	set_bus_volume(BUS_MASTER, volume_db)

func set_music_volume(volume_db: float) -> void:
	## Volumen de música
	set_bus_volume(BUS_MUSIC, volume_db)

func set_sfx_volume(volume_db: float) -> void:
	## Volumen de efectos de sonido
	set_bus_volume(BUS_SFX, volume_db)

## Registra dinámicamente un SFX
func register_sfx(event: String, stream: AudioStream) -> void:
	SFX_LIBRARY[event] = stream

## Registra dinámicamente una música
func register_music(key: String, stream: AudioStream) -> void:
	MUSIC_LIBRARY[key] = stream

## Obtiene el estado de reproducción de música
func is_music_playing() -> bool:
	return _music_player.playing

## Pausa/reanuda toda la música
func set_music_paused(paused: bool) -> void:
	if paused:
		_music_player.stream_paused = true
	else:
		_music_player.stream_paused = false
