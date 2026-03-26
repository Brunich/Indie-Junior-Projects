## HuellaSystem — Sistema de Huella del jugador (Identidad)
## Observa el comportamiento real del jugador y construye una identidad acumulada.
## No hay menú de selección. El jugador no elige su huella — la vive.
## Cuatro tipos: RAIZ, VIENTO, BRASA, NIEBLA
## El tipo dominante desbloquea eventos narrativos exclusivos y modifica respuestas de NPCs.
extends RefCounted
class_name HuellaSystem

enum Tipo { RAIZ, VIENTO, BRASA, NIEBLA }

## Puntos acumulados por tipo (0 - ∞)
## Se guardan en SaveSystem junto con el resto del estado del jugador.
var puntos := { Tipo.RAIZ: 0, Tipo.VIENTO: 0, Tipo.BRASA: 0, Tipo.NIEBLA: 0 }

## Historial de últimas 20 acciones (para tendencia reciente)
var _historial: Array[Tipo] = []
const HISTORIAL_MAX := 20

## ── Pesos de acción ──────────────────────────────────────────────────────────
## Cada acción suma puntos al tipo correspondiente.
## Las acciones tienen pesos distintos según su impacto en la identidad.
const ACCIONES := {
	# Cuidado y vínculo
	"curar_nexo":          { "tipo": Tipo.RAIZ,   "peso": 3 },
	"interactuar_nexo":    { "tipo": Tipo.RAIZ,   "peso": 1 },
	"restaurar_atado":     { "tipo": Tipo.RAIZ,   "peso": 5 },
	"ignorar_atado":       { "tipo": Tipo.BRASA,  "peso": 2 },

	# Exploración
	"zona_secreta":        { "tipo": Tipo.VIENTO, "peso": 3 },
	"npc_opcional":        { "tipo": Tipo.VIENTO, "peso": 2 },
	"lore_encontrado":     { "tipo": Tipo.VIENTO, "peso": 2 },
	"saltarse_combate":    { "tipo": Tipo.NIEBLA, "peso": 2 },

	# Combate
	"iniciar_combate":     { "tipo": Tipo.BRASA,  "peso": 2 },
	"victoria_rapida":     { "tipo": Tipo.BRASA,  "peso": 3 },
	"combate_eficiente":   { "tipo": Tipo.BRASA,  "peso": 1 },
	"proteger_nexo":       { "tipo": Tipo.RAIZ,   "peso": 2 },

	# Sigilo / evasión
	"evitar_encuentro":    { "tipo": Tipo.NIEBLA, "peso": 3 },
	"ruta_alterna":        { "tipo": Tipo.NIEBLA, "peso": 2 },
	"observar_sin_actuar": { "tipo": Tipo.NIEBLA, "peso": 2 },

	# Diálogo
	"dialogo_curioso":     { "tipo": Tipo.VIENTO, "peso": 1 },
	"dialogo_directo":     { "tipo": Tipo.BRASA,  "peso": 1 },
	"dialogo_empático":    { "tipo": Tipo.RAIZ,   "peso": 2 },
	"dialogo_silencioso":  { "tipo": Tipo.NIEBLA, "peso": 2 },
}

## ── API principal ─────────────────────────────────────────────────────────────

## Registra una acción del jugador. Llamar desde GameManager o controladores.
func registrar(accion_id: String) -> void:
	if not ACCIONES.has(accion_id):
		return
	var entrada := ACCIONES[accion_id]
	var tipo: Tipo = entrada["tipo"]
	var peso: int  = entrada["peso"]
	puntos[tipo] += peso
	_historial.append(tipo)
	if _historial.size() > HISTORIAL_MAX:
		_historial.pop_front()

## Tipo dominante acumulado (el que más puntos tiene)
func tipo_dominante() -> Tipo:
	var mejor := Tipo.RAIZ
	var max_pts := -1
	for t in puntos:
		if puntos[t] > max_pts:
			max_pts = puntos[t]
			mejor = t
	return mejor

## Tipo de tendencia reciente (últimas HISTORIAL_MAX acciones)
## Útil para adaptar eventos narrativos al estado actual, no al total.
func tendencia_reciente() -> Tipo:
	if _historial.is_empty():
		return tipo_dominante()
	var conteo := { Tipo.RAIZ: 0, Tipo.VIENTO: 0, Tipo.BRASA: 0, Tipo.NIEBLA: 0 }
	for t in _historial:
		conteo[t] += 1
	var mejor := Tipo.RAIZ
	var max_c := -1
	for t in conteo:
		if conteo[t] > max_c:
			max_c = conteo[t]
			mejor = t
	return mejor

## Verifica si el jugador tiene al menos N puntos de un tipo
func tiene_umbral(tipo: Tipo, umbral: int) -> bool:
	return puntos.get(tipo, 0) >= umbral

## Nombre legible del tipo
static func nombre(tipo: Tipo) -> String:
	match tipo:
		Tipo.RAIZ:   return "Raíz"
		Tipo.VIENTO: return "Viento"
		Tipo.BRASA:  return "Brasa"
		Tipo.NIEBLA: return "Niebla"
	return "Desconocida"

## Descripción corta del tipo (para UI de pausa / reflexión)
static func descripcion(tipo: Tipo) -> String:
	match tipo:
		Tipo.RAIZ:
			return "Proteges. Cuidas. El vínculo importa más que el resultado."
		Tipo.VIENTO:
			return "Explorar primero, actuar después. El mundo tiene más de lo que muestra."
		Tipo.BRASA:
			return "Directo. Rápido. El resultado vale más que el método."
		Tipo.NIEBLA:
			return "Observas sin ser visto. La mejor acción es la que no necesita hacerse."
	return ""

## Serialización para guardado
func to_dict() -> Dictionary:
	return {
		"puntos": {
			"raiz":   puntos[Tipo.RAIZ],
			"viento": puntos[Tipo.VIENTO],
			"brasa":  puntos[Tipo.BRASA],
			"niebla": puntos[Tipo.NIEBLA],
		}
	}

## Restauración desde guardado
func from_dict(d: Dictionary) -> void:
	var p: Dictionary = d.get("puntos", {})
	puntos[Tipo.RAIZ]   = p.get("raiz",   0)
	puntos[Tipo.VIENTO] = p.get("viento", 0)
	puntos[Tipo.BRASA]  = p.get("brasa",  0)
	puntos[Tipo.NIEBLA] = p.get("niebla", 0)
