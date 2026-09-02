## DialogueTriggers.gd
## Autoload — Gestiona todos los triggers narrativos del juego
## Se conecta con DialogueManager para mostrar los diálogos
extends Node

## Diccionario maestro de todos los triggers
var _triggers: Dictionary = {
    # ===== NIVEL 01 =====
    "game_start": {
        "level": "nivel_01",
        "secuencia": false,
        "dialogos": [
            {
                "personaje": "narrador",
                "texto": "Despierto. No recuerdo cómo llegué aquí.",
                "duracion": 3.0,
                "tipo": "pantalla"
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
    },

    "primer_movimiento": {
        "level": "nivel_01",
        "secuencia": false,
        "dialogos": [
            {
                "personaje": "iris",
                "texto": "Oh, así que sí estás vivo.",
                "duracion": 2.0,
                "tipo": "dialogo",
                "tono": "sarcasmo",
                "sfx": "iris_habla"
            }
        ]
    },

    "thanatos_aparece": {
        "level": "nivel_01",
        "secuencia": true,
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
                "tono": "sarcasmo"
            },
            {
                "personaje": "thanatos",
                "texto": "La excepcionalidad. Debe ser procesada. Eso es lo que hago.",
                "duracion": 2.5,
                "tipo": "dialogo",
                "sfx": "papel_rustling"
            }
        ]
    },

    "primer_enemigo_muerto": {
        "level": "nivel_01",
        "secuencia": false,
        "dialogos": [
            {
                "personaje": "thanatos",
                "texto": "Defensa neutralizada. Proceder con expediente.",
                "duracion": 2.0,
                "tipo": "dialogo",
                "sfx": "firma_sello"
            }
        ]
    },

    "primer_checkpoint": {
        "level": "nivel_01",
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
                "tono": "pesimismo"
            }
        ]
    },

    "primer_muerte": {
        "level": "nivel_01",
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
    },

    "muerte_3_veces": {
        "level": "nivel_01",
        "secuencia": false,
        "dialogos": [
            {
                "personaje": "iris",
                "texto": "Tres veces. ¿Lo notas? El Sistema se cansa.",
                "duracion": 2.0,
                "tipo": "dialogo",
                "tono": "preocupacion"
            },
            {
                "personaje": "iris",
                "texto": "Continúa. Pero ten cuidado.",
                "duracion": 2.0,
                "tipo": "dialogo",
                "tono": "advertencia"
            }
        ]
    },

    "moneda_recogida": {
        "level": "nivel_01",
        "secuencia": false,
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
    },

    "power_up_recogido": {
        "level": "nivel_01",
        "secuencia": false,
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
    },

    "mitad_nivel": {
        "level": "nivel_01",
        "secuencia": false,
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
    },

    "previo_salida": {
        "level": "nivel_01",
        "secuencia": false,
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
                "tono": "esperanza"
            }
        ]
    },

    "salida_alcanzada": {
        "level": "nivel_01",
        "secuencia": false,
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
    },

    # ===== NIVEL 02 =====
    "entrada_nivel": {
        "level": "nivel_02",
        "secuencia": false,
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
    },

    "primera_plataforma": {
        "level": "nivel_02",
        "secuencia": false,
        "dialogos": [
            {
                "personaje": "narrador",
                "texto": "Las plataformas son expedientes.",
                "duracion": 2.0,
                "tipo": "pantalla"
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
    },

    "thanatos_reaparece": {
        "level": "nivel_02",
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
                "tono": "nostalgico"
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
    },

    "zona_trampa": {
        "level": "nivel_02",
        "secuencia": false,
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
                "tono": "vulnerable"
            },
            {
                "personaje": "iris",
                "texto": "No quiero que caigas.",
                "duracion": 2.0,
                "tipo": "dialogo",
                "tono": "genuina"
            },
            {
                "personaje": "iris",
                "texto": "Digo... para que no tengas que reintentar tanto.",
                "duracion": 2.0,
                "tipo": "dialogo",
                "tono": "cinismo"
            }
        ]
    },

    "boss_encontrado": {
        "level": "nivel_02",
        "secuencia": true,
        "dialogos": [
            {
                "personaje": "narrador",
                "texto": "El Archivador Primario.",
                "duracion": 1.5,
                "tipo": "pantalla"
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
                "tono": "conspiracion"
            }
        ]
    },

    "boss_derrotado": {
        "level": "nivel_02",
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
                "tono": "dolor"
            },
            {
                "personaje": "iris",
                "texto": "Pero yo lo recuerdo.",
                "duracion": 2.0,
                "tipo": "dialogo",
                "tono": "verdad"
            }
        ]
    },

    "nivel_completado": {
        "level": "nivel_02",
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
                "tono": "resolucion"
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
}

## Registro de triggers ya disparados en esta sesión
var _triggered_this_session: Dictionary = {}

## Conexión con DialogueManager
var _dialogue_manager: Node = null

func _ready() -> void:
    _dialogue_manager = get_node_or_null("/root/DialogueManager")
    if not _dialogue_manager:
        push_warning("DialogueTriggers: DialogueManager no encontrado en /root/")

## Dispara un trigger por nombre y nivel
func disparar(trigger_id: String, level: String = "global") -> void:
    if not _triggers.has(trigger_id):
        push_warning("DialogueTriggers: trigger '%s' no existe en DB" % trigger_id)
        return
    
    var trigger_data = _triggers[trigger_id]
    
    # Verificar que el trigger es válido para este nivel
    if trigger_data.get("level", "") != level and trigger_data.get("level", "") != "global":
        push_warning("DialogueTriggers: trigger '%s' no es válido para nivel '%s'" % [trigger_id, level])
        return
    
    # Ejecutar diálogos en secuencia
    if trigger_data.get("secuencia", false):
        _ejecutar_secuencia(trigger_data["dialogos"])
    else:
        _ejecutar_paralelo(trigger_data["dialogos"])
    
    # Registrar que se disparó
    _triggered_this_session[trigger_id] = Time.get_unix_time_from_system()

## Ejecuta diálogos simultáneamente (para narradores o descripciones simples)
func _ejecutar_paralelo(dialogos: Array) -> void:
    for dialogo_config in dialogos:
        if _dialogue_manager:
            _dialogue_manager.mostrar_dialogo(dialogo_config)
        
        # Reproducir SFX si existe
        if dialogo_config.has("sfx"):
            var audio_manager = get_node_or_null("/root/AudioManager")
            if audio_manager:
                audio_manager.play_sfx(dialogo_config["sfx"])

## Ejecuta diálogos en secuencia (para conversaciones)
func _ejecutar_secuencia(dialogos: Array) -> void:
    for dialogo_config in dialogos:
        if _dialogue_manager:
            _dialogue_manager.mostrar_dialogo(dialogo_config)
            await get_tree().create_timer(dialogo_config.get("duracion", 2.0)).timeout
        
        # Reproducir SFX si existe
        if dialogo_config.has("sfx"):
            var audio_manager = get_node_or_null("/root/AudioManager")
            if audio_manager:
                audio_manager.play_sfx(dialogo_config["sfx"])

## Verifica si un trigger ya fue disparado en esta sesión
func fue_disparado(trigger_id: String) -> bool:
    return _triggered_this_session.has(trigger_id)

## Retorna lista de todos los triggers disponibles
func get_all_triggers() -> Array:
    return _triggers.keys()

## Retorna info de un trigger específico
func get_trigger_info(trigger_id: String) -> Dictionary:
    return _triggers.get(trigger_id, {})
