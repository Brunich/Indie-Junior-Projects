# Indie Junior Projects

Portafolio de **Bruno Salas Rodríguez** — Ing. Software UANL, Monterrey NL.
Juegos de Godot 4 de menor a mayor complejidad, más las automatizaciones en
Python.

Este fichero es **el índice**: qué hay, en qué estado está y por dónde se entra.
La documentación de cada proyecto vive dentro de su carpeta.

> **Si eres una IA y acabas de abrir esto:** lee este índice, entra a la carpeta
> del proyecto que te toca y lee su `CLAUDE.md`. No leas los demás. Las reglas
> comunes del repo están en [`CLAUDE.md`](CLAUDE.md), y el estado de hoy en
> [`docs/SIGUIENTE_CHAT.md`](docs/SIGUIENTE_CHAT.md).

---

## 🎮 Juegos en Godot 4

De menos a más. Los cuatro son proyectos completos: abre su `project.godot` en
Godot 4.2+ y pulsa **F5**.

| Proyecto | Nivel | Qué enseña | Estado |
|---|---|---|---|
| **[PONG](PROYECTOS%20GAME%20DEV/PONG/)** | Fácil | Entrada de dos jugadores y colisiones. La raqueta derecha lleva IA básica | ✅ Jugable |
| **[SPACE_SHOOTER](PROYECTOS%20GAME%20DEV/SPACE_SHOOTER/)** | Fácil | Spawner de enemigos, disparo, bucle arcade | ✅ Jugable |
| **[ROGUELIKE](PROYECTOS%20GAME%20DEV/ROGUELIKE/)** | Fácil | Movimiento por rejilla, turnos y progresión de pisos | ✅ Jugable |
| **[PLATAFORMERO_2D](PROYECTOS%20GAME%20DEV/PLATAFORMERO_2D/)** | Medio | FSM del jugador, logros, diálogos, BeatSync, 25 shaders | ⚠️ **No abría**: 4 autoloads rotos. Ver su [`CLAUDE.md`](PROYECTOS%20GAME%20DEV/PLATAFORMERO_2D/CLAUDE.md) |

### Los grandes viven en su propio repo

No están duplicados aquí a propósito — dos copias de lo mismo se separan y nadie
sabe cuál manda.

| Proyecto | Qué es | Repo |
|---|---|---|
| **IA Rogue** | Roguelike 3D pixel art estilo Hades. Godot 4.6. El proyecto grande | [Brunich/IA-Rogue-DEFINITIVE](https://github.com/Brunich/IA-Rogue-DEFINITIVE) |
| **NEXOS: FRACTURA** | RPG por turnos con criaturas y vínculo. Continente Piélago, 8 Guardianes, 5 finales | [Brunich/Nexos](https://github.com/Brunich/Nexos) |
| **AutoChart** | Charts jugables de Clone Hero sacados del audio, con karaoke sílaba a sílaba | [Brunich/clonehero-autochart](https://github.com/Brunich/clonehero-autochart) |

### Y lo que queda aquí sin ser un juego

| Carpeta | Qué es |
|---|---|
| **[WEBMOTION_ENGINE](PROYECTOS%20GAME%20DEV/WEBMOTION_ENGINE/)** | ⛔ **Cerrado el 01-09-2026.** Iba a ser un addon de animación web para Godot; el mercado ya cubre 3 de sus 4 hitos. El porqué, con fuentes, en [`VEREDICTO.md`](PROYECTOS%20GAME%20DEV/WEBMOTION_ENGINE/VEREDICTO.md) |
| **[AUTOCHART_EDITOR](PROYECTOS%20GAME%20DEV/AUTOCHART_EDITOR/)** | 🟡 No es un proyecto: es una copia de la rama `editor/tocar-y-grabar` con [PR 3 abierto](https://github.com/Brunich/clonehero-autochart/pull/3). Se borra cuando ese PR cierre |
| **[_SHARED](PROYECTOS%20GAME%20DEV/_SHARED/)** | 📦 Autoloads reutilizables + histórico de QA y standups de marzo |

---

## 🐍 Automatizaciones en Python

| Proyecto | Qué hace | Stack | Tamaño |
|---|---|---|---|
| **[OMNIBOT_DISCORD](PROYECTOS%20CODIGO/OMNIBOT_DISCORD/)** | Bot de Discord: música multi-fuente, generación de media con IA, búsqueda inversa (simulada) | `discord.py` | 523 líneas |
| **[GMAIL_MORNING_BRIEFING](PROYECTOS%20CODIGO/GMAIL_MORNING_BRIEFING/)** | Panel local que resume y tría el correo de la mañana | Streamlit + Gmail API + Gemini | 354 líneas |
| **[ACCESSI_GAMING_CAM](PROYECTOS%20CODIGO/ACCESSI_GAMING_CAM/)** | Jugar shooters con la webcam: la cabeza apunta, los gestos disparan. Para gamers con discapacidad | OpenCV + `pydirectinput` | 306 líneas |
| **[SPEEDRUN_EXAM_SIMULATOR](PROYECTOS%20CODIGO/SPEEDRUN_EXAM_SIMULATOR/)** | Estudiar contrarreloj: sube el audio de clase, salen flashcards, 10/10 o vuelves a empezar | Streamlit + IA | 232 líneas |
| **[OUTLOOK_UNI_HUB](PROYECTOS%20CODIGO/OUTLOOK_UNI_HUB/)** | Ordena solo los archivos de la uni que llegan por Outlook, por materia | Microsoft Graph | 190 líneas |
| **[BUSINESS_VOICE_WHATSAPP](PROYECTOS%20CODIGO/BUSINESS_VOICE_WHATSAPP/)** | Bot de voz para WhatsApp de negocio: contesta con nota de voz clonada | Playwright + Coqui TTS + Gemini | 178 líneas |
| **[SURVEY_POPULATION_BOT](PROYECTOS%20CODIGO/SURVEY_POPULATION_BOT/)** | Rellena formularios desde un CSV, y deja anotado cada dato que tuvo que inventar | Playwright + pandas | 137 líneas |
| **[WHATSAPP_TICKET_HUNTER](PROYECTOS%20CODIGO/WHATSAPP_TICKET_HUNTER/)** | Caza entradas y avisa por WhatsApp | Playwright | 122 líneas |
| **[Generales y basicos pero mios](PROYECTOS%20CODIGO/Generales%20y%20basicos%20pero%20mios/)** | Los primeros: calculadora, adivina el número, lista de tareas, piedra-papel-tijera | Python puro | 132 líneas |

Cada uno tiene su `FUTURE_PLAN.md` con la hoja de ruta.

---

## 📂 El resto del repo

| Carpeta | Contenido |
|---|---|
| `docs/` | [`SIGUIENTE_CHAT.md`](docs/SIGUIENTE_CHAT.md) — **estado y la tarea siguiente**. Y los documentos que cruzan proyectos |
| `CONFIG/` | Scripts de push y setup de GitHub. **El token va aquí y está en `.gitignore`** |
| `LEEME.md` | El origen: el sistema de 9 agentes con el que arrancó todo, marzo 2026 |

---

## 🚫 Lo que NO entra en este repo, y por qué

Está en [`.gitignore`](.gitignore) con la razón escrita al lado de cada regla:

- **`NEXOS/` y `AUTOCHART/`** — tienen repo propio, enlazado arriba. El de NEXOS
  además está **más al día** que la copia local (junio contra abril): mismos
  sistemas, mismo LevelArchitect, mismas escenas. Duplicar un proyecto es la vía
  rápida a tener dos versiones que se separan.
- Salida generada (`salida/`, `output/`), `__pycache__/`, `.godot/` y secretos
  (`*.token`, `.env`).

## Convención de nombres (01-09-2026)

**Las carpetas se llaman por su nombre, sin número delante.** Antes eran
`01_PONG`, `03_SPACE_SHOOTER`, `05_NEXOS`… Los números decían el orden en que se
empezaron —que a nadie le sirve— y encima chocaban: había **dos `06_`**.

---

**English:** Godot 4 learning portfolio, from Pong to a turn-based dungeon
crawler, plus Python automation tools. Each folder under `PROYECTOS GAME DEV/`
is a standalone Godot project — open its `project.godot` and press F5. The three
big projects (IA Rogue, Nexos, AutoChart) live in their own repositories, linked
above.
