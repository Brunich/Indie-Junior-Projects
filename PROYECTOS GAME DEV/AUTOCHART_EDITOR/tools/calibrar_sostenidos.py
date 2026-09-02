"""Cuantos sostenidos escribe cada regla, contra los que escribio el humano.

El generador llevaba desde siempre poniendo el MISMO ratio de sostenidos a
todas las canciones (0.15), porque el objetivo del perfil era una cuota: se
cogian las N notas de hueco mas ancho hasta llenarla. Los humanos van de 0.00
(Blur - Song 2) a 0.76 (Dethklok - Thunderhorse), asi que la cuota es la causa
directa de que todos los charts se sientan iguales por ese lado.

Esta herramienta barre las dos reglas que deciden quien se queda un sostenido
-- cuanto del hueco tiene que cubrir el sonido de la nota (`SUSTAIN_RELLENO`) y
cuanto tiene que durar para que se vea (`SUSTAIN_MIN_LENGTH_BEATS`) -- mas el
tope del perfil, y las juzga contra el ratio del charter humano de la MISMA
cancion. El audio se analiza una sola vez por cancion y despues se generan
todas las combinaciones, que es lo que hace el barrido barato.

Lo que decide no es solo el error medio: una regla que le pone 0.10 a todo
acierta de media y sigue sin distinguir una cancion de otra. Por eso se mira
tambien la CORRELACION con el humano, que es lo que dice si la regla oye la
cancion.

    python tools/calibrar_sostenidos.py --humanos 12
"""

from __future__ import annotations

import argparse
import json
import sys
import zlib
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))

from autochart import audio, generate  # noqa: E402
from autochart.corpus import load_profile  # noqa: E402
from mide_el_ring import BIBLIOTECA, PRIDE, SOSTENIDO_MIN_TIEMPOS, notas_humanas  # noqa: E402
from sigue_la_melodia import _con_guitarra_aislada  # noqa: E402

PERFIL = RAIZ / "datos" / "perfil_oro.json"

RELLENOS = (0.0,)
LARGOS = (0.5, 0.75, 1.0, 1.25)
TOPES = ("p50", "p75", "p95")


def ratio_humano(carpeta: Path) -> float | None:
    notas = notas_humanas(carpeta)
    if not notas:
        return None
    sostenes = np.array([s for _, s in notas], dtype=float)
    return float((sostenes >= SOSTENIDO_MIN_TIEMPOS).mean())


def perfil_con_tope(perfil: dict, punto: str) -> dict:
    """El mismo perfil con el tope de sostenidos movido a otro percentil."""
    copia = dict(perfil)
    bloque = dict(perfil.get("sustain_ratio") or {})
    if punto != "p50" and bloque.get(punto):
        bloque = dict(bloque, p50=bloque[punto])
    copia["sustain_ratio"] = bloque
    return copia


def medir_cancion(carpeta: Path, perfil: dict) -> dict | None:
    ruta = carpeta / "guitar.ogg"
    if not ruta.is_file():
        return None
    humano = ratio_humano(carpeta)
    if humano is None:
        return None
    analisis = audio.analyse(str(ruta), beat_audio_path=audio.pick_beat_audio(carpeta))
    semilla = zlib.crc32(carpeta.name.encode("utf-8")) % 100000
    fila = {"cancion": carpeta.name, "humano": round(humano, 4), "combos": {}}

    largo_original = generate.SUSTAIN_MIN_LENGTH_BEATS
    try:
        for relleno in RELLENOS:
            for largo in LARGOS:
                for tope in TOPES:
                    generate.SUSTAIN_MIN_LENGTH_BEATS = largo
                    generate.SOSTENIDOS.clear()
                    generate.generate_chart(
                        analisis, profile=perfil_con_tope(perfil, tope),
                        difficulties=("Expert",), seed=semilla,
                    )
                    cont = generate.SOSTENIDOS
                    total = cont.get("candidatos", 0) or 1
                    clave = f"{relleno}|{largo}|{tope}"
                    fila["combos"][clave] = round(cont.get("escritos", 0) / total, 4)
    finally:
        generate.SUSTAIN_MIN_LENGTH_BEATS = largo_original
    return fila


def resumir(filas: list[dict]) -> None:
    if not filas:
        return
    humanos = np.array([f["humano"] for f in filas], dtype=float)
    claves = list(filas[0]["combos"].keys())
    print("\n=== {} canciones, humano p50 {:.3f} (de {:.3f} a {:.3f}) ===".format(
        len(filas), float(np.median(humanos)), float(humanos.min()), float(humanos.max())))
    print("{:18s} {:>8s} {:>8s} {:>8s} {:>8s}".format(
        "relleno|largo|tope", "media", "error", "corr", "desv"))
    resultados = []
    for clave in claves:
        vals = np.array([f["combos"][clave] for f in filas], dtype=float)
        error = float(np.abs(vals - humanos).mean())
        desv = float(vals.std())
        corr = float(np.corrcoef(vals, humanos)[0, 1]) if desv > 1e-9 else float("nan")
        resultados.append((error, clave, float(vals.mean()), corr, desv))
    for error, clave, media, corr, desv in sorted(resultados):
        print("{:18s} {:8.3f} {:8.3f} {:8.3f} {:8.3f}".format(
            clave, media, error, corr, desv))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--humanos", type=int, default=0)
    p.add_argument("--perfil", default=str(PERFIL))
    p.add_argument("--salida", default="salida/calibrar_sostenidos.json")
    args = p.parse_args(argv)

    carpetas = (_con_guitarra_aislada(BIBLIOTECA, args.humanos)
                if args.humanos else [PRIDE])
    perfil = load_profile(Path(args.perfil))
    filas = []
    for i, carpeta in enumerate(carpetas, 1):
        print("  [{}/{}] {}".format(i, len(carpetas), carpeta.name[:60]), flush=True)
        fila = medir_cancion(carpeta, perfil)
        if fila is None:
            print("      (sin guitarra aislada o sin chart humano)")
            continue
        filas.append(fila)
        mejor = min(fila["combos"].items(), key=lambda kv: abs(kv[1] - fila["humano"]))
        print("      humano {:.3f}   mejor combo {} -> {:.3f}".format(
            fila["humano"], mejor[0], mejor[1]), flush=True)
    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.salida).write_text(json.dumps(filas, indent=1, ensure_ascii=False),
                                 encoding="utf-8")
    resumir(filas)
    print("\n[OK] " + args.salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
