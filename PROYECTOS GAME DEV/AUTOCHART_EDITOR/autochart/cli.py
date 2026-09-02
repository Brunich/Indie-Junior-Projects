"""Linea de comandos de AutoChart.

    python -m autochart minar    --biblioteca "<Songs>"  --salida perfil.json
    python -m autochart generar  "<carpeta o audio>"     --salida salida/
    python -m autochart revisar  "<notes.chart>"
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

DEFAULT_LIBRARY = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
DEFAULT_PROFILE = Path(__file__).resolve().parent.parent / "datos" / "perfil_corpus.json"


def _load_profile(path: str | Path | None) -> dict | None:
    candidate = Path(path) if path else DEFAULT_PROFILE
    if candidate.is_file():
        from .corpus import load_profile

        return load_profile(candidate)
    return None


def cmd_minar(args: argparse.Namespace) -> int:
    from .corpus import aggregate, cargar_oro, save_profile, scan_library

    library = Path(args.biblioteca)
    if not library.is_dir():
        print(f"[X] No existe la biblioteca: {library}")
        return 2

    # se comprueba ANTES de escanear: leer la biblioteca entera son minutos
    oro = None
    if args.solo_oro:
        ruta_oro = Path(args.solo_oro)
        if not ruta_oro.is_file():
            print(f"[X] No existe el corpus de oro: {ruta_oro}")
            print("    Correlo antes: python tools/elegir_oro.py")
            return 2
        oro = cargar_oro(ruta_oro)
        if not oro:
            print(f"[X] {ruta_oro.name} no marca ni una cancion como oro.")
            return 2
        print(f"[*] Solo oro: {len(oro)} canciones marcadas en {ruta_oro.name}")

    print(f"[*] Analizando charts humanos en: {library}")
    started = time.time()

    def progress(count: int, stats) -> None:
        if count % 25 == 0:
            print(f"    {count} charts leidos... ultimo: {stats.song[:52]}")

    stats = scan_library(library, difficulty=args.dificultad, limit=args.limite,
                         on_progress=progress, solo_oro=oro)
    if not stats:
        print("[X] CERO charts leidos. El perfil no se escribe: un fichero de ceros")
        print("    es peor que ninguno, porque parece una medida.")
        if oro is not None:
            print("    Comprueba que los nombres de pack/cancion del corpus de oro")
            print(f"    son los de {library}.")
        return 2
    profile = aggregate(stats)

    # Los bloques por genero necesitan muestra: con los 60 charts del oro ningun
    # genero llega a los 12 que pide `corpus.MINIMO_POR_GENERO`, asi que el oro
    # se queda sin ellos. Se le prestan los de la biblioteca entera, que es
    # legitimo porque un bloque de genero NO es un nivel sino un desvio contra
    # su propia referencia (`by_genre._referencia`), y el generador lo aplica
    # como factor sobre las medianas del perfil activo.
    if args.solo_oro and DEFAULT_PROFILE.is_file():
        from .corpus import load_profile

        prestados = (load_profile(DEFAULT_PROFILE).get("by_genre") or {})
        faltan = [g for g in prestados if g not in profile["by_genre"]]
        for g in faltan:
            bloque = dict(prestados[g])
            bloque["prestado_de"] = DEFAULT_PROFILE.name
            profile["by_genre"][g] = bloque
        if faltan:
            print(f"    [i] generos sin muestra propia, prestados de "
                  f"{DEFAULT_PROFILE.name}: {', '.join(sorted(faltan))}")
        # La recta de densidad tambien se presta, y por la misma razon: con 60
        # charts todos densos su pendiente sale plana (0.0116 contra 0.0159) y
        # solo dos generos llegan al minimo. Es un desvio contra su propia
        # referencia, asi que viaja entre poblaciones sin mezclar niveles.
        prestada = load_profile(DEFAULT_PROFILE).get("nps_por_bpm")
        if prestada:
            prestada = dict(prestada, prestado_de=DEFAULT_PROFILE.name)
            profile["nps_por_bpm"] = prestada
            print("    [i] recta de densidad prestada de " + DEFAULT_PROFILE.name)

    destination = save_profile(profile, args.salida)
    elapsed = time.time() - started

    print(f"[OK] {profile['charts_analysed']} charts usables de {profile['songs_seen']} leidos "
          f"en {elapsed:.1f} s")
    nps = profile["notes_per_second"]
    print(f"     densidad (notas/s): p25={nps['p25']}  p50={nps['p50']}  p75={nps['p75']}")
    print(f"     acordes: p50={profile['chord_ratio']['p50']}   "
          f"sostenidos: p50={profile['sustain_ratio']['p50']}")
    print(f"     perfil guardado en: {destination}")
    return 0


def cmd_generar(args: argparse.Namespace) -> int:
    from .audio import analyse, pick_audio, pick_beat_audio
    from .export import export_song, read_song_ini
    from .generate import generate_chart
    from .validate import validate_chart

    source = Path(args.entrada)
    if not source.exists():
        print(f"[X] No existe: {source}")
        return 2

    audio_path = pick_audio(source)
    if audio_path is None:
        print(f"[X] No se encontro audio dentro de: {source}")
        return 2
    beat_path = pick_beat_audio(source) or audio_path

    source_dir = source if source.is_dir() else None
    info = read_song_ini(source_dir) if source_dir else {}
    # Un audio suelto suele venir de YouTube, con el artista y la basura del
    # titulo metidos en el nombre del fichero. Separarlos aqui es lo que luego
    # permite que `autochart letra` encuentre la cancion.
    from .export import artista_y_titulo

    suelto_artista, suelto_titulo = ("", "") if source_dir else artista_y_titulo(source.stem)
    name = args.nombre or info.get("name") or suelto_titulo or (
        source_dir.name if source_dir else source.stem)
    artist = args.artista or info.get("artist") or suelto_artista or "Desconocido"

    profile = _load_profile(args.perfil)
    pulse = "" if beat_path == audio_path else f" | pulso desde {beat_path.name}"
    print(f"[*] Audio: {audio_path.name}{pulse}"
          + ("" if profile else "   (sin perfil de corpus)"))

    started = time.time()
    analysis = analyse(audio_path, max_seconds=args.segundos, beat_audio_path=beat_path)
    print(f"    tempo detectado: {analysis.tempo:.1f} BPM | {len(analysis.onsets)} ataques | "
          f"{len(analysis.sections)} secciones | {analysis.duration:.0f} s")

    difficulties = tuple(args.dificultades.split(",")) if args.dificultades else (
        "Expert", "Hard", "Medium", "Easy"
    )

    # Si la cancion ya trae la letra alineada, sus silabas son sitios donde
    # tiene que haber nota: es lo que hace que se sienta que tocas lo que se
    # canta en vez de ir por otro lado. Ver docs/PLAN_MELODIA.md F1.
    silabas = None
    # ...pero solo si lo que estamos charteando ES la voz. Medido el 22-08-2026
    # en Pride & Joy: el rip trae 213 silabas cantadas, y al anclarlas el chart
    # perdia el 19 % de sus notas (819 -> 661) porque `thin` deja las ventanas
    # con canto SOLO con las silabas. En una cancion de guitarra eso es seguir
    # a quien canta en vez de al riff, que es justo lo contrario de lo que se
    # busca. Cuando las notas salen de una pista de guitarra aislada, sabemos
    # que instrumento se toca y la letra no manda.
    de_guitarra = audio_path.name.lower().startswith(("guitar", "rhythm", "lead"))
    if source_dir is not None and not de_guitarra:
        from .voz import leer_voz

        try:
            pista_voz = leer_voz(source_dir)
        except Exception:
            pista_voz = None
        if pista_voz is not None and len(pista_voz.silabas) >= 20:
            silabas = [pista_voz.tick_to_seconds(s.tick) for s in pista_voz.silabas]
            print(f"    letra alineada: {len(silabas)} silabas -> se ancla la melodia")
    chart, report = generate_chart(
        analysis, metadata={"Name": name, "Artist": artist}, profile=profile,
        difficulties=difficulties, seed=args.semilla,
        density=args.densidad, density_percentile=args.percentil,
        silabas=silabas, genero=info.get("genre", ""),
    )

    destination = Path(args.salida) / f"{artist} - {name} (AutoChart)"
    # export_song devuelve la ruta REAL: puede no ser la pedida, porque el
    # titulo de song.ini lleva caracteres que Windows no admite en una carpeta.
    destination = export_song(
        chart, destination, audio_path, source_dir=source_dir,
        name=name, artist=artist,
        album=info.get("album", ""), genre=info.get("genre", ""), year=info.get("year", ""),
        duration_s=analysis.duration,
    )

    check = validate_chart(chart, profile)
    elapsed = time.time() - started

    print(f"[OK] Generado en {elapsed:.1f} s -> {destination}")
    for difficulty, data in report.per_difficulty.items():
        print(f"     {difficulty:<7} {data['notas']:>5} notas  "
              f"{data['notas_por_segundo']:>5.2f} n/s  "
              f"acordes {data['acordes_pct']:>4.1f}%  "
              f"sostenidos {data['sostenidos_pct']:>4.1f}%  "
              f"ligadas {data['ligadas_pct']:>4.1f}% ({data['forzadas']} forzadas)  "
              f"SP {data['star_power']}")
    for warning in report.warnings + check.warnings:
        print(f"     [aviso] {warning}")
    for error in check.errors:
        print(f"     [ERROR] {error}")

    if args.informe:
        Path(args.informe).write_text(
            json.dumps(
                {
                    "cancion": name, "artista": artist, "audio": audio_path.name,
                    "tempo": report.tempo, "duracion": report.duration,
                    "ataques": report.onsets_detected, "secciones": report.sections,
                    "eventos_tempo": report.tempo_events,
                    "dificultades": report.per_difficulty,
                    "errores": check.errors, "avisos": check.warnings + report.warnings,
                    "metricas": check.metrics,
                },
                indent=2, ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"     informe: {args.informe}")
    return 0 if check.ok else 1


def cmd_separar(args: argparse.Namespace) -> int:
    """Parte una cancion en pistas para que el chart deje de escribir la bateria.

    Medido antes de esto (`tools/quien_toca.py`): el 58-63 % de las notas caian
    en un instante mas percusivo que armonico. Mientras la fuente sea la mezcla,
    lo mas fuerte de cada ventana es el bombo.
    """
    from . import separar as separador

    entrada = Path(args.entrada)
    if entrada.is_dir():
        from .audio import pick_audio
        mezcla = pick_audio(entrada)
        nombre = args.nombre or entrada.name
    else:
        mezcla = entrada if entrada.is_file() else None
        nombre = args.nombre or entrada.stem
    if mezcla is None:
        print(f"[X] No encuentro audio en: {entrada}")
        return 2

    ya = separador.stems_de(nombre, args.destino)
    if ya and not args.forzar:
        print(f"[=] {nombre}: ya estaba separada. --forzar para repetirla.")
    else:
        print(f"[*] Separando {nombre} ... (demucs en CPU, alrededor de 1 min por cada 2-3 min de cancion)")
        if separador.separar(mezcla, nombre=nombre, destino=args.destino,
                             forzar=args.forzar) is None:
            return 1

    pista = separador.pista_de_notas(nombre, args.destino)
    if pista is None:
        print("[X] Las pistas estan pero no se pudo mezclar la de notas (falta ffmpeg?)")
        return 1
    carpeta = separador.carpeta_de(nombre, args.destino)
    peso = sum(f.stat().st_size for f in carpeta.glob("*.ogg")) / 1e6
    print(f"[OK] {carpeta}  ({peso:.1f} MB)")
    for nombre_pista in (*separador.PISTAS, "notas"):
        f = carpeta / f"{nombre_pista}.ogg"
        if f.exists():
            marca = "  <- de aqui salen las notas" if nombre_pista == "notas" else ""
            print(f"     {nombre_pista:8} {f.stat().st_size / 1e6:>5.1f} MB{marca}")
    return 0


def cmd_revisar(args: argparse.Namespace) -> int:
    from .chartio import parse_chart
    from .validate import validate_chart

    path = Path(args.chart)
    if not path.is_file():
        print(f"[X] No existe: {path}")
        return 2
    chart = parse_chart(path)
    report = validate_chart(chart, _load_profile(args.perfil))
    print(f"[*] {path}")
    for name, metrics in report.metrics.items():
        print(f"     {name:<14} {metrics['notas']:>5} notas  {metrics['notas_por_segundo']:>5.2f} n/s  "
              f"acordes {metrics['acordes']:.2f}  sostenidos {metrics['sostenidos']:.2f}")
    for warning in report.warnings:
        print(f"     [aviso] {warning}")
    for error in report.errors:
        print(f"     [ERROR] {error}")
    print("[OK] El chart es valido." if report.ok else "[X] El chart tiene errores.")
    return 0 if report.ok else 1


def cmd_alinear(args: argparse.Namespace) -> int:
    """Pegar un chart que ya existe a su rejilla, o arreglarle el tempo."""
    from . import editar
    from .chartio import parse_chart, write_chart

    ruta = Path(args.carpeta)
    if ruta.is_dir():
        ruta = ruta / "notes.chart"
    if not ruta.is_file():
        print(f"[X] No existe: {ruta}")
        return 2

    chart = parse_chart(ruta)
    desvios = editar.medir_rejilla(chart, args.pista)
    if not desvios:
        print(f"[X] {ruta} no tiene pista {args.pista} con golpes suficientes")
        return 2

    print(f"[*] {ruta.parent.name}   pista {args.pista}   resolucion {chart.resolution}")
    print("")
    print("    rejilla     paso      encajan   desvio p50")
    for d in desvios:
        print(f"    1/{d.division:<2}   {d.paso:8.1f} tk   {100 * d.encajan:5.1f} %   "
              f"{d.p50_ticks:5.1f} tk")

    sugerida = editar.mejor_division(desvios)
    if sugerida:
        print(f"    -> la mas gruesa donde ya cae casi todo: 1/{sugerida}")
    division = args.division or sugerida or 4

    tempo = editar.buscar_tempo(chart, division, args.pista)
    if tempo is not None:
        print("")
        print(f"    en fase con el tempo escrito {100 * tempo.ahora:5.1f} %"
              f"   mejor factor {tempo.factor:.4f} -> {100 * tempo.concentracion:5.1f} %")
        if tempo.esta_mal and not args.tempo:
            print("    [!] Esto NO es temblor: el tempo escrito no es el de la cancion.")
            print(f"        Alinear no lo arregla. Primero:  --tempo {tempo.factor:.4f}")

    if args.solo_medir:
        return 0

    if args.tempo:
        tocados = editar.reescalar(chart, args.tempo)
        print("")
        print(f"    reescalado por {args.tempo:.4f}: {tocados} notas, todas las pistas")

    informe = editar.alinear(chart, division, args.pista)
    print("")
    print(f"    alinear a 1/{division}: {informe.movidos} de {informe.golpes} golpes movidos"
          f"   desvio p50 {informe.desvio_p50_ms:.0f} ms  max {informe.desvio_max_ms:.0f} ms")
    for aviso in informe.avisos:
        print(f"    [aviso] {aviso}")

    if args.probar:
        print("")
        print("[--] --probar: no se ha escrito nada.")
        return 0
    destino = Path(args.salida) if args.salida else ruta
    write_chart(chart, destino)
    print("")
    print(f"[OK] escrito en {destino}")
    print("     Si es un chart instalado, haz SCAN SONGS en el juego.")
    return 0

# Subcomando -> (fichero en tools/, para que sirve). Estan aqui para que no
# haya que saberse los 18 nombres de tools/: se descubren escribiendo
# `autochart` a secas.
HERRAMIENTAS = {
    "letra":         ("poner_letra", "Pone letra de karaoke: la busca, la verifica y la escribe"),
    "revisar-letra": ("revisar_letra", "Dice que letras salieron torcidas, sin abrir el juego"),
    "instalar":      ("instalar_letras", "Copia las letras a la biblioteca, con respaldo"),
    "censo":         ("censo_letras", "Que tiene letra, que falta y que es instrumental"),
    "atlas":         ("minar_atlas", "Mide QUE se toca: 16 gestos por genero e instrumento"),
    "voz":           ("minar_voz", "Mide la voz humana de la biblioteca -> perfil"),
    "comparar":      ("comparar_atlas", "Nuestro chart contra el humano, con la misma vara"),
    "patron":        ("ver_patron", "Ensena el patron de un chart generado"),
    "banco":         ("banco", "El control: genera y compara contra 24 charts humanos"),
    "en-juego":      ("revisar_in_game", "Si el juego puede cargarlo y jugarlo entero"),
    "puerta":        ("verificar_puerta", "Que la documentacion de entrada no engorde"),
}


def _correr_herramienta(nombre: str, argv: list[str]) -> int:
    """Ejecuta un script de tools/ como si lo hubieras llamado a mano."""
    import importlib.util

    fichero = Path(__file__).resolve().parent.parent / "tools" / (nombre + ".py")
    if not fichero.is_file():
        print("[X] Falta " + str(fichero))
        return 2
    sys.path.insert(0, str(fichero.parent))
    spec = importlib.util.spec_from_file_location("_tool_" + nombre, fichero)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    # No todas las herramientas aceptan argumentos: `verificar_puerta.main()` y
    # `revisar_in_game.main()` no llevan ninguno y leen `sys.argv` por su cuenta.
    # Se mira la firma en vez de adivinar: probar y cazar el TypeError tapaba
    # los TypeError de dentro de la herramienta, que son fallos de verdad.
    import inspect

    try:
        parametros = len(inspect.signature(modulo.main).parameters)
    except (TypeError, ValueError):
        parametros = 1
    if parametros:
        return modulo.main(argv)
    original = sys.argv
    try:
        sys.argv = [str(fichero), *argv]
        return modulo.main()
    finally:
        sys.argv = original


AYUDA = """
AutoChart - charts de 5 trastes para Clone Hero, sacados del audio

  QUIERO UNA CANCION NUEVA JUGABLE
    autochart generar "<carpeta o mp3>"     saca el chart, las 4 dificultades
    autochart en-juego salida               comprueba que el juego lo carga
    autochart comparar                      lo compara con el chart humano

  QUIERO LETRA PARA CANTAR
    autochart censo                         que tiene letra, que falta, que es instrumental
    autochart letra --pack 10               se la pone a un pack entero
    autochart revisar-letra                 cual salio torcida
    autochart instalar --probar             que copiaria a la biblioteca
    autochart instalar                      la copia (guardando el original)

  QUIERO SABER COMO SON LOS CHARTS BUENOS
    autochart minar                         densidad, acordes, sostenidos
    autochart atlas                         que se toca: 16 gestos por genero
    autochart voz                           como escribe la letra un humano

  ANTES DE DAR ALGO POR BUENO
    autochart banco --muestra 24            el control (tarda unos 7 min)
    autochart puerta                        que la documentacion no engorde

  O SIN ESCRIBIR NADA
    autochart interfaz                      una ventana: metes canciones y marcas

  Empieza por:   autochart estado
  Ayuda de uno:  autochart letra --help
"""


def cmd_estado(args: argparse.Namespace) -> int:
    """Que hay hoy y que conviene hacer. Sin leer ninguna documentacion."""
    import json

    raiz = Path(__file__).resolve().parent.parent
    biblioteca = Path(args.biblioteca)
    print("=== AutoChart: estado ===")
    print("")

    if biblioteca.is_dir():
        carpetas = {q.parent for patron in ("**/notes.chart", "**/notes.mid")
                    for q in biblioteca.glob(patron)}
        packs = len([d for d in biblioteca.iterdir() if d.is_dir()])
        print("  Biblioteca       %d canciones con chart, en %d packs"
              % (len(carpetas), packs))
    else:
        print("  Biblioteca       [X] no existe: %s" % biblioteca)

    faltan = []
    for nombre, fichero, clave, comando in (
        ("perfil de notas", "perfil_corpus.json", "charts_analysed", "minar"),
        ("perfil de voz", "perfil_voz.json", "canciones_con_voz", "voz"),
        ("atlas de patrones", "atlas_patrones.json", "pistas_analizadas", "atlas"),
    ):
        ruta = raiz / "datos" / fichero
        if ruta.is_file():
            try:
                datos = json.loads(ruta.read_text(encoding="utf-8"))
                print("  %-16s %s medidos  (%d KB)"
                      % (nombre, datos.get(clave, "?"), ruta.stat().st_size // 1024))
            except Exception:
                print("  %-16s [X] ilegible" % nombre)
        else:
            print("  %-16s falta" % nombre)
            faltan.append(comando)

    salida = raiz / "salida"
    if salida.is_dir():
        aparte = {"letras", "respaldo_letras", "airogue"}
        generados = [d for d in salida.iterdir() if d.is_dir() and d.name not in aparte]
        letras_dir = salida / "letras"
        cuantas = len([d for d in letras_dir.iterdir() if d.is_dir()]) if letras_dir.is_dir() else 0
        print("  En salida/       %d carpetas generadas, %d letras listas para instalar"
              % (len(generados), cuantas))

    censo = raiz / "datos" / "censo_letras.json"
    if censo.is_file():
        try:
            datos = json.loads(censo.read_text(encoding="utf-8"))
            from collections import Counter
            cuenta = Counter(v.get("estado", "?") for v in datos.values())
            print("  Censo de letra   %d se pueden poner ya, %d instrumentales, "
                  "%d que LRCLIB no tiene"
                  % (cuenta.get("FALTA", 0), cuenta.get("INSTR", 0), cuenta.get("NO_ESTA", 0)))
        except Exception:
            pass

    print("")
    print("  Lo siguiente, segun lo que quieras:")
    for comando in faltan:
        print("    falta una medida   ->  autochart %s" % comando)
    print("    jugar algo nuevo   ->  autochart generar <mp3 o carpeta>")
    print("    cantar             ->  autochart censo   (y luego: letra / instalar)")
    print("    mejorar el chart   ->  autochart comparar")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autochart",
        description="Genera charts de 5 trastes para Clone Hero a partir del audio.",
    )
    subparsers = parser.add_subparsers(dest="comando")

    miner = subparsers.add_parser("minar", help="Mide los charts humanos de tu biblioteca")
    miner.add_argument("--biblioteca", default=str(DEFAULT_LIBRARY))
    miner.add_argument("--salida", default=str(DEFAULT_PROFILE))
    miner.add_argument("--dificultad", default="Expert")
    miner.add_argument("--limite", type=int, default=None)
    miner.add_argument("--solo-oro", metavar="CORPUS_ORO.JSON", default=None,
                       help="mide solo los charts marcados como oro (lo produce "
                            "tools/elegir_oro.py). El perfil de TODA la biblioteca "
                            "es la mediana de lo mediano: el oro esta en 4.18 notas/s "
                            "contra 3.70 y en 29 % de acordes contra 34.8 %.")
    miner.set_defaults(func=cmd_minar)

    maker = subparsers.add_parser("generar", help="Crea un chart nuevo desde una cancion")
    maker.add_argument("entrada", help="Carpeta de cancion de Clone Hero o archivo de audio")
    maker.add_argument("--salida", default="salida")
    maker.add_argument("--perfil", default=None)
    maker.add_argument("--nombre", default=None)
    maker.add_argument("--artista", default=None)
    maker.add_argument("--dificultades", default=None, help="Ej: Expert,Hard")
    maker.add_argument("--semilla", type=int, default=7)
    maker.add_argument(
        "--densidad", type=float, default=1.0,
        help="Multiplica las notas por segundo objetivo. 1.3 = un 30 %% mas cargado",
    )
    maker.add_argument(
        "--percentil", default="p50", choices=("p25", "p50", "p75", "p95"),
        help="A que punto de la distribucion humana apuntar (p50 = la mediana)",
    )
    maker.add_argument("--segundos", type=float, default=None, help="Analizar solo los primeros N s")
    maker.add_argument("--informe", default=None, help="Ruta de un JSON con el informe")
    maker.set_defaults(func=cmd_generar)

    partidor = subparsers.add_parser(
        "separar", help="Parte una cancion en voz/bateria/bajo/resto (demucs)")
    partidor.add_argument("entrada", help="Carpeta de cancion de Clone Hero o archivo de audio")
    partidor.add_argument("--nombre", default=None)
    partidor.add_argument("--destino", default=str(Path("salida") / "stems"))
    partidor.add_argument("--forzar", action="store_true",
                          help="Rehacer aunque ya esten las cuatro pistas")
    partidor.set_defaults(func=cmd_separar)

    checker = subparsers.add_parser("revisar", help="Valida un notes.chart existente")
    checker.add_argument("chart")
    checker.add_argument("--perfil", default=None)
    checker.set_defaults(func=cmd_revisar)

    alineador = subparsers.add_parser(
        "alinear", help="Pega un chart que ya existe a su rejilla, o le arregla el tempo")
    alineador.add_argument("carpeta", help="Carpeta de la cancion o el notes.chart")
    alineador.add_argument("--division", type=int, default=None,
                           help="Golpes por tiempo: 4 = semicorchea. Sin esto, la mide")
    alineador.add_argument("--pista", default="ExpertSingle")
    alineador.add_argument("--tempo", type=float, default=None,
                           help="Estira el chart por este factor ANTES de alinear")
    alineador.add_argument("--solo-medir", action="store_true", dest="solo_medir",
                           help="Solo dice que rejilla tiene y si el tempo esta mal")
    alineador.add_argument("--probar", action="store_true", help="No escribe nada")
    alineador.add_argument("--salida", default=None, help="Escribir en otro sitio")
    alineador.set_defaults(func=cmd_alinear)

    grabadora = subparsers.add_parser(
        "grabar", help="Abre la ventana de grabar tocando encima de la cancion")
    grabadora.set_defaults(
        func=lambda _a: __import__("autochart.interfaz_grabar", fromlist=["abrir"]).abrir())

    ventana = subparsers.add_parser("interfaz", help="Abre una ventana para no escribir comandos")
    ventana.set_defaults(func=lambda _a: __import__("autochart.interfaz", fromlist=["abrir"]).abrir())

    estado = subparsers.add_parser("estado", help="Que hay hoy y que conviene hacer despues")
    estado.add_argument("--biblioteca", default=str(DEFAULT_LIBRARY))
    estado.set_defaults(func=cmd_estado)

    for subcomando, (fichero, ayuda) in HERRAMIENTAS.items():
        atajo = subparsers.add_parser(subcomando, help=ayuda, add_help=False)
        atajo.add_argument("resto", nargs=argparse.REMAINDER)
        atajo.set_defaults(herramienta=fichero)

    return parser


def _consola_que_aguante_cualquier_nombre() -> None:
    """Que un nombre de fichero raro no tumbe el programa.

    La consola de Windows va en cp1252. Un mp3 bajado de YouTube puede llamarse
    `Tame Impala - Loser (Sub. Espanol) ｜｜ Video Oficial.mp3`, con barras
    verticales de ancho completo, y el simple `print` del nombre reventaba con
    UnicodeEncodeError **despues de haber analizado la cancion entera**. Perder
    veinte segundos de trabajo por no poder imprimir un caracter es absurdo.
    """
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            try:
                flujo.reconfigure(errors="replace")
            except Exception:
                pass


def main(argv: list[str] | None = None) -> int:
    _consola_que_aguante_cualquier_nombre()
    entrada = list(sys.argv[1:] if argv is None else argv)

    # Las herramientas se despachan ANTES de parsear. argparse con REMAINDER no
    # captura las opciones que van pegadas al subcomando (`censo --sin-red` se
    # le escapa y protesta), y aqui lo que se quiere es pasarle a la herramienta
    # sus argumentos tal cual, sin que nadie los interprete por el camino.
    if entrada and entrada[0] in HERRAMIENTAS:
        fichero, _ = HERRAMIENTAS[entrada[0]]
        return _correr_herramienta(fichero, entrada[1:])

    parser = build_parser()
    args = parser.parse_args(entrada)
    if getattr(args, "comando", None) is None:
        print(AYUDA)
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
