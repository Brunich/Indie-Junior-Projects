"""Cuanto hay que pesar lo melodico al elegir que ataque se lleva la nota.

De donde sale la pregunta, medido y no supuesto:

- El generador escribia la bateria: el 58 % de las notas de DALI caian en un
  instante mas percusivo que armonico.
- Separar la cancion (S1) lo bajo al 47 %. Ayuda y no resuelve.
- Barriendo el desfase, el maximo de "percusivo" cae en 0-20 ms: la nota se pone
  ENCIMA del golpe, a proposito, no por un error de sincronia.
- Y el humano esta en 6-12 % (medido en cuatro charts de GH1 descontando su
  desfase de autoria): pone la nota DESPUES del golpe, no encima.

`separar.py` dejo escrito que "esto no se arregla subiendo LEAD_PRIORITY,
mientras la fuente sea la mezcla lo mas fuerte de cada ventana sigue siendo el
bombo". **Esa premisa ha caducado**: la fuente ya no es la mezcla, es `notas.ogg`
(other + vocals, sin bateria ni bajo). Con la fuente limpia, pesar lo melodico ya
no pelea contra el bombo -- y esto lo comprueba en vez de suponerlo.

Se generan las canciones de control con cada valor y se mide cada chart. El
valor se elige con la tabla, no con lo que parezca razonable.

    python tools/barrido_lead.py
    python tools/barrido_lead.py --valores 0.4,1.0,2.0
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
PRUEBAS = BIBLIOTECA / "17_Pruebas AutoChart"
VALORES = (0.40, 0.70, 1.00, 1.50)


def generar(carpeta: Path, destino: Path, lead: float) -> bool:
    """Genera parcheando LEAD_PRIORITY, reutilizando el CLI entero."""
    guion = (
        "import sys; sys.path.insert(0, r'{raiz}');"
        "import autochart.generate as g; g.LEAD_PRIORITY = {lead};"
        "from autochart.cli import main;"
        "sys.exit(main(['generar', r'{entrada}', '--salida', r'{salida}',"
        " '--dificultades', 'Expert']))"
    ).format(raiz=RAIZ, lead=lead, entrada=carpeta, salida=destino)
    hecho = subprocess.run([sys.executable, "-c", guion],
                           capture_output=True, text=True)
    if hecho.returncode != 0:
        print(f"    [X] {carpeta.name[:30]} con lead {lead}: "
              f"{(hecho.stderr or '').strip()[-200:]}")
    return hecho.returncode == 0


def medir(carpeta: Path, mezcla: Path) -> float | None:
    from tools.quien_toca import medir as medir_chart

    datos = medir_chart(carpeta, mezcla, "ExpertSingle", 0.0)
    if not datos:
        return None
    # `notas_percusivas` viene en fraccion (0-1): la fraccion de notas cuyo
    # ataque tiene mas energia percusiva que armonica en ese instante.
    return 100.0 * float(datos["notas_percusivas"])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--valores", default=",".join(str(v) for v in VALORES))
    parser.add_argument("--pruebas", default=str(PRUEBAS))
    parser.add_argument("--destino", default="salida/barrido_lead")
    args = parser.parse_args(argv)

    valores = [float(v) for v in args.valores.split(",")]
    canciones = sorted(p for p in Path(args.pruebas).iterdir() if p.is_dir())
    if not canciones:
        print(f"[X] No hay canciones en {args.pruebas}")
        return 2

    tabla: dict[float, dict[str, float | None]] = {}
    for lead in valores:
        tabla[lead] = {}
        print(f"[*] LEAD_PRIORITY = {lead}")
        for carpeta in canciones:
            destino = Path(args.destino) / f"lead_{lead}"
            mezcla = next((carpeta / f"song{e}" for e in (".mp3", ".ogg", ".opus")
                           if (carpeta / f"song{e}").is_file()), None)
            if mezcla is None or not generar(carpeta, destino, lead):
                tabla[lead][carpeta.name] = None
                continue
            tabla[lead][carpeta.name] = medir(destino / carpeta.name, mezcla)

    print()
    print("Notas cuyo ataque es MAS percusivo que armonico (menos es mejor).")
    print("Referencia: humano 6-12 %. Control antes de separar: DALI 58 %.")
    print()
    nombres = [c.name for c in canciones]
    print(f"{'lead':>6} " + " ".join(f"{n[:14]:>15}" for n in nombres) + f" {'media':>8}")
    for lead in valores:
        fila = [tabla[lead].get(n) for n in nombres]
        validos = [v for v in fila if v is not None]
        media = sum(validos) / len(validos) if validos else float("nan")
        celdas = " ".join(f"{'--':>15}" if v is None else f"{v:>14.0f}%" for v in fila)
        print(f"{lead:>6.2f} {celdas} {media:>7.1f}%")
    print()
    print("El valor se elige de esta tabla. Y hay que mirar el banco despues:")
    print("bajar percusivas no vale si se rompe la sincronia (f1 0.663).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
