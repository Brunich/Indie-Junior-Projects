## ResonanciaPlena — Estado de Eco máximo (equivalente a Mega Evolución)
## Solo disponible cuando el Latido del Nexo está en estado RESONANTE.
## No es una evolución permanente — es un momento de máxima presencia mutua.
## Solo 1 Nexo por batalla. Se rompe si el Latido cae a TENSO durante el estado.
extends Node
class_name ResonanciaPlena

signal resonancia_iniciada(nexo_id: String)
signal resonancia_terminada(nexo_id: String)
signal resonancia_rota(nexo_id: String)  ## Si el Latido cayó durante el estado

## Nexos que soportan Resonancia Plena y sus modificadores temporales de stat
const RESONANCIA_DATA := {
	"volcandar":      { "stat_boost": {"atk": 30, "sp_atk": 30, "speed": 15}, "duracion": 3 },
	"florasma":       { "stat_boost": {"def": 25, "sp_def": 25, "speed": 20}, "duracion": 4 },
	"deltaire":       { "stat_boost": {"sp_atk": 40, "speed": 25},            "duracion": 3 },
	"banderalma":     { "stat_boost": {"sp_atk": 35, "sp_def": 20},           "duracion": 4 },
	"umbracaliz":     { "stat_boost": {"sp_atk": 40, "sp_def": 30},           "duracion": 3 },
	"tiburlava":      { "stat_boost": {"atk": 25, "sp_atk": 25, "speed": 20}, "duracion": 3 },
	"carburo":        { "stat_boost": {"atk": 35, "speed": 25},               "duracion": 3 },
	"xolcan":         { "stat_boost": {"sp_atk": 30, "atk": 20, "speed": 15}, "duracion": 4 },
	"luminariax":     { "stat_boost": {"sp_atk": 45, "speed": 20},            "duracion": 2 },
	"polilla_sudario":{ "stat_boost": {"sp_atk": 45, "sp_def": 20},           "duracion": 3 },
}

## Estado de combate actual
var _nexo_activo: String = ""
var _turnos_restantes: int = 0
var _usado_esta_batalla: bool = false
var _stats_originales: Dictionary = {}

## Referencia al LatidoSystem (inyectada desde BattleManager)
var latido: LatidoSystem = null

## ── API de combate ─────────────────────────────────────────────────────────────

## Reinicia el estado entre batallas
func reset_batalla() -> void:
	if _nexo_activo != "":
		resonancia_terminada.emit(_nexo_activo)
	_nexo_activo = ""
	_turnos_restantes = 0
	_usado_esta_batalla = false
	_stats_originales.clear()

## ¿Se puede activar la Resonancia Plena?
func puede_activar(nexo_id: String) -> bool:
	if _usado_esta_batalla:
		return false
	if not RESONANCIA_DATA.has(nexo_id):
		return false
	if latido == null:
		return false
	return latido.puede_resonar_pleno(nexo_id)

## Activa la Resonancia Plena para un Nexo
## stats_actuales: Dictionary con los stats base actuales del Nexo
## Devuelve los stats modificados temporalmente, o {} si no puede activarse
func activar(nexo_id: String, stats_actuales: Dictionary) -> Dictionary:
	if not puede_activar(nexo_id):
		return {}
	var datos := RESONANCIA_DATA[nexo_id]
	_nexo_activo = nexo_id
	_turnos_restantes = datos["duracion"]
	_usado_esta_batalla = true
	_stats_originales = stats_actuales.duplicate()

	var stats_modificados := stats_actuales.duplicate()
	for stat in datos["stat_boost"]:
		if stats_modificados.has(stat):
			stats_modificados[stat] += datos["stat_boost"][stat]

	resonancia_iniciada.emit(nexo_id)
	return stats_modificados

## Llama al final de cada turno mientras la Resonancia esté activa
## Devuelve true si la Resonancia continúa, false si terminó
func tick_turno() -> bool:
	if _nexo_activo == "":
		return false

	# Verificar si el Latido cayó durante el estado
	if latido != null and not latido.puede_resonar_pleno(_nexo_activo):
		resonancia_rota.emit(_nexo_activo)
		_terminar_resonancia()
		return false

	_turnos_restantes -= 1
	if _turnos_restantes <= 0:
		resonancia_terminada.emit(_nexo_activo)
		_terminar_resonancia()
		return false
	return true

## Devuelve los stats originales sin modificar (para restaurar al terminar)
func get_stats_originales() -> Dictionary:
	return _stats_originales.duplicate()

## ¿Hay una Resonancia activa?
func esta_activa() -> bool:
	return _nexo_activo != ""

## ¿Qué Nexo tiene Resonancia activa?
func nexo_activo() -> String:
	return _nexo_activo

func _terminar_resonancia() -> void:
	_nexo_activo = ""
	_turnos_restantes = 0
	_stats_originales.clear()
