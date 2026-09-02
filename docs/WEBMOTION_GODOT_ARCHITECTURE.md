# WebMotion Engine para Godot 4 — Arquitectura y Plan Maestro
> **Fecha:** 01-09-2026  
> **Autor:** Antigravity (Análisis y Diseño Arquitectónico)  
> **Objetivo:** Sistema universal para traducir y renderizar UI, animaciones y microinteracciones de estilo Web moderno (Uiverse, Framer Motion, CSS Keyframes) en videojuegos de Godot 4 a 60/120+ FPS de forma limpia, robusta y multiplataforma.

> ## ⛔ ESTO YA NO ES UNA HOJA DE RUTA (revisado 01-09-2026)
>
> Se revisó el mercado antes de implementar. **Los hitos 2, 3 y 4 de la sección 6
> ya existen publicados y mantenidos** (librerías de tween con juice, un tema de
> glassmorphism completo, y HTML2TSCN que convierte HTML/CSS a `.tscn`). El único
> hueco real —resortes para UI y el conflicto Container-contra-escala— son ~170
> líneas que van dentro de `systems/ui/ui_motion.gd` de IA Rogue, no un addon.
>
> **Veredicto y fuentes:**
> [`PROYECTOS GAME DEV/WEBMOTION_ENGINE/VEREDICTO.md`](../PROYECTOS%20GAME%20DEV/WEBMOTION_ENGINE/VEREDICTO.md)
>
> Este documento se conserva como **referencia de diseño** (el patrón
> `MotionWrapper` de §3.1 y la ecuación de §3.3 son correctos y se usan). No se
> construye `addons/web_motion/`.

---


## 1. Resumen Ejecutivo y Diagnóstico

### El Problema Fundamental
En el ecosistema web actual existen millones de componentes altamente estilizados con físicas fluidas (*springs*), transiciones elásticas (*cubic-bezier*), efectos de cristal esmerilado (*glassmorphism*) y microinteracciones reactivas. 

Sin embargo, al intentar trasladar estas animaciones a un motor de videojuegos como Godot 4 surgen fricciones técnicas críticas:
1. **Los `Container` de Godot destruyen las transformaciones visuales:** A diferencia de CSS (donde `transform: scale()` no afecta el flujo del DOM), en Godot un `VBoxContainer` o `HBoxContainer` anula la posición y escala de sus hijos en cada pase de layout o hace saltar a los elementos hermanos.
2. **Cámaras y Espacios de Renderizado:** La UI puede vivir en *Screen-Space* (`CanvasLayer`), en *World-Space 2D/3D* (anclada a actores con zoom y shake de cámara) o en *Superficies Diegéticas 3D* (`SubViewport` sobre mallas).
3. **Disparidad de Entrada (Mando vs Ratón):** La web se basa en puntero (`:hover`, `:active`). Un juego en Steam/Consola exige navegación por foco con cruceta/stick (`focus_entered`, `focus_neighbor`) sin disparar eventos duplicados de sonido ni romper el estado visual.
4. **Curvas Físicas vs Interpolaciones Lineales:** Las animaciones web modernas utilizan física de resortes (*damping*, *stiffness*, *mass*) que permiten interrupciones orgánicas con conservación de inercia.

---

## 2. Arquitectura del Addon / Framework (`addons/web_motion/`)

```
addons/web_motion/
├── core/
│   ├── web_motion.gd             # Singleton / API pública estática
│   ├── motion_wrapper.gd         # Wrapper que aísla transformaciones del Container
│   ├── motion_state_machine.gd   # Unificador de estados (Idle, Hovered/Focused, Pressed, Disabled)
│   ├── spring_solver.gd          # Integrador físico de resortes (Euler/Verlet para Framer Motion)
│   └── bezier_curve_parser.gd    # Evaluador de curvas cubic-bezier(p1, p2, p3, p4)
├── adapters/
│   ├── screen_space_adapter.gd   # Manejo de CanvasLayer, anclajes y layouts responsivos
│   ├── world_space_adapter.gd    # UI proyectada en mundo 2D/3D con compensación de cámara y LOD
│   └── diegetic_3d_adapter.gd    # Renderizado en SubViewport para terminales y pantallas 3D
├── shaders/
│   ├── glassmorphism.gdshader    # Desenfoque de fondo + realce de borde (Backdrop Blur)
│   ├── neon_glow_border.gdshader # Borde de energía y luminancia reactiva
│   ├── shimmer_sweep.gdshader    # Barrido de luz UV al enfocar/activar
│   └── scene_wipe.gdshader       # Cortinillas de transición basadas en texturas de ruido
└── components/
    ├── motion_button.gd          # Botón reactivo listo para usar (drop-in replacement de Button)
    ├── motion_card.gd            # Tarjeta / Panel interactivo con elevación y sombras
    └── motion_toast_system.gd    # Sistema de notificaciones emergentes
```

---

## 3. Especificación Técnica de los Módulos Core

### 3.1. Patrón `MotionWrapper` (Solución al conflicto con `Container`)
Para permitir que un botón dentro de un `VBoxContainer` o `GridContainer` se agrande (`scale 1.05`), se desplace (`translateY -4px`) o rote ligeramente sin romper el layout ni hacer parpadear a sus vecinos:

```gdscript
# Estructura del árbol:
# [VBoxContainer]
#   └── [MotionWrapper] (Control transparente que reserva el espacio original en el layout)
#         └── [VisualContent] (Control libre de escalar, rotar y elevar z_index)
```
* **Comportamiento:**
  * El `MotionWrapper` reporta su `custom_minimum_size` fijo al contenedor padre.
  * El nodo hijo `VisualContent` tiene `pivot_offset = size / 2.0` calculado automáticamente.
  * Al hacer hover/focus, el `VisualContent` incrementa su `z_index = 1` y ejecuta el `Tween` de escala/desplazamiento de forma totalmente libre del layout.

### 3.2. Unificador de Entrada Reactivo (Ratón + Mando + Touch)
* Mantiene un estado único por componente:
  * `State.IDLE`
  * `State.FOCUSED` (Activado indistintamente por `mouse_entered` o `focus_entered`)
  * `State.PRESSED` (`button_down` o `ui_accept`)
  * `State.DISABLED`
* **Anti-Doble Disparo de Audio:** Se utiliza una marca temporal (`_last_focus_time_ms`) para sincronizar el foco del ratón (`grab_focus()`) con el gestor de audio del juego sin duplicar sonidos.

### 3.3. Motor de Físicas de Resortes (*Spring Solver*)
Permite reproducir exactamente el comportamiento de librerías como *Framer Motion* o *React Spring*:
$$\text{Fuerza} = -k \cdot (x - x_{\text{target}}) - c \cdot v$$
Donde:
* $k$ (*stiffness* / rigidez del resorte).
* $c$ (*damping* / amortiguación).
* Permite interrupciones suaves: si el jugador mueve el stick rápidamente entre opciones, el botón no "teletransporta" ni reinicia su animación, sino que transiciona fluidamente desde su velocidad actual.

### 3.4. Parser de Curvas Bézier Web
Permite leer directamente strings de CSS como:
`cubic-bezier(0.34, 1.56, 0.64, 1.0)`
Y construir una curva polinómica de tercer grado evaluable en tiempo real o mapeable a curvas de `Tween` nativas de Godot 4.

---

## 4. Protocolo de Traducción IA (De CSS / Web a Godot)

Para que cualquier IA pueda traducir un componente web (de Uiverse.io, CodePen, etc.) a Godot sin margen de error, se define el siguiente esquema estándar:

### Entrada (CSS Web):
```css
.modern-card {
  background: #0d1117;
  border-radius: 12px;
  border: 1px solid rgba(100, 200, 255, 0.2);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
}
.modern-card:hover {
  transform: translateY(-6px) scale(1.03);
  box-shadow: 0 12px 28px rgba(100, 200, 255, 0.35);
  border-color: rgba(100, 200, 255, 0.8);
}
```

### Salida Esperada en Godot (GDScript limpio):
```gdscript
extends MotionCard

func _setup_motion() -> void:
    # Estado Reposo
    style_normal.bg_color = Color("#0d1117")
    style_normal.corner_radius = 12
    style_normal.border_color = Color(0.39, 0.78, 1.0, 0.2)
    
    # Estado Hover / Focus
    motion_hover.offset = Vector2(0, -6)
    motion_hover.scale = Vector2(1.03, 1.03)
    motion_hover.shadow_size = 28
    motion_hover.shadow_color = Color(0.39, 0.78, 1.0, 0.35)
    motion_hover.border_color = Color(0.39, 0.78, 1.0, 0.8)
    motion_hover.curve = WebMotion.BEZIER(0.34, 1.56, 0.64, 1.0)
    motion_hover.duration = 0.3
```

---

## 5. Integración con Proyectos Existentes (Caso de Estudio: IA Rogue)

En proyectos con sistemas avanzados existentes como *IA Rogue*:
1. **Compatibilidad con `UIKit`:** Los colores y estilos se alimentan directamente de constantes de paleta semántica (`UIKit.INK`, `UIKit.ACCENT_SELECT`, `UIKit.ACCENT_THREAT`).
2. **Compatibilidad con `HudLayoutService`:** Los offsets dinámicos de banners y barras de jefe se aplican al `MotionWrapper` o contenedor padre sin romper las microinteracciones del nodo visual.
3. **Sincronización con `GraphicsSettings`:** Respeta el multiplicador de accesibilidad (`GraphicsSettings.duration`) para jugadores que deseen reducir el movimiento de pantalla.

---

## 6. Hoja de Ruta para la Implementación

1. **Hito 1: Core Engine**
   - Implementar `motion_wrapper.gd`, `bezier_curve_parser.gd` y `spring_solver.gd`.
   - Pruebas unitarias de evaluación matemática de curvas y resortes.
2. **Hito 2: Componentes Base**
   - Implementar `motion_button.gd` y `motion_card.gd` con soporte de `StyleBoxFlat` dinámico y sombras reactivas.
   - Verificación en listas `VBoxContainer` con navegación mediante Gamepad y Ratón.
3. **Hito 3: Shaders Web**
   - Implementar `glassmorphism.gdshader` (desenfoque de fondo optimizado para viewport) y `shimmer_sweep.gdshader`.
4. **Hito 4: Documentación y Prompts de Traducción**
   - Publicar el catálogo de ejemplos interactivos y la guía para IAs.
