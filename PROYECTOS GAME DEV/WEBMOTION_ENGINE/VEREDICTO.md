# WebMotion Engine — ¿vale la pena? Veredicto tras revisar el mercado

> **Fecha:** 01-09-2026 · **Pregunta de Bruno:** *«si ya hay otras páginas
> oficiales que hagan lo mismo o alguna aplicación que haga lo mismo, y así
> considerar si vale la pena hacerlo, y si lo puedo llegar a hacer mejor de lo
> que hay actualmente»*.

## La respuesta en una línea

**No como addon público. Sí como tres piezas concretas dentro de IA Rogue** —
porque el 70 % del plan ya existe publicado y gratis, y el 30 % que NO existe
ya está medio escrito en tu propio repo, en `systems/ui/ui_motion.gd`.

---

## 1. El dato que cambia la decisión: esto ya existe en tu casa

El documento maestro
[`docs/WEBMOTION_GODOT_ARCHITECTURE.md`](../../docs/WEBMOTION_GODOT_ARCHITECTURE.md)
propone construir desde cero `motion_wrapper.gd`, `spring_solver.gd`,
`bezier_curve_parser.gd` y una máquina de estados de foco.

Pero en IA Rogue ya hay:

| Lo que el plan propone crear | Lo que ya existe | Dónde |
|---|---|---|
| Máquina de estados hover/press/idle | `bind_button()`, `_set_hovered()`, `_press()` | `systems/ui/ui_motion.gd` (180 líneas) |
| Anti-doble-disparo de audio ratón vs mando | `_sync_mouse_focus()` | `ui_motion.gd:82` |
| Paleta semántica para los componentes | `ui_kit.gd` (393 líneas) | `systems/ui/ui_kit.gd` |
| Entrada/salida con retardo escalonado | `enter()`, `exit()`, `stagger()` | `ui_motion.gd:20-105` |
| Multiplicador de accesibilidad | `_duration()` contra `GraphicsSettings` | `ui_motion.gd:168` |
| El diagnóstico de los 3 cuellos de botella | Ya redactado, con números de línea | `Narrativa/AREA_UI_E_INTERFAZ.md` §1-3 |

**El plan de `docs/` y el análisis de `Narrativa/AREA_UI_E_INTERFAZ.md` §1-3 son
el mismo trabajo escrito dos veces.** Los dos los dejó Antigravity el 01-09. El
de `Narrativa/` es el bueno: está pegado al fichero que hay que tocar y cita
líneas reales. El de `docs/` está en otro repo, hablando de un `addons/web_motion/`
que no existe.

---

## 2. Lo que YA hay publicado (y por qué no vale la pena competir)

Busqué en el Asset Library de Godot y en itch.io. Estado a septiembre 2026:

| Hito del plan | ¿Ya existe? | Quién lo hace |
|---|---|---|
| **Hito 2** — componentes con juice, hover, rebote | ✅ Saturado | [TweenFX](https://godotengine.org/asset-library/asset/4827) (mar-2026), [Tween Composer](https://godotengine.org/asset-library/asset/5108) (jul-2026), [Godot UI Animation Library](https://godotengine.org/asset-library/asset/4033), [Tween Orchestrator](https://godotengine.org/asset-library/asset/4253), [Tween Suite](https://godotassetlibrary.com/asset/ErJMSx/tween-suite), [AnimUI](https://code-main.itch.io/anim-ui/purchase) |
| **Hito 3** — glassmorphism, blur de fondo | ✅ Existe hecho | [Audacious Assets: Glassmorphism UI for Godot](https://audaciousgabe.itch.io/audacious-assets-glassmorphism) — tema completo + shader de blur + scripts de expand/shrink en hover |
| **Hito 4** — traducir Web → Godot | ✅ Existe, y mejor | [HTML2TSCN](https://soulpersona.itch.io/godot-html-ui-converter) convierte HTML/CSS a `.tscn` nativo (Control, VBoxContainer, StyleBoxFlat) con ~90 % de acierto y **te reporta el CSS que no supo traducir con línea y nodo**. Y [Godot WRY](https://godotengine.org/asset-library/asset/3426) directamente mete un webview real dentro de Godot |

Tres de los cuatro hitos ya están cubiertos por gente que lleva meses
manteniéndolos. **Un protocolo de traducción en Markdown para que «una IA
traduzca CSS a GDScript» (sección 4 del plan) pierde contra HTML2TSCN**, que
hace lo mismo determinista y encima te dice qué falló.

---

## 3. Lo que NO existe (y aquí sí eres mejor que lo que hay)

Dos huecos reales, confirmados:

### 3.1 Resortes para UI
No hay ningún addon de *spring physics* para interfaz. Lo que Godot trae —
`DampedSpringJoint2D` — es para **cuerpos físicos**, no sirve para animar un
`Control`. La única alternativa publicada es
[Cuberact Library](https://cuberact.itch.io/cuberact-library) (GDExtension con
Verlet), que tampoco es para UI.

Es la ecuación de una línea. No necesita framework:

```gdscript
# integrador de resorte amortiguado, por cuadro
var f := -stiffness * (value - target) - damping * velocity
velocity += f / mass * delta
value += velocity * delta
```

Lo que compra: **cuando recorres una lista rápido con el stick, el botón no se
teletransporta ni reinicia la animación** — sale de la velocidad que ya llevaba.
Eso hoy no lo puede hacer un `Tween`, que es justo el punto 3 del análisis.

### 3.2 El conflicto Container contra escala
Sigue **sin resolver dentro del motor y sin addon que lo empaquete**. Hay hilos
abiertos y issues vivos —
[#101877](https://github.com/godotengine/godot/issues/101877) (ni siquiera puedes
poner el pivot desde el inspector si el nodo está en un Container),
[el hilo del foro](https://forum.godotengine.org/t/how-to-scale-control-nodes-without-breaking-the-layout-of-its-children/74332) —
y lo que la gente usa es el truco de `top_level`, a mano, caso por caso.

El patrón `MotionWrapper` de tu plan es correcto: un `Control` neutro que le
miente al Container sobre su tamaño mientras el hijo escala libre. Y en Godot 4
`z_index` **sí** existe en `Control` (subió de `Node2D` a `CanvasItem`), así que
la parte de «flotar por encima de la lista» del plan funciona tal cual está
escrita.

---

## 4. Por qué aun así NO conviene publicarlo como addon

Aunque los dos huecos son reales, **empaquetarlos como framework te cuesta lo
que no te devuelve**:

1. **Tienes un solo cliente.** IA Rogue. Un addon exige versionado,
   compatibilidad hacia atrás, documentación, ejemplos, y responder issues —
   todo eso es trabajo que no hace avanzar tu juego.
2. **El plan pesa 4 hitos y 15 ficheros para envolver ~300 líneas útiles.** El
   `spring_solver` es una fórmula. El `bezier_curve_parser` es
   [`Tween.interpolate_value`](https://docs.godotengine.org/en/stable/classes/class_tween.html)
   con una curva, o 20 líneas de Bézier cúbica. Los `adapters/` de world-space y
   3D diegético del plan **no los pide ninguna pantalla que tengas hoy**.
3. **Los shaders de glassmorphism ya los tienes decididos** — IA Rogue tiene su
   idioma visual cerrado (`52_REFERENCIAS_DE_INTERFAZ.md`, un solo color de
   acento por pantalla). Un shader genérico de addon iría contra esa dirección,
   no a favor.

---

## 5. Lo que sí hay que hacer (esto es la propuesta)

**Tres cambios dentro de `systems/ui/ui_motion.gd` de IA Rogue. Ni carpeta
`addons/`, ni repo nuevo, ni framework.**

| # | Qué | Dónde | Tamaño |
|---|---|---|---|
| 1 | `MotionWrapper` — Control que fija `custom_minimum_size` y deja al hijo escalar con `z_index` | nodo nuevo junto a `ui_motion.gd` | ~80 líneas |
| 2 | Estado único `ACTIVE_SELECTION` que funde `mouse_entered` y `focus_entered` | dentro de `_set_hovered()` | ~30 líneas |
| 3 | Integrador de resorte para transiciones interrumpibles | `spring()` estático junto a `enter()`/`exit()` | ~60 líneas |

**A dónde lleva:** los menús de inventario, ajustes y selección de boon dejan de
vibrar cuando el jugador los recorre rápido con el mando, que es el único
síntoma que hoy se nota jugando. Es una tanda, no un proyecto.

Lo que se descarta explícitamente: `adapters/` (world-space, 3D diegético),
`shaders/` propios, `components/` genéricos y el protocolo de traducción por IA
— tres de los cuatro ya se compran hechos y el cuarto no tiene pantalla que lo
pida.

---

## 6. Qué hacer con esta carpeta

Este proyecto **no se borra: se degrada a estudio de mercado**, que es lo que
acabó siendo. El plan de implementación se muda a IA Rogue, donde está el
código y el cliente:

- El análisis técnico bueno vive en
  `Friends/IA Rogue DEFINITIVE_latest_c7f4d7b/Narrativa/AREA_UI_E_INTERFAZ.md` §1-3.
- El documento de `codigos/docs/WEBMOTION_GODOT_ARCHITECTURE.md` se queda como
  referencia de diseño, pero **ya no es una hoja de ruta** — sus hitos 2, 3 y 4
  están cubiertos por addons publicados.
- Esta carpeta guarda el porqué, para que ninguna IA vuelva a proponer construir
  el framework dentro de seis meses.

## Fuentes

- [TweenFX — Godot Asset Library](https://godotengine.org/asset-library/asset/4827)
- [Tween Composer — Godot Asset Library](https://godotengine.org/asset-library/asset/5108)
- [Godot UI Animation Library — Godot Asset Library](https://godotengine.org/asset-library/asset/4033)
- [Tween Orchestrator — Godot Asset Library](https://godotengine.org/asset-library/asset/4253)
- [Tween Suite](https://godotassetlibrary.com/asset/ErJMSx/tween-suite)
- [AnimUI — itch.io](https://code-main.itch.io/anim-ui/purchase)
- [Audacious Assets: Glassmorphism UI for Godot](https://audaciousgabe.itch.io/audacious-assets-glassmorphism)
- [HTML2TSCN — Design Godot UI in HTML](https://soulpersona.itch.io/godot-html-ui-converter)
- [Godot WRY — UI con HTML, CSS y JS](https://godotengine.org/asset-library/asset/3426)
- [Cuberact Library (GDExtension, Verlet)](https://cuberact.itch.io/cuberact-library)
- [Issue #101877 — Pivot Offset no editable dentro de Container](https://github.com/godotengine/godot/issues/101877)
- [Foro Godot — escalar Control sin romper el layout](https://forum.godotengine.org/t/how-to-scale-control-nodes-without-breaking-the-layout-of-its-children/74332)
- [Docs — CanvasItem (`z_index`, heredado por Control)](https://docs.godotengine.org/en/stable/classes/class_canvasitem.html)
- [Docs — DampedSpringJoint2D (es de físicas, no de UI)](https://docs.godotengine.org/en/stable/classes/class_dampedspringjoint2d.html)
