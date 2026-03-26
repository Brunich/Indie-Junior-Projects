## DayNightSystem — Real-time day/night cycle (Pokémon Gold/Silver style + extended)
## Time phases: DAWN(5-7) MORNING(7-12) AFTERNOON(12-17) EVENING(17-20) NIGHT(20-5)
## Affects: wild encounter tables, NPC schedules, ambient color overlays
extends Node

enum TimePhase { DAWN, MORNING, AFTERNOON, EVENING, NIGHT }

## Use in-game time (1 real second = 2 in-game minutes, so full day = 12 real minutes)
## Or sync to real clock (option in GameOptions)
@export var use_real_clock : bool = true
@export var time_scale     : float = 120.0  ## 1 real second = 120 in-game seconds (if not real clock)

var current_hour    : int   = 8
var current_minute  : int   = 0
var current_phase   : TimePhase = TimePhase.MORNING

## Color overlays per phase (modulate for the game world CanvasLayer)
const PHASE_COLORS := {
	TimePhase.DAWN:      Color(1.0, 0.85, 0.70, 1.0),  ## warm orange tint
	TimePhase.MORNING:   Color(1.0, 1.0,  1.0,  1.0),  ## normal
	TimePhase.AFTERNOON: Color(1.0, 0.97, 0.90, 1.0),  ## slight warmth
	TimePhase.EVENING:   Color(0.85, 0.65, 0.5, 1.0),  ## deep orange-amber
	TimePhase.NIGHT:     Color(0.35, 0.40, 0.65, 1.0), ## dark blue tint
}

## Encounter rate modifiers per phase (multiplicative)
const ENCOUNTER_MODIFIERS := {
	TimePhase.DAWN:      {"ghost": 1.5, "normal": 0.8},
	TimePhase.MORNING:   {"normal": 1.0},
	TimePhase.AFTERNOON: {"fire": 1.3, "normal": 1.0},
	TimePhase.EVENING:   {"ghost": 1.3, "dark": 1.2},
	TimePhase.NIGHT:     {"ghost": 2.0, "dark": 1.8, "normal": 0.5},
}

signal phase_changed(new_phase: TimePhase)
signal hour_changed(new_hour: int)

func _ready() -> void:
	_update_time()
	# Update every in-game minute
	var t := Timer.new()
	t.wait_time = 1.0 / time_scale * 60.0 if not use_real_clock else 60.0
	t.timeout.connect(_tick)
	t.autostart = true
	add_child(t)

func _update_time() -> void:
	if use_real_clock:
		var dt := Time.get_datetime_dict_from_system()
		current_hour   = dt.get("hour", 8)
		current_minute = dt.get("minute", 0)
	var new_phase := _hour_to_phase(current_hour)
	if new_phase != current_phase:
		current_phase = new_phase
		emit_signal("phase_changed", current_phase)

func _tick() -> void:
	if use_real_clock:
		_update_time()
	else:
		current_minute += 1
		if current_minute >= 60:
			current_minute = 0
			current_hour = (current_hour + 1) % 24
			emit_signal("hour_changed", current_hour)
		_update_time()

func _hour_to_phase(h: int) -> TimePhase:
	if h >= 5  and h < 7:  return TimePhase.DAWN
	if h >= 7  and h < 12: return TimePhase.MORNING
	if h >= 12 and h < 17: return TimePhase.AFTERNOON
	if h >= 17 and h < 20: return TimePhase.EVENING
	return TimePhase.NIGHT

func get_world_color() -> Color:
	return PHASE_COLORS[current_phase]

func get_encounter_modifier(creature_type: String) -> float:
	var mods = ENCOUNTER_MODIFIERS.get(current_phase, {})
	return mods.get(creature_type.to_lower(), mods.get("normal", 1.0))

func get_time_string() -> String:
	return "%02d:%02d" % [current_hour, current_minute]

func is_night() -> bool:
	return current_phase == TimePhase.NIGHT

func is_day() -> bool:
	return current_phase in [TimePhase.MORNING, TimePhase.AFTERNOON]
