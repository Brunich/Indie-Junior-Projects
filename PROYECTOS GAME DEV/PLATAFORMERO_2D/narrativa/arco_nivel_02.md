# ARCO NARRATIVO — NIVEL 02: ARCHIVO GENERAL B-7

## Información Técnica
- **Escena:** nivel_02.tscn
- **Ubicación narrativa:** Archivo General B-7 — plataformas flotantes de expedientes, pilas de archivos apilados infinitamente
- **Spawnpoints:** player1 (4, 16), player2 (8, 16)
- **Plataformas:** 12 x basadas en expedientes (posiciones variables)
- **Enemigos:** 3 x Archivador (spawn en puntos estratégicos)
- **Boss:** El Archivador Primario (aparece en mitad_nivel)
- **Monedas:** 8x dispersas (más que nivel 01)
- **Salida:** Puerta a Depósitos D-12 (posición: 24, 4)
- **Duración esperada:** 4-6 minutos (normal), 8-12 min (explorando y muriendo)

---

## DIAGRAMA DE FLUJO NARRATIVO

```
entrada_nivel
    ↓
primera_plataforma (narrador: "Las plataformas son expedientes...")
    ↓
thanatos_reaparece (Thanatos: info nueva sobre sí mismo)
    ↓ [rama: si zona_trampa próxima]
    ↓ [rama: si muere antes del boss]
zona_trampa (Iris: momento genuino de afecto)
    ↓
boss_encontrado (El Archivador: presentación intimidante)
    ↓
[BOSS FIGHT]
    ↓
boss_derrotado (Iris: "Te he visto antes. En el expediente.")
    ↓
nivel_completado (Thanatos hace algo inesperado)
    [FIN NIVEL]
```

---

## TRIGGERS DETALLADOS (CON CÓDIGO GDSCRIPT)

### TRIGGER 1: entrada_nivel
**Evento:** El nivel 02 carga completamente  
**Condición:** 0.5 segundos después de cargar la escena  
**Ejecución:**

```gdscript
# En nivel_02.gd
func _ready() -> void:
    await get_tree().process_frame
    await get_tree().create_timer(0.5).timeout
    SignalBus.level_started.emit("nivel_02")
    DialogueTriggers.disparar("entrada_nivel", "nivel_02")

# En DialogueTriggers.gd
"entrada_nivel": {
    "locutores": ["iris"],
    "dialogos": [
        {
            "personaje": "iris",
            "texto": "¿Recuerdas la sala de espera?",
            "duracion": 1.5,
            "tipo": "dialogo",
            "tono": "sarcasmo"
        },
        {
            "personaje": "iris",
            "texto": "Esto es 400% peor.",
            "duracion": 1.5,
            "tipo": "dialogo"
        },
        {
            "personaje": "iris",
            "texto": "Bienvenido al archivo.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "tono": "oscuro"
        }
    ]
}
```

---

### TRIGGER 2: primera_plataforma
**Evento:** El jugador salta a la primera plataforma estable  
**Condición:** Player entra en CollisionArea2D de plataforma_01  
**Ejecución:**

```gdscript
# En Plataforma.gd (o directamente en nivel_02.gd)
func _on_first_platform_entered() -> void:
    if not _first_platform_triggered:
        _first_platform_triggered = true
        DialogueTriggers.disparar("primera_plataforma", "nivel_02")

# En DialogueTriggers.gd
"primera_plataforma": {
    "locutores": ["narrador"],
    "dialogos": [
        {
            "personaje": "narrador",
            "texto": "Las plataformas son expedientes.",
            "duracion": 2.0,
            "tipo": "pantalla",
            "efecto": "fade"
        },
        {
            "personaje": "narrador",
            "texto": "Millones de vidas apiladas.",
            "duracion": 2.0,
            "tipo": "pantalla"
        },
        {
            "personaje": "narrador",
            "texto": "Caminamos sobre los muertos.",
            "duracion": 2.5,
            "tipo": "pantalla",
            "tono": "pesado"
        }
    ]
}
```

---

### TRIGGER 3: thanatos_reaparece
**Evento:** El jugador avanza a 30% del nivel  
**Condición:** `player.global_position.x > 8` o `player.global_position.y < 12`  
**Ejecución:**

```gdscript
# En nivel_02.gd
func _process(delta: float) -> void:
    var player = get_tree().get_first_node_in_group("player")
    if player and not _thanatos_reappeared:
        if player.global_position.x > 8 or player.global_position.y < 12:
            _thanatos_reappeared = true
            DialogueTriggers.disparar("thanatos_reaparece", "nivel_02")

# En DialogueTriggers.gd
"thanatos_reaparece": {
    "secuencia": true,
    "dialogos": [
        {
            "personaje": "thanatos",
            "texto": "Has llegado más lejos de lo esperado.",
            "duracion": 2.0,
            "tipo": "dialogo"
        },
        {
            "personaje": "thanatos",
            "texto": "Quizás debería contarte un secreto.",
            "duracion": 2.0,
            "tipo": "dialogo"
        },
        {
            "personaje": "thanatos",
            "texto": "Yo también fui procesado una vez. Hace mucho.",
            "duracion": 2.5,
            "tipo": "dialogo",
            "tono": "nostálgico_vencido"
        },
        {
            "personaje": "thanatos",
            "texto": "Acepté un puesto. Cualquier cosa para no morir de nuevo.",
            "duracion": 2.5,
            "tipo": "dialogo"
        },
        {
            "personaje": "thanatos",
            "texto": "Ahora solo obedezco. ¿Cuándo fue la última vez que tuve una opción?",
            "duracion": 3.0,
            "tipo": "dialogo",
            "tono": "quebrado"
        }
    ]
}
```

---

### TRIGGER 4: zona_trampa
**Evento:** El jugador entra en un área con trampa o hazard especial  
**Condición:** Player entra en CollisionArea2D de "trampa_01"  
**Ejecución:**

```gdscript
# En zona_trampa (Area2D especial)
func _on_entered(body: Node2D) -> void:
    if body.is_in_group("player"):
        DialogueTriggers.disparar("zona_trampa", "nivel_02")

# En DialogueTriggers.gd
"zona_trampa": {
    "locutores": ["iris"],
    "dialogos": [
        {
            "personaje": "iris",
            "texto": "Cuidado aquí.",
            "duracion": 1.0,
            "tipo": "dialogo"
        },
        {
            "personaje": "iris",
            "texto": "Yo misma casi caigo, hace 500 años.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "tono": "vulnerabilidad"
        },
        {
            "personaje": "iris",
            "texto": "No quiero que caigas.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "tono": "genuina",
            "efecto": "glitch_brevísimo"
        },
        {
            "personaje": "iris",
            "texto": "Digo... para que no tengas que reintentar tanto.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "tono": "cínismo_defensivo"
        }
    ]
}
```

---

### TRIGGER 5: boss_encontrado
**Evento:** El jugador detecta la presencia del Archivador Primario  
**Condición:** El enemigo boss aparece en pantalla o a distancia < 10 tiles  
**Ejecución:**

```gdscript
# En ArchivadorPrimario.gd (boss)
func _ready() -> void:
    super._ready()
    # No disparar el trigger aquí, hacerlo cuando se haga visible

func _process(delta: float) -> void:
    var player = get_tree().get_first_node_in_group("player")
    if player and global_position.distance_to(player.global_position) < 10 and not _dialogue_played:
        _dialogue_played = true
        DialogueTriggers.disparar("boss_encontrado", "nivel_02")
        # Detener movimiento del boss durante el diálogo
        paused = true
        await get_tree().create_timer(8.0).timeout  # duracion total diálogos
        paused = false

# En DialogueTriggers.gd
"boss_encontrado": {
    "secuencia": true,
    "dialogos": [
        {
            "personaje": "narrador",
            "texto": "El Archivador Primario.",
            "duracion": 1.5,
            "tipo": "pantalla",
            "efecto": "shake"
        },
        {
            "personaje": "narrador",
            "texto": "Verifica cada expediente. Rechaza los inválidos.",
            "duracion": 2.0,
            "tipo": "pantalla"
        },
        {
            "personaje": "iris",
            "texto": "No puedes pasar sin su aprobación.",
            "duracion": 2.0,
            "tipo": "dialogo"
        },
        {
            "personaje": "iris",
            "texto": "Pero te daré un secreto: él también duda.",
            "duracion": 2.5,
            "tipo": "dialogo",
            "tono": "conspiración"
        }
    ]
}
```

---

### TRIGGER 6: boss_derrotado
**Evento:** El Archivador Primario es destruido  
**Condición:** `boss.health <= 0`  
**Ejecución:**

```gdscript
# En ArchivadorPrimario.gd
func _on_death() -> void:
    # Efecto visual y de audio
    display_particles()
    SignalBus.enemy_died.emit(id, global_position)
    DialogueTriggers.disparar("boss_derrotado", "nivel_02")
    # Esperar antes de desparecer
    await get_tree().create_timer(5.0).timeout
    queue_free()

# En DialogueTriggers.gd
"boss_derrotado": {
    "secuencia": true,
    "dialogos": [
        {
            "personaje": "iris",
            "texto": "Lo hiciste.",
            "duracion": 1.5,
            "tipo": "dialogo",
            "tono": "sorpresa"
        },
        {
            "personaje": "iris",
            "texto": "He visto tu expediente.",
            "duracion": 1.5,
            "tipo": "dialogo"
        },
        {
            "personaje": "iris",
            "texto": "Hace 500 años.",
            "duracion": 1.5,
            "tipo": "dialogo"
        },
        {
            "personaje": "iris",
            "texto": "Tu nombre fue... olvidado.",
            "duracion": 2.5,
            "tipo": "dialogo",
            "tono": "dolor_contenido",
            "efecto": "glitch"
        },
        {
            "personaje": "iris",
            "texto": "Pero yo lo recuerdo.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "tono": "verdad"
        }
    ]
}
```

---

### TRIGGER 7: nivel_completado
**Evento:** El jugador alcanza la salida del nivel  
**Condición:** Player entra en CollisionArea2D de exit_02  
**Ejecución:**

```gdscript
# En Exit.gd (o puerta nivel 2)
func _on_entered(body: Node2D) -> void:
    if body.is_in_group("player"):
        DialogueTriggers.disparar("nivel_completado", "nivel_02")
        await get_tree().create_timer(4.0).timeout
        LevelManager.go_to_level("res://niveles/nivel_03.tscn")

# En DialogueTriggers.gd
"nivel_completado": {
    "secuencia": true,
    "dialogos": [
        {
            "personaje": "thanatos",
            "texto": "Has llegado al final.",
            "duracion": 2.0,
            "tipo": "dialogo"
        },
        {
            "personaje": "thanatos",
            "texto": "Después de milenios de servicio, he tomado una decisión.",
            "duracion": 2.5,
            "tipo": "dialogo",
            "tono": "resolución"
        },
        {
            "personaje": "thanatos",
            "texto": "No voy a detenerte.",
            "duracion": 2.0,
            "tipo": "dialogo"
        },
        {
            "personaje": "thanatos",
            "texto": "Que alguien elija, aunque sea una vez.",
            "duracion": 2.5,
            "tipo": "dialogo",
            "tono": "rebelde"
        }
    ]
}
```

---

## NOTAS SOBRE MECÁNICAS DE NIVEL 02

### Plataformas Especiales
- **Plataformas normales:** Sólidas, sin eventos
- **Plataformas inestables:** Se derrumban después de 2 segundos (se regeneran)
- **Plataformas trampa:** Hacen daño al tocar (claramente marcadas visualmente)
- **Plataformas secretas:** Solo aparecen si tienes todas las monedas (visual hint)

### Enemigos Archivadores
- 3 x Archivador estándar (movimiento patrulla simple)
- 1 x Archivador Primario (boss — más fuerte, patrones complejos)
- Boss usa ataques que citan tus "errores": "Expediente incompleto", "Clasificación inválida", etc.

### Sincronización de Audio/Visual
- SFX para este nivel: `plataforma_derrumba`, `archivador_paso`, `boss_roar`, `expediente_glitch`, `boss_derrota`
- Efectos visuales: particulas cuando plataforma cae, glitch cuando boss ataca, fade cuando se completa

---

## LOGROS ESPECÍFICOS DE NIVEL 02

- **sin_excepciones:** Completar nivel sin morir (no applicable here, muy difícil)
- **procesamiento_eficiente:** Completar en menos de 4 minutos
- **boss_en_primer_intento:** Derrotar al Archivador Primario sin morir en el encuentro

---

**Fin del Arco de Nivel 02**
