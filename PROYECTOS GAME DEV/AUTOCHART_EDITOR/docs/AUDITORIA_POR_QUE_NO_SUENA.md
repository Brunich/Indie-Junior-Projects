# Auditoria: por que el chart no se siente como la cancion

**22-08-2026.** Bruno pidio parar y auditar el proyecto entero: *"siento que se
esta desviando el punto porque ya lleva bastante analisis"*, *"no veo que ninguno
de los charts se parezca a ninguna de las canciones"*, y dejo escrito el criterio
de aceptacion, que es el que manda sobre cualquier medida de aqui:

> *"el resultado al final es que se sienta como si se estuviera tocando ese
> instrumento que se esta tocando, no importa si sea una voz; al final siguen
> siendo notas musicales"* — y — *"cuando cambia de nota suele cambiar el patron
> en el chart"*.

**Veredicto en una linea: el generador hace bien su trabajo sobre una melodia
que no existe.** El contorno de tono que lee del audio no es la melodia de
ningun instrumento; es el bin mas fuerte del CQT saltando de octava. Todo lo
demas del proyecto — gestos, motivos, dificultades, perfil del oro — se construye
encima de eso.

**Informe visual publicado:** https://claude.ai/code/artifact/7593bc41-ede7-418b-9ad0-54409b1680b7

---

## 1. La causa, con la referencia que ya estaba en el proyecto

Una melodia humana se mueve por grados. No hay que suponerlo: el propio proyecto
lo tiene medido en `datos/perfil_voz.json`, sacado de las pistas `PART VOCALS`
escritas a mano de su biblioteca (tono MIDI real, no estimado).

| | melodia humana cantada | el contorno que leemos del audio |
|---|---|---|
| se queda en la misma nota | 35,1 % | — |
| saltos de 3 semitonos o menos | 86,7 % | — |
| salto mediano cuando se mueve | **2 semitonos** | **5 a 12 semitonos** |
| saltos de mas de una quinta | **2,01 %** | **28 % a 59 %** |
| saltos de una octava o mas | **0,55 %** | **11 % a 50 %** |

Entre 14 y 25 veces mas saltos grandes que cualquier melodia que un humano
cante. Eso no es una melodia con ruido: es otra cosa.

**La firma del fallo se ve a simple vista.** En *AC/DC — Thunderstruck*, con la
pista de guitarra AISLADA (`guitar.ogg`, sin bateria ni voz que estorben), el
contorno que sacamos tiene un salto **mediano de 12,0 semitonos exactos** y el
50,1 % de sus saltos son de una octava o mas. El riff de Thunderstruck se mueve
de uno en uno por una sola cuerda. Un estimador que devuelve *exactamente* una
octava como valor tipico no esta oyendo la melodia: esta eligiendo unas veces el
fundamental y otras su armonico.

`autochart/audio.py:390` coge el bin mas fuerte del CQT dentro de la banda de la
solista, **cuadro a cuadro y sin memoria**. Con una guitarra distorsionada el
armonico de octava supera al fundamental la mitad del tiempo, y el tono salta.
Y como el salto de octava **invierte el signo del intervalo**, la direccion del
contorno — que es justo lo que el generador convierte en movimiento de la mano —
sale al azar.

### 1bis. Contrastado contra un seguidor de tono de verdad

`librosa.pyin` es un seguidor monofonico de referencia. Corrido sobre el MISMO
`guitar.ogg` y en los MISMOS cuadros que nuestro estimador, en el primer minuto
de tres canciones de guitarra:

| guitarra aislada | mismo tono | misma nota, otra octava | error mediano |
|---|---|---|---|
| AC/DC — Thunderstruck | 5,0 % | 11,7 % | **17,0 semitonos** |
| Audioslave — Cochise | 0,0 % | **47,3 %** | 12,6 semitonos |
| Alice in Chains — Them Bones | 0,0 % | 22,6 % | 14,0 semitonos |

Un error mediano de mas de una octava no se explica porque pyin sea imperfecto
con una guitarra distorsionada. Y el 47,3 % de *Cochise* — la nota correcta en
la octava equivocada — es la firma del salto de octava, ya sin interpretacion.

**Y hay una causa estructural, escrita a proposito.** `audio.py:63` limita la
busqueda a MIDI 55 (G3) hacia arriba, y el comentario explica por que: cogiendo
el bin mas fuerte de todo el CQT, *"el 61 % de los tonos caia por debajo de
MIDI 52 -- el contorno seguia al acompanamiento"*. El remedio contra "seguia al
bajo" fue **prohibir el registro donde vive la guitarra**: la sexta al aire es
MIDI 40 y el riff de Thunderstruck vive alrededor de MIDI 47. Con el suelo en
55, su fundamental es inalcanzable y el estimador **no puede** devolver otra
cosa que un armonico. De ahi los 17 semitonos.

## 2. Como se comprobo

Herramienta nueva, `tools/sigue_la_melodia.py`: entre nota y nota compara si el
tono sube/baja/se queda contra si el traste sube/baja/se queda, y lo mide contra
el azar de **barajar los trastes de esa misma cancion** (el azar no es 33 %:
depende de cuanto repita trastes cada chart).

Sobre 12 canciones humanas con la guitarra aislada, y sobre nuestras 4 de control:

| | acierto | azar | ventaja |
|---|---|---|---|
| charts HUMANOS (mediana de 12) | 39,2 % | 34,7 % | **+4,7 %** |
| charts nuestros (mediana de 4) | 50,8 % | 35,1 % | **+15,6 %** |

**Ese resultado parece bueno y es el que delata el problema.** Nuestros charts
siguen el contorno tres veces mejor que los humanos porque estan *construidos*
con ese contorno: seguimos fielmente nuestro propio ruido. Los humanos, que
tocan la melodia de verdad, apenas le sacan 5 puntos al azar — porque el
contorno contra el que se les compara no es la melodia que ellos oyeron.

El detalle por cancion lo confirma: donde el riff es de una nota cada vez el
humano sube (*Thunderstruck* +20,3 %, *Cochise* +15,7 %) y donde son acordes de
potencia se desploma (*Blink-182* −4,4 %, *Serj Tankian* −4,9 %).

## 3. Por que nadie lo vio antes

El proyecto tiene 24 herramientas de medida y **ninguna miraba el tono**:

- el banco (F1) mide **cuando** suena la nota — y esta escrito desde hace
  semanas que *no ve los trastes*;
- el atlas, `transiciones.py` y `parecidas.py` miden **que forma** tiene el
  gesto;
- `quien_toca.py` mide **de que instrumento** es el ataque;
- `banco_alineado.py` mide **la letra**.

Ninguna medida del proyecto podia distinguir "toca la melodia" de "toca notas en
el momento correcto con los trastes al azar". Y como todas las demas mejoraban,
todas las tandas iban por ahi.

**La deriva, con numeros:** 156 commits en total, de los cuales **15** tocan
`generate.py`, que es el fichero que decide que nota se toca. 8 documentos de
plan, 27 secciones de medidas en `DECISIONES_MEDIDAS.md` (53 KB), y 4.483 lineas
de herramientas de medida contra 7.162 de codigo del programa. La sensacion de
Bruno de que "ya lleva bastante analisis" tiene respaldo aritmetico.

## 4. Lo que NO era la causa (para no volver ahi)

Todo esto esta medido y descartado en `DECISIONES_MEDIDAS.md`:

- **La sincronia no falla:** el 94,8 % de las notas caen a menos de 50 ms de un
  ataque real.
- **Separar la cancion no lo arregla:** en DALI el contorno mejora algo
  (44,8 % → 28,4 % de saltos grandes) pero sigue lejisimos del 2 % humano; y en
  Thunderstruck la pista aislada sale *peor* que la mezcla. Quitar la bateria no
  arregla un estimador que salta de octava.
- **Ni el peso de lo melodico (`LEAD_PRIORITY`), ni la semilla por cancion, ni
  el perfil del oro.** Los dos ultimos suman y dejan el "todas iguales" en 6,5
  veces contra el objetivo de 3.

## 5. Que hacer, en tres pasos y con puerta

**P1 — Un contorno que sea una melodia.** Sustituir el argmax por cuadro por un
seguidor con memoria: `librosa.pyin` sobre la pista melodica separada, o
`librosa.sequence.viterbi` sobre el CQT con castigo al salto de octava. Y
**quitar el suelo de G3**: el problema que lo puso (seguir al bajo) se resuelve
con continuidad, no prohibiendo el registro de la guitarra.
*Puerta:* saltos de mas de una quinta **por debajo del 8 %** y de octava **por
debajo del 2 %** en las 4 de control (hoy 28-51 % y 11-40 %); y que en las 12
humanas con guitarra aislada la ventaja del chart humano suba de **+4,7 % a
+15 %** — si el contorno es la melodia, el humano tiene que reconocerse en el.

**P2 — Que el traste siga a ese contorno sin que nadie lo reescriba.** Hoy hay
cinco capas que pueden pisar lo que dijo la melodia: el banco de motivos cuando
el tono lleva 3 notas quieto, el limite de salto por velocidad, la racha de
gesto, la regla anti-repeticion y la reutilizacion de compases.
*Puerta:* contar cuantas notas de cada chart decide la melodia y cuantas una de
esas cinco reglas. Hoy no se sabe. Objetivo: **la melodia decide 2 de cada 3**.

**P3 — La prueba es jugarlo, no la tabla.** Las canciones de control tienen que
ser de las que el propio Bruno dice: una que sea solo guitarra y una que sea
solo voz, donde no haya duda de que instrumento se esta tocando.

**Y la queja que sigue viva y sin arreglar:** la letra. `banco_alineado.py`
mide hoy **117 ms** de error mediano contra el objetivo de 60, con las lineas
largas en 178 ms. Por eso *"la letra va mas atras que la voz"*. No es la misma
causa que lo del chart, pero es la otra mitad de lo que se nota jugando.

## 6. Hace falta instalar algo?

Para P1 no: `pyin` y `viterbi` vienen dentro de librosa, que ya esta. Demucs ya
esta instalado de la tanda anterior.

Si despues de P1 el contorno sigue sin ser una melodia en canciones con mucha
capa, el paso siguiente seria transcripcion polifonica de verdad
(`basic-pitch`, de Spotify: da notas con tono y duracion, ~50 MB). Eso si es una
instalacion, y no se pide hasta que P1 diga que hace falta.

---

## 7. Lo hecho el mismo dia: P1, a medias y medido

El contorno nuevo (`audio.contorno_de_tono`) ya esta puesto: suma armonica,
peso grave suave en vez del suelo de G3, y Viterbi con el prior de intervalos
sacado de `datos/perfil_voz.json`.

| | antes | ahora | puerta |
|---|---|---|---|
| saltos de octava (nuestras 4) | 20,2 % | **6,3 %** | < 2 % |
| saltos de octava (Thunderstruck aislado) | 39,7 % | **4,6 %** | < 2 % |
| ventaja del chart **humano** | +4,7 % | **+13,2 %** | >= +15 % |
| "todas iguales" | 6,5 veces | **5,4 veces** | < 3 |

Ninguna puerta se cruza del todo y las cuatro medidas se mueven en la buena
direccion. El "todas iguales" es el mejor numero que ha tenido el proyecto, y
esta vez la mediana acompana a la media: la mejora es uniforme.

**El defecto nuevo, que es la tarea siguiente:** el contorno se aplana. Se queda
quieto el 43,8 % de las veces contra el 35,1 % humano, y `assign_lanes` tira del
banco de motivos en cuanto lleva tres notas quietas (`flat_run >= 3`). O sea que
un contorno plano le devuelve el mando al banco — que es la causa medida del
"todas las canciones se sienten iguales".

**Descartado con numero en la misma tanda:** restar el armonico de la nota grave
(`SUPRESION_OCTAVA`) empeora las dos cosas. Barrido de 6 combinaciones en
`DECISIONES_MEDIDAS.md`.
