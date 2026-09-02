# El formato `.chart`, medido en la biblioteca real

Notas tomadas leyendo los charts de `C:\Users\bruni\OneDrive\Documents\Clone Hero\Songs`
(882 charts humanos analizados). Esto no es la especificacion oficial: es lo que
de verdad aparece en los archivos que Clone Hero carga en esta maquina.

## Estructura

Un `.chart` es texto plano: secciones con nombre, cada una entre llaves, y
dentro lineas `tick = evento`.

```
[Song]
{
  Name = "Keelhauled"
  Resolution = 192
  MusicStream = "song.ogg"
}
[SyncTrack]
{
  0 = TS 4
  0 = B 118400
}
[Events]
{
  768 = E "section Intro A"
}
[ExpertSingle]
{
  768 = N 2 0
  768 = N 6 0
  768 = E solo
}
```

## `[Song]`

| Clave | Que hace |
|---|---|
| `Resolution` | Ticks por negra. **192** en la practica totalidad de la biblioteca. |
| `Offset` | Retraso del audio en segundos. Se deja en 0 y el ajuste va en `song.ini`. |
| `MusicStream` | Nombre del archivo de audio principal dentro de la carpeta. |

Los valores de texto van entre comillas; `Offset`, `Resolution`, `Difficulty`,
`PreviewStart` y `PreviewEnd` van sin ellas.

## `[SyncTrack]`

- `tick = B <bpm x 1000>` — cambio de tempo. `B 118400` son 118.4 BPM.
- `tick = TS <numerador> [<log2 del denominador>]` — compas. `TS 4` es 4/4;
  el denominador se omite cuando es 4.

El tick 0 es siempre el segundo 0 de la cancion. Esto importa mas de lo que
parece: si la primera pulsacion detectada esta en el segundo 0.41, no se puede
poner en el tick 0 sin desplazar el chart entero. AutoChart resuelve esto con un
**pulso de entrada**: el pulso `i` vive en el tick `(i+1) x 192` y el primer
evento de tempo se estira para cubrir ese hueco inicial.

## `[Events]`

`tick = E "section <nombre>"` marca las secciones que se ven en la barra de
progreso del juego. Cualquier otro texto se ignora.

## Pistas de notas

El nombre es `<Dificultad><Instrumento>`: `ExpertSingle`, `HardSingle`,
`MediumSingle`, `EasySingle` para la guitarra principal.

`tick = N <valor> <sostenido en ticks>`:

| Valor | Significado |
|---|---|
| 0–4 | verde, rojo, amarillo, azul, naranja |
| 5 | *forced* — invierte el estado natural HOPO/rasgueo |
| 6 | *tap* |
| 7 | nota abierta |

Un acorde son varias lineas `N` con el mismo tick. Las banderas 5 y 6 tambien se
escriben como lineas `N` en el mismo tick que la nota que modifican, lo que hace
facil contarlas como notas por error: el analizador de este proyecto las filtra
en cuanto lee la pista.

`tick = S 2 <duracion>` es una frase de Star Power. `tick = E solo` y
`E soloend` delimitan los solos.

### HOPO natural

Clone Hero convierte en HOPO cualquier nota que caiga a menos de 65/192 de negra
de la anterior (una semicorchea a resolucion 192 son 48 ticks: HOPO; una
corchea, 96 ticks: rasgueo). AutoChart se apoya en ese comportamiento y **no**
escribe banderas `5`/`6` todavia, porque una bandera mal puesta se nota mucho
mas que su ausencia.

## `song.ini`

Lo lee el juego para el menu; el chart lo lee para las notas. Los campos que
importan:

```ini
[Song]
name = ...
artist = ...
charter = ...
song_length = 226074      ; milisegundos
diff_guitar = 3           ; 0-6, -1 = no hay pista
preview_start_time = 0
delay = 0                 ; ms de retraso del audio
```

## Nombres de pistas de audio reconocidos

`song`, `guitar`, `bass`, `rhythm`, `vocals`, `keys`, `drums`, `drums_1`..`drums_4`,
`crowd`, `preview`. Cualquier otro `.ogg` en la carpeta el juego lo ignora.
Cuando existe `guitar.ogg` conviene analizarlo a el y no la mezcla: los ataques
de la guitarra salen mucho mas limpios.

## `notes.mid`

La mayoria de la biblioteca (757 de 1011 charts) usa MIDI en lugar de `.chart`.
Solo hace falta leerlo, para minar estadisticas. Distribucion de alturas en la
pista `PART GUITAR`:

| Dificultad | Notas MIDI |
|---|---|
| Easy | 60–64 |
| Medium | 72–76 |
| Hard | 84–88 |
| Expert | 96–100 |

`103` marca solo, `116` marca Star Power. Los charts convertidos desde MIDI
suelen llevar un desfase de autoria de unas decenas de milisegundos contra el
audio (medido: **+65 ms** en *Teddy Picker*), asi que cualquier comparacion
contra un chart humano tiene que estimar y descontar ese desfase antes de
puntuar nada.
