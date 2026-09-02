"""El traste, sigue a la melodia que suena?

Bruno, 22-08-2026: *"el resultado al final es que se sienta como si se estuviera
tocando ese instrumento que se esta tocando, no importa si sea una voz; al final
siguen siendo notas musicales"* y *"cuando cambia de nota suele cambiar el patron
en el chart"*.

Eso es una medida y **este proyecto no la tenia**. Lo que hay mide CUANDO suena
la nota (el banco, F1), QUE forma tiene el gesto (atlas, transiciones,
parecidas) y DE QUE instrumento es el ataque (quien_toca). Ninguna mira si el
traste se mueve cuando se mueve el tono, que es literalmente lo que hace que se
sienta que tocas la cancion.

    python tools/sigue_la_melodia.py "<carpeta de cancion>"            # su audio
    python tools/sigue_la_melodia.py "<carpeta>" --audio guitar.ogg    # aislada
    python tools/sigue_la_melodia.py --humanos 12                      # biblioteca

La referencia son las canciones con `guitar.ogg`: ahi el audio ES el instrumento
que el chart hace tocar, sin bateria ni voz que confundan. La biblioteca tiene
283 asi.

Se compara, entre nota y nota:

    tono   sube / baja / se queda   (CQT en la banda de la solista)
    traste sube / baja / se queda   (el chart)

y se cuenta cuantas veces coinciden. El azar no es 33 %: depende de cuantas
veces se repite el traste. Por eso se mide tambien el AZAR de cada cancion
barajando sus propios trastes, y lo que importa es la diferencia.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autochart import audio, chartio, midiio  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
# Cuanto tiene que moverse el tono para llamarlo movimiento. Es el mismo umbral
# con el que el generador decide sacar la mano de un traste repetido.
ZONA_MUERTA_SEMITONOS = 0.75
MINIMO_PAREJAS = 40


def notas_con_traste(carpeta: Path, pista: str = "ExpertSingle"):
    """(instante, trastes) de cada golpe, venga de `.chart` o de `.mid`."""
    ruta_chart = carpeta / "notes.chart"
    if ruta_chart.is_file():
        chart = chartio.parse_chart(ruta_chart)
        track = chart.tracks.get(pista)
        if track is None:
            return None, f"no hay pista {pista}"
        por_tick: dict[int, set[int]] = {}
        for n in track.notes:
            if n.fret < 5:
                por_tick.setdefault(n.tick, set()).add(n.fret)
        if not por_tick:
            return None, "pista vacia"
        return [(chart.tick_to_seconds(t), sorted(f))
                for t, f in sorted(por_tick.items())], "chart"

    ruta_mid = carpeta / "notes.mid"
    if not ruta_mid.is_file():
        return None, "no hay notes.chart ni notes.mid"
    chart, pistas = midiio.parse_midi_multi(ruta_mid)
    dificultad = next((d for d in ("Expert", "Hard", "Medium", "Easy")
                       if pista.startswith(d)), "Expert")
    notas = (pistas.get("guitarra") or {}).get(dificultad)
    if not notas:
        return None, f"el midi no trae guitarra/{dificultad}"
    por_tick: dict[int, set[int]] = {}
    for n in notas:
        f = getattr(n, "fret", 0)
        if f < 5:
            por_tick.setdefault(n.tick, set()).add(f)
    if not por_tick:
        return None, "pista vacia"
    return [(chart.tick_to_seconds(t), sorted(f))
            for t, f in sorted(por_tick.items())], "midi"


def tonos_en(ruta_audio: Path, instantes: list[float]) -> np.ndarray:
    """El tono dominante de la banda de la solista en cada instante.

    Llama a `audio.contorno_de_tono`, que es exactamente lo que usa el
    generador, y lo lee en los instantes del CHART en vez de en los ataques
    detectados. Asi la comparacion es contra lo que el generador ve.
    """
    import librosa

    y, sr = librosa.load(str(ruta_audio), sr=audio.ANALYSIS_SR, mono=True)
    cqt = np.abs(librosa.cqt(
        y=y, sr=sr, hop_length=audio.HOP_LENGTH,
        fmin=librosa.note_to_hz(audio.CQT_FMIN_NOTE),
        n_bins=audio.CQT_BINS, bins_per_octave=12))
    base = float(librosa.note_to_midi(audio.CQT_FMIN_NOTE))
    # LA MISMA funcion que usa el generador, no una copia: una medida que no
    # aplica la regla del programa no mide lo que crees (CLAUDE.md, trampa 5).
    contorno = audio.contorno_de_tono(cqt, base)
    ventana = max(2, int(0.07 * sr / audio.HOP_LENGTH))

    salida = np.zeros(len(instantes), dtype=float)
    for i, t in enumerate(instantes):
        cuadro = int(round(t * sr / audio.HOP_LENGTH))
        if cuadro < 0 or cuadro >= contorno.size:
            continue
        tramo = contorno[cuadro:min(contorno.size, cuadro + ventana)]
        vivos = tramo[tramo > 0]
        if vivos.size:
            salida[i] = float(np.median(vivos))
    return salida


def _signo(valor: float, zona: float) -> int:
    if valor > zona:
        return 1
    if valor < -zona:
        return -1
    return 0


def medir(carpeta: Path, ruta_audio: Path, pista: str = "ExpertSingle",
          semilla: int = 7) -> dict | None:
    notas, fuente = notas_con_traste(carpeta, pista)
    if notas is None:
        return {"error": fuente}
    instantes = [t for t, _ in notas]
    # el traste de referencia del golpe es el mas grave: en un acorde es la raiz
    trastes = [min(f) for _, f in notas]
    tonos = tonos_en(ruta_audio, instantes)

    parejas = []
    for i in range(1, len(notas)):
        if tonos[i] == 0.0 or tonos[i - 1] == 0.0:
            continue
        parejas.append((tonos[i] - tonos[i - 1], trastes[i] - trastes[i - 1], i))
    if len(parejas) < MINIMO_PAREJAS:
        return {"error": f"solo {len(parejas)} parejas con tono conocido"}

    aciertos = quietas = 0
    tono_se_mueve_traste_no = traste_se_mueve_tono_no = 0
    for dtono, dtraste, _ in parejas:
        st, sf = _signo(dtono, ZONA_MUERTA_SEMITONOS), _signo(float(dtraste), 0.0)
        if st == sf:
            aciertos += 1
            if st == 0:
                quietas += 1
        if st != 0 and sf == 0:
            tono_se_mueve_traste_no += 1
        if sf != 0 and st == 0:
            traste_se_mueve_tono_no += 1

    # El azar de ESTA cancion: mismos trastes, mismos tonos, otro orden.
    rng = random.Random(semilla)
    azar_total = 0.0
    for _ in range(20):
        barajados = trastes[:]
        rng.shuffle(barajados)
        buenos = 0
        for dtono, _, i in parejas:
            sf = _signo(float(barajados[i] - barajados[i - 1]), 0.0)
            if _signo(dtono, ZONA_MUERTA_SEMITONOS) == sf:
                buenos += 1
        azar_total += buenos / len(parejas)
    azar = azar_total / 20

    total = len(parejas)
    return {
        "fuente": fuente,
        "notas": len(notas),
        "parejas": total,
        "acierto": aciertos / total,
        "azar": azar,
        "ventaja": aciertos / total - azar,
        "tono_se_mueve_traste_no": tono_se_mueve_traste_no / total,
        "traste_se_mueve_tono_no": traste_se_mueve_tono_no / total,
        "quietas": quietas / total,
    }


def _con_guitarra_aislada(raiz: Path, cuantas: int) -> list[Path]:
    """Una por pack primero, para no medir doce canciones del mismo juego."""
    encontradas: list[Path] = []
    packs = sorted(p for p in raiz.iterdir() if p.is_dir() and not p.name.startswith("_"))
    for vuelta in range(6):
        for pack in packs:
            vistas = 0
            for cancion in sorted(p for p in pack.iterdir() if p.is_dir()):
                if not (cancion / "guitar.ogg").is_file():
                    continue
                if not ((cancion / "notes.mid").is_file() or (cancion / "notes.chart").is_file()):
                    continue
                if cancion in encontradas:
                    continue
                vistas += 1
                if vistas <= vuelta:
                    continue
                encontradas.append(cancion)
                break
            if len(encontradas) >= cuantas:
                return encontradas
    return encontradas


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="El traste, sigue a la melodia?")
    parser.add_argument("carpeta", nargs="?", default=None)
    parser.add_argument("--audio", default=None,
                        help="nombre del fichero de audio dentro de la carpeta")
    parser.add_argument("--pista", default="ExpertSingle")
    parser.add_argument("--humanos", type=int, default=0,
                        help="mide N canciones humanas con guitar.ogg")
    parser.add_argument("--biblioteca", default=str(BIBLIOTECA))
    args = parser.parse_args(argv)

    objetivos: list[tuple[Path, Path]] = []
    if args.humanos:
        for carpeta in _con_guitarra_aislada(Path(args.biblioteca), args.humanos):
            objetivos.append((carpeta, carpeta / "guitar.ogg"))
    if args.carpeta:
        carpeta = Path(args.carpeta)
        if args.audio:
            objetivos.append((carpeta, carpeta / args.audio))
        else:
            elegido = audio.pick_audio(carpeta)
            if elegido is None:
                print(f"[X] no encuentro audio en {carpeta}")
                return 2
            objetivos.append((carpeta, elegido))
    if not objetivos:
        parser.error("hace falta una carpeta o --humanos N")

    print("[*] El traste, sigue a la melodia que suena?")
    print(f"    {'cancion':40} {'acierto':>8} {'azar':>7} {'ventaja':>8}  tono se mueve")
    print(f"    {'':40} {'':>8} {'':>7} {'':>8}  y el traste no")
    filas = []
    for carpeta, ruta in objetivos:
        if not ruta.is_file():
            print(f"    {carpeta.name[:40]:40} (sin {ruta.name})")
            continue
        r = medir(carpeta, ruta, args.pista)
        if r is None or "error" in r:
            print(f"    {carpeta.name[:40]:40} {r['error'] if r else 'sin datos'}")
            continue
        filas.append(r)
        print(f"    {carpeta.name[:40]:40} {r['acierto']*100:7.1f}% {r['azar']*100:6.1f}% "
              f"{r['ventaja']*100:+7.1f}%  {r['tono_se_mueve_traste_no']*100:5.1f}%")
    if len(filas) > 1:
        med = lambda k: float(np.median([f[k] for f in filas]))  # noqa: E731
        print(f"\n    {'MEDIANA':40} {med('acierto')*100:7.1f}% {med('azar')*100:6.1f}% "
              f"{med('ventaja')*100:+7.1f}%  {med('tono_se_mueve_traste_no')*100:5.1f}%")
        print("\n    La ventaja es lo que importa: cuanto le saca el chart al azar de")
        print("    barajar sus propios trastes. Si sale 0, el traste no sabe nada del tono.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
