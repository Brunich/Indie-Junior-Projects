## SFXLibrary.gd — Constantes y preloads centralizados para todos los eventos SFX
## Autoload: añadir como SFXLibrary en project.godot
## Uso: SFXLibrary.play(SFXLibrary.PLAYER_JUMP)
##
## Convención de carpetas esperada:
##   res://audio/sfx/player/
##   res://audio/sfx/enemy/
##   res://audio/sfx/ui/
##   res://audio/sfx/world/
##   res://audio/sfx/combat/
extends Node

# ---------------------------------------------------------------------------
# EVENTOS — claves string para identificar cada sonido
# ---------------------------------------------------------------------------

## PLAYER
const PLAYER_JUMP          := "player_jump"
const PLAYER_DOUBLE_JUMP   := "player_double_jump"
const PLAYER_LAND          := "player_land"
const PLAYER_LAND_HARD     := "player_land_hard"    # caída desde gran altura
const PLAYER_RUN_STEP      := "player_run_step"
const PLAYER_DASH          := "player_dash"
const PLAYER_HURT          := "player_hurt"
const PLAYER_DEATH         := "player_death"
const PLAYER_SHOOT         := "player_shoot"
const PLAYER_RELOAD        := "player_reload"

## COMBAT
const COMBAT_HIT_LIGHT     := "combat_hit_light"
const COMBAT_HIT_HEAVY     := "combat_hit_heavy"
const COMBAT_PARRY         := "combat_parry"
const COMBAT_CRITICAL      := "combat_critical"     # golpe on-beat (Hi-Fi Rush style)
const COMBAT_SHIELD_BLOCK  := "combat_shield_block"

## ENEMY
const ENEMY_ALERT          := "enemy_alert"
const ENEMY_ATTACK         := "enemy_attack"
const ENEMY_HURT           := "enemy_hurt"
const ENEMY_DEATH          := "enemy_death"
const ENEMY_SPAWN          := "enemy_spawn"

## WORLD / INTERACCIÓN
const WORLD_COIN_PICKUP    := "world_coin_pickup"
const WORLD_POWERUP        := "world_powerup"
const WORLD_CHECKPOINT     := "world_checkpoint"
const WORLD_DOOR_OPEN      := "world_door_open"
const WORLD_DOOR_LOCKED    := "world_door_locked"
const WORLD_EXPLOSION      := "world_explosion"
const WORLD_PLATFORM_MOVE  := "world_platform_move"

## UI
const UI_CONFIRM           := "ui_confirm"
const UI_CANCEL            := "ui_cancel"
const UI_HOVER             := "ui_hover"
const UI_PAUSE             := "ui_pause"
const UI_ACHIEVEMENT       := "ui_achievement"
const UI_LEVEL_COMPLETE    := "ui_level_complete"
const UI_GAME_OVER         := "ui_game_over"

# ---------------------------------------------------------------------------
# TABLA DE RECURSOS
# Cada entrada puede ser un AudioStream único o un Array[AudioStream]
# (el sistema elige uno al azar para dar variación natural).
# Si el archivo no existe aún, se registra null sin errores en editor.
# ---------------------------------------------------------------------------
var _sfx_table: Dictionary = {}

func _ready() -> void:
	_register_all()

func _register_all() -> void:
	# --- PLAYER ---
	_reg(PLAYER_JUMP,        "res://audio/sfx/player/jump.ogg")
	_reg(PLAYER_DOUBLE_JUMP, "res://audio/sfx/player/double_jump.ogg")
	_reg(PLAYER_LAND,        [
		"res://audio/sfx/player/land_01.ogg",
		"res://audio/sfx/player/land_02.ogg",
	])
	_reg(PLAYER_LAND_HARD,   "res://audio/sfx/player/land_hard.ogg")
	_reg(PLAYER_RUN_STEP,    [
		"res://audio/sfx/player/step_01.ogg",
		"res://audio/sfx/player/step_02.ogg",
		"res://audio/sfx/player/step_03.ogg",
	])
	_reg(PLAYER_DASH,        "res://audio/sfx/player/dash.ogg")
	_reg(PLAYER_HURT,        [
		"res://audio/sfx/player/hurt_01.ogg",
		"res://audio/sfx/player/hurt_02.ogg",
	])
	_reg(PLAYER_DEATH,       "res://audio/sfx/player/death.ogg")
	_reg(PLAYER_SHOOT,       "res://audio/sfx/player/shoot.ogg")
	_reg(PLAYER_RELOAD,      "res://audio/sfx/player/reload.ogg")

	# --- COMBAT ---
	_reg(COMBAT_HIT_LIGHT,   [
		"res://audio/sfx/combat/hit_light_01.ogg",
		"res://audio/sfx/combat/hit_light_02.ogg",
	])
	_reg(COMBAT_HIT_HEAVY,   "res://audio/sfx/combat/hit_heavy.ogg")
	_reg(COMBAT_PARRY,       "res://audio/sfx/combat/parry.ogg")
	_reg(COMBAT_CRITICAL,    "res://audio/sfx/combat/critical_beat.ogg")   # on-beat bonus
	_reg(COMBAT_SHIELD_BLOCK,"res://audio/sfx/combat/shield_block.ogg")

	# --- ENEMY ---
	_reg(ENEMY_ALERT,        "res://audio/sfx/enemy/alert.ogg")
	_reg(ENEMY_ATTACK,       "res://audio/sfx/enemy/attack.ogg")
	_reg(ENEMY_HURT,         [
		"res://audio/sfx/enemy/hurt_01.ogg",
		"res://audio/sfx/enemy/hurt_02.ogg",
	])
	_reg(ENEMY_DEATH,        "res://audio/sfx/enemy/death.ogg")
	_reg(ENEMY_SPAWN,        "res://audio/sfx/enemy/spawn.ogg")

	# --- WORLD ---
	_reg(WORLD_COIN_PICKUP,  "res://audio/sfx/world/coin.ogg")
	_reg(WORLD_POWERUP,      "res://audio/sfx/world/powerup.ogg")
	_reg(WORLD_CHECKPOINT,   "res://audio/sfx/world/checkpoint.ogg")
	_reg(WORLD_DOOR_OPEN,    "res://audio/sfx/world/door_open.ogg")
	_reg(WORLD_DOOR_LOCKED,  "res://audio/sfx/world/door_locked.ogg")
	_reg(WORLD_EXPLOSION,    "res://audio/sfx/world/explosion.ogg")
	_reg(WORLD_PLATFORM_MOVE,"res://audio/sfx/world/platform_move.ogg")

	# --- UI ---
	_reg(UI_CONFIRM,         "res://audio/sfx/ui/confirm.ogg")
	_reg(UI_CANCEL,          "res://audio/sfx/ui/cancel.ogg")
	_reg(UI_HOVER,           "res://audio/sfx/ui/hover.ogg")
	_reg(UI_PAUSE,           "res://audio/sfx/ui/pause.ogg")
	_reg(UI_ACHIEVEMENT,     "res://audio/sfx/ui/achievement.ogg")
	_reg(UI_LEVEL_COMPLETE,  "res://audio/sfx/ui/level_complete.ogg")
	_reg(UI_GAME_OVER,       "res://audio/sfx/ui/game_over.ogg")

# ---------------------------------------------------------------------------
# API PÚBLICA
# ---------------------------------------------------------------------------

## Reproduce un SFX por nombre de evento. Delega al AudioManager.
## Ejemplo: SFXLibrary.play(SFXLibrary.PLAYER_JUMP)
## bus: bus de audio (por defecto "SFX" definido en AudioManager)
func play(event: String, bus: String = "SFX") -> void:
	var stream := get_stream(event)
	if stream == null:
		push_warning("SFXLibrary: stream no encontrado para evento '%s'" % event)
		return
	if not has_node("/root/AudioManager"):
		# Fallback: reproducir directo sin pool
		var player := AudioStreamPlayer.new()
		add_child(player)
		player.stream = stream
		player.bus = bus
		player.play()
		player.finished.connect(player.queue_free)
		return
	# AudioManager.play_sfx espera el NOMBRE del evento, no el stream:
	# se registra una vez y a partir de ahi suena por el pool del manager.
	if not AudioManager.SFX_LIBRARY.has(event):
		AudioManager.register_sfx(event, stream)
	AudioManager.play_sfx(event)

## Reproduce on-beat usando BeatSync: sólo suena si estamos en ventana rítmica.
## Ideal para efectos de golpe con bonus Hi-Fi Rush style.
func play_on_beat(event: String, bus: String = "SFX") -> void:
	if has_node("/root/BeatSync") and BeatSync.is_on_beat():
		play(COMBAT_CRITICAL, bus)   # sonido especial on-beat
	else:
		play(event, bus)

## Devuelve el AudioStream registrado (elige al azar si hay variantes).
func get_stream(event: String) -> AudioStream:
	if not _sfx_table.has(event):
		return null
	var entry = _sfx_table[event]
	if entry is Array:
		if entry.is_empty():
			return null
		return entry[randi() % entry.size()]
	return entry as AudioStream

## Verifica si un evento tiene stream cargado (útil para debug).
func has_event(event: String) -> bool:
	return _sfx_table.has(event) and _sfx_table[event] != null

# ---------------------------------------------------------------------------
# PRIVADO — registro con carga segura (null si el archivo no existe)
# ---------------------------------------------------------------------------
func _reg(event: String, paths) -> void:
	if paths is Array:
		var arr: Array[AudioStream] = []
		for p in paths:
			var s := _load_safe(p)
			if s:
				arr.append(s)
		_sfx_table[event] = arr if not arr.is_empty() else null
	else:
		_sfx_table[event] = _load_safe(paths)

func _load_safe(path: String) -> AudioStream:
	if ResourceLoader.exists(path):
		return load(path) as AudioStream
	return null
