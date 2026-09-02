# WebMotion Engine — estudio de mercado (NO es un proyecto a construir)

> **Estado: cerrado el 01-09-2026. No se implementa como addon.**
> El veredicto completo, con lo que ya existe publicado y lo que no, está en
> **[`VEREDICTO.md`](VEREDICTO.md)**.

## Qué era

Un addon para Godot 4 que trasladara estilos y animaciones web modernas
(Uiverse.io, Framer Motion, CSS keyframes) a juegos 2D/3D: físicas de resortes,
curvas Bézier, shaders de cristal/neón y soporte de mando + ratón.

## Por qué no se construye

Se revisó el mercado. De los cuatro hitos del plan:

- **Tres ya existen publicados y mantenidos** — librerías de tween con juice,
  un tema de glassmorphism completo, y un conversor de HTML/CSS a `.tscn`
  (HTML2TSCN) que hace la traducción mejor y encima reporta lo que no supo
  traducir.
- **El cuarto —resortes para UI y el conflicto Container-contra-escala— sí es
  un hueco real**, pero son ~170 líneas, no un framework, y ya están medio
  escritas en IA Rogue (`systems/ui/ui_motion.gd`, 180 líneas).

## Dónde vive ahora el trabajo

En **IA Rogue**, que es donde está el código y el único cliente:

- Análisis técnico con números de línea:
  `Friends/IA Rogue DEFINITIVE_latest_c7f4d7b/Narrativa/AREA_UI_E_INTERFAZ.md` §1-3
- Fichero a tocar: `systems/ui/ui_motion.gd`
- Los tres cambios propuestos: [`VEREDICTO.md` §5](VEREDICTO.md)

## Qué queda en esta carpeta

El porqué, para que ninguna IA vuelva a proponer construir el framework dentro
de seis meses. El documento de arquitectura original sigue en
[`../../docs/WEBMOTION_GODOT_ARCHITECTURE.md`](../../docs/WEBMOTION_GODOT_ARCHITECTURE.md)
como referencia de diseño — **pero ya no es una hoja de ruta.**
