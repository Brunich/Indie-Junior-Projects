"""Read `notes.mid` charts well enough to mine statistics from them.

Most of the library ships MIDI charts rather than `.chart` text files, and the
corpus miner needs both. This is deliberately a *reader* only: the generator
always writes `.chart`, which Clone Hero reads natively.

MIDI note-pitch layout for a five-fret track (`PART GUITAR`):

    Easy   60..64   Medium 72..76   Hard 84..88   Expert 96..100
    base+5 = forced HOPO, base+6 = forced strum, base+7 = open (some charters)
    104 = tap (no aparece ni una vez en esta biblioteca)
    103 = solo marker, 116 = star power / overdrive
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import mido

from . import chartio

DIFFICULTY_BASE = {"Easy": 60, "Medium": 72, "Hard": 84, "Expert": 96}
GUITAR_TRACK_NAMES = ("PART GUITAR", "T1 GEMS", "PART GUITAR COOP")

SOLO_PITCH = 103
STAR_POWER_PITCH = 116


@dataclass
class MidiNote:
    tick: int
    fret: int
    sustain: int


@dataclass
class MidiChart:
    resolution: int = 480
    tempos: list[tuple[int, float]] = field(default_factory=list)  # (tick, bpm)
    tracks: dict[str, list[MidiNote]] = field(default_factory=dict)
    star_power: dict[str, list[tuple[int, int]]] = field(default_factory=dict)

    def tick_to_seconds(self, tick: int) -> float:
        tempos = self.tempos or [(0, 120.0)]
        seconds = 0.0
        prev_tick, prev_bpm = 0, tempos[0][1]
        for at, bpm in tempos:
            if at >= tick:
                break
            seconds += (at - prev_tick) / self.resolution * (60.0 / prev_bpm)
            prev_tick, prev_bpm = at, bpm
        return seconds + (tick - prev_tick) / self.resolution * (60.0 / prev_bpm)


# Un `.mid` escribe DOS marcas distintas -- `base+5` obliga a ligar y `base+6`
# obliga a rasguear -- y un `.chart` escribe UNA, `N 5`, que invierte lo que el
# juego decidio solo. Hasta el 24-08-2026 este lector se quedaba con los cinco
# trastes y tiraba las dos: 84.462 marcas de 224 charts, y con ellas media regla.
# La ligadura mediana de la biblioteca .mid salia 0.106 cuando es 0.142, y contra
# los .chart (0.189) parecia que los dos formatos hablaban de cosas distintas --
# la misma trampa que costo el capitulo de los sostenidos.
#
# Las marcas caen justo sobre la nota el 100 % de las veces (84.454 de 84.462),
# asi que se casan por tick. Solo el 0.7 % abarca mas de una nota.
MARCA_LIGAR = 5
MARCA_RASGUEAR = 6


def _marcas_de_forzado(notas: list[MidiNote], ligar: set[int], rasguear: set[int],
                       resolution: int) -> list[MidiNote]:
    """Traducir las dos marcas del `.mid` a la unica del `.chart`.

    La marca solo se escribe cuando el charter CONTRADICE al juego, y quien dice
    lo que decide el juego es `chartio.is_natural_hopo` -- la misma funcion que
    usa el generador, a proposito: con dos copias, la medida acabaria dando por
    bueno lo que el juego no hace.
    """
    if not ligar and not rasguear:
        return []
    grupos = chartio.group_notes([chartio.Note(n.tick, n.fret, n.sustain) for n in notas])
    umbral = chartio.hopo_distance(resolution)
    marcas: list[MidiNote] = []
    previo = None
    for grupo in grupos:
        natural = chartio.is_natural_hopo(previo, grupo, umbral)
        if grupo.tick in ligar:
            final = True
        elif grupo.tick in rasguear:
            final = False
        else:
            final = natural
        if final != natural:
            marcas.append(MidiNote(grupo.tick, chartio.FLAG_FORCE, 0))
        previo = grupo
    return marcas


def _pick_guitar_track(midi: mido.MidiFile) -> mido.MidiTrack | None:
    named: dict[str, mido.MidiTrack] = {}
    for track in midi.tracks:
        name = ""
        for message in track:
            if message.type == "track_name":
                name = message.name.strip().upper()
                break
        if name:
            named[name] = track
    for candidate in GUITAR_TRACK_NAMES:
        if candidate in named:
            return named[candidate]
    for name, track in named.items():
        if "GUITAR" in name:
            return track
    return None


# Nombres de pista -> instrumento, en la convencion de Rock Band / Guitar Hero.
# `T1 GEMS` es la de los GH viejos, que no separaban guitarra de nada.
INSTRUMENTOS_MIDI = {
    "PART GUITAR": "guitarra",
    "T1 GEMS": "guitarra",
    "PART GUITAR COOP": "guitarra_coop",
    "PART BASS": "bajo",
    "PART RHYTHM": "ritmica",
    "PART KEYS": "teclado",
}


def parse_midi_multi(path: str | Path) -> tuple[MidiChart, dict[str, dict[str, list[MidiNote]]]]:
    """Como `parse_midi`, pero devuelve TODOS los instrumentos de 5 trastes.

    Hace falta para el atlas de patrones: el bajo y la ritmica se chartean con
    reglas distintas de la solista, y esa diferencia es justo lo que hay que
    medir. Devuelve `(chart, {instrumento: {dificultad: notas}})`.
    """
    midi = mido.MidiFile(str(path), clip=True)
    chart = MidiChart(resolution=midi.ticks_per_beat or 480)

    for track in midi.tracks:
        elapsed = 0
        for message in track:
            elapsed += message.time
            if message.type == "set_tempo":
                chart.tempos.append((elapsed, mido.tempo2bpm(message.tempo)))
    chart.tempos.sort(key=lambda item: item[0])
    if not chart.tempos:
        chart.tempos = [(0, 120.0)]

    salida: dict[str, dict[str, list[MidiNote]]] = {}
    for track in midi.tracks:
        nombre = ""
        for message in track:
            if message.type == "track_name":
                nombre = message.name.strip().upper()
                break
        instrumento = INSTRUMENTOS_MIDI.get(nombre)
        if instrumento is None:
            continue

        abiertas: dict[int, int] = {}
        crudo: list[tuple[int, int, int]] = []
        elapsed = 0
        for message in track:
            elapsed += message.time
            if message.type == "note_on" and message.velocity > 0:
                abiertas[message.note] = elapsed
            elif message.type in ("note_off", "note_on"):
                inicio = abiertas.pop(message.note, None)
                if inicio is not None:
                    crudo.append((inicio, message.note, elapsed - inicio))

        por_dificultad: dict[str, list[MidiNote]] = {}
        for difficulty, base in DIFFICULTY_BASE.items():
            notas = [
                MidiNote(tick, pitch - base, sustain)
                for tick, pitch, sustain in crudo
                if base <= pitch <= base + 4
            ]
            notas.sort(key=lambda nota: (nota.tick, nota.fret))
            if notas:
                ligar = {tick for tick, pitch, _ in crudo if pitch == base + MARCA_LIGAR}
                rasguear = {tick for tick, pitch, _ in crudo if pitch == base + MARCA_RASGUEAR}
                notas += _marcas_de_forzado(notas, ligar, rasguear, chart.resolution)
                notas.sort(key=lambda nota: (nota.tick, nota.fret))
                por_dificultad[difficulty] = notas
        if por_dificultad:
            salida[instrumento] = por_dificultad
            fases = [(tick, sustain) for tick, pitch, sustain in crudo
                     if pitch == STAR_POWER_PITCH]
            if fases:
                chart.star_power[instrumento] = sorted(fases)
    return chart, salida


def parse_midi(path: str | Path) -> MidiChart:
    """Extract the five-fret guitar tracks and the tempo map from a MIDI chart."""
    midi = mido.MidiFile(str(path), clip=True)
    chart = MidiChart(resolution=midi.ticks_per_beat or 480)

    for track in midi.tracks:
        elapsed = 0
        for message in track:
            elapsed += message.time
            if message.type == "set_tempo":
                chart.tempos.append((elapsed, mido.tempo2bpm(message.tempo)))
    chart.tempos.sort(key=lambda item: item[0])
    if not chart.tempos:
        chart.tempos = [(0, 120.0)]

    guitar = _pick_guitar_track(midi)
    if guitar is None:
        return chart

    open_notes: dict[int, int] = {}
    elapsed = 0
    raw: list[tuple[int, int, int]] = []  # (tick, pitch, sustain)
    for message in guitar:
        elapsed += message.time
        if message.type == "note_on" and message.velocity > 0:
            open_notes[message.note] = elapsed
        elif message.type in ("note_off", "note_on"):
            start = open_notes.pop(message.note, None)
            if start is not None:
                raw.append((start, message.note, elapsed - start))

    for difficulty, base in DIFFICULTY_BASE.items():
        notes = [
            MidiNote(tick, pitch - base, sustain)
            for tick, pitch, sustain in raw
            if base <= pitch <= base + 4
        ]
        notes.sort(key=lambda note: (note.tick, note.fret))
        if notes:
            ligar = {tick for tick, pitch, _ in raw if pitch == base + MARCA_LIGAR}
            rasguear = {tick for tick, pitch, _ in raw if pitch == base + MARCA_RASGUEAR}
            notes += _marcas_de_forzado(notes, ligar, rasguear, chart.resolution)
            notes.sort(key=lambda note: (note.tick, note.fret))
            chart.tracks[difficulty] = notes

    phrases = [(tick, sustain) for tick, pitch, sustain in raw if pitch == STAR_POWER_PITCH]
    if phrases:
        chart.star_power["all"] = sorted(phrases)
    return chart
