# Plataformero 2D — reglas antes de tocar nada

Plataformas 2D, Godot 4 / GDScript. Nombre interno: **«El Registro Eterno»**.
Estado: **MVP cerrado el 17-03-2026, congelado desde entonces.**

La documentación del juego (sistemas, logros, paleta, BPM) está en
[`README.md`](README.md). La bitácora de la jornada en que se construyó todo,
en [`BITACORA_2026-03-17.md`](BITACORA_2026-03-17.md). Aquí sólo va lo que hace
daño si se ignora.

---

## 🔴 EL PROYECTO NO ABRE TAL CUAL ESTÁ (medido el 01-09-2026)

`project.godot` declara nueve autoloads. **Cuatro de ellos no pueden cargar:**

```
NetworkManager  = "*res://../../_SHARED/autoloads/NetworkManager.gd"
GameManager     = "*res://../../_SHARED/autoloads/GameManager.gd"
AudioManager    = "*res://../../_SHARED/autoloads/AudioManager.gd"
DialogueManager = "*res://../../_SHARED/autoloads/DialogueManager.gd"
```

Dos problemas distintos, y hay que arreglar los dos:

1. **`res://` no puede salir de la raíz del proyecto.** `res://../../` no es una
   ruta válida en Godot: `res://` *es* la carpeta del proyecto. Los cuatro
   fallan por esto, existan o no.
2. **Dos de esos ficheros ni siquiera existen.** En `_SHARED/autoloads/` sólo
   hay `GameManager.gd` y `NetworkManager.gd`. **`AudioManager.gd` y
   `DialogueManager.gd` no están** — y el README documenta a los dos como
   sistemas centrales, con ejemplos de uso.

**Cómo se arregla de verdad:** copiar los `.gd` de `_SHARED/autoloads/` dentro
de `codigo/` y apuntar los autoloads a `res://codigo/...`; y escribir
`AudioManager.gd` y `DialogueManager.gd`, que están documentados pero no
existen. Un enlace simbólico o un `ProjectSettings` apañado no vale: se rompe en
cuanto alguien clona el repo.

Los cinco autoloads que sí funcionan son los locales: `SignalBus`,
`LevelManager`, `SaveSystem`, `AchievementManager`, `DialogueTriggers`.

---

## Lo que hay de verdad, contado

| Carpeta | Contenido real |
|---|---|
| `codigo/` | **18 scripts.** FSM del jugador (359 líneas), disparos, slime, checkpoint, power-ups, spawner, cámara, BeatSync, capas de música, logros, diálogos, guardado |
| `shaders/` | **25 ficheros** — hit flash, aberración cromática, CRT scanline, outline, transiciones |
| `ui/` | **9** — HUD, menú principal, game over, popup de logro (con sus `.tscn`) |
| `arte/` | **8** |
| `narrativa/` | **5** |
| `animaciones/` | **vacía** |
| `niveles/` | **vacía** — los niveles son `nivel_01.tscn` y `nivel_02.tscn`, en la raíz |

Sólo dos escenas de nivel. Cuando el README hable de más, manda el disco.

---

## Los ficheros llevan la fecha delante y así se quedan

`2026-03-17_player_state_machine.gd`, `2026-03-24_music_layers.gd`… Es la
convención con la que se generó el proyecto y **no se renombra**: hay scripts
que se referencian entre sí por ruta. Si algún día se limpia, se limpia de una
vez y comprobando cada `preload`/`load`, no fichero a fichero.

---

## Antes de dar por bueno un cambio

1. **Abre el proyecto en Godot 4 y mira la consola de errores.** Con cuatro
   autoloads rotos, el primer arranque escupe fallos que no son culpa de tu
   cambio. Sepáralos antes de perseguir un fantasma.
2. Este proyecto está congelado desde marzo. Si vas a retomarlo, **el primer
   trabajo es el de arriba** — arreglar los autoloads. Cualquier otra cosa se
   construye sobre algo que no arranca.
3. Los `.png` de `arte/` son pocos y ligeros: esos sí van a git.
