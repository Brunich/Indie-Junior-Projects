## DifficultySystem — Dificultad adaptativa de NEXUS
## No hay menú de dificultad. El mundo ajusta la presión según el patrón de juego.
## El sistema es silencioso — el jugador no ve números, solo siente el cambio.
## Se actualiza automáticamente al cruzar regiones o después de N combates.
extends RefCounted
class_name DifficultySystem

## Perfil calculado del jugador
enum Perfil {
	CAUTELOSO,    ## Evita combates, huye, protege al equipo
	EQUILIBRADO,  ## Mix estándar
	AGRESIVO,     ## Busca combates, usa ataques fuertes, va rápido
	ESTRATEGA,    ## Combates eficientes, cambios tácticos, usa ventajas
}

## Historial de métricas de juego
var _combates_ganados:    int   = 0
var _combates_huidos:     int   = 0
var _combates_esquivados: int   = 0
var _derrotas:            int   = 0
var _turnos_promedio:     float = 0.0
var _n_turnos_total:      int   = 0
var _cambios_tacticos:    int   = 0

## ── Registro de eventos ──────────────────────────────────────────────────────

func registrar_combate_ganado(turnos: int, con_cambio: bool) -> void:
	_combates_ganados += 1
	_n_turnos_total += turnos
	_turnos_promedio = float(_n_turnos_total) / float(_combates_ganados + _derrotas)
	if con_cambio:
		_cambios_tacticos += 1

func registrar_huida() -> void:
	_combates_huidos += 1

func registrar_encuentro_evitado() -> void:
	_combates_esquivados += 1

func registrar_derrota() -> void:
	_derrotas += 1

## ── Cálculo del perfil ────────────────────────────────────────────────────────

func calcular_perfil() -> Perfil:
	var total := _combates_ganados + _combates_huidos + _derrotas
	if total == 0:
		return Perfil.EQUILIBRADO

	var ratio_evasion := float(_combates_huidos + _combates_esquivados) / float(total + _combates_esquivados)
	var ratio_cambio  := float(_cambios_tacticos) / float(max(1, _combates_ganados))

	if ratio_evasion > 0.5:
		return Perfil.CAUTELOSO
	if _turnos_promedio <= 3.0 and ratio_evasion < 0.2:
		return Perfil.AGRESIVO
	if ratio_cambio > 0.4:
		return Perfil.ESTRATEGA
	return Perfil.EQUILIBRADO

## ── Modificadores de encuentro ────────────────────────────────────────────────

## Modificador de nivel para enemigos salvajes (1.0 = sin cambio)
func modificador_nivel() -> float:
	match calcular_perfil():
		Perfil.CAUTELOSO:  return 0.90
		Perfil.AGRESIVO:   return 1.15
		Perfil.ESTRATEGA:  return 1.10
	return 1.0

## Nivel de IA del entrenador enemigo (1-4)
func nivel_ia() -> int:
	match calcular_perfil():
		Perfil.CAUTELOSO:  return 1
		Perfil.AGRESIVO:   return 3
		Perfil.ESTRATEGA:  return 4
	return 2

## Frecuencia relativa de encuentros en hierba alta (0.5 - 1.5)
func frecuencia_encuentros() -> float:
	match calcular_perfil():
		Perfil.CAUTELOSO:  return 0.7
		Perfil.AGRESIVO:   return 1.3
	return 1.0

## ¿Los entrenadores rivales usan cambios tácticos?
func entrenadores_usan_cambios() -> bool:
	return calcular_perfil() == Perfil.ESTRATEGA

## ── Serialización ─────────────────────────────────────────────────────────────

func to_dict() -> Dictionary:
	return {
		"combates_ganados":    _combates_ganados,
		"combates_huidos":     _combates_huidos,
		"combates_esquivados": _combates_esquivados,
		"derrotas":            _derrotas,
		"turnos_promedio":     _turnos_promedio,
		"n_turnos_total":      _n_turnos_total,
		"cambios_tacticos":    _cambios_tacticos,
	}

func from_dict(d: Dictionary) -> void:
	_combates_ganados    = d.get("combates_ganados",    0)
	_combates_huidos     = d.get("combates_huidos",     0)
	_combates_esquivados = d.get("combates_esquivados", 0)
	_derrotas            = d.get("derrotas",            0)
	_turnos_promedio     = d.get("turnos_promedio",     0.0)
	_n_turnos_total      = d.get("n_turnos_total",      0)
	_cambios_tacticos    = d.get("cambios_tacticos",    0)
