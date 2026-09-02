# Plan: aprender los patrones de las canciones que ya tienes

**Que se quiere:** que un chart generado no solo caiga donde suena, sino que se
sienta *escrito por alguien que sabe*. Divertido de tocar. Y que lo que se
considere divertido salga de tus 396 canciones, no de mi criterio.

**El problema del enunciado:** "divertido" no es una medida. Es media docena de
propiedades distintas que se pueden medir por separado y que a veces se pelean
entre ellas. Este documento las separa, dice como se mide cada una, y sobre
todo **dice lo que te va a enganar por el camino**, que es la parte que decide
si el analisis vale o es humo.

---

## 1. Las tres capas de un patron

El error clasico de este tipo de analisis es medir solo la primera capa. La
sensacion de tocar vive repartida en las tres:

| Capa | Escala | Que es | Ejemplo |
|---|---|---|---|
| **Gesto** | 2–8 notas | lo que hace la mano | una escalera G-R-Y-B, un trino, un galope |
| **Figura** | 1–2 compases | el ritmo, independiente de que trastes | corchea recta, galope, sincopa, tresillo |
| **Arquitectura** | la cancion entera | donde va cada cosa | intro suave, verso repetido, solo de rafagas, final |

Un generador que clava la capa 1 y falla la 3 produce charts que se sienten
**planos**: cada compas por separado esta bien y la cancion entera aburre. Al
reves — capa 3 buena y capa 1 pobre — se siente **aleatorio**: la energia sube y
baja donde toca, pero lo que tocas no significa nada.

Hoy el generador de AutoChart trabaja en la capa 1 y media (contorno, motivos,
acordes en tramos) y **no toca la 3 en absoluto**. Ese es el hueco mas grande.

---

## 2. La unidad de medida (o el analisis no compara nada)

Cuatro decisiones que hay que tomar antes de contar la primera nota, porque si
se toman mal todo lo demas sale sesgado:

1. **En TIEMPOS, no en segundos.** Cuatro semicorcheas a 90 BPM y a 200 BPM son
   la misma figura escrita y dos actos fisicos distintos. Se cuenta en tiempos
   y la velocidad entra como **dimension aparte**, no mezclada.
2. **En FORMA, no en posicion.** `G-R-Y` y `R-Y-B` son la misma escalera. Se
   cuentan los pasos de carril (`+1,+1`), no los trastes absolutos. Lo absoluto
   solo importa para una cosa: las anclas (el verde y el naranja no son
   intercambiables para la mano).
3. **La unidad es el GOLPE, no la nota.** Un acorde de tres notas es un golpe.
   Contar notas infla los acordes y hunde las notas sueltas.
4. **El instrumento cambia el significado de todo.** Un tremolo en el bajo es
   normal; el mismo tremolo en la solista es un momento. Nunca se mezclan
   guitarra, bajo, ritmica y teclado en la misma cifra.

---

## 3. El vocabulario: los 16 gestos que se cuentan

Cada uno esta implementado en `autochart/atlas.py:detectar_licks` y elegido
porque **la mano lo reconoce**, no porque sea facil de detectar:

| Gesto | Que se siente | Umbral |
|---|---|---|
| `tremolo` | machaqueo, tension | 4+ iguales a <= 1/8 |
| `trino` | dos dedos alternando | 4+ entre 2 carriles |
| `escalera_sube` / `escalera_baja` | la mano corre | 3+ pasos del mismo signo |
| `zigzag` | inquietud, dificultad | 5+ cambiando de sentido, 3+ carriles |
| `galope` | el gesto del metal | larga-corta-corta **repetido** 2+ veces |
| `rafaga` | el momento | 6+ a semicorchea |
| `salto_ancho` | riesgo | 3+ carriles de un golpe |
| `acorde_martillo` | riff de power chord | 3+ el mismo acorde |
| `acorde_movil` | riff que se mueve | 3+ la misma forma desplazada |
| `acorde_alterno` | vamp, baile | acorde/suelta/acorde/suelta |
| `anclado` | comodidad | acordes seguidos que comparten carril |
| `abierta_bombeo` | chug moderno | abierta 3+ veces en 4 tiempos |
| `sostenido_largo` | respiro con premio | >= 2 tiempos |
| `cadena_sostenidos` | melodia lenta | 3+ sostenidos seguidos |
| `respiro` | silencio | 4+ tiempos sin nota |

**La medida que mas dice no es cuantas veces sale cada uno, es la COBERTURA:**
que porcentaje de las notas del chart cae dentro de algun gesto reconocido. Un
chart con cobertura baja no es un chart dificil, es un chart **sin idioma**.

Y una regla de honestidad: los gestos **se solapan a proposito**. Una rafaga
puede ser ademas una escalera y las dos cosas son verdad. Por eso la cobertura
se cuenta sobre notas unicas y los recuentos por separado.

---

## 4. Los siete confusores (lo que te va a enganar)

Esta es la seccion que hace que el analisis valga algo. Cada uno de estos ya ha
hecho dano en proyectos parecidos, y varios se pueden comprobar en tu biblioteca
ahora mismo:

### 1. El charter, no el genero
Los 25 GH3 ripeados de **Neversoft** y los 64 de **Buldy** son las mismas
canciones charteadas por manos distintas. Si "metal" sale con mucho galope y
resulta que el 70 % del metal de la muestra lo charteo la misma persona,
**mediste a esa persona**. → Se guarda el `charter` en cada fila y todo hallazgo
se repite quitando al charter dominante. Si desaparece, era del charter.

### 2. El pack no es el genero
`10_Customs - Latin & Mexican` no es un genero, es un origen. Dentro hay cumbia,
corrido, rock urbano y pop. Sirve como control de sesgo, **no como etiqueta**.

### 3. La etiqueta de genero miente
En tu `song.ini` hay generos que dicen `M3M3S`, `Rata`, `Anime`, `Relaxing` y
`pa acabar la fiesta siono raza`. Hay `Nu-Metal` y `Nu Metal` como dos generos
distintos, y `Pop/Rock`, `Pop-Rock`, `Pop Rock` como tres. → Se normaliza a
familias (`atlas.normalizar_genero`) y **se guarda siempre la etiqueta cruda al
lado**, para poder auditar. Un patron que solo aparece en un genero mal
etiquetado no es un hallazgo, es un error de datos.

### 4. MIDI y `.chart` no miden lo mismo
- En MIDI **toda nota tiene duracion**, asi que los sostenidos dan 100 % si no
  se aplica el umbral de 0.25 tiempos (ya esta aplicado).
- Los charts venidos de MIDI llevan **desfase de autoria** de +65/+70 ms contra
  el audio.
- Las marcas de ligadura y tap no se leen igual en los dos formatos.
→ En cada fila se guarda `fuente` (midi/chart) y **cualquier diferencia entre
generos se comprueba dentro de la misma fuente** antes de creerla.

### 5. Los 110 charts que solo tienen Experto
Un tercio de la biblioteca no tiene Facil/Medio/Dificil. Cualquier analisis de
"como se reduce la dificultad" esta calculado sobre los dos tercios que si las
tienen, que son sobre todo los rips oficiales. → El analisis de dificultades se
hace **solo sobre canciones con las cuatro**, y se dice cuantas son.

### 6. Los 16 duplicados del GH3
Cada pareja es la misma cancion dos veces (Neversoft vs Buldy). Contarlas las
dos **duplica el peso de esas canciones** en cualquier media del GH3. → Se
detectan por artista+titulo y se elige una, o se cuentan con medio peso.

### 7. Las celdas vacias
`genero x instrumento x velocidad x dificultad` son cientos de celdas y tu
biblioteca son 396 canciones. Muchas celdas quedan con 2 charts. → Hay un minimo
por celda (`atlas.MINIMO_POR_GRUPO`) y **las celdas por debajo no se publican**,
no se publican "con aviso". Un numero con n=2 en una tabla se acaba citando como
si fuera cierto.

---

## 5. Como se decide que un hallazgo es real

Cuatro filtros, en este orden. Un patron que no pase los cuatro no entra al
generador:

1. **Tamano minimo.** >= 4 charts y >= 3 canciones distintas en la celda.
2. **Contraste.** No basta con que el metal tenga galope: tiene que tener
   **mas** que el resto, fuera del rango intercuartil de las demas familias.
3. **Charter ciego.** Se repite quitando al charter que mas aporte a la celda.
   Si el efecto cae mas de la mitad, era del charter y se descarta.
4. **Reserva.** Se aparta el 20 % de las canciones antes de mirar nada, y el
   hallazgo se comprueba ahi. Es la unica defensa contra encontrar patrones en
   el ruido.

Esto extiende la regla que ya esta en `CLAUDE.md`: *una sola cancion no decide
nada*. Aqui: **una sola celda tampoco.**

---

## 6. Que es "divertido", partido en seis propiedades medibles

Aqui esta el nucleo del encargo. Cada propiedad se mide aparte, tiene su cifra
en la biblioteca, y **se puede subir sin subir las otras** — que es justo lo que
permite trabajar en ellas una por una.

### 6.1 Reconocimiento — "toco lo que oigo"
Si la nota no cae donde suena, nada de lo demas importa.
- **Medida:** F1 contra el chart humano y desviacion en ms contra el ataque real.
- **Hoy:** F1 0.668 sobre 24 canciones; 100 % de las notas a < 50 ms.
- **Estado:** resuelto. Es el suelo, no el techo.

### 6.2 Vocabulario — "esto es un riff, no notas"
- **Medida:** cobertura de gestos (% de notas dentro de un lick reconocido).
- **Que hacer:** comparar la cobertura del chart generado con la del humano de
  la misma cancion. Si el generado esta muy por debajo, esta poniendo notas
  correctas sin forma.
- **Es la medida nueva mas importante de este plan.**

### 6.3 Repeticion con variacion — "el estribillo se reconoce"
Una cancion es divertida en parte porque **aprendes** un trozo y luego vuelve.
- **Medida:** autosimilitud entre compases. Cuantos compases del chart son
  repeticion exacta de otro anterior, cuantos son variacion (mismo ritmo, otro
  contorno), cuantos son nuevos. Se saca la misma tripleta del humano.
- **Hoy:** el generador ya reutiliza compases repetidos
  (`generate.reuse_repeated_bars`) pero **nadie ha medido si repite tanto como un
  humano**. Es un hueco directo.

### 6.4 Respiracion — "no me ahoga"
- **Medida:** contraste = pico/valle de la curva de densidad en 12 tramos, y
  numero de `respiro` (huecos de 4+ tiempos).
- **Por que importa:** un chart sin valles es agotador aunque su densidad media
  sea correcta. **La media puede ser perfecta y la cancion insoportable.**
- **Hoy:** el generador reparte densidad por ventana, o sea que **aplana el
  contraste a proposito**. Sospecha fuerte de que aqui hay una regresion de
  sensacion que ninguna medida actual ve.

### 6.5 Comodidad fisica — "la mano sabe donde esta"
- **Medidas:** distribucion de saltos (0/±1/±2/±3), anclas en acordes seguidos,
  cuantas veces la mano tiene que reposicionarse por minuto, y si los tramos
  rapidos caen en posiciones comodas.
- **Hoy:** los saltos de ±2 salen al 18.9 % contra el 14 % humano. Es la unica
  desviacion que quedaba abierta del plan viejo, y **este analisis la absorbe**:
  deja de ser una tarea suelta y pasa a ser una de las seis propiedades.

### 6.6 Recompensa — "aqui pasa algo"
- **Medidas:** donde caen las rafagas, los sostenidos largos y las frases de
  Star Power respecto a las secciones de la cancion. Un solo detectado en el
  audio deberia coincidir con un pico de densidad.
- **Hoy:** el Star Power se coloca en 10 frases repartidas, **sin mirar la
  musica**. Un humano lo pone donde hay algo que celebrar.

---

## 6bis. Lo que tu biblioteca ya dijo (primera pasada, 21-08-2026)

607 pistas de 396 canciones, solo Experto, 562 162 notas. `datos/atlas_patrones.json`.
**Son numeros de la fase P0: aun NO han pasado los cuatro filtros del §5.** Se
publican porque orientan, y se marcan como provisionales para que nadie los cite
como cerrados.

### Cada instrumento es otro juego

| | canc | nps | acordes | sost | ligadas | cobertura | contraste |
|---|---|---|---|---|---|---|---|
| guitarra | 393 | 3.75 | 0.36 | 0.14 | 0.14 | 0.48 | 2.8 |
| bajo | 169 | 3.35 | **0.00** | 0.24 | 0.05 | 0.32 | 2.5 |
| ritmica | 17 | **4.35** | 0.24 | 0.08 | 0.05 | **0.59** | 3.6 |
| teclado | 22 | **1.46** | 0.10 | **0.54** | 0.00 | 0.55 | **6.8** |

Lo que salta: **el bajo no tiene acordes. Cero.** Y tiene el triple de tremolo
que la guitarra (0.90 contra 0.57 por 100 notas) y **once veces menos anclas**
(0.48 contra 5.38). Un generador de bajo que copie las reglas de la guitarra
esta garantizado que se sienta mal, y ahora hay el numero que lo dice.

La ritmica es lo contrario de lo que uno supondria: **es la mas densa de todas**
(4.35 n/s) y la que mas machaca — tremolo 1.88, rafaga 1.06, anclas 5.39.

### Cada genero tiene firma propia

Veces por cada 100 notas, con la densidad al lado:

| | canc | nps | acordes | tremolo | galope | escaleras | acorde_martillo | acorde_alterno | anclado | cadena_sost |
|---|---|---|---|---|---|---|---|---|---|---|
| rock | 174 | 3.42 | 0.21 | 0.36 | 0.34 | 1.87 | 0.75 | 0.23 | 4.10 | 0.66 |
| metal | 99 | **4.30** | 0.16 | **1.17** | **0.64** | 1.96 | 0.30 | 0.17 | 3.70 | 0.53 |
| punk | 31 | 4.08 | **0.47** | 0.37 | 0.33 | **0.51** | **1.46** | 0.10 | 4.23 | 0.57 |
| latino | 28 | 2.77 | **0.48** | **0.05** | 0.54 | 1.66 | 0.85 | **0.79** | **7.28** | **1.78** |
| pop | 15 | 2.86 | 0.33 | 0.10 | 0.47 | 0.83 | 1.20 | 0.04 | 5.35 | 1.12 |
| acustico | 5 | 3.03 | 0.13 | 0.05 | 0.19 | **4.54** | 0.44 | 0.28 | 3.38 | **4.17** |
| urbano | 5 | 1.68 | 0.11 | 0.70 | 0.66 | 1.93 | 0.35 | 0.08 | 2.74 | 1.20 |

Cuatro firmas que se leen solas, y que ademas **tienen sentido musical**, que es
la primera senal de que los detectores no estan midiendo ruido:

- **Metal** = velocidad + tremolo + galope. Lo mas rapido (4.30 n/s), el triple
  de tremolo que el rock y el doble de galope. Y **pocos acordes** (0.16): la
  solista de metal es de nota suelta.
- **Punk** = acordes rapidos y **casi ninguna escalera** (0.51 contra 1.96 del
  metal). Power chords a toda velocidad; la mano no corre, machaca.
- **Latino** = **el mas anclado de todos con diferencia** (7.28), acorde alterno
  x3 sobre cualquiera (0.79) y cadenas de sostenidos. Es el vamp de la cumbia y
  el corrido descrito en numeros. Y **el tremolo casi no existe** (0.05).
- **Acustico** = escaleras (4.54, el doble del metal) y cadenas de sostenidos
  (4.17, x6 sobre la media). Es lo que se siente al puntear.

**Cuidado con las cuatro ultimas filas:** pop 15, latino 28, acustico 5 y urbano
5 canciones. Acustico y urbano **estan por debajo del minimo del §5** y no deben
usarse para nada hasta que crezcan. Metal y rock si aguantan.

### La biblioteca entera, para tener referencia

Cobertura de vocabulario p50 **0.46** (p5 0.13, p95 0.80): en la mitad de los
charts humanos, menos de la mitad de las notas cae dentro de un gesto
reconocible. **Eso baja el liston de lo que hay que pedirle al generador** — y es
justo la clase de numero que uno se inventaria mal si no lo midiera.

Contraste de densidad p50 **2.84**, p95 12.58. Reparto ritmico: corchea 44.8 %,
semicorchea 24.5 %, negra 9.5 %. El giro de 4 golpes mas repetido es corchea
recta (27.2 %) y el segundo semicorchea recta (15.0 %). Movimiento de mano: el
28.3 % de los tresillos de pasos es `+0,+0` — **quedarse quieto es el gesto mas
comun de todos**, lo que confirma por otra via lo que ya se habia medido con las
repeticiones de traste.

### Un aviso sobre las abiertas

Salen a 0 % en todos los percentiles. **No es un fallo de lectura**: solo 15 de
167 `.chart` usan notas abiertas y ningun `.mid` de la biblioteca las trae. El
`abierta_bombeo` (0.01 por 100 notas) esta medido sobre casi nada, y cualquier
conclusion sobre chug moderno con abiertas no tiene datos detras.

---

## 7. Fases, con entregable y control

Cada fase deja un numero. Ninguna se da por buena sin el.

| Fase | Que se hace | Entregable | Control |
|---|---|---|---|
| **P0 ✅** | vocabulario de 16 gestos + atlas por genero/instrumento/velocidad | `datos/atlas_patrones.json` | 607 pistas de 396 canciones |
| **P1** | aplicar los 4 filtros del §5 y publicar solo lo que sobreviva | `docs/HALLAZGOS_PATRONES.md` | cada hallazgo con n, contraste y charter-ciego |
| **P2 ✅** | medir el chart GENERADO con la misma vara | `tools/comparar_atlas.py`, 6 canciones | acordes s=0.000 contra s=0.229 humano; contraste <p5 en las 6; ver `DECISIONES_MEDIDAS.md` §10 |
| **P3** | arquitectura: secciones del audio -> curva de densidad objetivo | `generate.thin` deja de aplanar | contraste 1.2 -> p25-p75 humano (1.9-4.5) y respiros > 0 |
| **P3b** | caracter por cancion: acordes y sostenidos salen del audio, no de la mediana | `target_ratio` deja de ser global | desviacion de acordes 0.000 -> acercarse a 0.229 |
| **P4** | vocabulario dirigido: elegir gestos segun genero detectado | motivos por familia | cobertura sube sin que el banco baje de 0.668 |
| **P5** | bajo y ritmica como generadores propios | `generadores/` | banco por instrumento |

**El orden no es negociable.** P2 antes que P3 y P4 porque **hasta que no midas
el chart generado con la misma vara que el humano, no sabes que te falta.** Hoy
sabemos como es un chart humano y no sabemos como es el nuestro en estas
medidas: eso es lo primero que hay que arreglar, y es barato.

---

## 8. Como entra esto en el generador

En este orden, y cada paso con la puerta del banco:

1. **Como aviso** (`validate.py`): si un chart generado tiene cobertura de
   gestos por debajo del p5 humano de su familia, se avisa. Sin cambiar nada
   mas. Barato y ya dice si el generador tiene idioma.
2. **Como objetivo de curva** (P3): la densidad por ventana deja de ser plana y
   copia la forma de la curva humana del genero.
3. **Como banco de motivos por familia** (P4): `generate._motif_bank` ya lee
   trigramas del corpus; pasa a leerlos de la fila del genero detectado.
4. **Como colocacion de premios** (P6): Star Power y rafagas se colocan donde
   el audio dice que hay solo o estribillo.

---

## 9. Lo que este analisis NO va a poder decir

Escrito a proposito, para que no se gaste una tanda en ello:

- **No dice si una cancion es divertida de escuchar.** Solo de tocar.
- **No detecta la afinacion ni la armonia.** Un chart de 5 trastes no guarda
  notas reales; `+1` de carril puede ser un semitono o una quinta.
- **No distingue un chart bueno de uno famoso.** Si tu biblioteca tiene 89
  canciones del GH3, el "gusto medio" se parecera al GH3. Eso no es un fallo,
  es tu biblioteca — pero hay que saberlo al leer cualquier media global.
- **No sabe lo que tu no tienes.** No hay jazz, ni progresivo denso, ni djent.
  Cualquier cosa que se genere en esos estilos sale extrapolada.
