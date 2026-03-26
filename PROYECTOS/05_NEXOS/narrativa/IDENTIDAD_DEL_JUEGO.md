# EMBERVEIL — Identidad Original: Sistema Libre de Copyright
> Este documento define la identidad propia del juego, alejada de Pokémon/Nintendo.
> Claude Code debe usar esta terminología en TODO el código nuevo.
> Reemplazar gradualmente las referencias antiguas.

---

## El problema con la versión anterior

El diseño original usaba mecánicas y términos demasiado cercanos a Pokémon:
- "Pokéball" para capturar criaturas
- "Gym" para los templos de combate
- "Pokédex" para el registro
- "Evolution" como término exacto
- Mecánica de captura idéntica a Pokémon

Este documento establece la identidad nueva: 100% original, con raíces en la **cultura mesoamericana mexicana**.

---

## Nueva Terminología — Tabla Maestra

| Término viejo | Término nuevo | Significado/Origen |
|---|---|---|
| Pokémon / criatura | **Tonal** (pl. Tonales) | Nahuatl: espíritu animal compañero de cada persona |
| Pokéball | **Ofrenda** (pl. Ofrendas) | Ofrenda ceremonial que invita al Tonal a vincularse |
| Pokédex | **Códice** | Como los códices mexicas — registro de conocimiento |
| Gym | **Santuario** | Lugar sagrado donde se prueba el vínculo |
| Gym Leader | **Guardián / Guardiana** | Protector del Santuario |
| Gym Badge | **Sello** | Ya usábamos este término ✓ |
| Evolution | **Despertar** | El Tonal despierta a su forma más plena |
| Trainer / Entrenador | **Guía** | El humano que acompaña y guía a sus Tonales |
| Rival | **Compañero de Camino** | O simplemente por nombre |
| Champion | **Custodio Mayor** | El Guía más fuerte de la región |
| Elite Four | **Los Cuatro Pilares** | Los cuatro guardianes supremos antes del Custodio |
| Move / Ataque | **Arte** | Cada Arte tiene nombre propio |
| Type | **Esencia** | La naturaleza fundamental de un Tonal |
| HM (Hidden Machine) | **Conocimiento Ancestral** | Saberes que se enseñan, no se olvidan |
| TM (Technical Machine) | **Pergamino** | Pergamino con un Arte inscrito |
| PC (Pokémon storage) | **Altar** | Altar donde los Tonales descansan en paz |
| Heal / Pokémon Center | **Casa de Reposo** / **Temazcal** | Lugar de sanación |
| Professor | **Sabio / Sabia** | El anciano/a que guía al protagonista |
| Starter Pokémon | **Tonal Guardián** | El primer Tonal que elige al Guía |

---

## El Sistema de Vínculos — Mecánica Core (reemplaza Pokéballs)

### La filosofía
En Emberveil, los Tonales **no se capturan**. Se **vinculan**.
Un Tonal no puede ser forzado a acompañar a alguien — debe elegirlo.
El Guía demuestra su valía en combate, y luego presenta una **Ofrenda**.
Si el Tonal acepta la Ofrenda, el vínculo se forma.

Esta mecánica es completamente original y encaja perfectamente con el lore del Veilfire.

### Cómo funciona en gameplay

**Paso 1 — El Encuentro:** El jugador encuentra un Tonal salvaje.

**Paso 2 — La Prueba:** Combate hasta debilitar al Tonal (demostrar que el Guía es digno).

**Paso 3 — La Ofrenda:** El jugador selecciona una Ofrenda del menú.
- El Códice muestra qué Ofrenda resuena con este tipo de Tonal.
- Cada Tonal tiene preferencias según su Esencia.

**Paso 4 — La Decisión:** El Tonal considera la Ofrenda.
- Si acepta → el vínculo se forma (animación de luz dorada).
- Si rechaza → el vínculo falla (el Tonal huye o ataca).

**Fórmula de éxito** (reemplaza fórmula de Pokéball):
```
P(vínculo) = (HP_max * 3 - HP_actual * 2) / (HP_max * 3) * tasa_tonal * mult_ofrenda * mult_estado
```

### Los 9 tipos de Ofrenda

| Ofrenda | Equivalente Pokémon | Descripción | Multiplicador |
|---|---|---|---|
| **Ofrenda de Copal** | Pokéball | Incienso básico, funciona con cualquier Tonal | ×1.0 |
| **Ofrenda de Cempasúchil** | Premier Ball | Flor de marigold, especial para Tonales de Esencia Espectro | ×1.5 Espectro/Sombra |
| **Ofrenda de Jade** | Greatball | Piedra preciosa, mayor probabilidad general | ×1.5 |
| **Ofrenda de Obsidiana** | Ultraball | Piedra volcánica, Tonales raros y fuertes | ×2.0 |
| **Ofrenda de Miel** | Healball | Endulza el vínculo, restaura HP al vincularse | ×1.0 + cura |
| **Ofrenda de Xocolatl** | Quickball | Chocolate sagrado, funciona mejor en el primer turno | ×4.0 primer turno |
| **Ofrenda de Turquesa** | Netball | Piedra del agua, mejor con Tonales de Agua/Hielo | ×3.0 Agua/Hielo |
| **Ofrenda de Fuego Ceremonial** | Duskball | Llama ritual, mejor en lugares oscuros o de noche | ×3.5 noche/cuevas |
| **Ofrenda Sagrada** | Masterball | Reliquia del Veilfire — garantiza el vínculo | ×∞ |

### Animación de vínculo (reemplaza sacudidas de Pokéball)
En vez de una bola sacudiéndose, el Tonal es rodeado por luz del Veilfire.
- 1 pulso de luz → vínculo fallido
- 2 pulsos → casi logrado
- 3 pulsos → vínculo casi perfecto
- 4 pulsos + destello dorado → **¡Vínculo formado!**

---

## El Despertar — Reemplaza "Evolution"

Los Tonales no "evolucionan" — **Despiertan**.
El Despertar es un momento espiritual donde el Tonal alcanza su forma más plena.

### Tipos de Despertar
| Trigger viejo | Trigger nuevo | Descripción |
|---|---|---|
| Level up | **Madurez** | El Tonal alcanza cierto nivel de experiencia |
| Trade | **Vínculo Compartido** | El Tonal se vincla con otro Guía que lo honra |
| Stone | **Piedra de Despertar** | Objeto sagrado que activa el potencial dormido |
| Friendship | **Profundidad de Vínculo** | El vínculo emocional alcanza máxima resonancia |
| Time of day | **Hora del Día** | El Despertar ocurre solo en cierto momento |

### Animación de Despertar
No es "Evolution" genérico — cada Tonal tiene su propia animación de Despertar única.
Ej: Embral → Embralcinder → el perro de fuego se envuelve en llamas negras, sus ojos cambian a dorado, emerge Embralcinder.

---

## La Región: Esencia Mexicana

### El nombre del mundo: **Teocalli** ("Casa de Dios" en Nahuatl)
O alternativamente: **Anahuac** (el nombre antiguo del territorio mexicano)

Sugerencia final: **La Región de Xolotl** — Xolotl es el dios azteca del rayo y la muerte, perro guía de las almas. Encaja PERFECTAMENTE con el tema del juego (vínculos, espíritus, viaje).

### Ciudades con nombres mexicanos (actualización)
| Nombre actual | Nombre nuevo sugerido | Referencia |
|---|---|---|
| Cinder Village | **Pueblo Tizón** o **Tepetlixpa** | tepetl=cerro, tl=sufijo Nahuatl |
| Ashgate Town | **San Volcán** o **Ixtla** | de Ixtlaccihuatl |
| Tidelock Port | **Puerto Xólotl** | dios guía de almas |
| Canopyhold | **Selva Quetzal** | ave sagrada mexicana |
| Voltpeak City | **Tlaltecuhtli** o **Tonatiuh** | dioses del rayo/sol |
| Duskwall Necropolis | **Valle Cempa** ✓ | ¡ya está en el juego! Valle de Cempasúchil |
| Crystalspire | **Cristalán** o **Xilonen** | diosa del maíz tierno |
| Scarmouth | **Tlaltipa** o **Boca del Volcán** | |
| Veilwatch Spire | **Torre Nahual** | nahual = ser que puede cambiar de forma |

### Los Cuatro Pilares + Custodio Mayor (reemplaza Elite 4 + Champion)
El sistema ya tenía nombres buenos. Solo actualizamos los títulos:

| Personaje | Título nuevo | Esencia |
|---|---|---|
| Ignar | Guardián del Santuario Ascua | Fuego/Normal |
| Marina | Guardiana del Santuario Marea | Agua/Hielo |
| Sylvari | Guardiana del Santuario Quetzal | Planta/Bicho |
| Volta | Guardián del Santuario Rayo | Eléctrico/Acero |
| Mortem | Guardián del Santuario Cempa ⭐ | Espectro/Sombra |
| Glacien | Guardiana del Santuario Cristal | Hielo/Hada |
| Ashira | Guardiana del Santuario Volcán | Dragón/Fuego |
| Varis | Guardián de la Torre Nahual | Psíquico/Velo |
| Mara Solís | **Custodio Mayor** | — |

---

## Los Santuarios — Reemplaza "Gyms"

Cada Santuario es un templo cultural, no un gimnasio deportivo.
Los Guardianes no son "líderes de gimnasio" — son protectores de un lugar sagrado y de una forma de entender el vínculo.

### Por qué esto evita copyright
- Nintendo/Pokémon tiene "Gym Leader", "Gym Badge", "Pokémon Gym"
- Nosotros tenemos "Guardián", "Sello", "Santuario"
- La mecánica de "ganar el sello del Santuario" es diferente en tono y ejecución

---

## Nombres de Personajes con Cultura Mexicana

### Protagonista: **Riven Solís** → mantener Solís (apellido sol mexicano) ✓

### NPCs con nombres actualizados

| Nombre actual | Nombre nuevo | Origen |
|---|---|---|
| Ignar | **Ignacio "Nacho" Brasa** | Nombre mexicano cotidiano |
| Marina | **Marina Xochitl** | Xochitl = flor en Nahuatl |
| Sylvari | **Silvia Quetzal** | Silvia + nombre sagrado |
| Volta | **Volta Cienfuegos** | Apellido mexicano |
| Mortem | **Don Muerte** o **Señor Mortem** | Tratamiento de respeto |
| Glacien | **Glacia Tlapalteotl** | tlapalteotl = ser de colores |
| Ashira | **Ashira Huitzil** | de Huitzilopochtli |
| Varis | **Varis Nahua** | Nahua = pueblo |
| Cael Brynn | **Cael Brindis** | Brindis = toast, dicho mexicano |
| Nyx Verath | **Nyx Veracruz** | Estado mexicano, significado: vera + cruz |
| Mara Solís | **Mara Solís** ✓ | Perfecto como está |

### El Sabio inicial (reemplaza "Professor")
**Sabio Cuauhtémoc** o **La Sabia Tonatzin**
- Tonatzin = "nuestra madrecita" — diosa madre azteca, equivalente a la Virgen de Guadalupe
- Cuauhtémoc = último emperador azteca, símbolo de resistencia

---

## Expresiones Mexicanas en Diálogos

Agregar estas expresiones auténticas a los diálogos de NPCs:

**Saludos y expresiones:**
- "¡Órale!" — expresión de acuerdo/emoción
- "¡Ándale!" — ¡vamos! / apresúrate
- "¡Híjole!" — sorpresa
- "No manches" — expresión de incredulidad (PG-13)
- "¡Qué chido/a!" — qué genial
- "De volada" — rápidamente
- "Ahorita" — en un momento (puede ser ahora o mañana)
- "¿Qué onda?" — ¿qué pasa? / hola informal
- "Me cae bien" — me cae bien / le tengo aprecio
- "A todo dar" — muy bien/excelente
- "¡Está cañón!" — está difícil/fuerte
- "Con ganas" — con esfuerzo/intensidad
- "Ni modo" — no hay remedio
- "Pa' luego es tarde" — más vale hacerlo ahora

**Expresiones regionales por zona:**
- Norte (Voltpeak, zona fronteriza): "¿Qué pasó, mano?", "Órale pues", "De aquellas"
- Sur/Centro (Canopyhold, zona selvática): "Ahorita vengo", "¿Qué onda, cuate?"
- Duskwall (zona Día de Muertos): "Ya mero", "Pos sí", "¿Cómo amaneció?"
- Costa (Tidelock): "Ándale, vámonos", "Está de pelos"

---

## Qué Cambiar en el Código (Para Claude Code)

### Alta prioridad — cambiar en código nuevo
- `catch_system.gd` → renombrar a `vinculo_system.gd`, usar "Ofrenda" en lugar de "ball"
- `pokedex_screen.gd` → renombrar UI a "Códice"
- UI de batalla: "Atrapar" → "Ofrecer Vínculo"
- `evolution_data.gd` → `despertar_data.gd`, cambiar "evolve" → "awaken/despertar"

### Media prioridad — cambiar gradualmente
- Strings en `dialogue_data.gd`: reemplazar "Gym" → "Santuario", "entrenador" → "Guía"
- `npc_teams.gd`: no cambia mecánica, solo las referencias en comentarios
- `game_options.gd`: textos de UI

### No cambiar (código interno, no visible)
- Variable names en GDScript pueden quedarse en inglés por convención
- Lógica de batalla no cambia, solo la presentación

---

## Por qué Esto Evita Copyright

Nintendo/Game Freak tiene copyright sobre:
- El nombre "Pokémon" ✓ (nosotros usamos "Tonal")
- El diseño de Pokéballs ✓ (nosotros usamos "Ofrenda")
- Los nombres de Pokémon específicos ✓ (las criaturas Emberveil son originales)
- El nombre "Pokédex" ✓ (nosotros usamos "Códice")
- Los nombres de Gym Leaders famosos ✓ (nuestros Guardianes son originales)

Lo que NO tienen copyright:
- El concepto general de coleccionar/criar criaturas (Digimon, Yo-Kai Watch, Coromon, etc.)
- Mecánicas de batalla por turnos
- Sistema de tipos de elemento
- Estructura de "8 líderes + Elite + Campeón"

**Conclusión:** Con esta terminología nueva, Emberveil es tan diferente de Pokémon como Coromon, Cassette Beasts, o TemTem — todos publicados sin problemas legales.

---

*Documento creado: Cowork marzo 2026*
*Este documento es la referencia definitiva para identidad del juego*
*Compartir con Claude Code para uso en todo código nuevo*
