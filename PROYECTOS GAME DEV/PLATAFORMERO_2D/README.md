# PLATAFORMERO 2D — El Registro Eterno

**Juego narrativo de plataforma ambientado en un purgatorio burocrático infinito.**

---

## 📋 Descripción General

"El Registro Eterno" es un plataformero 2D donde el jugador despierta sin recuerdos en una oficina de procesamiento administrativa que parece ser un purgatorio. A medida que avanzan a través de niveles, descubren la verdad: son el Expediente Supremo, la única alma que nunca fue registrada por el Sistema.

**Temas principales:** Identidad, libertad, burocracia como antagonista, memoria, resistencia.

---

## 🎮 Características Principales

- **Narrativa ramificada:** Finales múltiples según las elecciones del jugador
- **Sistema de logros:** 25+ logros incluyendo secretos descubribles
- **Diálogos dinámicos:** Triggers que se conectan con eventos del gameplay
- **Co-op:** Modo para dos jugadores con mecánicas sincronizadas
- **Sistema de guardado:** Persistencia automática cada 60 segundos
- **Arquitectura desacoplada:** Uso de SignalBus para comunicación entre sistemas

---

## 📂 Estructura de Archivos

### `/codigo` — Scripts GDScript (Autoloads + Componentes)

| Script | Descripción |
|--------|-------------|
| **SignalBus.gd** | Bus global de señales — desacopla todos los sistemas |
| **LevelManager.gd** | Gestiona transiciones entre niveles con efectos shader |
| **SaveSystem.gd** | Persistencia de progreso y estadísticas (auto-guardado cada 60s) |
| **AchievementManager.gd** | Gestor de logros, desbloqueos y recompensas |
| **achievements_db.gd** | Base de datos con 25+ logros (historia, habilidad, secretos, co-op, cosméticos) |
| **DialogueTriggers.gd** | Sistema de triggers narrativos conectado con eventos del juego |
| DialogueManager.gd | Renderiza diálogos en pantalla (shared) |
| AudioManager.gd | Gestión de sonidos y música (shared) |
| 2026-03-17_player_state_machine.gd | Máquina de estados del jugador |
| 2026-03-17_enemy_spawner.gd | Spawn automático de enemigos |
| 2026-03-17_checkpoint.gd | Sistema de checkpoints |
| 2026-03-17_powerup.gd | Power-ups y buffs |
| 2026-03-17_shooting_system.gd | Sistema de disparo |
| 2026-03-17_beat_sync.gd | Sincronización con BPM para mecánicas on-beat |
| 2026-03-17_camera_smooth.gd | Cámara suave y cinematic |

### `/narrativa` — Contenido Narrativo

| Archivo | Descripción |
|---------|-------------|
| **biblia_mundo.md** | Documento completo del worldbuilding, personajes, temas y finales múltiples |
| **arco_nivel_01.md** | 12 triggers narrativos con código GDScript para Nivel 1 (Sala de Espera) |
| **arco_nivel_02.md** | 7 triggers narrativos con código GDScript para Nivel 2 (Archivo General) |
| personajes.md | Descripciones de personajes (Iris, Thanatos, El Sistema, El Jugador) |
| 2026-03-17_dialogue_manager.gd | Renderizador de diálogos (shared) |

### `/ui` — Interfaz de Usuario

| Script | Descripción |
|--------|-------------|
| **achievement_popup.gd** | Panel animado para mostrar logros desbloqueados |
| 2026-03-17_hud.gd | Heads-up display (vidas, monedas, tiempo) |
| 2026-03-17_game_over.gd | Pantalla de fin de juego |
| 2026-03-17_menu_principal.gd | Menú principal |
| 2026-03-17_dialogue_ui.gd | Caja de diálogo (compartida) |

### `/arte/ui` — Sprites de Interfaz (128x128, pixel art)

- **trofeo_oro.png** — Copa dorada para logros de Historia
- **trofeo_plata.png** — Copa plateada para logros de Habilidad
- **trofeo_bronce.png** — Copa de bronce para logros Secretos
- **icono_historia.png** — Libro/pergamino para categoría Historia
- **icono_skill.png** — Rayo para categoría Habilidad
- **icono_secreto.png** — Interrogación oscura para Secretos
- **icono_coop.png** — Dos siluetas para logros Co-op
- **icono_cosmetico.png** — Estrella brillante para Cosméticos

### `/arte/sprites` — Sprites de Personajes y Enemigos

- 2026-03-17_personaje_femenino_HQ.png
- 2026-03-17_enemigo_goblin_arquero_HQ.png
- 2026-03-17_plataforma_tile_v*.png
- 2026-03-17_tile_roca_HQ.png

### `/shaders` — Efectos Visuales

- screen_transition.gdshader — Transición circular entre niveles
- outline.gdshader — Contorno de objetos

### Niveles (`.tscn`)

- **nivel_01.tscn** — Sala de Espera 001 (introducción)
- **nivel_02.tscn** — Archivo General B-7 (mid-game)
- *(nivel_03.tscn — Depósitos Remotos D-12 — planeado)*

---

## 🔌 Arquitectura de Sistemas

```
┌─────────────────┐
│   SignalBus     │  (Bus global de comunicación)
└────────┬────────┘
         │
    ┌────┴──────────────────────┬─────────────┬────────────┐
    │                           │             │            │
┌───▼──────┐  ┌─────────────┐ ┌─▼──────────┐ │  ┌──────────▼──┐
│Level      │  │AchievementM │ │DialogueTrig│  │  │  SaveSystem │
│Manager    │  │anager       │ │gers        │  │  │             │
└──────────┘  └──────────────┘ └────────────┘  │  └─────────────┘
                   ▲                │           │
                   │                │           │
              ┌────▼────────────────▼──────┐    │
              │    GameManager (Shared)    │    │
              │    AudioManager (Shared)   │◄───┘
              │    DialogueManager (Shared)│
              └────────────────────────────┘
```

### Flujo de Eventos Clave

1. **Carga de Nivel** → LevelManager emite `level_started` → DialogueTriggers dispara "game_start"
2. **Jugador se mueve** → SignalBus emite `player_first_input` → DialogueTriggers dispara "primer_movimiento"
3. **Enemigo muere** → SignalBus emite `enemy_died` → AchievementManager revisa triggers de contador
4. **Nivel completado** → LevelManager emite `level_completed` → SaveSystem guarda progreso
5. **Logro desbloqueado** → AchievementManager emite `achievement_unlocked` → achievement_popup muestra animación

---

## 🎮 Cómo Abrir en Godot 4

1. Abrir Godot 4.2+
2. Proyecto → Abrir → navegar a `/PROYECTOS GAME DEV/PLATAFORMERO_2D/`
3. Seleccionar `project.godot`
4. Editor debería cargar automáticamente todos los autoloads

**Autoloads activos:**
- SignalBus
- LevelManager
- SaveSystem
- AchievementManager
- DialogueTriggers
- NetworkManager, GameManager, AudioManager, DialogueManager (compartidos)

---

## 🏆 Sistemas de Logros

**25 logros totales distribuidos en 5 categorías:**

### Historia (5)
- Primera Excepción (Completar Nivel 1)
- Formulario Rechazado (Completar Nivel 2)
- Apelación Denegada (Completar Nivel 3)
- Error en el Sistema (Desbloquear redemption de Thanatos)
- Expediente Incompleto (Ending)

### Habilidad (5)
- Procesamiento Eficiente (Nivel 1 en <90s)
- Sin Excepciones (Completar nivel sin morir)
- En el Ritmo (10 kills on-beat)
- Salto de Fe (3 wall jumps consecutivos)
- Combo Burocrático (5 kills sin daño)

### Secretos (8) — Requieren descubrimiento
- Burocracia Total (Morir exactamente 7 veces en L1)
- Formulario 404 (Área oculta en L2)
- Multitarea Cuántica (Co-op: ambos saltan simultáneamente)
- El Método Thanatos (Completar nivel sin disparar)
- Existencia Cuestionable (Idle 60 segundos)
- Iris Tiene Razón (Morir con 1 enemigo restante)
- Protocolo 7B (Easter egg en L1)
- Glitch en el Sistema (Morir y matar en el mismo frame)

### Co-op (4)
- Compañeros de Papeleo (Completar nivel en 2 jugadores)
- Muerte Sincronizada (Ambos mueren simultáneamente)
- Pareja de Hecho (3 niveles en co-op)
- ¿Quién Necesita al Otro? (Desbalance: 5 muertes vs 0)

### Cosméticos (3)
- Arqueólogo Digital (Encontrar todos los sprites legacy)
- Aprobado por el Sistema (Desbloquear todos los de Historia)
- Error 404: Jugador no encontrado (Desbloquear todos los Secretos)

---

## 🔧 Cómo Conectar BeatSync con Logros

```gdscript
# En _on_beat() del BeatSync:
func _on_beat(beat_index: int) -> void:
    SignalBus.beat_triggered.emit(beat_index)
    
    # Si el jugador mata un enemigo en el beat:
    if _player_killed_this_beat:
        AchievementManager.increment_stat("on_beat_kills")
        SignalBus.on_beat_kill.emit(player_id)
```

---

## 📝 Triggers Narrativos Disponibles

**Nivel 01:**
- game_start
- primer_movimiento
- thanatos_aparece
- primer_enemigo_muerto
- primer_checkpoint
- primer_muerte
- muerte_3_veces
- moneda_recogida
- power_up_recogido
- mitad_nivel
- previo_salida
- salida_alcanzada

**Nivel 02:**
- entrada_nivel
- primera_plataforma
- thanatos_reaparece
- zona_trampa
- boss_encontrado
- boss_derrotado
- nivel_completado

---

## 🎨 Paleta de Colores (Tono Administrativo Neón)

- **Beige administrativo:** #D4C4A8
- **Gris acero:** #708090
- **Oro desvanecido:** #B8860B
- **Cyan neón:** #00FFFF (interfaz)
- **Púrpura oscuro:** #2F0F4F (sombras)
- **Blanco frío:** #F0F8FF (texto)

---

## 🎵 BPM y Sincronización

El juego usa **120 BPM** como estándar (ajustable en SaveSystem).

- Ataques sincronizados con beat desbloquean "En el Ritmo"
- Las máquinas del Sistema tienen animaciones que "parpardean" al ritmo
- Iris hace pequeños gestos melancólicos off-beat (subvierte expectativas)

---

## 🐛 Debug y Testing

```gdscript
# En consola de debug:
AchievementManager.print_stats()           # Ver todas las estadísticas
AchievementManager.print_unlocked()        # Ver logros desbloqueados
AchievementManager.debug_unlock("id")      # Desbloquear logro manualmente
SaveSystem.print_save_data()               # Ver archivo guardado
DialogueTriggers.disparar("trigger_id")    # Dispara trigger manualmente
```

---

## 📊 MVP Status (Estimado)

- **Narrativa completa:** 100% (biblia + 2 arcos de nivel)
- **Sistemas core:** 95% (solo faltan pequeñas conexiones)
- **Arte UI:** 100% (trofeos e iconos)
- **Logros:** 100% (base de datos + manager)
- **Niveles jugables:** 60% (2 de 3 implementados)
- **Audio/Música:** 30% (framework listo, falta música y SFX)

**MVP jugable estimado:** 2-3 semanas

---

## 🔮 Roadmap Futuro

- [ ] Nivel 3: Depósitos Remotos D-12 + Final Acto 4
- [ ] Animaciones sprite sheets (idle, walk, hurt)
- [ ] Música original (jazz con glitches)
- [ ] SFX completo (papel, sellos, máquinas)
- [ ] Tutorial interactivo
- [ ] Accesibilidad (colorblind mode, subtítulos)
- [ ] Localización (español/inglés/otro)

---

## 📞 Contacto y Créditos

**Desarrollado en:** IndieStudio de Bruno Salas  
**Género:** Plataformero narrativo  
**Plataforma:** Godot 4.2+  
**Duración estimada:** 30-45 minutos (primer playthrough)

---

**Última actualización:** 2026-03-17
