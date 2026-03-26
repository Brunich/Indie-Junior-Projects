# EMBERVEIL — Briefing completo para Claude Code
> Lee este archivo COMPLETO antes de hacer cualquier cosa en este proyecto.

---

## División de trabajo: Claude Code vs Cowork

**Claude Code (tú):** todo lo relacionado a código GDScript, escenas .tscn, sprites, lógica de batalla, mapas, sistemas de juego.

**Cowork (agente paralelo):** narrativa, diálogos, spreadsheets, documentos de diseño, arte. Documentos ya creados:
- `narrativa/IDENTIDAD_DEL_JUEGO.md` ← **LEE ESTO PRIMERO** — nueva terminología, sistema de Ofrendas, cultura mexicana
- `narrativa/PLAN_ARTE_HD2D.md` — plan de arte y workflow de mapas con LDtk
- `narrativa/dialogos_npcs.md` — scripts de diálogo completos para todos los NPCs
- `narrativa/diseno_gimnasios.md` — blueprints de los 5 gimnasios pendientes
- `emberveil_stats.xlsx` — stats de todas las criaturas en formato visual

## ⚠️ CAMBIOS DE IDENTIDAD — LEER ANTES DE ESCRIBIR CÓDIGO NUEVO

El juego está siendo rediseñado con identidad propia (libre de copyright Pokémon).
Ver `narrativa/IDENTIDAD_DEL_JUEGO.md` para la tabla completa. Resumen urgente:

| Término viejo | Término nuevo en código/UI |
|---|---|
| Pokéball / ball | **Ofrenda** |
| Pokédex | **Códice** |
| Gym / Gimnasio | **Santuario** |
| Gym Leader | **Guardián/Guardiana** |
| Evolution / Evolve | **Despertar / Awaken** |
| Trainer / Entrenador | **Guía** |
| Champion | **Custodio Mayor** |

El archivo `catch_system.gd` debe renombrarse a `vinculo_system.gd` gradualmente.
La UI de "Atrapar" en batalla debe decir "Ofrecer Vínculo".

No dupliques trabajo de narrativa/diálogos — esos los está escribiendo Cowork.

---

## ¿Qué es este proyecto?

**Emberveil** es un juego RPG estilo Pokémon Gen 3-4 hecho en **Godot 4** (GDScript).
Es un proyecto de portafolio de **Bruno (brunich99@gmail.com)**.

⚠️ **NO tocar** `godot-modular-arc-demo-master/` — es el proyecto de un amigo, no tiene nada que ver con este.

Todo el trabajo va en: `IA TEAM/PROYECTOS/05_POKEMON/`

---

## Dos conceptos de juego en este proyecto

### 1. EMBERVEIL (lo que se está construyendo en Godot ahora)
El proyecto activo. 8 gimnasios, mundo Veilfire, Riven Solís, The Unsheathed. Ver secciones abajo.

### 2. POKÉMON: FRACTURA (concepto narrativo avanzado — ver `narrativa/biblia_historia.md`)
Un segundo concepto más maduro que Bruno tiene en desarrollo paralelo. Región: Esteria.
Historia: Vale (protagonista) descubre que su abuela, la Dra. Aldana Vega, encontró Pokémon Primordiales con inteligencia humana. El Campeón Ciro enterró esa verdad para mantener la paz. 50 años de mentira fundacional.
Mecánica clave: Mega Evolución con sistema de vínculo — forzarla con bajo bond hace daño al Pokémon.
**No confundir los dos conceptos.** Si Bruno pregunta sobre FRACTURA, la info completa está en `narrativa/biblia_historia.md`.

---

## Estructura de carpetas

```
05_POKEMON/
├── CLAUDE.md                  ← estás aquí
├── WORLD_BIBLE.html           ← lore Emberveil completo
├── SPRITES_VIEWER.html        ← galería interactiva de sprites
├── project.godot              ← proyecto Godot 4
├── codigo/                    ← todos los scripts GDScript
│   ├── autoload/              ← game_manager.gd, network_manager.gd
│   ├── batalla/               ← battle_manager, battle_scene, type_chart, catch_system, experience_system
│   ├── datos/                 ← pokedex_completo, npc_teams, character_profiles, dialogue_data, evolution_data, tm_hm_data
│   ├── overworld/             ← village_map, route_map, route2, route3, ashgate, tidelock, canopyhold + controllers
│   ├── recursos/              ← creature_instance, move_data, character_data, skin_data, pokedex_data
│   ├── sistemas/              ← audio_manager, save_system, inventory_system, game_options, day_night_system, difficulty_system, ability_system, weather_system
│   └── ui/                    ← title_screen, pause_menu, options_screen, battle_effects, items_screen, party_screen, pokedex_screen, stats_screen, save_screen
├── escenas/                   ← archivos .tscn
│   ├── overworld/             ← overworld.tscn, route1.tscn, ashgate.tscn, tidelock.tscn, canopyhold.tscn
│   ├── batalla/               ← battle.tscn, battle_scene.tscn
│   └── ui/                    ← title_screen.tscn, game_menu.tscn
├── sprites/
│   ├── pokemon/emberveil/     ← sprites de criaturas (.png, 192×192) — generando via ComfyUI
│   ├── tiles/                 ← tiles regionales
│   └── animaciones/batalla/   ← frames de entrada a batalla
├── audio/
│   ├── cries/                 ← sonidos de criaturas (.wav)
│   └── *.wav                  ← BGM estilo Gen 4
└── narrativa/
    ├── WORLD_BIBLE.html
    ├── WORLD_MAP.html
    └── biblia_historia.md     ← concepto FRACTURA completo
```

---

## El mundo: Emberveil

**Ambientación:** Mundo con 5 regiones culturalmente distintas. El poder central es el **Veilfire** — una energía que se amplifica con vínculos emocionales genuinos.

**Historia principal:** Riven Solís, joven de Cinder Village, empieza su viaje para ganar los 8 Veil Seals (insignias). En paralelo descubre que su madre, **Mara Solís** (la Champion), desapareció hace 12 años en "La Cicatriz" (The Scar). La facción villana **The Unsheathed** cree que los vínculos emocionales son debilidad.

**Las 8 regiones y sus gimnasios:**
1. Ashenveil → Ashgate Town → **Ignar** (Fire/Normal) → Cinder Seal
2. Tidebreak → Tidelock Port → **Marina** (Water/Ice) → Tidal Seal
3. Canopy Forest → Canopyhold → **Sylvari** (Grass/Bug) → Web Seal
4. Voltpeak → Voltpeak City → **Volta** (Electric/Steel) → Storm Seal *(financiada por The Unsheathed)*
5. Duskwall Necropolis → **Mortem** (Ghost/Dark) → Bone Seal ⭐ *(Día de Muertos CÁLIDA — fue el último en ver a Mara)*
6. Crystalspire → **Glacien** (Ice/Fairy) → Crystal Seal
7. Scarmouth → **Ashira** (Dragon/Fire) → Scar Seal *(sabe que Mara sigue viva)*
8. Veilwatch Spire → **Varis** (Psychic/Veil) → Veil Seal

**Champion:** Mara Solís — equipo de 6 sin punto débil único. Signature: Veildark-Omega lv88, Shadow Shield.
**Rival:** Cael Brynn — amigo de infancia, equipo evoluciona a lo largo del juego.
**Villano:** Nyx Verath — lidera The Unsheathed, NO usa held items ("los vínculos son cadenas").

---

## Criaturas de Emberveil (región custom)

| ID | Nombre | Tipos | Región | Notas |
|---|---|---|---|---|
| 1001 | Embral | Fire/Normal | Ashenveil | Starter perro de fuego |
| 1002 | Embralcinder | Fire/Dark | Ashenveil | Evolución de Embral (lv28) |
| 1003 | Folimp | Grass | Canopy | Hada de hojas |
| 1004 | Folivian | Grass/Bug | Canopy | Evolución mariposa/polilla |
| 1005 | Larvox | Bug | Canopy | Oruga gorda |
| 1006 | Solmund | Fire/Psychic | Ashenveil | Espíritu solar |
| 1007 | Crystabel | Ice/Fairy | Crystalspire | Hada de cristal |
| 1008 | Aquellux | Water/Electric | Tidebreak | Anguila eléctrica |
| 1009 | Oshenite | Water/Ice | Tidebreak | Medusa bioluminiscente |
| 1010 | Necroveil | Ghost/Dark | Duskwall | Velo espectral ancestral |
| 1011 | Glacinth | Ice/Steel | Crystalspire | Gólem de cristal |
| 1012 | Scarfang | Dragon/Fire | Scarmouth | Dragón volcánico |
| 1013 | Bonehound | Ghost/Normal | Duskwall | Perro esquelético (flor de cempasúchil) |
| 1014 | Veildark | Psychic/Dark | Veilwatch | Ser de sombra (ojos estrella) |
| 1015 | Spidrel | Bug/Poison | Canopy | Araña del bosque |
| 1016 | Deepfin | Water/Dark | Tidebreak | Pez de las profundidades |
| 1017 | Drakpup | Dragon | Scarmouth | Cría de dragón |
| 1018 | Voltux | Electric/Steel | Voltpeak | Gólem de trueno |
| 1019 | Spectryn | Ghost/Psychic | Duskwall | Fantasma de los Seers |

---

## Sistemas implementados ✅

### Batalla
- `type_chart.gd` — 18 tipos + tipo Veil (débil a Dark/Fire, fuerte vs Ghost/Psychic/Dragon, inmune a Normal)
- `experience_system.gd` — fórmula Gen 3+, IVs/EVs/nature, 6 curvas de crecimiento
- `catch_system.gd` — fórmula Gen 6, 9 Pokéballs
- `ability_system.gd` — 50+ habilidades (Intimidate, Shadow Shield, Sturdy, Swift Swim, Mold Breaker, etc.)
- `weather_system.gd` — 7 tipos incluyendo Harsh Sun y Heavy Rain extremos
- `battle_effects.gd` — efectos visuales Gen 4: flash, HP drain animado, catch wobble, XP gain

### Sistemas del juego
- `game_options.gd` — Classic + Extras (Nuzlocke, Hardcore, damage numbers, type hints)
- `difficulty_system.gd` — **Adaptativo por comportamiento** (sin menú de dificultad). Perfil enum: CAUTELOSO/EQUILIBRADO/AGRESIVO/ESTRATEGA. Ajusta nivel enemigos, IA, frecuencia encuentros.
- `day_night_system.gd` — 5 fases sincronizadas al reloj real, modifica encuentros
- `save_system.gd`, `inventory_system.gd`, `audio_manager.gd`
- `latido_system.gd` — Sistema de vínculo portador↔Nexo (El Latido). 4 estados: RESONANTE/ESTABLE/TENSO/ROTO. Controla obediencia, iniciativa propia, Resonancia Plena.
- `huella_system.gd` — Identidad del jugador observada (sin menú). 4 tipos: RAIZ/VIENTO/BRASA/NIEBLA. Desbloquea eventos narrativos exclusivos.
- `resonancia_plena.gd` — Equivalente a Mega Evolución. Solo con Latido RESONANTE. 1 por batalla. Se rompe si el vínculo cae durante el estado.

### Overworld
- `player_controller.gd`, `npc_controller.gd`, `overworld_controller.gd`
- Mapas: Cinder Village, Route 1-3, Ashgate, Tidelock, Canopyhold

### Datos
- `pokedex_completo.gd` — **NexosDB**: 34 criaturas NEXUS Gen 01 (3 líneas de starters + criaturas regionales + legendarios). Reemplazó Kanto data.
- `npc_teams.gd` — 16 entrenadores con EVs, natures, held items, estrategias
- `character_profiles.gd` — perfiles de 16 NPCs con backstory y estilo de batalla
- `tm_hm_data.gd` — 100 TMs + 8 HMs reutilizables (estilo Radical Red)

---

## NPCs — notas de lore críticas

- **Mortem** (Gym 5): fue el último en ver a Mara. Gengar con Shadow Tag + Trick.
- **Ashira** (Gym 7): sabe que Mara está viva. Scarfang es Mold Breaker + Scarfed.
- **Volta** (Gym 4): financiada por The Unsheathed. No lo sabe el jugador hasta Gym 7.
- **Nyx Verath**: equipo SIN held items. Filosófico, no malicioso — tiene un punto válido.
- **Mara Solís (Champion + madre)**: Embralcinder / Glacinth / Garchomp / Togekiss / Mewtwo / Veildark-Omega lv88 Shadow Shield. Es el clímax emocional, no solo mecánico.
- **Cael Brynn (rival)**: starter opuesto al del jugador. Equipo escala con el progreso.

---

## Tareas pendientes prioritarias

### 🔴 Alta prioridad (Claude Code)
- [x] **Pueblo Reynosa** — `escenas/overworld/pueblo_reynosa.tscn` creado. TileMapLayer con `pueblo_reynosa_map.gd`, 10 WarpZones, 10 SpawnPoints, 5 NPCs. ⚠️ Falta asignar TileSet en editor Godot (LimeZu packs en `world_building_draft/Serene Village/16x16_original/`).
- [ ] **Conectar escenas** — TileMapLayer atlas, señales del jugador, transiciones
- [ ] **Battle entry** — overworld → battle via `battle_effects.gd`
- [ ] **NPC teams en batalla** — conectar `npc_teams.gd` con `battle_manager.gd`
- [x] **Sprites Nigromante** — 30 sprites NPC Día de Muertos generando via ComfyUI → `sprites/personajes/nigromante/nig_personaje_001-030.png`

### 🟡 Media prioridad (Claude Code)
- [ ] Rutas 4-8
- [ ] Mapas Gimnasios 4-8
- [ ] Sistema de evolución (trigger mechanic)
- [ ] Pokédex UI conectada a `pokedex_completo.gd`
- [ ] AnimatedSprite2D de batalla entry

### 📝 Ya en progreso (Cowork — no duplicar)
- [x] CLAUDE.md actualizado con FRACTURA y división de trabajo
- [ ] Spreadsheet XLSX de stats de criaturas
- [ ] Scripts de diálogo completos para todos los NPCs clave
- [ ] Documento de diseño de niveles para Gimnasios 4-8

---

## Convenciones de código

- **Paths:** `res://codigo/`, `res://escenas/`, `res://sprites/`, `res://audio/`
- **Sprites criaturas:** `res://sprites/nexos/` (no `sprites/pokemon/emberveil/` — ya renombrado)
- **Autoloads:** GameManager, SaveSystem, InventorySystem, AudioManager, GameOptions, DayNightSystem, NetworkManager
- **Sprites:** 1