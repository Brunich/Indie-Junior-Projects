# codigos — estado y tarea siguiente

**Última tanda: 02-09-2026.** Todo fusionado en `main`.

---

## Lo que quedó hecho

- Los proyectos se llaman **por su nombre, sin número**. Fusionado en
  [PR 2](https://github.com/Brunich/Indie-Junior-Projects/pull/2).
- **NEXOS y AUTOCHART salieron de este repo**: tienen el suyo, y el de NEXOS
  está tres meses más al día que la copia local. Enlazados desde el índice.
- **PLATAFORMERO_2D vuelve a abrir.** Llevaba desde marzo sin poder abrirse por
  9 causas distintas, ninguna de diseño. Verificado con Godot 4.6.2 headless.
- **AUTOCHART_EDITOR borrado**: era un worktree con el registro roto, sus 81
  ficheros idénticos a la rama `editor/tocar-y-grabar`, que está subida con
  [PR 3 abierto](https://github.com/Brunich/clonehero-autochart/pull/3).
- **WEBMOTION_ENGINE cerrado** tras revisar el mercado
  ([`VEREDICTO.md`](../PROYECTOS%20GAME%20DEV/WEBMOTION_ENGINE/VEREDICTO.md)).
- El token salió de la URL del `origin`. **Bruno ya lo revocó.**

## Los juegos son una BASE. No se «terminan».

Decisión de Bruno (02-09): PONG, SPACE_SHOOTER, ROGUELIKE y PLATAFORMERO_2D
están para tener un poco de cada cosa de donde partir. **Los juegos propios los
hace él con este estilo.**

Lo que se arregla en ellos es **código roto** (algo que no compila, una ruta
imposible, un proyecto que no abre). Lo que NO se toca es **contenido**: montar
niveles, poner sprites, añadir enemigos. Eso es suyo.

En PLATAFORMERO_2D quedan a propósito errores de escena —`Node not found:
Sprite2D`, y el nivel sin jugador, sólo con marcadores de spawn—. Son
exactamente ese trabajo.

---

## La tarea siguiente (elige una)

### A) Nada pendiente aquí — el trabajo vivo está en IA Rogue
```
Proyecto: Friends/IA Rogue DEFINITIVE_latest_c7f4d7b
Lee CLAUDE.md y Narrativa/AREA_UI_E_INTERFAZ.md.
La tarea siguiente de ese repo la marca su propio SIGUIENTE_CHAT.
```

### B) Llevar las correcciones de NEXOS a su repo de verdad
```
Repo: https://github.com/Brunich/Nexos   (NO la carpeta local, que es de abril)

Su CLAUDE.md mandaba leer 9 documentos inexistentes y daba por implementados
6 ficheros que no estan. Ese diagnostico se hizo sobre la copia local: hay que
REHACERLO contra el repo, que es mas nuevo, antes de aplicar nada.

Ojo con una cosa que si es real y no esta en ese repo: la carpeta local
codigos/PROYECTOS GAME DEV/NEXOS/world_building_tiles/ son 442 MB de arte que
NO existen en Brunich/Nexos. Si se quieren versionar, Git LFS.
```

### C) Los juegos base, si él lo pide
```
No por iniciativa propia: Bruno dijo el 02-09 que los hace el.
```

---

## Trampas de esta carpeta, ya pagadas

- **`git fetch` antes de ramificar.** Un ref de seguimiento sin fetch no es el
  remoto: es la última foto que se le tomó. Costó documentar un juego como
  «vacío» cuando en GitHub estaba entero.
- **Los documentos mienten.** `ls` antes de construir encima. Un `✅` no es
  prueba de que el fichero exista.
- **`res://` es la raíz del proyecto**: `res://../../` no puede salir de ella.
  Era la causa de que Plataformero no abriera, repetida en 4 autoloads y en la
  escena principal.
- **Un `.git` que es un fichero es un worktree.** Si `git status` dice «not a
  git repository», mira `git worktree list` antes de dar la carpeta por
  corrupta.
- **`NEXOS/` y `AUTOCHART/` no son de este repo.** Tienen el suyo.
- **IA Rogue no se toca desde aquí.**
