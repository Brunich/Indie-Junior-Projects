# codigos — estado y tarea siguiente

**Última tanda: 01-09-2026.** PR abierto y sin fusionar:
<https://github.com/Brunich/Indie-Junior-Projects/pull/2>

---

## Lo que quedó hecho

- Los 17 proyectos se llaman **por su nombre, sin número** (`NEXOS`, no
  `05_NEXOS`). Arregladas las 5 referencias vivas al nombre viejo.
- `CLAUDE.md` nuevo en la raíz y en NEXOS y PLATAFORMERO_2D; README para los 4
  proyectos de Python que no tenían.
- **WEBMOTION_ENGINE cerrado** tras revisar el mercado
  ([`VEREDICTO.md`](../PROYECTOS%20GAME%20DEV/WEBMOTION_ENGINE/VEREDICTO.md)).
- El token salió de la URL del `origin`; autentica el credential helper.

## Lo que Bruno tiene que hacer a mano (no lo puede hacer una IA)

1. **Revocar el token `ghp_af6U…`** en <https://github.com/settings/tokens>.
   Estuvo incrustado en la URL del remote y salía en cada `git remote -v`.
   Reescribir después `CONFIG/.github_token`, o borrarlo si ya no usa el `.bat`.
2. **Fusionar el PR 2** si está de acuerdo con lo que dice.

---

## La tarea siguiente (elige una)

### A) Los 170 minutos de UI en IA Rogue — el que da fruto visible
```
Proyecto: Friends/IA Rogue DEFINITIVE_latest_c7f4d7b
Lee CLAUDE.md y Narrativa/AREA_UI_E_INTERFAZ.md §1-3.

Implementa en systems/ui/ui_motion.gd los tres cambios de
codigos/PROYECTOS GAME DEV/WEBMOTION_ENGINE/VEREDICTO.md §5:
 1. MotionWrapper — Control que fija custom_minimum_size y deja al hijo
    escalar con z_index (~80 lineas)
 2. estado unico ACTIVE_SELECTION que funde mouse_entered y focus_entered
    dentro de _set_hovered() (~30 lineas)
 3. integrador de resorte amortiguado para transiciones interrumpibles,
    junto a enter()/exit() (~60 lineas)

Y añade en Narrativa/AREA_UI_E_INTERFAZ.md, al final de §3, la linea que
apunta al VEREDICTO — hoy ese documento aun manda al plan viejo de
codigos/docs/WEBMOTION_GODOT_ARCHITECTURE.md como si fuera hoja de ruta.

A donde lleva: los menus de inventario, ajustes y seleccion de boon dejan de
vibrar cuando se recorren rapido con el mando.
```

### B) Que PLATAFORMERO_2D vuelva a abrir
```
Proyecto: codigos/PROYECTOS GAME DEV/PLATAFORMERO_2D
Lee CLAUDE.md — ahi esta el diagnostico medido.

project.godot declara 4 autoloads que no cargan. Dos por la ruta imposible
res://../../ ; dos porque el fichero no existe (AudioManager.gd y
DialogueManager.gd, que el README documenta con ejemplos de uso).

Copia los .gd de _SHARED/autoloads/ dentro de codigo/, reapunta los autoloads
a res://codigo/..., y escribe los dos que faltan. Abre el proyecto en Godot 4
y pega la consola limpia como prueba.

A donde lleva: un proyecto de portafolio que hoy no arranca, arranca.
```

### C) Limpiar NEXOS
```
Proyecto: codigos/PROYECTOS GAME DEV/NEXOS
Lee CLAUDE.md.

Tres cosas, en este orden:
 1. Sprites_Nexos/ tiene 27 carpetas basura llamadas ",," de una descarga
    rota. 26 estan vacias; ",, - Copy (26)/" tiene 3 sprites de VERDAD
    (Chanmayu_fase1, chanmayan_fase2, Gorilox_fase3). Colocalos donde toque
    y borra el resto — comprobando antes que ningun .tscn los referencie.
 2. Migrar los restos de terminologia vieja: datos/pokedex_data.gd y
    ui/pokedex_screen.gd siguen diciendo "pokedex" en vez de Codice.
 3. Decidir que hacer con world_building_tiles (442 MB): Git LFS, o dejarlo
    fuera y que LevelArchitect avise al usuario en vez de fallar mudo.
```

---

## Trampas de esta carpeta, ya pagadas

- **Los documentos mienten.** `ls` antes de construir encima de lo que un
  Markdown da por hecho. Un `✅` no es una prueba.
- **`AUTOCHART/` no es de este repo** — tiene el suyo
  (`Brunich/clonehero-autochart`) y está en `.gitignore`.
- **`AUTOCHART_EDITOR/` no es un proyecto**: es una copia de la rama
  `editor/tocar-y-grabar`, con PR 3 abierto. Se borra cuando ese PR cierre.
- **IA Rogue no se toca desde aquí.** Tiene una sesión en marcha con miles de
  ficheros sin rastrear.
