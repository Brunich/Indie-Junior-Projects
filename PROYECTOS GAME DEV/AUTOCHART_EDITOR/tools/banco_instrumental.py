"""Mide QUE rasgo separa una cancion instrumental de una cantada.

No elige el umbral a ojo: coge dos grupos con etiqueta segura, mide los cinco
rasgos en los dos, y dice cual separa y por donde cortar.

  CANTADAS      canciones con letra escrita a mano en su chart (hay 184).
  INSTRUMENTALES lista corta y a mano, de temas que se sabe que no se cantan.

Se descarto `diff_vocals = -1` de `song.ini` como etiqueta: 135 canciones lo
llevan y entre ellas estan *Iron Man* y *Cowboys from Hell*. Significa "sin
pista de voz charteada", no "sin voz".

    python tools/banco_instrumental.py
    python tools/banco_instrumental.py --cantadas 30
"""

from __future__ import annotations

import argparse
import statistics as est
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from autochart import instrumental, voz  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
AUDIO = (".ogg", ".mp3", ".opus", ".wav", ".flac")

# Temas sin voz, comprobados de oido uno por uno. Se busca por subcadena.
INSTRUMENTALES = (
    "buckethead - jordan",
    "buckethead - the left panel",
    "buckethead - soothsayer",
    "rush (wavegroup) - yyz",
    "an endless sporadic - impulse",
    "eric johnson - cliffs of dover",
    "van halen - eruption",
    "halo theme mjolnir",
    "raul di blasio - corazon de nino",
)

RASGOS = ("banda_voz", "planitud", "modulacion", "contraste", "centro")


def mezcla_de(carpeta: Path) -> Path | None:
    """El audio con TODO dentro. Nunca un stem: comparar mezcla contra stem
    de guitarra mediria la separacion de pistas, no la presencia de voz."""
    for nombre in ("song", "mix"):
        for extension in AUDIO:
            if (carpeta / f"{nombre}{extension}").is_file():
                return carpeta / f"{nombre}{extension}"
    sueltos = [f for f in carpeta.iterdir() if f.suffix.lower() in AUDIO]
    return max(sueltos, key=lambda f: f.stat().st_size) if sueltos else None


def separacion(a: list[float], b: list[float]) -> float:
    """Cuanto separa un rasgo a los dos grupos (d de Cohen, en valor absoluto)."""
    if len(a) < 2 or len(b) < 2:
        return 0.0
    va, vb = est.pstdev(a), est.pstdev(b)
    comun = ((va ** 2 + vb ** 2) / 2) ** 0.5
    return abs(est.mean(a) - est.mean(b)) / comun if comun > 1e-9 else 0.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Que rasgo distingue instrumental de cantada")
    parser.add_argument("--biblioteca", default=str(BIBLIOTECA))
    parser.add_argument("--cantadas", type=int, default=24)
    args = parser.parse_args(argv)

    raiz = Path(args.biblioteca)
    carpetas = sorted({p.parent for patron in ("**/notes.chart", "**/notes.mid")
                       for p in raiz.glob(patron)})

    sin_voz: list[Path] = []
    con_voz: list[Path] = []
    for carpeta in carpetas:
        bajo = carpeta.name.lower()
        if any(clave in bajo for clave in INSTRUMENTALES):
            sin_voz.append(carpeta)
            continue
        try:
            pista = voz.leer_voz(carpeta)
        except Exception:
            pista = None
        if pista is not None and len(pista.silabas) >= 60:
            con_voz.append(carpeta)

    # una de cada N, para no coger 24 seguidas del mismo pack ni del mismo charter
    paso = max(1, len(con_voz) // args.cantadas)
    con_voz = con_voz[::paso][:args.cantadas]

    print(f"[*] {len(sin_voz)} instrumentales y {len(con_voz)} cantadas\n")
    medidas: dict[str, list[instrumental.RasgosVoz]] = {"inst": [], "cant": []}
    for etiqueta, grupo in (("inst", sin_voz), ("cant", con_voz)):
        for carpeta in grupo:
            audio = mezcla_de(carpeta)
            if audio is None:
                print(f"  [--] {carpeta.name[:46]:46} sin audio")
                continue
            medida = instrumental.rasgos(audio)
            if medida is None:
                print(f"  [X] {carpeta.name[:46]:46} no se pudo leer")
                continue
            medidas[etiqueta].append(medida)
            if etiqueta == "inst":
                print(f"  [inst] {carpeta.name[:44]:44} "
                      + "  ".join(f"{r[:4]} {getattr(medida, r):6.3f}" for r in RASGOS))

    print(f"\n{'rasgo':12} {'INSTRUMENTAL':>22} {'CANTADA':>22} {'separacion':>11}  corte")
    print("-" * 82)
    mejor = None
    for rasgo in RASGOS:
        a = [getattr(m, rasgo) for m in medidas["inst"] if getattr(m, rasgo)]
        b = [getattr(m, rasgo) for m in medidas["cant"] if getattr(m, rasgo)]
        if len(a) < 2 or len(b) < 2:
            print(f"{rasgo:12} {'sin datos':>22}")
            continue
        d = separacion(a, b)
        corte = (est.mean(a) + est.mean(b)) / 2
        print(f"{rasgo:12} {est.mean(a):8.3f} +-{est.pstdev(a):6.3f}   "
              f"{est.mean(b):8.3f} +-{est.pstdev(b):6.3f}   {d:9.2f}   {corte:.3f}")
        if mejor is None or d > mejor[1]:
            mejor = (rasgo, d, corte, est.mean(a) < est.mean(b))

    if mejor:
        rasgo, d, corte, menor_es_inst = mejor
        print(f"\n[OK] El que mas separa es **{rasgo}** (d de Cohen {d:.2f}).")
        print(f"     Instrumental si {rasgo} {'<' if menor_es_inst else '>'} {corte:.3f}")
        aciertos = sum(1 for m in medidas["inst"]
                       if (getattr(m, rasgo) < corte) == menor_es_inst)
        fallos = sum(1 for m in medidas["cant"]
                     if (getattr(m, rasgo) < corte) == menor_es_inst)
        print(f"     Con ese corte: {aciertos}/{len(medidas['inst'])} instrumentales bien, "
              f"{fallos}/{len(medidas['cant'])} cantadas mal etiquetadas")
        if d < 1.0:
            print(f"     [!] d < 1.0: NO separa lo bastante. No lo uses para decidir solo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
