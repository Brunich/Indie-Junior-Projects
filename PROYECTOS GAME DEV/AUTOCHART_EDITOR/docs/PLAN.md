# Plan de AutoChart

## La idea

Tengo 763 canciones en Clone Hero y ~1000 charts hechos a mano por otra gente.
Quiero un programa que escuche **cualquier** cancion y saque un patron de 5
notas que valga la pena tocar. No un metronomo con colores: algo que siga el
riff, que repita cuando la cancion repite y que se sienta escrito.

## Como se decide que es "bueno"

Esta es la decision de diseno que sostiene todo lo demas: **no invento reglas de
lo que es divertido, las mido**. Los ~1000 charts humanos de la biblioteca son
el criterio. El comando `minar` los lee todos y saca las distribuciones reales:

| Medida | Mediana medida (882 charts, Experto) |
|---|---|
| Densidad | 3.75 notas/s |
| Proporcion de acordes | 0.35 |
| Proporcion de sostenidos | 0.15 |
| Notas repetidas seguidas | ver `datos/perfil_corpus.json` |

El generador apunta a esas cifras en vez de a numeros inventados, y el validador
avisa cuando un chart generado se sale del rango p5–p95 de lo humano.

Y hay una segunda prueba, mas dura: generar un chart para una cancion **que ya
tiene chart humano** y ver cuanto coinciden nota a nota. Eso es `tools/banco.py`.

## Fases

### F0 — Cimientos ✅ hecho
- Lector/escritor de `.chart`, lector de `notes.mid`.
- Minero del corpus -> `datos/perfil_corpus.json`.
- CLI en espanol: `minar`, `generar`, `revisar`.

### F1 — Sincronia ✅ hecho
Lo primero que hay que ganar: que las notas caigan donde suena la guitarra.
- Pulso desde la mezcla, ataques desde el stem de guitarra.
- Mapa de tempo que se **reengancha** cuando la cancion acelera, en vez de un
  BPM constante que se va desviando.
- La rejilla se suaviza antes de escribir el tempo: sin eso salian 254 eventos
  de tempo en *Keelhauled* con 6.9 % de desviacion, y la autopista se ve
  acelerar y frenar. Con ventana 3 quedan 161 eventos y 4.6 %; con ventana 5,
  154 y 3.1 %, pero el F1 del banco baja de 0.648 a 0.642. Se queda en 3.
- Medido en *Teddy Picker*: deriva del mapa de tempo **1.19 ms de media**
  (max 5.99 ms sobre 408 pulsos) y **100 %** de las notas a menos de 50 ms de un
  ataque real del audio (media 14.9 ms).

### F2 — Que siga el riff ✅ hecho
- Cuantizado a rejilla con tolerancia, control de densidad por ventana,
  asignacion de trastes por contorno de tono, motivos sacados del corpus cuando
  el audio no da tono util, reutilizacion de compases repetidos.
- Medido contra el chart humano de *Teddy Picker*: **F1 0.72**
  (recall 83.5 %, precision 63.6 %).
- Banco de 16 canciones con chart humano: **F1 medio 0.65**, 0 charts con
  errores de validacion.

El cambio que mas movio la aguja no fue ninguna heuristica bonita, fue bajar el
umbral de deteccion de ataques a 0: con un umbral "limpio" el generador solo
veia el 20 % de las notas que escribio el humano en *Everlong*, y el F1 medio
del banco estaba en 0.45 con la mitad de densidad de la que toca. Detectar de
sobra y dejar que la etapa de densidad elija subio el banco a 0.66.

### F3 — Que se sienta escrito 🔶 en curso
- ✅ **La mano se queda quieta como en los charts humanos.** La regla
  anti-repeticion sacaba la mano del traste en cuanto el tono se movia 0.75
  semitonos, y salia un 12.5 % de repeticiones frente al 27 % humano: se sentia
  inquieto. Con el umbral en 3 semitonos queda en **24.5 %**, dentro de la banda,
  y sin mover ni una nota de sitio (el F1 se quedo clavado en 0.648).
- ✅ **El hueco de densidad estaba diagnosticado al reves.** El filtrado acierta
  su objetivo casi exacto (3.76 pedido → 3.76 generado); lo que fallaba era el
  objetivo. Ver «La trampa del F1» mas abajo.
- ✅ **Las ligaduras ya se escriben** con la bandera `5`, en vez de dejar que el
  juego lo decida todo por la distancia entre notas. El humano corta la primera
  nota de una racha ligada (21.4 % de las veces) y liga la corchea recta cuando
  la mano se mueve un solo carril (11.9 %); son tasas medidas en 254 charts, no
  criterio. Deja 20-30 marcas por cancion, que es el presupuesto humano
  (mediana 20), y la ligadura real cae en 4.3-18.7 % contra el p50 humano de
  17.2 %. **Ojo: la cifra que estaba escrita aqui era falsa** — «34.2 %» era
  proximidad entre notas, no ligadura. Ver `DECISIONES_MEDIDAS.md` §7sexies.
- ❌ **Taps (`N 6`): no se escriben, y es decision.** La mediana de la biblioteca
  es cero por chart y solo el 26 % de los charts pone alguno.
- 🔜 Acordes con criterio armonico en vez de elegir la forma por sorteo.
- 🔜 Separacion con Demucs. Despriorizada con medida: ver la tabla de riesgos.

### La trampa del F1

Apuntar a un percentil mas alto del corpus **siempre** sube el F1, incluso
pasandose de densidad. Sobre la muestra de 24 canciones, donde el humano esta en
3.77 notas/s:

| Objetivo | F1 | Recall | Precision | Densidad generada |
|---|---|---|---|---|
| p50 | 0.666 | 0.702 | 0.652 | 3.64 (−3 % del humano) |
| p75 | 0.685 | 0.776 | 0.628 | 4.22 (+12 %) |
| p95 | 0.692 | 0.859 | 0.592 | 5.10 (+35 %) |

El F1 sube monotonamente hasta un 35 % por encima de la densidad humana, porque
cada nota de mas cae sobre un ataque real del audio: pilla mas notas humanas
(recall 0.702 → 0.859) y apenas pierde precision (0.652 → 0.592). **Es decir: el
F1 premia pasarse de notas, y llevado al limite se maximiza llenando la
autopista.** Por eso la densidad no la decide el F1, la decide el parecido con la
distribucion humana — y ahi p50 gana. Se queda p50 por defecto; `--percentil p75`
esta ahi para quien quiera el chart mas cargado a proposito.

Y de paso: la muestra de 16 canciones estaba sesgada hacia lo denso (humano
4.16 n/s) frente a la de 24 (3.77). Cualquier decision tomada con una sola
muestra hay que repetirla con otra distinta antes de creersela.
- Solos: marcar `E solo` / `E soloend` en los tramos donde la guitarra domina.
- Acordes con sentido armonico (el bajo de la cancion decide la forma) en vez de
  elegir la forma por sorteo entre las que contienen el traste.

### F4 — Dificultades de verdad
Ahora cada dificultad se genera por separado desde los mismos ataques. Lo
correcto es **reducir** desde Experto, para que Facil sea un subconjunto
reconocible de lo que suena en Experto y no otro chart distinto.

### F5 — Afinado con el banco
- Subir la muestra del banco a 40–60 canciones.
- Barrido de parametros (tolerancia de cuantizado, ventana de densidad, salto
  maximo de traste) puntuando con el banco.
- Objetivo: F1 medio > 0.65 sin que ningun chart genere errores de validacion.

### F6 — Uso diario
- Modo lote: apuntar a una carpeta y chartear todo lo que no tenga chart.
- Vista previa del patron sin abrir el juego (imagen de la autopista).
- Semilla en el nombre de la carpeta para poder regenerar variantes y quedarse
  con la que mas guste.

### F7 - Chartear tocando, en vez de que lo haga la maquina

Idea de Bruno (22-08-2026), y **es para el final**, no ahora:

> *"Poner en la interfaz tambien una [pantalla] en las que puedas tocar tu
> guitarra mientras esta reproducida tu cancion, y tu ir poniendo basicamente el
> patron de tu cancion como quieras, en vez de que te lo haga."*

O sea: suena la cancion, el toca, y lo que toque se graba como chart. Modo
charter en directo.

Por que encaja aqui y no es un capricho de interfaz:

- **Su mando funciona.** Medido en `scorestats.json` del 22-08: Cliffs of Dover
  en Experto con `controller_type: Guitar`, 908 de 1244 notas. El proyecto tenia
  escrito que la guitarra estaba muda por el protocolo de PS3; ya no lo esta.
- **La mitad del trabajo ya existe.** El escritor de `.chart` esta hecho
  (`chartio.py`), el mapa de tempo tambien, y cuantizar a la rejilla es lo mismo
  que ya se hace al generar. Lo que falta es leer el mando y grabar.
- **Y da algo que no tenemos: charts suyos.** Hoy el criterio de "buen chart"
  son los 347 humanos de la biblioteca, gente que no es el. Lo que el toque
  encima de una cancion es la unica muestra directa de su gusto, y sirve para
  calibrar el generador, no solo para jugar.

Lo que habria que decidir cuando toque: cuanto se cuantiza (a la rejilla o al
audio), que hacer con lo que toca a destiempo, y si se graban sostenidos.

## Lo que este proyecto NO va a hacer

- No toca la biblioteca original. Todo se escribe en `salida/`.
- No sube canciones a ningun sitio. El audio se queda en esta maquina; el repo
  ignora `.ogg`, `.mp3` y compania.
- No pretende sustituir a un charter humano. Pretende que una cancion sin chart
  pase de no ser jugable a serlo.

## Riesgos conocidos

| Riesgo | Estado |
|---|---|
| Canciones sin stem de guitarra dan patrones sucios | **Medido y mas pequeno de lo que parecia**: forzando la mezcla en las mismas 16 canciones el F1 baja de 0.648 a 0.618. Demucs tiene como mucho 0.03 que recuperar, asi que deja de ser prioridad |
| Tempo variable o rubato rompe la rejilla | Mitigado con el reenganche del mapa de tempo; sin medir en canciones con rubato fuerte |
| El contorno de tono falla con distorsion densa | Mitigado con los motivos del corpus; es la parte mas floja |
| 50 s por cancion (analisis) | Aceptable en lote; se puede cachear el analisis |
