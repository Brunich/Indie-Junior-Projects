"""Medir las ligaduras: cuantas notas se tocan sin rasguear, y por que.

Clone Hero decide **solo** si una nota es HOPO ("hammer-on / pull-off", se toca
con la izquierda sin rasguear) mirando la distancia a la anterior. A eso se le
llama el HOPO *natural*. Encima de eso, el charter puede escribir dos marcas:

    N 5   forzado -- invierte lo que el juego decidio (liga lo separado,
                     o corta una ligadura que el juego habria hecho sola)
    N 6   tap     -- se toca sin rasguear pase lo que pase

Esta herramienta cuenta las tres cosas en los charts humanos: el natural, el
real (natural XOR forzado, mas los taps) y **para que usa un humano el
forzado**. Sin esta medida no se puede saber si lo que escribe el generador se
parece a lo que hace una mano.

    python tools/medir_hopo.py                       # el corpus humano
    python tools/medir_hopo.py "salida/<carpeta>"    # un chart concreto
    python tools/medir_hopo.py --json salida/hopo_corpus.json

La regla del HOPO natural esta copiada de Moonscraper (`Note.IsNaturalHopo`),
que es de donde la toma el juego: la distancia son **65 ticks a resolucion
192**, o sea algo mas de un tresillo de corchea, y la nota tiene que ser suelta
y distinta de la anterior. Un acorde no es nunca HOPO natural.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autochart import chartio  # noqa: E402
from autochart.chartio import (  # noqa: E402
    NoteGroup, group_notes, hopo_distance, is_natural_hopo,
)

DEFAULT_LIBRARY = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"

# La regla del HOPO natural vive en `chartio` a proposito: es la del juego, y la
# usan tanto el generador (para decidir donde marcar) como esta herramienta
# (para medir si acerto). Con dos copias, la medida acabaria dando por bueno lo
# que el juego no hace.

# Por que una nota forzada NO era ligadura natural. Es lo que dice para que usa
# el humano la marca.
REASONS = ("acorde", "mismo_traste", "lejos", "primera")


def why_not_natural(previous: NoteGroup | None, current: NoteGroup, threshold: float) -> str:
    if previous is None:
        return "primera"
    if current.is_chord:
        return "acorde"
    if current.tick - previous.tick > threshold:
        return "lejos"
    return "mismo_traste"


@dataclass
class TrackHopo:
    song: str = ""
    groups: int = 0
    natural: int = 0
    real: int = 0
    forced: int = 0
    taps: int = 0
    force_corta: int = 0          # forzado sobre una ligadura natural -> rasgueo
    force_liga: int = 0           # forzado sobre un rasgueo -> ligadura
    liga_por: Counter = field(default_factory=Counter)
    liga_huecos_beats: list[float] = field(default_factory=list)
    arranca_natural: int = 0      # ligaduras naturales que ABREN racha
    arranca_real: int = 0         # ligaduras de verdad (ya con marcas) que abren racha
    hopo_acordes: int = 0         # acordes que acaban ligados (el juego no los liga solo)
    tap_acordes: int = 0

    @property
    def natural_ratio(self) -> float:
        return self.natural / self.groups if self.groups else 0.0

    @property
    def real_ratio(self) -> float:
        return self.real / self.groups if self.groups else 0.0

    @property
    def racha_natural(self) -> float:
        """Cuantas notas seguidas dura una ligadura, de media.

        No es un adorno: `generate.FORCE_CUT_RUN_START` (0.214) es CUATRO veces
        `FORCE_CUT_IN_RUN` (0.055), asi que el que abre la frase se rasguea y el
        resto se liga. Con rachas cortas casi toda la ligadura paga la tasa cara.
        Medido el 24-08-2026: el humano encadena 3.16 y nosotros 1.66.
        """
        return self.natural / self.arranca_natural if self.arranca_natural else 0.0

    @property
    def racha_real(self) -> float:
        """La misma racha pero ya con las marcas puestas: lo que siente la mano."""
        return self.real / self.arranca_real if self.arranca_real else 0.0


def measure_track(chart: chartio.Chart, track_name: str = "ExpertSingle") -> TrackHopo | None:
    track = chart.tracks.get(track_name)
    if track is None:
        return None
    groups = group_notes(track.notes)
    if len(groups) < 32:
        return None

    threshold = hopo_distance(chart.resolution)
    out = TrackHopo(groups=len(groups))
    previous: Group | None = None
    natural_antes = real_antes = False
    for group in groups:
        natural = is_natural_hopo(previous, group, threshold)
        real = group.tap or (natural != group.forced)
        out.natural += int(natural)
        out.real += int(real)
        out.arranca_natural += int(natural and not natural_antes)
        out.arranca_real += int(real and not real_antes)
        natural_antes, real_antes = natural, real
        out.forced += int(group.forced)
        out.taps += int(group.tap)
        if group.forced:
            if natural:
                out.force_corta += 1
            else:
                out.force_liga += 1
                reason = why_not_natural(previous, group, threshold)
                out.liga_por[reason] += 1
                if reason == "lejos" and previous is not None:
                    gap = (group.tick - previous.tick) / chart.resolution
                    out.liga_huecos_beats.append(round(gap, 3))
        if real and group.is_chord:
            out.hopo_acordes += 1
        if group.tap and group.is_chord:
            out.tap_acordes += 1
        previous = group
    return out


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------


def looks_generated(path: Path, chart: chartio.Chart) -> bool:
    if "(autochart)" in path.parent.name.lower():
        return True
    return "autochart" in chart.metadata.get("Charter", "").lower()


def percentiles(values: list[float], points=(5, 25, 50, 75, 95)) -> dict[str, float]:
    if not values:
        return {f"p{p}": 0.0 for p in points}
    ordered = sorted(values)
    out = {}
    for point in points:
        index = min(len(ordered) - 1, max(0, int(round((point / 100.0) * (len(ordered) - 1)))))
        out[f"p{point}"] = round(ordered[index], 4)
    return out


def scan_corpus(library: Path, track_name: str, limit: int | None = None) -> list[TrackHopo]:
    """Solo `.chart`: el `.mid` guarda el forzado de otra forma y mezclarlos miente."""
    results: list[TrackHopo] = []
    for path in sorted(library.glob("**/notes.chart")):
        if limit is not None and len(results) >= limit:
            break
        try:
            chart = chartio.parse_chart(path)
        except Exception:  # un chart roto no tumba la medida
            continue
        if looks_generated(path, chart):
            continue
        stats = measure_track(chart, track_name)
        if stats is None:
            continue
        stats.song = path.parent.name
        results.append(stats)
    return results


def report_corpus(rows: list[TrackHopo]) -> dict:
    total_groups = sum(r.groups for r in rows)
    total_forced = sum(r.forced for r in rows)
    total_taps = sum(r.taps for r in rows)
    corta = sum(r.force_corta for r in rows)
    liga = sum(r.force_liga for r in rows)
    reasons: Counter = Counter()
    for row in rows:
        reasons.update(row.liga_por)
    gaps = [g for r in rows for g in r.liga_huecos_beats]

    con_marcas = [r for r in rows if r.forced or r.taps]
    return {
        "charts": len(rows),
        "charts_con_marcas": len(con_marcas),
        "golpes": total_groups,
        "forzadas": total_forced,
        "taps": total_taps,
        "ligadura_natural": percentiles([r.natural_ratio for r in rows]),
        "ligadura_real": percentiles([r.real_ratio for r in rows]),
        "ligadura_real_con_marcas": percentiles([r.real_ratio for r in con_marcas]),
        "forzado_para": {
            "cortar_ligadura": corta,
            "ligar_separadas": liga,
            "cortar_pct": round(100 * corta / max(1, total_forced), 1),
        },
        "ligar_separadas_por": {k: reasons.get(k, 0) for k in REASONS},
        "hueco_al_ligar_lejos_beats": percentiles(gaps) if gaps else {},
        "acordes_ligados": sum(r.hopo_acordes for r in rows),
        "acordes_tap": sum(r.tap_acordes for r in rows),
        "marcas_por_chart": {
            "forzadas_p50": round(statistics.median([r.forced for r in rows]), 1) if rows else 0,
            "taps_p50": round(statistics.median([r.taps for r in rows]), 1) if rows else 0,
        },
    }


def print_corpus(summary: dict) -> None:
    print(f"\n[*] {summary['charts']} charts humanos (.chart), {summary['golpes']} golpes")
    print(f"    con alguna marca escrita: {summary['charts_con_marcas']}")
    print(f"    forzadas {summary['forzadas']}   taps {summary['taps']}"
          f"   (mediana por chart: {summary['marcas_por_chart']['forzadas_p50']:.0f}"
          f" / {summary['marcas_por_chart']['taps_p50']:.0f})")

    print("\n    Que porcentaje de notas se tocan LIGADAS (sin rasguear):")
    header = "      {:<26} {:>6} {:>6} {:>6} {:>6} {:>6}".format("", "p5", "p25", "p50", "p75", "p95")
    print(header)
    for label, key in (
        ("natural (sin marcas)", "ligadura_natural"),
        ("real (con marcas)", "ligadura_real"),
        ("real, solo los que marcan", "ligadura_real_con_marcas"),
    ):
        row = summary[key]
        print("      {:<26} {:>5.1f}% {:>5.1f}% {:>5.1f}% {:>5.1f}% {:>5.1f}%".format(
            label, *[100 * row[f"p{p}"] for p in (5, 25, 50, 75, 95)]))

    forced_for = summary["forzado_para"]
    print(f"\n    Para que se usa el forzado ({summary['forzadas']} marcas):")
    print(f"      cortar una ligadura que el juego haria sola  {forced_for['cortar_ligadura']:>7}"
          f"  ({forced_for['cortar_pct']:.1f} %)")
    print(f"      ligar dos notas que el juego NO ligaria      {forced_for['ligar_separadas']:>7}"
          f"  ({100 - forced_for['cortar_pct']:.1f} %)")
    for reason, count in summary["ligar_separadas_por"].items():
        if count:
            print(f"          por {reason:<14} {count:>7}")
    if summary["hueco_al_ligar_lejos_beats"]:
        gaps = summary["hueco_al_ligar_lejos_beats"]
        print(f"      hueco al ligar lejos (tiempos): p25 {gaps['p25']:.2f}"
              f"  p50 {gaps['p50']:.2f}  p75 {gaps['p75']:.2f}  p95 {gaps['p95']:.2f}")
    print(f"\n    Acordes que acaban ligados: {summary['acordes_ligados']}"
          f"   (taps en acorde: {summary['acordes_tap']})")


def print_one(stats: TrackHopo, track_name: str) -> None:
    print(f"\n[*] {stats.song or '?'} -- {track_name}: {stats.groups} golpes")
    print(f"    ligadura natural  {100 * stats.natural_ratio:5.1f} %")
    print(f"    ligadura real     {100 * stats.real_ratio:5.1f} %"
          f"   (forzadas {stats.forced}, taps {stats.taps})")
    if stats.forced:
        print(f"    el forzado corta {stats.force_corta} y liga {stats.force_liga}"
              f"  {dict(stats.liga_por)}")
    print(f"    racha de ligadura {stats.racha_natural:5.2f} notas naturales"
          f"   {stats.racha_real:5.2f} con las marcas   (humano 3.16)")
    print(f"    acordes ligados   {stats.hopo_acordes}")
    print("    (humano, 254 charts: ligadura real p25 7.5 %  p50 17.2 %  p75 37.2 %)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Medir HOPO, tap y forzado")
    parser.add_argument("carpeta", nargs="?", help="Chart suelto; sin esto mide el corpus")
    parser.add_argument("--biblioteca", default=str(DEFAULT_LIBRARY))
    parser.add_argument("--pista", default="ExpertSingle")
    parser.add_argument("--limite", type=int, default=None)
    parser.add_argument("--json", dest="json_path", default=None)
    args = parser.parse_args()

    if args.carpeta:
        path = Path(args.carpeta)
        if path.is_dir():
            path = path / "notes.chart"
        if not path.is_file():
            print(f"[X] No existe: {path}")
            return 2
        chart = chartio.parse_chart(path)
        stats = measure_track(chart, args.pista)
        if stats is None:
            print(f"[X] {path} no tiene pista {args.pista} con notas suficientes")
            return 2
        stats.song = chart.metadata.get("Name", path.parent.name)
        print_one(stats, args.pista)
        return 0

    library = Path(args.biblioteca)
    if not library.is_dir():
        print(f"[X] No existe la biblioteca: {library}")
        return 2
    rows = scan_corpus(library, args.pista, args.limite)
    if not rows:
        print("[X] No se pudo leer ningun chart")
        return 2
    summary = report_corpus(rows)
    print_corpus(summary)
    if args.json_path:
        destination = Path(args.json_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "resumen": summary,
            "charts": [
                {
                    "cancion": r.song,
                    "golpes": r.groups,
                    "natural": round(r.natural_ratio, 4),
                    "real": round(r.real_ratio, 4),
                    "forzadas": r.forced,
                    "taps": r.taps,
                }
                for r in rows
            ],
        }
        destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"    guardado en {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
