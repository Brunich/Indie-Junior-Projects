"""Mide el silabeador contra los cortes que hicieron los humanos.

La idea: en un chart de voz, una silaba que acaba en `-` se pega a la siguiente.
O sea que las 128 canciones con voz de la biblioteca no solo traen la letra:
traen **las palabras ya partidas por una persona**. Eso es un corpus de
silabeo real en espanol y en ingles, gratis, y es mejor criterio que mi opinion.

    python tools/banco_silabas.py
    python tools/banco_silabas.py --idioma es --fallos 30

Se mide de dos maneras, porque no dicen lo mismo:

  - **palabra exacta**: el corte coincide entero. Es la dura.
  - **fronteras**: de todos los sitios donde el humano corto, cuantos acerte, y
    de los que yo corte, cuantos existian. Es la que dice si el fallo es grave
    (corto donde no toca) o leve (una silaba de mas en una palabra larga).

No escribe nada. Solo lee.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from autochart import silabas as S  # noqa: E402
from autochart import voz  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"

_SOLO_LETRAS = re.compile(r"^[^\W\d_]+$", re.UNICODE)


def palabras_partidas(pista: voz.PistaVoz) -> list[list[str]]:
    """Reconstruye las palabras con el corte humano puesto.

    Una silaba con `enlaza` sigue la palabra; la primera sin `enlaza` la cierra.
    Se tiran las que llevan marcadores raros o cifras: no son palabras cantadas.
    """
    salida: list[list[str]] = []
    actual: list[str] = []
    for silaba in pista.silabas:
        if silaba.desliza:
            continue
        trozo = silaba.palabra
        if not trozo:
            if actual:
                salida.append(actual)
                actual = []
            continue
        actual.append(trozo)
        if not silaba.enlaza:
            salida.append(actual)
            actual = []
    if actual:
        salida.append(actual)

    limpias = []
    for trozos in salida:
        # La puntuacion final no cuenta como parte de la palabra.
        trozos = [t.strip(".,;:!?\"'()¡¿…-") for t in trozos]
        if not all(t and _SOLO_LETRAS.match(t) for t in trozos):
            continue
        if sum(len(t) for t in trozos) < 3:
            continue
        limpias.append(trozos)
    return limpias


def fronteras(trozos: list[str]) -> set[int]:
    """Posiciones (en letras) donde se corto la palabra."""
    puntos, acumulado = set(), 0
    for trozo in trozos[:-1]:
        acumulado += len(trozo)
        puntos.add(acumulado)
    return puntos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Banco de silabeo contra el corpus humano")
    parser.add_argument("--biblioteca", default=str(BIBLIOTECA))
    parser.add_argument("--idioma", default="ambos", choices=("ambos", "es", "en"))
    parser.add_argument("--fallos", type=int, default=15, help="Cuantos fallos listar")
    args = parser.parse_args(argv)

    raiz = Path(args.biblioteca)
    if not raiz.is_dir():
        print(f"[X] No existe la biblioteca: {raiz}")
        return 2

    carpetas = sorted({p.parent for patron in ("**/notes.mid", "**/notes.chart")
                       for p in raiz.glob(patron)})
    print(f"[*] Buscando palabras ya partidas por humanos en {len(carpetas)} carpetas")

    por_idioma: dict[str, dict[str, object]] = {
        "es": {"canciones": 0, "palabras": Counter(), "casos": {}},
        "en": {"canciones": 0, "palabras": Counter(), "casos": {}},
    }

    for carpeta in carpetas:
        try:
            pista = voz.leer_voz(carpeta)
        except Exception:
            pista = None
        if pista is None or len(pista.silabas) < 40:
            continue
        texto = " ".join(f.texto for f in pista.frases[:60])
        idioma = S.detectar_idioma(texto)
        if args.idioma != "ambos" and idioma != args.idioma:
            continue
        por_idioma[idioma]["canciones"] += 1
        casos = por_idioma[idioma]["casos"]
        for trozos in palabras_partidas(pista):
            palabra = "".join(trozos)
            clave = palabra.lower()
            # Una palabra puede aparecer partida de dos maneras en canciones
            # distintas: se guarda la mas frecuente, no la ultima.
            casos.setdefault(clave, Counter())[tuple(trozos)] += 1

    print()
    for idioma in ("es", "en"):
        datos = por_idioma[idioma]
        casos: dict = datos["casos"]
        if not casos:
            continue
        exactas = 0
        total = 0
        multi_exactas = 0
        multi_total = 0
        acertadas = 0
        humanas = 0
        mias = 0
        fallos: list[tuple[str, str, str]] = []
        for clave, variantes in casos.items():
            trozos = list(max(variantes.items(), key=lambda kv: kv[1])[0])
            palabra = "".join(trozos)
            mio = S.dividir_palabra(palabra, idioma)
            total += 1
            if [t.lower() for t in mio] == [t.lower() for t in trozos]:
                exactas += 1
            elif len(fallos) < args.fallos and len(trozos) > 1:
                fallos.append((palabra, "-".join(trozos), "-".join(mio)))
            if len(trozos) > 1:
                multi_total += 1
                multi_exactas += int([t.lower() for t in mio] == [t.lower() for t in trozos])
            fh, fm = fronteras(trozos), fronteras(mio)
            acertadas += len(fh & fm)
            humanas += len(fh)
            mias += len(fm)

        nombre = "ESPANOL" if idioma == "es" else "INGLES"
        print(f"=== {nombre} ===")
        print(f"  canciones               {datos['canciones']}")
        print(f"  palabras distintas      {total}")
        print(f"  palabra exacta          {exactas / max(1, total) * 100:5.1f} %  "
              f"({exactas}/{total})")
        print(f"  ... solo las que el humano PARTIO   "
              f"{multi_exactas / max(1, multi_total) * 100:5.1f} %  ({multi_exactas}/{multi_total})")
        print(f"  fronteras: acierto      {acertadas / max(1, humanas) * 100:5.1f} % "
              f"de las {humanas} que puso el humano")
        print(f"  fronteras: precision    {acertadas / max(1, mias) * 100:5.1f} % "
              f"de las {mias} que puse yo")
        if fallos:
            print(f"  fallos de ejemplo (palabra | humano | mio):")
            for palabra, humano, mio in fallos:
                print(f"      {palabra[:22]:22} {humano[:26]:26} {mio[:26]}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
