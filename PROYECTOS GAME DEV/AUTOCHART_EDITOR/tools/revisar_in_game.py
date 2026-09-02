"""Revisa una carpeta generada con los ojos del JUEGO, no con los del oido.

`autochart revisar` comprueba que el chart sea musicalmente sano. Esto comprueba
lo otro: que Clone Hero pueda cargarlo y que se pueda jugar de principio a fin.
Son cosas distintas, y las tres que mas dolian no las veia el validador:

* la ultima nota (o su sostenido) sonando despues de que acabe el audio -- la
  cancion termina con la nota pulsada y se pierde;
* la primera nota antes de que la autopista haya bajado nada;
* frases de Star Power vacias, solapadas, o directamente ausentes en Facil y
  Medio, donde el medidor no llegaba a llenarse nunca.

Uso:

    python tools/revisar_in_game.py "salida\\<carpeta>"
    python tools/revisar_in_game.py salida            # todas las de dentro

Necesita `ffprobe` en el PATH para medir el audio; sin el, se salta las
comprobaciones que dependen de la duracion y avisa.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autochart.chartio import FLAG_FORCE, FLAG_TAP, parse_chart

AUDIO_EXTENSIONS = (".ogg", ".mp3", ".opus", ".wav", ".flac")
KNOWN_STEMS = {"song", "guitar", "bass", "rhythm", "vocals", "keys", "drums", "preview"}

# Margenes, todos medidos contra los charts humanos de la biblioteca:
#   primera nota  p5 = 2.0 s   (mediana 3.7)
#   sostenidos    p50 = 0.75 tiempos en las cuatro dificultades
#   frases de SP  p50 = 10 por pista, tambien en las cuatro
LEAD_IN_WARN_S = 1.0
END_MARGIN_S = 0.25
SP_MIN_PHRASES = 4  # cuatro frases = una activacion


def audio_duration(path: Path) -> float | None:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=60,
        )
        return float(out.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def read_ini(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    raw = path.read_bytes()
    text = ""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if "=" in line and not line.startswith(("[", ";", "#")):
            key, _, value = line.partition("=")
            values[key.strip().lower()] = value.strip()
    return values


def check_folder(folder: Path) -> dict:
    report: dict = {"carpeta": folder.name, "errores": [], "avisos": [], "pistas": {}}
    errors, warnings = report["errores"], report["avisos"]

    chart_path = folder / "notes.chart"
    if not chart_path.is_file():
        errors.append("no hay notes.chart: el juego ni siquiera ve la carpeta")
        return report
    chart = parse_chart(chart_path)
    ini = read_ini(folder / "song.ini")

    # --- lo que hace falta para que CARGUE -------------------------------
    audios = [p for p in folder.iterdir() if p.suffix.lower() in AUDIO_EXTENSIONS]
    names = {p.stem.lower() for p in audios}
    if not audios:
        errors.append("la carpeta no tiene audio")
    elif not (names & KNOWN_STEMS):
        errors.append(f"ningun audio con nombre que el juego reconozca: {sorted(names)}")
    stream = chart.metadata.get("MusicStream", "")
    if stream and not (folder / stream).is_file():
        errors.append(f"MusicStream apunta a {stream!r} y ese archivo no esta")
    if not ini:
        warnings.append("sin song.ini: el juego usara solo lo que ponga el chart")

    main = next((p for p in audios if p.stem.lower() == "song"), audios[0] if audios else None)
    duration = audio_duration(main) if main is not None else None
    if duration is None and main is not None:
        warnings.append("no pude medir el audio (¿falta ffprobe?); me salto el final de la cancion")
    report["duracion_audio_s"] = round(duration, 2) if duration else None

    declared = int(ini.get("song_length", 0) or 0) / 1000.0
    if duration and declared and abs(declared - duration) > 2.0:
        warnings.append(f"song.ini dice {declared:.1f} s y el audio dura {duration:.1f} s")

    # --- lo que hace falta para que se pueda JUGAR ------------------------
    for name, track in sorted(chart.tracks.items()):
        notes = [n for n in track.notes if n.fret not in (FLAG_FORCE, FLAG_TAP)]
        if not notes:
            continue
        ticks = sorted({n.tick for n in notes})
        first = chart.tick_to_seconds(ticks[0])
        last = chart.tick_to_seconds(max(n.tick + n.sustain for n in notes))

        if first < LEAD_IN_WARN_S:
            errors.append(
                f"{name}: la primera nota cae en {first:.2f} s; la autopista no ha "
                f"bajado nada todavia (el humano no baja de 2.0 s)"
            )
        if duration and last > duration + 0.05:
            errors.append(
                f"{name}: la ultima nota acaba en {last:.1f} s y el audio en "
                f"{duration:.1f} s; la cancion termina con la nota pulsada"
            )

        phrases = sorted([s for s in track.specials if s.kind == 2], key=lambda s: s.tick)
        empty = sum(
            1 for p in phrases
            if not any(p.tick <= t < p.tick + p.length for t in ticks)
        )
        overlapped = sum(
            1 for a, b in zip(phrases, phrases[1:]) if b.tick < a.tick + a.length
        )
        if empty:
            errors.append(f"{name}: {empty} frases de Star Power sin ninguna nota dentro")
        if overlapped:
            errors.append(f"{name}: {overlapped} frases de Star Power solapadas")
        if len(phrases) < SP_MIN_PHRASES:
            warnings.append(
                f"{name}: {len(phrases)} frases de Star Power; hacen falta "
                f"{SP_MIN_PHRASES} para poder activarlo una vez"
            )

        sustains = [n.sustain / chart.resolution for n in notes if n.sustain > 0]
        report["pistas"][name] = {
            "notas": len(ticks),
            "gemas": len(notes),
            "primera_nota_s": round(first, 2),
            "ultima_nota_s": round(last, 2),
            "sp_frases": len(phrases),
            "sostenido_p50_tiempos": (
                round(sorted(sustains)[len(sustains) // 2], 3) if sustains else 0.0
            ),
        }

    # --- que las dificultades bajas sean la misma cancion ------------------
    expert = chart.tracks.get("ExpertSingle")
    if expert:
        expert_map: dict[int, set[int]] = {}
        for note in expert.notes:
            if note.fret < 5:
                expert_map.setdefault(note.tick, set()).add(note.fret)
        for name in ("HardSingle", "MediumSingle", "EasySingle"):
            track = chart.tracks.get(name)
            if not track:
                continue
            own: dict[int, set[int]] = {}
            for note in track.notes:
                if note.fret < 5:
                    own.setdefault(note.tick, set()).add(note.fret)
            if not own:
                continue
            shared = [t for t in own if t in expert_map]
            same_fret = sum(1 for t in shared if own[t] & expert_map[t])
            report["pistas"].setdefault(name, {})["coincide_con_experto"] = {
                "posicion_pct": round(100 * len(shared) / len(own), 1),
                "traste_pct": round(100 * same_fret / max(1, len(shared)), 1),
            }

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ruta", help="Carpeta generada, o una carpeta que las contenga")
    parser.add_argument("--json", action="store_true", help="Sacar el informe en JSON")
    args = parser.parse_args()

    root = Path(args.ruta)
    if not root.exists():
        print(f"[X] No existe: {root}")
        return 2
    folders = (
        [root] if (root / "notes.chart").is_file()
        else sorted(p for p in root.iterdir() if p.is_dir() and (p / "notes.chart").is_file())
    )
    if not folders:
        print(f"[X] No hay ninguna carpeta con notes.chart en {root}")
        return 2

    bad = 0
    for folder in folders:
        report = check_folder(folder)
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
            bad += 1 if report["errores"] else 0
            continue

        print(f"\n[*] {report['carpeta']}")
        for name, data in report["pistas"].items():
            coincide = data.get("coincide_con_experto")
            extra = (
                f"  = Experto {coincide['posicion_pct']}% pos / {coincide['traste_pct']}% traste"
                if coincide else ""
            )
            if "notas" in data:
                print(
                    f"     {name:14} {data['notas']:4} notas  "
                    f"1a {data['primera_nota_s']:6.2f}s  ult {data['ultima_nota_s']:7.2f}s  "
                    f"SP {data['sp_frases']:3}  sost {data['sostenido_p50_tiempos']:5.2f}t{extra}"
                )
        for warning in report["avisos"]:
            print(f"     [!] {warning}")
        for error in report["errores"]:
            print(f"     [X] {error}")
        if report["errores"]:
            bad += 1
        else:
            print("     [OK] cargable y jugable de principio a fin.")

    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
