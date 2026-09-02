"""Compara un chart generado contra el chart humano de la MISMA cancion.

Es la unica prueba que responde "esto se parece a algo que hizo una persona?".
Ambos charts se refieren al mismo audio, asi que sus tiempos son comparables
directamente.

    aciertos (recall)  : notas humanas que tienen una nota generada al lado
    precision          : notas generadas que caen sobre una nota humana
    F1                 : media armonica de las dos

Un F1 alto no es el objetivo final -- copiar al humano nota por nota no es lo
que queremos --, pero por debajo de ~0.35 el chart no esta siguiendo la
guitarra, y eso si es un fallo.

Uso:
    python tools/comparar_humano.py "<carpeta generada>" "<carpeta original>"
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autochart import chartio, midiio  # noqa: E402

TOLERANCE_S = 0.07


def human_note_times(song_dir: Path, difficulty: str = "Expert") -> np.ndarray:
    chart_path = song_dir / "notes.chart"
    if chart_path.is_file():
        chart = chartio.parse_chart(chart_path)
        track = chart.tracks.get(f"{difficulty}Single")
        if track:
            ticks = sorted({n.tick for n in track.notes if n.fret <= chartio.FRET_ORANGE})
            return np.array([chart.tick_to_seconds(t) for t in ticks])
    midi_path = song_dir / "notes.mid"
    if midi_path.is_file():
        midi = midiio.parse_midi(midi_path)
        notes = midi.tracks.get(difficulty, [])
        ticks = sorted({n.tick for n in notes})
        return np.array([midi.tick_to_seconds(t) for t in ticks])
    return np.array([])


def generated_note_times(song_dir: Path, difficulty: str = "Expert") -> np.ndarray:
    chart = chartio.parse_chart(song_dir / "notes.chart")
    track = chart.tracks.get(f"{difficulty}Single")
    if not track:
        return np.array([])
    ticks = sorted({n.tick for n in track.notes if n.fret <= chartio.FRET_ORANGE})
    return np.array([chart.tick_to_seconds(t) for t in ticks])


def match_ratio(a: np.ndarray, b: np.ndarray, tolerance: float = TOLERANCE_S) -> float:
    if a.size == 0 or b.size == 0:
        return 0.0
    distances = np.abs(a[:, None] - b[None, :]).min(axis=1)
    return float((distances <= tolerance).mean())


def best_offset(a: np.ndarray, b: np.ndarray, search: float = 0.5, step: float = 0.005) -> float:
    """Constant shift that best aligns `a` onto `b`.

    Charts made from MIDI carry an authoring delay of a few tens of
    milliseconds against the audio; comparing without removing it measures the
    charter's offset convention instead of the notes.
    """
    if a.size == 0 or b.size == 0:
        return 0.0
    best, score = 0.0, -1.0
    for shift in np.arange(-search, search + step, step):
        value = match_ratio(a + shift, b)
        if value > score:
            best, score = float(shift), value
    return best


def main(generated: str, original: str, difficulty: str = "Expert") -> int:
    generated_dir, original_dir = Path(generated), Path(original)
    mine = generated_note_times(generated_dir, difficulty)
    theirs = human_note_times(original_dir, difficulty)
    if mine.size == 0 or theirs.size == 0:
        print("[X] Falta alguno de los dos charts (o la dificultad pedida).")
        return 2

    offset = best_offset(theirs, mine)
    aligned = theirs + offset
    recall = match_ratio(aligned, mine)
    precision = match_ratio(mine, aligned)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)

    span_mine = float(mine[-1] - mine[0]) or 1.0
    span_theirs = float(theirs[-1] - theirs[0]) or 1.0
    print(f"[*] {original_dir.name}  ({difficulty})")
    print(f"    humano   : {theirs.size:>5} notas  {theirs.size / span_theirs:.2f} n/s")
    print(f"    generado : {mine.size:>5} notas  {mine.size / span_mine:.2f} n/s")
    print(f"    desfase del charter: {offset * 1000:+.0f} ms (descontado antes de comparar)")
    print(f"    aciertos (recall)  : {recall * 100:5.1f} %  "
          f"(notas humanas cubiertas, +-{int(TOLERANCE_S * 1000)} ms)")
    print(f"    precision          : {precision * 100:5.1f} %  (notas generadas sobre una humana)")
    print(f"    F1                 : {f1:.3f}")
    if f1 < 0.35:
        print("[X] Por debajo del minimo: el chart no esta siguiendo la guitarra.")
        return 1
    print("[OK] El chart sigue la guitarra.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2], *sys.argv[3:4]))
