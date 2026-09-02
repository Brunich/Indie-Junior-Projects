"""Cuantos arranques hay que ofrecerle al emparejador por cada silaba.

La pregunta sale de una medida, no de una intuicion: con el stem de voz el
alineado baja a 117 ms de mediana, pero desglosado por longitud de linea las de
6-8 silabas van a 55 ms y las de 12-14 a 162 ms. La diferencia entre esas dos
no es la longitud en si -- es cuantos candidatos tiene el emparejador por cada
silaba que colocar. Con 40 arranques para 8 silabas hay 76 millones de repartos
posibles y el coste no distingue el bueno.

Esto prueba de una sola pasada varios topes: quedarse con los K mas fuertes por
silaba y tirar el resto. K sale de aqui, no de que parezca razonable.

    python tools/experimento_candidatos.py --cuantas 10
"""

from __future__ import annotations

import argparse
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from autochart import alinear, letras, voz  # noqa: E402
from tools.banco_alineado import BIBLIOTECA, es_humana, mezcla_de  # noqa: E402

TOPES = [1.0, 1.5, 2.0, 3.0, 5.0, 0.0]  # 0 = sin tope, que es lo de hoy


def podar(picos, fuerzas, cuantas, tope):
    """Deja los `tope * cuantas` arranques mas fuertes, en orden de tiempo."""
    if tope <= 0 or not picos:
        return picos, fuerzas
    limite = max(cuantas, int(round(tope * cuantas)))
    if len(picos) <= limite:
        return picos, fuerzas
    mejores = sorted(range(len(picos)), key=lambda i: -fuerzas[i])[:limite]
    mejores.sort()
    return [picos[i] for i in mejores], [fuerzas[i] for i in mejores]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--cuantas", type=int, default=10)
    args = parser.parse_args(argv)

    carpetas = sorted({p.parent for patron in ("**/notes.mid", "**/notes.chart")
                       for p in Path(BIBLIOTECA).glob(patron)})
    errores = {t: [] for t in TOPES}
    a_ojo_todos = []
    ratios = []
    hechas = 0

    for carpeta in carpetas:
        if hechas >= args.cuantas:
            break
        if not es_humana(carpeta):
            continue
        try:
            pista = voz.leer_voz(carpeta)
        except Exception:
            continue
        if pista is None or len(pista.silabas) < 80:
            continue
        audio = mezcla_de(carpeta)
        if audio is None:
            continue
        arranques = alinear.arranques_de_voz(audio)
        if arranques is None:
            continue
        hechas += 1

        for frase in pista.frases:
            if len(frase.silabas) < 3:
                continue
            reales = [pista.tick_to_seconds(s.tick) for s in frase.silabas]
            inicio, fin = reales[0], reales[-1]
            if fin - inicio < 0.3:
                continue
            textos = [s.palabra or "la" for s in frase.silabas]
            pesos = letras._reparto(textos)
            picos, fuerzas = arranques.entre(inicio - 0.25, fin + 0.25)
            n = len(reales)
            if picos:
                ratios.append(len(picos) / n)
            a_ojo = alinear._reparto_plano(inicio, fin, n, pesos)
            a_ojo_todos += [abs(a - b) for a, b in zip(reales, a_ojo)]
            for tope in TOPES:
                p2, f2 = podar(picos, fuerzas, n, tope)
                puesto = alinear.emparejar(inicio, fin, n, p2, f2, pesos)
                errores[tope] += [abs(a - b) for a, b in zip(reales, puesto)]

    if not a_ojo_todos:
        print("[X] Sin datos.")
        return 2
    print()
    print(f"{hechas} canciones, {len(a_ojo_todos)} silabas")
    print(f"candidatos por silaba hoy: mediana {st.median(ratios):.1f}, "
          f"maximo {max(ratios):.0f}")
    print()
    print(f"{'tope':>16} {'mediana':>9} {'p75':>9} {'p95':>9}")
    print(f"{'reparto a ojo':>16} {st.median(a_ojo_todos)*1000:>8.0f}ms")
    for tope in TOPES:
        v = sorted(errores[tope])
        nombre = "sin tope (hoy)" if tope <= 0 else f"{tope:g} x silabas"
        print(f"{nombre:>16} {st.median(v)*1000:>8.0f}ms "
              f"{v[int(len(v)*0.75)]*1000:>8.0f}ms {v[int(len(v)*0.95)]*1000:>8.0f}ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
