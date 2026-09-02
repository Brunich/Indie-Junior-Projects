"""Comprueba que el chart generado suena donde debe.

Dos medidas, ambas en milisegundos y sobre el archivo ya escrito en disco
(no sobre las estructuras en memoria, que es donde es facil enganarse):

1. **Deriva del mapa de tempo**: cada pulso detectado en el audio deberia caer
   exactamente en su tick. Si esto se va, el chart entero se desplaza.
2. **Ataque mas cercano**: cada nota escrita deberia coincidir con un ataque
   real del audio. Si esto se va, hay notas inventadas.

Uso:
    python tools/verificar_sincronia.py "salida/<carpeta generada>"
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autochart import chartio  # noqa: E402
from autochart.audio import analyse, pick_audio  # noqa: E402
from autochart.timing import build_tempo_map  # noqa: E402


def main(folder: str) -> int:
    song_dir = Path(folder)
    chart_path = song_dir / "notes.chart"
    if not chart_path.is_file():
        print(f"[X] No hay notes.chart en {song_dir}")
        return 2

    audio_path = pick_audio(song_dir)
    if audio_path is None:
        print(f"[X] No hay audio en {song_dir}")
        return 2

    print(f"[*] Reanalizando {audio_path.name} para comparar contra el chart escrito...")
    analysis = analyse(audio_path)
    chart = chartio.parse_chart(chart_path)
    tempo_map = build_tempo_map(analysis.beat_times, chart.resolution)

    # 1. Deriva del mapa de tempo.
    drifts = []
    for index, beat_time in enumerate(tempo_map.beat_times):
        tick = tempo_map.beat_to_tick(index)
        drifts.append(abs(chart.tick_to_seconds(tick) - float(beat_time)) * 1000.0)
    drifts = np.array(drifts)
    print(f"    pulsos comprobados: {len(drifts)}")
    print(f"    deriva del tempo  : media {drifts.mean():.2f} ms | "
          f"p95 {np.percentile(drifts, 95):.2f} ms | max {drifts.max():.2f} ms")

    # 2. Distancia de cada nota al ataque mas cercano del audio.
    onset_times = np.array([o.time for o in analysis.onsets])
    track = chart.tracks.get("ExpertSingle")
    if track is None or not onset_times.size:
        print("[X] Falta la pista ExpertSingle o no hay ataques detectados.")
        return 1
    ticks = sorted({n.tick for n in track.notes if n.fret <= chartio.FRET_ORANGE})
    note_times = np.array([chart.tick_to_seconds(t) for t in ticks])
    nearest = np.abs(note_times[:, None] - onset_times[None, :]).min(axis=1) * 1000.0
    print(f"    notas comprobadas : {len(note_times)}")
    print(f"    distancia al ataque: media {nearest.mean():.1f} ms | "
          f"p95 {np.percentile(nearest, 95):.1f} ms | max {nearest.max():.1f} ms")
    within = (nearest <= 50).mean() * 100
    print(f"    notas a menos de 50 ms de un ataque real: {within:.1f} %")

    bad_drift = float(np.percentile(drifts, 95)) > 15.0
    bad_notes = within < 85.0
    if bad_drift:
        print("[X] El mapa de tempo se desvia demasiado.")
    if bad_notes:
        print("[X] Demasiadas notas lejos de un ataque real.")
    if not bad_drift and not bad_notes:
        print("[OK] Sincronia dentro de tolerancia.")
    return 1 if (bad_drift or bad_notes) else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
