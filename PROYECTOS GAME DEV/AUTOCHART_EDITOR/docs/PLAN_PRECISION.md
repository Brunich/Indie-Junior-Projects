# Plan: dejar de ajustar umbrales y medir de verdad

**Lo que dijo Bruno el 22-08-2026, y tiene razon:**

> *"Las canciones estan muy mal, necesitan mucha mejora, ni cerca de un buen
> nivel. Las silabas tienen que ser aun mas precisas en cada instante, mejores
> patrones, mejores transiciones entre patrones, analizar cuales se usan mas en
> canciones de distintos generos. **Y ser asi de preciso y especifico con los
> sistemas, y no nada mas usar ciertos numeros de porcentajes de entre segundos
> y asi.**"*

Esa ultima frase es el diagnostico correcto de lo que llevo hecho. El generador
esta lleno de constantes ajustadas a ojo -- `SILABA_TOLERANCIA_S = 0.06`,
`INSTRUMENTO_MINIMO_POR_S = 2.2`, `VOZ_HUECO_DE_FRASE_S = 1.2`,
`HUECO_MUDO_MAXIMO_S = 1.6` -- y cada una se puso porque *parecia razonable*, no
porque una medida la exigiera. Eso tiene un techo, y lo hemos tocado.

Este plan cambia el metodo: **cada decision sale de una medida sobre el audio o
sobre el corpus, no de un numero elegido.**

---

## 1. Por que la letra a veces cuadra y a veces no

Bruno: *"hay momentos que si le va muy bien con la cancion y hay otros que no,
no entiendo por que"*. **Ya se por que, y es medible.**

Un `.lrc` trae **una sola marca por linea**. Las silabas dentro de esa linea las
reparto yo por peso de letras. Medido contra 41 canciones con voz humana --
14 650 silabas con su tiempo real al lado:

| | error de mi reparto |
|---|---|
| mediana | **148 ms** |
| p75 | 284 ms |
| p95 | **597 ms** |

Y depende del largo de la linea, que es exactamente lo que el nota:

| silabas en la linea | error mediano | p95 |
|---|---|---|
| 3-5 | 114 ms | 554 ms |
| 6-8 | 123 ms | 499 ms |
| 9-11 | 174 ms | 603 ms |
| 12-14 | 162 ms | 654 ms |
| 15-17 | **186 ms** | **706 ms** |

**Las lineas cortas cuadran y las largas se van medio segundo.** Cantar no es
uniforme: hay notas largas, pausas y palabras atropelladas, y mi reparto por
peso de letras no puede saberlo.

### El arreglo, que no es un umbral

**Medir donde esta cada silaba en el audio.** Dentro de la ventana de cada
linea, detectar los arranques de canto en la banda de voz y emparejarlos con las
silabas por orden. Es un alineamiento, no un reparto:

1. Aislar la banda de voz (200-4000 Hz) del tramo de esa linea.
2. Sacar la envolvente y sus arranques -- un arranque de silaba deja una subida
   clara aunque la nota anterior siga sonando.
3. Emparejar los N arranques con las M silabas con programacion dinamica
   (el mismo problema que alinear dos secuencias), permitiendo que una silaba
   larga se coma varios arranques y que una silaba sin arranque caiga entre dos.
4. Si no hay arranques suficientes, se cae al reparto de hoy -- pero se **marca
   la linea como estimada**, para que `revisar-letra` lo diga.

**Como se comprueba:** el mismo experimento de arriba. Se cogen las 41 canciones
con voz humana, se tiran sus tiempos, se realinean con esto, y el error mediano
tiene que bajar de **148 ms a menos de 60 ms** -- que es el umbral con el que
medimos si una nota coincide con una silaba. Si no baja de ahi, no sirve.

---

## 2. Por que los patrones no se sienten

Hoy los trastes salen de: el contorno de tono (`_contour_to_lanes`) con tres
cortes calibrados con **dos** canciones, un banco de trigramas del corpus, y
reglas de acorde. No hay **vocabulario** ni **transiciones**: el chart pasa de
una figura a otra sin que nada diga si esa transicion existe en la musica real.

El atlas ya tiene la mitad del trabajo hecho -- 16 gestos medidos sobre 607
pistas -- pero **solo se usa para medir, no para generar**. Eso es lo que hay
que cerrar.

### 2a. El vocabulario, con transiciones

Del corpus, por genero e instrumento, sacar no solo cuantas veces sale cada
gesto sino **que gesto sigue a cual**. Una matriz de transicion:

```
        despues de...   tremolo  escalera  acorde  rafaga  ...
   tremolo                 0.31     0.12     0.22    0.05
   escalera_sube           0.08     0.34     0.15    0.11
   ...
```

Eso ya se puede medir con `detectar_licks`: basta con guardar el ORDEN en que
aparecen, cosa que hoy se tira. **Es una tarde de trabajo y es la pieza que
falta.**

### 2b. Generar por gestos, no por notas sueltas

Hoy se elige nota a nota. Lo que hace un charter es elegir **un gesto para este
compas** y escribirlo entero. El cambio:

1. Trocear la cancion en compases.
2. Para cada compas, mirar que pide el audio (densidad, contorno, si hay voz).
3. Elegir un gesto **de la familia del genero** que encaje, y con una
   transicion legal desde el gesto anterior.
4. Escribirlo respetando los ataques reales -- el gesto dice la FORMA, el audio
   dice DONDE.

**Como se comprueba:** la cobertura de gestos, que hoy esta en 0.27-0.33 contra
0.46 humano, y la matriz de transiciones del chart generado contra la del
humano del mismo genero.

### 2c. Que las constantes salgan del corpus

Repasar las que hay y sustituir cada una por una medida:

| Hoy | De donde deberia salir |
|---|---|
| `SILABA_TOLERANCIA_S = 0.06` | la ventana de acierto del propio juego |
| `VOZ_HUECO_DE_FRASE_S = 1.2` | el p75 de hueco entre frases humanas (0.73 s) |
| `HUECO_MUDO_MAXIMO_S = 1.6` | el p95 de `respiro` en el corpus |
| `INSTRUMENTO_MINIMO_POR_S = 2.2` | la densidad p25 del instrumento en el atlas |
| `FRASE_MAXIMA_S = 7.0` | el p95 de `segundos_por_frase` (5.82 s) |

---

## 3. El nivel al que hay que apuntar

De `scorestats.json`, la partida real de Bruno del 22-08-2026:

| | |
|---|---|
| cancion | Eric Johnson - Cliffs of Dover (chart de Buldy) |
| dificultad | **Experto**, mando de guitarra |
| notas acertadas | **908 de 1244 = 73 %** |
| racha maxima | 36 |
| estrellas | 2 de 5 |
| notas de mas | 161 |

**Ese es el listón real, y cambia el objetivo.** Un chart que el pueda tocar al
73 % es un chart exigente pero justo. No hay que hacerlo mas facil: hay que
hacerlo mas *coherente*, que es otra cosa. Con 36 de racha maxima, lo que le
rompe la partida son los cambios que no se ven venir -- justo lo que arreglan
las transiciones de 2a.

Y que juegue en Experto con guitarra **contradice lo que estaba escrito** en el
proyecto (que el mando estaba mudo por el protocolo de PS3). Ya no lo esta.

---

## 4. En que orden

| | Que | Por que ahi | Se mide con |
|---|---|---|---|
| **1** | Alinear cada silaba con el audio | Sin esto, anclar las notas a la voz propaga el error de 148 ms a las notas | error mediano < 60 ms sobre las 41 canciones humanas |
| **2** | Matriz de transiciones del corpus | Es medir, no generar: barato y no puede romper nada | que exista y tenga sentido por genero |
| **3** | Generar por gestos | Es el cambio grande. Necesita 1 y 2 hechos | cobertura 0.30 -> 0.46, transiciones parecidas al humano |
| **4** | Constantes sustituidas por medidas | Limpieza, cuando lo de arriba este | el banco no se mueve |

**Nada de esto se toca en Facil/Medio/Dificil hasta que Experto este bien**, que
es lo que pidio Bruno.

---

## 5. Lo que NO voy a volver a hacer

Escrito para mi mismo, porque es el error de los ultimos dias:

- **Ajustar un umbral y medir una sola cancion.** Se hizo tres veces seguidas
  con el reparto voz/instrumento y las tres salieron peor.
- **Dar por bueno un cambio porque la metrica sube.** Las silabas-con-nota
  subieron a 0.83 y el chart se volvio karaoke con botones.
- **Poner un numero "razonable" sin una medida detras.** Es lo que Bruno señalo
  y es lo que hay que dejar de hacer.
