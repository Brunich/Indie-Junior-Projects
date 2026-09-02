"""El "contraste" con el que se elige el corpus de oro, puesto a prueba.

Hoy `atlas.medir_pista` lo calcula asi:

    contraste = max(curva) / min(los tramos vivos)      (curva = 12 tramos)

Dos cosas de esa formula que no se han mirado nunca y deciden que entra en el
oro, o sea que deciden a que se parece todo lo que genera AutoChart:

1. Es un cociente entre **dos puntos sueltos** de doce. El maximo y el minimo
   son los dos estadisticos mas fragiles que existen: un solo tramo raro mueve
   el resultado entero.
2. **Los tramos con densidad cero se excluyen del divisor** (`vivos`). Un chart
   con una zona muerta no baja de nota: sube, porque el tramo casi-vacio que
   queda al lado hace de divisor pequeno.

La sospecha, que es lo que esto mide: el filtro premia tener zonas vacias --
justo el defecto del que se queja Bruno jugando ("hay zonas en las que ni
siquiera se toca nada") -- y castiga las canciones constantes, que son las que
el elige jugar (Cliffs of Dover sale 1.59 y se cae por "no respira").

    python tools/revisar_contraste.py
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from autochart import atlas  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"


def percentil(valores: list[float], p: float) -> float:
    if not valores:
        return 0.0
    orden = sorted(valores)
    i = min(len(orden) - 1, max(0, int(round(p / 100 * (len(orden) - 1)))))
    return orden[i]


def medidas(curva: list[float]) -> dict:
    """Varias formas de decir 'cuanto respira', sobre la misma curva."""
    vivos = [c for c in curva if c > 0]
    if not vivos:
        return {}
    media = st.mean(curva)
    mediana = st.median(vivos)
    return {
        # la de hoy
        "actual": round(max(curva) / max(0.1, min(vivos)), 2),
        # la misma idea pero sin apoyarse en dos puntos sueltos
        "p90_p25": round(percentil(curva, 90) / max(0.1, percentil(curva, 25)), 2),
        # dispersion relativa: no es un cociente de extremos
        "variacion": round(st.pstdev(curva) / max(0.01, media), 3),
        # y lo que de verdad molesta jugando: cuanto de la cancion esta muerto
        "tramos_muertos": round(sum(1 for c in curva if c < 0.25 * mediana) / len(curva), 3),
        "tramos_cero": round(sum(1 for c in curva if c <= 0) / len(curva), 3),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--biblioteca", default=str(BIBLIOTECA))
    parser.add_argument("--salida", default="salida/revision_contraste.json")
    args = parser.parse_args(argv)

    hechas = [0]

    def progreso(*_a, **_k):
        hechas[0] += 1
        if hechas[0] % 40 == 0:
            print(f"   ... {hechas[0]}", flush=True)

    rasgos = atlas.escanear(args.biblioteca, ("Expert",), al_progresar=progreso)
    filas = []
    for r in rasgos:
        if getattr(r, "instrumento", "") != "guitarra":
            continue
        curva = list(getattr(r, "curva", []) or [])
        if len(curva) < 12:
            continue
        m = medidas(curva)
        if not m:
            continue
        m.update(cancion=getattr(r, "cancion", ""), artista=getattr(r, "artista", ""),
                 pack=getattr(r, "pack", ""), curva=curva)
        filas.append(m)

    if not filas:
        print("[X] Ninguna pista de guitarra medida.")
        return 2

    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.salida).write_text(json.dumps(filas, ensure_ascii=False, indent=1),
                                 encoding="utf-8")

    actual = [f["actual"] for f in filas]
    muertos = [f["tramos_muertos"] for f in filas]
    ceros = [f["tramos_cero"] for f in filas]

    def correlacion(a, b):
        ma, mb = st.mean(a), st.mean(b)
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
        return num / den if den else 0.0

    print()
    print(f"{len(filas)} pistas de guitarra en Experto")
    print()
    print("LA PREGUNTA: el contraste premia tener zonas muertas?")
    print(f"   correlacion contraste  <->  tramos casi muertos : {correlacion(actual, muertos):+.2f}")
    print(f"   correlacion contraste  <->  tramos a cero       : {correlacion(actual, ceros):+.2f}")
    print()
    print("Y cuanto se mueve el ranking si la medida no depende de dos puntos sueltos:")
    orden_hoy = {f["cancion"]: i for i, f in enumerate(sorted(filas, key=lambda f: -f["actual"]))}
    orden_rob = {f["cancion"]: i for i, f in enumerate(sorted(filas, key=lambda f: -f["p90_p25"]))}
    saltos = [abs(orden_hoy[c] - orden_rob[c]) for c in orden_hoy]
    print(f"   salto mediano de puesto: {st.median(saltos):.0f} de {len(filas)}")
    print(f"   canciones que se mueven mas de 50 puestos: "
          f"{sum(1 for s in saltos if s > 50)} ({sum(1 for s in saltos if s > 50)/len(saltos):.0%})")
    print()
    print(f"{'':46} {'hoy':>7} {'p90/p25':>8} {'variac':>7} {'muertos':>8}")
    for buscar in ("Cliffs of Dover", "Them Bones", "Impulse", "Corazon De Ni"):
        for f in filas:
            if buscar.lower() in f["cancion"].lower():
                print(f"{(f['artista'][:22] + ' - ' + f['cancion'][:22])[:46]:46} "
                      f"{f['actual']:>7.2f} {f['p90_p25']:>8.2f} {f['variacion']:>7.3f} "
                      f"{f['tramos_muertos']:>8.0%}")
    print()
    print(f"{'mediana de las ' + str(len(filas)):46} "
          f"{st.median(actual):>7.2f} {st.median([f['p90_p25'] for f in filas]):>8.2f} "
          f"{st.median([f['variacion'] for f in filas]):>7.3f} {st.median(muertos):>8.0%}")
    print(f"\nDetalle en {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
