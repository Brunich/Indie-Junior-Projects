## LatidoSystem — Estado del vínculo entre portador y Nexo (El Latido / Nexus Safe)
## Cada Nexo del equipo tiene un estado de Latido independiente.
## El estado no se muestra como número — se lee en comportamiento.
## Cuatro estados: RESONANTE, ESTABLE, TENSO, ROTO
extends RefCounted
class_name LatidoSystem

enum Estado { RESONANTE, ESTABLE, TENSO, ROTO }

## Valor interno del vínculo: 0 (Roto) ↔ 100 (Resonante)
## No se expone directamente en UI — solo el estado se comunica al jugador.
const UMBRAL_RESONANTE := 80
const UMBRAL_ESTABLE   := 50
const UMBRAL_TENSO     := 20

## Mapa de nexo_id (String) → valor de vínculo (int 0-100)
## Se guarda junto con el CreatureInstance en SaveSystem.
var vinculos: Dictionary = {}

## ── API principal ─────────────────────────────────────────────────────────────

## Inicializa el vínculo de un Nexo nuevo (comienza estable)
func registrar_nexo(nexo_id: String, valor_inicial: int = 60) -> void:
	if not vinculos.has(nexo_id):
		vinculos[nexo_id] = clamp(valor_inicial, 0, 100)

## Devuelve el estado actual del Latido de un Nexo
func estado(nexo_id: String) -> Estado:
	var v: int = vinculos.get(nexo_id, 60)
	if v >= UMBRAL_RESONANTE: return Estado.RESONANTE
	if v >= UMBRAL_ESTABLE:   return Estado.ESTABLE
	if v >= UMBRAL_TENSO:     return Estado.TENSO
	return Estado.ROTO

## Modifica el vínculo. Positivo = mejora. Negativo = deterioro.
func modificar(nexo_id: String, cantidad: int) -> void:
	if not vinculos.has(nexo_id):
		registrar_nexo(nexo_id)
	vinculos[nexo_id] = clamp(vinculos[nexo_id] + cantidad, 0, 100)

## Eventos que mejoran el Latido
func evento_cuidado(nexo_id: String) -> void:
	modificar(nexo_id, +8)   # Curar fuera de combate

func evento_descanso(nexo_id: String) -> void:
	modificar(nexo_id, +5)   # Descansar en posada

func evento_victoria(nexo_id: String) -> void:
	modificar(nexo_id, +3)   # Ganar un combate

func evento_interaccion(nexo_id: String) -> void:
	modificar(nexo_id, +2)   # Tocar, llamar, inspeccionar al Nexo

## Eventos que deterioran el Latido
func evento_derrota(nexo_id: String) -> void:
	modificar(nexo_id, -4)   # El Nexo cayó en combate

func evento_descuido(nexo_id: String) -> void:
	modificar(nexo_id, -3)   # No curar al Nexo después de batalla

func evento_sobrecarga(nexo_id: String) -> void:
	modificar(nexo_id, -6)   # Usar al Nexo sin descanso durante muchos combates

func evento_daño_critico(nexo_id: String) -> void:
	modificar(nexo_id, -8)   # Nexo recibió daño crítico severo

func evento_atado_temporal(nexo_id: String) -> void:
	modificar(nexo_id, -15)  # Usar piedra de resonancia forzada sobre un Nexo voluntario

## ── Comportamientos según estado ─────────────────────────────────────────────

## ¿El Nexo puede actuar con iniciativa propia en combate?
func tiene_iniciativa(nexo_id: String) -> bool:
	return estado(nexo_id) == Estado.RESONANTE

## ¿El Nexo obedece sin hesitación?
func obedece_directo(nexo_id: String) -> bool:
	return estado(nexo_id) in [Estado.RESONANTE, Estado.ESTABLE]

## ¿El Nexo puede desobedecer o actuar erráticamente?
func puede_desobedecer(nexo_id: String) -> bool:
	return estado(nexo_id) == Estado.TENSO

## ¿El Nexo está en estado crítico de vínculo?
func esta_roto(nexo_id: String) -> bool:
	return estado(nexo_id) == Estado.ROTO

## ¿El Nexo puede entrar en Resonancia Plena?
func puede_resonar_pleno(nexo_id: String) -> bool:
	return estado(nexo_id) == Estado.RESONANTE

## Probabilidad de desobediencia en TENSO (0.0 - 1.0)
func prob_desobediencia(nexo_id: String) -> float:
	if estado(nexo_id) != Estado.TENSO:
		return 0.0
	var v: int = vinculos.get(nexo_id, 60)
	return inverse_lerp(float(UMBRAL_TENSO), float(UMBRAL_ESTABLE), float(v))

## ── Nombre y descripción del estado ─────────────────────────────────────────

static func nombre_estado(e: Estado) -> String:
	match e:
		Estado.RESONANTE: return "Resonante"
		Estado.ESTABLE:   return "Estable"
		Estado.TENSO:     return "Tenso"
		Estado.ROTO:      return "Roto"
	return "Desconocido"

static func descripcion_estado(e: Estado) -> String:
	match e:
		Estado.RESONANTE:
			return "Vínculo pleno. El Nexo actúa con voluntad propia."
		Estado.ESTABLE:
			return "Vínculo sano. Todo funciona como debe."
		Estado.TENSO:
			return "El vínculo se está deteriorando. El Nexo lo nota."
		Estado.ROTO:
			return "El vínculo se rompió. El Nexo actúa solo."
	return ""

## ── Serialización ─────────────────────────────────────────────────────────────

func to_dict() -> Dictionary:
	return { "vinculos": vinculos.duplicate() }

func from_dict(d: Dictionary) -> void:
	vinculos = d.get("vinculos", {})
