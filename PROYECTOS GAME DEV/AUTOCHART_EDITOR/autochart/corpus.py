"""Mine the local Clone Hero library for what a *human-made* chart looks like.

This is the part that gives the generator its taste. Instead of inventing rules
from scratch, we measure ~1000 charts made by real charters and record the
distributions the generator should land inside: how dense a chart is at a given
BPM, how often notes are chords, how far consecutive frets jump, how long
sustains run, which three-note shapes actually show up.

Everything here is read-only. The library is never modified.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from . import atlas, chartio, midiio

# Subdivisions we test a note against, expressed in quarter-note fractions.
GRID_DIVISIONS = (1, 2, 3, 4, 6, 8, 12, 16)


@dataclass
class ChartStats:
    """Measurements taken from one difficulty of one song."""

    song: str = ""
    source: str = ""
    difficulty: str = "Expert"
    bpm: float = 0.0
    duration_s: float = 0.0
    note_count: int = 0  # chord-groups, not individual gems
    gem_count: int = 0
    notes_per_second: float = 0.0
    notes_per_beat: float = 0.0
    chord_ratio: float = 0.0
    chord_sizes: dict[int, int] = field(default_factory=dict)
    open_ratio: float = 0.0
    sustain_ratio: float = 0.0
    sustain_beats: list[float] = field(default_factory=list)
    fret_histogram: dict[int, int] = field(default_factory=dict)
    interval_histogram: dict[int, int] = field(default_factory=dict)
    repeat_ratio: float = 0.0
    grid_histogram: dict[int, int] = field(default_factory=dict)
    trigram_counts: dict[str, int] = field(default_factory=dict)
    star_power_phrases: int = 0
    # Cuando dos notas van seguidas (hueco corto), cuantas veces el charter
    # cambia de traste. Es la vara con la que se calibra `ALTERNANCIA_PROB`.
    cambio_seguidas: float = 0.0
    seguidas: int = 0
    genero_crudo: str = ""
    genero: str = "sin_clasificar"


# Hueco maximo para considerar que dos notas van "seguidas", en tiempos.
# Es el mismo numero que usa el generador (`generate.ALTERNANCIA_HUECO`).
HUECO_SEGUIDAS = 0.55


def _group_by_tick(notes) -> list[tuple[int, list[int], int]]:
    """Collapse note events into (tick, frets, sustain) chord groups."""
    groups: dict[int, list] = {}
    for note in notes:
        fret = note.fret
        if fret in (chartio.FLAG_FORCE, chartio.FLAG_TAP):
            continue
        groups.setdefault(note.tick, []).append((fret, note.sustain))
    out = []
    for tick in sorted(groups):
        frets = sorted(f for f, _ in groups[tick])
        sustain = max(s for _, s in groups[tick])
        out.append((tick, frets, sustain))
    return out


def _grid_division(tick: int, resolution: int) -> int:
    """Finest subdivision the tick lands on, or 0 when it is off-grid."""
    for division in GRID_DIVISIONS:
        step = resolution / division
        if step <= 0:
            continue
        offset = tick % step
        if min(offset, step - offset) <= max(1.0, resolution * 0.01):
            return division
    return 0


def _measure(
    groups: list[tuple[int, list[int], int]],
    resolution: int,
    tick_to_seconds,
    bpm: float,
) -> ChartStats:
    stats = ChartStats(bpm=bpm)
    if len(groups) < 8:
        return stats

    first_s = tick_to_seconds(groups[0][0])
    last_s = tick_to_seconds(groups[-1][0])
    stats.duration_s = max(1e-6, last_s - first_s)
    stats.note_count = len(groups)
    stats.gem_count = sum(len(frets) for _, frets, _ in groups)
    stats.notes_per_second = stats.note_count / stats.duration_s
    stats.notes_per_beat = stats.notes_per_second * 60.0 / max(bpm, 1.0)

    chords = 0
    opens = 0
    sustains = 0
    chord_sizes: Counter[int] = Counter()
    frets_hist: Counter[int] = Counter()
    intervals: Counter[int] = Counter()
    grid: Counter[int] = Counter()
    trigrams: Counter[str] = Counter()
    repeats = 0

    singles: list[tuple[int, int]] = []  # (tick, fret) for single-note groups
    for tick, frets, sustain in groups:
        size = len(frets)
        chord_sizes[size] += 1
        if size > 1:
            chords += 1
        if chartio.FRET_OPEN in frets:
            opens += 1
        if sustain >= resolution * chartio.SOSTENIDO_MIN_TIEMPOS:
            sustains += 1
            stats.sustain_beats.append(round(sustain / resolution, 3))
        for fret in frets:
            frets_hist[fret] += 1
        grid[_grid_division(tick, resolution)] += 1
        if size == 1 and frets[0] <= chartio.FRET_ORANGE:
            singles.append((tick, frets[0]))

    seguidas = 0
    cambios = 0
    for (tick_a, a), (tick_b, b) in zip(singles, singles[1:]):
        intervals[b - a] += 1
        if a == b:
            repeats += 1
        if (tick_b - tick_a) / max(1, resolution) <= HUECO_SEGUIDAS:
            seguidas += 1
            if a != b:
                cambios += 1
    for a, b, c in zip(singles, singles[1:], singles[2:]):
        trigrams[f"{a[1]}{b[1]}{c[1]}"] += 1

    total = len(groups)
    stats.chord_ratio = chords / total
    stats.open_ratio = opens / total
    stats.sustain_ratio = sustains / total
    stats.chord_sizes = dict(chord_sizes)
    stats.fret_histogram = dict(frets_hist)
    stats.interval_histogram = dict(intervals)
    stats.grid_histogram = dict(grid)
    stats.trigram_counts = dict(trigrams.most_common(40))
    stats.repeat_ratio = repeats / max(1, len(singles) - 1)
    stats.seguidas = seguidas
    stats.cambio_seguidas = cambios / seguidas if seguidas else 0.0
    return stats


def analyse_chart_file(path: Path, difficulty: str = "Expert") -> ChartStats | None:
    chart = chartio.parse_chart(path)
    track = chart.tracks.get(f"{difficulty}Single")
    if track is None or len(track.notes) < 16:
        return None
    groups = _group_by_tick(track.notes)
    bpm = _median([t.bpm for t in chart.tempos] or [120.0])
    stats = _measure(groups, chart.resolution, chart.tick_to_seconds, bpm)
    stats.difficulty = difficulty
    stats.source = "chart"
    stats.star_power_phrases = len([s for s in track.specials if s.kind == 2])
    return stats if stats.note_count else None


def analyse_midi_file(path: Path, difficulty: str = "Expert") -> ChartStats | None:
    chart = midiio.parse_midi(path)
    notes = chart.tracks.get(difficulty)
    if not notes or len(notes) < 16:
        return None
    groups = _group_by_tick(notes)
    bpm = _median([bpm for _, bpm in chart.tempos] or [120.0])
    stats = _measure(groups, chart.resolution, chart.tick_to_seconds, bpm)
    stats.difficulty = difficulty
    stats.source = "midi"
    stats.star_power_phrases = len(chart.star_power.get("all", []))
    return stats if stats.note_count else None


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _leer_genero(carpeta: Path) -> str:
    """La etiqueta `genre` de `song.ini`, o cadena vacia si no hay."""
    from .export import read_song_ini

    try:
        return read_song_ini(carpeta).get("genre", "")
    except Exception:  # una ini rota no puede parar el escaneo
        return ""


def cargar_oro(ruta: str | Path) -> set[tuple[str, str]]:
    """Los `(pack, cancion)` que pasaron los filtros de `tools/elegir_oro.py`."""
    import json

    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return {(c.get("pack", ""), c["cancion"])
            for c in datos.get("canciones", []) if c.get("oro")}


def scan_library(
    songs_dir: str | Path,
    difficulty: str = "Expert",
    limit: int | None = None,
    on_progress=None,
    solo_oro: set[tuple[str, str]] | None = None,
) -> list[ChartStats]:
    """Walk a Clone Hero `Songs` folder and measure every chart it can read.

    Con `solo_oro` se mide unicamente el corpus de oro. Hace falta porque el
    perfil que usa el generador sale hoy de TODOS los charts, o sea de la
    mediana de lo mediano: medido, el oro esta en 4.18 notas/s contra 3.70, y
    en 29 % de acordes contra 34.8 %. Apuntar a la mediana global es apuntar a
    un chart que este proyecto ya tiene medido como plano.
    """
    root = Path(songs_dir)
    results: list[ChartStats] = []
    candidates: list[Path] = []
    for pattern in ("**/notes.chart", "**/notes.mid"):
        candidates.extend(sorted(root.glob(pattern)))

    seen_folders: set[Path] = set()
    for path in candidates:
        if limit is not None and len(results) >= limit:
            break
        if solo_oro is not None:
            carpeta = path.parent
            if (carpeta.parent.name, carpeta.name) not in solo_oro:
                continue
        # Prefer .chart when a folder has both.
        if path.suffix == ".mid" and path.parent in seen_folders:
            continue
        try:
            stats = (
                analyse_chart_file(path, difficulty)
                if path.suffix == ".chart"
                else analyse_midi_file(path, difficulty)
            )
        except Exception:  # a broken chart must never stop the scan
            stats = None
        if stats is None:
            continue
        seen_folders.add(path.parent)
        stats.song = path.parent.name
        stats.genero_crudo = _leer_genero(path.parent)
        stats.genero = atlas.normalizar_genero(stats.genero_crudo)
        results.append(stats)
        if on_progress is not None:
            on_progress(len(results), stats)
    return results


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

BPM_BUCKETS = ((0, 100), (100, 130), (130, 160), (160, 190), (190, 10_000))

# Cuantos charts hacen falta para que un genero tenga bloque propio.
MINIMO_POR_GENERO = 12


def _percentiles(values: list[float], points=(5, 25, 50, 75, 95)) -> dict[str, float]:
    if not values:
        return {f"p{p}": 0.0 for p in points}
    ordered = sorted(values)
    out = {}
    for point in points:
        index = min(len(ordered) - 1, max(0, int(round((point / 100.0) * (len(ordered) - 1)))))
        out[f"p{point}"] = round(ordered[index], 4)
    return out


def _merge_counter(dicts: list[dict], normalise: bool = True) -> dict[str, float]:
    total: Counter[str] = Counter()
    for item in dicts:
        for key, count in item.items():
            total[str(key)] += count
    grand = sum(total.values()) or 1
    if not normalise:
        return dict(total)
    return {key: round(count / grand, 5) for key, count in total.most_common()}


def aggregate(stats: list[ChartStats]) -> dict:
    """Turn per-song measurements into the profile the generator reads."""
    usable = [s for s in stats if s.note_count >= 32 and 30 <= s.bpm <= 400]
    profile: dict = {
        "charts_analysed": len(usable),
        "songs_seen": len(stats),
        "notes_per_second": _percentiles([s.notes_per_second for s in usable]),
        "notes_per_beat": _percentiles([s.notes_per_beat for s in usable]),
        "chord_ratio": _percentiles([s.chord_ratio for s in usable]),
        "open_ratio": _percentiles([s.open_ratio for s in usable]),
        "sustain_ratio": _percentiles([s.sustain_ratio for s in usable]),
        "repeat_ratio": _percentiles([s.repeat_ratio for s in usable]),
        "sustain_beats": _percentiles([b for s in usable for b in s.sustain_beats[:200]]),
        "chord_sizes": _merge_counter([s.chord_sizes for s in usable]),
        "fret_histogram": _merge_counter([s.fret_histogram for s in usable]),
        "interval_histogram": _merge_counter([s.interval_histogram for s in usable]),
        "grid_histogram": _merge_counter([s.grid_histogram for s in usable]),
        "trigrams": dict(Counter(_merge_counter([s.trigram_counts for s in usable], normalise=False)).most_common(60)),
        "cambio_seguidas": _percentiles([s.cambio_seguidas for s in usable if s.seguidas >= 20]),
        "by_bpm": {},
        "by_genre": {},
    }
    generos: dict[str, list[ChartStats]] = {}
    for s in usable:
        generos.setdefault(s.genero, []).append(s)
    for nombre, grupo in sorted(generos.items()):
        # Con menos de 12 charts la mediana de un genero es la de dos personas,
        # no la de un estilo: se deja fuera y esa cancion cae al perfil global.
        if nombre == "sin_clasificar" or len(grupo) < MINIMO_POR_GENERO:
            continue
        # Cada bloque lleva SU factor ya calculado contra la mediana de esta
        # misma tanda. Un genero no dice "4.49 notas/s", dice "un 21 % mas
        # denso que la mediana", y guardarlo asi es lo que permite:
        #   - aplicarlo sobre otro perfil (el del oro) sin mezclar poblaciones,
        #   - y juntar en un mismo perfil bloques venidos de dos minados
        #     distintos, que es lo que hace falta porque el oro son 60 charts y
        #     solo metal y rock llegan solos a los 12 del minimo.
        factores = {}
        for clave in ("notes_per_second", "chord_ratio", "repeat_ratio", "cambio_seguidas"):
            base = (profile.get(clave) or {}).get("p50") or 0.0
            propio = _percentiles([getattr(s, clave) for s in grupo
                                   if clave != "cambio_seguidas" or s.seguidas >= 20]).get("p50") or 0.0
            if base > 0 and propio > 0:
                factores[clave] = round(propio / base, 4)
        profile["by_genre"][nombre] = {
            "songs": len(grupo),
            "factores": factores,
            "medido_sobre": len(usable),
            "notes_per_second": _percentiles([s.notes_per_second for s in grupo]),
            "notes_per_beat": _percentiles([s.notes_per_beat for s in grupo]),
            "chord_ratio": _percentiles([s.chord_ratio for s in grupo]),
            "sustain_ratio": _percentiles([s.sustain_ratio for s in grupo]),
            "repeat_ratio": _percentiles([s.repeat_ratio for s in grupo]),
            "cambio_seguidas": _percentiles(
                [s.cambio_seguidas for s in grupo if s.seguidas >= 20]),
            "trigrams": dict(Counter(_merge_counter(
                [s.trigram_counts for s in grupo], normalise=False)).most_common(60)),
        }

    # La densidad, como RECTA sobre el BPM y no como cinco escalones. Medido
    # sobre los 392 charts humanos, contra la densidad que escribio cada persona:
    #
    #   todos la mediana (la regla tonta)     error 1.002   corr    --    1.0x
    #   bucket de BPM (5 tramos)              error 0.902   corr +0.398   1.5x
    #   recta sobre el BPM                    error 0.903   corr +0.421   2.2x
    #   recta sobre el BPM + desvio de genero error 0.865   corr +0.481   2.7x
    #
    # Lo que importa no es solo el error sino el RANGO: el humano va de 1.75 a
    # 5.99 notas/s y los escalones solo saben decir 1.5 veces de diferencia.
    #
    # Se guarda como recta + desvios + la referencia de ESTA tanda, no como
    # niveles, para que el generador la aplique como factor sobre el perfil
    # activo -- que suele ser el del oro, otra poblacion. Misma razon que en
    # `by_genre`.
    con_bpm = [s for s in usable if s.bpm > 0]
    if len(con_bpm) >= 30:
        xs = [s.bpm for s in con_bpm]
        ys = [s.notes_per_second for s in con_bpm]
        n = float(len(xs))
        media_x, media_y = sum(xs) / n, sum(ys) / n
        var_x = sum((x - media_x) ** 2 for x in xs)
        a = (sum((x - media_x) * (y - media_y) for x, y in zip(xs, ys)) / var_x
             if var_x > 0 else 0.0)
        b = media_y - a * media_x
        desvios: dict[str, float] = {}
        por_genero: dict[str, list[float]] = {}
        for s in con_bpm:
            por_genero.setdefault(s.genero, []).append(s.notes_per_second - (a * s.bpm + b))
        for nombre, resid in por_genero.items():
            if nombre != "sin_clasificar" and len(resid) >= MINIMO_POR_GENERO:
                desvios[nombre] = round(_median(resid), 4)
        profile["nps_por_bpm"] = {
            "a": round(a, 6),
            "b": round(b, 4),
            "referencia": round(media_y, 4),
            "medido_sobre": len(con_bpm),
            "genero": desvios,
        }

    for low, high in BPM_BUCKETS:
        bucket = [s for s in usable if low <= s.bpm < high]
        if len(bucket) < 3:
            continue
        profile["by_bpm"][f"{low}-{high if high < 10_000 else 'inf'}"] = {
            "songs": len(bucket),
            "notes_per_second": _percentiles([s.notes_per_second for s in bucket]),
            "notes_per_beat": _percentiles([s.notes_per_beat for s in bucket]),
            "chord_ratio": _percentiles([s.chord_ratio for s in bucket]),
            "sustain_ratio": _percentiles([s.sustain_ratio for s in bucket]),
        }
    return profile


def save_profile(profile: dict, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    return destination


def load_profile(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
