"""Mide si alinear las silabas con el audio acierta mas que repartirlas a ojo.

El experimento es el mismo que destapo el problema: se cogen canciones con voz
escrita a mano -- que traen el tiempo REAL de cada silaba -- se tiran esos
tiempos dejando solo el principio y el final de cada linea, y se vuelven a
colocar. Lo que salga se compara con lo que puso la persona.

    python tools/banco_alineado.py            # 12 canciones
    python tools/banco_alineado.py --cuantas 30

Control a batir (medido el 22-08-2026 sobre 41 canciones, 14 650 silabas):

    reparto por peso de letras:  mediana 148 ms   p75 284 ms   p95 597 ms

Objetivo: **mediana < 60 ms**, que es la ventana con la que se decide si una
nota del chart coincide con una silaba. Por encima de eso, anclar las notas a la
letra propaga el error a las notas.
"""

from __future__ import annotations

import argparse
import statistics as st
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from autochart import alinear, letras, voz  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
RESPALDO = RAIZ / "salida" / "respaldo_letras"
AUDIO = (".ogg", ".mp3", ".opus", ".wav", ".flac")


def es_humana(carpeta: Path) -> bool:
    """La letra la escribio una persona, no AutoChart."""
    copia = RESPALDO / carpeta.name
    if not copia.is_dir():
        return True
    try:
        original = voz.leer_voz(copia)
    except Exception:
        return True
    return original is not None and len(original.silabas) >= 20


def mezcla_de(carpeta: Path) -> Path | None:
    """El audio donde buscar los arranques de canto.

    **El stem de voz manda sobre la mezcla, y no es un detalle.** Midiendo sobre
    `song.ogg` el detector encontraba 2664 arranques en Pull Me Under y 1411 en
    Carolina: eso no son silabas, es la bateria y la guitarra entrando en la
    banda de 200-4000 Hz. Con eso el alineado salia 177 ms contra los 151 ms del
    reparto a ojo -- peor que no hacer nada. Es la misma leccion que ya estaba
    escrita para el pulso (mezcla) y las notas (stem de guitarra), sin aplicar
    a la voz. De las 398 carpetas, 101 traen `vocals`.
    """
    for nombre in ("vocals", "song"):
        for extension in AUDIO:
            if (carpeta / f"{nombre}{extension}").is_file():
                return carpeta / f"{nombre}{extension}"
    sueltos = [f for f in carpeta.iterdir() if f.suffix.lower() in AUDIO]
    return max(sueltos, key=lambda f: f.stat().st_size) if sueltos else None


def percentiles(valores: list[float]) -> tuple[float, float, float]:
    orden = sorted(valores)
    return (st.median(orden),
            orden[int(len(orden) * 0.75)],
            orden[int(len(orden) * 0.95)])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Alinear silabas contra el reparto a ojo")
    parser.add_argument("--biblioteca", default=str(BIBLIOTECA))
    parser.add_argument("--cuantas", type=int, default=12)
    parser.add_argument("--detalle", action="store_true")
    args = parser.parse_args(argv)

    raiz = Path(args.biblioteca)
    carpetas = sorted({p.parent for patron in ("**/notes.mid", "**/notes.chart")
                       for p in raiz.glob(patron)})

    plano: list[float] = []
    alineado: list[float] = []
    # Los mismos errores, pero tras descontar el desfase de autoria de CADA
    # cancion. El proyecto ya tiene medido que un chart venido de `.mid` va
    # +65/+70 ms contra el audio: el charter cuadra a la rejilla, no a la onda.
    # Si eso pasa tambien con la voz, parte del error que me apunto no es mio.
    plano_corr: list[float] = []
    alineado_corr: list[float] = []
    desfases: list[tuple[str, float]] = []
    por_largo: dict[int, tuple[list[float], list[float]]] = {}
    hechas = 0
    empezado = time.time()

    for carpeta in carpetas:
        if hechas >= args.cuantas:
            break
        if not es_humana(carpeta):
            continue
        try:
            pista = voz.leer_voz(carpeta)
        except Exception:
            pista = None
        if pista is None or len(pista.silabas) < 80:
            continue
        audio = mezcla_de(carpeta)
        if audio is None:
            continue

        arranques = alinear.arranques_de_voz(audio)
        if arranques is None:
            continue
        hechas += 1

        errores_plano: list[float] = []
        errores_alineado: list[float] = []
        # con signo, para ver si la cancion entera va adelantada o atrasada
        signo_plano: list[float] = []
        signo_alineado: list[float] = []
        for frase in pista.frases:
            if len(frase.silabas) < 3:
                continue
            reales = [pista.tick_to_seconds(s.tick) for s in frase.silabas]
            inicio, fin = reales[0], reales[-1]
            if fin - inicio < 0.3:
                continue
            textos = [s.palabra or "la" for s in frase.silabas]
            pesos = letras._reparto(textos)

            a_ojo = alinear._reparto_plano(inicio, fin, len(reales), pesos)
            picos, fuerzas = arranques.entre(inicio - 0.25, fin + 0.25)
            medido = alinear.emparejar(inicio, fin, len(reales), picos, fuerzas, pesos)

            errores_plano += [abs(a - b) for a, b in zip(reales, a_ojo)]
            errores_alineado += [abs(a - b) for a, b in zip(reales, medido)]
            signo_plano += [a - b for a, b in zip(reales, a_ojo)]
            signo_alineado += [a - b for a, b in zip(reales, medido)]
            clave = min(len(reales) // 3 * 3, 15)
            hueco = por_largo.setdefault(clave, ([], []))
            hueco[0].extend(abs(a - b) for a, b in zip(reales, a_ojo))
            hueco[1].extend(abs(a - b) for a, b in zip(reales, medido))

        if errores_plano:
            plano += errores_plano
            alineado += errores_alineado
            desfase = st.median(signo_alineado)
            desfases.append((carpeta.name, desfase))
            plano_corr += [abs(v - st.median(signo_plano)) for v in signo_plano]
            alineado_corr += [abs(v - desfase) for v in signo_alineado]
            if args.detalle:
                print(f"  {carpeta.name[:44]:44} a ojo {st.median(errores_plano)*1000:5.0f} ms"
                      f"  ->  alineado {st.median(errores_alineado)*1000:5.0f} ms"
                      f"   ({len(arranques.tiempos)} arranques)")

    if not plano:
        print("[X] No se pudo medir ninguna cancion. Sin resultado.")
        return 2

    pm, p75, p95 = percentiles(plano)
    am, a75, a95 = percentiles(alineado)
    print(f"\n{hechas} canciones, {len(plano)} silabas, {time.time() - empezado:.0f} s\n")
    print(f"{'':22} {'mediana':>9} {'p75':>9} {'p95':>9}")
    print(f"{'reparto a ojo':22} {pm*1000:>8.0f}ms {p75*1000:>8.0f}ms {p95*1000:>8.0f}ms")
    print(f"{'ALINEADO con el audio':22} {am*1000:>8.0f}ms {a75*1000:>8.0f}ms {a95*1000:>8.0f}ms")
    mejora = (pm - am) / pm * 100 if pm else 0
    print(f"{'mejora':22} {mejora:>8.0f}%")

    # Lo mismo descontando el desfase propio de cada cancion.
    if alineado_corr:
        cm, c75, c95 = percentiles(alineado_corr)
        qm, _, _ = percentiles(plano_corr)
        print()
        print("sin el desfase de autoria de cada cancion:")
        print(f"{'   a ojo':22} {qm*1000:>8.0f}ms")
        print(f"{'   ALINEADO':22} {cm*1000:>8.0f}ms {c75*1000:>8.0f}ms {c95*1000:>8.0f}ms")
        print()
        print(f"{'desfase por cancion':38} {'ms':>7}")
        for nombre, valor in sorted(desfases, key=lambda x: -abs(x[1])):
            print(f"   {nombre[:35]:35} {valor*1000:>+7.0f}")

    print(f"\n{'silabas por linea':22} {'a ojo':>9} {'alineado':>10}")
    for clave in sorted(por_largo):
        a, b = por_largo[clave]
        if len(a) < 30:
            continue
        print(f"   {clave:2d}-{clave+2:2d}{'':14} {st.median(a)*1000:>8.0f}ms {st.median(b)*1000:>9.0f}ms")

    print()
    if am <= 0.060:
        print(f"[OK] {am*1000:.0f} ms de mediana: por debajo de los 60 ms que hacen falta.")
        return 0
    print(f"[!] {am*1000:.0f} ms de mediana. El objetivo son 60 ms y no se llega.")
    print("    Si no baja de ahi, anclar las notas a la letra propaga el error.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
