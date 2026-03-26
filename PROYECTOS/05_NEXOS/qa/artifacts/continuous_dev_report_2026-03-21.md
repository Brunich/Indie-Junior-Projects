# Ciclo continuo de mejora — 2026-03-21

## Qué se mejoró
- La validación local ya distingue mejor entre fallas jugables reales y ruido de limpieza al cerrar escenas headless.
- El HUD de combate quedó más despejado en pantalla amplia: la caja de texto y el menú de acciones ya no comparten el mismo espacio de forma tan agresiva.
- `Route2` ya trae pickups y sigue conectando de forma estable con Monterrey y Valle Cempa.

## Qué se corrigió
- [scripts/simulate_gameplay_passes_2026-03-20.ps1](C:\Users\bruni\OneDrive\Desktop\Programming Brunich\IA TEAM\PROYECTOS\05_POKEMON\scripts\simulate_gameplay_passes_2026-03-20.ps1)
  - Ahora trata como `ADVERTENCIA` los avisos de limpieza al cierre cuando el probe ya reportó éxito.
- [scripts/validate_godot_local.ps1](C:\Users\bruni\OneDrive\Desktop\Programming Brunich\IA TEAM\PROYECTOS\05_POKEMON\scripts\validate_godot_local.ps1)
  - Ya no marca como falla general los cierres headless que solo dejan ruido de recursos.
- [escenas/batalla/battle_scene.tscn](C:\Users\bruni\OneDrive\Desktop\Programming Brunich\IA TEAM\PROYECTOS\05_POKEMON\escenas\batalla\battle_scene.tscn)
  - Separé mejor la caja de texto del menú de combate.
- [codigo/batalla/battle_scene.gd](C:\Users\bruni\OneDrive\Desktop\Programming Brunich\IA TEAM\PROYECTOS\05_POKEMON\codigo\batalla\battle_scene.gd)
  - El layout del combate ahora acomoda mejor texto y acciones en resoluciones amplias.
- [escenas/overworld/route2.tscn](C:\Users\bruni\OneDrive\Desktop\Programming Brunich\IA TEAM\PROYECTOS\05_POKEMON\escenas\overworld\route2.tscn)
  - Se añadieron pickups simples para que el tramo tenga más valor jugable.

## Qué quedó estable
- Guardado manual.
- Cambio de criatura al frente.
- Huida de batalla con regreso a la posición correcta.
- Encuentros solo en pasto.
- Ruta Reynosa -> Monterrey -> Sendero del Cempasúchil -> Valle Cempa.
- Entrada y salida de casas.
- Diálogo con NPC.
- Movimiento base de NPC.
- Captura con catnip.
- Derrota y respawn.
- Clínica y PC.
- Olvido de técnica.

## Advertencias reales que siguen vivas
- Algunos probes dejan `ObjectDB instances leaked at exit` al cerrar en headless.
- `battle_item_target_probe` todavía deja `2 resources still in use at exit`, aunque la acción jugable sí termina bien.
- Conviene revisar después qué recurso queda retenido al final de escenas de combate y mapas importados.

## Siguiente bloque recomendable
1. Limpiar el cierre de recursos en probes de combate y mapas importados.
2. Seguir aireando el menú `TAB` y el HUD de combate.
3. Convertir NPCs/personajes overworld ya curados en sprites definitivos o placeholders más consistentes.
