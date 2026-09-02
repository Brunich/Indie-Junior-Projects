# Plan: que se sienta que tocas la melodia principal

**La meta, con las palabras de Bruno (22-08-2026):** *"no se siente como si
estuviera tocando la melodía principal (...) literalmente lo que suena de
instrumento, sentir que se esté tocando con la guitarra al mismo tiempo en cada
nota. Y cuando alguien canta y él es la melodía principal con su voz, detectar
cada nota y timearlo bien."*

Y una consecuencia que el pide explicitamente: **solo Experto.** Facil, Medio y
Dificil se congelan. Cuando Experto este bien, las demas salen de el.

---

## 1. El numero que manda

Hasta hoy el proyecto medía si las notas caían donde había un **ataque**. Eso
no es lo mismo que caer donde está **la melodía**, y por eso podíamos tener
F1 0.67 y que se sintiera desconectado.

La medida nueva sale de las 126 canciones de la biblioteca que tienen chart de
guitarra **y** voz, las dos cosas hechas a mano:

| | humano | nuestro |
|---|---|---|
| **silabas cantadas que tienen una nota de guitarra encima** (±60 ms) | **0.59** | **0.42** |
| notas de guitarra que caen sobre una silaba | 0.28 | 0.22 |

Leido en voz alta: **cuando alguien canta, el humano te hace tocar 6 de cada 10
silabas; nosotros 4.** Esas dos de diferencia son exactamente la sensacion de
"la letra va por un lado y yo por otro".

El rango humano es enorme y eso tambien dice algo: *Mr. Brightside* 0.98,
*Blink-182* 0.93, *Blur* 0.88... y *Tame Impala - Feels Like* 0.16. **No todas
las canciones se chartean sobre la voz**, y el generador tiene que saber cuando
si y cuando no. Eso es la fase 2.

La otra cara: solo el 28 % de las notas del humano caen sobre una silaba. O sea
que **el chart no es la melodia vocal**: es la guitarra, que muchas veces va con
la voz y muchas otras hace lo suyo. Copiar la voz nota a nota seria tan malo
como ignorarla.

**Objetivo de este plan:** silabas-con-nota de **0.42 a >= 0.59**, sin que la
densidad se dispare y sin que el banco (f1 0.670) baje.

---

## 2. Por que falla hoy

Tres causas, y las tres estan localizadas:

1. **El generador no sabe que existe la voz.** `thin` elige los ataques mas
   fuertes de cada ventana con un presupuesto. Un ataque que es una silaba
   cantada vale exactamente lo mismo que un golpe de caja.
2. **`lead` no distingue guitarra de voz.** Medido en las cuatro canciones de
   prueba: la de rap (*Milo J, Trueno - Gil*) da `lead` 0.695 y tono valido
   98 %, **igual que las de guitarra**. El detector ve "algo melodico" y no sabe
   si es una Stratocaster o una garganta.
3. **El contorno de trastes sigue el tono del audio, no una melodia.** Cuando en
   ese momento la melodia es la voz, el tono que mide el CQT es la voz mezclada
   con todo lo demas.

---

## 3. Las fases

### F1 — La voz como ancla  *(la mas barata y la que mas se nota)*

Cuando la cancion trae letra alineada, **cada silaba es un sitio donde tiene que
haber nota**, salvo que la densidad no de para tanto.

- En `thin`, un candidato que cae sobre una silaba (±60 ms) sube de prioridad
  por delante de la fuerza y del `lead`.
- Si no hay ningun ataque detectado en esa silaba, se **crea** el candidato: la
  voz esta ahi aunque el detector de ataques no la haya visto.
- Tope: no pasarse de la densidad objetivo. Si sobran silabas, se quedan las que
  caen en tiempo fuerte, que es lo que hace un humano.

**Se mide:** silabas-con-nota, objetivo >= 0.59.
**Control:** banco f1 0.670 y nps 3.4-3.5. Si el nps sube, es que estamos
metiendo notas en vez de cambiarlas de sitio.

### F2 — Quien lleva la melodia, FRASE A FRASE  *(hecha 22-08-2026)*

*"En la de Gil sí hay una guitarra, no toca mucho, pero sí suena. Esas partes de
a huevo se tienen que tocar con guitarra."*

Por ventana de ~4 s, decidir: **manda la guitarra**, **manda la voz**, o **las
dos**. Señales disponibles hoy, todas ya calculadas:

- hay silabas en la ventana (de la letra alineada);
- `lead` medio de los ataques;
- energia en la banda de guitarra (1-5 kHz) **descontando** la banda de voz;
- ataques que NO caen sobre silaba: si hay muchos y son fuertes, hay
  instrumento tocando por su cuenta.

Con eso: si manda la guitarra, se chartea la guitarra (como hoy). Si manda la
voz, se ancla a las silabas (F1). Si van juntas, las silabas mandan y los
ataques de guitarra rellenan.

**Se mide:** silabas-con-nota **por tramo**, no solo global. En los tramos de
voz tiene que subir a 0.8+; en los de guitarra puede ser bajo y estar bien.

### F3 — La ALTURA de la voz, no solo su tiempo

F1 y F2 arreglan *cuando*. Falta *que traste*. Hoy el contorno sale del CQT de
la mezcla; en un tramo cantado eso es la voz + todo lo demas.

- Si el chart trae `PART VOCALS` con alturas (los humanos las tienen: mediana 10
  alturas distintas), **usarlas directamente**: es la melodia escrita por una
  persona.
- Si no, sacar el tono de la voz con un detector de f0 restringido a 80-400 Hz
  sobre la banda vocal, solo en las ventanas donde F2 dice que manda la voz.

**Se mide:** contra `tools/ver_patron.py` y las distribuciones del atlas -- que
el movimiento de mano siga pareciendo humano (±1 al 47 %, quedarse al 31 %).

### F4 — El timing de la letra, comprobado por linea

Bruno: *"el problema es el timing, yo estoy tocando otra parte y está la letra en
otra parte"*.

Hoy se corrige **un desfase global** por cancion y se comprueba que el 80 % de
las lineas tenga canto cerca. Eso deja pasar una deriva lenta: la primera mitad
cuadra y la segunda se va.

- Medir el residuo **linea a linea** despues del desfase global.
- Si la deriva es sistematica, ajustar tambien el estiramiento (ya esta el hueco
  en `Veredicto.deriva`, hoy sin usar).
- Y una comprobacion nueva en `revisar-letra`: **cuantas silabas coinciden con
  una nota del chart**. Si la letra y las notas no coinciden, una de las dos
  esta mal y hay que saberlo sin abrir el juego.

### F5 — Solo Experto

Facil, Medio y Dificil se dejan como estan y **no se vuelven a tocar** hasta que
Experto pase la prueba de Bruno. Cuando pase, se rehacen desde el Experto nuevo.

---

## 4. Las canciones con las que se prueba

Que sean de los cuatro casos que ha nombrado, porque cada uno rompe de una
manera distinta:

| Caso | Cancion | Que tiene que pasar |
|---|---|---|
| voz lleva la melodia | `Tame Impala - Loser` | silabas-con-nota alto casi todo el rato |
| guitarra a ratos, voz el resto | `Milo J, Trueno - Gil` | la guitarra donde suena, la voz donde no |
| instrumental suyo | `Brunich - Electro Guitar Cyber Club` | cada nota del instrumento que suene |
| corrido con guitarra y voz | `MARCOS YTZ - DALI` | las dos, sin que se pise |

Y de referencia, humanas: `The Killers - Mr. Brightside` (0.98),
`Blink-182 - What's My Age Again` (0.93) y `Tame Impala - Feels Like We Only Go
Backwards` (0.16), que es el contraejemplo: ahi el humano **no** sigue la voz.

---

## 5. Lo que puede salir mal

| Riesgo | Que se hace |
|---|---|
| Anclar a la voz sube la densidad | El nps se vigila aparte; si sube, se quitan notas de los huecos, no se relaja el ancla |
| El chart se vuelve "karaoke con botones" y pierde el riff | Por eso F2: la voz solo manda donde manda. El 28 % humano dice que la mayoria de las notas NO son silabas |
| La letra bajada esta mal alineada y arrastra las notas | F4 va antes que F3 por esto: si la letra miente, anclarse a ella empeora todo |
| `Feels Like We Only Go Backwards` (0.16) sale forzado | Es el caso de prueba que demuestra que F2 funciona: si tambien sube a 0.8, F2 no esta decidiendo nada |


---

## 6. Lo que dijo Bruno al probarlo, y lo que salio (22-08-2026)

**DALI:** *"mejoro, pero no estaba siguiendo ninguna melodia ni la voz principal
(...) si se concentra en uno se volveria muy facil. Concentrate en dos, la voz y
el instrumento secundario, sin que se solapen, pasando de uno a otro."*

**GIL:** *"esta estupidamente dificil, ni siquiera se siente que se esta tocando
la cancion en una guitarra. Con la letra, cada silaba seria basicamente cada
nota casi siempre."*

Las dos quejas eran **el mismo fallo**: F1 anclaba a la voz pero seguia metiendo
el relleno de antes encima. Sonaba a dos cosas a la vez y sobraban notas.

F2 lo arregla: mientras se canta, la nota es la silaba y nada mas; las frases se
reparten entre la voz y el instrumento, y nunca dos seguidas del instrumento.

| | F1 | **F2** | humano |
|---|---|---|---|
| DALI | 0.87 | **0.56** | 0.59 |
| Tame Impala | 0.94 | **0.80** | 0.59 |
| Gil | 0.68 | **0.49** (nps 3.19 -> 2.09) | 0.59 |
| JUNIOR H | 0.83 | **0.72** | 0.59 |

**Un techo que conviene saber:** en Gil las silabas van mas juntas que el minimo
fisico entre rasgueos (0.14 s a su tempo). La mitad **no son tocables**. Ese
0.49 no es el reparto fallando, es la mano.

---

## 7. La interfaz para todo el mundo  *(al final, cuando esto este bien)*

Peticion de Bruno, y va la ultima a proposito: *"una interfaz para hacer las
canciones, arrastrarlas y seleccionarlas de forma facil sin poner codigo, hecha
para todos, facil de descargar."*

Ya existe `autochart interfaz` (tkinter, cero dependencias) y hace lo basico.
Lo que le falta para ser lo que pide:

- **Arrastrar y soltar** ficheros y carpetas encima de la ventana. `tkinter` no
  lo trae; se hace con `tkinterdnd2` (pequeno) o con un `.bat` que reciba los
  ficheros soltados sobre el.
- **Que se instale sin saber Python**: un `.exe` con PyInstaller. Ojo, `librosa`
  arrastra `numba` y `scipy` y el ejecutable se va a 300-500 MB. Alternativa
  honesta: un instalador que ponga Python y las dependencias por detras.
- **Que no haga falta la biblioteca de Bruno**: hoy los perfiles medidos
  (`perfil_corpus`, `perfil_voz`, `atlas_patrones`) van en el repo y son la
  vara. Eso ya funciona en cualquier maquina -- **es lo que hace que esto se
  pueda repartir**, porque el criterio viaja con el programa.

**No se empieza hasta que Bruno de por bueno el Experto jugandolo.** Una interfaz
sobre algo que aun cambia de forma hay que rehacerla dos veces.
