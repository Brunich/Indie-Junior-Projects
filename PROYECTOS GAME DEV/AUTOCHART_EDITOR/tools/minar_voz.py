"""Mide la VOZ escrita a mano que hay en la biblioteca.

Es el `minar` de la letra: lee todas las canciones que traen `PART VOCALS` en
`notes.mid` o eventos `lyric` en `notes.chart`, y guarda las convenciones
medidas en `datos/perfil_voz.json`. Ese fichero es el criterio del generador de
karaoke, igual que `perfil_corpus.json` lo es del generador de notas.

    python tools/minar_voz.py
    python tools/minar_voz.py --biblioteca "<Songs>" --salida datos/perfil_voz.json

No escribe nada dentro de la biblioteca.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from autochart import voz  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
SALIDA = RAIZ / "datos" / "perfil_voz.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mide la voz humana de la biblioteca")
    parser.add_argument("--biblioteca", default=str(BIBLIOTECA))
    parser.add_argument("--salida", default=str(SALIDA))
    parser.add_argument("--detalle", action="store_true", help="Lista cancion por cancion")
    args = parser.parse_args(argv)

    biblioteca = Path(args.biblioteca)
    if not biblioteca.is_dir():
        print(f"[X] No existe la biblioteca: {biblioteca}")
        return 2

    print(f"[*] Buscando voz escrita a mano en: {biblioteca}")
    empezado = time.time()

    def progreso(cuenta: int, est) -> None:
        if args.detalle:
            print(f"    {cuenta:3d}  {est.silabas:5d} silabas  {est.frases:4d} frases  "
                  f"{est.fuente:5s}  {est.cancion[:46]}")
        elif cuenta % 10 == 0:
            print(f"    {cuenta} canciones con voz...")

    estadisticas = voz.escanear_biblioteca(biblioteca, al_progresar=progreso)
    perfil = voz.agregar(estadisticas)
    destino = voz.guardar_perfil(perfil, args.salida)
    tardado = time.time() - empezado

    print(f"\n[OK] {perfil['canciones_con_voz']} canciones con voz, "
          f"{perfil['silabas_totales']} silabas, en {tardado:.1f} s")
    print(f"     perfil -> {destino}\n")

    def fila(titulo: str, clave: str, unidad: str = "") -> None:
        datos = perfil[clave]
        print(f"     {titulo:26} p5 {datos['p5']:>7}  p50 {datos['p50']:>7}  "
              f"p95 {datos['p95']:>7} {unidad}")

    fila("silabas por frase", "silabas_por_frase")
    fila("segundos por frase", "segundos_por_frase", "s")
    fila("hueco entre frases", "hueco_entre_frases", "s")
    fila("la linea aparece antes", "aviso_de_frase", "s")
    fila("duracion de silaba", "duracion_silaba", "s")
    fila("silabas por segundo", "silabas_por_segundo")
    fila("palabras por frase", "palabras_por_frase")
    fila("caracteres por frase", "caracteres_por_frase")
    fila("notas sin silaba escrita", "ratio_sin_texto")
    fila("silabas que enlazan", "ratio_enlaza")
    fila("silabas de deslizado", "ratio_desliza")
    fila("silabas habladas", "ratio_hablada")
    fila("frases con overdrive", "ratio_overdrive")
    fila("altura mas grave", "pitch_min", "MIDI")
    fila("altura mas aguda", "pitch_max", "MIDI")

    print("\n     rejilla en la que caen las silabas (1 = negra, 4 = semicorchea):")
    for division, parte in list(perfil["rejilla"].items())[:8]:
        etiqueta = "fuera de rejilla" if division == "0" else f"1/{division} de negra"
        print(f"       {etiqueta:20} {parte * 100:5.1f} %")

    print("\n     saltos de altura entre silabas seguidas:")
    for salto, parte in list(perfil["saltos_semitono"].items())[:9]:
        print(f"       {salto:>4} semitonos  {parte * 100:5.1f} %")

    print("\n     por origen:")
    for origen, datos in perfil["por_origen"].items():
        print(f"       {origen[:38]:38} {datos['canciones']:3d} canciones  "
              f"silabas/frase p50 {datos['silabas_por_frase']['p50']:>5}  "
              f"sil/s p50 {datos['silabas_por_segundo']['p50']:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
