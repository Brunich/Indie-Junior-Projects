## achievements_db.gd
## Database de todos los logros del juego
## Exportar DATA en _ready() o como constante

extends Node

const DATA: Dictionary = {
    # ===== HISTORIA (5 logros) =====
    "primera_excepcion": {
        "nombre": "Primera Excepción",
        "descripcion": "Completa el Nivel 1: Sala de Espera",
        "descripcion_secreta": "El viaje comienza con un paso",
        "icono": "📋",
        "categoria": "historia",
        "secreto": false,
        "puntos": 10,
        "recompensa": {"tipo": "none"},
        "frase_unlock": {
            "thanatos": "Expediente catalogado.",
            "iris": "Bienvenido al archivo."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "level_completed",
            "nivel": "nivel_01"
        }
    },

    "formulario_rechazado": {
        "nombre": "Formulario Rechazado",
        "descripcion": "Completa el Nivel 2: Archivo General B-7",
        "descripcion_secreta": "El Archivador cae, pero el Sistema permanece",
        "icono": "📄",
        "categoria": "historia",
        "secreto": false,
        "puntos": 15,
        "recompensa": {"tipo": "none"},
        "frase_unlock": {
            "iris": "Lo hiciste. De verdad lo hiciste.",
            "thanatos": "He tomado una decisión."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "level_completed",
            "nivel": "nivel_02"
        }
    },

    "apelacion_denegada": {
        "nombre": "Apelación Denegada",
        "descripcion": "Completa el Nivel 3: Depósitos Remotos",
        "descripcion_secreta": "El Sistema se fisura",
        "icono": "🚫",
        "categoria": "historia",
        "secreto": false,
        "puntos": 20,
        "recompensa": {"tipo": "none"},
        "frase_unlock": {
            "iris": "Casi estamos ahí.",
            "thanatos": "La libertad es un concepto ilegal."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "level_completed",
            "nivel": "nivel_03"
        }
    },

    "error_en_el_sistema": {
        "nombre": "Error en el Sistema",
        "descripcion": "Completa el Acto 3 y descubre la verdad sobre Thanatos",
        "descripcion_secreta": "Un milenio de obediencia termina",
        "icono": "⚡",
        "categoria": "historia",
        "secreto": false,
        "puntos": 25,
        "recompensa": {"tipo": "none"},
        "frase_unlock": {
            "thanatos": "Por primera vez, elijo.",
            "iris": "Lo sabía. Siempre lo supe."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "thanatos_redemption",
            "nivel": "global"
        }
    },

    "expediente_incompleto": {
        "nombre": "Expediente Incompleto",
        "descripcion": "Alcanza el final del juego",
        "descripcion_secreta": "La verdad que cambia todo",
        "icono": "📑",
        "categoria": "historia",
        "secreto": false,
        "puntos": 50,
        "recompensa": {"tipo": "none"},
        "frase_unlock": {
            "iris": "Eres el Expediente. Siempre lo fuiste.",
            "sistema": "ANOMALÍA CRÍTICA."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "game_ending",
            "nivel": "global"
        }
    },

    # ===== HABILIDAD (5 logros) =====
    "procesamiento_eficiente": {
        "nombre": "Procesamiento Eficiente",
        "descripcion": "Completa Nivel 1 en menos de 90 segundos",
        "descripcion_secreta": "La velocidad es su propia forma de resistencia",
        "icono": "⚡",
        "categoria": "habilidad",
        "secreto": false,
        "puntos": 15,
        "recompensa": {"tipo": "skin", "valor": "velocidad_blur"},
        "frase_unlock": {
            "thanatos": "Expedición acelerada.",
            "iris": "Parece que tienes prisa."
        },
        "trigger": {
            "tipo": "tiempo",
            "evento": "level_completed",
            "nivel": "nivel_01",
            "valor": 90,
            "exacto": false
        }
    },

    "sin_excepciones": {
        "nombre": "Sin Excepciones",
        "descripcion": "Completa un nivel sin morir",
        "descripcion_secreta": "Perfección momentánea",
        "icono": "💎",
        "categoria": "habilidad",
        "secreto": false,
        "puntos": 25,
        "recompensa": {"tipo": "cosmetic", "valor": "halo_oro"},
        "frase_unlock": {
            "thanatos": "Expediente limpio. Impresionante.",
            "iris": "¿Cómo lo hiciste?"
        },
        "trigger": {
            "tipo": "contador",
            "evento": "deaths_in_level",
            "valor": 0,
            "exacto": true
        }
    },

    "on_beat": {
        "nombre": "En el Ritmo",
        "descripcion": "Mata 10 enemigos sincronizados con el beat",
        "descripcion_secreta": "La burocracia tiene su propia música",
        "icono": "♪",
        "categoria": "habilidad",
        "secreto": false,
        "puntos": 20,
        "recompensa": {"tipo": "none"},
        "frase_unlock": {
            "iris": "¿Lo escuchas? El pulso del Sistema.",
            "thanatos": "Sincronización detectada."
        },
        "trigger": {
            "tipo": "contador",
            "evento": "on_beat_kills",
            "valor": 10,
            "exacto": false
        }
    },

    "salto_de_fe": {
        "nombre": "Salto de Fe",
        "descripcion": "Completa 3 wall jumps consecutivos",
        "descripcion_secreta": "A veces solo tienes que creer",
        "icono": "🌙",
        "categoria": "habilidad",
        "secreto": false,
        "puntos": 15,
        "recompensa": {"tipo": "none"},
        "frase_unlock": {
            "iris": "Supongo que tienes más control del que pensé.",
            "thanatos": "Salto registrado."
        },
        "trigger": {
            "tipo": "contador",
            "evento": "consecutive_wall_jumps",
            "valor": 3,
            "exacto": false
        }
    },

    "combo_burocrático": {
        "nombre": "Combo Burocrático",
        "descripcion": "Mata 5 enemigos sin recibir daño",
        "descripcion_secreta": "La venganza administrativa",
        "icono": "⚔️",
        "categoria": "habilidad",
        "secreto": false,
        "puntos": 20,
        "recompensa": {"tipo": "none"},
        "frase_unlock": {
            "thanatos": "Defensa perfecta. Anómalo.",
            "iris": "Prácticamente eres parte del Sistema ya."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "combo_achieved",
            "valor": 5
        }
    },

    # ===== SECRETOS - YAKUZA STYLE (8 logros) =====
    "burocracia_total": {
        "nombre": "Burocracia Total",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Muere exactamente 7 veces en Nivel 1",
        "icono": "☠️",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 30,
        "recompensa": {"tipo": "skin", "valor": "error_404"},
        "frase_unlock": {
            "sistema": "PATRÓN INUSUAL DETECTADO.",
            "iris": "El número 7. Siempre el 7."
        },
        "trigger": {
            "tipo": "contador",
            "evento": "deaths_nivel_01",
            "valor": 7,
            "exacto": true
        }
    },

    "formulario_404": {
        "nombre": "Formulario 404",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Encuentra el área oculta en Nivel 2",
        "icono": "🔍",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 25,
        "recompensa": {"tipo": "skin", "valor": "invisible"},
        "frase_unlock": {
            "iris": "Nunca pensé que lo encontrarías.",
            "thanatos": "Eso no debería existir."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "secret_area_found",
            "nivel": "nivel_02"
        }
    },

    "multitarea_cuantica": {
        "nombre": "Multitarea Cuántica",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "En co-op, ambos saltan exactamente al mismo tiempo",
        "icono": "↔️",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 35,
        "recompensa": {"tipo": "cosmetic", "valor": "sync_effect"},
        "frase_unlock": {
            "iris": "¿Cómo sincronizaron eso?",
            "thanatos": "Entrelazamiento cuántico registrado."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "coop_sync_jump",
            "tolerancia": 0.1
        }
    },

    "el_metodo_thanatos": {
        "nombre": "El Método Thanatos",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Completa un nivel sin disparar nunca",
        "icono": "🤐",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 40,
        "recompensa": {"tipo": "skin", "valor": "pacifista"},
        "frase_unlock": {
            "thanatos": "No usaste violencia. Interesante.",
            "iris": "¿Quién eres realmente?"
        },
        "trigger": {
            "tipo": "contador",
            "evento": "shots_fired",
            "valor": 0,
            "exacto": true,
            "nivel": "any"
        }
    },

    "existencia_cuestionable": {
        "nombre": "Existencia Cuestionable",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Permanece quieto 60 segundos sin input",
        "icono": "👤",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 20,
        "recompensa": {"tipo": "none"},
        "frase_unlock": {
            "iris": "¿Sigues ahí?",
            "sistema": "ENTIDAD EN SUSPENSIÓN."
        },
        "trigger": {
            "tipo": "tiempo",
            "evento": "idle_time",
            "valor": 60,
            "exacto": false
        }
    },

    "iris_tiene_razon": {
        "nombre": "Iris Tiene Razón",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Muere cuando faltaba 1 enemigo para ganar",
        "icono": "🎭",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 15,
        "recompensa": {"tipo": "none"},
        "frase_unlock": {
            "iris": "Te lo dije.",
            "thanatos": "Fallo por milisegundos."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "death_with_one_enemy_left",
            "nivel": "any"
        }
    },

    "protocolo_7b": {
        "nombre": "Protocolo 7B",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Easter egg oculto en Nivel 1",
        "icono": "🔐",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 50,
        "recompensa": {"tipo": "skin", "valor": "retro_16bit"},
        "frase_unlock": {
            "sistema": "CÓDIGO LEGACY EJECUTADO.",
            "iris": "¿De dónde salió eso?"
        },
        "trigger": {
            "tipo": "evento",
            "evento": "easter_egg_protocol_7b",
            "nivel": "nivel_01"
        }
    },

    "glitch_en_el_sistema": {
        "nombre": "Glitch en el Sistema",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Muere y mata a un enemigo en el mismo frame",
        "icono": "📺",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 45,
        "recompensa": {"tipo": "skin", "valor": "glitch_scanlines"},
        "frase_unlock": {
            "sistema": "INCONSISTENCIA LÓGICA DETECTADA.",
            "thanatos": "Eso es... imposible."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "simultaneous_death_and_kill",
            "tolerancia": 1
        }
    },

    # ===== CO-OP (4 logros) =====
    "companeros_de_papeleo": {
        "nombre": "Compañeros de Papeleo",
        "descripcion": "Completa un nivel en co-op",
        "descripcion_secreta": "Dos voluntarios para el Registro",
        "icono": "👥",
        "categoria": "coop",
        "secreto": false,
        "puntos": 15,
        "recompensa": {"tipo": "none"},
        "frase_unlock": {
            "iris": "Dos en lugar de uno. Doble riesgo.",
            "thanatos": "Duplicación de excepciones registrada."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "coop_level_completed",
            "players": 2
        }
    },

    "muerte_sincronizada": {
        "nombre": "Muerte Sincronizada",
        "descripcion": "En co-op, ambos mueren al mismo tiempo",
        "descripcion_secreta": "Hasta en la muerte, juntos",
        "icono": "☠️☠️",
        "categoria": "coop",
        "secreto": false,
        "puntos": 20,
        "recompensa": {"tipo": "cosmetic", "valor": "sync_particles"},
        "frase_unlock": {
            "iris": "Qué par.",
            "thanatos": "Sincronización de defunción."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "coop_simultaneous_death",
            "tolerancia": 0.5
        }
    },

    "pareja_de_hecho": {
        "nombre": "Pareja de Hecho",
        "descripcion": "Completa 3 niveles en co-op",
        "descripcion_secreta": "El Sistema no previó esto",
        "icono": "💍",
        "categoria": "coop",
        "secreto": false,
        "puntos": 30,
        "recompensa": {"tipo": "none"},
        "frase_unlock": {
            "iris": "Se están volviendo como uno solo.",
            "thanatos": "Unidad detectada."
        },
        "trigger": {
            "tipo": "contador",
            "evento": "coop_levels_completed",
            "valor": 3,
            "exacto": false
        }
    },

    "quien_necesita_al_otro": {
        "nombre": "¿Quién Necesita al Otro?",
        "descripcion": "Uno de ustedes muere 5 veces mientras el otro no muere",
        "descripcion_secreta": "Asimetría perfecta",
        "icono": "⚖️",
        "categoria": "coop",
        "secreto": false,
        "puntos": 25,
        "recompensa": {"tipo": "none"},
        "frase_unlock": {
            "iris": "Uno lleva al otro.",
            "thanatos": "Dependencia registrada."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "coop_imbalance_achievement",
            "deaths_p1": 5,
            "deaths_p2": 0
        }
    },

    # ===== COSMÉTICOS (3 logros) =====
    "arqueólogo_digital": {
        "nombre": "Arqueólogo Digital",
        "descripcion": "Encuentra todos los sprites legacy de 16x16",
        "descripcion_secreta": "El pasado pixelado del Registro",
        "icono": "🔲",
        "categoria": "cosmetico",
        "secreto": false,
        "puntos": 35,
        "recompensa": {"tipo": "skin", "valor": "retro_16bit"},
        "frase_unlock": {
            "iris": "Esos son... antiguos. Muy antiguos.",
            "sistema": "ARCHIVOS LEGACY RECUPERADOS."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "all_legacy_sprites_found",
            "cantidad": 8
        }
    },

    "aprobado_por_el_sistema": {
        "nombre": "Aprobado por el Sistema",
        "descripcion": "Desbloquea todos los logros de Historia",
        "descripcion_secreta": "El sello de la burocracia",
        "icono": "✓",
        "categoria": "cosmetico",
        "secreto": false,
        "puntos": 100,
        "recompensa": {"tipo": "hud_element", "valor": "sello_dorado"},
        "frase_unlock": {
            "sistema": "EXPEDIENTE COMPLETADO.",
            "thanatos": "Perfección registrada."
        },
        "trigger": {
            "tipo": "evento",
            "evento": "all_story_achievements",
            "logros": ["primera_excepcion", "formulario_rechazado", "apelacion_denegada", "error_en_el_sistema", "expediente_incompleto"]
        }
    },

    "error_404_skin": {
        "nombre": "Error 404: Jugador no encontrado",
        "descripcion": "Desbloquea el skin de glitch",
        "descripcion_secreta": "La interfaz se corrompe",
        "icono": "💻",
        "categoria": "cosmetico",
        "secreto": false,
        "puntos": 40,
        "recompensa": {"tipo": "skin", "valor": "error_404_glitch"},
        "frase_unlock": {
            "sistema": "ERROR DE PRESENTACIÓN.",
            "iris": "Acabas de... desaparecer?"
        },
        "trigger": {
            "tipo": "evento",
            "evento": "all_secret_achievements",
            "minimo": 5
        }
    },

    # ===== NUEVOS — 2026-03-17 (5 logros) =====

    "tramitacion_urgente": {
        "nombre": "Tramitación Urgente",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Muere en los primeros 3 segundos de un nivel, 3 veces distintas.",
        "icono": "⏱️",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 25,
        "recompensa": {"tipo": "titulo", "valor": "El Más Eficiente"},
        "frase_unlock": {
            "thanatos": "Tres muertes instantáneas. Hay cierta elegancia en esa consistencia.",
            "iris": "Espera, ¿lo estás haciendo a propósito? No. No lo creo.",
        },
        "trigger": {
            "tipo": "contador",
            "evento": "death_within_3s_of_level_start",
            "valor": 3,
            "exacto": false
        }
    },

    "consulta_previa": {
        "nombre": "Consulta Previa",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Pausa el juego 20 veces o más durante un solo nivel.",
        "icono": "⏸️",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 20,
        "recompensa": {"tipo": "titulo", "valor": "El Indeciso Oficial"},
        "frase_unlock": {
            "thanatos": "Veinte interrupciones al flujo de trabajo. Mis registros raramente llegan a tanto.",
            "iris": "¿Necesitas un momento? ¿O veinte? Al parecer, veinte.",
        },
        "trigger": {
            "tipo": "contador",
            "evento": "pauses_in_single_level",
            "valor": 20,
            "exacto": false
        }
    },

    "resolucion_definitiva": {
        "nombre": "Resolución Definitiva",
        "descripcion": "Derrota al último enemigo de un nivel con exactamente 1 de vida.",
        "descripcion_secreta": "El filo entre existir y no existir",
        "icono": "❤️",
        "categoria": "habilidad",
        "secreto": false,
        "puntos": 50,
        "recompensa": {"tipo": "cosmetic", "valor": "aura_roja_tenue"},
        "frase_unlock": {
            "thanatos": "Un punto de vida. La diferencia entre el archivo activo y el archivado.",
            "iris": "Sobreviviste por... literalmente nada. Fue impresionante. No te lo diré de nuevo.",
        },
        "trigger": {
            "tipo": "evento",
            "evento": "level_last_kill_at_one_hp",
            "nivel": "any"
        }
    },

    "circular_sin_respuesta": {
        "nombre": "Circular Sin Respuesta",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Activa la misma trampa o peligro exactamente 5 veces seguidas en un nivel, sin recibir daño de nada más entre medias.",
        "icono": "🔁",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 35,
        "recompensa": {"tipo": "skin", "valor": "bucle_infinito"},
        "frase_unlock": {
            "thanatos": "Cinco veces el mismo error. El Sistema llama a eso 'aprendizaje'. Yo lo llamo poesía.",
            "iris": "Oye. Oye. Esa trampa no va a moverse. Nunca. ¿Lo sabes?",
        },
        "trigger": {
            "tipo": "contador",
            "evento": "same_hazard_consecutive_deaths",
            "valor": 5,
            "exacto": true,
            "sin_daño_intermedio": true
        }
    },

    "manual_no_incluido": {
        "nombre": "Manual de Usuario No Incluido",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Completa el Nivel 1 sin usar el dash ni una sola vez.",
        "icono": "📵",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 40,
        "recompensa": {"tipo": "skin", "valor": "sin_rastro"},
        "frase_unlock": {
            "thanatos": "Terminaste el primer nivel sin usar el protocolo de evasión estándar. No sé si eso es valentía o ignorancia.",
            "iris": "El dash existe. Lo pusimos ahí. Fue un esfuerzo considerable. Solo digo.",
        },
        "trigger": {
            "tipo": "contador",
            "evento": "dash_used_in_level",
            "nivel": "nivel_01",
            "valor": 0,
            "exacto": true
        }
    }
    # ===== NUEVOS — 2026-03-18 (5 logros) =====
    # Inspiración: PEAK (Aggro Crab, co-op caótico), Hollow Knight: Silksong
    # (dominio del movimiento aéreo), y patrones únicos detectados en indie 2025.
    # Ideas originales extraídas del research:
    #  1. PEAK → logro de agotamiento simultáneo de recursos en co-op
    #  2. Silksong → logro de tiempo acumulado en el aire (dominio vertical)
    #  3. Indie 2025 → logro de perseverancia ciega contra el mismo peligro

    "reunion_de_emergencia": {
        "nombre": "Reunión de Emergencia",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "En co-op, ambos jugadores se quedan sin munición exactamente al mismo segundo.",
        "icono": "📭",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 40,
        "recompensa": {"tipo": "cosmetic", "valor": "modo_cero_balas"},
        "frase_unlock": {
            "thanatos": "Ambos agotaron sus recursos de forma simultánea. El Sistema llama a eso 'sinergia'. Yo lo llamo catástrofe coordinada.",
            "iris": "¿Lo planearon? ¿O fue instinto? No sé qué me preocupa más.",
        },
        "trigger": {
            "tipo": "evento",
            "evento": "coop_simultaneous_empty_ammo",
            "tolerancia": 1.0
        }
    },

    "delegacion_de_responsabilidad": {
        "nombre": "Delegación de Responsabilidad",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Muere exactamente en el mismo punto del nivel 3 veces consecutivas, sin morir en ningún otro lugar entre medias.",
        "icono": "📍",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 35,
        "recompensa": {"tipo": "titulo", "valor": "El Geógrafo del Fracaso"},
        "frase_unlock": {
            "thanatos": "Tres muertes idénticas en coordenadas idénticas. He archivado patrones de comportamiento más complejos. Este no es uno de ellos.",
            "iris": "Ese punto específico del mapa. Ese. Tres veces. ¿Puedes explicarlo? Porque yo no puedo.",
        },
        "trigger": {
            "tipo": "contador",
            "evento": "consecutive_deaths_at_same_position",
            "valor": 3,
            "exacto": true,
            "tolerancia_px": 32
        }
    },

    "hora_punta": {
        "nombre": "Hora Punta",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Acumula más de 25 segundos en el aire (saltando o cayendo) dentro de un solo nivel.",
        "icono": "🌤️",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 30,
        "recompensa": {"tipo": "cosmetic", "valor": "estela_aerea"},
        "frase_unlock": {
            "thanatos": "Pasaste más tiempo en el aire que en el suelo. Eso no tiene precedentes en los registros de eficiencia burocrática.",
            "iris": "¿Eres un pájaro? ¿Una excepción? El Sistema aún no tiene formulario para esto.",
        },
        "trigger": {
            "tipo": "tiempo",
            "evento": "airtime_in_level",
            "valor": 25,
            "exacto": false
        }
    },

    "optimizacion_del_caos": {
        "nombre": "Optimización del Caos",
        "descripcion": "Mata 3 enemigos con un solo proyectil perforante.",
        "descripcion_secreta": "La eficiencia como arte marcial",
        "icono": "🎯",
        "categoria": "habilidad",
        "secreto": false,
        "puntos": 45,
        "recompensa": {"tipo": "cosmetic", "valor": "rastro_perforante"},
        "frase_unlock": {
            "thanatos": "Un proyectil, tres expedientes cerrados. Eficiencia máxima. No esperaba menos… aunque sí lo esperaba.",
            "iris": "Eso fue ridículo. En el buen sentido. Completamente ridículo.",
        },
        "trigger": {
            "tipo": "evento",
            "evento": "piercing_multikill",
            "valor": 3,
            "exacto": false
        }
    },

    "el_informe_anual": {
        "nombre": "El Informe Anual",
        "descripcion": "Desbloquea todos los logros de Habilidad.",
        "descripcion_secreta": "El resumen de un año de dedicación sistemática",
        "icono": "📊",
        "categoria": "cosmetico",
        "secreto": false,
        "puntos": 75,
        "recompensa": {"tipo": "skin", "valor": "uniforme_auditor"},
        "frase_unlock": {
            "thanatos": "Todos los logros de habilidad completados. He actualizado tu expediente con la categoría más alta disponible. Eso es algo.",
            "iris": "¿Sabes cuántas anomalías de este calibre registro al año? Ninguna. Hasta ahora.",
        },
        "trigger": {
            "tipo": "evento",
            "evento": "all_skill_achievements",
            "logros": ["procesamiento_eficiente", "sin_excepciones", "on_beat", "salto_de_fe", "combo_burocrático", "resolucion_definitiva", "optimizacion_del_caos"]
        }
    },

    # ===== NUEVOS — 2026-03-24 (5 logros) =====
    # Inspiración: Hollow Knight: Silksong (encadenar movimiento con narrativa),
    # Clair Obscur: Expedition 33 (timing de combate + cooperación táctica),
    # PEAK (asimetría total en co-op), Blue Prince (exploración sin mapa).
    # Ideas originales:
    #  1. Silksong → logro por leer todo el diálogo (recompensa narrativa sobre mecánica)
    #  2. BeatSync extendido → partitura perfecta nivel completo (skill extremo)
    #  3. Checkpoint abuse → quedarse varado en el mismo checkpoint repitiéndolo
    #  4. Co-op asimétrico → uno mata todo, el otro no mata nada (líder/becario)
    #  5. Coleccionista de categorías → al menos 1 logro de cada tipo

    "revision_exhaustiva": {
        "nombre": "Revisión Exhaustiva",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "No saltes ninguna línea de diálogo durante un nivel entero.",
        "icono": "📖",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 25,
        "recompensa": {"tipo": "titulo", "valor": "Lector Certificado"},
        "frase_unlock": {
            "thanatos": "Leíste cada palabra. Cada línea. Yo misma escribí muchas de ellas. No esperaba que nadie llegara hasta el final. Gracias.",
            "iris": "Eso fue... un poco raro. En el buen sentido. Nadie hace eso. Oye, ¿leíste también mis partes? Sí, ¿verdad? Lo sabía.",
        },
        "trigger": {
            "tipo": "contador",
            "evento": "dialogue_lines_skipped_in_level",
            "valor": 0,
            "exacto": true,
            "nivel": "any"
        }
    },

    "partitura_perfecta": {
        "nombre": "Partitura Perfecta",
        "descripcion": "Completa un nivel matando todos los enemigos on beat (±80ms).",
        "descripcion_secreta": "El Sistema también tiene un pulso",
        "icono": "🎼",
        "categoria": "habilidad",
        "secreto": false,
        "puntos": 60,
        "recompensa": {"tipo": "cosmetic", "valor": "estela_musical"},
        "frase_unlock": {
            "thanatos": "Cada eliminación sincronizada. El ritmo del Sistema no es una metáfora para ti. Es un instrumento. Impresionante y ligeramente perturbador.",
            "iris": "Acabas de hacer el nivel entero como si fuera una coreografía. Me alegra que estés de nuestro lado.",
        },
        "trigger": {
            "tipo": "evento",
            "evento": "level_all_kills_on_beat",
            "minimo_enemigos": 8,
            "nivel": "any"
        }
    },

    "reforma_administrativa": {
        "nombre": "Reforma Administrativa",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "Activa un checkpoint y muere 5 veces seguidas desde él sin avanzar ni un metro.",
        "icono": "🔄",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 30,
        "recompensa": {"tipo": "titulo", "valor": "Experto en Procesos"},
        "frase_unlock": {
            "thanatos": "Cinco regresos al mismo punto de control. Sin progreso. Sin variación. El Sistema define eso como 'adherencia al protocolo'. Yo lo defino como rendición disfrazada de rutina.",
            "iris": "Oye. El checkpoint no va a cambiar. Tú tampoco, al parecer. ¿Necesitas que hablemos de esto?",
        },
        "trigger": {
            "tipo": "contador",
            "evento": "deaths_from_same_checkpoint",
            "valor": 5,
            "exacto": false,
            "sin_avance_minimo": 64
        }
    },

    "jefe_y_becario": {
        "nombre": "Jefe y Becario",
        "descripcion": "[SECRETO]",
        "descripcion_secreta": "En co-op, un jugador mata 10+ enemigos y el otro no mata ninguno en el mismo nivel.",
        "icono": "👔",
        "categoria": "secreto",
        "secreto": true,
        "puntos": 35,
        "recompensa": {"tipo": "cosmetic", "valor": "titulo_flotante_jefe_becario"},
        "frase_unlock": {
            "thanatos": "Distribución de tareas completamente asimétrica. Un expediente activo, uno de apoyo. El Sistema reconoce esta jerarquía. Yo la encuentro vagamente cómica.",
            "iris": "Alguien hizo todo el trabajo. El otro... existió. Y obtuvieron el mismo logro. Eso es lo más burocrático que ha pasado en este juego.",
        },
        "trigger": {
            "tipo": "evento",
            "evento": "coop_kill_asymmetry",
            "kills_p1_min": 10,
            "kills_p2_max": 0,
            "nivel": "any"
        }
    },

    "expediente_diverso": {
        "nombre": "Expediente Diverso",
        "descripcion": "Desbloquea al menos un logro de cada categoría.",
        "descripcion_secreta": "Un archivo completo, aunque incompleto",
        "icono": "🗂️",
        "categoria": "cosmetico",
        "secreto": false,
        "puntos": 50,
        "recompensa": {"tipo": "hud_element", "valor": "barra_categorias_colores"},
        "frase_unlock": {
            "thanatos": "Historia. Habilidad. Secretos. Co-op. Cosmético. Tienes al menos uno de cada departamento. El Sistema no sabe cómo clasificarte. Eso es inusual. Y correcto.",
            "iris": "Hiciste un poco de todo. No eres especialista en nada. Eso me parece perfecto. Bienvenido al club de las anomalías multifuncionales.",
        },
        "trigger": {
            "tipo": "evento",
            "evento": "one_per_category_unlocked",
            "categorias": ["historia", "habilidad", "secreto", "coop", "cosmetico"]
        }
    }
}

func _ready() -> void:
    # Validar que DATA está correctamente formado
    for achievement_id in DATA.keys():
        var achievement = DATA[achievement_id]
        if not achievement.has("nombre") or not achievement.has("categoria"):
            push_error("Achievement '%s' está mal formado" % achievement_id)
