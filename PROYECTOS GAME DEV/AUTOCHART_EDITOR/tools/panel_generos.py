"""El panel con el que se juzga si el GENERO sirve: varias canciones, no una.

CLAUDE.md manda que una sola cancion no decide nada, y el genero es justo la
clase de cambio que no se puede juzgar con la cancion de referencia: Pride &
Joy dice `Electric Blues`, cae en la familia `acustico`, y esa familia tiene 5
charts en la biblioteca -- menos de los 12 que pide `corpus.MINIMO_POR_GENERO`,
asi que se queda SIN bloque y el genero no la toca.

Por eso el panel coge canciones de las familias que si tienen muestra (metal,
rock, punk, latino, pop), todas con `guitar.ogg` -- ahi el audio ES el
instrumento del chart -- y mide lo mismo que `contra_el_humano.py` contra su
chart hecho a mano. Se corre dos veces, una con cada perfil, y se restan:

    python tools/panel_generos.py --perfil salida/perfil_oro_ANTES.json --salida salida/panel_antes.json
    python tools/panel_generos.py --perfil datos/perfil_oro.json        --salida salida/panel_ahora.json
    python tools/panel_generos.py --comparar salida/panel_antes.json salida/panel_ahora.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zlib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))

from autochart import atlas, corpus  # noqa: E402
from comparar_humano import (best_offset, generated_note_times,  # noqa: E402
                             human_note_times, match_ratio)
from contra_el_humano import distancia, perfil_corto, vector_de_gestos  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
# Familias con muestra suficiente. `acustico` (5 charts) y `urbano` (6) quedan
# fuera porque no tienen bloque propio.
FAMILIAS = ("metal", "rock", "punk", "latino", "pop")
POR_FAMILIA = 2


def elegir(biblioteca: Path) -> list[Path]:
    """Dos canciones por familia, repartidas a lo largo de la lista.

    Se toman a intervalos regulares y no al azar: el panel tiene que ser el
    MISMO en las dos corridas o la resta no significa nada.
    """
    por: dict[str, list[Path]] = {}
    for patron in ("**/notes.chart", "**/notes.mid"):
        for path in sorted(biblioteca.glob(patron)):
            carpeta = path.parent
            if not (carpeta / "guitar.ogg").is_file():
                continue
            familia = atlas.normalizar_genero(corpus._leer_genero(carpeta))
            if familia not in FAMILIAS:
                continue
            por.setdefault(familia, []).append(carpeta)
    elegidas: list[Path] = []
    for familia in FAMILIAS:
        lista = por.get(familia, [])
        if not lista:
            continue
        paso = max(1, len(lista) // (POR_FAMILIA + 1))
        elegidas.extend(lista[paso::paso][:POR_FAMILIA])
    return elegidas


def generar(carpeta: Path, destino: Path, perfil: Path, remedir: bool = False) -> Path:
    """Genera esta cancion y devuelve SU carpeta, no la ultima de la lista.

    Ese detalle costo una tanda entera: todas las canciones caen en el mismo
    `destino`, asi que "la ultima por orden alfabetico" deja de ser la recien
    hecha en cuanto una cancion se ordena antes que otra ya generada. Con diez
    canciones, cinco se midieron contra el chart de The Sex Pistols y salieron
    con acordes y densidad identicos -- que es exactamente el aspecto que
    tendria el cambio si no funcionase.
    """
    antes = {p for p in destino.iterdir() if p.is_dir()} if destino.is_dir() else set()
    esperada = destino / (carpeta.name + " (AutoChart)")
    if remedir and esperada.is_dir():
        return esperada
    semilla = zlib.crc32(carpeta.name.encode("utf-8")) % 100000
    orden = [sys.executable, "-m", "autochart", "generar", str(carpeta),
             "--salida", str(destino), "--dificultades", "Expert",
             "--semilla", str(semilla), "--perfil", str(perfil)]
    r = subprocess.run(orden, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(RAIZ))
    if r.returncode:
        print(r.stdout[-600:])
        raise SystemExit("[X] fallo generando " + carpeta.name)
    if esperada.is_dir():
        return esperada
    nuevas = [p for p in destino.iterdir() if p.is_dir() and p not in antes]
    if not nuevas:
        raise SystemExit("[X] no aparecio carpeta nueva para " + carpeta.name)
    return nuevas[0]


def medir(humana: Path, generada: Path) -> dict:
    fila: dict = {"cancion": humana.name,
                  "genero": atlas.normalizar_genero(corpus._leer_genero(humana))}
    humanas, nuestras = human_note_times(humana), generated_note_times(generada)
    if humanas is not None and nuestras is not None and len(humanas) and len(nuestras):
        desfase = best_offset(humanas, nuestras)
        recall = match_ratio(humanas, nuestras + desfase)
        precision = match_ratio(nuestras + desfase, humanas)
        fila["recall"] = round(float(recall), 4)
        fila["f1"] = round(float(2 * recall * precision / (recall + precision)
                                 if (recall + precision) else 0.0), 4)
    va, vb = vector_de_gestos(generada), vector_de_gestos(humana)
    if va is not None and vb is not None:
        fila["distancia"] = round(float(distancia(va, vb)), 4)
    ph, pn = perfil_corto(humana), perfil_corto(generada)
    if ph and pn:
        for clave in ("nps", "acordes", "sostenidos", "repeticion", "ligadas"):
            fila["h_" + clave] = round(float(ph[clave]), 4)
            fila["g_" + clave] = round(float(pn[clave]), 4)
    return fila


def comparar(antes: Path, ahora: Path) -> int:
    a = {f["cancion"]: f for f in json.loads(antes.read_text(encoding="utf-8"))}
    b = {f["cancion"]: f for f in json.loads(ahora.read_text(encoding="utf-8"))}
    comunes = [c for c in a if c in b]
    print("{:8s} {:38s} {:>10s} {:>7s}   {:>6s}".format(
        "genero", "cancion", "dist antes", "ahora", "d F1"))
    mejoras = 0
    for c in sorted(comunes, key=lambda c: a[c].get("genero", "")):
        da, db = a[c].get("distancia"), b[c].get("distancia")
        if da is None or db is None:
            continue
        marca = "+" if db < da - 0.0005 else ("-" if db > da + 0.0005 else "=")
        mejoras += 1 if db < da - 0.0005 else 0
        print("{:8s} {:38s} {:10.3f} {:7.3f} {:1s} {:+6.3f}".format(
            a[c].get("genero", "?"), c[:38], da, db, marca,
            b[c].get("f1", 0) - a[c].get("f1", 0)))

    def media(d, k):
        vals = [d[c][k] for c in comunes if d[c].get(k) is not None]
        return sum(vals) / len(vals) if vals else float("nan")

    print("\n{:47s} {:10.3f} {:7.3f}".format("MEDIA distancia", media(a, "distancia"),
                                             media(b, "distancia")))
    print("{:47s} {:10.3f} {:7.3f}".format("F1 medio", media(a, "f1"), media(b, "f1")))

    # El error contra SU humano, metrica a metrica. La distancia de gestos las
    # resume todas y por eso puede tapar un empeoramiento: una tanda que arregla
    # los sostenidos y estropea los acordes se ve igual desde arriba.
    def error(d, clave):
        vals = [abs(d[c]["g_" + clave] - d[c]["h_" + clave]) for c in comunes
                if d[c].get("g_" + clave) is not None and d[c].get("h_" + clave) is not None]
        return sum(vals) / len(vals) if vals else float("nan")

    print("")
    for clave in ("nps", "acordes", "sostenidos", "repeticion", "ligadas"):
        ea, eb = error(a, clave), error(b, clave)
        marca = "+" if eb < ea - 0.0005 else ("-" if eb > ea + 0.0005 else "-")
        print("{:47s} {:10.3f} {:7.3f} {}".format("error de " + clave, ea, eb,
                                                  "=" if abs(eb - ea) <= 0.0005 else marca))

    print("\nmejoran {} de {}".format(mejoras, len(comunes)))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--perfil", default="datos/perfil_oro.json")
    p.add_argument("--salida", default="salida/panel.json")
    p.add_argument("--charts", default=None, help="Donde dejar los charts generados")
    p.add_argument("--comparar", nargs=2, metavar=("ANTES", "AHORA"), default=None)
    p.add_argument("--remedir", action="store_true",
                   help="No regenerar lo que ya este en --charts, solo medirlo")
    args = p.parse_args(argv)

    if args.comparar:
        return comparar(Path(args.comparar[0]), Path(args.comparar[1]))

    destino = Path(args.charts or (Path(args.salida).with_suffix("") / "charts"))
    destino.mkdir(parents=True, exist_ok=True)
    canciones = elegir(BIBLIOTECA)
    print("[*] {} canciones, perfil {}".format(len(canciones), args.perfil))
    filas = []
    for i, carpeta in enumerate(canciones, 1):
        print("  [{}/{}] {}".format(i, len(canciones), carpeta.name[:60]))
        generada = generar(carpeta, destino, Path(args.perfil), args.remedir)
        filas.append(medir(carpeta, generada))
    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.salida).write_text(json.dumps(filas, indent=1, ensure_ascii=False),
                                 encoding="utf-8")
    print("[OK] " + args.salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
