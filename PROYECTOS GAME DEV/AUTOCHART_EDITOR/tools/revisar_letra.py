"""Dice que letras han salido sospechosas, sin abrir el juego.

Es a la letra lo que `revisar_in_game.py` es a las notas. Genera un lote de 70
canciones y no puedes cantarlas todas para ver cual salio mal; esto las mide
contra `datos/perfil_voz.json` -- las 128 canciones con voz escrita a mano -- y
saca solo las que se salen.

    python tools/revisar_letra.py                    # todo salida/letras
    python tools/revisar_letra.py salida/letras/<X>  # una
    python tools/revisar_letra.py --todo             # lista tambien las buenas

Lo que mira, y por que cada cosa:

  ERROR   frases solapadas          la linea nueva borra la anterior a media palabra
  ERROR   silabas fuera de orden    el juego las pinta donde no toca
  ERROR   frase vacia               un phrase_start sin nada dentro
  ERROR   letra mas larga que la cancion   sobra letra al final: version distinta
  aviso   se canta demasiado rapido  por encima del p95 humano no es cantable
  aviso   frase demasiado larga      no cabe en pantalla
  aviso   trocea de mas o de menos   cuantas silabas enlazan contra el humano
  aviso   poca cancion con letra     puede faltar media letra
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from autochart import voz  # noqa: E402
from autochart.export import read_song_ini  # noqa: E402

PERFIL = RAIZ / "datos" / "perfil_voz.json"
BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"


def duracion_de(nombre: str) -> float:
    """Busca la cancion original en la biblioteca para saber cuanto dura."""
    for pack in BIBLIOTECA.iterdir() if BIBLIOTECA.is_dir() else []:
        if not pack.is_dir():
            continue
        candidata = pack / nombre
        if candidata.is_dir():
            try:
                return float(read_song_ini(candidata).get("song_length", 0)) / 1000.0
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def revisar(carpeta: Path, perfil: dict) -> tuple[list[str], list[str], dict]:
    errores: list[str] = []
    avisos: list[str] = []
    pista = voz.leer_voz(carpeta)
    if pista is None or not pista.silabas:
        return ["no tiene letra que leer"], [], {}

    est = voz.medir(pista)
    silabas = pista.silabas

    # --- errores: cosas que el juego pinta mal -----------------------------
    ticks = [s.tick for s in silabas]
    if ticks != sorted(ticks):
        errores.append("hay silabas fuera de orden")
    for frase in pista.frases:
        if not frase.silabas:
            errores.append("hay una frase vacia")
            break
    for a, b in zip(pista.frases, pista.frases[1:]):
        if b.inicio < a.fin - 1:
            errores.append(f"frases solapadas en {pista.tick_to_seconds(b.inicio):.1f}s")
            break

    duracion = duracion_de(carpeta.name)
    ultima = pista.tick_to_seconds(silabas[-1].tick)
    if duracion and ultima > duracion + 2:
        errores.append(f"la letra acaba en {ultima:.0f}s y la cancion dura {duracion:.0f}s")

    # --- avisos: cosas raras contra el humano ------------------------------
    def fuera(valor: float, clave: str, etiqueta: str, unidad: str = "") -> None:
        rango = perfil.get(clave)
        if not rango:
            return
        if valor > rango["p95"]:
            avisos.append(f"{etiqueta} {valor:.2f}{unidad} (humano p95 {rango['p95']})")
        elif valor < rango["p5"]:
            avisos.append(f"{etiqueta} {valor:.2f}{unidad} (humano p5 {rango['p5']})")

    if est.silabas_por_segundo:
        rapidas = [v for v in est.silabas_por_segundo
                   if v > perfil["silabas_por_segundo"]["p95"]]
        if len(rapidas) > max(2, len(est.silabas_por_segundo) * 0.1):
            avisos.append(f"{len(rapidas)} frases se cantan por encima del p95 humano "
                          f"({perfil['silabas_por_segundo']['p95']} sil/s)")
    largas = [v for v in est.silabas_por_frase if v > perfil["silabas_por_frase"]["p95"]]
    if largas:
        avisos.append(f"{len(largas)} frases pasan de {perfil['silabas_por_frase']['p95']:.0f} "
                      f"silabas (no caben en pantalla)")
    fuera(est.ratio_enlaza, "ratio_enlaza", "silabas enlazadas")

    if duracion:
        primera = pista.tick_to_seconds(silabas[0].tick)
        cubierto = (ultima - primera) / duracion
        if cubierto < 0.35:
            avisos.append(f"solo el {cubierto * 100:.0f} % de la cancion lleva letra")

    resumen = {
        "silabas": est.silabas,
        "frases": est.frases,
        "enlaza": round(est.ratio_enlaza, 3),
        "sil_s": round(sorted(est.silabas_por_segundo)[len(est.silabas_por_segundo) // 2], 2)
        if est.silabas_por_segundo else 0.0,
        "duracion": duracion,
    }
    return errores, avisos, resumen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Revisa las letras generadas")
    parser.add_argument("carpeta", nargs="?", default=str(RAIZ / "salida" / "letras"))
    parser.add_argument("--perfil", default=str(PERFIL))
    parser.add_argument("--todo", action="store_true", help="Lista tambien las que estan bien")
    args = parser.parse_args(argv)

    perfil = json.loads(Path(args.perfil).read_text(encoding="utf-8"))
    raiz = Path(args.carpeta)
    if (raiz / "notes.chart").is_file() or (raiz / "notes.mid").is_file():
        carpetas = [raiz]
    else:
        carpetas = sorted(d for d in raiz.iterdir() if d.is_dir()) if raiz.is_dir() else []
    if not carpetas:
        print(f"[X] No hay nada que revisar en {raiz}")
        return 2

    print(f"[*] {len(carpetas)} letras contra el perfil de 128 canciones humanas\n")
    con_error = con_aviso = limpias = 0
    for carpeta in carpetas:
        try:
            errores, avisos, resumen = revisar(carpeta, perfil)
        except Exception as fallo:
            errores, avisos, resumen = [f"{type(fallo).__name__}: {fallo}"], [], {}
        if errores:
            con_error += 1
        elif avisos:
            con_aviso += 1
        else:
            limpias += 1
        if not errores and not avisos and not args.todo:
            continue
        marca = "[X] " if errores else "[!] "
        cifras = (f"{resumen.get('silabas', 0):4d} sil  {resumen.get('frases', 0):3d} frases  "
                  f"enlaza {resumen.get('enlaza', 0):.2f}  {resumen.get('sil_s', 0):.2f} sil/s")
        print(f"{marca}{carpeta.name[:40]:40} {cifras}")
        for error in errores:
            print(f"      ERROR  {error}")
        for aviso in avisos:
            print(f"      aviso  {aviso}")

    print(f"\n[OK] {limpias} limpias | {con_aviso} con avisos | {con_error} con errores")
    return 1 if con_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
