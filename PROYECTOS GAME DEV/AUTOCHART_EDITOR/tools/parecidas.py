"""Se parecen los charts generados entre si mas que los humanos entre si?

Bruno, 22-08-2026: *"siento que estoy tocando las mismas canciones que antes"*.
Eso no es una impresion, es una medida: si dos charts distintos usan la misma
mezcla de gestos, jugarlos se siente igual por muy distintas que sean las
canciones.

Cada pista se convierte en su **vector de gestos** -- cuantas veces sale cada
uno de los 16 tipos del atlas por cada 100 notas -- y se mide la distancia
coseno entre todas las parejas. Un lote variado tiene distancia alta; un lote
que es el mismo chart con otro audio detras la tiene cerca de cero.

    python tools/parecidas.py salida/<lote>
    python tools/parecidas.py salida/<lote> --contra "<carpeta de charts humanos>"

Control medido el 22-08-2026:

    15 charts generados (AI Rogue + Pruebas)  distancia media 0.071
    16 charts humanos   (Memes + Latin)       distancia media 0.556

O sea que **los generados se parecen entre si 7.8 veces mas que los humanos**.
Ese es el numero que tiene que moverse para que la reestructuracion valga: el
objetivo esta escrito en `docs/PLAN_TOCAR_LA_CANCION.md`.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autochart import atlas  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
MINIMO_NOTAS = 100


def vectores(carpeta, instrumento="guitarra", limite=None):
    """Un vector de gestos por 100 notas para cada pista de `carpeta`."""
    salida = []
    for r in atlas.escanear(carpeta, ("Expert",)):
        if r.instrumento != instrumento or r.notas < MINIMO_NOTAS:
            continue
        v = np.array([r.licks.get(t, 0) for t in atlas.TIPOS_LICK], dtype=float)
        salida.append(v / max(1.0, r.notas) * 100.0)
        if limite and len(salida) >= limite:
            break
    return salida


def dispersion(vs) -> np.ndarray:
    """Distancia coseno de todas las parejas. Alta = lote variado."""
    d = []
    for a, b in itertools.combinations(vs, 2):
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na and nb:
            d.append(1.0 - float(a @ b) / (na * nb))
    return np.array(d)


def informe(nombre: str, vs) -> np.ndarray | None:
    if len(vs) < 2:
        print(f"[X] {nombre}: hacen falta 2 charts al menos, hay {len(vs)}")
        return None
    d = dispersion(vs)
    print(f"    {nombre:34} {len(vs):3d} charts  distancia media {d.mean():.3f}"
          f"  (mediana {np.median(d):.3f})")
    return d


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("carpeta", help="Lote de charts generados")
    parser.add_argument("--contra", default="",
                        help="Carpeta de charts humanos; sin esto usa dos packs de customs")
    parser.add_argument("--instrumento", default="guitarra")
    args = parser.parse_args(argv)

    print("[*] Cuanto se parecen los charts de un lote entre si")
    gen = informe("generados", vectores(args.carpeta, args.instrumento))
    if gen is None:
        return 2

    if args.contra:
        hum = informe("humanos", vectores(args.contra, args.instrumento))
    else:
        vs = (vectores(BIBLIOTECA / "13_Customs - Memes & Humor", args.instrumento)
              + vectores(BIBLIOTECA / "10_Customs - Latin & Mexican", args.instrumento, 12))
        hum = informe("humanos (Memes + Latin)", vs)
    if hum is None:
        return 2

    veces = hum.mean() / max(gen.mean(), 1e-9)
    print()
    print(f"    Los generados se parecen entre si {veces:.1f} veces mas que los humanos.")
    print("    Por debajo de 1.5 el lote es tan variado como uno humano; por encima")
    print("    de 3 es el mismo chart con otro audio detras.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
