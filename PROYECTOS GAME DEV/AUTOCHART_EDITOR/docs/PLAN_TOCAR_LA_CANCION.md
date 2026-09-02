# Plan: que el chart toque LA CANCION, no la bateria

*22-08-2026. Este plan manda sobre `PLAN_MELODIA.md` y sobre el bloque §10 que
habia antes: los dos daban por buena la etapa que este documento demuestra que
esta rota.*

## 1. Lo que dijo Bruno, y en que se traduce cada cosa

> *"El nivel sigue siendo bastante bajo. La letra va mas atras que la verdadera
> voz, y en algunos momentos la letra no aparece. No se siente que se este
> tocando la cancion. **Siento que estoy tocando las mismas canciones que
> antes.** Ni siquiera las canciones que son de guitarra como INTRO se siente
> que se este tocando la guitarra. Ahorita no vale la pena."*

Cinco quejas, y ninguna es de gusto: las cinco se pueden medir. Antes de tocar
una linea se midieron las cuatro que se podian medir hoy.

## 2. Las medidas, hechas antes de cambiar nada

### a) La sincronia NO es el problema

`tools/verificar_sincronia.py`, sobre las canciones que el probo:

| | INTRO | DALI |
|---|---|---|
| deriva del mapa de tempo | 1.54 ms | 1.09 ms |
| notas a menos de 50 ms de un ataque real | **94.8 %** | **92.3 %** |

O sea que las notas **caen sobre ataques de verdad**. Lo que falla no es
*cuando*, es **cual**.

### b) El chart esta tocando la percusion

`tools/quien_toca.py` (nueva). Para cada nota escrita mira que sonaba en ese
instante exacto, separando energia percusiva de armonica:

| | notas mas percusivas que armonicas | lead elegidas | lead de todos los ataques |
|---|---|---|---|
| JUNIOR H - INTRO | 29 % | 0.548 | 0.473 |
| MARCOS YTZ - DALI | **58 %** | 0.711 | 0.651 |
| Brunich - Cyber Club | **63 %** | **0.668** | **0.692** |

La ultima fila es la que cierra el argumento: en una cancion **suya, de
guitarra**, el filtro de densidad elige ataques **menos melodicos que la media
de la propia cancion**. No es que se le escape la guitarra: es que prefiere el
golpe.

Y tiene una causa exacta, no misteriosa. `generate.thin` se queda con **lo mas
fuerte de cada ventana**, y en una mezcla lo mas fuerte es el bombo o la caja.
La solista solo tiene un premio pequeno (`LEAD_PRIORITY = 0.40`) contra el peso
1.0 de la fuerza bruta.

### c) Todos los charts son el mismo chart

`tools/parecidas.py` (nueva). Convierte cada pista en su mezcla de gestos y mide
la distancia entre todas las parejas:

| lote | charts | distancia media |
|---|---|---|
| generados (AI Rogue + Pruebas) | 15 | **0.077** |
| humanos (Memes + Latin) | 16 | **0.582** |

**Los generados se parecen entre si 7.5 veces mas que los humanos.** *"Siento
que estoy tocando las mismas canciones que antes"* no es una impresion: es esta
cifra. Y encaja con (b) — un chart escrito sobre la bateria se siente igual en
todas partes, porque las baterias se parecen entre si mucho mas que las
melodias.

### d) La letra no va tarde: va a la deriva

Medido comparando cada silaba escrita con el arranque de canto mas cercano
(sesgado a favor nuestro, o sea que la verdad es peor):

| | silabas | mediana | p25 | p75 | tarde >60 ms | pronto >60 ms | segundos con voz y sin letra |
|---|---|---|---|---|---|---|---|
| INTRO | 153 | +1 ms | −80 | +80 | 30 % | 29 % | 17 s |
| DALI | 531 | −10 ms | −160 | +136 | 37 % | 41 % | 2 s |
| Gil | 630 | +3 ms | −119 | +121 | 35 % | 36 % | 2 s |
| Loser | 217 | −13 ms | −109 | +134 | 35 % | 37 % | **29 s** |

No hay un desfase constante que restar: **hay un temblor de ±130 ms**, el doble
o el triple de la ventana de 60 ms con la que se decide si una nota coincide con
una silaba. Un tercio va tarde y otro tercio va pronto, y por eso a veces cuadra
y a veces no — que es exactamente lo que el describe. Los segundos con voz y sin
letra son la otra queja, y en *Loser* son medio minuto.

## 3. El diagnostico, en una frase

**El generador oye la cancion entera y escribe la percusion.** Todo lo demas
—los gestos, las rachas, el contraste, las dificultades— esta construido encima
de esa eleccion, y por eso ninguna mejora de patron se nota: se estan puliendo
los trastes de una linea de notas que no es la de la cancion.

## 4. Por que el proyecto no lo vio (y esto es lo importante)

Porque **la unica medida grande que tiene es ciega a esto**. Esta escrito en
`CLAUDE.md` §2 desde hace semanas:

> *El banco no ve los trastes. El F1 compara **cuando** suena cada nota, no
> **cual**.*

Y con ese banco se tomo la decision que mas ha costado. En
`DECISIONES_MEDIDAS.md`:

> *Separar la guitarra con Demucs — **Despriorizado**: forzando la mezcla el F1
> solo baja de 0.648 a 0.618.*

Ese numero es real y sigue siendo real. Lo que estaba mal era la conclusion:
**el F1 apenas baja porque la bateria y la guitarra suelen atacar en el mismo
sitio de la rejilla**, asi que quitar el stem casi no mueve *cuando* suenan las
notas. Justo la parte que el F1 no mira —*cual* de los dos sonidos se lleva la
nota— es la que decide si se siente que tocas la cancion.

**O sea: la separacion de pistas se descarto con una medida estructuralmente
incapaz de ver lo que la separacion arregla.** Es la trampa n.º 1 del propio
proyecto, aplicada a su decision mas cara.

## 5. La prueba barata, ya hecha

Antes de proponer instalar nada se probo lo que ya esta en casa: quitar la
percusion con **HPSS** (viene en librosa, cero instalacion), escribir eso como
`guitar.ogg` y dejar que el pipeline lo use sin tocar una linea de codigo.

| | antes | con HPSS |
|---|---|---|
| Brunich - Cyber Club, notas percusivas | 63 % | **31 %** |
| MARCOS YTZ - DALI, notas percusivas | 58 % | 55 % |

Y eso ya ensena el reparto del trabajo:

- **En lo electronico y lo de guitarra, HPSS se lleva la mitad del problema
  gratis.**
- **En DALI no hace nada**, y la razon es que ahi lo que compite no es una
  bateria: es **la voz contra la guitarra acustica**, y las dos son armonicas.
  Separarlas necesita separacion de fuentes de verdad.

(Aviso para no engañarse repitiendo la prueba: la carpeta de prueba no llevaba
`notes.chart`, asi que esa pasada de DALI fue **sin anclar a la letra**. La
comparacion de percusividad vale; la de patron, no.)

## 6. La reestructuracion, por fases

Cada fase cambia UNA cosa, tiene su numero objetivo y su control. El orden no es
negociable: las de abajo dependen de las de arriba.

### S1 — La cancion llega separada en pistas

Instalar `demucs` (torch 2.13 **ya esta instalado**, asi que es un `pip install`
pequeno, no una descarga de 2 GB) y guardar las cuatro pistas en
`salida/stems/<cancion>/` para no repetir el trabajo. Un `autochart separar`
que se salta las que ya estan.

- **Se mide con:** `tools/quien_toca.py`.
- **Objetivo:** notas mas percusivas que armonicas **por debajo del 20 %** en
  las tres canciones de control (hoy 29 / 58 / 63 %).
- **Control:** el banco no baja de f1 0.663. Se espera que **suba**.
- **Coste:** ~1-2 min por cancion en CPU, una sola vez.

### S2 — Quien manda en cada tramo se decide con las pistas, no adivinando

Hoy `repartir_frases` decide voz-o-instrumento con `lead`, que es una relacion
de bandas de la mezcla y por eso confunde una guitarra distorsionada con una
voz (ya medido: en Milo J/Trueno el rap da el mismo `lead` 0.695 que una
cancion de guitarra). Con las pistas separadas la pregunta es trivial: se
compara la energia de `other` contra la de `vocals` en cada ventana de 4 s.

- **Se mide con:** `tools/medir_melodia.py` (silabas-con-nota y notas-en-silaba
  por tramo, ya definido en `PLAN_MELODIA.md` §F2).
- **Objetivo:** silabas-con-nota 0.55-0.70 (humano 0.59) y notas-en-silaba ~0.30
  (humano 0.28), **y el contraejemplo obligatorio**: en *Tame Impala - Feels
  Like We Only Go Backwards* el humano NO sigue la voz (0.16); si ahi sale alto,
  S2 no esta decidiendo nada.

### S3 — Las notas salen de la pista que manda

Los ataques se detectan sobre `other` en los tramos de instrumento y sobre
`vocals` en los de voz, en vez de sobre la mezcla. El pulso **sigue saliendo de
la mezcla** (esto ya esta medido: sobre guitarra aislada el detector se equivoca
de compas entero).

- **Se mide con:** `quien_toca.py` + `verificar_sincronia.py`.
- **Objetivo:** percusivas < 20 % **sin** que las notas a menos de 50 ms de un
  ataque real bajen del 90 %.

### S4 — El traste sale de la pista que manda

Hoy el contorno de trastes sale del CQT de **la mezcla**: en un tramo cantado
eso es la voz mas todo lo demas, y en un tramo de guitarra es la guitarra mas el
bajo. Con la pista aislada, el contorno de cada cancion pasa a ser el suyo.

**Esta es la fase que arregla la queja del "todas iguales"**, porque es la que
hace que dos canciones distintas den contornos distintos.

- **Se mide con:** `tools/parecidas.py`.
- **Objetivo:** de **7.5 veces** mas parecidos que los humanos a **menos de 2.5**
  (distancia media del lote generado por encima de **0.25**; los humanos estan
  en 0.58).
- **Control:** la distribucion de movimiento de la mano sigue en su sitio
  (se queda ~31 %, ±1 47 %, ±2 14 %, ±3 6 %) y el banco no baja de 0.663.

### S5 — La letra deja de temblar

Con `vocals` aislado, `alinear.arranques_de_voz` deja de competir con la
bateria. Ya hay una medida de esto: 177 ms sobre la mezcla contra 117 ms sobre
el stem de voz.

- **Se mide con:** `tools/banco_alineado.py`.
- **Objetivo:** mediana **por debajo de 60 ms** (hoy 148 ms sobre 41 canciones),
  y el temblor p25-p75 dentro de ±60 ms (hoy ±130).
- **Y la segunda queja:** un aviso nuevo en `revisar_letra.py` cuando haya mas
  de 10 s seguidos con canto y sin una sola silaba (hoy: *Loser* 29 s,
  *INTRO* 17 s).

### S6 — La puerta de aceptacion

Nada de esto se da por bueno porque los numeros suban. **Se le pasan a Bruno las
tres canciones de control y las juega.** Lo que decide es lo que diga jugando;
los numeros solo sirven para no hacerle probar algo que ya se sabe que esta mal.

## 7. Lo que hay en IA Rogue, mirado

Lo pidio expresamente. Hay diez herramientas de audio en
`Friends\IA Rogue DEFINITIVE_latest_c7f4d7b\tools\`. **El codigo no sirve aqui**:
`analyze_music_library.py` mide cada pista entera con ffmpeg+numpy (bpm, energia,
rango dinamico en dB, golpes por segundo, reparto grave/medio/agudo) y AutoChart
ya hace todo eso por nota con librosa, que es bastante mas fino.

Lo que si vale es **una idea y un aviso**, y los dos se aplican a este plan:

1. **`mapa_de_estilo_musical.py` busca las casillas VACIAS**, no las llenas. Lo
   que descubrio alli fue que la biblioteca no era monotona de genero sino **de
   densidad**: *"ni una pista por debajo de 2,0 ataques/s"*. Es el mismo error
   que aqui — 15 charts con la misma mezcla de gestos — y es la razon por la que
   `parecidas.py` se queda en el repo como medida permanente.
2. Escrito en mayusculas en su propio codigo: **"LO QUE DICE BRUNO MANDA SOBRE
   LO QUE DICE EL MEDIDOR"**. Aqui el medidor decia que la sincronia estaba bien
   (94.8 %) y que el banco no bajaba, y Bruno decia que no vale la pena. Tenia
   razon el, y por eso hay dos medidas nuevas.

## 8. Lo que NO se va a hacer

- **No se tocan Facil, Medio y Dificil.** Peticion suya: congeladas hasta que de
  por bueno el Experto.
- **No se ajusta ni un umbral mas de los que ya hay.** El problema no es que
  `LEAD_PRIORITY` valga 0.40 en vez de 0.6; es que se esta puntuando la mezcla.
  Subirlo seria otra tarde perdida y ya hay tres asi escritas en
  `DECISIONES_MEDIDAS.md`.
- **No se re-instala nada en su biblioteca hasta S4**, porque hasta entonces el
  chart sigue siendo el mismo chart de siempre y volveria a decir lo mismo con
  razon.
