# Corpus de oro — a que chart humano hay que parecerse

*21-08-2026. Sale de una pregunta de Bruno: «que se tomen en consideracion los
mejores temas, como Impulse o los de Junior H, para hacer canciones y que den esa
calidad».*

## El problema que arregla

`atlas_patrones.json` mide las 396 canciones de la biblioteca y saca percentiles.
Todas pesan lo mismo. Ahi dentro conviven:

| | repeticion | vocabulario | contraste |
|---|---:|---:|---:|
| `An Endless Sporadic — Impulse` | 17 % | 0.48 | 7.74 |
| `Siddhartha — Unicos` | 81 % | 0.08 | 1.24 |

Apuntar a la mediana de esa mezcla es apuntar a la mediocridad. El generador no
tiene que parecerse al chart **medio**: tiene que parecerse a los **buenos**.

## Los cuatro filtros

Nada de esto es una nota inventada. Son cuatro cortes sobre cifras que ya calcula
`atlas.medir_pista`, y los umbrales salen de los percentiles de la propia
biblioteca (360 pistas de guitarra en Experto con >= 400 notas).

| Filtro | Falla si | Umbral | Caen |
|---|---|---|---:|
| **machacona** | `repeticion` > p75 | 43,3 % | 90 |
| **vacia** | `nps` < p25 | 3,13 notas/s | 90 |
| **poco vocabulario** | `cobertura` < p50 | 0,48 | 180 |
| **no respira** | `contraste` < p50 | 2,81 | 178 |

**Pasan los cuatro: 38 de 360 (11 %).** Estan en `datos/corpus_oro.json` con
`"oro": true`, y el reparto completo de las 360 en
[`CATALOGO_BIBLIOTECA.md`](CATALOGO_BIBLIOTECA.md).

```
python tools/elegir_oro.py        # produce datos/corpus_oro.json
python tools/catalogo_md.py       # produce docs/CATALOGO_BIBLIOTECA.md
```

Se mide con `atlas.escanear`, la misma funcion que alimenta el atlas. Con otra no
serian cifras comparables — es la trampa 5 de CLAUDE.md, la que ya costo la cifra
falsa de HOPO.

## Los tres hallazgos

### 1. El chart medio no es machacon: es plano

Lo que mas se cae no es la repeticion (90 pistas) sino el **vocabulario** (180) y el
**contraste** (178). La mitad de la biblioteca toca siempre los mismos cuatro gestos
con la misma intensidad de principio a fin.

Eso importa mucho aqui porque **es exactamente el fallo que un generador produce
solo**. El plan de patrones ya sospechaba de `thin`, que reparte la densidad por
ventana y por tanto aplana el contraste a proposito. Este reparto lo confirma desde
el otro lado: si la referencia son las 396, la mediana de contraste ya viene
contaminada por 178 charts planos. Contra el oro, la vara sube.

### 2. Los corridos tumbados son vocabulario alto y contraste cero

Bruno pidio expresamente que se tuvieran en cuenta los de Junior H. Miden asi:

| | notas | nps | repeticion | vocabulario | contraste | |
|---|---:|---:|---:|---:|---:|---|
| Dias Nublados | 919 | 4,25 | 24,5 % | 0,52 | **2,92** | **oro** |
| ENTRE NOSOTROS | 885 | 5,48 | **8,5 %** | **0,98** | 1,40 | no respira |
| Y LLORO | 710 | 4,06 | 19,0 % | 0,65 | 1,38 | no respira |
| ROCKSTAR | 698 | 4,30 | 3,9 % | 0,57 | 1,43 | no respira |
| Jueves 10 | 964 | 3,43 | 15,4 % | 0,65 | 1,53 | no respira |
| Extssy Model | 905 | 3,85 | 26,3 % | 0,60 | 1,69 | no respira |
| Ella | 989 | 3,90 | 22,0 % | 0,59 | 2,23 | no respira |
| Natanael Cano — Madrid | 717 | 3,64 | 3,1 % | 0,63 | 1,32 | no respira |

`ENTRE NOSOTROS` tiene **cobertura 0,98** — usa practicamente todos los gestos del
atlas — y solo **8,5 % de repeticion**. Como construccion de patrones es de lo mejor
de la biblioteca. Y aun asi cae, porque su contraste es 1,40 contra el 2,81 mediano:
el punteo del corrido no para nunca, no hay estrofa floja ni subida.

**Lo que esto significa para el generador:** el contraste no puede ser un objetivo
global. Un corrido tumbado bien charteado *es* plano y esta bien que lo sea. Si el
validador exige 2,81 de contraste a todo, va a marcar como malo un corrido correcto.
El objetivo de contraste tiene que salir de `por_genero`, no de `global`.

Y al reves: para **aprender vocabulario**, los de Junior H son de lo mejor que hay
aqui. Conviene separar las dos cosas — de quien se aprende *que* tocar no tiene que
ser de quien se aprende *cuando aflojar*.

### 3. La medida no sabe si una cancion es divertida

Hay charts queridisimos que suspenden:

| | veredicto | por que |
|---|---|---|
| `Buckethead — Jordan` | poco vocabulario, no respira | 7,9 notas/s constantes; es un muro, y ese es el chiste |
| `Dick Dale — Misirlou` | machacona, poco vocabulario, no respira | surf a 7,9 n/s: machacar el traste *es* el tema |
| `The Fall of Troy — F.C.P.R.E.M.I.X.` | poco vocabulario | famoso justo por lo dificil, no por lo variado |

Los filtros encuentran charts **planos**, no charts **aburridos**. Para elegir la
referencia del generador sirven; para decidir que borrar de la biblioteca solo son
una pista. Un tema que machaca a proposito no esta mal charteado.

## Las dos varas, medidas

```
python tools/minar_atlas.py --salida datos/atlas_patrones.json
python tools/minar_atlas.py --solo-oro datos/corpus_oro.json --salida datos/atlas_oro.json
```

`--solo-oro` filtra los rasgos por `(pack, cancion)` antes de agregar. Sobre las
pistas de guitarra, 393 contra 38:

| p50 de… | todas | oro | cambio |
|---|---:|---:|---:|
| contraste | 2,84 | **3,96** | **+39 %** |
| ligadas (HOPO) | 0,144 | **0,249** | **+74 %** |
| repite traste | 0,269 | 0,170 | −37 % |
| acordes | 0,364 | 0,203 | −44 % |
| vocabulario | 0,481 | 0,536 | +12 % |
| notas por segundo | 3,75 | 4,23 | +13 % |
| sostenidos | 0,141 | 0,101 | −28 % |
| fuera de pulso | 0,342 | 0,307 | −10 % |

**El objetivo actual esta calibrado contra charts planos.** El contraste sube un
39 % al quitar de la referencia lo que no vale. Un generador que aterrice en 2,84
esta dando en la mediana de una biblioteca cuya mitad no respira, y ninguna medida
del proyecto lo estaba viendo.

Dos cifras mas que no se esperaban:

- **Ligadas +74 %.** Los charts buenos ligan mucho mas. Es la diferencia entre una
  frase de guitarra y una lista de golpes, y hoy no es objetivo de nada.
- **Acordes −44 %.** El chart medio se apoya en acordes; los buenos tocan lineas de
  nota suelta. Al reves de lo que sugiere la mediana global.

## Sobre el gusto de Bruno

Dijo (21-08-2026) que de las que sobrevivieron a la limpieza hay unas cuantas que no
le gustan tanto, y nombro **las de Metallica**. Comprobado contra el corpus: de sus
**26 pistas de Metallica, solo 1 entra en el oro**. Los cuatro filtros ya las dejaban
fuera por su cuenta, asi que no hay que corregir nada — el thrash de ocho minutos es
denso y plano a la vez, justo lo que el corte de contraste castiga.

Ningun artista domina el oro: el mas repetido es Ozzy Osbourne con 2 de 38. Por
genero queda rock 47 %, metal 39 %, el resto 14 %.

## Lo que falta

- Objetivo de contraste **por genero**, no global (hallazgo 2). El corrido tumbado
  bien charteado es plano y esta bien que lo sea.
- Meter `ligadas` como objetivo del generador: +74 % es la separacion mas grande
  entre lo bueno y lo medio, y hoy no se persigue.
- Decidir si el generador aprende vocabulario y dinamica de corpus distintos: para
  *que* tocar, los corridos son de lo mejor; para *cuando aflojar*, no sirven.
