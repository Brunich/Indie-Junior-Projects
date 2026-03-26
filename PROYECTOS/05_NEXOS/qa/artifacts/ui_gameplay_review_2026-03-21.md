# Revision de UI y flujo jugable — 2026-03-21

## Estado general
- El loop base ya se sostiene: explorar, entrar en pasto, pelear, capturar, huir, curar y volver a salir.
- La ruta extendida ahora llega hasta `Valle Cempa` y el `WORLD_PATH_PROBE` sigue en verde.
- El cambio de mayor impacto de esta pasada fue quitar aperturas innecesarias del explorador y dejar el tooling mucho mas predecible.

## Hallazgos de UI
- El menu de `TAB` ya funciona, pero sigue viendose mas cargado de texto de lo ideal para una experiencia tipo Pokemon clasico.
- Los paneles de criaturas son funcionales, aunque todavia conviene dar mas aire entre bloques y reducir informacion secundaria visible al mismo tiempo.
- El combate sigue siendo la parte visual mas apretada: la lectura del HUD baja cuando se acumulan paneles y feedback al mismo tiempo.
- La caja de dialogo es util, pero aun puede ganar claridad si despues se anade nombre de hablante y una jerarquia mas fuerte entre texto principal y contexto.

## Hallazgos de gameplay
- `VALIDACION GENERAL: OK` en [validate_godot_local_report.txt](C:\Users\bruni\OneDrive\Desktop\Programming Brunich\IA TEAM\PROYECTOS\05_POKEMON\qa\artifacts\validate_godot_local_report.txt).
- La simulacion local nueva quedo en [gameplay_simulation_report_2026-03-21-route2.txt](C:\Users\bruni\OneDrive\Desktop\Programming Brunich\IA TEAM\PROYECTOS\05_POKEMON\qa\artifacts\gameplay_simulation_report_2026-03-21-route2.txt).
- Lo estable:
  - guardado manual
  - cambio de equipo
  - huida y regreso a posicion
  - encuentros solo en pasto
  - dialogos NPC
  - movimiento NPC
  - derrota y respawn
  - clinica y PC
  - tramo Reynosa -> Monterrey -> Sendero del Cempasuchil -> Valle Cempa
- Lo que sigue dejando ruido:
  - warnings de limpieza al cerrar algunas escenas headless
  - el probe de objeto dirigido en batalla sigue marcado como `FALLA` por recursos vivos al salir, aunque la accion jugable en si termina bien

## Prioridades siguientes
1. Limpiar el cierre de recursos en probes de combate y mapas importados.
2. Compactar el menu TAB y el HUD de combate para que respiren mas.
3. Convertir los personajes overworld curados en sprites definitivos o referencias directas para sprite pass.
