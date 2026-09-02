"""De QUE instrumento son los ataques que acaban siendo notas del chart.

El banco dice que las notas caen sobre ataques reales del audio -- 93-95 % a
menos de 50 ms -- y aun asi Bruno dice que no se siente que se toque la cancion.
Las dos cosas son verdad a la vez, y esta herramienta mide por que: **caer sobre
un ataque no es caer sobre el ataque BUENO**. El detector va con umbral 0 y ve
todo lo que suena; la etapa de densidad se queda con lo mas fuerte de cada
ventana, y en una mezcla lo mas fuerte casi siempre es el bombo o la caja.

Un chart escrito sobre la percusion se siente igual en todas las canciones,
porque las baterias se parecen entre si mucho mas que las melodias. Por eso esta
medida y `tools/parecidas.py` son la misma queja mirada por los dos lados.

    python tools/quien_toca.py "salida/<carpeta>"
    python tools/quien_toca.py "salida/<carpeta>" --mezcla "ruta/song.mp3"

Lo que sale, y como leerlo:

  lead        0 = el ataque es grave/percusivo, 1 = manda la banda melodica.
              Si el de las ELEGIDAS no supera claramente al de TODAS, la etapa
              de densidad no esta prefiriendo la melodia: esta cogiendo lo mas
              fuerte, que es la bateria.
  % percusiva Energia percusiva contra armonica en ese instante exacto (HPSS).
              Es la cifra que decide: por encima del 50 % esa nota es un golpe
              de bateria con un color encima.

Control medido el 22-08-2026 sobre la mezcla, sin separar nada:

    JUNIOR H - INTRO        29 % de las notas mas percusivas que armonicas
    MARCOS YTZ - DALI       58 %
    Brunich - Cyber Club    63 %   (y lead ELEGIDAS 0.668 < TODAS 0.692)

Ese ultimo caso es el peor posible: en una cancion suya de guitarra, el filtro
elige ataques MENOS melodicos que la media de la cancion.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autochart import audio, chartio, midiio  # noqa: E402


def tiempos_de_notas(carpeta: Path, pista: str, desfase_s: float = 0.0):
    """Los instantes de las notas, venga el chart de `.chart` o de `.mid`.

    Hasta ahora esto solo leia `.chart`, y **todos los charts humanos de la
    biblioteca son `.mid`**: la herramienta con la que se fijo el objetivo del
    20 % no podia medir a un humano, o sea que ese 20 % no salia de ninguna
    referencia. Con esto ya se puede saber cuanto da un chart escrito a mano.

    `desfase_s` existe porque un chart venido de `.mid` lleva el desfase de
    autoria que este proyecto tiene medido (+65/+70 ms contra el audio): el
    charter cuadra a la rejilla, no a la onda. Sin descontarlo se juzga la
    costumbre del charter y no donde cae la nota.
    """
    ruta_chart = carpeta / "notes.chart"
    if ruta_chart.is_file():
        chart = chartio.parse_chart(ruta_chart)
        track = chart.tracks.get(pista)
        if track is None:
            return None, f"no hay pista {pista}"
        ticks = sorted({n.tick for n in track.notes if n.fret < 5})
        if not ticks:
            return None, "pista vacia"
        return np.array([chart.tick_to_seconds(t) for t in ticks]) - desfase_s, "chart"

    ruta_mid = carpeta / "notes.mid"
    if not ruta_mid.is_file():
        return None, "no hay notes.chart ni notes.mid"
    chart, pistas = midiio.parse_midi_multi(ruta_mid)
    dificultad = next((d for d in ("Expert", "Hard", "Medium", "Easy")
                       if pista.startswith(d)), "Expert")
    instrumento = "guitarra"
    notas = (pistas.get(instrumento) or {}).get(dificultad)
    if not notas:
        return None, f"el midi no trae {instrumento}/{dificultad} (hay {list(pistas)})"
    ticks = sorted({n.tick for n in notas if getattr(n, "fret", 0) < 5})
    if not ticks:
        return None, "pista vacia"
    return np.array([chart.tick_to_seconds(t) for t in ticks]) - desfase_s, "midi"


def medir(carpeta: Path, mezcla: Path, pista: str = "ExpertSingle",
          desfase_ms: float = 0.0) -> dict | None:
    import librosa

    tiempos, fuente = tiempos_de_notas(carpeta, pista, desfase_ms / 1000.0)
    if tiempos is None:
        print(f"[X] {carpeta.name}: {fuente}")
        return None

    # El pozo de ataques es el de la MEZCLA, que es lo que oye Bruno, aunque el
    # chart se haya generado desde un stem: la pregunta es cual de los sonidos
    # que suenan a la vez se ha llevado la nota.
    analisis = audio.analyse(mezcla)
    pozo = np.array([o.time for o in analisis.onsets])
    if pozo.size == 0:
        print(f"[X] {carpeta.name}: ni un ataque en la mezcla")
        return None
    lead = np.array([o.lead for o in analisis.onsets])
    midi = np.array([o.midi for o in analisis.onsets])

    cerca = np.clip(np.searchsorted(pozo, tiempos), 0, pozo.size - 1)
    cerca = np.array([
        i - 1 if i > 0 and abs(pozo[i - 1] - t) < abs(pozo[i] - t) else i
        for i, t in zip(cerca, tiempos)
    ])

    # Percusivo contra armonico en el instante exacto de cada nota.
    y, sr = librosa.load(str(mezcla), sr=audio.ANALYSIS_SR, mono=True)
    armonico, percusivo = librosa.decompose.hpss(
        librosa.stft(y, n_fft=1024, hop_length=audio.HOP_LENGTH))
    ea = np.abs(armonico).sum(axis=0)
    ep = np.abs(percusivo).sum(axis=0)

    def fraccion(instantes):
        f = np.clip(librosa.time_to_frames(instantes, sr=sr, hop_length=audio.HOP_LENGTH),
                    0, ea.size - 1)
        return ep[f] / np.maximum(1e-9, ep[f] + ea[f])

    perc, perc_pozo = fraccion(tiempos), fraccion(pozo)
    datos = {
        "carpeta": carpeta.name,
        "ataques": int(pozo.size),
        "notas": int(tiempos.size),
        "lead_elegidas": float(lead[cerca].mean()),
        "lead_todas": float(lead.mean()),
        "midi_elegidas": float(np.median(midi[cerca])),
        "midi_todas": float(np.median(midi)),
        "percusiva_elegidas": float(perc.mean()),
        "percusiva_todas": float(perc_pozo.mean()),
        "notas_percusivas": float((perc > 0.5).mean()),
    }
    print(f"[*] {datos['carpeta']}")
    print(f"    ataques detectados {datos['ataques']:5d}  ->  notas escritas "
          f"{datos['notas']:4d}  ({100 * datos['notas'] / datos['ataques']:.0f} %)")
    print(f"    lead (0=percusion, 1=melodia)          elegidas {datos['lead_elegidas']:.3f}"
          f"   todas {datos['lead_todas']:.3f}"
          f"{'   <-- ELIGE LO MENOS MELODICO' if datos['lead_elegidas'] < datos['lead_todas'] else ''}")
    print(f"    tono MIDI del ataque                   elegidas {datos['midi_elegidas']:.0f}"
          f"      todas {datos['midi_todas']:.0f}")
    print(f"    % de energia percusiva en ese instante elegidas "
          f"{100 * datos['percusiva_elegidas']:.0f} %    todas {100 * datos['percusiva_todas']:.0f} %")
    print(f"    notas cuyo ataque es MAS percusivo que armonico: "
          f"{100 * datos['notas_percusivas']:.0f} %")
    return datos


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("carpeta", help="Carpeta con notes.chart")
    parser.add_argument("--desfase-ms", type=float, default=0.0,
                        help="Restar el desfase de autoria del .mid (medido: 65-70)")
    parser.add_argument("--mezcla", default=None,
                        help="El audio que oye el jugador (por defecto, el de la carpeta)")
    parser.add_argument("--pista", default="ExpertSingle")
    args = parser.parse_args(argv)

    carpeta = Path(args.carpeta)
    mezcla = Path(args.mezcla) if args.mezcla else audio.pick_beat_audio(carpeta)
    if mezcla is None or not Path(mezcla).exists():
        print(f"[X] No encuentro la mezcla de {carpeta}")
        return 2
    return 0 if medir(carpeta, Path(mezcla), args.pista, args.desfase_ms) else 2


if __name__ == "__main__":
    raise SystemExit(main())
