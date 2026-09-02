# Plan por tandas: de aqui a que esto se use sin pensar

Cuatro cosas pedidas el 21-08-2026:

1. Letra en todas las de Guitar Hero, **como la escriben los charts buenos**
   (la linea que se canta y la siguiente asomando debajo, con animacion).
2. **Dificultades que valgan la pena**: Medio y Dificil que no sean Experto
   descafeinado, con momentos donde la cosa suba.
3. Las mejoras que quedaron sugeridas al generador.
4. Una **interfaz pequena** para meter canciones y elegir que hacer.

**El orden no es el que pide el enunciado.** Va primero lo que ya esta medido y
tiene un numero que perseguir, y la interfaz va al final a proposito: una
interfaz sobre un sistema que aun cambia de forma hay que rehacerla dos veces.

| Tanda | Que | Por que ahi |
|---|---|---|
| **1 HECHA** | La letra, con la geometria del humano | Ya esta medida la diferencia exacta. Es barato y se nota al instante |
| **2 HECHA** | El sistema de dificultades (era el mismo problema que 3a) | Es lo que mas cambia la sensacion de jugar, y hoy no existe de verdad |
| **3** | Caracter por cancion (3a hecha con la 2; quedan 3b-3e) | Diagnosticado con numeros, pero es la mas cara |
| **4 HECHA** | La interfaz | Cuando lo de debajo ya no cambie de forma |

Regla que se aplica a las cuatro: **una tanda no se cierra sin su numero**. Si
al medir no mejora, se revierte y se escribe el descarte.

---

## TANDA 1 — La letra, como la escribe un humano

### Lo que ya esta medido

128 charts de voz humanos contra las 198 letras que puso AutoChart:

| | humanas | mias |
|---|---|---|
| hueco entre frases | p25 0.07 · **p50 0.36** · p75 0.73 s | **0.15 s, siempre** |
| la frase aparece antes de cantarse | +0.06 s | +0.15 s |
| alturas distintas en `PART VOCALS` | **10** | 0 (una nota fija) |

**Mi hueco entre frases es una constante.** Es exactamente la misma enfermedad
que tiene el generador de notas (34.8 % de acordes en todas las canciones): se
clava una media y no se varia. El humano no elige el hueco, **lo deja la
musica**: la frase acaba cuando se deja de cantar y el hueco es lo que haya
hasta la siguiente.

### Que se cambia y donde

1. **`letras.construir_frases`** — `phrase_end` deja de ser "0.30 s antes de la
   linea siguiente" y pasa a ser **el final de la ultima silaba**. El hueco deja
   de ser un parametro y pasa a ser una consecuencia.
2. **`AVISO_DE_FRASE_S`** de 0.15 a **0.06**, que es la mediana humana.
3. **`letras.escribir_en_midi`** — altura de la nota. Hoy es `PITCH_VOZ = 62`
   fija. El humano usa ~10 alturas distintas.

### La duda honesta, y como se resuelve

**No se con certeza que hace aparecer la segunda linea en Clone Hero.** Puede
ser el hueco (si la frase acaba pronto, hay tiempo de asomar la siguiente),
puede ser que el juego lo haga siempre y con 0.15 s no diera tiempo a verlo, o
puede pedir algo del `PART VOCALS` que hoy no escribo.

Por eso la tanda hace las tres cosas a la vez **para dejar el fichero igual que
uno humano**, y la comprobacion es mirarlo en el juego: `Arctic Monkeys - Knee
Socks` (humano, se ve bien) contra la misma cancion regenerada. Si con la
geometria humana sigue sin salir la segunda linea, el problema no era la
geometria y se escribe el descarte.

### Con que se mide

```bash
python -m autochart letra --pack 03 --forzar
python -m autochart revisar-letra
```

- hueco entre frases: de 0.15 fijo a **p50 dentro de 0.20–0.55** y con
  desviacion mayor que cero (que varie, que es el punto).
- 0 errores en `revisar-letra`, como hoy.
- **La prueba de verdad la haces tu**: una cancion regenerada al lado de una
  humana, y si se ve la segunda linea.

### Control que no debe bajar

`revisar-letra`: 191 limpias, 0 errores. Y `autochart censo`: 328 con letra.

---

## TANDA 2 — Dificultades que valgan la pena

### El problema, en una frase

Hoy Facil, Medio y Dificil **heredan el traste de Experto y se les quitan
notas** con un objetivo de densidad plano. Sale un Experto descafeinado: la
misma cancion todo el rato, mas lenta. Y ademas Facil sale con **0 marcas de
ligadura** cuando el humano pone unas 5.

Lo que pides — *"que tengan momentos donde suba la dificultad"* — es
exactamente lo que un reductor plano no puede dar.

### Lo que hay que medir primero (y ya esta corriendo)

Sobre las canciones humanas que traen **las cuatro** dificultades:

1. **Cuantas notas guarda cada dificultad** respecto a Experto.
2. **Si es un subconjunto o un chart nuevo**: cuantas notas de Medio caen
   exactamente donde una de Experto. Si es alto, reducir es lo correcto; si es
   bajo, el humano vuelve a chartear y copiar eso es otro trabajo.
3. **Politica de acordes y sostenidos** por dificultad.
4. **La curva dentro de la cancion**: si Medio reparte el recorte por igual o
   **guarda los picos**. Esta es LA medida de esta tanda. Si la curva de Medio
   es mas plana que la de Experto, el humano tambien aplana y no hay nada que
   arreglar; si conserva la forma, hay que conservarla.

### Que se cambia y donde

`generate.py:inherit_expert_lanes` y `generate.py:thin`, mas
`DIFFICULTY_SPECS`. La idea de diseno, a confirmar con la medida:

- El objetivo de densidad de cada dificultad deja de ser un numero y pasa a ser
  **una curva**: la de Experto, escalada y **con los picos conservados**.
- **Momentos**: los tramos que en Experto son rafaga o solo se recortan **menos**
  que el resto. Asi Medio tiene sus subidas en el mismo sitio que Experto, que
  es lo que hace que se sienta la misma cancion.
- Ligaduras en Facil: hoy no hay hueco de corchea que ligar. Se revisa si el
  humano las pone en otro sitio.

### Con que se mide

`autochart comparar` ya sabe medir cualquier dificultad. Objetivos:

- notas de cada dificultad respecto a Experto: dentro del p25–p75 humano.
- **contraste de densidad de Medio y Dificil: dentro del rango humano**, que es
  la medida de "tiene momentos".
- que el chart de Medio siga siendo reconocible como la misma cancion: % de
  notas que caen sobre una nota de Experto, contra el mismo % humano.

### Control

`banco --muestra 24`: f1_medio **0.660** (Experto). Esta tanda no deberia
moverlo — si lo mueve, se toco Experto sin querer.

**Y lo que NO se hace en esta tanda:** regenerar la biblioteca. Se desarrolla el
sistema y se prueba en 4–6 canciones de estilos distintos, como pediste.

---

## TANDA 3 — Que el chart tenga caracter

Son las mejoras que quedaron sugeridas, en orden de cuanto se notan:

### 3a. Que la cancion respire
`respiro` sale **0.00 por 100 notas en las seis** canciones medidas, contra 0.70
del humano, y el contraste cae bajo el p5 humano en las seis. Causa localizada:
`thin` reparte la densidad por ventana, o sea que aplana a proposito.
**Objetivo: contraste de 1.2 a dentro de p25–p75 humano (1.9–4.5) sin mover el
nps de 3.4–3.5.** Cuidado: si el contraste sube metiendo mas notas en los picos,
el banco lo tapara, porque el F1 premia pasarse.

### 3b. Que los acordes salgan de la cancion, no de la mediana
Desviacion de acordes en lo generado: **0.000**. Siempre 34.8 %, sea Thunderhorse
(humano 0 %) o una cumbia (humano 77 %). Hace falta una senal del audio -
polifonia por ataque - y es una tanda entera para ella sola.

### 3c. La letra como mapa de la cancion
**Esta es la mas barata y la que menos se ve venir.** Ahora hay 328 canciones
con la voz alineada. Eso dice donde estan el verso y el estribillo **sin
analizar nada**: donde se canta hay verso, donde se repite la misma frase hay
estribillo, y donde no se canta suele haber solo. Es justo la informacion de
arquitectura que le falta a 3a, y ya esta en el disco.

### 3d. Bajo y ritmica
Medido: **el bajo no tiene acordes (0.00)** y tiene once veces menos anclas que
la guitarra. Un generador de bajo que copie las reglas de la guitarra esta
garantizado que se sienta mal. Es el instrumento que falta y el mas facil de
anadir bien, porque su regla principal ya esta medida.

### 3e. Que las herramientas griten cuando midan cero
El banco devolvio 0 canciones durante semanas sin quejarse, y `atlas.escanear`
se traga las excepciones por carpeta. **Una herramienta de medida que falla en
silencio es peor que una que no existe**, porque da confianza falsa.

---

## TANDA 4 — La interfaz

Solo cuando 1–3 esten cerradas. Que hace, y nada mas:

- Arrastras una carpeta o un mp3 (o varios).
- Casillas: **generar chart** / **poner letra** / **instalar en la biblioteca**.
- Que dificultades: Facil, Medio, Dificil, Experto.
- Un boton, una barra de progreso, y **el informe de los validadores en
  pantalla** con lo que salio mal, no un "listo".

Decisiones ya tomadas para no rediscutirlas:

- **`tkinter`**, que viene con Python. Cero dependencias nuevas, cero MB.
- **La interfaz no lleva logica.** Llama a los mismos comandos que la consola.
  Si hace algo que la consola no puede hacer, esta mal hecha.
- **Nada de instalar sin respaldo.** El boton de instalar usa
  `instalar_letras.py`, con su `--deshacer`.

---

## Lo que puede salir mal, y que se hace

| Riesgo | Que se hace |
|---|---|
| La segunda linea no depende de la geometria | Se escribe el descarte y se mira el `PART VOCALS` del humano campo por campo |
| El humano tambien aplana las dificultades | Entonces la tanda 2 se queda en "no tan facil" y se suelta lo de los momentos |
| El contraste sube a base de notas de mas | El banco lo tapara: la densidad se vigila aparte del F1 |
| La interfaz se adelanta | Va la ultima, y si 1-3 se alargan, se queda sin hacer |


---

## Lo cerrado el 21-08-2026

**TANDA 1 hecha.** Hueco entre frases de 0.15 s constante a **p50 0.38 s** con
desviacion real (humano 0.36). Dos cambios: `phrase_end` sale de la ultima
silaba, y las silabas ocupan lo que se tarda en cantarlas (2.9 sil/s) en vez de
toda la ventana hasta la linea siguiente. **Queda por comprobar en el juego** si
esto es lo que hace asomar la segunda linea.

**TANDA 2 hecha, y resulto ser la 3a.** Medido sobre 284 canciones humanas con
las cuatro dificultades: la escalera que ya teniamos era correcta (41/63/86/100
contra 40/57/85/100 humano, acordes y sostenidos casi clavados). Lo unico roto
era el contraste, 1.1-1.2 en las cuatro contra 2.05-2.85 humano. **Las
dificultades aburridas y la cancion que no respira eran el mismo problema**, y
la causa era una linea de `thin`: el mismo presupuesto de notas por ventana
suene lo que suene.

  contraste  Easy 2.01 (humano 2.05) · Medium 2.27 (2.24) · Hard 2.01 (2.52) ·
             Expert 2.28 (2.85)
  respiro    de 0.00 en las cuatro a 3.42 / 0.76 / 0.26 / 0.16 por 100 notas
  control    banco 24/24, f1 0.670, precision 0.662 -> 0.703, 0 errores

**TANDA 4 hecha.** `autochart interfaz`.

### Lo que queda, por valor

1. **3c, la letra como mapa** (la mas barata y la que menos se ve venir): 328
   canciones con la voz alineada dicen donde hay verso, estribillo y solo sin
   analizar nada. Es lo que le falta al contraste para saber **donde** poner los
   picos en vez de solo cuanto.
2. **3b, acordes por cancion**: desviacion 0.000, siempre 34.8 %. Pide una senal
   de polifonia del audio y es una tanda entera.
3. **3d, el bajo**: no tiene acordes (0.00 medido) y once veces menos anclas.
4. **3e, que las herramientas griten al medir cero.**
5. Subir el contraste de Hard y Expert, que se quedaron en 2.0-2.3 contra
   2.5-2.85: probablemente subiendo `CONTRASTE_ALFA` por encima de 0.75.
