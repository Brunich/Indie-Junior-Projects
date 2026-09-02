# Arquitectura: como se corta este proyecto en sistemas

Este documento **no** manda cambiar nada hoy. Dice como esta cortado ahora, por
que aguanta, y cual es la linea por la que hay que cortarlo cuando deje de
aguantar — para que ese dia no se decida con prisa.

---

## 1. De donde viene la pregunta

AutoChart nacio haciendo **una** cosa: audio de guitarra -> `notes.chart` de 5
trastes. Para eso, nueve modulos planos en un paquete valen de sobra, y de hecho
valen: 5 571 lineas, 11 pruebas, un banco de 24 canciones que dice si algo se
rompio.

Lo que cambia la pregunta es que el proyecto acaba de abrir **tres frentes a la
vez**:

| Frente | Que anade |
|---|---|
| **Voz / karaoke** | otra pista, otro formato de evento, otro corpus, otra fuente de datos (la letra, que no esta en el audio) |
| **Otros instrumentos** | bajo, ritmica y teclado se chartean con reglas distintas de la solista |
| **Atlas de patrones** | un segundo criterio medido, que no es una media sino un vocabulario |

Los tres tiran del mismo sitio: `generate.py`, que hoy tiene **949 lineas** y es
el 17 % del codigo. Si el bajo, la voz y el vocabulario entran ahi, ese fichero
se convierte en el proyecto entero y deja de poder tocarse sin miedo.

La regla que aplica aqui es la misma del resto del repo: **no se refactoriza por
elegancia, se refactoriza cuando hay un numero que lo pide.** El numero es el
tamano de `generate.py` y la cantidad de razones distintas por las que hay que
abrirlo.

---

## 2. Los cinco sistemas

La linea de corte no es "por tipo de fichero", es **por que clase de verdad
maneja cada parte**. Cada sistema responde a una pregunta distinta y falla de una
manera distinta:

```
   ┌─────────────────────────────────────────────────────────────┐
   │ 1. FORMATOS      "que dice el fichero"                      │
   │    chartio · midiio · songini                               │
   │    Sin opinion musical. Un fallo aqui es un fallo de lectura.│
   └─────────────────────────────────────────────────────────────┘
                              │
   ┌─────────────────────────────────────────────────────────────┐
   │ 2. ESCUCHA       "que suena, y cuando"                      │
   │    audio · timing · (separacion)                            │
   │    De un mp3 a hechos con marca de tiempo.                  │
   │    Un fallo aqui desplaza el chart entero.                  │
   └─────────────────────────────────────────────────────────────┘
                              │
   ┌─────────────────────────────────────────────────────────────┐
   │ 3. CRITERIO      "que hace un humano"                       │
   │    corpus (cuanto) · atlas (que) · voz (como se canta)      │
   │    SOLO LECTURA sobre la biblioteca. Produce perfiles JSON. │
   │    Un fallo aqui no rompe nada: te hace apuntar a otro sitio│
   └─────────────────────────────────────────────────────────────┘
                              │
   ┌─────────────────────────────────────────────────────────────┐
   │ 4. GENERADORES   "que escribo yo"                           │
   │    guitarra · bajo · ritmica · karaoke · dificultades       │
   │    Uno por instrumento, TODOS con la misma interfaz.        │
   │    Un fallo aqui sale en el banco.                          │
   └─────────────────────────────────────────────────────────────┘
                              │
   ┌─────────────────────────────────────────────────────────────┐
   │ 5. SALIDA        "que entrego"                              │
   │    export · validate · revisar_in_game                      │
   │    Las puertas. Un fallo aqui llega al juego.               │
   └─────────────────────────────────────────────────────────────┘
```

El orden importa: **cada sistema solo puede depender de los de arriba.** El
criterio no sabe generar; el generador no sabe leer ficheros; la escucha no sabe
que es un traste. Hoy eso ya se cumple casi entero, que es por lo que no urge
mover nada.

---

## 3. El contrato que hace que esto funcione

Cortar en carpetas no sirve de nada si los trozos siguen hablando de cualquier
manera. Lo que hace que un corte aguante son **dos tipos de datos** en el medio:

### `Cancion` — lo que salio de escuchar

Todo lo que la etapa 2 sabe, sin una sola decision de charteo:

```python
@dataclass
class Cancion:
    duracion: float
    tempos: list[tuple[int, float]]     # mapa, no un BPM
    compases: list[TimeSignature]
    secciones: list[tuple[float, str]]  # intro / verso / estribillo / solo
    ataques: list[Ataque]               # tiempo, tono, ring, lead
    voz: PistaVoz | None                # si hay letra, ya alineada
```

### `Generador` — lo que hace falta para ser un instrumento

```python
class Generador(Protocol):
    nombre: str                         # "guitarra" | "bajo" | "karaoke"
    def generar(self, cancion: Cancion, criterio: Criterio,
                ajustes: Ajustes) -> Pista: ...
```

Con eso, **anadir el bajo no toca el generador de guitarra**: es una clase nueva
que lee el mismo `Cancion` y el mismo atlas, apuntando a la fila `bajo` en vez
de a la fila `guitarra`. Y anadir el karaoke tampoco: es un generador mas, que
casualmente escribe eventos en vez de notas.

Esa es la prueba de si el corte esta bien hecho: **si anadir un instrumento
obliga a abrir el generador de otro, el corte esta mal.**

---

## 4. Como se llega ahi sin romper nada

No hay mudanza grande. Hay tres reglas:

1. **Lo nuevo nace ya colocado.** `voz.py`, `silabas.py` y `atlas.py` se
   escribieron como sistemas independientes desde el primer dia: no importan
   nada de `generate.py` y `generate.py` no los importa. Eso ya es la
   arquitectura nueva, sin haber movido un fichero.

2. **Lo viejo se mueve cuando haya que abrirlo igual.** El dia que toque partir
   `generate.py` para meter el bajo, ese es el dia de sacar de ahi la parte
   comun (cuantizado, densidad, dificultades) a `nucleo/`. Ni antes ni despues.

3. **El banco es la red.** Cualquier movimiento de codigo se valida con
   `tools/banco.py --muestra 24`: si `f1_medio` sigue en 0.668 y `nps_humano_medio`
   sigue en 3.77, la mudanza no cambio el comportamiento. **Mover codigo que no
   tiene un control medido es lo unico que no se debe hacer.**

Orden previsto, cada paso con su control:

| Paso | Cuando | Control |
|---|---|---|
| Sacar `Cancion` como tipo explicito | al meter el 2.º instrumento | banco 0.668 |
| `nucleo/` (cuantizado, densidad, dificultades) | al partir `generate.py` | banco 0.668 |
| `generadores/guitarra.py` + `generadores/bajo.py` | idem | banco por instrumento |
| `criterio/` (corpus + atlas + voz juntos) | cuando el atlas alimente al generador | los perfiles no cambian |
| `formatos/` | ultimo, es puro orden | 11 pruebas |

---

## 5. Lo que NO se va a hacer

- **Plugins de verdad** (cargar generadores de fuera). No hay ningun caso de uso:
  los instrumentos son cinco y se conocen todos.
- **Base de datos.** Los perfiles son JSON de pocos cientos de KB y se leen
  enteros. Una base de datos es una dependencia a cambio de nada.
- **Una capa de abstraccion sobre `librosa`.** Solo hay un backend de audio y no
  se ve un segundo.
- **Separar en paquetes instalables.** Es un proyecto de una persona en una
  maquina.

Cada una de estas es una tentacion razonable, y por eso esta escrita: para que
la proxima vez que parezca buena idea, se lea que ya se penso y por que no.

---

## 6. Donde vive cada cosa hoy

| Sistema | Ficheros de hoy | Estado |
|---|---|---|
| Formatos | `chartio.py` `midiio.py` (+ `export.read_song_ini`) | limpio |
| Escucha | `audio.py` `timing.py` | limpio |
| Criterio | `corpus.py` **`atlas.py`** **`voz.py`** | los tres, solo lectura |
| Generadores | `generate.py` (949 lineas, solo guitarra) **`silabas.py`** | el que pide el corte |
| Salida | `export.py` `validate.py` `tools/revisar_in_game.py` | limpio |

En **negrita**, lo que nacio ya en su sitio.
