# AutoChart — todo lo que hace falta saber para seguir

**Si acabas de abrir un chat sobre este proyecto, lee esto y `CLAUDE.md`. Nada
mas.** Con eso se puede producir: no hace falta leer el codigo, y el historial
de decisiones **no se lee, se consulta**.

| Documento | Cuando |
|---|---|
| **`CLAUDE.md`** (raiz) | Siempre. Las reglas: como se mide, las trampas, como se cierra una tanda. |
| **Este** | Siempre. Que es, donde esta todo, estado de hoy, y **la** tarea siguiente. |
| `DECISIONES_MEDIDAS.md` | Antes de tocar una parte, o antes de gastar una tanda en una idea: ahi estan **las que ya se midieron y se descartaron**. |
| `FORMATO_CHART.md` | Cuando toques la escritura del `.chart`. |
| `PLAN_PATRONES.md` | **Patrones**: que se mide, los 7 confusores, y que es "divertido" partido en 6. |
| `PLAN_VOZ.md` | **Letra y karaoke**: de donde sale la letra, como se sincroniza, como se mide. |
| `ARQUITECTURA.md` | Cuando pida cortarse en sistemas. Y `PLAN.md`, el mapa de fases largo. |

Al final hay **un solo bloque** con la tarea siguiente. El bloque nuevo
sustituye al viejo, no se anade debajo — lo vigila
`python tools/verificar_puerta.py`.

---

## 1. Que es esto

Un programa que escucha una cancion y saca un `notes.chart` de 5 trastes
jugable en Clone Hero: pulso, ataques, contorno del riff, acordes, sostenidos,
Star Power y las cuatro dificultades. Tarda **~13 segundos** por cancion.

- Repo privado: `Brunich/clonehero-autochart`
- Local: `C:\Users\bruni\OneDrive\Desktop\Programming Brunich\codigos\PROYECTOS GAME DEV\AUTOCHART_EDITOR`
- Python 3.10 + librosa + mido. `ffmpeg` en el PATH para los mp3.

## 2. Donde esta el material

| Que | Donde |
|---|---|
| **Clone Hero que Bruno juega** | `C:\Users\bruni\OneDrive\Desktop\Games\Clone Hero\Clone Hero.exe` (v1.1.0.6142) |
| Instalacion vieja, no la uses | `C:\Users\bruni\AppData\Local\Programs\Clone Hero` (v1.0.0.4080) |
| **Las canciones** | `C:\Users\bruni\OneDrive\Documents\Clone Hero\Songs` |
| Ajustes y registro del juego | `C:\Users\bruni\OneDrive\Documents\Clone Hero\` (`settings.ini`, `badsongs.txt`, `Logs\`) |
| **Cancion de prueba de Bruno** | `...\Shit de AI ROGUE\rolas mias Ais\ACEPTADOS AL PROYECTO\ACEPTADOS IN GAME(BUENAS)\Mejores(MOMENTOS ESCOGIDOS Y ESPECIALES\Electro_guitar_Cyber_Club_v1.mp3` |

`Songs\` ya acepta escrituras de consola desde el 21-08 (si vuelve a fallar con
"Could not find file", el arreglo es copiar desde el Explorador). Aun asi **la
biblioteca no se toca**: todo va a `salida/`, ignorada por git.

La biblioteca **cambia**: hoy son 392 charts humanos (224 `.mid` + 168
`.chart`); antes fueron 763 carpetas y 20.6 GB. **Cualquier percentil calculado
con otro recuento esta medido sobre otra cosa.**

La cancion de prueba es musica suya de IA Rogue: un mp3 suelto, sin stems y sin
chart humano. Ahi **no se puede medir el F1** porque no hay humano contra quien
comparar; se mide la sincronia y las metricas de sensacion contra el corpus.

## 3. La idea que sostiene el proyecto

Lo que cuenta como "buen chart" **no se inventa, se mide**. Los charts hechos a
mano que hay en el disco son el criterio.

```bash
python -m autochart minar                              # -> datos/perfil_corpus.json
python -m autochart minar --solo-oro datos/corpus_oro.json   # -> perfil_oro.json
```

El generador apunta a los percentiles del perfil ACTIVO (hoy el del oro, 60
charts) y el validador avisa cuando se sale de p5-p95. **Los numeros no se citan
de memoria: se leen del JSON.** Una cifra escrita antes del 23-08 esta calculada
sobre otra biblioteca (fueron 882 charts, hoy son 394), y una de ligadura escrita
antes del 24-08 esta calculada con media regla -- el lector de `.mid` tiraba las
marcas de forzado. Hoy: ligadura mediana **0.154** sobre 392 charts (los `.chart`
0.167, los `.mid` 0.142).

## 4. Como usarlo

**Hay un solo comando y se descubre solo.** `python -m autochart` a secas lista
lo que se puede hacer agrupado por objetivo y `autochart estado` dice que hay
hoy; los ficheros de `tools/` tienen todos su subcomando.

```bash
python -m autochart estado                       # que hay y que hacer
python -m autochart generar "<carpeta o audio>"  # --densidad 1.2 --percentil p75
python -m autochart revisar "salida/.../notes.chart"

python -m autochart censo                        # letra: que hay, que falta, que es instrumental
python -m autochart letra --pack 10              # se la pone a un pack
python -m autochart revisar-letra                # cual salio torcida
python -m autochart instalar --probar            # y sin --probar, la instala

python -m autochart minar / voz / atlas          # las tres varas medidas
python -m autochart comparar                     # lo nuestro contra el humano
python -m autochart banco --muestra 24           # el control, ~7 min
python tests/test_basico.py                      # 26 pruebas, sin audio
python -m autochart puerta                       # que la entrada no engorde
```

**Los validadores no miran lo mismo y hacen falta los tres.** `revisar` dice si
el chart es musicalmente sano; `en-juego` si el juego puede cargarlo y jugarlo
entero; `revisar-letra` si la letra esta bien puesta.

Para jugar algo generado hay que copiarlo a `Songs\` y hacer **SCAN SONGS**.
Para las letras lo hace `autochart instalar`, con respaldo y `--deshacer`.

## 5. Como funciona por dentro

```
audio ─┬─ mezcla   ──► pulso, mapa de tempo con reenganche      timing.py
       └─ guitarra ──► ataques + 3 medidas por ataque:          audio.py
                         · tono, buscado en el registro
                           de la SOLISTA (MIDI 55-96)
                         · ring: cuanto sigue sonando
                         · lead: cuanto manda lo melodico
                           sobre lo grave
                          │
              cuantizar a la rejilla                            quantise
              recortar entrada y final del audio                generate_chart
              densidad por ventana, prefiriendo `lead` alto     thin
              trastes por INTERVALO -> paso de carril           _contour_to_lanes
              limites de salto y motivos del corpus             assign_frets
              reutilizar compases repetidos                     reuse_repeated_bars
              acordes EN TRAMOS, manteniendo la postura         build_notes
              sostenidos: el `ring` corta el largo              assign_notes
              Star Power: 10 frases de 7 tiempos                star_power_phrases
              LIGADURAS: rasguear la primera de la racha        hopo_flags
              Experto primero; las demas HEREDAN su traste      inherit_expert_lanes
                          │
              notes.chart + song.ini                            export.py
```

Todo lo de la columna derecha vive en `generate.py` salvo la ultima linea, y las
mayusculas marcan lo que se cambio en agosto. El porque, con numeros, en
[DECISIONES_MEDIDAS.md](DECISIONES_MEDIDAS.md).

| Fichero | Que hace |
|---|---|
| `chartio.py` / `midiio.py` | leer y escribir `.chart`; leer `.mid` para minar |
| `corpus.py` / `atlas.py` | medir los charts humanos → perfil y gestos |
| `audio.py` / `timing.py` | pulso, ataques, tono, ring; mapa de tempo |
| `generate.py` | el nucleo: de ataques a notas |
| `validate.py` / `export.py` | errores y avisos; carpeta lista para el juego |
| `cli.py` | `minar` / `generar` / `revisar` / `letra` |

## 6. Las trampas de las herramientas de medida

**Estan en `CLAUDE.md` seccion 2 y hay que leerlas antes de tocar nada**; el
detalle con las tablas, en [DECISIONES_MEDIDAS.md](DECISIONES_MEDIDAS.md)
seccion 9. Las dos que mas tandas han costado: **el banco no ve los trastes**
y **el F1 premia pasarse de notas** (hasta un 35 % por encima del humano).

## 7. Las cinco cosas que costaron horas y no son obvias

1. **El umbral de deteccion de ataques va a 0.** Con uno que "se ve limpio"
   (0.05) solo aparecia el 20 % de las notas del humano en *Everlong*; con 0, el
   97-100 %. Se detecta de sobra y la etapa de densidad elige: F1 0.45 -> 0.66.
2. **El pulso se busca en la mezcla, las notas en el stem de guitarra.** Sobre
   guitarra aislada el detector de pulso se equivoca de compas entero.
3. **Los charts convertidos de MIDI llevan desfase de autoria** contra el audio
   (+65/+70 ms). Sin descontarlo, comparar con el humano da 4 % en vez de 76 %.
4. **Los umbrales de sostenido van en segundos y en tiempos, manda el menor.**
   Solo en segundos, a 151 BPM *Teddy Picker* salia al 0.2 % contra el 12.9 % de
   su charter; solo en tiempos tampoco, porque el detector puede devolver la
   mitad del tempo (*Keelhauled*: 110 detectados, 220 charteados).
5. **Repetir traste no es un defecto.** La regla anti-repeticion movia la mano
   en cuanto el tono se iba 0.75 semitonos y daba 12.5 % de repeticiones contra
   el 27 % humano. Con el umbral en 3 semitonos queda en 24.5 %.

## 8. Lo hecho antes del 23-08 (el detalle, en DECISIONES_MEDIDAS.md)

**Sincronia, y no depende de la biblioteca** (*Teddy Picker*): deriva del mapa
de tempo 1.19 ms de media, cada nota a 14.9 ms del ataque real, **100 %** por
debajo de 50 ms. **Lo unico probado en el juego:** Clone Hero v1.1.0.6142
**carga** los charts (0 errores al escanear). Jugar uno entero sigue pendiente
del mando (seccion 12).

Y tres cosas que ya funcionan y no hay que rehacer: la **letra de karaoke**
(21-08, `autochart letra`, 328 de 391 canciones, con respaldo y `--deshacer`);
el **contraste por energia del audio**, que es lo que hizo respirar al generador
(Experto 1.14 -> 2.28, y Facil con MAS contraste que Experto a proposito,
decision de Bruno); y **cuatro fallos silenciosos** ya cazados (el banco
devolviendo 0 canciones, `atlas.escanear` tragandose 35 charts, `HARM1` en vez
de `PART VOCALS`, y el instalador dejando pasar lo que el validador marcaba).

---

## 10. LA TAREA SIGUIENTE

```
Proyecto: ...\PROYECTOS GAME DEV\AUTOCHART_EDITOR  (repo Brunich/clonehero-autochart)
Lee CLAUDE.md, este documento y las TRES ultimas secciones de
docs/DECISIONES_MEDIDAS.md (la ligadura, la cadena, y el tremolo). La cancion de
REFERENCIA la puso Bruno: Stevie Ray Vaughan - Pride & Joy. La prueba de
aceptacion es una orden:
    python tools/contra_el_humano.py --pride --generar

TAREA: que el BANCO DE MOTIVOS sepa quedarse quieto.

1) POR QUE, con el numero
   Escribimos dos gestos: anclado + salto_ancho son el 74.7 % de los nuestros y el
   54.8 % de los suyos, y el que mas falta es el tremolo -- de las rachas de largo
   >= 4, van a un solo traste el 19.9 % de las humanas de largo 4 y el 0.7 % de
   las nuestras (10.0 % contra 0.0 % en las de largo 8+).
   Ya esta medido quien se lo come: `flat_run >= 3` le pasa el mando al banco
   diciendo que el audio no dice nada, cuando con las notas pegadas lo que dice es
   TREMOLO. Y ya esta medido que quitarle el banco NO es el arreglo: sale tremolo
   (0.7 % -> 2.8 %) y "todas iguales" se va de 6.9 a 10.6 veces, porque entonces
   todas las tiradas de todas las canciones hacen lo mismo. El banco hace DOS
   trabajos y hay que dejarle el segundo.

2) QUE HAY QUE CAMBIAR, Y DONDE
   `generate._motif_bank` (:1095) y su uso en `assign_frets` (:1150).
   a) Las formas son carriles ABSOLUTOS -- `corpus.py:147` mina
      `trigrams[f"{a[1]}{b[1]}{c[1]}"]` -- asi que el `000` que SI esta en el banco
      no dice "quedate donde estas" sino "vete al verde", y a mitad de cancion
      tira la mano. Aplicarlas como movimientos RELATIVOS al carril de ahora es lo
      que deja al banco escribir un tremolo sin perder su variedad.
   b) El peso `max(1, min(6, count // 40))` aplasta la frecuencia: `000` es el
      trigrama MAS frecuente del corpus (2.560, por delante de 321 y 123) y se
      lleva 64 -> recortado a 6, lo mismo que una forma 64 veces mas rara. Las
      planas quedan en el 8.5 % del banco cuando son el 16.7 % del corpus.
   Empezar por (a), que es la que explica el 0.7 %. Una cosa a la vez.

3) CON QUE SE MIDE
   python tools/panel_generos.py --perfil datos/perfil_oro.json --salida ...
   python tools/parecidas.py salida/<lote>        "todas iguales", HAY QUE MIRARLA
   python tools/transiciones.py --biblioteca salida/<lote> --comparar \
       datos/transiciones.json                    el reparto de gestos
     objetivo: rachas de un solo traste de 0.7 % a >= 8 %, y con ello
     anclado+salto_ancho de 74.7 % a <= 65 %, SIN que la distancia pase de 0.384
     ni "todas iguales" de 6.9.

4) CONTROL (no debe bajar)
   python tests/test_basico.py                          -> 27 OK
   python tools/contra_el_humano.py --pride --generar   -> 819 notas, F1 0.586,
     distancia 0.066, sostenidos 0.095
   python tools/revisar_in_game.py salida/<lote>        -> [OK] en todas
   python tools/verificar_puerta.py                     -> verde

5) OJO -- descartados CON NUMERO, no repetirlos
   Del tremolo: quitarle el banco a las notas rapidas (sube el tremolo y "todas
   iguales" a 10.6) y tomar la decision de alternancia una vez por tirada (la tasa
   ya era buena: 24.5 % contra 29.8 %; la alternancia solo decide el 9.0 %).
   De la cadena: RACHA_VENTANA, el escalon de semicorchea, y CADENA_PREMIO.
   De la ligadura: predecirla por genero o por densidad.
   De los agujeros: bajar CONTRASTE_SUELO, quitar el premio a la rejilla.
   De la densidad: el audio, los 392 en vez del oro, la recta del BPM.
   **Y la leccion de la semana: un cambio bueno en su medida se cae en otra.**
   Tres se cayeron en la distancia de gestos y uno en `parecidas`. Mira las DOS
   antes de dar algo por bueno, y las trampas de CLAUDE.md §2.6 y §2.7.

6) DESPUES
   El resto del vocabulario: `escalera_baja` (0.9 % nuestro contra 5.4 % suyo) y
   `acorde_martillo` (1.7 % contra 5.5 %), que el humano persiste al 50 % y
   nosotros abandonamos al 0 %.
```

## 11. Estado al cerrar

Aqui va **solo lo que esta vivo**. Lo cerrado se cuenta entero en
[DECISIONES_MEDIDAS.md](DECISIONES_MEDIDAS.md), que se consulta y no se lee: los
sostenidos y el `ring`, el perfil por genero, la densidad, los agujeros, la
ligadura y la cadena. Si una tanda cierra un capitulo, su relato se va ahi y aqui
queda una linea.

- Rama de tema sobre `feat/v0-pipeline`, un PR por tanda. **27 pruebas OK.**
- **Los numeros que no deben bajar.** Pride & Joy: 819 notas de sus 982, F1
  **0.586**, distancia de gestos **0.066** (dos humanos cualesquiera estan a
  0.582), sostenidos 0.095. Panel de 10: distancia **0.384**, F1 0.505, error de
  nps 1.033, acordes 0.200, sostenidos 0.035, ligadas **0.105**, "todas iguales"
  6.9 veces. Cadena de ritmo 1.94 y racha de ligadura 1.60.
- **Dos palancas apagadas con su tabla en `generate.py`**, que se encienden
  cambiando un numero: `RACHA_VENTANA` (hace los agujeros humanos y cuesta las
  ligadas) y `CADENA_PREMIO` (alarga la cadena y cuesta la distancia). Y el
  arreglo de la fuga del presupuesto, medido y no adoptado.
- **La firma que hay que reconocer antes de gastar una tanda:** si un cambio sube
  el F1 y empeora la distancia de gestos, el chart se esta yendo donde suena en vez
  de donde manda el compas. Ya ha salido tres veces.
- **Y el aviso que ha costado dos objetivos esta semana:** antes de perseguir un
  numero, mirar de que poblacion sale. El de racha >= 2.8 venia de los `.chart`
  (3.16) y los diez humanos del panel estan en 1.78.
- **Las 15 canciones de Bruno: regeneradas e instaladas el 24-08**, ahora con las
  CUATRO dificultades (antes solo Expert). 15 de 15 `[OK]` in-game, cero avisos
  del validador; las viejas en `salida/respaldo_charts_bruno/`. **Pendiente: que
  Bruno haga SCAN SONGS y las pruebe.**
- **El tremolo (24-08):** es el gesto que mas falta (rachas de un solo traste,
  0.7 % nuestro contra 14.4 % suyo) y ya esta localizado -- `flat_run >= 3` le pasa
  el mando al banco justo donde el audio dice tremolo. Quitarselo NO es el
  arreglo: sube el tremolo a 2.8 % y "todas iguales" de 6.9 a **10.6**. El banco
  hace dos trabajos.
- Biblioteca: 332 de 395 con letra (132 humanas + 200 de AutoChart, con firma y
  `--deshacer`). `salida/` es desechable y esta ignorada por git.

## 12. El mando de Bruno (06-08-2026) - bloquea la prueba de jugarlo

La guitarra (`054C:0268`) habla protocolo de PS3 y no manda un solo informe
hasta que el host le envia el feature report `0xF4`. Windows no se lo manda,
asi que **aparece como mando bueno y esta muda** (medido: 3 s de silencio contra
547 bytes en 9 ms de su DualShock 4). No es Clone Hero ni el mapeo. Arreglo:
**DsHidMini**, driver de kernel, pendiente de que Bruno lo autorice.

Aparte: el menu de perfiles lanza `NullReferenceException` en bucle.
`profiles.ini` esta intacto; se renombra y el juego lo reconstruye.
