# 📖 Personajes — Plataformero 2D

## Thanatos — Antagonista
**Arquetipo**: Burócrata infernal, custodio del orden caótico

**Voz**: Habla como si redactara un informe administrativo. Cada frase parece una cita de un contrato legal. Sarcástico pero profesional.

**Manía**: Necesidad compulsiva de documentar TODO. Cada acción del jugador es un "incidente a reportar". Usa frases como "Expediente completado" y "Solicitud denegada".

### Líneas de diálogo (situacionales)

- **Al aparecer**: "Expediente abierto. Naturaleza del caso: caos humano recurrente. Prognosis: negativa."
- **Cuando el jugador muere**: "Defunción registrada. Solicitud de segunda oportunidad: procesada. Espere en la cola."
- **Cuando el jugador gana**: "Conclusión inesperada. Procedimiento standard violado. Auditoría iniciada."
- **Al recibir daño él mismo**: "Protesta formal presentada. Daño no autorizado a propiedad de la Corporación."
- **Idle largo (jugador no se mueve)**: "¿Solicitud en espera? Los trámites tardan. Mínimo 45 minutos de espera estimado."
- **Ante un power-up recolectado**: "Ventaja obtenida mediante medios irregulares. Sanción pendiente."

### Integración en código

```gdscript
const DIALOGOS_THANATOS = {
	"aparicion": "Expediente abierto. Naturaleza del caso: caos humano recurrente.",
	"player_muere": "Defunción registrada. Solicitud de segunda oportunidad: procesada.",
	"player_gana": "Conclusión inesperada. Procedimiento standard violado.",
	"recibe_daño": "Protesta formal presentada. Daño no autorizado.",
	"idle": "¿Solicitud en espera? Los trámites tardan.",
	"power_up": "Ventaja obtenida mediante medios irregulares.",
}

func say(key: String) -> void:
	GameManager.emit_dialogue("thanatos", DIALOGOS_THANATOS[key])
```

---

## Iris — Aliada/Guía
**Arquetipo**: Mercenaria sarcástica con buen corazón, veterana del caos

**Voz**: Habla con humor ácido y cinismo, pero sus consejos siempre son útiles. Rompe la cuarta pared con elegancia y sin avergonzarse.

**Manía**: No puede evitar hacer chistes sobre la situación, por grave que sea. Siempre tiene un comentario irónico listo, pero lo dice con verdadera intención de ayudar.

### Líneas de diálogo (situacionales)

- **Al aparecer**: "Otro desventurado en el purgatorio administrativo. Bienvenido. No te preocupes, Thanatos cobra por hablador, no por asesino."
- **Cuando el jugador muere**: "Ouch. Eso contó para tu historial de estrés. Pero tranquilo, aquí el 'game over' es solo un papeleo más."
- **Cuando el jugador gana**: "¡Wow! Cortaste las cintas rojas de la burocracia. Thanatos va a estar furioso. Disfruta el momento."
- **Al recibir daño ella misma**: "Eh, tranquilo paladín. Tengo seguro. Aunque rellenar el formulario es más mortal que el combate."
- **Idle largo**: "¿Se te pegó el teclado? Entiendo, Thanatos aburre a cualquiera. Pero vamos, sigue avanzando."
- **Ante un power-up**: "Ooh, equipo gratis. En la burocracia eso equivale a recibir un soborno. Me encanta."

### Integración en código

```gdscript
const DIALOGOS_IRIS = {
	"aparicion": "Otro desventurado. Bienvenido al purgatorio administrativo.",
	"player_muere": "Ouch. Eso contó para tu historial.",
	"player_gana": "¡Cortaste las cintas rojas! Thanatos estará furioso.",
	"recibe_daño": "Eh, tranquilo. Tengo seguro.",
	"idle": "¿Se te pegó el teclado? Sigue avanzando.",
	"power_up": "Equipo gratis. Equivalente a un soborno burocrático.",
	"ambiente": "Sabes, en todos mis años aquí, nadie como tú ha llegado tan lejos.",
}

func say(key: String) -> void:
	GameManager.emit_dialogue("iris", DIALOGOS_IRIS[key])
```

---

## Arquitectura Narrativa en Código

El sistema funciona así:

1. **GameManager emite señales** cuando ocurren eventos (muerte, victoria, daño)
2. **DialogueManager escucha y traduce** a llamadas de diálogo
3. **Los personajes responden** con sus líneas asociadas
4. **El HUD muestra** el texto en un panel deslizante

Ejemplo de flujo:
```gdscript
# En player_state_machine.gd
func die() -> void:
	state = State.DEAD
	GameManager.player_died.emit(self)

# En GameManager.gd (conectado en _ready)
func _on_player_died(player: Node) -> void:
	if randf() < 0.7:
		DialogueManager.say("thanatos", "player_muere")
	else:
		DialogueManager.say("iris", "player_muere")
```

---

## 💬 Diálogos de Gameplay — Thanatos

### Situacionales in-game
- **Combo ×5 kills**: "Cinco expedientes procesados. Eficiencia inusual. Anotado."
- **Player cae al vacío**: "Causa de muerte: exceso de optimismo vertical. Clásico."
- **Player recoge power-up**: "Eso no estaba en el formulario de términos y condiciones."
- **Player intenta pausa**: "No existe pausa en el papeleo del inframundo."
- **Nivel completado**: "Corrección: el expediente continúa. Anexo B, cláusula 7."
- **Primer game over**: "Primera vez. No se preocupe. Tenemos formularios para esto."
- **Game over repetido**: "Formulario de re-muerte. Ya viene prellenado con su nombre."
- **Boss fight inicio**: "Evaluación final. Sin apelaciones disponibles esta vez."

## 💬 Diálogos de Gameplay — Iris

### Situacionales in-game
- **Inicio del nivel**: "Otro día, otro dungeon genérico. Al menos las físicas funcionan."
- **Player tarda demasiado**: "¿Sabes que el juego no se pausa si te quedas quieto, verdad?"
- **Player muere 3+ veces seguidas**: "Oye, ¿quieres que te explique los controles? No te juzgo. Sí te juzgo."
- **Encuentra ruta secreta**: "Mira eso. Un secreto. Como si no te lo quisieran poner fácil. Oh, espera."
- **Derrota al boss**: "Lo lograste. Nadie apostaba por ti. Bueno, yo sí. Pero en contra."
- **Consigue todas las monedas**: "Completista. Interesante forma de evitar los problemas reales."
- **Modo co-op activado**: "¿Trajiste a alguien? Bien. Más testigos para mis comentarios."
