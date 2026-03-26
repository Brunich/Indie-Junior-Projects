## GameOptions — Player settings (classic Pokemon-style + extras)
## Autoloaded singleton. Persists to user://options.cfg
extends Node

# ── Classic Pokemon options ───────────────────────────────────────────────────
var text_speed        : int  = 1   ## 0=Slow, 1=Mid, 2=Fast, 3=Instant
var battle_animations : bool = true
var battle_style      : int  = 0   ## 0=Shift (asked to switch), 1=Set (not asked)
var sound             : int  = 1   ## 0=Mono, 1=Stereo
var bgm_volume        : float = 0.8
var sfx_volume        : float = 1.0

# ── Extra Emberveil options ───────────────────────────────────────────────────
var exp_share_auto    : bool = false ## Auto EXP share to whole party
var run_anywhere      : bool = false ## Can always run (no wild-can't-run rule)
var show_damage_nums  : bool = true  ## Show damage numbers in battle
var show_type_hint    : bool = false ## Show type effectiveness hint (beginner mode)
var show_move_pp      : bool = true  ## Show PP next to moves
var auto_heal_box     : bool = false ## Auto-heal when depositing to box
var nuzlocke_mode     : bool = false ## Nuzlocke rules (permadeath)
var hardcore_mode     : bool = false ## No items in battle
var language          : String = "es" ## "es" or "en"

const SAVE_PATH := "user://options.cfg"

func _ready() -> void:
	load_options()

func save_options() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("classic", "text_speed", text_speed)
	cfg.set_value("classic", "battle_animations", battle_animations)
	cfg.set_value("classic", "battle_style", battle_style)
	cfg.set_value("classic", "sound", sound)
	cfg.set_value("audio", "bgm_volume", bgm_volume)
	cfg.set_value("audio", "sfx_volume", sfx_volume)
	cfg.set_value("extras", "exp_share_auto", exp_share_auto)
	cfg.set_value("extras", "run_anywhere", run_anywhere)
	cfg.set_value("extras", "show_damage_nums", show_damage_nums)
	cfg.set_value("extras", "show_type_hint", show_type_hint)
	cfg.set_value("extras", "show_move_pp", show_move_pp)
	cfg.set_value("extras", "auto_heal_box", auto_heal_box)
	cfg.set_value("extras", "nuzlocke_mode", nuzlocke_mode)
	cfg.set_value("extras", "hardcore_mode", hardcore_mode)
	cfg.set_value("extras", "language", language)
	cfg.save(SAVE_PATH)

func load_options() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) != OK:
		return
	text_speed        = cfg.get_value("classic", "text_speed", 1)
	battle_animations = cfg.get_value("classic", "battle_animations", true)
	battle_style      = cfg.get_value("classic", "battle_style", 0)
	sound             = cfg.get_value("classic", "sound", 1)
	bgm_volume        = cfg.get_value("audio", "bgm_volume", 0.8)
	sfx_volume        = cfg.get_value("audio", "sfx_volume", 1.0)
	exp_share_auto    = cfg.get_value("extras", "exp_share_auto", false)
	run_anywhere      = cfg.get_value("extras", "run_anywhere", false)
	show_damage_nums  = cfg.get_value("extras", "show_damage_nums", true)
	show_type_hint    = cfg.get_value("extras", "show_type_hint", false)
	show_move_pp      = cfg.get_value("extras", "show_move_pp", true)
	auto_heal_box     = cfg.get_value("extras", "auto_heal_box", false)
	nuzlocke_mode     = cfg.get_value("extras", "nuzlocke_mode", false)
	hardcore_mode     = cfg.get_value("extras", "hardcore_mode", false)
	language          = cfg.get_value("extras", "language", "es")

func get_text_delay() -> float:
	match text_speed:
		0: return 0.07  # Slow
		1: return 0.04  # Mid
		2: return 0.02  # Fast
		3: return 0.0   # Instant
	return 0.04
