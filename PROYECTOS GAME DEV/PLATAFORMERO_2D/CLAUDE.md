# Plataformero 2D — reglas antes de tocar nada

Plataformas 2D, Godot 4. Nombre interno: **«El Registro Eterno»**.
**Es una base de portafolio, no un juego terminado** — está aquí para tener un
poco de cada cosa (FSM, logros, diálogos, shaders, BeatSync) de donde partir.

Documentación del juego: [`README.md`](README.md).
Bitácora de la jornada en que se construyó: [`BITACORA_2026-03-17.md`](BITACORA_2026-03-17.md).

---

## ✅ 02-09-2026 — YA ABRE. Lo que estaba roto y cómo se arregló

Estuvo desde marzo sin poder abrirse. **Ninguna de las causas era de diseño: el
`project.godot` y la escena principal estaban escritos a mano, no generados por
Godot.** Verificado con `Godot_v4.6.2 --headless --quit-after 60`.

| Qué estaba roto | Por qué | Arreglo |
|---|---|---|
| Faltaba `config_version=5` | Godot no lo reconocía como proyecto | Añadido |
| 4 autoloads con `res://../../_SHARED/...` | **`res://` ES la raíz del proyecto: no se puede salir de ella.** Y dos de esos ficheros ni existían | `AudioManager` y `DialogueManager` ya existían aquí dentro (`codigo/` y `narrativa/`) — se apunta a ellos. `GameManager` y `NetworkManager` se copiaron de `_SHARED/autoloads/` a `codigo/` |
| `nivel_01.tscn` con `res://../../codigo/...` | La misma ruta imposible, en la escena de arranque | Reescrita con rutas reales |
| `nivel_01.tscn` con `ExtResource("res://ruta.gd")` | En Godot 4 `ExtResource` toma un **id**, no una ruta; y `load_steps` decía 3 con 6 recursos | 5 `ext_resource` declarados con id, `load_steps=6` |
| `icon.svg` y `audio_bus_layout.tres` referenciados | No existían | Icono: se quitó la línea. Buses: se **creó** `audio_bus_layout.tres` con Master/Music/SFX, que son los que `AudioManager` busca por nombre |
| Faltaban las acciones `jump` y `shoot` | El código las usa y no estaban en el mapa de entrada | Declaradas (Espacio / X, y botones de mando) |
| `achievements_db.gd:630` no compilaba | **Faltaba una coma** antes del lote de 5 logros del 18-03. La base de logros ENTERA nunca cargó | Coma puesta |
| `powerup.gd:105` no compilaba | `CanvasItem.new()` — `CanvasItem` es **abstracta**. El power-up entero no hacía nada | `Node2D`, el CanvasItem concreto más simple |
| `sfx_library.gd:154` | Llamaba `AudioManager.play_sfx(stream, bus)`; la firma es `play_sfx(event: String, pitch: float, volume_db: float)` | Registra el stream una vez y llama por nombre de evento |

---

## Lo que queda, y es de Bruno

**No lo arregles tú.** Bruno lo dijo el 02-09: esto es una base para partir, y
los juegos propios los hace él con este estilo.

Al correr quedan errores de **escena, no de código**: `nivel_01.tscn` declara
nodos (`Checkpoint1`, `Enemigo1`) cuyos scripts buscan hijos `Sprite2D` y
`CollisionShape2D` que la escena no tiene, y el nivel **no tiene jugador** — sólo
`SpawnPlayer1` y `SpawnPlayer2` como marcadores. Eso es montar el nivel en el
editor, que es exactamente el trabajo que él quiere hacer.

---

## Lo que hay de verdad, contado

| Carpeta | Contenido real |
|---|---|
| `codigo/` | **20 scripts.** FSM del jugador (359 líneas), disparos, slime, checkpoint, power-ups, spawner, cámara, BeatSync, capas de música, logros, diálogos, guardado, + los 2 autoloads copiados |
| `shaders/` | **25** — hit flash, aberración cromática, CRT scanline, outline, transiciones |
| `ui/` | **9** — HUD, menú principal, game over, popup de logro (con sus `.tscn`) |
| `arte/` · `narrativa/` | 8 · 5 |
| `animaciones/` · `niveles/` | **vacías** — los niveles son `nivel_01.tscn` y `nivel_02.tscn`, en la raíz |

---

## Los ficheros llevan la fecha delante y así se quedan

`2026-03-17_player_state_machine.gd`, `2026-03-24_music_layers.gd`… Es la
convención con la que se generó el proyecto y **no se renombra**: hay escenas
que los referencian por ruta. Si algún día se limpia, se limpia de una vez y
comprobando cada referencia, no fichero a fichero.

## Antes de dar por bueno un cambio

**Ejecútalo, no lo supongas:**

```bash
"/c/Users/bruni/OneDrive/Desktop/Apps/Godot 4.6.2/Godot_v4.6.2-stable_win64_console.exe" --headless --path . --quit-after 60
```

Si aparece un `Parse Error` o un `Failed to load script`, eso **sí** es tuyo. Si
aparece un `Node not found`, es contenido de escena: de Bruno.
