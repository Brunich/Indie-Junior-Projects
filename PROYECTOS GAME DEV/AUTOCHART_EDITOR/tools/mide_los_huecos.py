"""Los huecos que deja un chart, y si ahi cabe un sostenido largo.

Un `sostenido_largo` -- el gesto que mas nos falta, 12.4 % de los gestos humanos
contra 1.2 % de los nuestros -- son 2 tiempos o mas. Para escribir uno hace
falta que la nota siguiente no llegue antes, asi que antes de tocar el ring, el
perfil o el banco de motivos hay que saber si **el sitio existe**.

Medido el 24-08-2026 sobre el panel de 10 canciones, la respuesta fue que no:

    huecos de 2.22 tiempos o mas    humano 1.45 %   nosotros 0.18 %
    sostenidos de 2 tiempos o mas   humano 1.13 %   nosotros 0.17 %
    cuando el hueco existe, se usa  humano 77.8 %   nosotros 94.8 %
    hueco mediano                   humano 0.500t   nosotros 0.467t

O sea que la maquinaria de sostenidos no falla -- es mas ansiosa que el humano
-- y el hueco mediano es casi el mismo. Lo que falta es la COLA: el humano deja
agujeros de verdad y nosotros repartimos las notas parejo.

    python tools/mide_los_huecos.py salida/<lote_de_charts>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))

from autochart import chartio, midiio  # noqa: E402
from panel_generos import elegir  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
# Lo que hace falta para que quepa un sostenido de 2 tiempos: los 2 del gesto
# mas la cola que `generate.SUSTAIN_TAIL_BEATS` deja antes de la nota siguiente.
HUECO_LARGO = 2.22
SOSTENIDO_LARGO = 2.0


def huecos_y_sostenidos(carpeta: Path, dificultad: str = "Expert"):
    """`(hueco hasta la nota siguiente, sostenido escrito)` en tiempos."""
    ruta = carpeta / "notes.chart"
    por: dict[int, int] = {}
    if ruta.is_file():
        ch = chartio.parse_chart(ruta)
        pista = ch.tracks.get(f"{dificultad}Single")
        if not pista:
            return None, None
        for n in pista.notes:
            if n.fret <= chartio.FRET_ORANGE:
                por[n.tick] = max(por.get(n.tick, 0), n.sustain)
        resolucion = ch.resolution
    else:
        ruta = carpeta / "notes.mid"
        if not ruta.is_file():
            return None, None
        m = midiio.parse_midi(ruta)
        for n in m.tracks.get(dificultad, []):
            por[n.tick] = max(por.get(n.tick, 0), n.sustain)
        resolucion = m.resolution
    if len(por) < 50:
        return None, None
    ticks = np.array(sorted(por))
    sostenes = np.array([por[t] for t in ticks], dtype=float) / resolucion
    return np.diff(ticks) / resolucion, sostenes[:-1]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("charts", help="carpeta con los charts generados")
    p.add_argument("--biblioteca", default=str(BIBLIOTECA))
    args = p.parse_args(argv)

    generados = Path(args.charts)
    filas = []
    print("{:34s} {:>18s} {:>18s}".format("cancion", "hueco>=2.22t", "sost>=2t"))
    for humana in elegir(Path(args.biblioteca)):
        generada = generados / (humana.name + " (AutoChart)")
        if not generada.is_dir():
            continue
        hh, hs = huecos_y_sostenidos(humana)
        gh, gs = huecos_y_sostenidos(generada)
        if hh is None or gh is None:
            continue
        fila = (float((hh >= HUECO_LARGO).mean()), float((gh >= HUECO_LARGO).mean()),
                float((hs >= SOSTENIDO_LARGO).mean()), float((gs >= SOSTENIDO_LARGO).mean()),
                float(np.median(hh)), float(np.median(gh)))
        filas.append(fila)
        print("{:34s}  hum {:5.2f}% nos {:5.2f}%   hum {:5.2f}% nos {:5.2f}%".format(
            humana.name[:34], 100 * fila[0], 100 * fila[1],
            100 * fila[2], 100 * fila[3]))

    if not filas:
        print("[X] ni una pareja: mira que el lote sea del panel")
        return 2
    a = np.array(filas)
    print("\n{} canciones".format(len(filas)))
    print("huecos de {:.2f} tiempos o mas    humano {:5.2f} %   nosotros {:5.2f} %".format(
        HUECO_LARGO, 100 * a[:, 0].mean(), 100 * a[:, 1].mean()))
    print("sostenidos de {:.0f} tiempos o mas   humano {:5.2f} %   nosotros {:5.2f} %".format(
        SOSTENIDO_LARGO, 100 * a[:, 2].mean(), 100 * a[:, 3].mean()))
    print("cuando el hueco existe, se usa  humano {:5.1f} %   nosotros {:5.1f} %".format(
        100 * a[:, 2].mean() / max(a[:, 0].mean(), 1e-9),
        100 * a[:, 3].mean() / max(a[:, 1].mean(), 1e-9)))
    print("hueco mediano (tiempos)         humano {:5.3f}     nosotros {:5.3f}".format(
        a[:, 4].mean(), a[:, 5].mean()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
