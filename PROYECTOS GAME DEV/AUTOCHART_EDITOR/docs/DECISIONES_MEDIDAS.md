# Por que el generador hace lo que hace

Historial de decisiones, **con los numeros que las justifican**. Esto NO hace
falta leerlo para trabajar: se consulta cuando vas a tocar una de estas partes,
o cuando se te ocurre una idea y quieres saber si ya se probo.

La entrada del proyecto es `SIGUIENTE_CHAT.md`. Las reglas de como trabajar aqui
estan en `CLAUDE.md`, en la raiz.

**Lo que mas vale de este documento son las ideas MEDIDAS Y DESCARTADAS.** Suenan
todas razonables; por eso se probaron. Si se te ocurre una, busca aqui antes de
gastar una tanda en ella:

| Idea | Veredicto |
|---|---|
| Normalizar el contorno por percentiles en vez de min/max | **Peor**: hasta 43 pp de error |
| Que el chart descanse cuando descansa el guitarrista | **Falso**: Experto humano casi no descansa (2.5 % de compases vacios) |
| Detectar los ataques solo en la banda de la solista | **Peor** en 5 de 6 canciones (F1 0.684 contra 0.683) |
| Deducir del audio cuanto sostiene cada cancion | **No hay senal**: va al reves del ratio humano |
| Separar la guitarra con Demucs | **Despriorizado**: forzando la mezcla el F1 solo baja de 0.648 a 0.618 |
| Escribir taps (`N 6`) | **No lo hace el humano**: mediana de 0 por chart, solo el 26 % pone alguno |
| Marcar todos los casos elegibles de ligadura | **Cinco veces** mas marcas que una persona: la tasa humana es 8-21 %, no 100 % |

---

## 7bis. Lo que el validador NO veia, y el juego si (06-08-2026)

`autochart revisar` mira si el chart es musicalmente sano. No miraba nada de lo
que hace falta para **jugarlo entero**. Seis fallos, los seis medidos contra la
biblioteca, los seis arreglados:

| | Antes | Humano (250 charts) | Ahora |
|---|---|---|---|
| Ultima nota vs fin del audio | +1.0 a +2.1 s **por fuera** | — | dentro |
| Primera nota | 0.44–0.58 s | p5 **2.0 s**, p50 3.7 | ≥ 1.0 s |
| Frases de SP en Facil/Medio | **0** | p50 **10** en las cuatro | 10 |
| Frases de SP en Experto | 4–6 | p50 10 | 10 |
| Sostenido p50 en Facil | **3.78** tiempos | **0.80** | 1.78 |
| Traste compartido con Experto (Dificil) | 59–75 % | p50 **91 %** | 100 % |

Las tres primeras se pierden notas de verdad jugando: la cancion acababa con un
sostenido a medias, y la primera nota aparecia ya encima de la linea.

Y **las cinco filas de `DIFFICULTY_SPECS` estaban puestas a ojo.** Medidas contra
su propio Experto en 250 charts humanos emparejados:

| | densidad (antes → medida) | acordes | sostenidos |
|---|---|---|---|
| Dificil | 0.66 → **0.865** | 0.70 → **0.999** | 1.25 → 1.133 |
| Medio | 0.42 → **0.641** | 0.38 → **0.716** | 1.60 → 1.499 |
| Facil | 0.24 → **0.457** | 0.16 → **0.013** | 2.10 → 2.051 |

Facil estaba a la mitad de densidad de lo que chartea un humano, y le metia
acordes donde el humano no pone practicamente ninguno (0.3 % de las notas).

**La tarea que estaba escrita aqui partia de una premisa falsa.** Decia que
Facil no era un subconjunto de Experto. Medido antes de tocar nada: el **100 %**
de las notas de Facil ya caian en un tick de Experto (el humano esta en 99.5 %).
Lo que no coincidia era el **traste**, y eso es lo que se arreglo heredandolo.

Herramienta nueva: `python tools/revisar_in_game.py salida` — comprueba lo que
mira el juego (carga, principio, final, Star Power, parecido con Experto).

## 7ter. Por que se sentia de acompanamiento (06-08-2026)

Bruno lo dijo asi: "que se sienta que se toca la guitarra principal y no
acompanamiento". No era una impresion, se podia medir.

El contorno de trastes lo decidia el bin mas fuerte del CQT desde E2 hacia
arriba. En su cancion, **el 61 % de los tonos caia por debajo de MIDI 52** (E3):
el bajo y el chug grave. Las notas mas repetidas eran A2, E2, G2, C3. El chart
seguia la linea del bajo, y por eso se sentia de acompanamiento.

Dos cambios:

1. **El tono se busca en el registro de la solista** (MIDI 55-96, de G3 para
   arriba). Si ahi arriba no suena nada, el ataque se queda sin tono y el
   generador interpola o tira de motivo del corpus -- mejor eso que copiar el
   bajo. Resultado: mediana de MIDI 48 -> **61.5**, y **0 %** por debajo de 52.
2. **El filtro de densidad prefiere los ataques donde suena la solista**
   (`Onset.lead`, cuanto manda la banda melodica sobre la grave). Sin eso, el
   filtro se quedaba con los golpes mas fuertes, que en una mezcla son la
   bateria.

Seguir la solista destapo un segundo problema: la melodia real tiene mucho mas
rango que el drone grave de antes, y el mapeo la esparcia por los cinco
carriles. **Se arreglo cambiando lo que se mapea.**

Antes: tono absoluto -> carril, con el minimo y el maximo de una ventana movil.
Es un mapeo **sin memoria**, y dos notas seguidas con tonos moderadamente
distintos caian a dos carriles de distancia.

Ahora: **intervalo -> cambio de carril**. El corpus no dice donde pone la mano
un humano, dice cuanto la mueve. Los umbrales salen de la distribucion de
intervalos de la propia cancion, cortada por los acumulados 38/85/95 (calibrados
sobre dos canciones, una electronica y una de metal; los del corpus tal cual,
31/78/92, no son los mejores porque `assign_frets` retoca despues).

| movimiento | antes | ahora | humano |
|---|---|---|---|
| se queda | 23.5 % | 27.5 % | 31 % |
| ±1 | 42.4 % | 50.5 % | 47 % |
| ±2 | **25.8 %** | **18.9 %** | **14 %** |
| ±3 | 6.1 % | 3.1 % | 6 % |
| **error total** | **23.9 pp** | **14.8 pp** | — |

En *Keelhauled* el error baja de 30.2 a 10.2 pp. Y las formas de tres notas
repetidas pasan de dispersas (101 x9, 111 x9, 210 x8) a de riff:
**121 x17, 112 x16, 111 x15, 232 x13**.

Probado y descartado: normalizar por percentiles en vez de min/max **lo empeora**
(hasta 43 pp de error), porque recortar el rango manda mas notas a los carriles
de los extremos. Ensanchar la ventana apenas hace nada (23.9 -> 22.1).

## 7quater. Tocar frases, no notas sueltas (09-08-2026)

Tercera vuelta sobre "que se sienta que tocas el instrumento principal". Lo que
faltaba: **un guitarrista toca tramos**. Acompana un rato a acordes y luego hace
una linea melodica. El generador puntuaba cada nota por su cuenta y decidia si
era acorde, asi que los acordes salian salpicados entre las sueltas.

Medido en 120 charts humanos (Experto), longitud media de las rachas:

| | antes | ahora | humano |
|---|---|---|---|
| acordes seguidos | 1.58 | **5.31** | 4.76 |
| notas sueltas seguidas | 2.97 | **10.00** | 10.51 |

Arreglo: la puntuacion de acorde se **suaviza sobre 8 notas** antes de cortar
(`CHORD_RUN_WINDOW`), lo que produce tramos en vez de puntos sueltos. Y la
puntuacion ahora resta `lead`: donde manda la banda melodica van notas sueltas
(es la linea), donde no, van acordes (esta acompanando). La ventana se calibro
sobre dos canciones y las dos coincidieron en 8.

**Y dentro del tramo, la postura se mantiene.** Segunda medida sobre los mismos
120 charts: cuando un acorde sigue a otro, el humano repite la **misma forma
exacta el 61.8 %** de las veces, la misma desplazada el 13.3 %, y cambia de
postura el 24.9 %. Sorteando una forma nueva cada vez salia un 15.2 % de
repeticion -- cinco acordes seguidos de formas al azar no suenan a riff.

| | antes | ahora | humano |
|---|---|---|---|
| misma forma exacta | 15.2 % | **55-64 %** | 61.8 % |
| misma desplazada | 29.1 % | 13-17 % | 13.3 % |
| forma distinta | 55.6 % | 23-29 % | 24.9 % |

`CHORD_SHAPE_KEEP = 1.0` (mantener si el carril cabe en la postura) y
`CHORD_SHAPE_SHIFT = 0.08` (desplazarla cuando no cabe; el resto de las veces se
cambia de postura, que es lo que hace el humano). Desplazar siempre daba un 33 %
de acordes desplazados contra el 13.3 % humano.

**Un fallo que salio de aqui y lo canto el validador:** guardando como postura
heredada el acorde YA engordado a tres notas, cada vuelta le anadia una mas y
salian **acordes de cinco**. La postura que se hereda es la base.

### Dos cosas medidas y DESCARTADAS -- no las repitas

1. **Hacer que el chart descanse cuando descansa el guitarrista.** Sonaba
   evidente y es falso: en 120 charts humanos, Experto casi no descansa
   (mediana **2.5 %** de compases vacios, racha mas larga de 1 compas). No hay
   nada que ganar ahi.
2. **Detectar los ataques solo en la banda de la solista** (en vez de en todo el
   espectro). Medido sobre 6 canciones con chart humano: el espectro completo
   gana en 5.

   | banda | F1 medio (6 canciones) |
   |---|---|
   | **todo (actual)** | **0.684** |
   | 300-2500 Hz | 0.683 |
   | 200-3000 Hz | 0.681 |

   La seleccion de instrumento ya la hace la etapa de densidad con `Onset.lead`;
   recortar la banda solo pierde informacion. El parametro `onset_band` se queda
   en `audio.analyse()` para poder repetir el experimento, pero por defecto va a
   `None`.

## 7quinquies. Las canciones rapidas ya no salen secas (09-08-2026)

`SUSTAIN_MIN_GAP_S = 0.45` era un umbral **en segundos** sobre una relacion
musical. A 151 BPM un tiempo dura 0.396 s, asi que pedia un hueco de 1.14
tiempos, y en una cancion densa casi ninguna nota lo tiene. A 90 BPM el mismo
umbral pide 0.67 tiempos. O sea: **cuanto mas rapida la cancion, menos
sostenidos** -- justo al reves de lo que hacen los humanos.

Ahora manda el menor de los dos: 0.45 s **o** 0.5 tiempos
(`SUSTAIN_MIN_GAP_BEATS`).

| Experto, sostenidos | antes | ahora | humano de esa cancion |
|---|---|---|---|
| *Teddy Picker* (151 BPM) | **0.2 %** | **14.9 %** | 12.9 % |
| *Keelhauled* (110 BPM) | 14.1 % | 14.5 % | 37.0 % |
| *Cyber Club* (126 BPM) | 15.2 % | 15.2 % | — |

*Teddy Picker* estaba por debajo del p5 humano (2.9 %) y el validador lo cantaba;
ahora esta en la mediana del corpus (15.2 %) y no queda ni un aviso.

**Cuidado al medir esto:** el corpus solo cuenta como sostenido lo que dura
**>= 0.25 tiempos** (`corpus.py:116`). Sin ese umbral, un chart venido de `.mid`
da el **100 %** de sostenidos, porque en MIDI toda nota tiene duracion. Casi
calibro contra ese 100 %.

### Medido y descartado

*Keelhauled* se queda en 14.5 % contra el 37 % de su charter. Se probo deducir
del audio cuanto sostiene cada cancion, y **no hay senal**: la proporcion de
notas que podrian aguantar un sostenido va al reves del ratio humano
(*Teddy Picker* 85.5 % de notas capaces y su humano pone 12.9 %; *Keelhauled*
71 % y su humano pone 37 %). El `ring` mediano si va en la direccion correcta
(0.89 s frente a 5.99 s) pero el de *Keelhauled* esta saturado en el tope de
`RING_MAX_S`, asi que no mide nada. Se sigue apuntando a la mediana del corpus,
que es la filosofia del proyecto; 14.5 % cae de lleno en el rango humano
(p5-p95 = 2.9-97 %).

## 7sexies. Las ligaduras: que se toca sin rasguear (10-08-2026)

Hasta hoy el chart no escribia **ni una** marca: el juego ligaba lo que caia
junto y no ligaba nada de lo que caia separado. Un humano no hace eso, y es lo
que mas se nota en la mano -- decide si un tramo se toca con la izquierda sola o
hay que rasguear cada nota.

**Antes de medir nada hubo que arreglar la medida, porque la que habia estaba
mal.** La cifra que arrastraban `PLAN.md` y `SIGUIENTE_CHAT.md` -- «HOPO natural
p25 12.8 %, p50 34.2 %, p75 58.4 %» -- no es la ligadura: es **proximidad**, o
sea cuantas notas caen cerca de la anterior, sin aplicar las dos reglas que el
juego si aplica (un acorde no liga nunca, y el mismo traste repetido tampoco).
Reproducida tal cual da 11.8 / 32.6 / 59.6, que es de donde salio. Aplicando la
regla del juego (`chartio.is_natural_hopo`, copiada de Moonscraper: 65 ticks a
resolucion 192) la ligadura natural humana es **menos de la mitad**:

| Experto, 254 charts `.chart` | p5 | p25 | p50 | p75 | p95 |
|---|---|---|---|---|---|
| ligadura natural (sin marcas) | 0.2 % | 5.0 % | **14.0 %** | 30.0 % | 63.2 % |
| **ligadura real (con marcas)** | 1.2 % | 7.5 % | **17.2 %** | 37.2 % | 68.4 % |

Y la otra cifra que estaba mal: «44.838 notas forzadas» son **todas las pistas y
todos los instrumentos** (bajo, rhythm, las cuatro dificultades). En la pista que
importa, `ExpertSingle`, son **13.524** -- mediana de 20 por chart, no 176.

**Para que usa un humano las marcas** (13.524 forzados, 254 charts):

| | |
|---|---|
| cortar una ligadura que el juego haria sola | 6.856 (50.7 %) |
| ligar dos notas que el juego dejaria sueltas | 6.668 (49.3 %) |
| hueco al ligar | **0.50 tiempos en p25, p50 y p75** |
| rachas de marcas seguidas | 76 % van solas |

O sea: casi todas las ligaduras escritas son **la corchea recta**, que es
justo el hueco que el juego no liga solo. No es un umbral elegido, es una sola
cosa repetida 6.668 veces.

**Lo que decide cuando marcar no son los totales, son las tasas base** -- de cada
cien sitios donde PODRIA marcar, en cuantos marca:

| caso | elegibles | marcados | tasa |
|---|---|---|---|
| cortar la **primera** nota de una racha ligada | 18.905 | 4.046 | **21.4 %** |
| cortar una de en medio | 50.979 | 2.810 | 5.5 % |
| ligar, la mano se mueve **un** carril | 28.529 | 3.406 | **11.9 %** |
| ligar, dos carriles | 11.550 | 614 | 5.3 % |
| ligar, tres o mas | 6.645 | 189 | 2.8 % |
| ligar despues de un acorde | 9.113 | 385 | 4.2 % |

Las dos cosas que dicen esas tasas tienen sentido fisico. Se rasguea **la nota
que abre la frase** y se liga el resto (cortar la primera es cuatro veces mas
frecuente que cortar una de en medio). Y se liga cuando **la mano apenas se
mueve**, que es la definicion de un martilleo: no vuelves a picar la cuerda
porque el dedo solo cambia un traste.

Estan puestas como sorteo (`FORCE_CUT_RUN_START`, `FORCE_LINK_STEP1`... en
`generate.py`) y no como regla fija **porque el humano tampoco marca siempre**:
marcar todos los casos elegibles daria cinco veces mas marcas que una persona, y
un chart donde toda corchea esta ligada se toca tan plano como uno donde no lo
esta ninguna.

Resultado, con el corpus al lado:

| Experto | golpes | ligadas | marcas | corta / liga |
|---|---|---|---|---|
| *Keelhauled* | 745 | 12.5 % -> **11.9 %** | 30 (4.0 %) | 17 / 13 |
| *Teddy Picker* | 622 | 2.1 % -> **4.3 %** | 20 (3.2 %) | 3 / 17 |
| *Cyber Club* | 536 | 22.4 % -> **18.7 %** | 24 (4.5 %) | 22 / 2 |
| **humano** | — | **p50 17.2 %** | **p50 3.0 %** | 50.7 / 49.3 |

El reparto entre cortar y ligar **lo decide la cancion**, no un parametro: donde
ya hay muchas ligaduras naturales (*Cyber Club*) casi todo son cortes, y donde
no hay ninguna (*Teddy Picker*) casi todo son ligaduras.

Sobre las **24 del banco**, que es la muestra que vale: ligadura p50 **10.7 %**
(p5 6.9, p95 16.2), **874 marcas = 4.1 %** de las notas contra el 3.0 % humano,
42.9 % cortes contra 50.7 %, **0 acordes ligados y 0 taps**. Las 24 caen dentro
del rango humano p5-p95 y ninguna se queda sin marcas.

Lo que **no** iguala: el reparto sale mucho mas apretado que el humano (6.9-16.2
frente a 1.2-68.4). No es un fallo del marcado sino de lo que hay debajo -- el
chart generado tiene una rejilla mas regular que uno escrito a mano, asi que hay
menos rachas rapidas que ligar. Subir la tasa de marcado para tapar eso seria
inventarse notas ligadas donde el humano no tiene ni el hueco.

**El control no se movio ni una milesima**: f1_medio 0.668, mediana 0.656,
recall 0.701, precision 0.656, nps 3.63, 0 errores, `nps_humano_medio` 3.77.
Identico al del 09-08, que es exactamente lo que tenia que pasar: una marca no
mueve ninguna nota de sitio.

### Tres cosas que NO se escriben, y son decision, no olvido

1. **Taps (`N 6`).** La mediana de la biblioteca es **cero** por chart: solo el
   26 % de los charts pone alguno, y ahi se concentran (p50 de 28 en los que
   ponen). Escribirlos seria inventarse un idioma que tres de cada cuatro
   charters no usan.
2. **Acordes ligados.** El humano los escribe 918 veces, pero el juego no los
   liga nunca por su cuenta y es un gesto avanzado. Sin tasa base medida, se
   deja fuera.
3. **Repetir traste ligado.** Cero casos de 6.668. No se puede martillear una
   nota que ya estaba pulsada -- y esto no es criterio, es que el humano no lo
   hace *ni una vez*.

### Lo que queda corto

`EasySingle` sale con **0 marcas** en las tres canciones; el humano pone unas 5.
A 1.4 notas/s y con `min_gap` de 0.98 tiempos no queda ni un hueco de corchea ni
una ligadura natural que cortar, asi que no hay donde marcar. Es consecuencia de
lo regular que sale Facil, no de la regla de marcado.

**Y una trampa de implementacion que costaria una comparacion falsa:** las marcas
se sortean en su **propia** tirada de dados (`random.Random(seed + 1009 * n)`).
Saliendo de la comun, anadirlas corre el sorteo de las dificultades siguientes y
les cambia los trastes -- el banco mediria dos cambios creyendo que mide uno.
Con la tirada aparte, las notas de las tres canciones son **las mismas de ayer**,
gema por gema.



## 8. Cuanto se parecia a una mano humana (09/10-08-2026)

Movido aqui desde `SIGUIENTE_CHAT.md` el 21-08-2026: es una foto de una
medida, o sea material de consulta, no de lectura al arrancar.

**Cuanto se parece a una mano humana** (Experto, contra 120 charts de la
biblioteca). Estas son las metricas que el banco NO ve y que deciden si se
siente que tocas la guitarra principal:

| | generado | humano |
|---|---|---|
| tono en la zona del bajo (< MIDI 52) | **0 %** | — |
| se queda en el mismo traste | 27.5 % | 31 % |
| salto de ±1 | 50.5 % | 47 % |
| salto de ±2 | 18.9 % | 14 % |
| acordes seguidos | 5.2–7.2 | 4.76 |
| notas sueltas seguidas | 9.7–13.5 | 10.51 |
| misma forma de acorde encadenada | 55–64 % | 61.8 % |
| sostenidos en Experto | 14.5–15.2 % | 15.2 % (mediana del corpus) |
| notas que se tocan ligadas | p50 10.7 % | p50 17.2 % (p25 7.5, p75 37.2) |
| marcas de forzado | 4.1 % de las notas | 3.0 % |
| de esas, cuantas cortan | 42.9 % | 50.7 % |
| acordes ligados / taps | 0 / 0 | raro / mediana 0 |

Ligaduras sobre las 24 del banco: **las 24 dentro del rango humano** y ninguna
sin marcas, pero mas apretadas que las humanas (6.9–16.2 % contra 1.2–68.4 %),
porque el chart generado es mas regular que uno escrito a mano.


## 9. Las trampas de las herramientas de medida, con sus numeros

Movido aqui desde `SIGUIENTE_CHAT.md` el 21-08-2026. Las cinco en corto
estan en `CLAUDE.md` seccion 2, que es lo que se lee al arrancar; esto es
el detalle con las tablas, que se consulta cuando toca medir.

**Leer esto antes de tocar nada**, porque las dos llevan a trabajar en balde.

1. **El banco no ve los trastes.** El F1 compara *cuando* suena cada nota, no
   *que traste* le toca. Medido: subir las repeticiones de traste del 12.5 % al
   24.5 % dejo el F1 clavado en 0.648, con el mismo recall y la misma precision.
   Cualquier trabajo sobre el patron hay que juzgarlo con `tools/ver_patron.py`
   y las distribuciones del corpus, no con el banco.
2. **El F1 premia pasarse de notas.** Sobre 24 canciones donde el humano esta en
   3.77 notas/s: p50 → F1 0.666 con 3.64 n/s; p75 → 0.685 con 4.22; p95 → 0.692
   con 5.10. Sube monotonamente hasta un 35 % por encima de lo humano, porque
   cada nota de mas cae sobre un ataque real. La densidad la decide el parecido
   con la distribucion humana, no el F1.

Y una tercera, de metodo: **la muestra de 16 canciones esta sesgada hacia lo
denso** (humano 4.16 n/s) frente a la de 24 (3.77). Cualquier decision tomada
con una sola muestra hay que repetirla con otra antes de creersela.

**Y una cuarta, que costo una conclusion falsa el 06-08-2026:** `pick_songs`
coge una carpeta de cada N de la biblioteca, asi que **copiar un solo chart
generado a `Songs\` cambia las 24 canciones de la muestra**. Una tirada dio F1
0.641 contra 0.668 y parecia una regresion del generador; era la muestra (el
nps humano habia pasado de 3.77 a 3.37, que es la senal de que el conjunto
cambio). Ya esta arreglado -- `banco.py:is_generated()` salta las carpetas de
AutoChart -- pero la leccion vale: **si el nps humano se mueve, no estas
comparando lo mismo.**


## 10. El generador no chartea la cancion: chartea la MEDIA (21-08-2026)

Fase P2 de `PLAN_PATRONES.md`, con `tools/comparar_atlas.py`. Seis canciones
generadas que conservan su chart humano en la biblioteca, medidas **con la misma
funcion** que el humano (`atlas.medir_pista`), Experto y guitarra.

### El numero que lo explica todo

| | generado (min-max, desv) | humano (min-max, desv) |
|---|---|---|
| acordes | **0.35-0.35 (s=0.000)** | 0.00-0.77 (s=0.229) |
| sostenidos | **0.15-0.15 (s=0.001)** | 0.00-0.76 (s=0.309) |
| notas/s | 2.94-3.84 (s=0.374) | 1.67-5.94 (s=1.345) |
| contraste | 1.04-1.24 (s=0.075) | 1.13-3.84 (s=0.894) |
| cobertura de gestos | 0.24-0.53 (s=0.099) | 0.29-0.86 (s=0.191) |

**La desviacion de los acordes es CERO.** El generador escribe 34.7-34.8 % de
acordes y 15.1-15.3 % de sostenidos en las seis canciones, sean lo que sean:

| cancion | genero | acordes hum. | sost. hum. | lo nuestro |
|---|---|---|---|---|
| Dethklok - Thunderhorse | metal | **0.00** | **0.76** | 0.35 / 0.15 |
| Pesado - Ojala Que Te Mueras | latino | **0.77** | **0.74** | 0.35 / 0.15 |
| Blur - Song 2 | rock | 0.39 | **0.00** | 0.35 / 0.15 |
| Blink-182 - What's My Age Again | punk | 0.40 | 0.09 | 0.35 / 0.15 |
| Arctic Monkeys - Teddy Picker | rock | 0.22 | 0.17 | 0.35 / 0.15 |
| Superbus - Radio Song | pop | 0.34 | 0.17 | 0.35 / 0.15 |

Thunderhorse es un solo de nota suelta con sostenidos largos y le ponemos un
tercio de acordes. *Ojala Que Te Mueras* son acordes casi todo el rato y le
quitamos la mitad. **Apuntar a la mediana del corpus no es apuntar a la
cancion**: `target_ratio` lee el percentil global y lo aplica igual a todo.

Y explica la paradoja del proyecto: se puede tener F1 0.668 (las notas caen
donde suena) y aun asi no sentirse la cancion, porque **acertar CUANDO no es
acertar QUE**.

### Lo segundo: no respiramos nunca

`respiro` (hueco de 4+ tiempos) = **0.00 por 100 notas en las SEIS**, contra
0.70 del humano. Y el contraste pico/valle sale **por debajo del p5 humano en
las seis** (1.2 de media contra 2.0). La causa esta localizada: `thin` reparte
la densidad por ventana, o sea que **aplana el contraste a proposito**. La
sospecha estaba escrita antes de medir y se confirma entera.

### El resto de la tabla, media de las 6

| | generado | humano | |
|---|---|---|---|
| notas/s | 3.45 | 3.94 | cerca |
| dentro de un gesto | 0.37 | 0.56 | **-0.18** |
| anclado /100 | 7.43 | 3.01 | nos sobra x2.5 |
| galope /100 | 1.82 | 0.63 | nos sobra x2.9 |
| salto_ancho /100 | 1.92 | 4.29 | nos falta |
| acorde_martillo /100 | 0.37 | 1.33 | nos falta |
| sostenido_largo /100 | 0.19 | 0.94 | nos falta |

Ojo con `salto_ancho`: **nos falta**, y son saltos de 3+ carriles. No contradice
la desviacion conocida de +-2 carriles al 18.9 %; son dos cosas distintas y
conviene no confundirlas al arreglar una.

### En que SI es bueno, medido

- **Donde caen las notas.** 100 % de las notas a menos de 50 ms del ataque real,
  media 14.9 ms; F1 0.668 contra el humano sobre 24 canciones.
- **La densidad global.** 3.45 contra 3.94, y las seis caen en p50-p75.
- **Que el juego lo cargue y se pueda jugar entero.** Las cuatro dificultades,
  10 frases de Star Power, 0 errores de validacion.

O sea: **la sincronia y el esqueleto estan resueltos; lo que falta es el
caracter.** Que es exactamente lo que este atlas hace medible.

### Y un fallo real que salio de paso

Generar reventaba con `WinError 123` en cualquier cancion cuyo titulo llevara
`? : * " < > | \ /`, porque el nombre de la carpeta sale del `name` de
`song.ini` y ahi los caracteres estan **sin sustituir** (la carpeta de la
biblioteca si los tiene cambiados, por eso no se habia visto). Arreglado con
`export.nombre_seguro`, que ademas cubre los nombres reservados de Windows
(`CON`, `NUL`, `COM1`...) y los que acaban en punto.



## 11. La letra como mapa de la cancion: MEDIDO Y DESCARTADO (22-08-2026)

**La idea.** Hay 332 canciones con la voz alineada silaba a silaba. Parecia
informacion gratis para el problema que quedaba abierto: el chart ya sube y baja
como uno humano (contraste 2.5-2.6) pero **no sabe DONDE subir** -- la
correlacion entre nuestra curva de densidad y la humana era **0.25**.

La hipotesis: donde nadie canta y la cancion sigue sonando hay solo o riff, y es
ahi donde un humano carga la mano.

**Lo que salio.** Se implemento como un multiplicador del presupuesto de notas
por ventana en `thin`, y se midio con la correlacion de forma de
`tools/comparar_atlas.py` sobre 5 canciones de estilos distintos:

| | forma media | por cancion |
|---|---|---|
| sin mapa (control) | **0.25** | 0.77 / 0.27 / 0.25 / -0.18 / ... |
| cargando donde NO se canta (1.35 / 0.85) | **0.18** | 0.70 / 0.62 / 0.30 / -0.10 / -0.62 |
| cargando donde SI se canta (1.15 / 0.88) | **-0.05** | 0.72 / 0.21 / -0.05 / -0.20 / -0.26 |

**Empeora en las dos direcciones**, o sea que no es un problema de ajustar el
numero: la premisa esta mal. Y se entiende al mirarlo: los huecos sin canto no
son solos, son sobre todo **intros y finales**, que es justo donde el humano
pone MENOS notas. Un tramo instrumental de 8 tiempos no distingue un solo de
guitarra de cuatro compases de silencio con un pad de fondo.

**Lo que habria que hacer si se retoma:** no basta con saber que no se canta;
hay que saber si en ese hueco **la guitarra esta haciendo algo**. Eso ya se mide
por ataque (`lead`), asi que la senal seria "sin canto **Y** con lead alto", no
"sin canto". Pero eso es otra tanda y hay que medirla igual que esta.

**Lo que SI queda de aqui:** la propia medida. `comparar_atlas` ahora saca la
correlacion de forma, que es lo que permitio ver que esto no funcionaba en vez
de darlo por bueno porque sonaba razonable.

---

## Alinear la letra con el audio (22-08-2026, tarde)

El plan `PLAN_PRECISION.md` puso un objetivo antes de escribir el codigo: bajar
el error de colocacion de silabas de **148 ms a menos de 60 ms**. El codigo se
escribio y **nunca se llego a correr**. Corrido, salia **177 ms: peor que no
hacer nada**. Lo que sigue es lo que se midio para averiguar por que.

### Lo que SI funciono: buscar el canto en el stem de voz

De 398 carpetas, **101 traen `vocals` aparte**, y el banco estaba midiendo sobre
`song` porque `mezcla_de()` probaba `song` primero. En la mezcla, la banda de
200-4000 Hz la llenan la bateria y la guitarra: el detector encontraba **2664
arranques en Pull Me Under** y 1411 en Carolina, que no son silabas.

| | mediana | p75 | p95 |
|---|---|---|---|
| reparto a ojo (control) | 151 ms | 286 ms | 597 ms |
| alineado sobre la mezcla | 177 ms | 286 ms | 613 ms |
| **alineado sobre el stem de voz** | **117 ms** | 284 ms | 591 ms |

**23 % mejor que el control**, y por longitud de linea: 3-5 silabas 87 ms,
**6-8 silabas 55 ms (objetivo cumplido)**, 9-11 127 ms, 12-14 162 ms.

Es la misma leccion que ya estaba escrita para el pulso (se busca en la mezcla)
y las notas (en el stem de guitarra), sin aplicar a la voz.

### La vara es buena: el humano SI esta donde se canta

Antes de seguir afinando habia que saber si el MIDI humano vale como juez, dado
que este proyecto ya tiene medido un desfase de autoria de +65/+70 ms en los
charts venidos de `.mid`. Medido sobre 4017 silabas humanas, distancia al
arranque de canto mas cercano del stem:

**mediana 22 ms, y solo el 13 % a mas de 60 ms.** Por cancion, entre 18 y 29 ms.

Dos conclusiones que mandan sobre lo que venga:

1. **El detector de arranques funciona.** El arranque bueno esta ahi, a 22 ms.
2. **El fallo no es detectar, es elegir.** Con el arranque correcto disponible y
   un error de 117 ms, lo que falla es el emparejador. El techo de esta via es
   ~22-30 ms, o sea que **los 60 ms son alcanzables** y merece la pena seguir.

### Tres cosas que parecian razonables y estan DESCARTADAS con numero

| Idea | Por que parecia buena | Medido | Veredicto |
|---|---|---|---|
| Descontar el desfase de autoria de cada cancion | El proyecto ya lo tiene medido en las notas (+65/+70 ms) | 117 -> **134 ms**, empeora. Solo 3 de 10 canciones tienen sesgo real (Bon Jovi +179, Pull Me Under +165, La Bamba +111); las otras 7 estan en +-24 ms | **NO.** No hay sesgo comun que descontar; restarlo mete ruido |
| Podar candidatos: dejar solo los K arranques mas fuertes por silaba | Con 40 candidatos para 8 silabas el coste no distingue el bueno | La mediana de candidatos por silaba **ya es 1,5** (maximo 11). Con tope 1,5x: 112 ms; con 1x: 121 ms; sin tope: 117 ms | **NO.** No sobran candidatos, la hipotesis era falsa |
| Normalizar el coste por el espaciado entre silabas en vez de por la frase | En una frase de 10 s, 300 ms de error cuestan 0,03 y la fuerza del pico decide sola | ventana **117 ms** vs espaciado **143 ms**. Y el peso de la fuerza casi no influye (0,45 -> 0,0 mueve 143 a 146) | **NO.** Con la escala fina el coste se pega a la expectativa y devuelve el reparto a ojo del que se huia |

**Lo que queda vivo para la proxima:** el emparejador tiene el arranque bueno a
22 ms y elige uno a 117 ms. Lo que no se ha probado es usar el audio para la
**esperanza** y no solo para el ajuste: hoy `esperado` sale del peso de letras,
que asume canto uniforme. Repartir las silabas segun la densidad de arranques
del tramo es la unica via que queda sin medir.

---

## El "contraste" era un artefacto, y elegia el corpus de oro (22-08-2026)

Esto no salio de una idea sino de una comprobacion tonta: **de las cuatro
canciones que Bruno jugo la noche del 21 al 22-08 -- Them Bones, Impulse,
Cliffs of Dover y Corazon De Nino -- solo Impulse entraba en el corpus de oro.**
Las otras tres se caian por el mismo filtro: *"no respira"*. Incluida Cliffs of
Dover, que es justo la partida con la que se fijo el liston del proyecto.

### Que estaba mal

`atlas.medir_pista` calculaba, sobre una curva de densidad de **12 tramos**:

    contraste = max(curva) / min(los tramos vivos)

Dos defectos, y los dos importan porque ese numero decidia el corpus de oro, o
sea a que se parece **todo lo que genera AutoChart**:

1. Es un cociente entre **dos puntos sueltos de doce**. Maximo y minimo son los
   estadisticos mas fragiles que hay.
2. **El minimo va en el divisor.** Un tramo casi vacio no baja la nota: la
   dispara. Un chart con un agujero puntua como si respirara maravillosamente.

### Medido sobre 392 pistas de guitarra en Experto

| | |
|---|---|
| correlacion contraste <-> tramos casi muertos | **+0.60** |
| biblioteca que se mueve mas de 50 puestos con una medida robusta | **55 %** |
| del oro anterior que habia entrado TENIENDO agujeros | **8 de 37** |

Los casos son descarados: Arctic Monkeys - Knee Socks puntuaba **33.70** con un
33 % de la cancion muerta; Linkin Park - What I've Done, **39.60** con un 25 %.
Mientras, Cliffs of Dover -- constante de principio a fin, **0 % muerto** --
puntuaba 1.59 y se descartaba por "no respira".

**Es decir: el filtro que elegia la referencia del generador premiaba
exactamente el defecto del que se queja Bruno jugando** (*"hay zonas en las que
ni siquiera se toca nada"*) y castigaba lo que el pide (*"si quiero que la
cancion sea constante"*). El propio `generate.py` ya lo tenia medido sin
nombrarlo: subir el contraste "deja fuera notas que el humano si escribio".

### Lo que lo sustituye

El contraste mezclaba dos cosas distintas. Ahora se miden por separado:

- **`tramos_muertos`** -- fraccion de tramos por debajo del 25 % de la mediana.
  Limite: **1 tramo de 12**. No es un numero elegido: el **87 %** de los charts
  humanos no tiene ninguno y el **95 %** tiene como mucho uno.
- **`variacion`** -- desviacion/media de la curva. Dinamica real, sin depender
  de extremos. Limite: p25 = 0.194.

El contraste se sigue guardando como dato, pero **ya no decide nada**.

| | antes | ahora |
|---|---|---|
| pistas en el oro | 37 | **60** |
| Them Bones | fuera | **oro** |
| Impulse | oro | **oro** |
| Knee Socks, What I've Done, Raining Blood, Danza Kuduro | dentro o alto | **fuera** |

**Cliffs of Dover sigue fuera**, y hay que decirlo: cae por *plana* (variacion
0.152) y *poco vocabulario* (0.39). Es el extremo constante, y ninguna medida de
dinamica lo va a admitir. Eso deja una pregunta abierta y honesta: puede que un
solo corpus de oro no valga, y que haya **dos familias legitimas** -- la
constante (shred continuo) y la dinamica. Hoy el generador apunta a una sola.

---

## Que gesto va despues de cual (22-08-2026)

`detectar_licks` encontraba 16 gestos y **tiraba el orden**. Ahora lo guarda, y
`tools/transiciones.py` mina la matriz. Sobre **391 pistas y 48 250
transiciones** de guitarra en Experto:

| despues de... | pares | sorpresa | lo que viene |
|---|---|---|---|
| anclado | 14 926 | **1.42 b** | **anclado 79 %** |
| salto_ancho | 11 364 | **1.84 b** | **salto_ancho 68 %** |
| sostenido_largo | 4 318 | 2.57 b | sostenido_largo 51 % |
| acorde_martillo | 2 693 | 2.68 b | acorde_martillo 50 % |
| tremolo | 1 830 | 2.60 b | tremolo 43 % |
| escalera_baja | 2 710 | 2.68 b | salto_ancho 36 %, escalera_sube 24 % |
| escalera_sube | 2 342 | 2.54 b | salto_ancho 37 %, escalera_baja 27 % |
| rafaga | 592 | **3.39 b** | rafaga 20 % (no hay regla) |

**El hallazgo es la persistencia.** Lo que un charter humano hace despues de un
gesto es, abrumadoramente, **el mismo gesto otra vez**: 79 % en anclado, 68 % en
salto_ancho, ~50 % en sostenidos, acordes y tremolos. Un chart humano se queda
en una figura y la agota antes de cambiar.

Y el generador de hoy elige **nota a nota**, sin ninguna memoria de que estaba
haciendo. Por eso los charts generados se sienten sorteados aunque cada nota
este en su sitio -- y por eso a Bruno le rompen la partida "los cambios que no
se ven venir" con racha maxima de 36 sobre un 73 % de aciertos: no le mata la
densidad, le mata la falta de continuidad.

Dos cosas mas que salen de la tabla y sirven para generar:

- **Las escaleras desembocan en saltos anchos** (36-37 % en las dos
  direcciones): subir o bajar por trastes seguidos y rematar con un salto es un
  gesto compuesto, no dos gestos.
- **Despues de una rafaga no hay regla** (3.39 bits, la sorpresa mas alta). Ahi
  el generador puede elegir libre sin sonar raro.

### El atlas de oro, reminado con las 60 (22-08-2026)

Al quitar el filtro del contraste, la propia diferencia de contraste entre el
oro y la biblioteca **desaparece**: de 3.96 (oro viejo, 38 pistas) baja a 2.97,
contra 2.84 del total. Era circular -- el oro tenia contraste alto porque se
elegia por contraste alto.

Lo que de verdad separa a lo bueno de lo medio, con el corpus ya limpio
(guitarra, medianas, 99 pistas de oro contra 607):

| | oro | todo | |
|---|---|---|---|
| **ligadas** | **0.237** | 0.144 | **+65 %** |
| repeticion | 0.196 | 0.269 | −27 % |
| acordes | 0.290 | 0.364 | −20 % |
| nps | 4.18 | 3.75 | +11 % |
| contraste | 2.97 | 2.84 | +5 % (ya no dice nada) |
| tramos_muertos | 0.0 | -- | el oro no tiene agujeros |

**Las ligadas siguen siendo la separacion mas grande y el generador sigue sin
perseguirlas.** Eso ya estaba escrito antes de esta limpieza y ahora se confirma
sobre un corpus que no esta sesgado por el artefacto: lo bueno son lineas de
nota suelta ligadas, no acordes machacados.

### La memoria del gesto, llevada al generador (22-08-2026, noche)

La tabla de arriba dice que el humano encadena y que este generador no. La causa
estaba en una linea de `generate.py:assign_frets`: el limite de salto se
recalculaba **nota a nota** mirando solo el hueco temporal. Un limite por nota
no puede producir rachas -- produce saltos sueltos, que jugando son justo "el
cambio que no ves venir".

Se cambiaron **dos cosas, las dos en esa misma linea de decision**:

1. **Memoria de la racha.** Mientras dura una racha de saltos anchos no se
   prohibe seguir saltando, y un movimiento que ya iba a ser grande (dos
   carriles) se completa hasta tres. La racha se corta a los cuatro, que es la
   media humana: 1/(1-0.68) = 3.1. Las dos cifras que definen un salto ancho
   aqui -- tres carriles, hueco maximo un tiempo -- son **las mismas** que usa
   `atlas.py` para contarlo, a proposito: lo que se genera y lo que se mide
   tienen que ser la misma cosa.
2. **El corte por velocidad estaba prohibiendo un tercio de los saltos que
   escribe un humano.** Medido en 168 charts `.chart` de la biblioteca (105.303
   pares de notas sueltas en Experto):

   | hueco | tasa de saltos >=3 | % de todos sus saltos |
   |---|---|---|
   | negra (>= 0.45) | 9.8 % | 46 % |
   | **corchea (0.24-0.45)** | **6.6 %** | **32 %** |
   | semicorchea (< 0.24) | 3.6 % | 6 % |

   El codigo cortaba a **dos** carriles en cuanto el hueco bajaba de 0.45, o sea
   que el 32 % de los saltos humanos era literalmente inalcanzable. La mano si
   salta deprisa; salta *menos*, y eso ya lo decide el contorno (solo el 5 % de
   los intervalos de una cancion pide tres carriles). El limite solo tenia que
   dejar de impedirlo. La semicorchea se queda en 1: ahi el humano casi no salta
   (6 % de sus saltos) y es donde se vuelve infumable.

**Medido regenerando 15 canciones** (las 11 de `16_Brunich - AI Rogue` y las 4
de `17_Pruebas AutoChart`) con el codigo de antes y el de ahora, 4.955 pares de
notas sueltas:

| | antes | ahora | humano |
|---|---|---|---|
| **salto ancho seguido de otro** | **33 %** | **53 %** | 68 % |
| pares de salto ancho | 76 | **150** | -- |
| movimiento +-3 | 2.6 % | **4.7 %** | 6 % |
| movimiento +-2 | 12.5 % | 10.6 % | 14 % |
| se queda | 28.9 % | 29.0 % | 31 % |
| sostenido_largo seguido | 17 % | 21 % | 51 % |

**El numero de notas no se mueve ni una** (686 / 546 / 524 / 682 en las cuatro
de prueba, antes y despues): esto solo cambia a que traste va cada nota. Y el
banco no puede juzgarlo -- no ve los trastes (CLAUDE.md §2) -- asi que sirve
solo de control de que no se rompio la sincronia.

**El precio, medido y no escondido: los acordes pierden racha.**

| | antes | ahora | humano |
|---|---|---|---|
| acorde_martillo seguido | 18 % | **13 %** | 50 % |
| acorde_movil seguido | 3 % | 2 % | 18 % |

Y la causa esta clara: `acorde_martillo` exige misma forma **y misma base**, o
sea que el acorde no se haya movido. Al mover mas la mano, la postura heredada
(`CHORD_SHAPE_KEEP`) deja de contener el carril nuevo y `_shift_chord_shape`
solo se dispara el 8 % de las veces, asi que se sortea una forma nueva. El
humano mueve la mano igual o mas y aun asi encadena el 50 %: lo que hace no es
quedarse quieto, es **mover la postura entera**. Esa es la tarea siguiente.

Confirmado que el efecto viene del punto 2 y no del 1: con solo la memoria de
racha, `acorde_martillo` se quedaba en 26 % (4 canciones) y solo cayo al
soltar el corte por velocidad.

**El control salio identico**, que es la comprobacion de que el cambio hace solo
lo que dice: banco de 24 canciones **f1 0.663 · precision 0.699 · recall 0.666 ·
0 errores**, con `nps_humano_medio 3.91`, las mismas cuatro cifras que antes de
tocar nada. Un cambio que solo mueve carriles no puede mover un F1 que compara
tiempos; si se hubiera movido, habria sido la senal de que toca algo mas.

## El chart estaba tocando la bateria (22-08-2026, noche)

Bruno, despues de probar el lote entero: *"el nivel sigue siendo bastante bajo
[...] no se siente que se este tocando la cancion [...] **siento que estoy
tocando las mismas canciones que antes**"*. Las cuatro medidas que se hicieron
antes de tocar nada estan en `docs/PLAN_TOCAR_LA_CANCION.md`; aqui queda lo que
no hay que volver a medir ni volver a suponer.

**1. La sincronia no era el problema.** 94.8 % y 92.3 % de las notas a menos de
50 ms de un ataque real, deriva de tempo por debajo de 1.6 ms. Caer sobre un
ataque y caer sobre el ataque BUENO no son lo mismo, y el proyecto solo medía lo
primero.

**2. El filtro de densidad prefiere la percusion.** `tools/quien_toca.py`, sobre
la mezcla que oye el jugador:

| | notas mas percusivas que armonicas | lead elegidas | lead de todos |
|---|---|---|---|
| JUNIOR H - INTRO | 29 % | 0.548 | 0.473 |
| MARCOS YTZ - DALI | 58 % | 0.711 | 0.651 |
| Brunich - Cyber Club | **63 %** | **0.668** | **0.692** |

En una cancion suya de guitarra el filtro elige ataques **menos** melodicos que
la media de la propia cancion. Causa exacta: `thin` se queda con lo mas fuerte
de cada ventana y en una mezcla lo mas fuerte es el bombo; `LEAD_PRIORITY` (0.40)
no llega a competir con el peso 1.0 de la fuerza.

**3. Los 15 charts generados son practicamente el mismo chart.**
`tools/parecidas.py`, distancia coseno entre las mezclas de gestos de todas las
parejas: **0.077 los generados contra 0.582 los humanos**, o sea que se parecen
entre si **7.5 veces mas**. La queja de Bruno tiene numero.

**4. La letra no va tarde: tiembla.** Mediana del desfase practicamente cero en
las cuatro canciones (+1, −10, +3, −13 ms) pero p25-p75 de **±130 ms**: un tercio
de las silabas mas de 60 ms tarde y otro tercio mas de 60 ms pronto. No hay
offset que restar. Y hay tramos con canto y sin una sola silaba: *Loser* 29 s,
*INTRO* 17 s.

### La decision que hay que revisar: Demucs se descarto con una medida ciega

Estaba escrito arriba en la tabla de riesgos: *"forzando la mezcla el F1 solo
baja de 0.648 a 0.618, asi que Demucs tiene como mucho 0.03 que recuperar"*. El
numero es correcto; **la conclusion no**. El F1 apenas se mueve porque la bateria
y la guitarra atacan en el mismo sitio de la rejilla, o sea que quitar el stem
casi no cambia *cuando* suenan las notas. Lo que cambia es *cual* de los dos
sonidos se lleva la nota, y eso es justo lo que el F1 no mira (CLAUDE.md §2,
trampa 1). **La separacion se despriorizo con la unica medida estructuralmente
incapaz de ver lo que la separacion arregla.**

### HPSS: medio problema, gratis, y donde no llega

Probado antes de proponer instalar nada, escribiendo la parte armonica como
`guitar.ogg` y dejando que el pipeline la coja sin tocar codigo:

| | antes | con HPSS |
|---|---|---|
| Brunich - Cyber Club, notas percusivas | 63 % | **31 %** |
| MARCOS YTZ - DALI, notas percusivas | 58 % | 55 % |

En lo electronico y lo de guitarra HPSS se lleva la mitad. En DALI no hace nada,
y la razon es estructural: ahi lo que compite con la guitarra no es una bateria,
es **la voz**, y las dos son armonicas. Eso no lo separa un HPSS.

Ojo al repetir la prueba: la carpeta de prueba no llevaba `notes.chart`, asi que
esa pasada fue **sin anclar a la letra**. La comparacion de percusividad vale; la
de patron no.

---

## S1: separar la cancion, y el objetivo del 20 % puesto a prueba (22-08-2026)

`autochart/separar.py` estaba escrito y **sin ejecutar ni una vez**, sin comando
en `cli.py` y sin que `audio.pick_audio` mirara las pistas. Aqui queda cerrado
el escalon entero y, sobre todo, **medido**.

### Lo que se cablea

`pick_audio` elige en este orden, y cada escalon tiene su razon:

1. El stem que ya traia la cancion (`guitar.ogg`). Sigue ganando: es mas limpio
   que cualquier separacion y es con lo que esta calibrado el banco.
2. `salida/stems/<cancion>/notas.ogg` -- `other` + `vocals` de demucs.
3. La mezcla.

El pulso NO cambia: sigue saliendo de la mezcla, porque sobre un stem aislado el
detector se equivoca de compas entero (ya medido en su dia).

Coste real, comprobado en DALI: **~5 MB por cancion**, una sola vez.

### Lo que dio, y no es lo que se esperaba

| DALI, notas cuyo ataque es mas percusivo que armonico | |
|---|---|
| desde la mezcla (control) | **58 %** |
| desde la pista separada | **47 %** |
| objetivo del plan | < 20 % |

Separar ayuda -- 11 puntos -- pero **no resuelve**. Y la razon se ve barriendo
el desfase sobre el chart generado:

    -40 ms  26 %      0 ms  47 %      +40 ms  33 %
    -20 ms  33 %    +20 ms  50 %      +65 ms  19 %

**El maximo esta justo en 0-20 ms.** Es decir: nuestras notas caen exactamente
encima del golpe percusivo. No es un fallo de sincronia que se pueda descontar,
es donde el generador esta poniendo la nota a proposito.

### El objetivo del 20 % era una suposicion, y ahora hay referencia

`tools/quien_toca.py` **solo leia `notes.chart`, y todos los charts humanos de la
biblioteca son `.mid`**: la herramienta con la que se fijo el objetivo nunca
habia podido medir a un humano. Arreglado (lee las dos cosas), sobre cuatro
charts humanos de Guitar Hero 1:

| | sin desfase | descontando 65 ms |
|---|---|---|
| Audioslave - Cochise | 22 % | **7 %** |
| Black Sabbath - Iron Man | 33 % | **12 %** |
| Cream - Crossroads | 42 % | **12 %** |
| Boston - More Than A Feeling | 23 % | **6 %** |

Los `.mid` humanos llevan el desfase de autoria que este proyecto ya tiene
medido (+65/+70 ms): el charter cuadra a la rejilla, no a la onda. Descontado,
**el humano escribe entre el 6 % y el 12 %**, o sea que el objetivo del 20 % es
alcanzable y hasta conservador.

Y lo que revela la comparacion es el gesto de fondo: **el humano coloca la nota
despues del golpe percusivo, no encima.** Nosotros la clavamos en el golpe. Por
eso un chart humano suena a que toca la cancion y el nuestro a que sigue la
bateria, aunque los dos caigan sobre "ataques reales".

**Aviso de metodo:** la medida se mueve del 42 % al 12 % con 65 ms de
diferencia. Cualquier cifra de `quien_toca.py` sin decir el desfase que se uso no
significa nada.

---

## S2 refutado, y S1 puesto a prueba contra la queja de verdad (22-08-2026)

Tres resultados seguidos, y ninguno es el que se esperaba. Se escriben enteros
porque los tres ahorran tandas.

### 1. LEAD_PRIORITY no hace nada

La tarea S2 decia: ahora que la fuente es la pista separada y no la mezcla,
pesar mas lo melodico ya no pelea contra el bombo. Barrido sobre las cuatro
canciones de control (`tools/barrido_lead.py`), notas mas percusivas que
armonicas:

| lead | INTRO | DALI | Gil | Loser | media |
|---|---|---|---|---|---|
| 0.40 | 26 % | 47 % | 28 % | 34 % | 33.8 % |
| 0.70 | 26 % | 47 % | 28 % | 34 % | 33.8 % |
| 1.00 | 26 % | 47 % | 28 % | 34 % | 33.6 % |
| 1.50 | 26 % | 46 % | 28 % | 33 % | 33.2 % |

**Multiplicar el peso por 3.75 mueve la media 0.6 puntos.** La premisa habia
caducado, si, pero el remedio tampoco funciona: una vez la fuente esta limpia,
`lead` ya no discrimina dentro de ella porque casi todos sus ataques son
melodicos. **LEAD_PRIORITY se queda en 0.40.**

### 2. El objetivo del 20 % comparaba peras con manzanas (error mio, corregido)

Se escribio que el objetivo era alcanzable "porque el humano esta en 6-12 %".
Ese 6-12 % es **descontando el desfase de autoria del `.mid`**. Los charts
generados no tienen ese desfase. Con la MISMA vara para los dos:

| | notas percusivas |
|---|---|
| humanos, sin descontar nada (4 charts de GH1) | 22 %, 33 %, 42 %, 23 % -- media ~30 % |
| generados, las 4 de control | 26 %, 47 %, 28 %, 34 % -- media 33.8 % |

**Estamos dentro del rango humano.** El objetivo del 20 % era inalcanzable por
construccion, y perseguirlo era perseguir un artefacto de autoria ajeno.

### 3. Y lo importante: separar EMPEORA lo que se queria arreglar

`tools/parecidas.py` es la medida que si captura la queja de Bruno ("siento que
estoy tocando las mismas canciones que antes"). Las mismas cuatro canciones,
antes y despues de S1:

| | distancia media | contra humanos |
|---|---|---|
| desde la mezcla | 0.105 | 5.5 veces mas parecidos |
| **desde los stems (S1)** | **0.062** | **9.4 veces mas parecidos** |

Separar baja las notas percusivas (58 -> 47 en DALI) **y a la vez hace los
charts MAS iguales entre si**. Al quitar bateria y bajo, lo que queda se parece
mas de una cancion a otra, y el chart lo hereda.

**Conclusion, y cambia el plan:** la via "separar + pesar lo melodico" no
arregla el "todas iguales". La causa esta en otro sitio y ya estaba medida: el
generador tiene un gesto iman. Su persistencia es `anclado` 69-71 % y **todo lo
demas desemboca ahi** (cadena_sostenidos -> anclado 53 %, galope -> anclado
43 %), mientras el humano mantiene el gesto en curso y reparte distinto en cada
cancion y genero. Si todos los charts estan dominados por el mismo gesto, todos
se parecen -- y eso no lo cambia de donde salga el audio.

**S1 no se revierte pero NO esta validado:** `pick_audio` solo usa los stems de
las canciones que se hayan separado a mano, asi que hoy no afecta a nada mas.
No separar el resto de la biblioteca hasta que la variedad este arreglada.

### La semilla fija: causa real pero pequena

`--semilla` vale 7 por defecto **para todas las canciones**, y con ella se
baraja `_motif_bank` (generate.py:814): el banco de formas de tres notas sale
del perfil, que es el mismo para todo, y se recorre en el mismo orden. Cuando el
audio deja de decir algo util (`flat_run >= 3`) todas las canciones toman las
mismas formas en la misma secuencia.

Medido, las mismas cuatro canciones:

| lote | distancia | veces mas parecidos que humanos |
|---|---|---|
| mezcla + semilla fija | 0.105 | 5.5 |
| stems + semilla fija | 0.062 | 9.4 |
| stems + semilla por cancion (crc32 del nombre) | 0.072 | 8.1 |

Derivar la semilla del nombre sube la distancia un 16 % y es gratis, pero **no
es la causa principal** y no justifica por si sola mover el defecto (cambiar la
semilla cambia el banco y obliga a re-medir el banco entero). Queda escrito con
su numero para quien lo retome.

**Lo que queda apuntado como causa principal, y ya esta medido:** el generador
tiene un gesto iman. `anclado` persiste el 69-71 % y todo lo demas desemboca ahi
(cadena_sostenidos 53 %, galope 43 %), mientras el humano mantiene el gesto en
curso y **reparte distinto en cada genero**. Las matrices por genero ya estan
minadas en `datos/transiciones.json` y no las usa nadie todavia.

### El perfil del oro: la vara estaba puesta sobre lo mediano

`python -m autochart minar --solo-oro datos/corpus_oro.json` mide solo los 60
charts que pasaron los filtros de `tools/elegir_oro.py` (60 de 60 leidos, 10.3 s).
Contra el perfil de los 882 que usa el generador hoy:

| | perfil (todos) | perfil del oro | cambio |
|---|---|---|---|
| notas/s | 3.748 | 4.176 | +11.4 % |
| acordes | 0.347 | 0.290 | -16.3 % |
| sostenidos | 0.152 | 0.107 | -29.6 % |
| repeticion de traste | 0.270 | 0.196 | -27.4 % |

**El de repeticion es el que no se esperaba.** El proyecto lleva desde el
05-08-2026 apuntando al 27 % porque es la mediana de TODA la biblioteca, y los
charts buenos repiten 19.6 %. Ojo: eso no resucita la regla anti-repeticion que
se quito (bajaba a 12.5 % y se sentia inquieta); dice que el objetivo esta 7
puntos por encima de lo que hacen los buenos. Hoy no lo persigue nadie: el
generador lee del perfil la densidad, los acordes, los sostenidos y los
trigramas del banco de motivos (generate.py:816), no `repeat_ratio`.

**Y no arregla el "todas iguales".** Mismas cuatro canciones de control,
misma vara (`tools/parecidas.py`, humanos 0.582):

| lote | distancia | veces mas parecidos que humanos |
|---|---|---|
| mezcla + perfil de todos | 0.105 | 5.5 |
| stems + perfil de todos | 0.062 | 9.4 |
| stems + semilla por cancion | 0.072 | 8.1 |
| stems + perfil del oro | 0.074 | 7.9 |

El perfil del oro recupera casi lo mismo que la semilla por cancion (+19 %
contra +16 %) y por la misma razon: cambia el banco de motivos, no quien lo
elige. Los cuatro charts pasan `revisar_in_game`. La escala esta comprobada:
re-medir `salida/semillas` hoy vuelve a dar 8.1, el mismo numero de ayer.

**Los dos empujones SI se suman.** Perfil del oro + semilla por cancion sobre
las mismas cuatro: media **0.089, o sea 6.5 veces** (base 0.062 / 9.4). El +44 %
es casi el producto de los dos sueltos (1.19 x 1.16 = 1.38), o sea que tocan
cosas distintas y no se pisan.

Con cuatro canciones son seis parejas y la media es fragil -- la mediana de
`oro + semilla` (0.069) es PEOR que la del oro solo (0.075) porque una pareja
tira del promedio. Lo que sostiene la conclusion es el **minimo**, que es
justamente el caso de "estas dos se sienten el mismo chart":

    base            parejas 0.024 0.031 0.057 0.075 0.080 0.106
    oro + semilla   parejas 0.047 0.052 0.068 0.070 0.144 0.152

La pareja mas parecida pasa de 0.024 a 0.047 y ninguna baja de 0.047, mientras
la base tenia dos por debajo de 0.032. Aun asi seguimos en 6.5 veces contra el
objetivo de 3: **son dos empujones, no el arreglo**. El arreglo sigue siendo el
gesto iman.

### P1: el contorno con continuidad, y lo que se probo encima

El estimador nuevo (`audio.contorno_de_tono`) es suma armonica + peso grave
suave + Viterbi con el prior de intervalos de `datos/perfil_voz.json`. Numeros
en el commit y en `docs/AUDITORIA_POR_QUE_NO_SUENA.md`; en corto, los saltos de
octava pasan del 20,2 % al 6,3 % en nuestras cuatro y del 39,7 % al 4,6 % en
Thunderstruck, y la ventaja del chart HUMANO sube de +4,7 % a +13,2 %.

**Barrido de dos parametros, 6 canciones con guitarra aislada, mediana:**

| supresion de octava | prob. de moverse | ventaja humana | octava | > quinta | quietas |
|---|---|---|---|---|---|
| **0.0** | **0.08** | **+18.9 %** | **1.9 %** | **7.2 %** | 53.6 % |
| 0.4 | 0.08 | +16.5 % | 2.8 % | 8.3 % | 51.6 % |
| 0.7 | 0.08 | +16.7 % | 2.5 % | 8.6 % | 51.6 % |
| 0.4 | 0.15 | +16.4 % | 3.1 % | 9.0 % | 49.1 % |
| 0.7 | 0.15 | +16.0 % | 2.9 % | 9.3 % | 49.6 % |
| 0.7 | 0.25 | +15.5 % | 2.9 % | 9.9 % | 45.4 % |

**Restar el armonico EMPEORA.** La idea razonable era: si a un bin que parece el
armonico de una nota mas grave se le quita energia, el contorno deja de irse
arriba. Medido, sube los saltos de octava (1,9 % -> 2,5-3,1 %) y baja la ventaja
(+18,9 % -> +16,5 %). Sumar los armonicos hacia abajo ya lo resuelve; restar
ademas se lleva por delante notas agudas legitimas. `SUPRESION_OCTAVA` se queda
en 0.0 y el parametro sigue ahi para que el experimento se pueda repetir.

**Ojo con la muestra:** ese +18,9 % es la mediana de 6 canciones elegidas con
riff claro. Sobre las 12 de la medida completa da **+13,2 %**, que es el numero
honesto contra la puerta de +15 %. Una muestra sola miente (CLAUDE.md, trampa 3).

**El defecto nuevo que hay que vigilar: el contorno se aplana.** Los saltos de 0
suben al 43,8 % en nuestras cuatro (53,6 % en las de guitarra aislada) contra el
35,1 % humano. Importa mas de lo que parece: `assign_lanes` tira del banco de
motivos en cuanto el tono lleva tres notas quieto (`flat_run >= 3`), o sea que un
contorno plano devuelve el control al banco -- que es justo la causa del "todas
las canciones se sienten iguales". Aplanar tambien es perder la melodia.

### Y el chart generado con ese contorno: el "todas iguales" baja a 5.4 veces

Regeneradas las cuatro de control con el contorno nuevo, el perfil del oro y la
semilla por cancion:

| lote | distancia | mediana | veces mas parecidos que humanos |
|---|---|---|---|
| stems + perfil de todos | 0.062 | 0.066 | 9.4 |
| stems + semilla por cancion | 0.072 | 0.058 | 8.1 |
| stems + perfil del oro | 0.074 | 0.075 | 7.9 |
| oro + semilla | 0.089 | 0.069 | 6.5 |
| **contorno nuevo + oro + semilla** | **0.108** | **0.109** | **5.4** |

Dos cosas que no se ven en la columna de "veces". La primera: **esta vez la
mediana acompana a la media** (0.108 contra 0.109), mientras que en el lote
anterior la media iba por delante por culpa de una sola pareja. La mejora es
uniforme, no un artefacto de seis parejas.

La segunda: **el aplanamiento no se cobro lo que se temia**. El contorno nuevo
se queda quieto mas veces, o sea que `flat_run >= 3` dispara mas y el banco de
motivos manda mas rato -- y aun asi la variedad mejora, porque cuando el
contorno habla, dice cosas distintas en cada cancion.

Y lo que el chart hace con el contorno, medido con la misma vara que los
humanos: la ventaja pasa de +11,0/+19,9 % a **+27,0/+34,1 %**. Ojo con leer eso
como un exito: nuestros charts estan CONSTRUIDOS con ese contorno, asi que la
cifra que de verdad juzga el contorno sigue siendo la del chart HUMANO (+13,2 %).

Las cuatro pasan `revisar_in_game`.

### Pride & Joy, la cancion de referencia que puso Bruno

Bruno, 22-08-2026: *"lo importante es que los generados esten muy similares a los
que estuvieron hechos a mano"*, y eligio **Stevie Ray Vaughan - Pride & Joy**
(en `03_`, con `guitar.ogg` aislado y `notes.mid` de Neversoft). Es la mejor
referencia posible: guitarra pura, chart humano bueno, y el audio ES el
instrumento que el chart hace tocar.

Herramienta nueva: `tools/contra_el_humano.py --pride`. Primera medida:

| | humano | generado |
|---|---|---|
| notas | 982 | 661 (67,3 %) |
| notas/s | 4,474 | 2,981 |
| acordes | 0,442 | 0,290 |
| sostenidos | 0,017 | 0,107 |
| repite traste | **0,141** | **0,380** |
| ligadas | **0,390** | **0,132** |

Recall 0,430 · precision 0,643 · F1 0,515 con +30 ms de desfase. Distancia de
gestos contra SU chart **0,114**, cuando dos humanos cualesquiera estan a 0,582:
el 80 % del camino hecho. Y la melodia: el humano saca +18,1 % al azar sobre
`guitar.ogg` y nosotros +33,4 %, o sea que en guitarra limpia el contorno nuevo
supera la puerta de +15 % que se le habia puesto.

**Tres cosas quedan refutadas o resueltas de golpe:**

1. **"No detecta todas las notas" no es del detector.** En esa cancion detecta
   **2.026 ataques** (9,06/s) contra las 982 del humano, y el objetivo que se
   pone el generador es de **912 notas**. El chart sale con 661: **lo que se
   pierde, se pierde despues de elegirlo**, en la etapa de densidad.
2. **Las "cinco capas que pisan la melodia" no existen.** Instrumentado
   `assign_frets` (contador `REPARTO`): contorno 81,5 %, banco de motivos
   16,4 %, anti-repeticion 1,5 %, racha 0,5 %, limite de velocidad 0,1 %. El
   objetivo escrito era 66 % y ya iba por 81,5 %.
3. **Mover mas el contorno no arregla la repeticion.** Barrido de
   `PROB_DE_MOVERSE` 0,08 -> 0,40 (cinco veces mas movimiento): la repeticion
   baja de 0,395 a 0,366 y nada mas. Los cuadros quietos del contorno pasan del
   70 % al 60 % sin efecto util. No es esa la palanca.

### La palanca que si era: cuando la nota se repite, el humano mueve la mano

De las parejas de notas en las que **el tono no se mueve**, el charter de
Pride & Joy cambia de traste el **46,5 %** de las veces. Este generador, el
31,2 %. De ahi salen sus dos defectos gemelos, que son el mismo: repite traste
2,7 veces mas que el humano y liga 3 veces menos -- **si el traste no cambia no
puede haber martilleo**, y un blues sin hammer-ons no se siente como un blues.

Regla nueva (`ALTERNANCIA_PROB`, `generate.py`): cuando la nota se repite y va
seguida (hueco <= 0,55 tiempos), mover la mano al traste vecino. Solo en notas
seguidas: en una nota larga o aislada, repetir el traste es lo que hace el
humano. Barrido sobre Pride & Joy:

| prob | repite | ligadas | F1 | distancia a su chart | mueve si mismo tono |
|---|---|---|---|---|---|
| 0,00 | 0,395 | 0,151 | 0,586 | 0,057 | 32,1 % |
| **0,25** | 0,302 | 0,188 | 0,586 | 0,078 | **46,8 %** |
| 0,45 | 0,262 | 0,217 | 0,586 | 0,071 | 51,9 % |
| 0,65 | 0,221 | 0,215 | 0,586 | 0,070 | 59,4 % |
| *humano* | *0,141* | *0,390* | | | *46,5 %* |

**El F1 no se mueve ni una milesima**: la regla toca el traste, no el momento.
Y hay que decir lo que empeora: la distancia de gestos contra su chart sube de
0,057 a 0,078 -- poco en absoluto (los dos son ~87 % del camino desde 0,582),
pero sube.

**El valor sale de DOCE canciones, no de una.** Medido en las 12 con guitarra
aislada, lo que mueve el humano cuando la nota se repite:

    Thunderstruck 86,4 % | Same Old Song & Dance 76,2 % | En Realidad 73,7 %
    Cochise 61,0 % | Mucha Lucha 59,8 % | What's My Age Again 55,0 %
    Lie Lie Lie 52,1 % | Am I Evil 41,2 % | Like a Stone 33,9 %
    Them Bones 33,7 % | Teen Spirit 33,6 % | Aliens Exist 7,7 %

    MEDIANA 53,6 %   MEDIA 51,2 %

O sea que el humano mueve la mano **mas de la mitad de las veces** que la nota
se repite, y el 46,5 % de Pride & Joy esta en la parte baja. Calibrando con esa
sola cancion habria salido 0,25; con las doce sale **0,45**, que da 51,9 % en
Pride & Joy. Es exactamente la trampa 3 de CLAUDE.md, y esta vez se vio a tiempo.

La dispersion (7,7 % a 86,4 %) dice que esto **deberia depender del genero**, no
ser una constante: el punk de Aliens Exist casi nunca mueve la mano y el riff de
Thunderstruck casi siempre. `datos/atlas_patrones.json` ya tiene las firmas por
genero y nadie las usa todavia.

**Resultado con `ALTERNANCIA_PROB = 0.45` puesto, medido entero:**

| Pride & Joy | antes | ahora | humano |
|---|---|---|---|
| distancia de gestos a SU chart | 0,114 | **0,087** | (0,582 entre dos humanos) |
| repite traste | 0,380 | **0,261** | 0,141 |
| ligadas | 0,132 | **0,169** | 0,390 |
| F1 | 0,515 | 0,515 | |
| ventaja de melodia | +33,4 % | **+25,4 %** | +18,1 % |

Y en las cuatro de control, el "todas iguales" baja otra vez: **5,4 -> 4,6
veces**. Las cuatro siguen jugables.

Tres cosas que conviene leer juntas. La distancia al chart humano pasa del 80 %
al **85 % del camino**. Nuestra ventaja de melodia BAJA (+33,4 -> +25,4) y eso
es bueno: dejamos de seguir el contorno servilmente y nos acercamos al +18,1 %
del humano, que no lo copia. Y las ligadas suben poco (0,132 -> 0,169 contra
0,390): mover la mano hace falta pero no basta, porque una ligadura tambien
pide que las dos notas esten cerca en el tiempo.

### La letra mandaba sobre la guitarra, y costaba el 19 % de las notas

Buscando por que el chart de Pride & Joy salia con 661 notas cuando el propio
generador se pone un objetivo de 917, aparecio esto: **el rip trae la letra
cantada** (213 silabas, "Well / you've / heard / about / love...") y
`cmd_generar` la usa como ancla. En las ventanas con canto, `thin` se queda
**solo** con las silabas y no rellena (PLAN_MELODIA F1).

En una cancion de voz eso es lo que se queria. En una de guitarra es seguir a
quien canta en vez del riff. Regla nueva en `cli.py`: **si las notas salen de
una pista de guitarra aislada (`guitar.ogg`, `rhythm.ogg`, `lead*`), la letra no
manda** -- ahi ya se sabe que instrumento se toca.

Y la tabla de donde se pierden las notas (`tools/quien_decide.py`, contador
`PERDIDAS`), que responde la pregunta de fondo:

    ataques detectados            1640   (2026 antes de cuadrar a la rejilla)
    presupuesto de densidad        917
    sobreviven al presupuesto      893
    tiradas por el hueco minimo     74
    notas finales                  819   (el humano escribio 982)

**El detector nunca fue el problema:** oye el doble de notas de las que el
humano escribio. Lo que faltaba era no tirarlas despues.

### Pride & Joy, de punta a punta en un dia

| | por la manana | ahora | humano |
|---|---|---|---|
| notas | 661 (67,3 %) | **819 (83,4 %)** | 982 |
| recall | 0,430 | **0,538** | |
| F1 | 0,515 | **0,586** | |
| distancia de gestos a SU chart | 0,114 | **0,071** | (0,582 entre humanos) |
| repite traste | 0,380 | **0,262** | 0,141 |
| ligadas | 0,132 | **0,217** | 0,390 |
| notas/s | 2,981 | **3,693** | 4,474 |
| ventaja de melodia | +33,4 % | **+22,2 %** | +18,1 % |

Del 80 % al **88 % del camino** hacia su chart. Lo que sigue lejos, y en este
orden: **los sostenidos, que sobran 6 veces** (0,106 contra 0,017 -- en un blues
las notas se pican, no se sostienen), los **acordes, que faltan** (0,291 contra
0,442) y las **ligadas, que faltan** (0,217 contra 0,390).

## El genero manda en los acordes y NO en los sostenidos (23-08-2026)

La tarea escrita pedia "que el perfil dependa del GENERO", y la razon escrita
eran los sostenidos: en Pride & Joy salian seis veces de mas (0.106 contra
0.017) clavados al objetivo del perfil (0.107), o sea que el generador acertaba
su objetivo y el objetivo estaba mal para esa cancion.

**La premisa era medio falsa, y ahora tiene numero.** Minado el genero con el
MISMO codigo que mide el corpus (`corpus.py`, no el atlas, que cuenta los
sostenidos de otra manera: su p50 de `acustico` es 0.4967 contra el 0.151 de
aqui), sobre los 392 charts humanos de la biblioteca. Varianza explicada
(`eta cuadrado`) por cada eje:

| | genero | BPM |
|---|---|---|
| acordes | **0.112** | 0.007 |
| notas/s | 0.116 | **0.159** |
| **sostenidos** | **0.024** | 0.012 |
| repeticion | 0.026 | 0.016 |
| cambio de traste en notas seguidas | 0.046 | 0.010 |

El genero es **lo unico** que explica los acordes. Y **no explica los
sostenidos**: 2.4 % es nada. Lo que si los predice es la densidad de la propia
cancion, r = -0.372, por cuartiles:

    Q1  2.42 notas/s  ->  sostenidos 0.299   acordes 0.414
    Q2  3.32          ->             0.152          0.364
    Q3  4.03          ->             0.137          0.357
    Q4  5.17          ->             0.070          0.233

Y aun asi Pride & Joy no se alcanza por ahi: su chart humano esta en el
**percentil 3.3** de sostenidos con densidad de percentil 75. Ninguna mediana de
ningun grupo llega a 0.017. Perseguir ese numero con un perfil es un callejon.

### Las medianas por familia (392 charts, Experto)

| genero | n | notas/s | acordes | sostenidos | repite | cambio en seguidas |
|---|---|---|---|---|---|---|
| GLOBAL | 392 | 3.696 | 0.348 | 0.151 | 0.270 | 0.760 |
| rock | 164 | 3.617 | 0.380 | 0.177 | 0.259 | 0.803 |
| metal | 96 | 4.490 | 0.218 | 0.117 | 0.312 | 0.685 |
| punk | 28 | 4.075 | 0.552 | 0.120 | 0.383 | 0.638 |
| latino | 25 | 2.911 | 0.499 | 0.209 | 0.245 | 0.917 |
| pop | 15 | 2.858 | 0.364 | 0.182 | 0.321 | 0.758 |

`acustico` (5 charts) y `urbano` (6) se quedan fuera del minimo de 12
(`corpus.MINIMO_POR_GENERO`): con menos, la mediana de un genero es la de dos
personas y no la de un estilo.

### Por que el bloque MUEVE la mediana y no la sustituye

Cada bloque guarda su **factor** (`p50 del genero / p50 de la misma tanda`), no
su nivel. Dos razones y las dos son de medida:

- El perfil que usa el generador es el del **oro** (60 charts), donde solo metal
  (21) y rock (26) llegan al minimo. Los otros tres se prestan del minado de la
  biblioteca entera, y prestar un **desvio** es legitimo mientras prestar un
  **nivel** mezclaria dos poblaciones. Por eso el factor viaja dentro del bloque
  (`by_genre.<familia>.factores`) y no en una referencia global suelta.
- El bucket de BPM ya explica mas densidad que el genero. Sustituir tiraria ese
  efecto en vez de componerlo.

### La cancion de aceptacion no puede juzgar esto

Pride & Joy dice `Electric Blues`, que `atlas.normalizar_genero` manda a la
familia `acustico`, y esa familia son cinco charts en toda la biblioteca (Black
Magic Woman, Buckethead, Ed Maverick, Pride & Joy, Rascal Flatts). O sea que la
cancion de referencia **se queda sin bloque** y el genero no la toca: medido
despues del cambio, `contra_el_humano.py --pride` da exactamente lo mismo que
antes (819 notas, F1 0.586, distancia 0.071). Eso es el control, no el
resultado.

El resultado se mide con `tools/panel_generos.py`: **diez** canciones, dos por
familia, todas con `guitar.ogg` -- ahi el audio ES el instrumento del chart --
generadas con el perfil viejo y con el nuevo.

### El resultado, y el descarte que salio de el

| media de las 10 | antes | genero completo | **genero sin densidad** |
|---|---|---|---|
| distancia de gestos al humano | 0.434 | 0.408 | **0.384** |
| F1 | 0.505 | 0.488 | **0.505** |
| error de acordes | 0.257 | 0.199 | **0.200** |
| error de densidad | 1.033 | 1.037 | **1.033** |
| error de repeticion | 0.159 | 0.143 | **0.150** |
| error de sostenidos | 0.272 | 0.272 | **0.272** |
| canciones que mejoran | -- | 7 de 10 | **9 de 10** |

**La densidad por genero esta MEDIDA Y DESCARTADA.** Componer el factor del
genero encima del bucket de BPM deja el error de densidad igual (1.033 ->
1.037) y baja el F1 de 0.505 a 0.488. La causa se ve por cancion: las dos
latinas del panel van a 3.85 y 4.11 notas/s y la mediana de las 25 latinas es
2.91, asi que el factor las **frenaba**. El genero acierta la familia y falla la
cancion; el BPM explica la cancion. El factor se sigue minando y guardando en el
perfil -- es una medida buena -- pero no manda en `target_notes_per_second`.

Sin la densidad, el cambio no toca ni un sostenido (0.272 en las tres columnas,
que es exactamente lo que predecia el 2.4 % de varianza) y mueve los acordes a
donde tenian que ir:

| genero | cancion | humano | antes | ahora |
|---|---|---|---|---|
| metal | Dethklok - Thunderhorse | 0.000 | 0.290 | **0.203** |
| metal | Metallica - Master of Puppets | 0.183 | 0.290 | **0.203** |
| punk | The Sex Pistols - Anarchy In The UK | 0.691 | 0.291 | **0.461** |
| punk | Boys Like Girls - Thunder | 0.499 | 0.290 | **0.461** |
| latino | Christian Nodal - Dime Como Quieres | 0.644 | 0.290 | **0.416** |
| pop | Shakira - La Tortura | 0.648 | 0.291 | **0.304** |

Antes, **las diez canciones salian con 0.290 acordes**: la mediana del corpus,
la misma para un blast beat de metal y para una cumbia. Esa columna es la queja
de "siento que estoy tocando las mismas canciones" escrita en un numero.

Y se ve en la vara de esa queja, sobre este mismo lote de diez:

    parecidas.py salida/panel_antes_charts   16.5 veces mas parecidos que humanos
    parecidas.py salida/panel_ahora_charts    7.0 veces

**Ojo con el lote de control de siempre:** las cuatro canciones de
`salida/alternancia/` (INTRO, DALI, Gil, Loser) **no traen `genre` en su
`song.ini`**, asi que el genero no las toca y siguen en **4.6**. El numero de
titular del proyecto no se mueve con esta tanda, y decirlo importa.

### Una trampa nueva de las herramientas de medida

`panel_generos.generar` devolvia "la ultima carpeta por orden alfabetico" del
destino, copiado de `contra_el_humano.py` (que usa una carpeta limpia por
corrida). Con diez canciones en el mismo destino, **cinco se midieron contra el
chart de The Sex Pistols** y salieron con acordes y densidad identicos -- que es
exactamente el aspecto que tendria el cambio si NO funcionase. Ahora se devuelve
la carpeta de la cancion, y `--remedir` permite volver a medir sin regenerar.

### Cosas de mantenimiento de esta tanda

- `datos/perfil_corpus.json` pasa de 882 charts a **392** (la biblioteca de hoy).
  Las medianas se mueven menos del 1.5 %: notas/s 3.7484 -> 3.6963, acordes
  0.3471 -> 0.3476, sostenidos 0.1517 -> 0.1511, repeticion 0.2701 -> 0.2698.
- Metrica nueva en el corpus: **`cambio_seguidas`**, cuantas veces cambia de
  traste entre dos notas con hueco corto (<= 0.55 tiempos, el mismo
  `ALTERNANCIA_HUECO` del generador). Mediana global 0.760. Es la vara hermana,
  minable en los 392 charts, de la que calibro `ALTERNANCIA_PROB = 0.45` (que
  necesita el tono del audio y solo se pudo medir en doce canciones). El genero
  la mueve por factor: punk 0.839, latino 1.206.

### El `ring` del audio no mide lo que dice medir (23-08-2026)

Buscando por que sobran sostenidos, se midio la senal que deberia decidirlos.
`audio.ring_times` avanza desde el ataque hasta que la energia cae por debajo
del 35 % del pico, con tope de 6 s. En Pride & Joy, sobre `guitar.ogg`:

    ataques 2026    ring >= 3 s: 61.0 %    p25 0.49  p50 5.99  p75 5.99
    clavados en el tope de 6 s: 52.2 %   (remedido el 23-08 por la tarde)

La mediana es **el tope exacto**. En una pista donde se toca sin parar la
energia nunca baja del 35 % del pico, asi que para mas de la mitad de los
ataques `ring` no mide nada. Y contra el chart humano no separa: las 17 notas
que el humano sostuvo tienen ring mediano 5.99 s y las 965 que pico, 3.80 s.

Consecuencia: en `assign_notes`, `room = min(hueco, ring)` deja el `ring` fuera
de juego, los sostenidos van al **hueco mas ancho** y el objetivo del perfil se
cumple a rajatabla. Es lo que el propio comentario del codigo queria evitar
("un hueco ancho puede ser un silencio"). Ahi esta la causa de los sostenidos, y
no en el genero.
## Los sostenidos: la vara estaba rota antes que el generador (23-08-2026)

La tarea escrita era "los sostenidos, que sobran seis veces en Pride & Joy
(0.106 contra 0.017)". Al medirlo aparecieron dos cosas distintas, y la primera
no era del generador sino de la regla con la que se contaba.

### 1. Que cuenta como sostenido: 0.25 tiempos medi­a el FORMATO, no la musica

El umbral estaba escrito a mano en tres sitios (`corpus`, `atlas` y el
generador). En un `.mid` toda nota tiene duracion, asi que los rips convertidos
salen inflados. Medido sobre los 392 charts humanos:

| umbral | `.chart` (168) | `.mid` (224) | razon |
|---|---|---|---|
| 0.25 | 0.1264 | 0.2036 | 1.61 |
| **0.50** | **0.1117** | **0.1056** | **0.95** |
| 0.75 | 0.0685 | 0.0856 | 1.25 |
| 1.00 | 0.0324 | 0.0440 | 1.36 |

**0.5 tiempos no es un gusto: es el unico punto donde las dos maneras de
escribir un chart dicen lo mismo.** Y el largo mediano de "sostenido" de un
`.mid` era 0.250 tiempos clavados, o sea el propio umbral. A 0.25 el p95 del
corpus daba 0.9552 -- "el 95 % de las notas sostenidas" -- que no describe
ningun chart que nadie haya tocado.

Lo que eso tapaba, en el panel de 10 canciones (los MISMOS charts, medidos con
una vara y con la otra):

| | vara vieja (0.25) | vara nueva (0.5) |
|---|---|---|
| Nirvana - Heart-Shaped Box, humano | 0.991 | **0.164** |
| The Outfield - Your Love, humano | 0.929 | **0.085** |
| Dethklok - Thunderhorse, humano | 0.763 | **0.069** |
| desviacion del humano en el panel | 0.376 | **0.041** |
| error nuestro contra el humano | 0.272 | **0.042** |

O sea: **la mitad de la variedad que este proyecto perseguia en los sostenidos
no existia**, y el 85 % del error tampoco. El umbral vive ahora en
`chartio.SOSTENIDO_MIN_TIEMPOS`, con `is_natural_hopo`, y lo leen los tres.

Reminados: `perfil_corpus` 0.1511 -> **0.1068**, `perfil_oro` 0.1068 ->
**0.0956**. Que el oro apenas se mueva (-10 %) y la biblioteca entera caiga un
29 % dice que los 60 del oro ya estaban limpios de esa inflacion.

### 2. El ring no medi­a nada, y ahora mide

`ring_times` avanzaba sobre la energia de toda la mezcla hasta que cayera al
35 % del pico. En una pista donde se toca sin parar eso no pasa nunca. La vara
nueva (`tools/mide_el_ring.py`) pregunta lo unico que importa: al coger una nota
que el humano sostuvo y una que pico, cuantas veces tiene mas ring la sostenida
(AUC; 0.50 es una moneda al aire).

| | medida vieja | `ring_por_tono` |
|---|---|---|
| AUC mediano, 12 canciones | **0.482** | 0.593 |
| AUC minimo | 0.133 | **0.506** |
| canciones donde iba AL REVES | 6 de 12 | **0** |
| ataques clavados en el tope de 6 s | 43.7 % | 1.4 % |
| AUC en Pride & Joy | 0.608 | **0.748** |

`ring_por_tono` mira solo el bin del CQT donde vive la nota mas su octava (la
misma suma armonica del contorno). Esa banda si se apaga aunque la cancion siga
atronando. Y **no muere al primer bache**: hacen falta 3 cuadros seguidos
(~35 ms), porque con uno solo el metal de alta ganancia se quedaba sin un solo
sostenido largo. El canje esta medido en la cabecera de `audio.py`.

### 3. Lo que el generador hace ahora, y lo que se descarto

El objetivo del perfil era una **cuota**: ordenar por hueco y coger las N
primeras. Por eso el ratio salia siempre clavado al objetivo, y por eso las seis
canciones de la §10 salian todas con 0.15. Ahora es un **tope**: filtra el audio
y el compas, y el perfil solo pone el maximo. El contador `SOSTENIDOS` de
`quien_decide.py` enseña por que hacia falta verlo: en Pride & Joy hay 819
candidatos, 408 con hueco suficiente, **280 elegibles y 87 de tope**.

**DESCARTADO CON NUMERO: que el audio decida CUANTOS.** Barrido de 12 reglas
sobre las 12 canciones con guitarra aislada, contra el ratio del charter humano
de cada una:

| largo x tope | ratio medio | error | correlacion |
|---|---|---|---|
| 0.5 x p50 | 0.093 | **0.131** | +0.257 |
| 0.5 x p75 | 0.118 | 0.132 | +0.203 |
| 0.5 x p95 | 0.155 | 0.152 | **-0.212** |
| 0.75 x p95 | 0.127 | 0.157 | -0.156 |
| 1.0 x cualquiera | 0.022 | 0.178 | -0.079 |

Aflojar el tope SI da variedad (desviacion 0.006 -> 0.047) pero la da **al
reves**: donde nuestro audio dice "aqui hay muchos sostenidos", el humano
escribio menos. El ring sabe ordenar QUE notas se sostienen; no sabe decir
CUANTAS.

**DESCARTADO CON NUMERO: la regla del relleno** (exigir que el sonido cubriera
el hueco entero para que contara como sostenido). Movia el ratio medio de 0.103
a 0.098 y dejaba el error igual en 0.208.

### 4. El numero que EMPEORA, y por que se deja asi

El lote de control de 4 canciones pasa de **4.6 a 5.5** en `parecidas.py` -- el
"todas iguales" -- con las mismas semillas y el mismo numero de notas (790, 478,
530, 736, identico antes y despues: lo unico que cambia son los sostenidos).

La causa esta medida y es el gesto `sostenido_largo` (un sostenido de 2 tiempos
o mas), por cada 100 notas:

    antes   0.89   1.46   2.08   3.80      <- de aqui salia la variedad
    ahora   0.00   0.21   0.75   1.09
    humano, medido en el panel: 1.20 de media (desviacion 0.80)

Los 3.80 de Tame Impala no eran musica: eran el ring viejo, que no se apagaba
nunca, estirando la nota hasta la siguiente **por encima del silencio** -- que
es exactamente lo que el comentario del codigo llevaba avisando ("un hueco ancho
puede ser un silencio"). Es la misma forma que el "contraste" refutado el 22-08:
una medida de variedad alimentada por un defecto.

Pero el saldo honesto es que **seguimos 8 veces por debajo del humano en
sostenidos largos** (0.13 contra 1.20 por 100 notas) y ahora se sabe donde
duele: en el metal de alta ganancia el ring todavia se queda corto
(Thunderhorse pide 1.30 s y damos 0.49). Ahi esta la variedad que falta, y es
la tarea siguiente.

### Estado de la cancion de referencia

| | 22-08 | tras el genero | ahora |
|---|---|---|---|
| notas | 819 (83.4 %) | 819 | 819 |
| F1 | 0.586 | 0.586 | 0.586 |
| distancia de gestos | 0.071 | 0.071 | **0.066** |
| sostenidos (vara nueva) | 0.106 | 0.106 | **0.095** |

## El ring SI separa, y la medida que decia que no estaba mal hecha (23-08-2026)

La tarea escrita decia: *"el ring dice cuanto suena una nota y NO dice si el
humano la sostuvo (AUC mediano 0.586, 1 de 12 canciones separa), asi que hay que
probar el contorno de tono"*. Las dos mitades resultaron falsas, y la primera es
la que importa.

### La medida contaba las notas que no pueden sostenerse

`mide_el_ring.py` emparejaba TODAS las notas humanas con su ataque y preguntaba
si la sostenida tiene mas ring que la picada. El problema es que la inmensa
mayoria de las notas de un chart **no puede sostenerse**: la siguiente entra
antes. En Pride & Joy son 13 sostenidas contra 860 picadas.

Se anadio al medidor una senal de referencia que **no es del audio**: el hueco
hasta la nota siguiente del propio humano. Sobre las 12 canciones con guitarra
aislada:

| senal | AUC mediano | minimo | separan (>= 0.70) |
|---|---|---|---|
| ring | 0.586 | 0.499 | 1 de 12 |
| tono | 0.565 | 0.442 | 1 de 12 |
| ambas | 0.575 | 0.458 | 1 de 12 |
| **hueco** | **0.990** | 0.919 | **12 de 12** |

Un 0.990 no es un hallazgo, es la trampa: **un sostenido OCUPA el hueco**. No se
puede escribir una nota de 1.2 tiempos donde la siguiente entra a 0.1 s, asi que
el hueco no *predice* el sostenido, lo *permite*. Es la misma familia que el
"contraste" refutado el 22-08 y que el ring viejo que no se apagaba nunca: una
medida alimentada por su propia mecanica.

### Repetida donde hay decision que tomar, se da la vuelta

La pregunta honesta es otra: **entre las notas que SI tienen sitio**, cual
sostuvo el humano. Filtrando por hueco >= 0.5 s (a 120 BPM, una corchea larga),
que deja 7 de las 12 canciones con al menos 5 notas de cada clase:

| senal | AUC mediano | minimo | maximo | separan |
|---|---|---|---|---|
| **ring** | **0.727** | 0.572 | 0.944 | **5 de 7** |
| hueco | 0.580 | **0.193** | 0.853 | 3 de 7 |
| tono | 0.548 | 0.465 | 0.768 | 2 de 7 |
| ambas | 0.561 | 0.539 | 0.869 | 2 de 7 |

**El ring ya cumplia el objetivo de 0.70 que el bloque de tarea daba por
incumplido.** Y el hueco, que parecia perfecto, cae a 0.580 con un minimo de
0.193 -- peor que una moneda -- en cuanto se le quita la mecanica.

### El contorno de tono: DESCARTADO CON NUMERO

La idea era razonable: una cuerda dejada sonar mantiene su tono, y una nota
picada cede el sitio a la siguiente aunque su banda tarde en apagarse. Se puso
como `audio.tono_firme_por_ataque` -- cuantos segundos el contorno de Viterbi
sigue diciendo esa nota -- y no cuesta nada, porque `analyse` ya calcula el
contorno ANTES del ring.

No separa: **0.548 contra 0.727 del ring**, y combinarlos con el minimo tampoco
(0.561). Se deja el campo `Onset.tono_firme` puesto porque el medidor lo usa y
es barato, pero **no manda en nada**.

### Ordenar por el ring: DESCARTADO CON NUMERO, y por que era predecible

Con el ring ya validado, lo siguiente parecia claro: en `assign_notes` los
elegibles se ordenan por `lengths`, y `lengths` es `min(hueco, ring)`, o sea que
el hueco -- que no sabe -- entraba en la decision. Ordenar por el ring solo:

    Pride & Joy         F1 0.586, distancia 0.066, sostenidos 0.095   (identico)
    lote de control 4   parecidas 9.3 -> 9.9
                        sostenido_largo por 100 notas 0.10 -> 0.06

Nada, o algo peor. La razon esta en la propia formula y se podia haber visto
antes: **para ser elegible una nota necesita hueco ancho**, asi que en el
conjunto que se ordena `min(hueco, ring)` YA es el ring casi siempre. El ring
mandaba donde podia mandar desde el commit anterior.

### La trampa de medida de esta tanda

El lote de control de 4 se regenero desde el `song.mp3` que vive dentro de la
carpeta de salida, y no desde la carpeta original de la biblioteca. Sale otro
chart: 897 notas contra 790, 745 contra 478, y `sostenido_largo` medio 0.10
contra 1.10. La causa es que **una carpeta de la biblioteca trae la letra
alineada y un mp3 suelto no**, y las silabas anclan la melodia. Los numeros de
arriba valen como A/B (las dos columnas se generaron igual) pero **no son
comparables con el 5.2 de `salida/alternancia_env`**.

## La densidad: tres reglas medidas, ninguna gana, y por que (23-08-2026)

La tarea escrita mandaba que la densidad la pusiera el propio audio en vez del
p50 del bucket de BPM. Se midio antes de tocar el generador, como pedia el
bloque. **Ninguna regla gana**, y lo que salio de intentarlo vale mas que el
cambio.

### Las reglas, contra las 12 canciones con guitarra aislada

La vara es cuantas notas por segundo puso la persona. La regla candidata
necesita una fraccion (que parte de los ataques detectados acaba siendo nota), y
esa fraccion **se saca de las otras once canciones, nunca de la que se juzga**:
sacarla de las doce le regala su propio caso y sube la nota sin merecerlo.

| regla | error medio | error mediano | correlacion | rango que sabe decir |
|---|---|---|---|---|
| perfil del oro (hoy) | 0.926 | 0.767 | **+0.038** | 3.9 - 4.4 |
| fraccion de los ataques | 0.905 | 0.765 | +0.317 | 2.9 - 4.6 |
| recta sobre los ataques | 1.041 | 0.974 | -0.111 | 2.8 - 4.7 |
| media de las dos | 0.937 | 0.721 | -0.101 | 3.5 - 4.4 |
| **constante (la mediana)** | **0.960** | 0.812 | -0.753 | 3.6 - 3.8 |

El humano va de **1.22 a 4.95** notas/s, con desviacion 1.15.

Dos cosas que hay que leer juntas: la regla de hoy tiene **correlacion +0.038 con
lo que escribio la persona**, o sea ninguna, y **apenas le gana a decir siempre
el mismo numero** (0.926 contra 0.960). No es que se equivoque de poco: es que
no sabe expresar la diferencia entre una balada y un thrash.

### El perfil del oro aplano la densidad

El 23-08 se adopto el perfil de los 60 charts de oro porque el de todos era "la
mediana de lo mediano". Para el estilo esta bien. **Para la densidad fue un tiro
en el pie**, porque los 60 son todos densos y sus buckets de BPM dejan de
distinguir:

    oro (60)      3.92  4.08  4.42  4.27  6.43   <- el de 160-190 es MENOR que
    todos (392)   3.25  3.32  3.88  4.38  4.89      el de 130-160: eso es ruido

Sobre las mismas 12 canciones, tomar la densidad de los 392 y dejar el resto en
el oro: error 0.926 -> **0.874** y correlacion 0.038 -> 0.173. Parecia el
arreglo.

### Y en los charts de verdad sale al reves: DESCARTADO CON NUMERO

Panel de 10 canciones, con el codigo de hoy en las dos columnas:

| | oro (hoy) | densidad de los 392 |
|---|---|---|
| distancia de gestos al humano | **0.384** | 0.421 |
| error de notas/s | **1.033** | 1.077 |
| F1 | 0.505 | 0.510 |
| error de repeticion | 0.150 | **0.135** |
| error de ligadas | 0.115 | **0.094** |
| canciones que mejoran | -- | 3 de 10 |

**El objetivo mejoro y el chart empeoro.** La razon es la seccion siguiente, y
es la leccion que hay que llevarse: *una regla de densidad no se puede juzgar
por su objetivo, porque el generador no entrega su objetivo.*

### El generador no cumple su propio presupuesto

`quien_decide.py` sobre cinco canciones. El presupuesto se gasta **antes** de
tirar las notas que quedan demasiado juntas, asi que lo que sale siempre es
menos de lo que se pidio:

| cancion | presupuesto | tiradas por el hueco minimo | finales | |
|---|---|---|---|---|
| Pride & Joy | 917 | 74 | 819 | -10.7 % |
| AC/DC - Thunderstruck | 1508 | 168 | 1312 | -13.0 % |
| Nirvana - Teen Spirit | 1263 | 121 | 1120 | -11.3 % |
| Audioslave - Like a Stone | 1229 | 82 | 1113 | -9.4 % |
| Chicos De Barrio - Mucha Lucha | 733 | 36 | 697 | -4.9 % |

Por eso bajar el objetivo (los 392 piden menos que el oro) hizo el chart mas
flaco todavia: ya llegabamos por debajo.

Y el recorte **no es un error**: medido en los 392 charts humanos y 364.327
huecos, solo el **7.8 %** de los huecos humanos baja del umbral de Experto
(0.235 tiempos), y por cancion la mediana es **1.1 %**. Lo que pasa es que
nuestro detector produce ataques mas apretados que las notas de un charter
(en Pride & Joy el recorte se lleva el 8.3 %), asi que el recorte esta
corrigiendo al detector con el presupuesto ya gastado.

(Ese 7.8 % es de estilo, no de regla: Van Halen - Eruption tiene el 88.2 % de
sus huecos por debajo, Misirlou el 70.6 %. 79 charts de 392 pasan del 10 %.)

### El numero que resume el problema, y la tarea siguiente

En el panel de 10, la media de densidad ya es casi la buena -- 3.81 nuestra
contra 3.72 humana. Lo que no se parece es el REPARTO:

    el humano va de   1.90  a  5.94   notas/s   (3.1 veces)
    nosotros de       3.16  a  4.30             (1.4 veces)

Escribimos 3.16 donde la persona puso 5.94 (Thunderhorse) y 4.30 donde puso 1.90
(La Tortura). **La densidad es lo mas audible de un chart y la nuestra casi no
varia**, que es la explicacion mas directa que ha aparecido del "siento que
estoy tocando las mismas canciones".

## La fuga del presupuesto: arreglada, medida, y NO adoptada (23-08-2026)

La tarea decia que esto iba primero, y tenia razon por un motivo que solo se ve
al hacerlo.

### El arreglo, que funciona

El presupuesto de notas se gastaba **antes** del recorte de "demasiado juntas",
asi que el chart salia siempre por debajo de lo que se habia pedido. Ahora se
coge por prioridad comprobando el hueco minimo sobre la marcha (`bisect` sobre
los beats ya elegidos), de forma que una nota descartada por estar pegada deja
su sitio a la siguiente en vez de perderlo.

En Pride & Joy, y mejora **todo**:

| | antes | con el arreglo | humano |
|---|---|---|---|
| notas | 819 (83.4 %) | **859 (87.5 %)** | 982 |
| tiradas por el hueco minimo | 74 | **18** | |
| recall | 0.538 | **0.557** | |
| F1 | 0.586 | **0.595** | |
| distancia de gestos | 0.066 | **0.055** (91 % del camino) | |
| notas/s | 3.693 | **3.873** | 4.474 |
| ligadas | 0.217 | **0.226** | 0.390 |
| variacion | 0.147 | **0.156** | 0.178 |
| ventaja de melodia | +22.2 % | **+19.7 %** | +18.1 % |

### Y en el panel de 10 empeora justo la queja de Bruno

| | base | con el arreglo |
|---|---|---|
| distancia de gestos | **0.384** | 0.420 |
| **"todas iguales"** | **6.9 veces** | **8.3 veces** |
| error de notas/s | **1.033** | 1.072 |
| F1 | 0.505 | **0.522** |
| canciones que mejoran | -- | 2 de 10 |

### Por que, y es el hallazgo de la tanda

Partiendo el panel en dos segun si el generador iba corto o pasado de densidad:

| | error de densidad antes | despues |
|---|---|---|
| donde ibamos CORTOS (5) | 0.950 | **0.803** |
| donde ibamos PASADOS (5) | 1.116 | **1.341** |

El arreglo hace exactamente lo que promete: entrega el presupuesto. El dano sale
entero de que **el presupuesto esta mal en la mitad de las canciones**, porque el
objetivo solo sabe decir entre 3.9 y 4.4 (correlacion +0.038 con el humano).

Y de ahi lo importante: **la fuga estaba tapando el objetivo malo**, y como cada
cancion perdia una cantidad distinta (de -4.9 % a -13.0 %), estaba dando
**variedad por accidente**. Al taparla, todas las canciones convergen en el mismo
sitio y el "todas iguales" sube de 6.9 a 8.3.

Es la misma forma que el `ring` viejo (variedad falsa por una medida rota) y que
el "contraste" del 22-08. La diferencia esta en la decision: alli el arreglo
mejoraba lo que se pretendia medir, aqui empeora todo lo que le importa a Bruno.
Por eso **se revierte y se deja escrito entero en el codigo**, con sus numeros,
para volver a ponerlo en un paso en cuanto el objetivo varie.

### Y la densidad de los 392 se vuelve a caer, ahora con el arreglo puesto

Se probaron las dos juntas, por si la fuga era lo que impedia juzgar la regla:

| panel de 10 | base | +presupuesto | +densidad 392 | las dos |
|---|---|---|---|---|
| distancia | **0.384** | 0.420 | 0.421 | 0.426 |
| F1 | 0.505 | **0.522** | 0.510 | 0.489 |
| error de notas/s | **1.033** | 1.072 | 1.077 | 1.066 |
| mejoran | -- | 2/10 | 3/10 | 1/10 |

Nada gana. **El orden correcto queda demostrado, no supuesto:** primero que el
objetivo VARIE, y solo despues se entrega. Ninguna de las dos piezas sirve sola.
## La densidad no se predice, y la regla tonta lo demuestra (24-08-2026)

La tarea escrita pedia que el objetivo de densidad **variase**: la media ya
acertaba (3.81 nuestra contra 3.72 humana) pero el reparto no, porque el humano
va de 1.90 a 5.94 notas/s y nosotros de 3.16 a 4.30.

### La mejor regla que se ha medido

Sobre los 392 charts humanos, contra la densidad que escribio cada persona:

| regla | error | correlacion | rango |
|---|---|---|---|
| todos la mediana (**la regla tonta**) | 1.002 | — | 1.0x |
| bucket de BPM, 5 tramos | 0.902 | +0.398 | 1.5x |
| BPM por cuantiles, 20 tramos | 0.865 | +0.444 | 1.8x |
| recta sobre el BPM | 0.903 | +0.421 | 2.2x |
| **recta sobre el BPM + desvio de genero** | **0.865** | **+0.481** | **2.7x** |

Contra el +0.038 de correlacion que tenia el objetivo de hoy, eso es otra liga.
Se minó en `corpus.aggregate` como recta + desvios + la referencia de esa tanda
(nunca como niveles, para poder aplicarla como factor sobre el perfil del oro,
que es otra poblacion) y se le presta al oro igual que los bloques de genero.

### Y aun asi el chart sale peor

| | hoy | con la recta |
|---|---|---|
| panel, distancia de gestos | **0.384** | 0.412 |
| panel, F1 | 0.505 | **0.518** |
| panel, error de notas/s | 1.033 | **1.009** |
| panel, error de ligadas | 0.115 | **0.101** |
| "todas iguales" | 6.9 | **6.0** |
| Pride & Joy, distancia | 0.066 | **0.053** |
| canciones que mejoran | — | 3 de 10 |

Casi todas las columnas mejoran y la que manda empeora. El dano se concentra
donde la recta **no puede** acertar: *Thunderhorse* va a 92 BPM y su humano
escribio 5.94 notas/s, asi que cualquier regla que baje la densidad de lo lento
le da de lleno (0.278 → 0.459). Las dos latinas y las dos de pop, que ya estaban
por encima de 0.6, tambien empeoran.

Y que Pride & Joy diera **la mejor distancia de la historia del proyecto**
(0.053, el 91 % del camino hacia su chart) mientras el panel empeora es la regla
de CLAUDE.md en carne viva: una cancion no decide nada.

### La regla tonta remata la linea entera

Sobre las 22 canciones con guitarra aislada (las 12 de la calibracion mas las 10
del panel), decir **siempre la mediana**:

| | error | correlacion |
|---|---|---|
| **la regla tonta** | **0.862** | 0.000 |
| la recta del BPM | 0.974 | +0.263 |
| los ataques del detector x 0.379 (lo mejor posible) | 0.931 | +0.285 |
| mezclas geometricas de las dos (5 pesos) | 0.915 – 0.941 | +0.32 a +0.34 |

**Ninguna le gana a no saber nada.** Y se ve por que: el humano va de 1.22 a
5.94 notas/s y ninguna regla se atreve a salir de 2.8–5.1, asi que la
correlacion sube y el error no baja.

Con esta son **tres reglas de densidad medidas y descartadas en dos tandas** --
el audio, los 392 en vez del oro, y la recta --, y la conclusion ya no es de una
regla concreta: **la densidad de una cancion no se predice con lo que tenemos**
(BPM, genero y tasa de ataques). Lo que queda de la linea es el arreglo de la
fuga del presupuesto, que sigue escrito y medido en `generate.py` sin adoptar, y
que solo tiene sentido el dia que haya un objetivo que merezca entregarse.

La recta se sigue minando: la medida es buena, y es la que dice que un chart a
190 BPM lleva un 50 % mas de notas que uno a 100.

## No es que los gestos no se encadenen: es que solo sabemos dos (24-08-2026)

La tarea escrita era usar `datos/transiciones.json` -- las matrices de que gesto
va despues de cual, minadas el 22-08 sobre 607 pistas y sin usar -- para que un
gesto llevara al siguiente. Antes de tocar nada se midio lo que ya escribimos,
con la propia herramienta que las mino (`tools/transiciones.py --biblioteca
<lote> --comparar datos/transiciones.json`), y la premisa se cayo.

### La persistencia no era el problema

| gesto | humano | nosotros | pares nuestros |
|---|---|---|---|
| anclado | 79 % | 74 % | 518 |
| salto_ancho | 68 % | 56 % | 242 |
| cadena_sostenidos | 14 % | 11 % | 55 |
| zigzag | 15 % | 12 % | 57 |
| galope | 18 % | 8 % | 59 |

Encadenamos casi como el humano en lo que escribimos. **El problema es lo que no
escribimos.** Sobre 48 250 transiciones humanas y 1 040 nuestras, que gesto es
cada una:

| gesto | humano | nosotros | x |
|---|---|---|---|
| anclado | 31.1 % | **49.1 %** | 1.58 |
| salto_ancho | 23.7 % | 25.6 % | 1.08 |
| **sostenido_largo** | **12.4 %** | **1.2 %** | **0.09** |
| acorde_martillo | 5.5 % | 1.7 % | 0.31 |
| escalera_baja | 5.4 % | 0.9 % | 0.16 |
| escalera_sube | 4.8 % | 2.7 % | 0.56 |
| tremolo | 3.3 % | 0.3 % | 0.09 |
| galope | 2.5 % | 5.5 % | 2.20 |
| zigzag | 1.9 % | 4.6 % | 2.44 |

`anclado` + `salto_ancho` son el **74.7 %** de nuestros gestos y el 54.8 % de los
suyos. Encadenar un vocabulario de dos no puede dar variedad, asi que las
matrices no eran la tarea: la tarea es tener el vocabulario.

### Y el que mas falta no se arregla escribiendo sostenidos

Herramienta nueva, `tools/mide_los_huecos.py`, sobre el panel de 10:

| | humano | nosotros |
|---|---|---|
| huecos de 2.22 tiempos o mas | **1.45 %** | **0.18 %** |
| sostenidos de 2 tiempos o mas | 1.13 % | 0.17 % |
| cuando el hueco existe, se usa | 77.8 % | **94.8 %** |
| hueco mediano | 0.500 t | 0.467 t |

O sea que la maquinaria de sostenidos **no falla: es mas ansiosa que el humano**,
y el hueco mediano es casi el mismo. Lo que falta es la COLA. El humano es
irregular -- muchos huecos cortos y algunos agujeros de verdad -- y nosotros
repartimos parejo. Es "todas se sienten iguales" dicho con la regla del compas.

### Tres maneras de dejar sitio, y las tres cuestan mas de lo que dan

Todo en el panel de 10, mismas semillas:

**1. Bajar el suelo de contraste** (0.35 → 0.20 → 0.10). No es por ahi: los
huecos pasan de 0.18 % a 0.19 % y 0.24 %. Y "todas iguales" se va de 6.9 a
**8.2 y 8.1**, porque cuando manda el contraste todas las canciones adoptan la
misma forma -- fuerte donde suena fuerte, vacio donde no.

**2. Quitar el premio a la rejilla** (0.35/0.12 → 0.12/0.04 → 0/0). Si hace
agujeros (0.28 % y 0.79 %) y el **F1 sube mucho** (0.505 → 0.536 y 0.533),
porque las notas dejan de ir donde manda el compas y van donde suena. Pero la
distancia de gestos empeora (0.401 y 0.411) y "todas iguales" se va a 7.2 y 8.8.
La rejilla no sobra.

**3. Elegir FRASES en vez de notas** (`RACHA_VENTANA`: suavizar la puntuacion de
`thin` sobre las vecinas antes de cortar, el mismo truco que subio las rachas de
acordes de 1.58 a 5.31):

| | hoy (1) | racha 2 | racha 3 | racha 5 | humano |
|---|---|---|---|---|---|
| huecos ≥ 2.22 t | 0.18 % | 0.77 % | **1.45 %** | 2.08 % | 1.45 % |
| sostenidos ≥ 2 t | 0.17 % | 0.54 % | 0.84 % | 1.19 % | 1.13 % |
| panel, distancia | **0.384** | 0.396 | 0.397 | 0.418 | |
| panel, F1 | 0.505 | **0.543** | 0.523 | 0.508 | |
| "todas iguales" | **6.9** | 7.0 | 7.1 | 9.6 | |
| error de ligadas | **0.115** | 0.132 | 0.150 | 0.137 | |

Con racha 3 **el agujero sale clavado al humano** (1.45 contra 1.45) y el gesto
que faltaba se multiplica por cinco. Y aun asi no pasa la puerta: la distancia de
gestos empeora en las tres y **las ligadas se estropean**, porque una ligadura
necesita que las notas vayan seguidas y las frases las separan. Queda apagado en
el codigo con su tabla; se enciende cambiando un numero.

### Dos cosas mas que quedan escritas

- **Un no-op que parecia obvio:** eximir al sostenido largo de la cuota del
  perfil. `elegibles` va ordenada por largo, asi que el tope corta por abajo y
  los largos ya estaban todos dentro; exentarlos no movio ni una milesima.
- **Donde esta el limite ahora:** con los huecos puestos (racha 3) solo se
  aprovecha el **57.9 %** de ellos contra el 77.8 % del humano, y eso ya no es
  la cuota sino el `ring` -- en el resto de esos huecos la cuerda ya no suena.
  Ahi es donde miraria el siguiente.


## La ligadura estaba medida con media regla, y aun asi no se predice (24-08-2026)

### El lector de `.mid` tiraba 84.462 marcas

La cabecera de `midiio.py` lo decia desde el primer dia -- `base+5` obliga a
ligar, `base+6` obliga a rasguear -- y el codigo se quedaba con `base <= pitch
<= base+4`. Los cinco trastes, y las dos marcas a la basura. Es la trampa de
CLAUDE.md §2.5 en un sitio nuevo: una medida que no aplica la regla del juego no
mide lo que crees.

Pesaba 84.462 marcas en 224 charts (22.817 de ligar, 61.645 de rasguear: el
humano usa la marca sobre todo para QUITAR ligadura, no para ponerla).

| medido igual, ExpertSingle | antes | ahora |
|---|---|---|
| mediana de los 224 `.mid` | 0.106 | **0.142** |
| mediana de los 168 `.chart` (se leian bien) | 0.167 | 0.167 |
| desacuerdo entre los dos formatos | 1.58x | **1.18x** |

Lo delataba justo eso: dos formatos que hablaban de cosas distintas, la misma
forma que el capitulo de los sostenidos. Por cancion el efecto es grande aunque
la media del panel se mueva poco -- Master of Puppets 0.096 -> **0.158** (tiene
2.134 marcas de rasgueo y 399 de ligar), Sex Pistols 0.057 -> 0.081, Ha-Ash
0.003 -> 0.061 -- y en el panel entero el **error de ligadas baja de 0.115 a
0.105 sin tocar el generador**. Ese 0.010 no era el chart, era el lector. Nada
mas se movio: distancia 0.384, F1 0.505, nps, acordes, sostenidos y repeticion
identicos.

**La traduccion no es directa, y creerlo da lo contrario de la verdad.** El
`.mid` escribe DOS marcas y el `.chart` UNA, `N 5`, que INVIERTE lo que el juego
decidio solo. Mapear las dos a `N 5` a pelo saca a Master of Puppets con **0.904
de ligadura**, que en una cancion de downpicking es absurdo. La marca se escribe
solo cuando el charter CONTRADICE al juego, y quien dice lo que decide el juego
es `chartio.is_natural_hopo`, la misma que usa el generador.

Dos cosas medidas antes de escribir el codigo: las marcas caen justo sobre la
nota **84.454 de 84.462 veces** (el 0.7 % abarca mas de una, y se ignora), y el
tap (nota 104) **no aparece ni una vez** en esta biblioteca, asi que no se
implementa lo que no se puede medir.

### Con la regla entera tampoco se predice: es la densidad otra vez

392 charts, ligadura mediana 0.154 y una desviacion de 0.208 -- se mueve
muchisimo. Y no se sabe con que.

| regla | error absoluto medio |
|---|---|
| **decir siempre la mediana (0.154)** | **0.1470** |
| la mediana de SU genero (dejandolo fuera) | 0.1406 |
| una recta sobre la densidad | 0.1509 |

El genero compra un 4 % sobre la regla tonta y la densidad **pierde contra**
ella. Los generos si se ordenan (metal 0.222, rock 0.153, latino 0.143, pop
0.084, punk 0.068) pero la desviacion DENTRO de cada uno es de 0.18 a 0.28: se
traga el orden entero. Correlacion con la densidad, +0.128.

Y en el panel de 10, con la vara ya arreglada: nuestro sistema da 0.105 y decir
siempre la mediana del panel da **0.070**. Escribimos 0.186 de media con una
desviacion de 0.066 contra un humano que va a 0.114 con 0.095, y la correlacion
entre lo que escribimos y lo que escribio el es **+0.285**. O sea que ponemos
casi lo mismo en todas: en Pride & Joy nos quedamos cortos (0.217 contra 0.390)
y en ocho de las diez del panel nos pasamos. **Ni pocas ni muchas: siempre las
mismas.**

### Lo que NO es la causa, medido para no volver

- **No son las tasas de `hopo_flags`.** Estan calibradas por caso sobre los
  charts humanos y siguen bien.
- **No es donde caen las notas.** Sitios donde se puede cortar por cada sitio
  donde se puede ligar: nosotros **0.92**, el humano **0.87**. (Una medida
  anterior daba 1.57 y estaba hecha sobre una muestra mezclada de varios lotes:
  el aviso de CLAUDE.md §2.3 aplica tambien a los charts propios.)

### Lo que SI es la causa: la ligadura no viene en rachas

| | nosotros | humano |
|---|---|---|
| racha media de ligadura natural | **1.66 notas** | **3.16 notas** |
| naturales que ARRANCAN racha | 60.3 % | 31.6 % |
| huecos de una semicorchea o menos | 22.9 % | 34.0 % |
| huecos de una negra | 24.2 % | 13.8 % |

Y eso decide el desequilibrio, porque `FORCE_CUT_RUN_START` (0.214) es **cuatro
veces** `FORCE_CUT_IN_RUN` (0.055): el que abre la frase se rasguea, el resto se
liga. Con nuestras rachas de 1.66 casi toda nuestra ligadura paga la tasa cara,
y las marcas salen **64 % cortes** contra el 56 % que saldria con el reparto
humano (y el 47 % que el humano escribe de verdad).

Es la tercera vez que sale lo mismo con otro nombre: nuestro ritmo reparte
parejo y el humano agrupa. Los acordes ya se arreglaron asi (`CHORD_RUN_WINDOW`,
rachas de 1.58 a 5.31), y explica por que `RACHA_VENTANA = 3` estropeaba las
ligadas -- tocaba la palanca buena en la direccion contraria, separando en
frases lo que hay que juntar.


## La ligadura no se encadena porque el RITMO no se encadena (24-08-2026)

La tarea pedia rachas de ligadura de 1.66 a >= 2.8. Lo primero fue poner la
medida, que no existia: `medir_hopo.py` da ahora `racha_natural` y `racha_real`.
Con ella, el control: nosotros 1.60 de media en el panel, los 168 `.chart`
humanos 2.97.

### Que rompe nuestras rachas: no es el traste, es el ritmo

| que corta la racha | nosotros | humano |
|---|---|---|
| **hueco largo** | **74.9 %** | **59.1 %** |
| mismo traste | 13.6 % | 26.8 % |
| acorde | 11.5 % | 14.1 % |

Separando las dos cosas -- cadenas de notas con hueco corto, sin mirar el traste:

| | cadena de ritmo | sigue el ritmo | sigue ligando |
|---|---|---|---|
| nosotros | **1.94** | 46.8 % | 36.9 % |
| humano | **3.04** | 62.0 % | 48.8 % |

El humano escribe tiradas de notas rapidas y nosotros pares. Y la media miente
aqui como en todo: la cadena humana tiene media **7.47** y mediana **3.04**, con
un maximo de 420 (un chart de tremolo entero). El 26 % de los charts humanos esta
por debajo de 2.0, donde estamos nosotros.

### El objetivo escrito estaba sobre la poblacion equivocada

El bloque pedia racha >= 2.8 tomando el 3.16 de los `.chart`. Los DIEZ humanos
del panel, que son contra quien se mide, tienen **racha 1.78 de media y 1.12 de
mediana**, y cuatro de ellos no encadenan ni una vez (racha 1.00). Nosotros
estamos en 1.60: **en la racha, el panel no nos separa del humano.** Lo que si
nos separa en las dos poblaciones es la cadena de ritmo. CLAUDE.md §2.6 otra vez,
y esta vez dentro de un objetivo ya escrito.

### Tres maneras de encadenar, y ninguna pasa

**1. `RACHA_VENTANA`** (suavizar la puntuacion de `thin` y agrupar). Mueve el
histograma de huecos entero -- semicorcheas 21.6 % -> 31.5 %, muy cerca del
34.0 % humano -- y **no alarga la cadena ni una decima** (1.94 -> 2.02). Los
lotes de aquella tanda seguian en disco y nadie les habia medido la cadena.

**2. Un escalon de rejilla para la semicorchea** (`REJILLA_CUARTO`). La idea
obvia: sin el, un ataque en el cuarto de tiempo no cobra NADA de rejilla y no
puede ganarle a una corchea suelta. Con la jerarquia que hay -- tiempo 0.35,
medio 0.06 -- ese escalon es ruido: Pride & Joy, cadena 1.48 -> 1.45.

**3. `CADENA_PREMIO`**: elegir de uno en uno y subir la puntuacion de los vecinos
a distancia de LIGADURA del elegido, para que cada nota tire de la siguiente. Es
la unica de las tres que mueve la palanca:

| panel de 10, mismas semillas | hoy | premio 0.10 | humano |
|---|---|---|---|
| cadena de ritmo | 1.94 | **2.18** | 3.04 |
| racha de ligadura | 1.60 | 1.66 | 1.78 |
| ligadura | 0.186 | 0.212 | 0.114 |
| error de ligadas | **0.105** | 0.124 | |
| F1 | 0.505 | **0.528** | |
| distancia de gestos | **0.384** | 0.412 | |

Sube el F1 y empeora la distancia: **la misma firma que quitar el premio a la
rejilla**, y ya se sabe lo que significa -- el chart va donde suena en vez de
donde manda el compas. Queda apagado con su tabla en `generate.py`.

Y lo que ensena de la tarea, mas que del codigo: **las dos mitades del objetivo
escrito tiran en direcciones contrarias en este panel.** Alargar la cadena SUBE
la ligadura (0.186 -> 0.212) y el humano de estas diez esta en 0.114, asi que
acercarse a la cadena aleja del error. En Pride & Joy si gana entero (distancia
0.066 -> 0.061 y ligadura 0.217 -> 0.264 contra su 0.390) porque su charter esta
en el otro extremo: cadena 3.43 y ligadura 0.390 sin una sola marca escrita.
Una cancion no decide nada, y un objetivo con dos mitades tampoco se cumple a la
vez si nadie comprobo que apuntan al mismo sitio.


### Y el vocabulario NO lo bloquea el ritmo: lo bloquea el traste (24-08-2026)

Antes de dar la tarea siguiente se comprobo lo que la habria hundido: las figuras
del atlas (`tremolo`, `trino`, `escalera_*`, `zigzag`, `rafaga`) se buscan dentro
de rachas de notas sueltas con hueco **<= corchea** y piden largo >= 3 o >= 4. Si
nuestras rachas no dieran para eso, el vocabulario dependeria de la cadena -- que
acaba de quedar descartada.

No es el caso. Rachas de corchea, ExpertSingle:

| | nosotros (10) | humano (165) |
|---|---|---|
| rachas | 1.143 | 17.945 |
| con largo >= 4 | **49 %** | **41 %** |
| reparto de largos (2/3/4/5/6/7/8+) | 33/18/12/10/6/4/17 % | 40/19/12/7/5/3/14 % |

O sea que **tenemos el sitio de sobra** y la distribucion es casi la misma. La
diferencia esta entera en el traste: de las rachas de largo >= 4,

| | nosotros | humano |
|---|---|---|
| **un solo traste (tremolo)** | **0.7 %** | **14.4 %** |
| dos trastes | 20.3 % | 15.8 % |

El humano **se compromete con un traste** durante una tirada rapida una vez de
cada siete, y nosotros una de cada ciento cuarenta. Y eso es una decision de
traste sobre notas que ya estan puestas, asi que no paga la distancia de gestos
que pagaron las tres maneras de tocar el ritmo. Ademas repetir traste **no es
ligadura** (el juego no liga la misma nota), asi que sube la cadena sin subir la
ligadura -- que es justo lo que hace falta, porque en el panel ya escribimos
0.212 contra su 0.114.

Y el control del vocabulario, con `tools/transiciones.py --comparar`: 1.040
transiciones nuestras, `anclado` 518 pares y `salto_ancho` 242, o sea el **73 %**
entre los dos. Cuatro gestos que el humano persiste y nosotros abandonamos al
**0 %**: `acorde_martillo` (el 50 % suyo), `acorde_alterno` (38 %), `acorde_movil`
(18 %) y `trino` (17 %).


## El tremolo: la tasa era buena y el banco se lo comia (24-08-2026)

### El primer sospechoso solo tenia media razon

El bloque apuntaba a `ALTERNANCIA_PROB = 0.45`. La medida dice que **la tasa ya es
correcta** -- pasos de traste dentro de las rachas de largo >= 4 (562 nuestras,
7.526 humanas):

| paso de traste | nosotros | humano |
|---|---|---|
| **0 (repite)** | **24.5 %** | **29.8 %** |
| ±1 | 55.8 % | 49.4 % |
| ±2 | 12.2 % | 13.2 % |
| mas | 7.5 % | 7.6 % |

Lo que es otra cosa es **como se reparten esos ceros**:

| ceros por tirada | nosotros | humano |
|---|---|---|
| ninguno | 26 % | **45 %** |
| exactamente uno | **33 %** | 17 % |
| dos | 21 % | 10 % |
| tres | 8 % | 10 % |
| cuatro o mas | 12 % | **19 %** |

El humano es **bimodal**: o no repite el traste ni una vez, o repite mucho.
Nosotros nos quedabamos en "exactamente uno", que es justo donde el casi no esta.
Y la causa estaba a la vista: `rng.random() < alternancia` se sorteaba **nota a
nota**, y un sorteo independiente no puede ser bimodal.

**Descartado con numero:** tomar esa decision una vez por tirada. Panel de 10,
error de repeticion 0.150 -> 0.143 y de ligadas sin cambio, F1 igual, y la
distancia de gestos **0.384 -> 0.399**, mejorando 1 de 10. La causa de que no
baste esta medida y es la util: **la alternancia solo decide el 9.0 % de los
carriles.** `tools/quien_decide.py` sobre Pride & Joy, 818 decisiones --

| quien decide | notas | % |
|---|---|---|
| contorno | 593 | **72.5 %** |
| motivo del banco | 126 | 15.4 % |
| alternancia de nota repetida | 74 | 9.0 % |
| anti-repeticion | 19 | 2.3 % |

Comprometerse no puede escribir un tremolo que el contorno no ofrezca, ni salvar
el que se lleve el banco.

### La causa: `flat_run >= 3` le pasa el mando al banco justo ahi

El patron que lo delata: tiradas con TRES trastes repetidos seguidos las hacemos
casi como el humano (29.0 % de nuestras rachas contra su 32.1 %) y tiradas
ENTERAS de un solo traste casi nunca. Algo rompe siempre la cuarta. Y esta escrito
en `assign_frets`:

```python
if flat_run >= 3:
    # The audio stopped telling us anything useful; borrow a shape.
    decide = "motivo del banco"
```

Tres notas seguidas sin que el tono se mueva y el generador declara que el audio
no dice nada, asi que presta una FORMA de tres carriles -- que por definicion
mueve la mano. **Pero un tono plano con las notas pegadas no es el audio
callandose: es el audio diciendo tremolo.**

Que no es un artefacto del largo. De cada largo, cuantas rachas van a un solo
traste:

| | largo 4 | largo 5 | largo 6-7 | largo 8+ |
|---|---|---|---|---|
| nosotros | 0.7 % | 0.9 % | 1.7 % | **0.0 %** |
| humano | **19.9 %** | 7.0 % | **19.0 %** | **10.0 %** |

El humano hace tremolo en todos los largos, hasta ocho notas seguidas al mismo
traste; nosotros en ninguno.

### Dos cosas mas del banco, medidas al comprobar si tenia la culpa

- **`000` es el trigrama MAS frecuente de todo el corpus** (2.560, por delante de
  `321` y `123`), y las formas planas son el **16.7 %** de su peso. El humano hace
  esto constantemente: no es una excepcion.
- Pero el banco pesa con `max(1, min(6, count // 40))`, y ese tope de 6 **aplasta
  la frecuencia**: `000` se lleva 64 y se recorta a 6, lo mismo que una forma 64
  veces mas rara. Las planas acaban siendo el 8.5 % del banco en vez del 16.7 %.
- Y sus formas son **carriles ABSOLUTOS** (`corpus.py`: `trigrams[f"{a[1]}{b[1]}
  {c[1]}"]`), asi que un `000` a mitad de cancion no dice "quedate quieto" sino
  "vete al verde". Aunque el banco ofreciera la forma plana, no haria el tremolo.

### Y el arreglo obvio esta DESCARTADO, por la metrica que le importa a Bruno

No prestar la forma cuando las notas van pegadas. Panel de 10, mismas semillas:

| | hoy | sin banco en lo rapido |
|---|---|---|
| rachas de un solo traste (tremolo) | 0.7 % | **2.8 %** |
| error de repeticion | 0.150 | **0.117** |
| error de ligadas | 0.115 | **0.097** |
| F1 | 0.505 | 0.505 |
| distancia de gestos | **0.384** | 0.399 |
| **"todas iguales"** | **6.9 veces** | **10.6 veces** |
| mejoran | | 4 de 10 |

Acierta en su diana -- cuatro veces mas tremolo, y los dos errores que dependen
de el bajan de verdad -- y **lo mata el 10.6**. La causa es que ese `if` hace DOS
trabajos: sin el, todas las tiradas rapidas de todas las canciones hacen lo mismo
(aguantar el traste), y era el banco el que las hacia distintas. **Matar el
tremolo era el precio de la variedad.**

Es la cuarta vez esta semana que un cambio bueno en su medida se cae en otra, y
las tres anteriores se caian en la distancia de gestos. Esta se cae en
`parecidas`, que es la queja literal de Bruno: **hay que mirar las dos.**

### Por donde va entonces

El arreglo no es quitarle el trabajo al banco: es que el banco **sepa hacer
tremolo**. Las dos cosas medidas aqui y sin tocar son justo eso -- el tope
`min(6, count // 40)` deja las formas planas en el 8.5 % del banco cuando son el
16.7 % del corpus, y las formas son carriles ABSOLUTOS, asi que la que si hay no
puede escribir un tremolo donde este la mano. Arreglando lo segundo el banco
conserva su variedad Y puede quedarse quieto, que es lo que hace el humano.

Una cosa a la vez: en esta tanda no se toca ninguna de las dos.
