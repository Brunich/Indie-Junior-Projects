# AutoChart - charts de Clone Hero sacados del audio

> **Si eres una IA y acabas de abrir esto:** no leas el README entero. Lee
> [`CLAUDE.md`](CLAUDE.md) (las reglas) y
> [`docs/SIGUIENTE_CHAT.md`](docs/SIGUIENTE_CHAT.md) (estado y tarea siguiente).
> Son ~24 KB y con eso se empieza a producir.

Escucha una cancion y saca un `notes.chart` de 5 trastes jugable: pulso,
ataques, contorno del riff, acordes, sostenidos, Star Power y las cuatro
dificultades. Y le pone **letra de karaoke** que se colorea silaba a silaba.

Lo que decide si algo esta bien no es el gusto de nadie: son los **charts
hechos a mano** que ya hay en el disco. Se miden y el generador apunta ahi.

## Empezar

```bash
pip install -r requirements.txt
python -m autochart
```

`python -m autochart` a secas **dice que se puede hacer**, agrupado por lo que
quieras conseguir. Y `python -m autochart estado` dice que hay hoy en tu
maquina y que conviene hacer despues. Con esos dos no hace falta leer nada mas.

Python 3.10 y `ffmpeg` en el PATH (solo para los `.mp3`).

## Las cuatro cosas que se pueden hacer

**Una cancion nueva jugable:**

```bash
python -m autochart generar "<carpeta de Clone Hero o un mp3>"
python -m autochart en-juego salida
```

Sale una carpeta en `salida/` lista para copiar a `Songs/`. Con `--densidad 1.2`
o `--percentil p75` sale mas cargada. **La cancion original no se toca.**

**Letra de karaoke:**

```bash
python -m autochart censo              # que tiene letra, que falta, que es instrumental
python -m autochart letra --pack 10    # se la pone a un pack entero
python -m autochart revisar-letra      # cual salio torcida
python -m autochart instalar --probar  # que copiaria; sin --probar, la copia
```

La letra sincronizada se baja de LRCLIB y **se verifica contra tu audio** antes
de escribirla: se mide la energia de voz y se corrige el desfase. Las versiones
que no cuadran se rechazan, porque una letra corrida es peor que no tener letra.
`instalar` guarda el original y tiene `--deshacer`.

**Saber como son los charts buenos:**

```bash
python -m autochart minar    # densidad, acordes, sostenidos -> perfil
python -m autochart atlas    # QUE se toca: 16 gestos por genero e instrumento
python -m autochart voz      # como escribe la letra un humano
```

**Comprobar antes de dar algo por bueno:**

```bash
python tests/test_basico.py            # 22 pruebas, sin audio ni biblioteca
python -m autochart comparar           # nuestro chart contra el humano
python -m autochart banco --muestra 24 # el control (~7 min)
```

## Que hay medido hoy (21-08-2026)

| | |
|---|---|
| canciones en la biblioteca | 407, en 16 packs |
| charts humanos minados | 882 (hay que volver a minar: la biblioteca cambio) |
| pistas en el atlas de patrones | 607, de 396 canciones, 562 162 notas |
| canciones con voz humana medida | 128, 49 459 silabas |
| canciones con letra ahora | 184 de 407 |
| control del banco | F1 0.660 sobre 24 canciones, 0 errores |

## Como funciona

```
audio ─┬─ mezcla  ──► pulso, mapa de tempo que se reengancha
       └─ guitarra ─► ataques, contorno de tono (CQT), secciones
                        │
                        ▼
              cuantizar a la rejilla  (lo que no cae en rejilla, fuera)
                        │
                        ▼
              densidad por ventana    (objetivo = mediana del corpus)
                        │
                        ▼
              trastes por contorno    (sube el riff → sube la mano)
              motivos del corpus      (cuando el audio no da tono)
              reutilizar compases     (si la cancion repite, el patron repite)
                        │
                        ▼
              acordes, sostenidos, Star Power, 4 dificultades
                        │
                        ▼
              notes.chart + song.ini
```

**El contorno sigue a la guitarra solista, no al bajo.** El tono se busca solo
en el registro de la solista (MIDI 55-96, de G3 para arriba) y el filtro de
densidad prefiere los ataques donde esa banda esta sonando. Cogiendo sin mas el
bin mas fuerte del espectro, el 61 % de los tonos caia en la zona del bajo y del
chug grave: el chart seguia el acompanamiento y se notaba al jugarlo.

**Y lo que se mapea es el intervalo, no el tono.** El corpus no dice donde pone
la mano un humano, dice cuanto la mueve entre nota y nota (se queda 31 %, ±1
47 %, ±2 14 %, ±3 6 %). Mapear el tono absoluto a un carril es un mapeo sin
memoria y sacaba un 25.8 % de saltos de ±2; mapeando el intervalo baja al
18.9 %, y el error total contra la distribucion humana pasa de 23.9 a 14.8
puntos (de 30.2 a 10.2 en *Keelhauled*).

Tres detalles que son el 90 % de que esto suene sincronizado y se sienta bien:

- **El pulso se busca en la mezcla, las notas en la guitarra.** Los detectores de
  pulso viven de la bateria; sobre un stem de guitarra aislado se equivocan de
  compas entero y desplazan el chart completo.
- **El mapa de tempo se reengancha.** En vez de un BPM constante, se emite un
  evento de tempo cada vez que el chart se ha desviado mas de 6 ms del audio, y
  el nuevo tempo se calcula para *cancelar* esa desviacion, no solo para igualar
  el pulso local.

## Lo que esta medido

Corpus (`python -m autochart minar`, 882 charts, Experto):

| | p5 | p50 | p95 |
|---|---|---|---|
| Densidad (notas/s) | 2.01 | **3.75** | 5.95 |
| Acordes | 0.03 | **0.35** | 0.77 |
| Sostenidos | 0.03 | **0.15** | 0.97 |
| Notas repetidas seguidas | 0.06 | **0.27** | 0.68 |

Saltos de traste entre notas seguidas: quieto 31 %, ±1 47 %, ±2 14 %, ±3 6 %.
Acordes: 68 % notas sueltas, 27 % de dos, 5 % de tres.

Sincronia (`tools/verificar_sincronia.py`, *Arctic Monkeys — Teddy Picker*):

- deriva del mapa de tempo: **1.19 ms de media**, 5.99 ms el peor pulso de 408
- distancia de cada nota al ataque real mas cercano: **14.9 ms de media**
- notas a menos de 50 ms de un ataque real: **100 %**

Parecido con el chart humano (`tools/comparar_humano.py`, misma cancion):

- recall **83.5 %** · precision **63.6 %** · **F1 0.72**

Banco de 16 canciones que ya tenian chart humano (`python tools/banco.py --muestra 16`):

- **F1 medio 0.65**, mediana 0.65
- densidad generada **3.5 notas/s** frente a **4.2** del humano
- **0 charts con errores** de validacion

El suavizado de la rejilla cuesta un poco de F1 y se paga a gusto, porque lo que
compra es que la autopista no se vea acelerar y frenar (mismas 16 canciones):

| Suavizado | F1 medio | Eventos de tempo* | Desviacion del BPM* |
|---|---|---|---|
| ninguno | 0.660 | 254 | 6.9 % |
| **ventana 3 (actual)** | **0.648** | **161** | **4.6 %** |
| ventana 5 | 0.642 | 154 | 3.1 % |

<sub>* medido en *Keelhauled*</sub>

Pruebas: `python tests/test_basico.py` → 11 OK, sin audio ni biblioteca.

### Lo que el F1 no mide, y donde enganya

**No ve los trastes.** El F1 compara *cuando* suena cada nota, no *que traste* le
toca. Se comprobo subiendo las repeticiones de traste del 12.5 % al 24.5 %: el
F1 se quedo clavado en 0.648, con el mismo recall y la misma precision. Para
juzgar el patron estan `tools/ver_patron.py` y las distribuciones del corpus.

**Y premia pasarse de notas.** Sobre una muestra distinta de 24 canciones, donde
el humano esta en 3.77 notas/s:

| Objetivo de densidad | F1 | Recall | Precision | Densidad generada |
|---|---|---|---|---|
| **p50 (por defecto)** | 0.666 | 0.702 | 0.652 | **3.64** (−3 % del humano) |
| p75 | 0.685 | 0.776 | 0.628 | 4.22 (+12 %) |
| p95 | 0.692 | 0.859 | 0.592 | 5.10 (+35 %) |

El F1 sube monotonamente mientras la densidad se va un 35 % por encima de la
humana. La razon es que cada nota de mas cae sobre un ataque real del audio, asi
que pilla mas notas humanas y apenas pierde precision. Llevado al limite, la
forma de maximizar este numero es llenar la autopista.

Por eso **la densidad no la decide el F1**: la decide el parecido con la
distribucion humana, y ahi gana p50. `--percentil p75` esta ahi para quien quiera
el chart mas cargado a proposito.

## Estructura

```
autochart/
  chartio.py    leer y escribir .chart
  midiio.py     leer notes.mid (solo para minar)
  corpus.py     medir los charts humanos -> perfil
  audio.py      pulso, ataques, tono, secciones
  timing.py     mapa de tempo con reenganche
  generate.py   cuantizar, densidad, trastes, acordes, sostenidos, SP
  validate.py   errores (rompe) y avisos (raro)
  export.py     carpeta lista para Clone Hero
  cli.py        minar / generar / revisar
tools/
  banco.py               genera N canciones y las puntua contra el humano
  comparar_humano.py     una cancion contra su chart humano
  medir_hopo.py          que se toca ligado, y para que marca un humano
  verificar_sincronia.py deriva del tempo y distancia a los ataques
docs/
  PLAN.md            el plan por fases y lo que falta
  FORMATO_CHART.md   el formato .chart medido en la biblioteca real
```

## Estado

F0 (cimientos), F1 (sincronia) y F2 (que siga el riff) hechos. F3 (que se sienta
escrito) en curso: ya se escriben las **ligaduras** con la bandera `5` — se
rasguea la nota que abre la frase y se liga la corchea cuando la mano apenas se
mueve, con las tasas medidas en 254 charts humanos. Quedan los acordes con
criterio armonico y afinar cuanto salta la mano. El detalle esta en
[docs/PLAN.md](docs/PLAN.md).

## Aviso

Repo privado. El `.gitignore` bloquea todo el audio: aqui no se sube ni una
cancion, solo codigo y estadisticas agregadas.
