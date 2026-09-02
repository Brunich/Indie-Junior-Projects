"""Mide el chart GENERADO con la misma vara que el humano.

Es la fase P2 de `docs/PLAN_PATRONES.md`. El atlas ya dice como es un chart
humano por dentro; de los nuestros no sabiamos ninguna de esas cifras. Sin esta
tabla no se sabe en que nos separamos, y sin saberlo no se puede arreglar nada.

    python tools/comparar_atlas.py                       # todo lo que hay en salida/
    python tools/comparar_atlas.py "salida/<carpeta>"    # una sola
    python tools/comparar_atlas.py "salida/<gen>" "<carpeta humana>"

**Usa `atlas.medir_pista` TAL CUAL para los dos lados.** Si la medida del
generado no fuera exactamente la misma funcion que la del humano, la tabla no
compararia nada -- es la trampa que ya costo la cifra falsa de HOPO.

No escribe en la biblioteca. Solo lee.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from autochart import atlas  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"

# Las medidas que deciden si "se siente escrito", con el percentil humano global
# sacado de datos/atlas_patrones.json para poder situar cada numero.
MEDIDAS = (
    ("nps", "notas por segundo", 2),
    ("acordes", "acordes", 2),
    ("sostenidos", "sostenidos", 2),
    ("repeticion", "repite traste", 2),
    ("ligadas", "ligadas", 2),
    ("sincopa", "a contratiempo", 2),
    ("cobertura", "DENTRO DE UN GESTO", 2),
    ("contraste", "CONTRASTE pico/valle", 1),
)


def _clave(nombre: str) -> str:
    """Nombre de carpeta -> algo comparable: sin tildes, sin puntuacion, sin (AutoChart)."""
    limpio = re.sub(r"\(autochart\)", "", nombre, flags=re.I)
    limpio = unicodedata.normalize("NFD", limpio)
    limpio = "".join(c for c in limpio if unicodedata.category(c) != "Mn")
    limpio = re.sub(r"[^a-z0-9]+", "", limpio.lower())
    return limpio


def buscar_humano(generado: Path, biblioteca: Path) -> Path | None:
    """Encuentra la carpeta humana de la misma cancion, si sigue en la biblioteca."""
    objetivo = _clave(generado.name)
    if not objetivo:
        return None
    mejor = None
    for carpeta in {p.parent for patron in ("**/notes.chart", "**/notes.mid")
                    for p in biblioteca.glob(patron)}:
        clave = _clave(carpeta.name)
        if clave == objetivo:
            return carpeta
        # el charter a veces cambia la puntuacion o corta el titulo
        if len(clave) > 12 and (clave in objetivo or objetivo in clave):
            if mejor is None or len(clave) > len(_clave(mejor.name)):
                mejor = carpeta
    return mejor


def guitarra(carpeta: Path):
    """La pista de guitarra en Experto, que es la que se compara."""
    try:
        pistas = atlas.analizar_carpeta(carpeta, dificultades=("Expert",))
    except Exception as error:
        print(f"     [X] no se pudo leer {carpeta.name}: {error}")
        return None
    for pista in pistas:
        if pista.instrumento == "guitarra" and pista.notas >= 32:
            return pista
    return None


def _forma(a: list[float], b: list[float]) -> float | None:
    """Correlacion entre dos curvas de densidad: si suben y bajan a la vez.

    Es distinto del contraste. El contraste dice CUANTO sube y baja; esto dice
    si sube DONDE sube el humano. Un chart puede tener el contraste clavado y
    ponerlo todo en el sitio equivocado.
    """
    if len(a) != len(b) or len(a) < 4:
        return None
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) ** 0.5
    vb = sum((x - mb) ** 2 for x in b) ** 0.5
    if va < 1e-9 or vb < 1e-9:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (va * vb)


def _percentil_de(valor: float, percentiles: dict) -> str:
    """Donde cae este numero dentro de la distribucion humana."""
    escala = [("p5", 5), ("p25", 25), ("p50", 50), ("p75", 75), ("p95", 95)]
    if valor < percentiles["p5"]:
        return "<p5 !"
    for (clave, _), (siguiente, _) in zip(escala, escala[1:]):
        if valor < percentiles[siguiente]:
            return f"{clave}-{siguiente}"
    return ">p95 !"


def comparar(generado: Path, humano: Path, referencia: dict | None) -> dict | None:
    a = guitarra(generado)
    b = guitarra(humano)
    if a is None or b is None:
        print(f"  [X] {generado.name}: falta la pista de guitarra en "
              f"{'el generado' if a is None else 'el humano'}")
        return None

    print(f"\n=== {generado.name} ===")
    print(f"    humano: {humano.name}  ({b.fuente}, charter {b.charter or '?'}, "
          f"{b.genero or '?'})")
    global_ = (referencia or {}).get("global", {})
    print(f"    {'':22} {'generado':>10} {'humano':>10} {'dif':>9}   {'donde cae':>10}")
    for clave, etiqueta, decimales in MEDIDAS:
        va, vb = getattr(a, clave), getattr(b, clave)
        marca = _percentil_de(va, global_[clave]) if clave in global_ else ""
        diferencia = va - vb
        print(f"    {etiqueta:22} {va:>10.{decimales}f} {vb:>10.{decimales}f} "
              f"{diferencia:>+9.{decimales}f}   {marca:>10}")

    forma = _forma(a.curva, b.curva)
    if forma is not None:
        juicio = ("los picos caen donde los del humano" if forma > 0.5 else
                  "la forma no se parece" if forma < 0.2 else "se parece a medias")
        print(f"    {'FORMA de la cancion':22} {forma:>10.2f} {'':>10} {'':>9}   {juicio}")

    print(f"    --- gestos por cada 100 notas ---")
    print(f"    {'':22} {'generado':>10} {'humano':>10}")
    for tipo in atlas.TIPOS_LICK:
        ga = a.licks.get(tipo, 0) / max(1, a.notas) * 100
        gb = b.licks.get(tipo, 0) / max(1, b.notas) * 100
        if ga < 0.02 and gb < 0.02:
            continue
        aviso = ""
        if gb >= 0.3 and ga < gb * 0.4:
            aviso = "  <- nos falta"
        elif ga >= 0.3 and gb < ga * 0.4:
            aviso = "  <- nos sobra"
        print(f"    {tipo:22} {ga:>10.2f} {gb:>10.2f}{aviso}")
    return {"gen": a, "hum": b}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generado contra humano, con la misma vara")
    parser.add_argument("generado", nargs="?", default=None)
    parser.add_argument("humano", nargs="?", default=None)
    parser.add_argument("--salida", default="salida")
    parser.add_argument("--biblioteca", default=str(BIBLIOTECA))
    parser.add_argument("--atlas", default=str(RAIZ / "datos" / "atlas_patrones.json"))
    args = parser.parse_args(argv)

    referencia = None
    if Path(args.atlas).is_file():
        referencia = atlas.cargar(args.atlas)

    biblioteca = Path(args.biblioteca)
    parejas: list[tuple[Path, Path]] = []

    if args.generado and args.humano:
        parejas.append((Path(args.generado), Path(args.humano)))
    else:
        carpetas = ([Path(args.generado)] if args.generado
                    else sorted(p for p in Path(args.salida).iterdir() if p.is_dir()))
        for carpeta in carpetas:
            humano = buscar_humano(carpeta, biblioteca)
            if humano is None:
                print(f"  [--] {carpeta.name}: no queda chart humano en la biblioteca")
                continue
            parejas.append((carpeta, humano))

    if not parejas:
        print("[X] No hay ninguna pareja que comparar.")
        return 2

    resultados = [r for r in (comparar(g, h, referencia) for g, h in parejas) if r]
    if len(resultados) < 2:
        return 0

    print(f"\n\n=== RESUMEN sobre {len(resultados)} canciones ===")
    print(f"    {'':22} {'generado':>10} {'humano':>10} {'dif':>9}")
    for clave, etiqueta, decimales in MEDIDAS:
        ga = sum(getattr(r["gen"], clave) for r in resultados) / len(resultados)
        gb = sum(getattr(r["hum"], clave) for r in resultados) / len(resultados)
        print(f"    {etiqueta:22} {ga:>10.{decimales}f} {gb:>10.{decimales}f} "
              f"{ga - gb:>+9.{decimales}f}")

    formas = [f for f in (_forma(r["gen"].curva, r["hum"].curva) for r in resultados)
              if f is not None]
    if formas:
        print(f"    {'FORMA de la cancion':22} {sum(formas) / len(formas):>10.2f} "
              f"{'':>10} {'':>9}  (1 = los picos en el mismo sitio, 0 = sin relacion)")

    print(f"\n    --- gestos por cada 100 notas, media de las {len(resultados)} ---")
    filas = []
    for tipo in atlas.TIPOS_LICK:
        ga = sum(r["gen"].licks.get(tipo, 0) / max(1, r["gen"].notas) for r in resultados) / len(resultados) * 100
        gb = sum(r["hum"].licks.get(tipo, 0) / max(1, r["hum"].notas) for r in resultados) / len(resultados) * 100
        if ga < 0.02 and gb < 0.02:
            continue
        filas.append((gb - ga, tipo, ga, gb))
    print(f"    {'':22} {'generado':>10} {'humano':>10} {'falta':>9}")
    for falta, tipo, ga, gb in sorted(filas, reverse=True):
        print(f"    {tipo:22} {ga:>10.2f} {gb:>10.2f} {falta:>+9.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
