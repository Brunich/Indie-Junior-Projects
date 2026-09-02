"""Pone letra de karaoke a las canciones que no la tienen.

    python tools/poner_letra.py "<carpeta de la cancion>"
    python tools/poner_letra.py --pack "13_Customs - Memes & Humor"
    python tools/poner_letra.py --pack 10 --pack 13 --pack 14
    python tools/poner_letra.py --pack 10 --sin-audio     # rapido, sin verificar

**No escribe en la biblioteca.** Deja el fichero listo en
`salida/letras/<carpeta>/` y hay que copiarlo a mano desde el Explorador de
Windows, porque `OneDrive\\Documents` rechaza las escrituras de consola. Se
escribe SOLO el `notes.chart` o el `notes.mid`, no la carpeta entera: asi se
copia un fichero encima y ya.

Despues, **SCAN SONGS** en el juego o sigue sonando el de la cache.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from autochart import chartio, letras, silabas, voz  # noqa: E402
from autochart.export import read_song_ini  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
SALIDA = RAIZ / "salida" / "letras"
RESPALDO = RAIZ / "salida" / "respaldo_letras"
AUDIO = (".ogg", ".mp3", ".opus", ".wav", ".flac")


def duracion_de(carpeta: Path, info: dict) -> float:
    try:
        valor = float(info.get("song_length", 0)) / 1000.0
        if valor > 5:
            return valor
    except (TypeError, ValueError):
        pass
    return 0.0


def audio_de(carpeta: Path) -> Path | None:
    """El fichero con la voz dentro: la mezcla, nunca un stem de guitarra."""
    for nombre in ("song", "vocals"):
        for extension in AUDIO:
            candidato = carpeta / f"{nombre}{extension}"
            if candidato.is_file():
                return candidato
    todos = [f for f in carpeta.iterdir() if f.suffix.lower() in AUDIO]
    sin_stems = [f for f in todos if not any(m in f.stem.lower()
                 for m in ("guitar", "bass", "drums", "rhythm", "keys"))]
    # Si lo unico que hay es un stem, ese stem ES la cancion entera: hay carpetas
    # con solo `guitar.ogg` y ahi tambien suena la voz.
    elegibles = sin_stems or todos
    return max(elegibles, key=lambda f: f.stat().st_size) if elegibles else None


def idioma_de(info: dict, lineas: list) -> str:
    muestra = " ".join(l.texto for l in lineas[:40])
    return silabas.detectar_idioma(muestra) if muestra else "es"


def _era_nuestra(carpeta: Path) -> bool:
    """Segundo criterio, para la letra que pusimos ANTES de que hubiera firma.

    Si hay respaldo de esa cancion y el respaldo NO traia letra, entonces la que
    hay ahora la pusimos nosotros. Es exactamente el criterio de
    `instalar_letras --devolver-humanas`, y cubre las 200 canciones que se
    instalaron antes de que la marca existiera.
    """
    copia = RESPALDO / carpeta.name
    if not copia.is_dir():
        return False
    try:
        original = voz.leer_voz(copia)
    except Exception:
        return False
    return original is None or len(original.silabas) < 20


def procesar(carpeta: Path, args) -> tuple[str, str]:
    """Devuelve (estado, detalle).

    Estados: ok / ya / instrumental / sin_letra / no_cuadra / error.
    `instrumental` y `sin_letra` NO son lo mismo y por eso van separados: la
    primera esta terminada (no hay nada que cantar) y la segunda es trabajo
    pendiente. Mezcladas, las dos parecen un hueco y no se sabe cual perseguir.
    """
    info = read_song_ini(carpeta)
    artista = info.get("artist", "").strip()
    titulo = info.get("name", "").strip() or carpeta.name
    duracion = duracion_de(carpeta, info)

    try:
        existente = voz.leer_voz(carpeta)
    except Exception:
        existente = None
    if existente and len(existente.silabas) >= 20:
        if not args.forzar:
            return "ya", f"ya trae {len(existente.silabas)} silabas"
        # `--forzar` rehace LA NUESTRA, no la de una persona. Pisar una letra
        # cronometrada a mano es perder trabajo que no sabemos rehacer igual de
        # bien, y ya paso una vez con 112 canciones.
        if not (letras.la_escribio_autochart(carpeta) or _era_nuestra(carpeta))                 and not args.pisar_humanas:
            return "ya", (f"la escribio una persona ({len(existente.silabas)} silabas): "
                          f"no se pisa. Con --pisar-humanas si.")

    ruta_audio = None if args.sin_audio else audio_de(carpeta)
    candidatas = letras.buscar(artista, titulo, duracion)
    if not candidatas:
        return "sin_letra", "LRCLIB no tiene esta cancion (no es lo mismo que instrumental)"
    elegida = letras.elegir(candidatas, duracion, habra_audio=ruta_audio is not None)
    if elegida is None:
        naturaleza = letras.parece_instrumental(candidatas, artista, duracion)
        if naturaleza.instrumental:
            return "instrumental", naturaleza.motivo
        cercana = candidatas[0]
        return "sin_letra", (f"ninguna cuadra en duracion (la mejor: "
                             f"{cercana.duracion:.0f}s contra {duracion:.0f}s"
                             f"{', sin tiempos' if not cercana.tiene_tiempos else ''})")

    lineas = letras.leer_lrc(elegida.sincronizada)
    if len(lineas) < 4:
        return "sin_letra", f"la letra sincronizada trae {len(lineas)} lineas"

    veredicto = letras.verificar(lineas, duracion, elegida.duracion, ruta_audio)
    if not veredicto.vale:
        return "no_cuadra", veredicto.motivo

    idioma = idioma_de(info, lineas)
    destino_dir = Path(args.salida) / carpeta.name
    chart_path = carpeta / "notes.chart"
    mid_path = carpeta / "notes.mid"

    if chart_path.is_file():
        chart = chartio.parse_chart(chart_path)
        frases = letras.construir_frases(lineas, idioma, veredicto.desfase,
                                         duracion=duracion)
        escritas = letras.escribir_en_chart(chart, frases)
        destino_dir.mkdir(parents=True, exist_ok=True)
        chartio.write_chart(chart, destino_dir / "notes.chart")
        formato = "chart"
    elif mid_path.is_file():
        frases = letras.construir_frases(lineas, idioma, veredicto.desfase,
                                         duracion=duracion)
        escritas = letras.escribir_en_midi(mid_path, frases, destino_dir / "notes.mid")
        formato = "mid"
    else:
        return "error", "la carpeta no tiene ni notes.chart ni notes.mid"

    return "ok", (f"{len(frases)} frases, {escritas} silabas [{idioma}] "
                  f"-> {formato}  ({veredicto.motivo})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pone letra de karaoke")
    parser.add_argument("carpeta", nargs="?", default=None)
    parser.add_argument("--pack", action="append", default=[],
                        help="Nombre (o prefijo numerico) de un pack. Se puede repetir")
    parser.add_argument("--biblioteca", default=str(BIBLIOTECA))
    parser.add_argument("--salida", default=str(SALIDA))
    parser.add_argument("--forzar", action="store_true",
                        help="Rehace la letra que ya haya puesto AutoChart")
    parser.add_argument("--pisar-humanas", action="store_true",
                        help="Rehace TAMBIEN la letra escrita a mano (piensalo dos veces)")
    parser.add_argument("--sin-audio", action="store_true",
                        help="No verifica contra el audio (mas rapido, menos seguro)")
    parser.add_argument("--todo", action="store_true",
                        help="Toda la biblioteca, sin tener que nombrar los packs")
    parser.add_argument("--limite", type=int, default=None)
    args = parser.parse_args(argv)

    biblioteca = Path(args.biblioteca)
    carpetas: list[Path] = []
    if args.carpeta:
        carpetas = [Path(args.carpeta)]
    elif args.todo:
        carpetas = sorted({q.parent for patron in ("**/notes.chart", "**/notes.mid")
                           for q in biblioteca.glob(patron)})
    elif args.pack:
        for pedido in args.pack:
            encontrado = [d for d in biblioteca.iterdir()
                          if d.is_dir() and (d.name == pedido or d.name.startswith(f"{pedido}_"))]
            if not encontrado:
                # Avisar y seguir, NO abortar: la biblioteca se reorganiza y un
                # nombre de pack viejo tiraba las 390 canciones de la tanda.
                print(f"[--] No hay ningun pack que empiece por {pedido!r}, lo salto")
                continue
            for pack in encontrado:
                carpetas += sorted(d for d in pack.iterdir() if d.is_dir())
        if not carpetas:
            print("[X] Ninguno de los packs pedidos existe. Los que hay:")
            for d in sorted(x for x in biblioteca.iterdir() if x.is_dir()):
                print(f"      {d.name}")
            return 2
    else:
        parser.error("hace falta una carpeta, --pack o --todo")

    if args.limite:
        carpetas = carpetas[:args.limite]

    print(f"[*] {len(carpetas)} canciones. Fuente: LRCLIB. "
          f"Verificacion con audio: {'NO' if args.sin_audio else 'si'}")
    print(f"    salida -> {args.salida}\n")

    cuenta = {"ok": 0, "ya": 0, "instrumental": 0, "sin_letra": 0,
              "no_cuadra": 0, "error": 0}
    empezado = time.time()
    for indice, carpeta in enumerate(carpetas, 1):
        try:
            estado, detalle = procesar(carpeta, args)
        except Exception as error:
            estado, detalle = "error", f"{type(error).__name__}: {error}"
        cuenta[estado] = cuenta.get(estado, 0) + 1
        marca = {"ok": "[OK]", "ya": "[--]", "instrumental": "[IN]",
                 "sin_letra": "[  ]", "no_cuadra": "[!!]", "error": "[XX]"}[estado]
        if estado != "ya" or args.carpeta:
            print(f"  {marca} {carpeta.name[:44]:44} {detalle}")
        if indice % 25 == 0:
            print(f"       ... {indice}/{len(carpetas)}")

    print(f"\n[OK] {cuenta['ok']} con letra nueva | {cuenta['ya']} ya la tenian | "
          f"{cuenta['sin_letra']} sin fuente | {cuenta['no_cuadra']} no cuadraban | "
          f"{cuenta['error']} errores    ({time.time() - empezado:.0f} s)")
    if cuenta["ok"]:
        print(f"\n     Para probarlas: copia cada notes.chart / notes.mid de")
        print(f"     {args.salida}")
        print(f"     a su carpeta en Songs\\ DESDE EL EXPLORADOR, y haz SCAN SONGS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
