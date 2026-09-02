# Plan: letra y karaoke

**Que se quiere:** que cuando Bruno toque una cancion, la letra aparezca en su
momento y se vaya coloreando para poder cantarla. Buscando la letra ya sincronizada
en una fuente fiable cuando exista, y generandola cuando no.

**El hallazgo que cambia el planteamiento:** *la animacion no hay que
programarla*. Clone Hero ya colorea la letra solo. Lo que decide si se anima o
no es **como este partida en el fichero**, y eso se puede comprobar en tu
biblioteca:

| Cancion tuya | Como esta escrita | Que se ve al tocarla |
|---|---|---|
| `Ed Maverick - Fuentes de Ortiz` | un evento `lyric` **por silaba** | la linea se colorea al ritmo: karaoke |
| `Cardenales De Nuevo Leon - Belleza De Cantina` | la linea **entera** en un evento, con las palabras pegadas con espacios duros | la linea aparece y se ilumina de golpe |

O sea que el trabajo no es dibujar nada: es **partir bien y colocar bien**. Y
eso es texto, que ocupa entre 5 y 15 KB por cancion. **Espacio: cero problema.**

---

## 1. La escalera de fuentes (de la mejor a la ultima)

El sistema prueba en este orden y se queda con la primera que pase la
verificacion del §3. Cada peldano da menos precision que el anterior:

| # | Fuente | Que da | Precision |
|---|---|---|---|
| 0 | **La cancion ya la trae** | letra + tiempos + altura | perfecta |
| 1 | **LRCLIB** (`lrclib.net`) | letra sincronizada por LINEA (`.lrc`) | linea: ±100–300 ms |
| 2 | **`.lrc` local** junto al audio | igual que 1 | igual que 1 |
| 3 | **Texto plano** que le pases | letra sin tiempos | depende del alineado |
| 4 | **Transcripcion del audio** | letra aproximada + tiempos | la peor, y a veces mal la letra |

Notas sobre cada una:

- **Peldano 0 ya cubre 128 de tus canciones.** Antes de bajar a internet, se
  mira si la propia carpeta trae `PART VOCALS` o eventos `lyric`. Ya esta
  implementado (`autochart/voz.py:leer_voz`).
- **LRCLIB es la fuente elegida** porque es abierta, no pide clave, y su base
  es justamente letra **sincronizada** aportada por la comunidad — que es
  exactamente lo que pides: bajarla ya con su ritmo. Se busca por
  artista + titulo + duracion; la duracion es lo que evita traer la letra de
  otra version.
- **Peldano 4 es opcional y no se instala por defecto.** Transcribir audio pide
  un modelo de varios cientos de MB. Va detras de una bandera, y si no esta
  instalado el sistema lo dice y para, no adivina.

**Lo que NO se hace:** raspar paginas de letras que no ofrecen API. Ni por
educacion ni por que funcione: rompen cada dos meses. Y lo que se baje se queda
**en tu maquina**; los charts que compartas no llevan la letra pegada salvo que
tu lo decidas.

---

## 2. De linea a silaba: los tres niveles de karaoke

Una `.lrc` da **una marca por linea**. Eso ya sirve para "que aparezca en el
momento", pero no se anima por dentro. Los tres niveles, en orden de trabajo:

### Nivel A — la linea aparece a tiempo
Un `phrase_start` en la marca de la `.lrc`, la linea entera como un solo evento,
`phrase_end` antes de la siguiente. **Es lo que ya hace el chart de Cardenales.**
Barato, robusto, y suficiente para leerla.

### Nivel B — se colorea silaba a silaba  ← el objetivo
La linea se parte con `autochart/silabas.py` y cada silaba recibe su tick.
Como se reparten los ticks dentro de la ventana de la linea, en orden de
preferencia:

1. **Ataques de la voz.** Si hay stem de voz (o se separa), los ataques dentro
   de la ventana marcan donde cae cada silaba. Es lo mas fiel.
2. **La rejilla.** Sin ataques utiles, se reparten sobre la rejilla del mapa de
   tempo que ya calcula `timing.py`. Las silabas humanas caen en negra (25.5 %),
   corchea (19.1 %) y semicorchea (12.9 %): **repartir a ojo en tiempo lineal es
   justo lo que no hace un humano.**
3. **Reparto proporcional** por longitud de silaba, como ultimo recurso.

Y con dos topes sacados de tus 128 canciones, para que no salga algo imposible:
- velocidad de canto p50 **2.9 silabas/s**, p95 5.55
- duracion de silaba p50 **0.284 s**, p5 0.126

### Nivel C — con altura (`PART VOCALS`)
Solo tiene sentido si algun dia quieres jugar la parte de voz. Clone Hero no
puntua voz, asi que **esta despriorizado**: se deja el hueco en el modelo de
datos (`Silaba.pitch` ya existe) y no se implementa.

---

## 3. La verificacion que hace falta (el fallo #1 de todo esto)

**La `.lrc` que bajes esta cronometrada contra OTRO fichero de audio.** Otra
remasterizacion, otra edicion, un intro mas largo, un silencio distinto al
principio. Si se aplica tal cual, la letra va corrida toda la cancion y parece
que el sistema no funciona.

Por eso ninguna letra bajada se acepta sin pasar esto:

1. **Duracion.** Si la duracion que declara la fuente difiere mas de un 3 % de
   la del audio, es otra version: se descarta sin mirar mas.
2. **Desfase global.** Se mide la energia en la banda de voz (200–4000 Hz) del
   audio y se busca el desplazamiento que mejor alinea las marcas de linea con
   los arranques de canto. Un desfase constante se corrige y ya.
3. **Deriva.** Se ajusta una recta (desfase + estiramiento). Si el estiramiento
   se sale de ±0.5 %, son versiones distintas: se descarta.
4. **Residuo.** Si despues de corregir, mas del 20 % de las lineas queda a mas
   de 400 ms de un arranque de canto medible, se descarta y se baja de peldano.

Y ademas hay que respetar dos desfases que ya existen en el formato y que se
olvidan siempre: el `Offset` del `.chart` y el `delay` del `song.ini`.

---

## 4. Como se mide si esto funciona (el banco de voz)

Igual que el banco de notas, y con la misma idea: **hay 128 charts con voz
escrita a mano, o sea 49 459 silabas con su tiempo humano al lado.** Eso es un
banco de pruebas gratis.

**El experimento:** coger una cancion con voz humana, **tirar los tiempos**,
quedarse solo con el texto, volver a alinearlo con el sistema, y comparar contra
lo que escribio la persona.

Metricas, y los objetivos que propongo:

| Que se mide | Objetivo |
|---|---|
| error mediano por silaba | < 120 ms |
| silabas a menos de 250 ms | > 80 % |
| lineas que empiezan a menos de 300 ms | > 90 % |
| silabas por frase, contra la distribucion humana (p50 8) | dentro de p25–p75 |
| silabas por segundo (p50 2.9) | dentro de p25–p75 |

Y una trampa que hay que anotar antes de medir: **los charts venidos de MIDI
llevan desfase de autoria** (+65/+70 ms medidos en las notas). Si no se descuenta,
el banco de voz medira la costumbre del charter y no el alineado — es
exactamente el error que ya costo horas en el banco de notas.

---

## 5. Lo que hay que partir bien: las silabas — YA MEDIDO

`autochart/silabas.py` esta escrito, y `tools/banco_silabas.py` lo mide contra
**los cortes que hicieron los charters humanos**: en un chart de voz, la silaba
que acaba en `-` se pega a la siguiente, asi que tus 128 canciones traen las
palabras ya partidas por personas. Corpus gratis, en los dos idiomas.

| | espanol (29 canciones, 1 255 palabras) | ingles (99 canciones, 2 390 palabras) |
|---|---|---|
| palabra exacta | **51.4 %** | 66.8 % -> **81.7 % con pyphen** |
| ... de las que el humano SI partio | **88.3 %** | 45.1 % -> **63.8 % con pyphen** |
| fronteras acertadas | **92.9 %** | 62.1 % -> **71.1 %** |
| fronteras que puse de mas | 44.1 % de precision | 51.6 % -> **84.7 %** |

**Decision medida: se adopta `pyphen`** (6 MB, Python puro, opcional). El
heuristico se queda como respaldo para cuando no este.

### El hallazgo que cambia el diseno del alineador

Mira la fila del espanol: **acierto de fronteras 92.9 %, precision 44.1 %.**
Traducido: donde el humano corta, yo casi siempre corto igual — pero **corto en
el doble de sitios**. El humano partio 506 de las 1 255 palabras; yo parto
casi todas (1 579 fronteras contra sus 750).

No es que el humano silabee mal. Es que **el humano no silabea la palabra:
silabea la MELODIA.** Una palabra cantada sobre una sola nota se queda entera
aunque tenga tres silabas. El numero de eventos lo decide cuantos ataques de voz
hay, no el diccionario.

Consecuencia directa para el nivel B del §2, y es un cambio de orden de las
etapas:

```
   MAL (lo que parecia obvio)        BIEN (lo que dice la medida)
   1. partir la palabra              1. contar los ataques de la ventana
   2. repartir los ataques           2. partir la palabra en ESE numero de
      entre las silabas                 trozos, como mucho sus silabas
```

El silabeador deja de ser el que manda y pasa a ser **el techo**: dice en
cuantos trozos *se puede* partir; la musica dice en cuantos *se parte*.

### Dos avisos sobre el propio corpus

1. **Varios charts en espanol estan partidos con un silabeador ingles**
   (*mar-i-ner-o*, *Es-per-an-do*, *pon-ien-te*). Y al reves: hay charts en
   ingles partidos con reglas espanolas (*A-rrows*, *spa-rrow*). El criterio
   humano esta contaminado y **el 100 % no es el objetivo**: por encima del
   ~90 % en espanol se estaria copiando el error de alguien.
2. **9 de las 29 canciones en espanol estan escritas sin tildes** (medido: 20
   con, 9 sin, y cero caracteres corruptos). No es un fallo de lectura, es como
   las escribio el charter.

### Lo que queda por afinar (medido, barato)

Los fallos que quedan en ingles son casi todos del mismo tipo: *a-go*, *a-way*,
*o-kay*, *a-round*, *a-fraid*. pyphen **se niega a dejar una letra sola** porque
es un guionador de imprenta, y en canto esa vocal inicial suele llevar su propia
nota. Permitir silabas de una letra al principio de palabra deberia subir el
acierto de fronteras sin tocar nada mas.

**Y lo que escribas a mano manda.** Si en la letra pones `co-ra-zon`, se respeta
tal cual. Esa es la valvula de escape para que nada quede mal para siempre.

---

## 6. Fases

| Fase | Que se hace | Control |
|---|---|---|
| **V0 ✅** | leer la voz que ya existe + perfil de 128 canciones | `datos/perfil_voz.json`, 49 459 silabas |
| **V0.5 ✅** | silabeador es/en | 36/36 en la bateria de espanol |
| **V1 ✅** | banco de silabeo contra los cortes humanos | es 88.3 % / en 63.8 % en palabras partidas |
| **V1.5** | silabas de una letra al principio (*a-go*, *a-way*) | fronteras en ingles > 71.1 % |
| **V2 ✅** | escribir letra en `.chart` Y en `PART VOCALS` del `.mid` + validador | 55 canciones con letra, 53 limpias, 0 errores |
| **V3 ✅** | cliente de LRCLIB + las verificaciones del §3 | corrigio +1.70 s en una y rechazo 2 de otra version |
| **V4** | banco de voz: reconstruir el tiempo y comparar con el humano | error mediano < 120 ms |
| **V5** | reparto por ataques de voz (nivel B fino) | mejora sobre V4 |
| **V6** | transcripcion del audio, opcional | solo detras de bandera |

---

## 7. Decisiones tomadas, para no rediscutirlas

- **Se escribe en `.chart`, no en `.mid`.** El generador ya escribe `.chart` y
  Clone Hero lee la letra de `[Events]`. Un `PART VOCALS` en MIDI obligaria a
  cambiar el formato de salida entero para ganar cero.
- **La altura de la voz no se escribe.** Clone Hero no puntua voz.
- **La letra no se mete en el repo.** Igual que el audio: `.gitignore`.
- **Si la fuente no cuadra, no se pone letra.** Una letra corrida es peor que
  no tener letra: molesta durante toda la cancion y ademas parece que el
  programa esta roto.

---

## 7bis. Lo medido al ponerlo en marcha (21-08-2026)

Primera pasada real sobre los packs de customs (10, 11, 12, 13, 14):

| | |
|---|---|
| con letra nueva | **55** |
| ya la tenian | 44 |
| sin fuente en LRCLIB | 16 |
| rechazadas por no cuadrar | 2 |
| errores | **0** |

**La verificacion se gano el sueldo el primer dia.** `Grupo Ensamble - Tus
Jefes No Me Quieren` traia la letra con **+1.70 s de desfase** contra el audio
de Bruno: se corrigio sola midiendo la energia de voz contra las marcas del
`.lrc`. `Hombres G - Venecia` traia una letra de 270 s para una cancion de
201 s: rechazada. Y `Enrique Guzman - La Plaga` se cayo porque el 25 % de sus
lineas no tenian canto cerca.

**Los tres arreglos que salieron de mirar el resultado**, no de pensarlo antes:

1. **Juntar las marcas pegadas.** Un `.lrc` con dos marcas a menos de 0.35 s es
   el mismo momento; dejarlas sueltas daba frases solapadas, que el juego pinta
   borrando la linea anterior a media palabra.
2. **Partir las frases de mas de 15 silabas** (p95 humano) por final de palabra.
   Con `round()` una frase de 16 no se partia; con techo, si.
3. **Acotar el marcador de frase del MIDI** contra el arranque de la siguiente:
   el minimo de longitud del marcador se tragaba la frase de al lado y el juego
   pintaba las dos como una sola.

Y el freno del troceado, que es el hallazgo del §5 puesto en codigo: partir cada
palabra daba **33 % de silabas enlazadas** contra el 13.9 % humano. Con
`TROZOS_POR_PALABRA = 8/6` (las 8 silabas por 6 palabras que escribe un humano)
queda en **0.12-0.25**, dentro del rango.

## 8. Lo que ya funciona hoy

- `autochart/voz.py` lee los dos formatos y mide 128 canciones con voz.
- `autochart/silabas.py` parte espanol e ingles.
- `autochart/letras.py` busca en LRCLIB, verifica y escribe (chart y mid).
- `tools/minar_voz.py` saca `datos/perfil_voz.json`.
- `tools/poner_letra.py` pone letra a una cancion o a un pack entero.
- `tools/revisar_letra.py` dice cual salio torcida sin abrir el juego.
- `tools/banco_silabas.py` mide el silabeo contra los cortes humanos.

**Como se usa:**

```bash
python tools/poner_letra.py --pack 10 --pack 13    # un pack entero
python tools/revisar_letra.py                      # ver cual salio mal
```

El resultado queda en `salida/letras/<cancion>/` con **solo** el `notes.chart` o
el `notes.mid`: se copia ese fichero encima del de la cancion **desde el
Explorador** (`OneDrive\Documents` rechaza las escrituras de consola) y despues
**SCAN SONGS**.

**Un hallazgo del camino:** los 27 rips de Lego Rock Band guardan la silaba como
evento MIDI `text` (0x01) en vez de `lyrics` (0x05). Sin esa rama, esas 27
canciones se leian con todas sus notas de voz y **sin una sola palabra**.
