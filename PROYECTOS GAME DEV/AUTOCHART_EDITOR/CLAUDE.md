# ⚠️ ESTO ES UNA COPIA DE UNA RAMA, NO UN PROYECTO

> **Lee esto antes que nada (comprobado el 01-09-2026).**
>
> Esta carpeta **no es un proyecto**: es una copia de trabajo de la rama
> `editor/tocar-y-grabar` del repo `Brunich/clonehero-autochart`, que tiene
> **PR abierto**: <https://github.com/Brunich/clonehero-autochart/pull/3>
> («Editar charts que ya existen: rejilla, tempo, grabar tocando y sobrescribir
> un tramo», 4 commits).
>
> **Comprobado fichero a fichero:** `editar.py`, `grabar.py` e
> `interfaz_grabar.py` —lo unico que solo existe aqui— son **identicos a los de
> la rama**. El resto tambien (lo que parece diferir es solo fin de linea
> CRLF/LF). **No hay nada en esta carpeta que no este ya en GitHub.**
>
> **Que hacer con ella:** nada urgente, pero no se trabaja aqui. El trabajo va
> en el repo bueno (`PROYECTOS GAME DEV/AUTOCHART/`, o un `git worktree` de esa
> rama). Cuando el PR 3 se fusione o se cierre, **esta carpeta se borra**: hoy
> lo unico que hace es que haya dos AutoChart en el disco y no se sepa cual
> manda.
>
> Frente al AutoChart bueno le faltan `leadmap.py`, `phrases.py`, `preparar.py`
> y todo el `datos/` medido despues del 24-08.

---

# Como se trabaja en AutoChart

Esto son **reglas**, no historia. Se lee entero antes de tocar nada.

- **Entrada del proyecto:** `docs/SIGUIENTE_CHAT.md` (que es, donde esta todo,
  estado de hoy, y **la** tarea siguiente).
- **Por que el generador hace lo que hace:** `docs/DECISIONES_MEDIDAS.md`. Se
  consulta, no se lee: ahi estan **las ideas que ya se midieron y se
  descartaron**. Mirarlo antes de gastar una tanda en una idea razonable.
- **El formato del `.chart`:** `docs/FORMATO_CHART.md`.

---

## 1. La regla que manda sobre todas

**Lo que cuenta como "buen chart" no se inventa, se mide.** Los **392** charts
hechos a mano que hay hoy en el disco de Bruno son el criterio, no el gusto de
nadie. Todo cambio se justifica con un numero contra esa biblioteca, y esa cifra
cambia cuando el depura la suya: **un percentil de antes del 23-08 se midio
sobre otra poblacion.**

En la practica, cada tanda va asi:

1. **Medir primero, con el codigo sin tocar.** Ese numero es el control.
2. Cambiar una sola cosa.
3. Volver a medir. Si no mejora contra el corpus, **se revierte y se escribe el
   numero en `DECISIONES_MEDIDAS.md`** — un descarte medido vale tanto como un
   acierto, porque impide que el siguiente lo reintente.
4. Comprobar que no se rompio nada (seccion 3).

Y una regla de método que ya costo una tanda: **una sola cancion no decide
nada**. Si dos canciones discrepan, se prueba en mas o no se adopta. Los
parametros calibrados hoy (`CONTOUR_CUTS`, `CHORD_RUN_WINDOW`,
`CHORD_SHAPE_SHIFT`) salieron de dos canciones distintas a proposito: una
electronica y una de metal.

## 2. Las siete trampas de las herramientas de medida

Contadas largo en `docs/DECISIONES_MEDIDAS.md` §9. En corto, porque todas
llevan a trabajar en balde:

1. **El banco no ve los trastes.** El F1 compara *cuando* suena cada nota, no
   *cual*. El trabajo de patron se juzga con el panel y las distribuciones del
   corpus; el banco solo dice si rompiste la sincronia.
2. **El F1 premia pasarse de notas.** Sube hasta un 35 % por encima de la
   densidad humana. La densidad la decide el parecido con la distribucion.
3. **Una muestra sola miente.** La de 16 canciones esta sesgada a lo denso.
4. **Si el `nps_humano_medio` del banco no da 3.91, no comparas la misma
   muestra.** `pick_songs` coge una carpeta de cada N, asi que cualquier carpeta
   nueva en `Songs\` mueve las 24. **Ese numero es el testigo.**
5. **Una medida que no aplica la regla del juego no mide lo que crees.** La
   cifra de HOPO escrita durante semanas (34.2 %) era proximidad entre notas,
   sin las dos reglas que el juego si aplica; la real era la mitad (17.2 %). Por
   eso `is_natural_hopo` vive en `chartio.py` y la herramienta de medida llama a
   **la misma funcion** que el generador.

**6. Medir sobre la poblacion equivocada dice lo contrario de la verdad.** El
`ring` parecia una moneda al aire (AUC 0.586) para elegir que nota se sostiene.
Contaba TODAS las notas humanas, y el 90 % no puede sostenerse porque la
siguiente entra antes: en Pride & Joy son 13 sostenidas contra 860 picadas.
Entre las que **tienen sitio** (hueco >= 0.5 s) el mismo ring da **0.727** y
separa en 5 de 7 canciones. Antes de creerte un "esto no separa", mira sobre
que poblacion se calculo. Y el reverso: el HUECO daba 0.990 ahi, que no es un
hallazgo sino la mecanica -- un sostenido **ocupa** el hueco, no lo elige.
Mete siempre una regla tonta de control: en la densidad, "todas las canciones
igual" dio 0.960 contra el 0.926 del sistema real, y eso delato que el sistema
no sabe nada (correlacion +0.038 con el humano).

**7. Una regla no se juzga por su objetivo si el generador no lo entrega.** El
presupuesto de notas se gasta antes del recorte de "demasiado juntas", asi que
el chart sale entre un 5 % y un 13 % por debajo de lo pedido. Se probo una regla
de densidad que mejoraba el objetivo (error 0.926 -> 0.874) y empeoraba el chart
(distancia 0.384 -> 0.421). **Se mide el chart, no el objetivo.**

Y una trampa al medir sostenidos: solo cuenta como sostenido lo que dura **>=
`chartio.SOSTENIDO_MIN_TIEMPOS`, que son 0.5 tiempos**. A 0.25 se medía el
FORMATO y no la musica -- en un `.mid` toda nota tiene duracion y los rips
salian al 100 %. El umbral vive en `chartio` y lo leen el corpus, el atlas y el
generador: **no lo repitas en tu herramienta.**

## 3. Que hay que correr antes de dar algo por bueno

```bash
python tests/test_basico.py                          # 26 OK, sin audio
python tools/contra_el_humano.py --pride --generar   # la de aceptacion, ~3 min
python tools/revisar_in_game.py salida/<lote>        # [OK] en todas
python tools/verificar_puerta.py                     # la puerta, 1 s
```

Control de hoy (23-08-2026). **Estos son los numeros que no deben bajar:**

- **Pride & Joy**, la de aceptacion: 819 notas de las 982 del humano, F1
  **0.586**, distancia de gestos **0.066**, sostenidos 0.095.
- **Panel de 10** (`tools/panel_generos.py`, ~20 min): distancia **0.384**,
  F1 0.505, error de notas/s 1.033, error de sostenidos 0.035, y "todas
  iguales" **6.9 veces**.
- `tools/banco.py --muestra 24` sigue ahi y es lento (~7 min); ultimo valor
  22-08: f1_medio 0.663 con `nps_humano_medio 3.91`. **Solo ve la sincronia**:
  para trabajo de patron manda el panel.

**Los dos validadores no miran lo mismo y hacen falta los dos:**
`autochart revisar <chart>` dice si es **musicalmente** sano (densidad, acordes
y sostenidos dentro del rango humano); `tools/revisar_in_game.py <carpeta>` si
el **juego** puede cargarlo y jugarlo entero (audio, primera y ultima nota,
frases de Star Power vacias o solapadas). Ya han cazado fallos de verdad — el
ultimo, acordes de cinco notas. Si cantan algo, tienen razon.

## 4. Cosas del entorno que muerden

- **`OneDrive\Documents` YA acepta escrituras de consola** (21-08-2026).
  Durante meses fallaba con `"Could not find file"`, un error enganoso: si vuelve
  a fallar, ese es el sintoma y se copia desde el Explorador.
- **Aun asi, la biblioteca la toca UNA sola herramienta:**
  `tools/instalar_letras.py`, que guarda el original en `salida/respaldo_letras/`
  antes de pisarlo y trae `--probar` y `--deshacer`. Todo lo demas escribe en
  `salida/`.
- **Despues de cambiar un chart ya instalado hay que hacer SCAN SONGS** en el
  juego, o sigue sonando el de la cache.
- **La biblioteca no se toca a mano.** Instalado por AutoChart: 200 letras (con
  respaldo) y 15 charts, en `16_Brunich - AI Rogue` y `17_Pruebas AutoChart`.
- **La instalacion buena de Clone Hero es la del Escritorio** (`OneDrive\Desktop\
  Games\Clone Hero`, v1.1.0.6142), no la de AppData.
- **`contra_el_humano.py` NO regenera si la carpeta ya existe.** Sin `--generar`
  mides el chart viejo y concluyes que tu cambio "no hizo nada".
- **Un lote regenerado desde el `song.mp3` de `salida/` no es el mismo lote.**
  Una carpeta de la biblioteca trae la LETRA ALINEADA y un mp3 suelto no, y las
  silabas anclan la melodia: 897 notas contra 790 en la misma cancion. Vale como
  A/B contra si mismo, no contra los numeros historicos.

## 5. Como se cierra una tanda

En este orden, sin que Bruno lo pida:

1. `python tests/test_basico.py` → 26 OK.
2. `python tools/revisar_in_game.py salida` → [OK] en las tres.
3. **Commit archivo por archivo**, con el mensaje explicando *por que*, con los
   numeros. Los mensajes de este repo cuentan la medida, no el diff.
   Cuidado con las comillas invertidas en `git commit -m` desde bash: se las
   come el shell. Usa `git commit -F -` con un heredoc `<<'EOF'`.
4. `git push` y PR contra `main`.
5. **Reescribir el bloque §10 de `docs/SIGUIENTE_CHAT.md`** con la tarea
   siguiente. Es **uno solo**: el nuevo sustituye al viejo, no se anade debajo.
   Tiene que llevar las cuatro cosas o no sirve:
   - que se cambia y **donde** (fichero y funcion),
   - con que se mide y cual es el **objetivo en numero**,
   - cual es el **control** que no debe bajar,
   - **quien mas toca ese valor**, ya buscado con `grep`.
6. Lo que quede vivo del bloque viejo se mete en el nuevo o se muda a
   `DECISIONES_MEDIDAS.md`. No se archiva "por si acaso".

## 6. Que NO hacer

- No tocar la biblioteca de canciones de Bruno.
- No subir audio al repo: el `.gitignore` lo bloquea y esta bien asi.
- No "arreglar" a ojo algo que el corpus no respalde.
- No dar por bueno un cambio de patron porque el banco no baje: el banco no ve
  los trastes.
- No anadir un segundo bloque de tarea siguiente.

## 7. La bateria de la puerta de entrada

```bash
python tools/verificar_puerta.py
```

Falla si la puerta engorda (este fichero + `SIGUIENTE_CHAT.md`), si aparece un
segundo bloque de tarea, o si un enlace apunta a un `.md` que no existe.
Correrla al cerrar: una regla que depende de que alguien se acuerde no es una
regla.
