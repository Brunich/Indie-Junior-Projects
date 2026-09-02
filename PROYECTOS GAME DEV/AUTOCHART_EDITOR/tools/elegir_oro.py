"""Elige el corpus de oro: que charts humanos merecen ser la vara del generador.

El atlas mide las 396 canciones y saca percentiles de TODAS por igual. El problema
es que ahi dentro conviven `Impulse` (An Endless Sporadic) y `Nena` de Miguel Bose,
que repite el mismo traste en el 86 % de los golpes. Apuntar a la mediana de esa
mezcla es apuntar a la mediocridad.

Esto separa el subconjunto que si vale como referencia. No inventa una nota de
calidad: aplica cuatro filtros sobre las cifras que ya calcula `atlas.medir_pista`,
y los umbrales salen de los percentiles de la propia biblioteca.

    python tools/elegir_oro.py
    python tools/elegir_oro.py --ver 40
    python tools/elegir_oro.py --salida datos/corpus_oro.json

Se mide con `atlas.escanear`, la MISMA funcion que alimenta el atlas. Si se midiera
con otra cosa, las cifras no serian comparables -- es la trampa 5 de CLAUDE.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autochart import atlas  # noqa: E402

BIBLIOTECA = Path(r"C:\Users\bruni\OneDrive\Documents\Clone Hero\Songs")
MIN_NOTAS = 400


def percentil(valores: list[float], p: float) -> float:
    if not valores:
        return 0.0
    orden = sorted(valores)
    i = (len(orden) - 1) * p / 100.0
    bajo, alto = int(i), min(int(i) + 1, len(orden) - 1)
    return orden[bajo] + (orden[alto] - orden[bajo]) * (i - bajo)


def rango_percentil(valor: float, orden: list[float]) -> float:
    """En que percentil cae `valor` dentro de `orden` (lista ya ordenada)."""
    if not orden:
        return 0.0
    bajo = 0
    alto = len(orden)
    while bajo < alto:
        medio = (bajo + alto) // 2
        if orden[medio] < valor:
            bajo = medio + 1
        else:
            alto = medio
    return bajo / len(orden)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--biblioteca", default=str(BIBLIOTECA))
    ap.add_argument("--salida", default="datos/corpus_oro.json")
    ap.add_argument("--ver", type=int, default=25, help="cuantas imprimir")
    args = ap.parse_args()

    hechas = [0]

    def progreso(*_):
        hechas[0] += 1
        if hechas[0] % 50 == 0:
            print(f"  ... {hechas[0]}", file=sys.stderr)

    print("Midiendo la biblioteca con atlas.escanear ...", file=sys.stderr)
    rasgos = atlas.escanear(args.biblioteca, ("Expert",), al_progresar=progreso)

    gtr = [r for r in rasgos if r.instrumento == "guitarra" and r.notas >= MIN_NOTAS]
    print(f"pistas de guitarra con >= {MIN_NOTAS} notas: {len(gtr)} de {len(rasgos)}",
          file=sys.stderr)

    reps = [r.repeticion for r in gtr]
    npss = [r.nps for r in gtr]
    cobs = [r.cobertura for r in gtr]
    cons = [r.contraste for r in gtr]
    vars_ = [r.variacion for r in gtr]

    umbrales = {
        "repeticion_p75": percentil(reps, 75),
        "nps_p25": percentil(npss, 25),
        "cobertura_p50": percentil(cobs, 50),
        "variacion_p25": percentil(vars_, 25),
        # 1 tramo flojo de 12. No es un numero elegido: el 87 % de los charts
        # humanos no tiene NINGUNO y el 95 % tiene como mucho uno. Pasado ahi
        # ya no es un puente tranquilo, es un agujero.
        "muertos_maximo": 1 / 12,
        "min_notas": MIN_NOTAS,
    }

    cobs_orden = sorted(cobs)
    vars_orden = sorted(vars_)

    filas = []
    for r in gtr:
        motivos = []
        if r.repeticion > umbrales["repeticion_p75"]:
            motivos.append("machacona")
        if r.nps < umbrales["nps_p25"]:
            motivos.append("vacia")
        if r.cobertura < umbrales["cobertura_p50"]:
            motivos.append("poco vocabulario")
        # El filtro que habia aqui era `contraste < p50 -> "no respira"`, y era
        # un artefacto de la medida: el contraste es max/min de doce tramos y el
        # minimo va en el divisor, asi que una zona casi vacia dispara la nota.
        # Medido sobre 392 pistas, correlacion +0.60 con tramos casi muertos, y
        # 8 de las 37 del oro anterior habian entrado teniendo agujeros.
        # Lo sustituyen dos cosas que miden por separado lo que aquel mezclaba:
        if r.tramos_muertos > umbrales["muertos_maximo"] + 1e-9:
            motivos.append("zonas muertas")
        if r.variacion < umbrales["variacion_p25"]:
            motivos.append("plana")
        # expresividad: donde cae en cobertura de gestos y en dinamica de densidad
        expr = (rango_percentil(r.cobertura, cobs_orden)
                + rango_percentil(r.variacion, vars_orden)) / 2
        filas.append({
            "cancion": r.cancion,
            "artista": r.artista,
            "pack": r.pack,
            "genero": r.genero,
            "fuente": r.fuente,
            "notas": r.notas,
            "duracion_s": round(r.duracion_s, 1),
            "bpm": round(r.bpm, 1),
            "nps": round(r.nps, 2),
            "repeticion": round(r.repeticion, 4),
            "acordes": round(r.acordes, 4),
            "sostenidos": round(r.sostenidos, 4),
            "sincopa": round(r.sincopa, 4),
            "cobertura": round(r.cobertura, 4),
            "contraste": round(r.contraste, 4),
            "variacion": round(r.variacion, 4),
            "tramos_muertos": round(r.tramos_muertos, 4),
            "expresividad": round(expr, 4),
            "oro": not motivos,
            "descartada_por": motivos,
        })

    filas.sort(key=lambda f: -f["expresividad"])
    oro = [f for f in filas if f["oro"]]

    salida = {
        "generado_por": "tools/elegir_oro.py",
        "biblioteca": str(args.biblioteca),
        "medido_con": "atlas.escanear (la misma que alimenta atlas_patrones.json)",
        "pistas_guitarra_evaluadas": len(gtr),
        "umbrales": {k: round(v, 4) for k, v in umbrales.items()},
        "criterio": (
            "Una pista entra en el oro si NO es machacona (repeticion <= p75), "
            "NO esta vacia (nps >= p25), usa al menos el vocabulario mediano "
            "(cobertura >= p50), NO tiene agujeros (como mucho 1 tramo flojo de 12) "
            "y tiene dinamica de verdad (variacion >= p25). Los umbrales "
            "salen de la propia biblioteca, no de una opinion."
        ),
        "oro": len(oro),
        "canciones": filas,
    }

    destino = Path(args.salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")

    print()
    print(f"ORO: {len(oro)} de {len(gtr)} pistas de guitarra "
          f"({100 * len(oro) / max(len(gtr), 1):.0f} %)")
    print(f"umbrales: repeticion<={umbrales['repeticion_p75']:.3f}  "
          f"nps>={umbrales['nps_p25']:.2f}  "
          f"cobertura>={umbrales['cobertura_p50']:.3f}  "
          f"variacion>={umbrales['variacion_p25']:.3f} "
          f"muertos<=1/12")
    print()
    cab = f"{'CANCION':<34} {'ARTISTA':<22} {'notas':>6} {'nps':>5} {'rep':>6} {'cob':>5} {'con':>6}"
    print(cab)
    print("-" * len(cab))
    for f in oro[:args.ver]:
        print(f"{f['cancion'][:34]:<34} {f['artista'][:22]:<22} {f['notas']:>6} "
              f"{f['nps']:>5.2f} {f['repeticion']:>6.1%} {f['cobertura']:>5.2f} "
              f"{f['variacion']:>6.3f}")
    print()
    print(f"escrito: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
