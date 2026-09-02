"""Que gesto pone un charter DESPUES de cual.

El atlas ya sabe que gestos usa cada genero -- 16 tipos medidos sobre cientos de
pistas -- pero solo cuenta cuantas veces sale cada uno. El orden en que
aparecen se tiraba. Y el orden es justo lo que separa un chart escrito de uno
sorteado: nadie pone una rafaga de semicorcheas justo despues de un sostenido
largo sin avisar, y cuando pasa, jugando se siente como un tropiezo.

Esto lo mina: para cada pista saca los gestos en orden y cuenta los pares
seguidos. Sale una matriz por genero e instrumento.

Ademas mide lo que de verdad interesa para el generador: **cuanto de lo que
viene se puede predecir**. Si despues de un tremolo el humano pone casi siempre
lo mismo, esa transicion es una regla; si reparte entre ocho gestos distintos,
no la hay. La sorpresa (entropia) de cada gesto dice cuales son reglas.

    python tools/transiciones.py
    python tools/transiciones.py --genero metal
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from autochart import atlas  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"

# Dos gestos separados por mas de esto no son una transicion: hay una pausa por
# medio y la mano ya empezo otra cosa. No es un numero puesto a ojo -- es el
# hueco a partir del cual el propio atlas cuenta un "respiro" (cuatro tiempos).
SEPARACION_MAXIMA_NOTAS = 8


def pares_de(secuencia: list) -> list[tuple[str, str]]:
    """Los gestos seguidos, saltandose los solapes.

    Un mismo tramo puede ser rafaga y escalera a la vez: eso no es una
    transicion, es la misma mano descrita dos veces. Solo cuenta como par lo que
    EMPIEZA despues de que lo anterior termine.
    """
    pares = []
    ultimo = None
    for desde, hasta, tipo in secuencia:
        if ultimo is not None:
            fin_anterior, tipo_anterior = ultimo
            if 0 <= desde - fin_anterior <= SEPARACION_MAXIMA_NOTAS:
                pares.append((tipo_anterior, tipo))
        if ultimo is None or hasta > ultimo[0]:
            ultimo = (hasta, tipo)
    return pares


def entropia(cuenta: Counter) -> float:
    """Cuanta sorpresa hay en lo que viene despues, en bits."""
    total = sum(cuenta.values())
    if total <= 0:
        return 0.0
    return -sum((v / total) * math.log2(v / total) for v in cuenta.values() if v)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--biblioteca", default=str(BIBLIOTECA))
    parser.add_argument("--instrumento", default="guitarra")
    parser.add_argument("--genero", default="")
    parser.add_argument("--salida", default="datos/transiciones.json")
    parser.add_argument("--minimo", type=int, default=30,
                        help="pares minimos para fiarse de una fila")
    parser.add_argument("--comparar", default="",
                        help="otro transiciones.json contra el que medir la persistencia")
    args = parser.parse_args(argv)

    hechas = [0]

    def progreso(*_a, **_k):
        hechas[0] += 1
        if hechas[0] % 60 == 0:
            print(f"   ... {hechas[0]} carpetas", flush=True)

    rasgos = atlas.escanear(args.biblioteca, ("Expert",), al_progresar=progreso)

    matrices: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    pistas = Counter()
    for r in rasgos:
        if r.instrumento != args.instrumento:
            continue
        if args.genero and r.genero != args.genero:
            continue
        pares = pares_de(r.secuencia_licks)
        if not pares:
            continue
        pistas[r.genero] += 1
        pistas["TODO"] += 1
        for antes, despues in pares:
            matrices["TODO"][antes][despues] += 1
            matrices[r.genero][antes][despues] += 1

    if not matrices:
        print("[X] Ni un gesto encadenado. Sin resultado.")
        return 2

    volcado = {
        "instrumento": args.instrumento,
        "pistas_por_genero": dict(pistas),
        "separacion_maxima_notas": SEPARACION_MAXIMA_NOTAS,
        "matrices": {g: {a: dict(c) for a, c in m.items()} for g, m in matrices.items()},
    }
    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.salida).write_text(json.dumps(volcado, ensure_ascii=False, indent=1),
                                 encoding="utf-8")

    global_ = matrices["TODO"]
    total_pares = sum(sum(c.values()) for c in global_.values())
    print()
    print(f"{pistas['TODO']} pistas de {args.instrumento}, {total_pares} transiciones")
    print()
    print(f"{'despues de...':20} {'pares':>6} {'sorpresa':>9}  lo que viene, y cuanto manda")
    filas = sorted(global_.items(), key=lambda kv: -sum(kv[1].values()))
    for antes, cuenta in filas:
        n = sum(cuenta.values())
        if n < args.minimo:
            continue
        top = cuenta.most_common(3)
        detalle = "  ".join(f"{t} {v/n:.0%}" for t, v in top)
        print(f"{antes:20} {n:>6} {entropia(cuenta):>8.2f}b  {detalle}")

    if args.comparar:
        otro = json.loads(Path(args.comparar).read_text(encoding="utf-8"))
        base = otro["matrices"]["TODO"]
        print()
        print("PERSISTENCIA: cuantas veces un gesto va seguido de si mismo.")
        print("Es la firma de un chart escrito: el humano agota una figura antes")
        print("de cambiar, y un generador sin memoria la abandona en cuanto puede.")
        print()
        print(f"{'gesto':20} {'referencia':>11} {'esto':>8} {'pares':>7}")
        def persistencia(matriz, gesto):
            fila = matriz.get(gesto) or {}
            total = sum(fila.values())
            return (fila.get(gesto, 0) / total if total else 0.0), total
        for gesto in sorted(base, key=lambda g: -sum(base[g].values())):
            ref, n_ref = persistencia(base, gesto)
            mio, n_mio = persistencia({g: dict(c) for g, c in global_.items()}, gesto)
            if n_ref < args.minimo or n_mio < 10:
                continue
            aviso = "  <-- lo abandona" if ref - mio > 0.15 else ""
            print(f"{gesto:20} {ref:>10.0%} {mio:>7.0%} {n_mio:>7}{aviso}")

    print()
    print("Sorpresa baja = el humano casi siempre pone lo mismo despues: eso es una")
    print("regla y el generador puede seguirla. Sorpresa alta = no hay regla ahi.")
    print(f"\nMatrices por genero en {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
