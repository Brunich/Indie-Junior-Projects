"""Ver el patron sin abrir el juego.

Dibuja la autopista en texto: una linea por posicion de la rejilla, los cinco
trastes en columnas y los compases separados. Sirve para mirar si el patron
tiene forma -- si repite, si sube y baja, si se queda clavado -- antes de
gastar una partida en comprobarlo.

    python tools/ver_patron.py "salida/<carpeta>" --desde 30 --segundos 20
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autochart import chartio  # noqa: E402

COLOURS = ("V", "R", "A", "Z", "N")  # verde, rojo, amarillo, azul, naranja


def draw(chart: chartio.Chart, track_name: str, start_s: float, span_s: float) -> None:
    track = chart.tracks.get(track_name)
    if track is None:
        print(f"[X] No existe la pista {track_name}. Hay: {', '.join(sorted(chart.tracks))}")
        return

    groups: dict[int, list[chartio.Note]] = {}
    for note in track.notes:
        if note.fret > chartio.FRET_ORANGE:
            continue
        groups.setdefault(note.tick, []).append(note)

    resolution = chart.resolution
    ticks = [t for t in sorted(groups) if start_s <= chart.tick_to_seconds(t) <= start_s + span_s]
    if not ticks:
        print("[X] No hay notas en ese tramo.")
        return

    print(f"    tiempo   compas   {''.join(f'{c:<4}' for c in COLOURS)}")
    print("    " + "-" * 40)
    last_bar = -1
    for tick in ticks:
        bar = tick // (resolution * 4)
        if bar != last_bar:
            print(f"    {'':8} -- compas {bar} --")
            last_bar = bar
        frets = {n.fret for n in groups[tick]}
        sustain = max(n.sustain for n in groups[tick])
        lane = "".join(("[]" if f in frets else " .") + "  " for f in range(5))
        beat = (tick % (resolution * 4)) / resolution
        tail = f"  ~{sustain / resolution:.1f}" if sustain else ""
        print(f"    {chart.tick_to_seconds(tick):7.2f}  {beat:5.2f}   {lane}{tail}")


def summarise(chart: chartio.Chart, track_name: str) -> None:
    track = chart.tracks.get(track_name)
    if track is None:
        return
    groups: dict[int, set[int]] = {}
    for note in track.notes:
        if note.fret <= chartio.FRET_ORANGE:
            groups.setdefault(note.tick, set()).add(note.fret)

    singles = [next(iter(f)) for _, f in sorted(groups.items()) if len(f) == 1]
    moves = Counter(b - a for a, b in zip(singles, singles[1:]))
    total = sum(moves.values()) or 1
    print(f"\n    Movimiento de la mano en {track_name} ({total} pares de notas sueltas):")
    for delta in sorted(moves, key=lambda d: -moves[d])[:7]:
        label = "se queda" if delta == 0 else f"{'sube' if delta > 0 else 'baja'} {abs(delta)}"
        print(f"      {label:<10} {100 * moves[delta] / total:5.1f} %")
    print("      (en los charts humanos: se queda 31 %, +-1 47 %, +-2 14 %, +-3 6 %)")

    trigrams = Counter(
        "".join(str(v) for v in singles[i:i + 3]) for i in range(len(singles) - 2)
    )
    repeated = [(shape, count) for shape, count in trigrams.most_common(5)]
    print("    Formas de tres notas mas repetidas: "
          + ", ".join(f"{s} x{c}" for s, c in repeated))


def main() -> int:
    parser = argparse.ArgumentParser(description="Dibuja el patron de un chart en texto")
    parser.add_argument("carpeta", help="Carpeta con notes.chart, o el propio notes.chart")
    parser.add_argument("--pista", default="ExpertSingle")
    parser.add_argument("--desde", type=float, default=30.0, help="Segundo inicial")
    parser.add_argument("--segundos", type=float, default=12.0)
    args = parser.parse_args()

    path = Path(args.carpeta)
    if path.is_dir():
        path = path / "notes.chart"
    if not path.is_file():
        print(f"[X] No existe: {path}")
        return 2

    chart = chartio.parse_chart(path)
    print(f"[*] {chart.metadata.get('Artist', '?')} - {chart.metadata.get('Name', '?')}"
          f"   ({args.pista}, desde {args.desde:.0f} s)")
    draw(chart, args.pista, args.desde, args.segundos)
    summarise(chart, args.pista)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
