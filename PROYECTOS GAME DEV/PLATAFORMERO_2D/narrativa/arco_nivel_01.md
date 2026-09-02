# ARCO NARRATIVO — NIVEL 01: SALA DE ESPERA 001

## Información Técnica
- **Escena:** nivel_01.tscn
- **Ubicación narrativa:** Sala de Espera 001 — oficina pequeña, dos puertas, un teléfono roto
- **Spawnpoints:** player1 (4, 8), player2 (8, 8)
- **Enemigos:** 2 x GuardianFormulario (spawn en (12, 4) y (18, 6))
- **Monedas:** 5x dispersas (fichas de validación)
- **Salida:** Puerta a Archivo B-7 (posición: 22, 8)
- **Duración esperada:** 2-3 minutos (speedrun), 5-8 min (explorando)

---

## DIAGRAMA DE FLUJO NARRATIVO

```
game_start
    ↓
primer_movimiento (Iris)
    ↓
thanatos_aparece (secuencia de 3 líneas)
    ↓ [rama: si enemigo visto]
    ↓ [rama: si checkpoint próximo]
primer_enemigo_muerto
    ↓
primer_checkpoint / primer_muerte
    ↓ [si muerte = muerte_3_veces]
    ↓
moneda_recogida (x5)
    ↓
power_up_recogido [OPCIONAL]
    ↓
mitad_nivel (Thanatos con formularios)
    ↓
previo_salida (Iris menciona Expediente)
    ↓
salida_alcanzada (Thanatos procesa salida)
    [FIN NIVEL]
```

---

## TRIGGERS DETALLADOS (CON CÓDIGO GDSCRIPT)

### TRIGGER 1: game_start
**Evento:** El jugador puede moverse por primera vez  
**Condición:** 0.5 segundos después de cargar la escena  
**Ejecución:** `_on_level_loaded()` en el script principal del nivel

```gdscript
# En nivel_01.gd (Autoload o Manager del nivel)
func _ready() -> void:
    await get_tree().process_frame
    await get_tree().create_timer(0.5).timeout
    SignalBus.level_started.emit("nivel_01")
    DialogueTriggers.disparar("game_start", "nivel_01")

# En DialogueTriggers.gd
"game_start": {
    "locutores": ["narrador"],
    "dialogos": [
        {
            "personaje": "narrador",
            "texto": "Despierto. No recuerdo cómo llegué aquí.",
            "duracion": 3.0,
            "tipo": "pantalla"  # texto en el centro de la pantalla
        },
        {
            "personaje": "narrador",
            "texto": "La sala de espera. Un fluorescente parpadea.",
            "duracion": 2.5,
            "tipo": "pantalla"
        },
        {
            "personaje": "narrador",
            "texto": "Un teléfono suena. Nadie lo atiende.",
            "duracion": 2.0,
            "tipo": "pantalla"
        }
    ]
}
```

**Entrada en DialogueManager:**
```gdscript
func mostrar_dialogo(config: Dictionary) -> void:
    for dialogo in config["dialogos"]:
        var label := Label.new()
        label.text = dialogo["texto"]
        # Centrado en pantalla, font mediano
        add_child(label)
        await get_tree().create_timer(dialogo["duracion"]).timeout
        label.queue_free()
```

---

### TRIGGER 2: primer_movimiento
**Evento:** El jugador presiona una tecla de movimiento (W/A/D/SPACE o dirección)  
**Condición:** Cualquier input de movimiento del Player  
**Conexión código:**

```gdscript
# En Player.gd o InputHandler.gd
func _input(event: InputEvent) -> void:
    if event.is_action_pressed("move_left") or event.is_action_pressed("move_right") or event.is_action_pressed("jump"):
        if not _has_moved_first_time:
            _has_moved_first_time = true
            SignalBus.player_first_input.emit(player_id)
            DialogueTriggers.disparar("primer_movimiento", "nivel_01")

# En DialogueTriggers.gd
"primer_movimiento": {
    "locutores": ["iris"],
    "dialogos": [
        {
            "personaje": "iris",
            "texto": "Oh, así que sí estás vivo.",
            "duracion": 2.0,
            "tipo": "dialogo",  # en esquina inferior, con nombre
            "tono": "sarcasmo"
        }
    ]
}
```

---

### TRIGGER 3: thanatos_aparece
**Evento:** El jugador avanza a 40% del nivel (posición X > 12)  
**Condición:** Player.global_position.x > 12  
**Ejecución:**

```gdscript
# En nivel_01.gd
func _process(delta: float) -> void:
    var player = get_tree().get_first_node_in_group("player")
    if player and player.global_position.x > 12 and not _thanatos_appeared:
        _thanatos_appeared = true
        DialogueTriggers.disparar("thanatos_aparece", "nivel_01")

# En DialogueTriggers.gd
"thanatos_aparece": {
    "secuencia": true,  # Diálogos alternados
    "dialogos": [
        {
            "personaje": "thanatos",
            "texto": "Entidad detectada en zona de espera restringida.",
            "duracion": 2.5,
            "tipo": "dialogo",
            "sfx": "papel_rustling"
        },
        {
            "personaje": "iris",
            "texto": "Oh, no. Thanatos. ¿Qué te trae a pasear?",
            "duracion": 2.0,
            "tipo": "dialogo",
            "sfx": "suspiro"
        },
        {
            "personaje": "thanatos",
            "texto": "La excepcionalidad. Debe ser procesada. Eso es lo que hago.",
            "duracion": 2.5,
            "tipo": "dialogo",
            "sfx": "papel_rustling"
        }
    ]
}
```

---

### TRIGGER 4: primer_enemigo_muerto
**Evento:** El jugador destruye el primer GuardianFormulario  
**Condición:** Cuando `enemy_count` en el nivel baja de 2 a 1  
**Ejecución:**

```gdscript
# En Enemy.gd (en _die())
func _die() -> void:
    SignalBus.enemy_died.emit(id, global_position)
    if level_name == "nivel_01" and enemy_count >= 2:
        DialogueTriggers.disparar("primer_enemigo_muerto", "nivel_01")
    queue_free()

# En DialogueTriggers.gd
"primer_enemigo_muerto": {
    "locutores": ["thanatos"],
    "dialogos": [
        {
            "personaje": "thanatos",
            "texto": "Defensa neutralizada. Proceder con expediente.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "sfx": "firma_sello"
        }
    ]
}
```

---

### TRIGGER 5: primer_checkpoint
**Evento:** El jugador alcanza el primer checkpoint  
**Condición:** Player entra en área CollisionArea2D de checkpoint_1  
**Ejecución:**

```gdscript
# En Checkpoint.gd
func _on_body_entered(body: Node2D) -> void:
    if body.is_in_group("player"):
        save_position = body.global_position
        is_active = true
        if not _triggered_before:
            _triggered_before = true
            if level_name == "nivel_01":
                DialogueTriggers.disparar("primer_checkpoint", "nivel_01")
        body.respawn_point = save_position

# En DialogueTriggers.gd
"primer_checkpoint": {
    "secuencia": true,
    "dialogos": [
        {
            "personaje": "thanatos",
            "texto": "Punto de restauración registrado. Expediente asegurado.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "sfx": "sello_stamp"
        },
        {
            "personaje": "iris",
            "texto": "Por si acaso mueres de nuevo. Que morirás.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "tono": "pesimismo_cansado"
        }
    ]
}
```

---

### TRIGGER 6: primer_muerte
**Evento:** El jugador muere por primera vez  
**Condición:** `player.health <= 0` o contacto con hazard  
**Ejecución:**

```gdscript
# En Player.gd
func _on_death() -> void:
    health = 0
    SignalBus.player_died.emit(player_id)
    if death_count == 1 and level_name == "nivel_01":
        DialogueTriggers.disparar("primer_muerte", "nivel_01")
    respawn()

# En DialogueTriggers.gd
"primer_muerte": {
    "secuencia": true,
    "dialogos": [
        {
            "personaje": "thanatos",
            "texto": "Muerte registrada. Causa: fallo del usuario.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "sfx": "error_beep"
        },
        {
            "personaje": "thanatos",
            "texto": "Restaurando desde checkpoint. Esto es normal.",
            "duracion": 2.0,
            "tipo": "dialogo"
        },
        {
            "personaje": "iris",
            "texto": "Bienvenido al verdadero juego del Registro.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "tono": "oscuro"
        }
    ]
}
```

---

### TRIGGER 7: muerte_3_veces
**Evento:** El jugador muere exactamente 3 veces  
**Condición:** `death_count == 3` en nivel_01  
**Ejecución:**

```gdscript
# En Player.gd
func _on_death() -> void:
    death_count += 1
    AchievementManager.increment_stat("deaths_nivel_01")
    
    if death_count == 3 and level_name == "nivel_01":
        DialogueTriggers.disparar("muerte_3_veces", "nivel_01")

# En DialogueTriggers.gd
"muerte_3_veces": {
    "locutores": ["iris"],
    "dialogos": [
        {
            "personaje": "iris",
            "texto": "Tres veces. ¿Lo notas? El Sistema se cansa.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "tono": "genuina_preocupacion_oculta"
        },
        {
            "personaje": "iris",
            "texto": "Continúa. Pero ten cuidado.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "tono": "advertencia"
        }
    ]
}
```

---

### TRIGGER 8: moneda_recogida
**Evento:** El jugador recoge la primera ficha de validación  
**Condición:** Primer pickup de moneda  
**Ejecución:**

```gdscript
# En Coin.gd (o Pickup.gd)
func _on_collected(player: Node2D) -> void:
    player.add_coin()
    if coin_count_collected == 1:
        DialogueTriggers.disparar("moneda_recogida", "nivel_01")
    queue_free()

# En DialogueTriggers.gd
"moneda_recogida": {
    "locutores": ["iris"],
    "dialogos": [
        {
            "personaje": "iris",
            "texto": "Fichas de validación. Prueba de que exististe.",
            "duracion": 2.0,
            "tipo": "dialogo"
        },
        {
            "personaje": "iris",
            "texto": "Guárdalas. El Sistema las cuenta.",
            "duracion": 2.0,
            "tipo": "dialogo"
        }
    ]
}
```

---

### TRIGGER 9: power_up_recogido (OPCIONAL)
**Evento:** El jugador obtiene un power-up (solo si existe en el nivel)  
**Condición:** Recoger ítem especial  
**Ejecución:**

```gdscript
# En PowerUp.gd
func _on_collected(player: Node2D) -> void:
    player.apply_powerup(powerup_type)
    DialogueTriggers.disparar("power_up_recogido", "nivel_01")
    queue_free()

# En DialogueTriggers.gd
"power_up_recogido": {
    "locutores": ["iris"],
    "dialogos": [
        {
            "personaje": "iris",
            "texto": "Eso no debería estar ahí.",
            "duracion": 1.5,
            "tipo": "dialogo"
        },
        {
            "personaje": "iris",
            "texto": "Yo no hice eso.",
            "duracion": 1.5,
            "tipo": "dialogo"
        },
        {
            "personaje": "iris",
            "texto": "Define 'yo'.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "tono": "confundida"
        }
    ]
}
```

---

### TRIGGER 10: mitad_nivel
**Evento:** El jugador llega a la mitad del mapa (50% X)  
**Condición:** `player.global_position.x > 15`  
**Ejecución:**

```gdscript
# En nivel_01.gd
func _process(delta: float) -> void:
    if player.global_position.x > 15 and not _halfway_point:
        _halfway_point = true
        DialogueTriggers.disparar("mitad_nivel", "nivel_01")

# En DialogueTriggers.gd
"mitad_nivel": {
    "locutores": ["thanatos"],
    "dialogos": [
        {
            "personaje": "thanatos",
            "texto": "Progresión excepcional. Expediente actualizado.",
            "duracion": 2.0,
            "tipo": "dialogo"
        },
        {
            "personaje": "thanatos",
            "texto": "Se requieren formularios adicionales de clasificación.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "sfx": "papel_cayendo"
        }
    ]
}
```

---

### TRIGGER 11: previo_salida
**Evento:** El jugador está a 3 tiles de la salida  
**Condición:** `player.global_position.distance_to(exit_position) < 6`  
**Ejecución:**

```gdscript
# En nivel_01.gd
func _process(delta: float) -> void:
    if player.global_position.distance_to(exit_pos) < 6 and not _exit_imminent:
        _exit_imminent = true
        DialogueTriggers.disparar("previo_salida", "nivel_01")

# En DialogueTriggers.gd
"previo_salida": {
    "locutores": ["iris"],
    "dialogos": [
        {
            "personaje": "iris",
            "texto": "Espera. Hay algo que debes saber.",
            "duracion": 2.0,
            "tipo": "dialogo"
        },
        {
            "personaje": "iris",
            "texto": "Existe un archivo. El Expediente Supremo.",
            "duracion": 2.0,
            "tipo": "dialogo"
        },
        {
            "personaje": "iris",
            "texto": "Algunos dicen que puede deshacer cualquier muerte.",
            "duracion": 2.0,
            "tipo": "dialogo"
        },
        {
            "personaje": "iris",
            "texto": "Si lo encuentras... quizás todo tenga sentido.",
            "duracion": 2.5,
            "tipo": "dialogo",
            "tono": "esperanza_rota"
        }
    ]
}
```

---

### TRIGGER 12: salida_alcanzada
**Evento:** El jugador entra en el área de salida  
**Condición:** Player colisiona con trigger de puerta  
**Ejecución:**

```gdscript
# En Exit.gd (o Puerta.gd)
func _on_entered(body: Node2D) -> void:
    if body.is_in_group("player"):
        DialogueTriggers.disparar("salida_alcanzada", "nivel_01")
        # Esperar diálogo antes de transicionar
        await get_tree().create_timer(3.0).timeout
        LevelManager.go_to_level("res://niveles/nivel_02.tscn")

# En DialogueTriggers.gd
"salida_alcanzada": {
    "locutores": ["thanatos"],
    "dialogos": [
        {
            "personaje": "thanatos",
            "texto": "Expediente 4,892 en tránsito a Archivo B-7.",
            "duracion": 2.0,
            "tipo": "dialogo"
        },
        {
            "personaje": "thanatos",
            "texto": "Clasificación: Irregular.",
            "duracion": 1.5,
            "tipo": "dialogo"
        },
        {
            "personaje": "thanatos",
            "texto": "Pero procesable.",
            "duracion": 2.0,
            "tipo": "dialogo",
            "sfx": "sello_stamp_final"
        }
    ]
}
```

---

## NOTAS DE IMPLEMENTACIÓN

### Sincronización Audio
- Cada `sfx` debe conectarse a `AudioManager.play_sfx(sfx_name)`
- Los SFX de este nivel: `papel_rustling`, `suspiro`, `firma_sello`, `sello_stamp`, `error_beep`, `papel_cayendo`, `sello_stamp_final`

### Sincronización Visual
- Los diálogos en "pantalla" deben estar centrados, con transición de fade in/out
- Los diálogos de "dialogo" deben aparecer en esquina inferior izquierda con nombre del personaje

### Condiciones de Fallo (No triggers)
- Si el jugador muere más de 5 veces en nivel 01, se desbloquea el logro secreto `burocracia_total` (pero solo si muere EXACTAMENTE 7)
- Si el jugador usa un arma en co-op sincronizadamente, se desbloquea `on_beat`

---

**Fin del Arco de Nivel 01**
