## AudioManager — Gen 4-style music system for Emberveil
## Handles: BGM transitions, battle jingles, SFX via AudioStreamPlayer nodes.
## Registered as autoload "AudioManager" in project.godot.
extends Node

# ── Track registry ────────────────────────────────────────────────────────────
const MUSIC_DIR := "res://assets/music/"
const TRACKS := {
	# Overworld
	"cinder_village":  "overworld_cinder.wav",
	"route_1":         "overworld_route1.wav",
	"sea":             "overworld_sea.wav",
	# Battle
	"battle_wild":     "battle_wild.wav",
	"battle_trainer":  "battle_trainer.wav",
	"battle_gym":      "battle_gym.wav",
}

# ── Zone → track map (set in each scene or via set_zone) ─────────────────────
const ZONE_MUSIC := {
	"cinder_village": "cinder_village",
	"ashgate_town":   "cinder_village",   # placeholder until Gym 1 theme added
	"route_1":        "route_1",
	"route_2":        "sea",
	"tidelock_port":  "sea",
	"overworld_sea":  "sea",
}

# ── Fade config ───────────────────────────────────────────────────────────────
const FADE_OUT_TIME := 0.6
const FADE_IN_TIME  := 0.8

var _current_track : String = ""
var _bgm_player    : AudioStreamPlayer
var _fade_tween    : Tween = null
var _pending_track : String = ""

# ─────────────────────────────────────────────────────────────────────────────
func _ready() -> void:
	_bgm_player = AudioStreamPlayer.new()
	_bgm_player.bus = "Music"
	add_child(_bgm_player)

# ── Public API ────────────────────────────────────────────────────────────────

## Play a track by key (from TRACKS dict). Crossfades if different from current.
func play(track_key: String, force_restart: bool = false) -> void:
	if track_key == _current_track and not force_restart:
		return
	_pending_track = track_key
	if _bgm_player.playing:
		_fade_out_then_in()
	else:
		_start_track(track_key)

## Stop music with fade
func stop(fade: bool = true) -> void:
	_pending_track = ""
	if fade:
		_fade_out_and_stop()
	else:
		_bgm_player.stop()
		_current_track = ""

## Called when entering a zone/scene — auto-selects appropriate music
func on_zone_enter(zone_name: String) -> void:
	var track_key = ZONE_MUSIC.get(zone_name, "route_1")
	play(track_key)

## Called when battle starts
func on_battle_start(battle_type: String = "wild") -> void:
	match battle_type:
		"wild":    play("battle_wild",    true)
		"trainer": play("battle_trainer", true)
		"gym":     play("battle_gym",     true)
		_:         play("battle_wild",    true)

## Restore overworld music after battle
func on_battle_end(zone_key: String = "") -> void:
	var restore = zone_key if zone_key != "" else "route_1"
	play(restore)

## Adjust master music volume (0.0–1.0)
func set_volume(v: float) -> void:
	_bgm_player.volume_db = linear_to_db(clamp(v, 0.0, 1.0))

# ── Internal ──────────────────────────────────────────────────────────────────

func _start_track(key: String) -> void:
	var filename = TRACKS.get(key, "")
	if filename == "":
		push_warning("AudioManager: unknown track key '%s'" % key)
		return
	var path = MUSIC_DIR + filename
	var stream = load(path) if ResourceLoader.exists(path) else null
	if stream == null:
		_current_track = ""
		return

	_bgm_player.stream = stream
	_bgm_player.volume_db = -80.0
	_bgm_player.play()
	_current_track = key

	if _fade_tween:
		_fade_tween.kill()
	_fade_tween = create_tween()
	_fade_tween.tween_property(_bgm_player, "volume_db", 0.0, FADE_IN_TIME)

func _fade_out_then_in() -> void:
	if _fade_tween:
		_fade_tween.kill()
	_fade_tween = create_tween()
	_fade_tween.tween_property(_bgm_player, "volume_db", -80.0, FADE_OUT_TIME)
	_fade_tween.tween_callback(func():
		_bgm_player.stop()
		_start_track(_pending_track)
	)

func _fade_out_and_stop() -> void:
	if _fade_tween:
		_fade_tween.kill()
	_fade_tween = create_tween()
	_fade_tween.tween_property(_bgm_player, "volume_db", -80.0, FADE_OUT_TIME)
	_fade_tween.tween_callback(func():
		_bgm_player.stop()
		_current_track = ""
	)

## Ensure music loops — reconnect when finished
func _notification(what: int) -> void:
	if what == NOTIFICATION_READY:
		_bgm_player.finished.connect(_on_bgm_finished)

func _on_bgm_finished() -> void:
	if _current_track != "":
		_bgm_player.play()  # loop
