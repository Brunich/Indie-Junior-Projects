"""Check a generated chart before it ever reaches the game.

Two kinds of finding:

* **error**   -- the chart is broken or unplayable (overlapping sustains,
  impossible spacing, out-of-range tempo). These must be fixed.
* **aviso**   -- the chart is legal but sits outside what the mined corpus says
  is normal (far too dense, no chords at all, a wall of sustains). These are
  judgement calls, not failures.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .chartio import Chart, FLAG_FORCE, FLAG_TAP

MIN_PLAYABLE_GAP_S = 0.045  # ~22 notes/second, past any human strumming hand
MAX_CHORD_SIZE = 4


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, dict] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def _percentile_range(profile: dict, key: str) -> tuple[float, float] | None:
    data = (profile or {}).get(key)
    if not isinstance(data, dict) or "p5" not in data:
        return None
    return float(data["p5"]), float(data["p95"])


def validate_chart(chart: Chart, profile: dict | None = None) -> ValidationReport:
    report = ValidationReport()

    if not chart.tempos:
        report.errors.append("El chart no tiene ningun evento de tempo.")
    for tempo in chart.tempos:
        if not (20.0 <= tempo.bpm <= 400.0):
            report.errors.append(f"BPM fuera de rango en el tick {tempo.tick}: {tempo.bpm:.2f}")
        if tempo.tick < 0:
            report.errors.append(f"Evento de tempo con tick negativo: {tempo.tick}")
    if chart.tempos != sorted(chart.tempos, key=lambda t: t.tick):
        report.errors.append("Los eventos de tempo no estan ordenados por tick.")

    if not chart.tracks:
        report.errors.append("El chart no tiene ninguna pista de notas.")

    for name, track in chart.tracks.items():
        notes = [n for n in track.notes if n.fret not in (FLAG_FORCE, FLAG_TAP)]
        if not notes:
            report.warnings.append(f"{name}: pista vacia.")
            continue

        groups: dict[int, list] = {}
        for note in notes:
            if note.tick < 0:
                report.errors.append(f"{name}: nota con tick negativo ({note.tick}).")
            if note.sustain < 0:
                report.errors.append(f"{name}: sostenido negativo en el tick {note.tick}.")
            groups.setdefault(note.tick, []).append(note)

        duplicates = 0
        for tick, group in groups.items():
            frets = [n.fret for n in group]
            if len(frets) != len(set(frets)):
                duplicates += 1
            if len(set(frets)) > MAX_CHORD_SIZE:
                report.errors.append(f"{name}: acorde de {len(set(frets))} notas en el tick {tick}.")
        if duplicates:
            report.errors.append(f"{name}: {duplicates} ticks con la misma nota repetida.")

        ticks = sorted(groups)
        times = {tick: chart.tick_to_seconds(tick) for tick in ticks}
        too_close = 0
        for previous, current in zip(ticks, ticks[1:]):
            if times[current] - times[previous] < MIN_PLAYABLE_GAP_S:
                too_close += 1
        if too_close:
            report.errors.append(
                f"{name}: {too_close} pares de notas separadas menos de {int(MIN_PLAYABLE_GAP_S * 1000)} ms."
            )

        # Star Power: una frase vacia o dos frases solapadas son cosas que el
        # juego se come sin avisar y dejan el medidor sin llenarse nunca.
        phrases = sorted([s for s in track.specials if s.kind == 2], key=lambda s: s.tick)
        empty = 0
        overlapped = 0
        previous_end = -1
        note_ticks = sorted(groups)
        for phrase in phrases:
            if not any(phrase.tick <= tick < phrase.tick + phrase.length for tick in note_ticks):
                empty += 1
            if phrase.tick < previous_end:
                overlapped += 1
            previous_end = phrase.tick + phrase.length
        if empty:
            report.errors.append(f"{name}: {empty} frases de Star Power sin ninguna nota dentro.")
        if overlapped:
            report.errors.append(f"{name}: {overlapped} frases de Star Power solapadas.")

        overlaps = 0
        by_fret: dict[int, list] = {}
        for note in notes:
            by_fret.setdefault(note.fret, []).append(note)
        for fret_notes in by_fret.values():
            fret_notes.sort(key=lambda n: n.tick)
            for current, following in zip(fret_notes, fret_notes[1:]):
                if current.tick + current.sustain > following.tick:
                    overlaps += 1
        if overlaps:
            report.errors.append(f"{name}: {overlaps} sostenidos que invaden la nota siguiente.")

        span = max(1e-6, times[ticks[-1]] - times[ticks[0]])
        chords = sum(1 for group in groups.values() if len({n.fret for n in group}) > 1)
        sustained = sum(1 for note in notes if note.sustain > 0)

        # How often the hand stays on the same fret. Real charters do this ~27 %
        # of the time; a generator that always moves feels restless.
        singles = [
            next(iter({n.fret for n in groups[tick]}))
            for tick in ticks
            if len({n.fret for n in groups[tick]}) == 1
        ]
        repeats = sum(1 for a, b in zip(singles, singles[1:]) if a == b)
        repeat_ratio = repeats / max(1, len(singles) - 1)

        metrics = {
            "notas": len(ticks),
            "gemas": len(notes),
            "duracion_s": round(span, 1),
            "notas_por_segundo": round(len(ticks) / span, 3),
            "acordes": round(chords / len(ticks), 3),
            "sostenidos": round(sustained / len(notes), 3),
            "repeticiones": round(repeat_ratio, 3),
            "star_power": len([s for s in track.specials if s.kind == 2]),
        }
        report.metrics[name] = metrics

        if profile and name == "ExpertSingle":
            for key, metric_key, label in (
                ("notes_per_second", "notas_por_segundo", "densidad"),
                ("chord_ratio", "acordes", "proporcion de acordes"),
                ("sustain_ratio", "sostenidos", "proporcion de sostenidos"),
                ("repeat_ratio", "repeticiones", "notas repetidas seguidas"),
            ):
                bounds = _percentile_range(profile, key)
                if not bounds:
                    continue
                low, high = bounds
                value = metrics[metric_key]
                if value < low or value > high:
                    report.warnings.append(
                        f"{name}: {label} = {value} queda fuera del rango humano "
                        f"({low}-{high}) medido en la biblioteca."
                    )
        if metrics["star_power"] == 0 and name in ("ExpertSingle", "HardSingle"):
            report.warnings.append(f"{name}: sin frases de Star Power.")

    return report
