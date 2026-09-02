"""Banco de pruebas: genera charts para varias canciones y los puntua.

Para cada cancion de la muestra hace el ciclo completo -- analizar, generar,
validar y comparar contra el chart humano -- y saca una tabla y un JSON con los
numeros. Es la forma de saber si un cambio en el generador mejora o empeora,
en vez de opinar mirando una sola cancion.

**Lo que este banco NO mide.** El F1 compara *cuando* suena cada nota, no *que
traste* le toca. Un cambio en la asignacion de trastes puede mejorar o arruinar
la sensacion del patron y este numero no se movera ni una milesima -- se
comprobo midiendolo: subir las repeticiones de traste del 12.5 % al 24.5 % dejo
el F1 clavado en 0.648. Para juzgar el patron estan `tools/ver_patron.py` y las
distribuciones del corpus, no esto.

Uso:
    python tools/banco.py --muestra 10
    python tools/banco.py --muestra 10 --salida salida/banco.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autochart.audio import analyse, pick_audio, pick_beat_audio  # noqa: E402
from autochart.corpus import load_profile  # noqa: E402
from autochart.export import export_song, read_song_ini  # noqa: E402
from autochart.generate import generate_chart  # noqa: E402
from autochart.validate import validate_chart  # noqa: E402
from comparar_humano import (  # noqa: E402
    best_offset, generated_note_times, human_note_times, match_ratio,
)

DEFAULT_LIBRARY = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
DEFAULT_PROFILE = Path(__file__).resolve().parent.parent / "datos" / "perfil_corpus.json"


def is_generated(path: Path) -> bool:
    """¿Este chart lo escribio AutoChart?

    En cuanto se copia un chart generado a la biblioteca para jugarlo, pasan dos
    cosas malas si no se filtra: el banco puede puntuarse contra su propia salida
    creyendo que es humana, y -- peor -- la muestra se desplaza. `pick_songs`
    coge una carpeta de cada N, asi que **una sola carpeta nueva cambia las 24
    canciones** y los numeros dejan de ser comparables con los de ayer. Paso:
    una tirada dio F1 0.641 contra 0.668 y no era el generador, era la muestra.
    """
    if "(autochart)" in path.name.lower():
        return True
    ini = path / "song.ini"
    if ini.is_file():
        try:
            text = ini.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            return False
        for line in text.splitlines():
            if line.strip().startswith("charter") and "autochart" in line:
                return True
    return False


def pick_songs(library: Path, sample: int) -> list[Path]:
    """Spread the sample across the library instead of taking the first N."""
    # OJO: la biblioteca esta en packs numerados (`01_Guitar Hero 1`, ...), asi
    # que las canciones NO estan en el primer nivel. Mirando solo `iterdir()`
    # esto devolvia CERO canciones y el banco daba f1 0.0 sin quejarse -- un
    # fallo silencioso que dejo el control sin medir desde la reorganizacion.
    candidatas = {p.parent for patron in ("**/notes.chart", "**/notes.mid")
                  for p in library.glob(patron)}
    folders = []
    for path in sorted(candidatas):
        if is_generated(path):
            continue
        if pick_audio(path) is not None:
            folders.append(path)
    if not folders or sample >= len(folders):
        return folders
    step = len(folders) / sample
    return [folders[int(index * step)] for index in range(sample)]


def run_one(
    song_dir: Path,
    output_root: Path,
    profile: dict | None,
    source: str = "guitarra",
    density: float = 1.0,
    percentile: str = "p50",
) -> dict:
    started = time.time()
    beat_path = pick_beat_audio(song_dir)
    # "mezcla" ignora el stem de guitarra a proposito: es el caso real de una
    # cancion nueva, que llega como un mp3 suelto y sin pistas separadas.
    audio_path = beat_path if source == "mezcla" else pick_audio(song_dir)
    beat_path = beat_path or audio_path
    info = read_song_ini(song_dir)
    name = info.get("name") or song_dir.name
    artist = info.get("artist") or "Desconocido"

    analysis = analyse(audio_path, beat_audio_path=beat_path)
    chart, report = generate_chart(
        analysis, metadata={"Name": name, "Artist": artist}, profile=profile,
        difficulties=("Expert",), density=density, density_percentile=percentile,
    )
    destination = output_root / f"{song_dir.name} (AutoChart)"
    export_song(
        chart, destination, audio_path, source_dir=None, name=name, artist=artist,
        duration_s=analysis.duration, copy_all_stems=False, copy_audio=False,
    )
    check = validate_chart(chart, profile)

    mine = generated_note_times(destination)
    theirs = human_note_times(song_dir)
    offset = best_offset(theirs, mine) if theirs.size and mine.size else 0.0
    recall = match_ratio(theirs + offset, mine) if theirs.size and mine.size else 0.0
    precision = match_ratio(mine, theirs + offset) if theirs.size and mine.size else 0.0
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)

    metrics = check.metrics.get("ExpertSingle", {})
    human_span = float(theirs[-1] - theirs[0]) if theirs.size > 1 else 1.0
    return {
        "cancion": song_dir.name,
        "audio": audio_path.name,
        "tempo": report.tempo,
        "duracion_s": round(analysis.duration, 1),
        "notas_generadas": metrics.get("notas", 0),
        "notas_humanas": int(theirs.size),
        "nps_generado": metrics.get("notas_por_segundo", 0.0),
        "nps_humano": round(theirs.size / human_span, 2) if theirs.size > 1 else 0.0,
        "acordes": metrics.get("acordes", 0.0),
        "sostenidos": metrics.get("sostenidos", 0.0),
        "desfase_ms": round(offset * 1000, 0),
        "recall": round(recall, 3),
        "precision": round(precision, 3),
        "f1": round(f1, 3),
        "errores": check.errors,
        "avisos": check.warnings,
        "segundos": round(time.time() - started, 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Banco de pruebas de AutoChart")
    parser.add_argument("--biblioteca", default=str(DEFAULT_LIBRARY))
    parser.add_argument("--muestra", type=int, default=10)
    parser.add_argument("--perfil", default=str(DEFAULT_PROFILE))
    parser.add_argument("--salida", default="salida/banco.json")
    parser.add_argument("--trabajo", default="salida/_banco")
    parser.add_argument(
        "--fuente", choices=("guitarra", "mezcla"), default="guitarra",
        help="'mezcla' fuerza song.ogg aunque exista el stem de guitarra",
    )
    parser.add_argument("--densidad", type=float, default=1.0)
    parser.add_argument("--percentil", default="p50", choices=("p25", "p50", "p75", "p95"))
    args = parser.parse_args()

    library = Path(args.biblioteca)
    profile = load_profile(args.perfil) if Path(args.perfil).is_file() else None
    songs = pick_songs(library, args.muestra)
    if not songs:
        # Un banco que mide CERO canciones imprimia su resumen con ceros tan
        # tranquilo, y asi estuvo semanas: el control decia 0.0 y nadie lo leia
        # como un fallo. Un numero falso es peor que un error.
        print("[X] CERO canciones elegibles: el banco no mide nada.")
        print("    Sus ceros parecerian un resultado, asi que no se escribe nada.")
        print("    Causas vistas: la biblioteca esta en packs y se miro solo el")
        print(f"    primer nivel, o la ruta no existe -> {library}")
        return 2
    output_root = Path(args.trabajo)
    print(f"[*] {len(songs)} canciones | perfil: {'si' if profile else 'no'} | "
          f"fuente: {args.fuente} | densidad: x{args.densidad} sobre {args.percentil}")

    rows: list[dict] = []
    for index, song in enumerate(songs, start=1):
        print(f"    [{index}/{len(songs)}] {song.name[:60]}")
        try:
            row = run_one(song, output_root, profile, args.fuente, args.densidad, args.percentil)
        except Exception as error:  # una cancion rota no tumba el banco
            print(f"        [X] {type(error).__name__}: {error}")
            traceback.print_exc(limit=2)
            rows.append({"cancion": song.name, "error": f"{type(error).__name__}: {error}"})
            continue
        rows.append(row)
        print(f"        F1 {row['f1']:.3f}  recall {row['recall']:.2f}  prec {row['precision']:.2f}  "
              f"{row['nps_generado']:.2f} n/s (humano {row['nps_humano']:.2f})  "
              f"{row['segundos']:.0f} s"
              + (f"  [{len(row['errores'])} ERRORES]" if row["errores"] else ""))

    ok = [r for r in rows if "error" not in r]
    summary = {
        "fuente": args.fuente,
        "densidad": args.densidad,
        "percentil": args.percentil,
        "canciones": len(rows),
        "ok": len(ok),
        "f1_medio": round(float(np.mean([r["f1"] for r in ok])), 3) if ok else 0.0,
        "f1_mediana": round(float(np.median([r["f1"] for r in ok])), 3) if ok else 0.0,
        "recall_medio": round(float(np.mean([r["recall"] for r in ok])), 3) if ok else 0.0,
        "precision_media": round(float(np.mean([r["precision"] for r in ok])), 3) if ok else 0.0,
        "nps_generado_medio": round(float(np.mean([r["nps_generado"] for r in ok])), 2) if ok else 0.0,
        "nps_humano_medio": round(float(np.mean([r["nps_humano"] for r in ok])), 2) if ok else 0.0,
        "charts_con_errores": sum(1 for r in ok if r["errores"]),
    }
    print("\n[RESUMEN]")
    for key, value in summary.items():
        print(f"    {key:<22} {value}")

    destination = Path(args.salida)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps({"resumen": summary, "canciones": rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"    guardado en {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
