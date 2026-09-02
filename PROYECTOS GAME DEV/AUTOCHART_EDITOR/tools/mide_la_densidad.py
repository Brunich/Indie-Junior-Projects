"""Cuantas notas por segundo deberia llevar una cancion, y quien acierta mas.

Es el primer paso de la tarea escrita en `docs/SIGUIENTE_CHAT.md`, y es a
proposito una medida ANTES de tocar el generador: se comparan las dos reglas
sobre el mismo material y solo se cambia el codigo si la nueva gana.

    la regla de HOY      el p50 del bucket de BPM del perfil del oro.
                         La cancion no opina: dos canciones al mismo tempo
                         reciben el mismo presupuesto de notas.
    la regla CANDIDATA   una fraccion de los ataques que oye el detector.
                         La cancion opina, pero la fraccion no es constante:
                         medida en estas mismas canciones va de 0.137 a 0.525.

La vara es el chart que escribio una persona: para cada cancion se mira cuantas
notas por segundo puso, y se pregunta cual de las dos reglas se acerca mas.

    python tools/mide_la_densidad.py            # las 12 con guitarra aislada
    python tools/mide_la_densidad.py "<carpeta>"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))

from autochart import audio, corpus, generate  # noqa: E402
from sigue_la_melodia import _con_guitarra_aislada  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
PERFIL_ORO = RAIZ / "datos" / "perfil_oro.json"


def medir(carpeta: Path, perfil: dict) -> dict | None:
    """Las tres densidades de una cancion: la humana y las dos reglas."""
    chart = carpeta / "notes.chart"
    stats = (corpus.analyse_chart_file(chart) if chart.is_file()
             else corpus.analyse_midi_file(carpeta / "notes.mid"))
    if stats is None or stats.note_count < 32:
        return None

    ruta = carpeta / "guitar.ogg"
    if not ruta.is_file():
        ruta = audio.pick_audio(carpeta)
        if ruta is None:
            return None
    analisis = audio.analyse(str(ruta))
    ataques = len(analisis.onsets)
    if not ataques or analisis.duration <= 0:
        return None

    # La regla de hoy, pedida al generador con su propia funcion para no medir
    # una copia: el spec de Experto y el BPM que dice el chart humano.
    spec = generate.DIFFICULTY_SPECS["Expert"]
    del_perfil = generate.target_notes_per_second(perfil, stats.bpm, spec)

    return {
        "cancion": carpeta.name,
        "bpm": round(float(stats.bpm), 1),
        "duracion": round(float(analisis.duration), 1),
        "humano": round(float(stats.notes_per_second), 3),
        "del_perfil": round(float(del_perfil), 3),
        "ataques": ataques,
        "ataques_por_s": round(ataques / analisis.duration, 3),
    }


def informe(filas: list[dict]) -> None:
    if not filas:
        print("[X] ninguna cancion medida")
        return
    humano = np.array([f["humano"] for f in filas])
    perfil = np.array([f["del_perfil"] for f in filas])
    ataques = np.array([f["ataques_por_s"] for f in filas])

    # La fraccion de los ataques que el humano convierte en nota. Se saca de las
    # MISMAS canciones que se estan juzgando, asi que este numero le da ventaja
    # a la regla candidata: es su mejor caso posible, no una prediccion honesta.
    fraccion = float(np.median(humano / ataques))
    del_audio = ataques * fraccion

    print("\n{:34s} {:>6s} {:>8s} {:>8s} {:>8s}".format(
        "cancion", "bpm", "humano", "perfil", "audio"))
    for f, a in zip(filas, del_audio):
        print("{:34s} {:6.0f} {:8.2f} {:8.2f} {:8.2f}".format(
            f["cancion"][:34], f["bpm"], f["humano"], f["del_perfil"], a))

    print("\nfraccion de ataques que el humano hace nota: {:.3f}".format(fraccion))
    print("{:34s} {:>8s} {:>8s}".format("", "perfil", "audio"))
    print("{:34s} {:8.3f} {:8.3f}".format(
        "error medio (notas/s)", float(np.abs(perfil - humano).mean()),
        float(np.abs(del_audio - humano).mean())))
    print("{:34s} {:8.3f} {:8.3f}".format(
        "error mediano", float(np.median(np.abs(perfil - humano))),
        float(np.median(np.abs(del_audio - humano)))))
    print("{:34s} {:8d} {:8d}".format(
        "cuantas acierta mejor",
        int((np.abs(perfil - humano) < np.abs(del_audio - humano)).sum()),
        int((np.abs(del_audio - humano) < np.abs(perfil - humano)).sum())))

    def correl(x):
        if x.std() == 0 or humano.std() == 0:
            return float("nan")
        return float(np.corrcoef(x, humano)[0, 1])

    print("{:34s} {:8.3f} {:8.3f}".format(
        "correlacion con el humano", correl(perfil), correl(ataques)))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("carpeta", nargs="?", default=None)
    p.add_argument("--salida", default="salida/densidad.json")
    args = p.parse_args(argv)

    perfil = corpus.load_profile(PERFIL_ORO) if PERFIL_ORO.is_file() else None
    carpetas = ([Path(args.carpeta)] if args.carpeta
                else _con_guitarra_aislada(BIBLIOTECA, 12))
    filas = []
    for i, carpeta in enumerate(carpetas, 1):
        print("  [{}/{}] {}".format(i, len(carpetas), carpeta.name[:56]))
        try:
            fila = medir(Path(carpeta), perfil)
        except Exception as error:  # una cancion rota no para la medida
            print("      [X] {}".format(error))
            fila = None
        if fila:
            filas.append(fila)
    informe(filas)
    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.salida).write_text(json.dumps(filas, indent=1, ensure_ascii=False),
                                 encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
