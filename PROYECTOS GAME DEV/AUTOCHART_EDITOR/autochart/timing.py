"""Turn a list of detected beat times into a Clone Hero tempo map.

Two things have to be true at the same time:

1. Tick ``(i + 1) * resolution`` must land on detected beat ``i``. The +1 is a
   lead-in beat: tick 0 is always time 0 in a chart, but the first detected
   beat almost never is, so beat 0 is parked one beat in and the opening tempo
   event stretches to cover the gap.
2. The map must track a drifting performance. Emitting one tempo event per beat
   would work but bloats the file, so events are emitted only when the chart's
   own predicted time has drifted away from the audio by more than a few
   milliseconds -- and the new tempo is chosen to cancel that drift, not merely
   to match the local beat length.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .chartio import TempoEvent

MIN_BPM = 20.0
MAX_BPM = 400.0
DRIFT_TOLERANCE_S = 0.006


@dataclass
class TempoMap:
    resolution: int
    beat_times: np.ndarray  # detected beats; index i sits at tick (i+1)*resolution
    events: list[TempoEvent]

    def beat_to_tick(self, beat: float) -> int:
        return int(round((beat + 1.0) * self.resolution))

    def tick_to_beat(self, tick: int) -> float:
        return tick / self.resolution - 1.0

    def time_to_beat(self, time: float) -> float:
        """Fractional beat index for a time in seconds (extrapolates at the ends)."""
        beats = self.beat_times
        if beats.size < 2:
            return 0.0
        index = int(np.searchsorted(beats, time) - 1)
        if index < 0:
            gap = float(beats[1] - beats[0])
            return (time - float(beats[0])) / gap
        if index >= beats.size - 1:
            gap = float(beats[-1] - beats[-2])
            return (beats.size - 1) + (time - float(beats[-1])) / gap
        gap = float(beats[index + 1] - beats[index])
        return index + (time - float(beats[index])) / gap

    def beat_to_time(self, beat: float) -> float:
        beats = self.beat_times
        if beats.size < 2:
            return 0.0
        index = int(np.floor(beat))
        frac = beat - index
        if index < 0:
            gap = float(beats[1] - beats[0])
            return float(beats[0]) + beat * gap
        if index >= beats.size - 1:
            gap = float(beats[-1] - beats[-2])
            return float(beats[-1]) + (beat - (beats.size - 1)) * gap
        return float(beats[index]) + frac * float(beats[index + 1] - beats[index])

    @property
    def average_bpm(self) -> float:
        if self.beat_times.size < 2:
            return 120.0
        gaps = np.diff(self.beat_times)
        return float(60.0 / np.median(gaps))


TEMPO_BAND = (85.0, 200.0)


def normalise_tempo_octave(
    beat_times: np.ndarray, band: tuple[float, float] = TEMPO_BAND
) -> np.ndarray:
    """Double or halve the beat grid until the implied tempo sits in `band`.

    Beat trackers land an octave off the tempo a charter would have written
    fairly often (*Keelhauled* is charted at 220 BPM and comes back as 110).
    The notes still land correctly either way, because the subdivisions absorb
    the difference -- but anything expressed in beats would mean twice or half
    of what it should. Inside the band we leave it alone; outside it, a grid
    that coarse or that fine breaks the difficulty settings outright.
    """
    beats = np.asarray(beat_times, dtype=float)
    if beats.size < 3:
        return beats
    low, high = band
    for _ in range(3):
        bpm = 60.0 / float(np.median(np.diff(beats)))
        if bpm < low:
            midpoints = (beats[:-1] + beats[1:]) / 2.0
            beats = np.sort(np.concatenate([beats, midpoints]))
        elif bpm > high:
            beats = beats[::2]
        else:
            break
        if beats.size < 3:
            break
    return beats


def smooth_beat_grid(
    beat_times: np.ndarray, window: int = 3, drift_window: int = 33
) -> np.ndarray:
    """Take the tracker's jitter out of the grid without losing the real drift.

    A beat tracker is accurate to a couple of frames, which is fine for placing
    notes but terrible as a tempo map: every beat becomes its own tempo event
    and the note highway visibly speeds up and slows down. So the intervals get
    a rolling median (kills per-beat noise, keeps genuine tempo changes over a
    few beats), and then the slow component of the error is added back so the
    grid still follows the performance instead of running away from it.
    """
    beats = np.asarray(beat_times, dtype=float)
    if beats.size < max(window + 2, 8):
        return beats

    intervals = np.diff(beats)
    pad = window // 2
    padded = np.pad(intervals, pad, mode="edge")
    smoothed = np.array([np.median(padded[i:i + window]) for i in range(intervals.size)])
    # Start from zero rather than from the first detected beat: anchoring on
    # beat 0 would bake that one beat's tracking error into the whole grid.
    # The drift correction below puts the grid back in absolute position.
    rebuilt = np.concatenate([[0.0], np.cumsum(smoothed)])

    error = beats - rebuilt
    span = min(drift_window, error.size)
    if span >= 3:
        # Edge-padded, not zero-padded: a plain 'same' convolution averages the
        # first and last beats against nothing and leaves the intro and the
        # outro tens of milliseconds off.
        pad = span // 2
        kernel = np.ones(span) / span
        averaged = np.convolve(np.pad(error, pad, mode="edge"), kernel, mode="valid")
        rebuilt = rebuilt + averaged[: error.size]

    # A grid has to be strictly increasing or the tempo map is nonsense.
    rebuilt = np.maximum.accumulate(rebuilt)
    stuck = np.diff(rebuilt) <= 0
    if np.any(stuck):
        rebuilt[1:][stuck] = rebuilt[:-1][stuck] + 1e-3
        rebuilt = np.maximum.accumulate(rebuilt)
    return rebuilt


def prepare_beat_grid(beat_times: np.ndarray, min_lead_in: float = 0.18) -> np.ndarray:
    """Extend beats backwards toward zero, leaving room for the lead-in beat."""
    beats = np.asarray(beat_times, dtype=float)
    beats = beats[beats >= 0]
    if beats.size < 2:
        return beats
    gap = float(beats[1] - beats[0])
    if gap <= 0:
        return beats
    prefix: list[float] = []
    cursor = float(beats[0]) - gap
    while cursor > min_lead_in:
        prefix.append(cursor)
        cursor -= gap
    if prefix:
        beats = np.concatenate([np.array(sorted(prefix)), beats])
    while beats.size > 2 and beats[0] < min_lead_in:
        beats = beats[1:]
    return beats


def build_tempo_map(beat_times: np.ndarray, resolution: int = 192) -> TempoMap:
    """Build the tempo map that pins every beat tick onto its detected time."""
    beats = prepare_beat_grid(beat_times)
    if beats.size < 2:
        return TempoMap(resolution, beats, [TempoEvent(0, 120.0)])

    def clamp(bpm: float) -> float:
        return float(min(MAX_BPM, max(MIN_BPM, bpm)))

    events: list[TempoEvent] = []
    lead_in_bpm = clamp(60.0 / max(float(beats[0]), 1e-3))
    events.append(TempoEvent(0, round(lead_in_bpm, 3)))

    # Chart time actually reached at beat 0, after the rounding the file forces.
    current_bpm = round(lead_in_bpm, 3)
    predicted = 60.0 / current_bpm

    for index in range(beats.size - 1):
        target = float(beats[index + 1])
        remaining = target - predicted
        local_bpm = clamp(60.0 / max(remaining, 1e-3))
        drift = abs(predicted - float(beats[index]))
        needs_event = (
            index == 0
            or drift > DRIFT_TOLERANCE_S
            or abs(local_bpm - current_bpm) / max(current_bpm, 1e-6) > 0.015
        )
        if needs_event:
            corrected = round(clamp(60.0 / max(remaining, 1e-3)), 3)
            if abs(corrected - current_bpm) > 1e-3:
                events.append(TempoEvent((index + 1) * resolution, corrected))
                current_bpm = corrected
        predicted += 60.0 / current_bpm

    # Collapse duplicates that survived rounding.
    deduped: list[TempoEvent] = []
    for event in events:
        if deduped and (event.tick == deduped[-1].tick or abs(event.bpm - deduped[-1].bpm) < 1e-3):
            if event.tick == deduped[-1].tick:
                deduped[-1] = event
            continue
        deduped.append(event)
    return TempoMap(resolution, beats, deduped)
