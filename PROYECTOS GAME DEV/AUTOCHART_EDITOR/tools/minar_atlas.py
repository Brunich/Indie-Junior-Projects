"""Saca el atlas de patrones de la biblioteca y lo cuenta en pantalla.

    python tools/minar_atlas.py
    python tools/minar_atlas.py --dificultades Expert,Hard
    python tools/minar_atlas.py --ver genero        # que se toca en cada genero
    python tools/minar_atlas.py --ver instrumento   # guitarra vs bajo vs ritmica
    python tools/minar_atlas.py --ver pack

Escribe `datos/atlas_patrones.json`. No toca la biblioteca.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from autochart import atlas  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
SALIDA = RAIZ / "datos" / "atlas_patrones.json"

# Los que mas dicen de como se SIENTE tocar algo.
DESTACADOS = ("tremolo", "trino", "escalera_sube", "escalera_baja", "zigzag",
              "galope", "rafaga", "acorde_martillo", "acorde_movil",
              "acorde_alterno", "anclado", "abierta_bombeo", "cadena_sostenidos")


def tabla(atlas_datos: dict, seccion: str, titulo: str, ancho: int = 26) -> None:
    grupos = atlas_datos.get(seccion, {})
    if not grupos:
        return
    print(f"\n=== {titulo} ===")
    cabecera = (f"{'grupo':{ancho}} {'canc':>4} {'notas':>7} {'nps':>5} {'acor':>5} "
                f"{'sost':>5} {'liga':>5} {'sinc':>5} {'cobe':>5} {'contr':>6}")
    print(cabecera)
    print("-" * len(cabecera))
    for nombre, datos in sorted(grupos.items(), key=lambda kv: -kv[1]["canciones"]):
        print(f"{nombre[:ancho]:{ancho}} {datos['canciones']:>4} {datos['notas']:>7} "
              f"{datos['nps']['p50']:>5.2f} {datos['acordes']['p50']:>5.2f} "
              f"{datos['sostenidos']['p50']:>5.2f} {datos['ligadas']['p50']:>5.2f} "
              f"{datos['sincopa']['p50']:>5.2f} {datos['cobertura_licks']['p50']:>5.2f} "
              f"{datos['contraste']['p50']:>6.1f}")

    print(f"\n  vocabulario (veces por cada 100 notas)")
    encabezado = f"  {'grupo':{ancho}}" + "".join(f"{t[:7]:>8}" for t in DESTACADOS)
    print(encabezado)
    for nombre, datos in sorted(grupos.items(), key=lambda kv: -kv[1]["canciones"]):
        fila = f"  {nombre[:ancho]:{ancho}}"
        for tipo in DESTACADOS:
            fila += f"{datos['licks_por_100_notas'].get(tipo, 0):>8.2f}"
        print(fila)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Atlas de patrones de la biblioteca")
    parser.add_argument("--biblioteca", default=str(BIBLIOTECA))
    parser.add_argument("--salida", default=str(SALIDA))
    parser.add_argument("--dificultades", default="Expert")
    parser.add_argument("--ver", default="todo",
                        choices=("todo", "genero", "instrumento", "pack", "velocidad",
                                 "dificultad", "cruce"))
    parser.add_argument("--solo-oro", metavar="CORPUS_ORO.JSON", default=None,
                        help="mina solo las pistas marcadas como oro en ese json "
                             "(lo produce tools/elegir_oro.py). Sirve para comparar "
                             "la vara de TODA la biblioteca contra la de los buenos.")
    args = parser.parse_args(argv)

    biblioteca = Path(args.biblioteca)
    if not biblioteca.is_dir():
        print(f"[X] No existe la biblioteca: {biblioteca}")
        return 2

    # se comprueba ANTES de escanear: el escaneo son seis minutos
    ruta_oro = Path(args.solo_oro) if args.solo_oro else None
    if ruta_oro is not None and not ruta_oro.is_file():
        print(f"[X] No existe el corpus de oro: {ruta_oro}")
        print("    Correlo antes: python tools/elegir_oro.py")
        return 2

    dificultades = tuple(d.strip() for d in args.dificultades.split(","))
    print(f"[*] Leyendo patrones en {biblioteca}  (dificultades: {', '.join(dificultades)})")
    empezado = time.time()

    def progreso(indice: int, total: int, nombre: str, cuantas: int) -> None:
        if indice % 40 == 0 or indice == total:
            print(f"    {indice}/{total} carpetas...")

    rasgos = atlas.escanear(biblioteca, dificultades, al_progresar=progreso)

    fallos = getattr(atlas.escanear, "fallos", [])
    if fallos:
        print(f"\n[!] {len(fallos)} carpetas se cayeron al leerlas y NO estan en el atlas:")
        for nombre, motivo in fallos[:12]:
            print(f"      {nombre[:44]:44} {motivo[:44]}")
        if len(fallos) > 12:
            print(f"      ... y {len(fallos) - 12} mas")
    if not rasgos:
        print("\n[X] CERO pistas leidas. El atlas no se escribe: un fichero de ceros")
        print("    es peor que ninguno, porque parece una medida.")
        print(f"    Comprueba que {biblioteca} tiene canciones con notes.chart o notes.mid.")
        return 2

    if args.solo_oro:
        corpus = json.loads(ruta_oro.read_text(encoding="utf-8"))
        claves = {(f["pack"], f["cancion"]) for f in corpus["canciones"] if f["oro"]}
        antes = len(rasgos)
        rasgos = [r for r in rasgos if (r.pack, r.cancion) in claves]
        print(f"[*] Solo oro: {len(rasgos)} pistas de {antes} "
              f"({len(claves)} canciones marcadas en {ruta_oro.name})")
        if not rasgos:
            print("[X] Ninguna pista casa con el corpus. Se mira por (pack, cancion): "
                  "si la biblioteca cambio de sitio, vuelve a correr elegir_oro.py.")
            return 2

    datos = atlas.agregar(rasgos)
    destino = atlas.guardar(datos, args.salida)
    tardado = time.time() - empezado

    print(f"\n[OK] {datos['pistas_analizadas']} pistas usables de {datos['pistas_leidas']} "
          f"leidas en {tardado:.1f} s")
    print(f"     atlas -> {destino}")

    g = datos["global"]
    print(f"\n=== TODA LA BIBLIOTECA ({g['canciones']} canciones, {g['notas']} notas) ===")
    for clave, etiqueta in (("nps", "notas por segundo"), ("npb", "notas por tiempo"),
                            ("acordes", "acordes"), ("abiertas", "abiertas"),
                            ("sostenidos", "sostenidos"), ("repeticion", "repite traste"),
                            ("ligadas", "ligadas"), ("sincopa", "fuera de pulso"),
                            ("cobertura_licks", "notas dentro de un patron"),
                            ("contraste", "contraste de densidad")):
        d = g[clave]
        print(f"     {etiqueta:28} p5 {d['p5']:>7} p25 {d['p25']:>7} p50 {d['p50']:>7} "
              f"p75 {d['p75']:>7} p95 {d['p95']:>7}")

    print(f"\n     patrones por cada 100 notas, y que parte de las notas cubren:")
    for tipo in atlas.TIPOS_LICK:
        veces = g["licks_por_100_notas"].get(tipo, 0)
        cobertura = g["licks_cobertura"].get(tipo, 0)
        print(f"       {tipo:20} {veces:>7.2f} veces   {cobertura * 100:>5.1f} % de las notas")

    print(f"\n     figuras ritmicas mas usadas:")
    for figura, parte in list(g["figuras"].items())[:10]:
        print(f"       {figura:8} {parte * 100:5.1f} %")

    print(f"\n     giros ritmicos de 4 golpes mas repetidos:")
    for giro, parte in list(g["ritmo_4gramas"].items())[:10]:
        print(f"       {giro:32} {parte * 100:5.2f} %")

    print(f"\n     giros de movimiento de mano mas repetidos (pasos de carril):")
    for giro, parte in list(g["forma_3gramas"].items())[:10]:
        print(f"       {giro:12} {parte * 100:5.2f} %")

    if args.ver in ("todo", "instrumento"):
        tabla(datos, "por_instrumento", "POR INSTRUMENTO")
    if args.ver in ("todo", "genero"):
        tabla(datos, "por_genero", "POR GENERO")
    if args.ver in ("todo", "velocidad"):
        tabla(datos, "por_velocidad", "POR VELOCIDAD")
    if args.ver in ("todo", "pack"):
        tabla(datos, "por_pack", "POR ORIGEN", ancho=38)
    if args.ver in ("todo", "dificultad"):
        tabla(datos, "por_dificultad", "POR DIFICULTAD")
    if args.ver == "cruce":
        tabla(datos, "por_genero_instrumento", "GENERO x INSTRUMENTO", ancho=24)

    print("\n=== ETIQUETAS DE GENERO TAL Y COMO ESTAN ESCRITAS ===")
    for etiqueta, cuantas in list(datos["generos_crudos"].items())[:25]:
        print(f"     {cuantas:>4}  {etiqueta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
