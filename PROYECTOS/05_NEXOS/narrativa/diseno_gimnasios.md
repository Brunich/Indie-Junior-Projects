# EMBERVEIL — Diseño de Niveles: Gimnasios 4-8
> Documento de referencia para Claude Code al crear los mapas de gimnasios pendientes.
> Incluye: layout, puzzle, NPCs de relleno, estética, música sugerida.

---

## GIMNASIO 4: VOLTPEAK — "La Fábrica de Tormentas"
**Gym Leader:** Volta | **Tipos:** Electric / Steel | **Insignia:** Storm Seal
**Nivel sugerido del jugador:** 38-44

### Estética
Industrial. Cables eléctricos por todos lados. Plataformas metálicas con arcos de Tesla. Las luces parpadean cuando hay batallas. El suelo conduce electricidad — trozos de goma para caminar.

### Layout (30×24 tiles)
```
##################################
#  PUERTA ENTRADA                 #
#  [plataforma] [cable] [plataforma]#
#       ↓ puzzle eléctrico        #
#  [interruptor A]  [interruptor B]#
#       ↓                        #
#  [TRAINER 1]                   #
#  [puente magnético]             #
#  [TRAINER 2]  [TRAINER 3]       #
#       ↓ puzzle: activar orden   #
#  [sala de generadores]          #
#  [TRAINER 4]                   #
#       ↓                        #
#  [VOLTA — arena elevada]        #
##################################
```

### Puzzle
Hay 4 interruptores numerados. Deben activarse en el orden correcto (indicado por pistas en carteles dispersos por la ciudad). Orden incorrecto = descarga que manda al jugador al inicio del gym.
Secuencia correcta: 3 → 1 → 4 → 2 (pista en el noticiero de la ciudad).

### NPCs de Relleno
- **Técnico Ferran** (antes de Trainer 1): "La energía que generamos aquí alimenta tres ciudades. Volta lo hace posible."
- **Obrero Nadia** (bloquea camino secundario): "Por aquí no. Mantenimiento."
- **Investigadora Sol** (Trainer 2, Voltux lv38 + Magnezone lv40): "¡La corriente alterna siempre gana a la continua!"
- **Guardia Eléctrico Bram** (Trainer 3, Jolteon lv38 + Aquellux lv39): "Volta dice que el gym no es espectáculo. Pero a mí me parece bastante espectacular."
- **Técnico Senior Pío** (Trainer 4, Electrode lv41 + Voltux lv42): "La jefa lleva dos semanas más seria de lo normal. Algo le pesa."

### Diálogos ambientales
- Cartel entrada: "PROHIBIDO EL ACCESO SIN AUTORIZACIÓN — Voltpeak Energy Corp"
- Cartel puzzle: "Secuencia de reinicio de emergencia: ver Boletín Diario de Voltpeak"
- Radio encendida: "...y el suministro energético de Voltpeak continúa siendo el más estable de la región..."

---

## GIMNASIO 5: DUSKWALL NECROPOLIS — "El Jardín de los que se Fueron" ⭐
**Gym Leader:** Mortem | **Tipos:** Ghost / Dark | **Insignia:** Bone Seal
**Nivel sugerido del jugador:** 44-52
**Este es el gym más icónico — diseño y atmósfera cuidados al máximo**

### Estética
NO oscuro ni aterrador. Cálido y melancólico. Lápidas cubiertas de flores de cempasúchil (naranja/amarillo). Velas por todas partes. Música suave. Las paredes tienen murales de personas y Pokémon ya fallecidos. Mariposas monarca que vuelan. La luz es dorada, no gris.

### Layout (36×28 tiles)
```
####################################
#  ENTRADA — arco de flores         #
#  [mural: "los que se fueron ríen"] #
#  [TRAINER 1 — en cuclillas rezando]#
#       ↓                          #
#  [laberinto de lápidas]           #
#  — hay lápidas con nombres de     #
#    personajes del lore —          #
#  [TRAINER 2]  [TRAINER 3]        #
#  [altar central — acertijo]       #
#       ↓                          #
#  [pasillo de velas]               #
#  [TRAINER 4]                     #
#       ↓                          #
#  [arena: jardín abierto con luna] #
#  [altar de MORTEM — siempre hay   #
#   flores frescas sobre él]        #
####################################
```

### Puzzle
Hay 6 lápidas con nombres y fechas. En el altar central hay un libro con preguntas:
1. "¿Quién fue el primer Gym Leader de Duskwall?" → respuesta en una lápida → nombre grabado = "Aldric"
2. "¿Cuántos años vivió Bonehound antes de volverse fantasma?" → lápida con años = 7
3. "¿Qué flor nunca se marchita en Duskwall?" → cartel de flores = Cempasúchil

Cada respuesta correcta abre un camino. Respuesta incorrecta = batalla aleatoria.

**Lápidas con nombres del lore (easter eggs):**
- "Dra. Iris Vael — 'Entendió el Veil antes que nadie'"
- "Capitán Renn Solís — 'No tuvo miedo del mar ni de la muerte'" (familiar de Mara)
- "Bonehound del primer Mortem — 'El más fiel de todos'"

### NPCs de Relleno
- **Florista Amara** (entrada, no es trainer): "¿Primera vez en Duskwall? No tengas miedo. Los que duermen aquí están en paz."
- **Guardiana Celta** (Trainer 1, Gengar lv44 + Bonehound lv45): "Mortem dice que la batalla es un ritual. Que cuando dos equipos se enfrentan, sus almas se reconocen."
- **Devoto Isak** (Trainer 2, Spiritomb lv46 + Necroveil lv47): "¿Ves ese mural? Esa es la batalla más famosa de la historia de Duskwall. Dicen que duró tres días."
- **Veladora Prim** (Trainer 3, Mismagius lv46 + Spectryn lv48): "No lloramos aquí. Sería una descortesía con los que ya están tranquilos."
- **Guardián Mayor Rone** (Trainer 4, Dragapult lv50 + Gengar lv51): "Mortem conoció a alguien hace tiempo. No habla de ello. Pero a veces mira hacia el norte."

### Notas especiales de diseño
- La música del gym debe tener guitarra española suave, no música de terror
- Hay un Bonehound que camina libre por el gym — no ataca, solo te sigue un momento
- En la arena de Mortem hay una foto enmarcada (sprite pixelado) que el jugador puede examinar: "Una entrenadora y su Veildark — sin nombre"

---

## GIMNASIO 6: CRYSTALSPIRE — "La Cámara de Refracción"
**Gym Leader:** Glacien | **Tipos:** Ice / Fairy | **Insignia:** Crystal Seal
**Nivel sugerido del jugador:** 52-60

### Estética
Caverna de cristal natural. Todo refleja la luz — el jugador ve su reflejo multiplicado. Frío visual (azul/blanco). Los cristales tienen formas imposiblemente perfectas. Sonido de tintineos suaves al caminar.

### Layout (34×26 tiles)
```
##################################
#  ENTRADA — estalactitas de hielo #
#  [puzzle de reflejos]            #
#  [TRAINER 1]                    #
#       ↓ plataformas de hielo    #
#  [sala de los espejos]           #
#  — hay 3 Glacien falsas que      #
#    son reflejo —                 #
#  [TRAINER 2]  [TRAINER 3]       #
#       ↓ corredor helado         #
#  [TRAINER 4]                    #
#       ↓                        #
#  [GLACIEN — plataforma de cristal]#
##################################
```

### Puzzle
Hay espejos que redirigen un rayo de luz. El jugador debe orientarlos para abrir puertas de hielo. Hay 3 espejos giratorios con 4 posiciones cada uno. La solución está sugerida por el patrón de cristales en el suelo.

### NPCs de Relleno
- **Cristalógrafa Yena** (Trainer 1, Clefable lv52 + Crystabel lv54): "Los cristales tardan miles de años en formarse. Glacien tiene la paciencia de los cristales."
- **Explorador Rudo** (no trainer, bloqueado): "Está bien helado. Mis botas resbalan. No paso de aquí."
- **Guardiana de Hielo Sola** (Trainer 2, Glacinth lv54 + Mr. Rime lv55): "El frío no lastima. Solo clarifica."
- **Investigador Kael** (Trainer 3, Froslass lv56 + Oshenite lv56): "Glacien lleva años estudiando las propiedades del Veilfire en temperaturas extremas. Resultados fascinantes."
- **Capitana de Cristal Wren** (Trainer 4, Jynx lv57 + Glacinth lv58): "Si llegas hasta Glacien, mereces el sello. Nadie llega por accidente."

---

## GIMNASIO 7: SCARMOUTH — "La Boca del Volcán"
**Gym Leader:** Ashira | **Tipos:** Dragon / Fire | **Insignia:** Scar Seal
**Nivel sugerido del jugador:** 60-68
**Tono:** El gym más dramático visualmente — lava visible, calor extremo, tonos rojos y negros

### Estética
Cavernas volcánicas activas. Lava que fluye a los lados de los caminos. Roca negra y paredes escarlata. El techo es abierto — se ve el volcán. Las batallas aquí se sienten como duelos, no como competencia.

### Layout (38×30 tiles)
```
######################################
#  ENTRADA — entre dos cascadas de lava#
#  [puentes sobre lava]              #
#  [TRAINER 1]                      #
#       ↓ puzzle: caminos de roca    #
#  [sala de los dragones dormidos]   #
#  — estatuas de dragones de Emberveil#
#  [TRAINER 2]  [TRAINER 3]         #
#       ↓ ascenso                   #
#  [TRAINER 4]  [TRAINER 5]         #
#       ↓ cima — vistas al volcán   #
#  [ASHIRA — arena al borde del volcán]#
######################################
```

### Puzzle
Hay 4 pilares con símbolos de dragones. Cada pilar, cuando se activa, abre o cierra rutas de roca sobre la lava. La solución está indicada por los murales de los dragones en las paredes — cada dragón señala una dirección.

**Mural especial:** hay un mural de una entrenadora con un Veildark. Sin inscripción. Ashira lo mira a veces.

### NPCs de Relleno
- **Escaladora Fen** (Trainer 1, Charizard lv60 + Drakpup lv58): "Ashira dice que el fuego prueba al guerrero. Yo digo que el frío también, pero no le llevo la contraria."
- **Explorador de La Cicatriz Tymon** (no trainer, información clave): "He estado en La Cicatriz tres veces. La tercera vez... vi a alguien. Una mujer. Con un Veildark enorme." *(si el jugador presiona)* "No me preguntó su nombre. Pero miraba hacia adentro, no hacia afuera. Como si estuviera esperando algo."
- **Domadora Kira** (Trainer 2, Haxorus lv62 + Garchomp lv63): "Ashira nos enseñó que los dragones no se doman. Se respetan."
- **Veterano Sorn** (Trainer 3, Flygon lv62 + Scarfang lv64): "He visto a cientos intentarlo. Los que llegan a Ashira tienen algo diferente."
- **Guardiana del Volcán Mira** (Trainer 4, Salamence lv64 + Goodra lv65): "Si oyes el volcán rugir... está bien. Ashira dice que así respira."
- **Heraldo Drak** (Trainer 5, Dragonite lv66 + Drakpup lv63): "La batalla con Ashira no es para ganar. Es para que te vea."

---

## GIMNASIO 8: VEILWATCH SPIRE — "La Torre del Velo"
**Gym Leader:** Varis | **Tipos:** Psychic / Veil | **Insignia:** Veil Seal
**Nivel sugerido del jugador:** 68-74
**Tono:** Sobrenatural, tranquilo, casi onírico — la culminación de todo el viaje

### Estética
Una torre que literalmente se pierde en las nubes. Dentro, las paredes son translúcidas — se ven siluetas de Pokémon moviéndose en el Veil. El suelo tiene marcas de luz que forman constelaciones. La gravedad se siente diferente — los sonidos llegan con delay.

### Layout (32×44 tiles — es una torre vertical con múltiples pisos)
```
PISO 1 — ENTRADA
  [portal de entrada que vibra con el Veil]
  [TRAINER 1]
  [ascensor de luz]

PISO 2 — LA SALA DE LOS RECUERDOS
  [visiones del pasado del jugador — momentos de la historia narrados como siluetas]
  [TRAINER 2]  [TRAINER 3]

PISO 3 — EL LABERINTO DEL VEIL
  [el laberinto cambia de forma — hay que seguir la luz morada]
  [TRAINER 4]

PISO 4 — LA CIMA
  [abierto, vista de toda la región]
  [VARIS — de pie en el centro, sin arena]
```

### Puzzle
El laberinto del Viso 3 cambia su configuración cada vez que el jugador lo visita. La solución es siempre seguir las luces de color violeta — nunca las blancas. Las luces blancas llevan a combates de Pokémon salvajes del Veil.

**Detalle especial — Piso 2:**
En la sala de los recuerdos hay siluetas que representan momentos clave del juego. Si el jugador camina cerca de ellas, hay diálogos internos de Riven (el protagonista) recordando cada gym leader:
- Silueta de Mortem: *"Fue el primero en decirme su nombre. El primero que la mencionó."*
- Silueta de Ashira: *"Ella sabía. Lo supo antes de que yo lo pidiera."*
- Silueta de Cael: *"¿Dónde estás ahora, Cael?"*

### NPCs de Relleno
- **Vidente Aera** (Trainer 1, Gardevoir lv68 + Veildark lv70): "Varis dijo que vendrías. Nosotros nos preparamos. ¿Tú también?"
- **Estudioso del Veil Korr** (Trainer 2, Alakazam lv69 + Spectryn lv70): "El Veil no es magia. Es una frecuencia. La mayoría no puede sintonizarla."
- **Guardiana Silente Yris** (Trainer 3, Gallade lv70 + Necroveil lv71): "No hablo durante las batallas. El Veil habla por mí."
- **Observador del Velo Mael** (Trainer 4, Espeon lv71 + Spectryn lv72): "Llevas ocho sellos. Varis lo sintió esta mañana. Dijo: 'ya casi están aquí'."

### Notas de diseño
- La batalla con Varis NO tiene música de gym normal — usa un arreglo suave de la canción del título
- Cuando Veildark aparece en la batalla, hay un flash de luz donde se ve brevemente la silueta de Mara
- El diálogo de Varis al finalizar la batalla debe tener pausa de 3 segundos antes de que aparezca el Veil Seal en pantalla

---

## NOTAS GENERALES PARA IMPLEMENTACIÓN EN GODOT

### Estructura de archivos sugerida
```
codigo/overworld/
  voltpeak_gym.gd
  duskwall_gym.gd
  crystalspire_gym.gd
  scarmouth_gym.gd
  veilwatch_gym.gd
  veilwatch_gym_piso2.gd
  veilwatch_gym_piso3.gd
  veilwatch_gym_piso4.gd

escenas/overworld/
  voltpeak_gym.tscn
  duskwall_gym.tscn
  crystalspire_gym.tscn
  scarmouth_gym.tscn
  veilwatch_spire_1.tscn
  veilwatch_spire_2.tscn
  veilwatch_spire_3.tscn
  veilwatch_spire_4.tscn
```

### Niveles de trainers en cada gym
| Gym | Trainer Min | Trainer Max | Gym Leader |
|-----|------------|------------|------------|
| 4 Voltpeak | 38 | 43 | 42-44 |
| 5 Duskwall | 44 | 51 | 50-54 |
| 6 Crystalspire | 52 | 58 | 56-60 |
| 7 Scarmouth | 60 | 65 | 64-66 |
| 8 Veilwatch | 68 | 72 | 70-72 |

### TileMapLayer recomendados por gym
- **Voltpeak:** metal_tile, cable_tile, platform_tile, spark_tile
- **Duskwall:** stone_tile, grave_tile, flower_tile, candle_tile, dirt_path
- **Crystalspire:** crystal_tile, ice_tile, reflection_tile, snow_tile
- **Scarmouth:** lava_tile, rock_black_tile, fire_tile, crater_tile
- **Veilwatch:** veil_tile, cloud_tile, star_tile, glass_tile

---

*Documento de diseño creado por Cowork — marzo 2026*
*Para implementación en código por Claude Code*
*Ver también: `narrativa/dialogos_npcs.md` para los diálogos completos de cada Gym Leader*
