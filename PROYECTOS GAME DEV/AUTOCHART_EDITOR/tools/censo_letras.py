"""Censo de letra: que tiene la biblioteca, que falta y que no hace falta.

Responde a la pregunta que importa cuando ya has puesto letra a medio catalogo:
**de lo que queda sin letra, cuanto es trabajo pendiente y cuanto esta ya
terminado porque es instrumental.** Mezclados, los dos parecen un hueco.

    python tools/censo_letras.py                 # todo
    python tools/censo_letras.py --pack 10       # un pack
    python tools/censo_letras.py --sin-red       # solo lo que ya esta en cache

Cinco estados por cancion:

    CON        ya trae letra escrita (la tenia o se la pusimos)
    FALTA      se canta y LRCLIB la tiene: se puede poner ya
    INSTR      es instrumental: no hay nada que cantar, esta terminada
    OTRA       LRCLIB solo tiene otra version (duracion distinta)
    NO_ESTA    LRCLIB no conoce la cancion

Las consultas se guardan en `datos/censo_letras.json` para no repetirlas: la
base de LRCLIB es gratis y de la comunidad, y no hay que machacarla.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from autochart import letras, voz  # noqa: E402
from autochart.export import read_song_ini  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
CACHE = RAIZ / "datos" / "censo_letras.json"
PAUSA = 0.15   # segundos entre consultas, por educacion con LRCLIB


def clasificar(carpeta: Path, cache: dict, sin_red: bool) -> tuple[str, str]:
    try:
        pista = voz.leer_voz(carpeta)
    except Exception:
        pista = None
    if pista is not None and len(pista.silabas) >= 20:
        return "CON", f"{len(pista.silabas)} silabas"

    clave = str(carpeta.relative_to(BIBLIOTECA)) if BIBLIOTECA in carpeta.parents else carpeta.name
    if clave in cache:
        guardado = cache[clave]
        return guardado["estado"], guardado["detalle"]
    if sin_red:
        return "NO_ESTA", "sin consultar (--sin-red)"

    info = read_song_ini(carpeta)
    artista = info.get("artist", "").strip()
    titulo = info.get("name", "").strip() or carpeta.name
    try:
        duracion = float(info.get("song_length", 0) or 0) / 1000.0
    except ValueError:
        duracion = 0.0

    candidatas = letras.buscar(artista, titulo, duracion)
    time.sleep(PAUSA)
    naturaleza = letras.parece_instrumental(candidatas, artista, duracion)
    if naturaleza.instrumental:
        estado, detalle = "INSTR", naturaleza.motivo
    elif letras.elegir(candidatas, duracion, habra_audio=True) is not None:
        estado, detalle = "FALTA", "LRCLIB la tiene sincronizada"
    elif not candidatas:
        estado, detalle = "NO_ESTA", "LRCLIB no la conoce"
    else:
        cerca = candidatas[0]
        estado = "OTRA"
        detalle = (f"solo otra version ({cerca.duracion:.0f}s contra {duracion:.0f}s"
                   f"{', sin tiempos' if not cerca.tiene_tiempos else ''})")
    cache[clave] = {"estado": estado, "detalle": detalle}
    return estado, detalle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Censo de letra de la biblioteca")
    parser.add_argument("--biblioteca", default=str(BIBLIOTECA))
    parser.add_argument("--pack", action="append", default=[])
    parser.add_argument("--sin-red", action="store_true")
    parser.add_argument("--cache", default=str(CACHE))
    parser.add_argument("--listar", default="FALTA",
                        help="Que estado listar cancion por cancion (o 'nada')")
    args = parser.parse_args(argv)

    raiz = Path(args.biblioteca)
    ruta_cache = Path(args.cache)
    cache = json.loads(ruta_cache.read_text(encoding="utf-8")) if ruta_cache.is_file() else {}

    packs = sorted(p for p in raiz.iterdir() if p.is_dir())
    if args.pack:
        packs = [p for p in packs if any(p.name == q or p.name.startswith(f"{q}_")
                                         for q in args.pack)]

    print(f"[*] Censando {len(packs)} packs. Cache: {len(cache)} consultas guardadas\n")
    print(f"{'pack':40} {'CON':>5} {'FALTA':>6} {'INSTR':>6} {'OTRA':>5} {'NO_ESTA':>8}")
    print("-" * 74)

    total: Counter[str] = Counter()
    pendientes: list[tuple[str, str, str]] = []
    # Lo que se use de verdad en esta pasada. La cache se reescribe con esto y
    # no con lo que hubiera: una cancion a la que ya le pusimos letra se
    # clasifica leyendo su chart y NUNCA vuelve a tocar la cache, asi que su
    # entrada vieja ("FALTA") se quedaba ahi para siempre y `autochart estado`
    # seguia diciendo que faltaban 130 cuando ya estaban puestas.
    usadas: dict[str, dict] = {}
    for pack in packs:
        cuenta: Counter[str] = Counter()
        canciones = sorted({p.parent for patron in ("**/notes.chart", "**/notes.mid")
                            for p in pack.glob(patron)})
        for carpeta in canciones:
            estado, detalle = clasificar(carpeta, cache, args.sin_red)
            try:
                clave = str(carpeta.relative_to(raiz))
            except ValueError:
                clave = carpeta.name
            # Solo se guarda lo que sigue SIN letra. Si ya la tiene, su
            # entrada vieja sobra: guardarla "porque estaba" es justo lo que
            # dejaba 115 FALTA fantasma en el estado.
            if estado != "CON" and clave in cache:
                usadas[clave] = cache[clave]
            cuenta[estado] += 1
            total[estado] += 1
            if estado == args.listar:
                pendientes.append((pack.name, carpeta.name, detalle))
        if canciones:
            print(f"{pack.name[:40]:40} {cuenta['CON']:>5} {cuenta['FALTA']:>6} "
                  f"{cuenta['INSTR']:>6} {cuenta['OTRA']:>5} {cuenta['NO_ESTA']:>8}")

    ruta_cache.parent.mkdir(parents=True, exist_ok=True)
    ruta_cache.write_text(json.dumps(usadas, indent=1, ensure_ascii=False), encoding="utf-8")

    suma = sum(total.values()) or 1
    print("-" * 74)
    print(f"{'TOTAL':40} {total['CON']:>5} {total['FALTA']:>6} {total['INSTR']:>6} "
          f"{total['OTRA']:>5} {total['NO_ESTA']:>8}")
    print(f"\n     con letra          {total['CON']:4d}  ({total['CON'] / suma * 100:.0f} %)")
    print(f"     se puede poner ya  {total['FALTA']:4d}  <- esto es lo unico pendiente de verdad")
    print(f"     instrumentales     {total['INSTR']:4d}  (terminadas: no hay nada que cantar)")
    print(f"     solo otra version  {total['OTRA']:4d}  (haria falta la letra de ESTA grabacion)")
    print(f"     LRCLIB no la tiene {total['NO_ESTA']:4d}  (solo entra a mano o transcribiendo)")

    if pendientes and args.listar != "nada":
        print(f"\n=== {args.listar} ({len(pendientes)}) ===")
        for pack, cancion, detalle in pendientes[:60]:
            print(f"  {pack[:24]:24} {cancion[:44]:44} {detalle[:30]}")
        if len(pendientes) > 60:
            print(f"  ... y {len(pendientes) - 60} mas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
