## ============================================================
## DialogueManager.gd — Sistema de Diálogos Centralizado
## Bruno Salas | UANL Monterrey | 2026
## ============================================================
## Autoload: añadir en project.godot como DialogueManager
## Gestiona todos los diálogos de personajes del juego

extends Node

# ---- SEÑALES ----
signal dialogue_started(character: String, text: String)
signal dialogue_ended

# ---- PROPIEDADES ----
var _active: bool = false
var _current_speaker: String = ""
var _display_duration: float = 3.0

# ---- BIBLIOTECA DE DIÁLOGOS ----
var DIALOGUE_LIBRARY: Dictionary = {
	"thanatos": {
		"aparicion": "Expediente abierto. Naturaleza del caso: caos humano recurrente. Prognosis: negativa.",
		"player_muere": "Defunción registrada. Solicitud de segunda oportunidad: procesada. Espere en la cola.",
		"player_gana": "Conclusión inesperada. Procedimiento standard violado. Auditoría iniciada.",
		"recibe_daño": "Protesta formal presentada. Daño no autorizado a propiedad corporativa.",
		"idle": "¿Solicitud en espera? Los trámites tardan. Mínimo 45 minutos de espera estimado.",
		"power_up": "Ventaja obtenida mediante medios irregulares. Sanción pendiente.",
	},
	"iris": {
		"aparicion": "Otro desventurado en el purgatorio administrativo. Bienvenido. Thanatos cobra por hablador.",
		"player_muere": "Ouch. Eso contó para tu historial de estrés. Pero aquí el 'game over' es solo un papeleo más.",
		"player_gana": "¡Wow! Cortaste las cintas rojas. Thanatos va a estar furioso. Disfruta el momento.",
		"recibe_daño": "Eh, tranquilo paladín. Tengo seguro. Aunque rellenar el formulario es más mortal.",
		"idle": "¿Se te pegó el teclado? Entiendo, Thanatos aburre. Pero vamos, sigue avanzando.",
		"power_up": "Ooh, equipo gratis. Equivalente a un soborno burocrático. Me encanta.",
		"ambiente": "Sabes, en todos mis años aquí, nadie como tú ha llegado tan lejos.",
	}
}

func _ready() -> void:
	# Conectar señales del GameManager
	var gm = get_node_or_null("/root/GameManager")
	if gm:
		if gm.has_signal("player_died"):
			gm.player_died.connect(_on_player_died)
		if gm.has_signal("player_victory"):
			gm.player_victory.connect(_on_player_victory)

func say(character: String, key: String) -> void:
	## Reproduce un diálogo de un personaje
	## Uso: DialogueManager.say("thanatos", "aparicion")
	if _active:
		return  # No interrumpir diálogos en progreso

	var text = _get_dialogue(character, key)
	if not text:
		push_warning("DialogueManager: '%s' / '%s' no encontrado" % [character, key])
		return

	# Solo el servidor en multiplayer emite diálogos
	if multiplayer.is_server() or not multiplayer.has_multiplayer_peer():
		_show_dialogue.rpc(character, text)
	else:
		_show_dialogue.rpc_id(1, character, text)

@rpc("authority", "call_local", "reliable")
func _show_dialogue(character: String, text: String) -> void:
	_active = true
	_current_speaker = character
	dialogue_started.emit(character, text)

	# Mostrar por el tiempo calculado (1 segundo + 0.05 por carácter)
	var delay = 1.0 + (text.length() * 0.05)
	await get_tree().create_timer(delay).timeout

	_active = false
	dialogue_ended.emit()

func _get_dialogue(character: String, key: String) -> String:
	## Busca en la biblioteca y retorna el texto (o cadena vacía)
	if character not in DIALOGUE_LIBRARY:
		return ""
	if key not in DIALOGUE_LIBRARY[character]:
		return ""
	return DIALOGUE_LIBRARY[character][key]

func _on_player_died(player: Node) -> void:
	## Callback cuando el jugador muere
	if randf() < 0.7:
		say("thanatos", "player_muere")
	else:
		say("iris", "player_muere")

func _on_player_victory() -> void:
	## Callback cuando el jugador gana
	if randf() < 0.6:
		say("iris", "player_gana")
	else:
		say("thanatos", "player_gana")

## Método para añadir diálogos dinámicamente
func add_dialogue(character: String, key: String, text: String) -> void:
	if character not in DIALOGUE_LIBRARY:
		DIALOGUE_LIBRARY[character] = {}
	DIALOGUE_LIBRARY[character][key] = text

## Obtiene todas las líneas de un personaje
func get_character_dialogues(character: String) -> Dictionary:
	return DIALOGUE_LIBRARY.get(character, {})
