"""La prueba de aceptacion: ,se parece al chart que hizo una persona?

Bruno, 22-08-2026: *"lo importante es que los generados esten muy similares a
los que estuvieron hechos a mano"*, y puso la referencia:
**Stevie Ray Vaughan - Pride & Joy**, que es guitarra pura y esta bien
charteada. Sobre esa cancion hay que poder decir tres cosas con numero:

    ,detecta todas las notas?      recall contra el chart humano
    ,las coloca donde van?         precision y F1, con el desfase descontado
    ,el patron se parece al suyo?  distancia de gestos contra el humano

Las tres a la vez, porque cada una sola engana: se puede tener F1 alto tocando
la bateria a tiempo, y un patron humano en los sitios equivocados.

    python tools/contra_el_humano.py --pride            # la de referencia
    python tools/contra_el_humano.py "<carpeta>" --generar
    python tools/contra_el_humano.py "<carpeta>" --generado salida/x/<carpeta>

Referencias para leer la distancia de gestos (coseno, 0 = identicos):

    dos charts humanos cualesquiera   0.58
    nuestros charts entre si          0.11   <- se parecen demasiado
    nosotros contra el humano         es lo que mide esta herramienta

El desfase de autoria se busca y se descuenta: un chart venido de `.mid` cuadra
a la rejilla y lleva +65/+70 ms contra la onda. Sin descontarlo se mide la
costumbre del charter, no las notas (DECISIONES_MEDIDAS.md).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import zlib
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))

from autochart import atlas, audio  # noqa: E402
from comparar_humano import (best_offset, generated_note_times,  # noqa: E402
                             human_note_times, match_ratio)
from sigue_la_melodia import medir as medir_melodia  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
PRIDE = ("03_Guitar Hero 3 Legends of Rock/"
         "Stevie Ray Vaughan (Steve Ouimette) - Pride & Joy")
PERFIL_ORO = RAIZ / "datos" / "perfil_oro.json"
# Distancia de gestos entre dos charts humanos cualesquiera, medida en 16 charts
# de la biblioteca. Es la vara: acercarse a 0 es copiar, quedarse en 0.58 es no
# parecerse en nada.
DISTANCIA_ENTRE_HUMANOS = 0.582


def vector_de_gestos(carpeta: Path) -> np.ndarray | None:
    """Gestos por cada 100 notas de la pista de guitarra en Experto."""
    for r in atlas.analizar_carpeta(carpeta, ("Expert",)):
        if r.instrumento != "guitarra" or r.notas < 50:
            continue
        v = np.array([r.licks.get(t, 0) for t in atlas.TIPOS_LICK], dtype=float)
        return v / max(1.0, r.notas) * 100.0
    return None


def perfil_corto(carpeta: Path) -> dict | None:
    for r in atlas.analizar_carpeta(carpeta, ("Expert",)):
        if r.instrumento != "guitarra" or r.notas < 50:
            continue
        return {"notas": r.notas, "nps": r.nps, "acordes": r.acordes,
                "sostenidos": r.sostenidos, "repeticion": r.repeticion,
                "ligadas": r.ligadas, "variacion": r.variacion,
                "tramos_muertos": r.tramos_muertos}
    return None


def distancia(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if not na or not nb:
        return float("nan")
    return 1.0 - float(a @ b) / (na * nb)


def generar(carpeta: Path, destino: Path) -> Path:
    semilla = zlib.crc32(carpeta.name.encode("utf-8")) % 100000
    orden = [sys.executable, "-m", "autochart", "generar", str(carpeta),
             "--salida", str(destino), "--dificultades", "Expert",
             "--semilla", str(semilla)]
    if PERFIL_ORO.is_file():
        orden += ["--perfil", str(PERFIL_ORO)]
    print(f"[*] Generando (semilla {semilla})...")
    r = subprocess.run(orden, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(RAIZ))
    if r.returncode:
        print(r.stdout[-800:])
        print(r.stderr[-800:])
        raise SystemExit("[X] la generacion fallo")
    hechas = sorted(p for p in destino.iterdir() if p.is_dir())
    return hechas[-1] if hechas else destino


def informe(humana: Path, generada: Path) -> int:
    print(f"\n[*] {humana.name}")
    print(f"    humano   {humana}")
    print(f"    generado {generada}\n")

    humanas = human_note_times(humana)
    nuestras = generated_note_times(generada)
    if humanas is None or nuestras is None or not len(humanas) or not len(nuestras):
        print("[X] falta alguno de los dos charts")
        return 2

    desfase = best_offset(humanas, nuestras)
    recall = match_ratio(humanas, nuestras + desfase)
    precision = match_ratio(nuestras + desfase, humanas)
    f1 = 2 * recall * precision / (recall + precision) if (recall + precision) else 0.0

    print("    -- LAS NOTAS ------------------------------------------------")
    print(f"    humano   {len(humanas):5d} notas")
    print(f"    generado {len(nuestras):5d} notas   ({len(nuestras)/len(humanas)*100:5.1f} % de las suyas)")
    print(f"    desfase encontrado {desfase*1000:+6.0f} ms")
    print(f"    recall {recall:.3f}   precision {precision:.3f}   F1 {f1:.3f}")

    va, vb = vector_de_gestos(generada), vector_de_gestos(humana)
    print("\n    -- EL PATRON ------------------------------------------------")
    if va is None or vb is None:
        print("    (no se pudo sacar el vector de gestos)")
    else:
        d = distancia(va, vb)
        cerca = (1.0 - d / DISTANCIA_ENTRE_HUMANOS) * 100.0
        print(f"    distancia de gestos contra SU chart   {d:.3f}")
        print(f"    (dos humanos cualesquiera estan a {DISTANCIA_ENTRE_HUMANOS:.3f};"
              f" o sea {cerca:.0f} % del camino hecho)")

    ph, pn = perfil_corto(humana), perfil_corto(generada)
    if ph and pn:
        print(f"\n    {'':22} {'humano':>9} {'generado':>9}")
        for clave, nombre in (("nps", "notas/s"), ("acordes", "acordes"),
                              ("sostenidos", "sostenidos"), ("repeticion", "repite traste"),
                              ("ligadas", "ligadas"), ("variacion", "variacion"),
                              ("tramos_muertos", "tramos muertos")):
            print(f"    {nombre:22} {ph[clave]:9.3f} {pn[clave]:9.3f}")

    print("\n    -- LA MELODIA -----------------------------------------------")
    pista = audio.pick_audio(humana)
    if pista is None:
        print("    (no hay audio)")
    else:
        print(f"    audio: {pista.name}")
        for etiqueta, carpeta in (("humano", humana), ("generado", generada)):
            r = medir_melodia(carpeta, pista)
            if r is None or "error" in r:
                print(f"    {etiqueta:9} {r['error'] if r else 'sin datos'}")
                continue
            print(f"    {etiqueta:9} acierto {r['acierto']*100:5.1f} %   "
                  f"azar {r['azar']*100:5.1f} %   ventaja {r['ventaja']*100:+6.1f} %")
    print()
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Compara un chart generado con el humano")
    parser.add_argument("carpeta", nargs="?", default=None,
                        help="carpeta de la cancion humana")
    parser.add_argument("--pride", action="store_true",
                        help="usa la cancion de referencia de Bruno")
    parser.add_argument("--generar", action="store_true",
                        help="genera el chart antes de comparar")
    parser.add_argument("--generado", default=None,
                        help="carpeta con el chart ya generado")
    parser.add_argument("--salida", default="salida/contra_humano")
    args = parser.parse_args(argv)

    if args.pride:
        humana = BIBLIOTECA / PRIDE
    elif args.carpeta:
        humana = Path(args.carpeta)
    else:
        parser.error("hace falta una carpeta o --pride")
    if not humana.is_dir():
        print(f"[X] no existe {humana}")
        return 2

    if args.generado:
        generada = Path(args.generado)
    else:
        destino = RAIZ / args.salida
        candidata = destino / f"{humana.name} (AutoChart)"
        if args.generar or not candidata.is_dir():
            destino.mkdir(parents=True, exist_ok=True)
            generada = generar(humana, destino)
        else:
            generada = candidata
    if not generada.is_dir():
        print(f"[X] no existe el chart generado: {generada}")
        return 2

    return informe(humana, generada)


if __name__ == "__main__":
    raise SystemExit(main())
