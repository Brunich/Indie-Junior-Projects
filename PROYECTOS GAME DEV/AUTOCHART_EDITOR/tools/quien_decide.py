"""De cada nota del chart, ,quien eligio el traste?

`assign_frets` aplica seis reglas una detras de otra y la ultima que cambia el
valor es la que manda. Hasta el 22-08-2026 nadie habia contado cuantas notas
decide cada una, asi que "el chart sigue la melodia" era una creencia y no una
medida -- y justo la regla que mas se sospecha (el banco de motivos, que entra
cuando el tono lleva tres notas quietas) es la causa medida de que todas las
canciones se sientan iguales.

    python tools/quien_decide.py "<carpeta de cancion>"
    python tools/quien_decide.py --pride

Objetivo escrito en docs/SIGUIENTE_CHAT.md: que la melodia decida 2 de cada 3.
"""

from __future__ import annotations

import argparse
import sys
import zlib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from autochart import audio, generate  # noqa: E402
from autochart.cli import DEFAULT_PROFILE, _load_profile  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
PRIDE = ("03_Guitar Hero 3 Legends of Rock/"
         "Stevie Ray Vaughan (Steve Ouimette) - Pride & Joy")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Quien elige el traste de cada nota")
    parser.add_argument("carpeta", nargs="?", default=None)
    parser.add_argument("--pride", action="store_true")
    parser.add_argument("--perfil", default=str(RAIZ / "datos" / "perfil_oro.json"))
    args = parser.parse_args(argv)

    if args.pride:
        carpeta = BIBLIOTECA / PRIDE
    elif args.carpeta:
        carpeta = Path(args.carpeta)
    else:
        parser.error("hace falta una carpeta o --pride")
    if not carpeta.is_dir():
        print(f"[X] no existe {carpeta}")
        return 2

    ruta = audio.pick_audio(carpeta)
    if ruta is None:
        print(f"[X] no hay audio en {carpeta}")
        return 2
    perfil_path = Path(args.perfil)
    perfil = _load_profile(perfil_path if perfil_path.is_file() else DEFAULT_PROFILE)

    print(f"[*] {carpeta.name}")
    print(f"    audio: {ruta.name}")
    semilla = zlib.crc32(carpeta.name.encode("utf-8")) % 100000
    analisis = audio.analyse(ruta, beat_audio_path=audio.pick_beat_audio(carpeta))

    generate.REPARTO.clear()
    generate.PERDIDAS.clear()
    generate.SOSTENIDOS.clear()
    chart, _informe = generate.generate_chart(analisis, profile=perfil,
                                              difficulties=("Expert",), seed=semilla)
    pista = chart.tracks.get("ExpertSingle")
    notas = len({n.tick for n in pista.notes}) if pista else 0

    total = sum(generate.REPARTO.values())
    if not total:
        print("[X] nadie apunto nada: el contador no se relleno")
        return 2
    print(f"\n    {notas} notas en el chart, {total} decisiones apuntadas\n")
    print(f"    {'quien decide':24} {'notas':>7} {'%':>7}")
    for motivo, cuantas in sorted(generate.REPARTO.items(), key=lambda kv: -kv[1]):
        print(f"    {motivo:24} {cuantas:7d} {cuantas/total*100:6.1f}%")
    melodia = generate.REPARTO.get("contorno", 0) / total
    print(f"\n    La melodia decide el {melodia*100:.1f} % de las notas."
          f"  Objetivo: 66 %.")

    if generate.PERDIDAS:
        print(f"\n    -- CUANTAS NOTAS, Y DONDE SE PIERDEN --")
        orden = ("ataques detectados", "presupuesto de densidad",
                 "sobreviven al presupuesto", "tras rellenar huecos",
                 "tiradas por el hueco minimo", "notas finales")
        for clave in orden:
            if clave in generate.PERDIDAS:
                print(f"    {clave:30} {generate.PERDIDAS[clave]:6d}")

    if generate.SOSTENIDOS:
        print(f"\n    -- QUIEN SE QUEDA CON UN SOSTENIDO --")
        orden = ("candidatos", "sin_tono", "hueco_suficiente", "largo_suficiente",
                 "elegibles", "tope_del_perfil", "escritos")
        for clave in orden:
            if clave in generate.SOSTENIDOS:
                print(f"    {clave.replace('_', ' '):30} {generate.SOSTENIDOS[clave]:6d}")
        escritos = generate.SOSTENIDOS.get("escritos", 0)
        cand = generate.SOSTENIDOS.get("candidatos", 0) or 1
        print(f"    {'ratio que sale':30} {escritos / cand:6.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
