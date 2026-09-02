"""Read and write Clone Hero `.chart` files (Moonscraper text format).

The format is a small INI-like structure: named sections, each wrapped in
braces, holding `tick = <event>` lines.

    [Song]        metadata (Name, Resolution, MusicStream, ...)
    [SyncTrack]   tempo (`B`) and time signature (`TS`) changes
    [Events]      global events, mainly `E "section <name>"`
    [<Diff><Instrument>]  note tracks, e.g. `ExpertSingle`

Note lines inside a track:

    768 = N 0 0      note on fret 0 (green), no sustain
    768 = N 5 0      "forced" flag  -> flips natural HOPO/strum state
    768 = N 6 0      "tap" flag
    768 = N 7 0      open note
    768 = S 2 1920   star power phrase, 1920 ticks long
    768 = E solo     track-local text event
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Fret ids as they appear on disk.
FRET_GREEN = 0
FRET_RED = 1
FRET_YELLOW = 2
FRET_BLUE = 3
FRET_ORANGE = 4
FLAG_FORCE = 5
FLAG_TAP = 6
FRET_OPEN = 7

# Cuanto tiene que durar una nota para contar como SOSTENIDO. Vive aqui, con
# `is_natural_hopo`, porque es una regla de lectura del chart y la tienen que
# usar los dos lados: el que mide la biblioteca y el que escribe.
#
# Medido el 23-08-2026 sobre los 392 charts humanos, y no es un gusto: es el
# unico umbral con el que las dos maneras de escribir un chart dicen lo mismo.
# Los `.mid` (rips convertidos) le dan duracion a TODA nota, asi que a 0.25
# tiempos su mediana de sostenidos sale 1.61 veces la de los `.chart` hechos a
# mano -- y el largo mediano de "sostenido" de un `.mid` es 0.250 tiempos
# clavados, o sea el propio umbral.
#
#     umbral   .chart   .mid   razon
#      0.25    0.1264  0.2036   1.61
#      0.50    0.1117  0.1056   0.95   <- aqui coinciden
#      0.75    0.0685  0.0856   1.25
#      1.00    0.0324  0.0440   1.36
#
# A 0.25 el p95 del corpus era 0.9552, o sea "el 95 % de las notas sostenidas",
# que no describe ningun chart que nadie haya tocado.
SOSTENIDO_MIN_TIEMPOS = 0.5

DIFFICULTIES = ("Easy", "Medium", "Hard", "Expert")
INSTRUMENTS = ("Single", "DoubleBass", "DoubleRhythm", "DoubleGuitar", "Keyboard")

_SECTION_RE = re.compile(r"^\s*\[(?P<name>[^\]]+)\]\s*$")
_ENTRY_RE = re.compile(r"^\s*(?P<tick>\d+)\s*=\s*(?P<body>.+?)\s*$")
_META_RE = re.compile(r"^\s*(?P<key>[A-Za-z0-9_]+)\s*=\s*(?P<value>.*?)\s*$")


@dataclass
class Note:
    """A single playable event on a track."""

    tick: int
    fret: int
    sustain: int = 0

    @property
    def is_flag(self) -> bool:
        return self.fret in (FLAG_FORCE, FLAG_TAP)


@dataclass
class NoteGroup:
    """Todo lo que cae en el mismo tick: un golpe, con sus marcas."""

    tick: int
    frets: tuple[int, ...]
    forced: bool = False
    tap: bool = False

    @property
    def is_chord(self) -> bool:
        return len(self.frets) > 1


# Cuando el juego liga una nota SIN que nadie se lo diga. Copiado de Moonscraper
# (`Note.IsNaturalHopo`), que es de donde lo toma Clone Hero: 65 ticks a
# resolucion 192, o sea algo mas de un tresillo de corchea. Entre 64 (el
# tresillo) y 96 (la corchea recta) no hay nada en la rejilla, asi que el numero
# exacto no es delicado.
HOPO_TICKS_AT_192 = 65


def hopo_distance(resolution: int) -> float:
    return HOPO_TICKS_AT_192 * resolution / 192.0


def group_notes(notes: list[Note]) -> list[NoteGroup]:
    """Juntar las notas por tick y separar las marcas de las notas de verdad."""
    buckets: dict[int, list[Note]] = {}
    for note in notes:
        buckets.setdefault(note.tick, []).append(note)
    groups: list[NoteGroup] = []
    for tick in sorted(buckets):
        entries = buckets[tick]
        frets = tuple(sorted({n.fret for n in entries if n.fret not in (FLAG_FORCE, FLAG_TAP)}))
        if not frets:
            continue  # una marca huerfana, sin nota debajo
        groups.append(NoteGroup(
            tick=tick,
            frets=frets,
            forced=any(n.fret == FLAG_FORCE for n in entries),
            tap=any(n.fret == FLAG_TAP for n in entries),
        ))
    return groups


def is_natural_hopo(previous: NoteGroup | None, current: NoteGroup, threshold: float) -> bool:
    """Lo que decide el juego solo, sin ninguna marca escrita.

    Tiene que ser una nota suelta, caer cerca de la anterior, y no ser la misma
    que la anterior. Un acorde no es nunca ligadura natural.
    """
    if previous is None or current.is_chord:
        return False
    if current.tick - previous.tick > threshold:
        return False
    if previous.is_chord:
        return True
    return current.frets != previous.frets


def hopo_ratio(notes: list[Note], resolution: int) -> float:
    """Que fraccion de los golpes se toca SIN rasguear, ya contando las marcas.

    Es lo que siente la mano, y no es lo mismo que la ligadura natural: la marca
    `N 5` invierte lo que decidio el juego y el tap se toca suelto siempre.
    """
    groups = group_notes(notes)
    if not groups:
        return 0.0
    threshold = hopo_distance(resolution)
    ligadas = 0
    previous: NoteGroup | None = None
    for group in groups:
        natural = is_natural_hopo(previous, group, threshold)
        ligadas += int(group.tap or (natural != group.forced))
        previous = group
    return ligadas / len(groups)


@dataclass
class SpecialPhrase:
    tick: int
    kind: int  # 2 = star power
    length: int


@dataclass
class Track:
    """One difficulty of one instrument."""

    difficulty: str
    instrument: str
    notes: list[Note] = field(default_factory=list)
    specials: list[SpecialPhrase] = field(default_factory=list)
    events: list[tuple[int, str]] = field(default_factory=list)

    @property
    def name(self) -> str:
        return f"{self.difficulty}{self.instrument}"


@dataclass
class TempoEvent:
    tick: int
    bpm: float  # real beats per minute (the file stores bpm * 1000)


@dataclass
class TimeSignature:
    tick: int
    numerator: int
    denominator: int = 4


@dataclass
class Chart:
    metadata: dict[str, str] = field(default_factory=dict)
    resolution: int = 192
    tempos: list[TempoEvent] = field(default_factory=list)
    time_signatures: list[TimeSignature] = field(default_factory=list)
    events: list[tuple[int, str]] = field(default_factory=list)
    tracks: dict[str, Track] = field(default_factory=dict)

    # -- time helpers -----------------------------------------------------
    def tick_to_seconds(self, tick: int) -> float:
        """Convert a tick position to seconds using the tempo map."""
        tempos = self.tempos or [TempoEvent(0, 120.0)]
        seconds = 0.0
        prev_tick = 0
        prev_bpm = tempos[0].bpm
        for tempo in tempos:
            if tempo.tick >= tick:
                break
            seconds += (tempo.tick - prev_tick) / self.resolution * (60.0 / prev_bpm)
            prev_tick, prev_bpm = tempo.tick, tempo.bpm
        seconds += (tick - prev_tick) / self.resolution * (60.0 / prev_bpm)
        return seconds

    def seconds_to_tick(self, seconds: float) -> int:
        """Inverse of :meth:`tick_to_seconds`, rounded to the nearest tick."""
        tempos = self.tempos or [TempoEvent(0, 120.0)]
        elapsed = 0.0
        prev_tick = 0
        prev_bpm = tempos[0].bpm
        for tempo in tempos[1:]:
            span = (tempo.tick - prev_tick) / self.resolution * (60.0 / prev_bpm)
            if elapsed + span >= seconds:
                break
            elapsed += span
            prev_tick, prev_bpm = tempo.tick, tempo.bpm
        remaining = seconds - elapsed
        return int(round(prev_tick + remaining * prev_bpm / 60.0 * self.resolution))


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _split_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    buffer: list[str] = []
    depth = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = _SECTION_RE.match(line)
        if match and depth == 0:
            current = match.group("name")
            buffer = []
            sections[current] = buffer
            continue
        if line == "{":
            depth += 1
            continue
        if line == "}":
            depth = max(0, depth - 1)
            current = None
            continue
        if current is not None:
            buffer.append(line)
    return sections


def parse_chart(path: str | Path) -> Chart:
    """Parse a `.chart` file. Unknown sections are kept as extra tracks."""
    raw = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:  # pragma: no cover - latin-1 never fails
        text = raw.decode("latin-1", errors="replace")

    chart = Chart()
    sections = _split_sections(text)

    for line in sections.get("Song", []):
        match = _META_RE.match(line)
        if not match:
            continue
        key = match.group("key")
        value = match.group("value").strip().strip('"')
        chart.metadata[key] = value
    try:
        chart.resolution = int(float(chart.metadata.get("Resolution", 192)))
    except ValueError:
        chart.resolution = 192
    if chart.resolution <= 0:
        chart.resolution = 192

    for line in sections.get("SyncTrack", []):
        match = _ENTRY_RE.match(line)
        if not match:
            continue
        tick = int(match.group("tick"))
        parts = match.group("body").split()
        if not parts:
            continue
        if parts[0] == "B" and len(parts) >= 2:
            chart.tempos.append(TempoEvent(tick, int(parts[1]) / 1000.0))
        elif parts[0] == "TS" and len(parts) >= 2:
            denominator = 2 ** int(parts[2]) if len(parts) >= 3 else 4
            chart.time_signatures.append(TimeSignature(tick, int(parts[1]), denominator))

    for line in sections.get("Events", []):
        match = _ENTRY_RE.match(line)
        if not match:
            continue
        body = match.group("body")
        if body.startswith("E "):
            chart.events.append((int(match.group("tick")), body[2:].strip().strip('"')))

    for name, lines in sections.items():
        if name in ("Song", "SyncTrack", "Events"):
            continue
        difficulty = next((d for d in DIFFICULTIES if name.startswith(d)), "")
        instrument = name[len(difficulty):] if difficulty else name
        track = Track(difficulty=difficulty or name, instrument=instrument)
        for line in lines:
            match = _ENTRY_RE.match(line)
            if not match:
                continue
            tick = int(match.group("tick"))
            parts = match.group("body").split()
            if not parts:
                continue
            kind = parts[0]
            if kind == "N" and len(parts) >= 3:
                track.notes.append(Note(tick, int(parts[1]), int(parts[2])))
            elif kind == "S" and len(parts) >= 3:
                track.specials.append(SpecialPhrase(tick, int(parts[1]), int(parts[2])))
            elif kind == "E":
                track.events.append((tick, " ".join(parts[1:]).strip('"')))
        chart.tracks[name] = track

    chart.tempos.sort(key=lambda t: t.tick)
    chart.time_signatures.sort(key=lambda t: t.tick)
    if not chart.tempos:
        chart.tempos.append(TempoEvent(0, 120.0))
    return chart


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------

_SONG_KEY_ORDER = (
    "Name", "Artist", "Charter", "Album", "Year", "Offset", "Resolution",
    "Player2", "Difficulty", "PreviewStart", "PreviewEnd", "Genre",
    "MediaType", "MusicStream", "GuitarStream", "RhythmStream", "BassStream",
    "DrumStream",
)
_UNQUOTED_KEYS = {"Offset", "Resolution", "Difficulty", "PreviewStart", "PreviewEnd", "Player2"}


def write_chart(chart: Chart, path: str | Path) -> Path:
    """Serialise `chart` to disk and return the written path."""
    out: list[str] = []

    out.append("[Song]")
    out.append("{")
    metadata = dict(chart.metadata)
    metadata["Resolution"] = str(chart.resolution)
    ordered = [k for k in _SONG_KEY_ORDER if k in metadata]
    ordered += [k for k in metadata if k not in _SONG_KEY_ORDER]
    for key in ordered:
        value = metadata[key]
        if key in _UNQUOTED_KEYS:
            out.append(f"  {key} = {value}")
        else:
            out.append(f'  {key} = "{value}"')
    out.append("}")

    out.append("[SyncTrack]")
    out.append("{")
    sync: list[tuple[int, int, str]] = []
    for ts in chart.time_signatures:
        # Denominator is stored as its base-2 logarithm; 4 is the implicit default.
        if ts.denominator == 4:
            sync.append((ts.tick, 0, f"TS {ts.numerator}"))
        else:
            sync.append((ts.tick, 0, f"TS {ts.numerator} {int(ts.denominator).bit_length() - 1}"))
    for tempo in chart.tempos:
        sync.append((tempo.tick, 1, f"B {int(round(tempo.bpm * 1000))}"))
    for tick, _, body in sorted(sync, key=lambda item: (item[0], item[1])):
        out.append(f"  {tick} = {body}")
    out.append("}")

    out.append("[Events]")
    out.append("{")
    for tick, text in sorted(chart.events, key=lambda item: item[0]):
        out.append(f'  {tick} = E "{text}"')
    out.append("}")

    def track_sort_key(name: str) -> tuple[int, int]:
        difficulty = next((d for d in DIFFICULTIES if name.startswith(d)), "")
        return (
            INSTRUMENTS.index(name[len(difficulty):]) if name[len(difficulty):] in INSTRUMENTS else 99,
            DIFFICULTIES.index(difficulty) if difficulty in DIFFICULTIES else 99,
        )

    for name in sorted(chart.tracks, key=track_sort_key):
        track = chart.tracks[name]
        out.append(f"[{name}]")
        out.append("{")
        entries: list[tuple[int, int, str]] = []
        for phrase in track.specials:
            entries.append((phrase.tick, 0, f"S {phrase.kind} {phrase.length}"))
        for tick, text in track.events:
            entries.append((tick, 1, f"E {text}"))
        for note in track.notes:
            entries.append((note.tick, 2 + note.fret, f"N {note.fret} {note.sustain}"))
        for tick, _, body in sorted(entries, key=lambda item: (item[0], item[1])):
            out.append(f"  {tick} = {body}")
        out.append("}")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(out) + "\n", encoding="utf-8")
    return destination
