## BeatSync.gd — Reloj global de BPM para efectos rítmicos
## Autoload: añadir como BeatSync en project.godot
## Inspirado en Hi-Fi Rush: inputs on-beat dan puntos bonus
extends Node

## Emitida en cada beat (BPM configurable)
signal on_beat(beat_number: int)
## Emitida cada medio beat
signal on_half_beat

@export var bpm: float = 120.0
## Ventana de ±80ms donde un input cuenta como "on beat"
const BEAT_WINDOW_SEC: float = 0.080

var _beat_timer: float = 0.0
var _beat_number: int = 0
var _beat_duration: float = 0.5  # se recalcula en _ready

func _ready() -> void:
    _beat_duration = 60.0 / bpm

func set_bpm(new_bpm: float) -> void:
    bpm = new_bpm
    _beat_duration = 60.0 / bpm

func _process(delta: float) -> void:
    _beat_timer += delta
    if _beat_timer >= _beat_duration:
        _beat_timer -= _beat_duration
        _beat_number += 1
        on_beat.emit(_beat_number)
    if _beat_timer >= _beat_duration * 0.5 and _beat_timer < _beat_duration * 0.5 + delta:
        on_half_beat.emit()

## Retorna true si estamos dentro de la ventana on-beat (±80ms)
func is_on_beat() -> bool:
    var dist := minf(_beat_timer, _beat_duration - _beat_timer)
    return dist <= BEAT_WINDOW_SEC

## Multiplicador para puntos rítmicos (2x on-beat, 1x off-beat)
func get_beat_multiplier() -> float:
    return 2.0 if is_on_beat() else 1.0

## Progreso del beat actual (0.0 → 1.0)
func get_beat_progress() -> float:
    return _beat_timer / _beat_duration
