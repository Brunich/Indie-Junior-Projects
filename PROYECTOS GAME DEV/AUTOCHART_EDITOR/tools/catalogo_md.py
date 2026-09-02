"""Escribe docs/CATALOGO_BIBLIOTECA.md: las 396 canciones repartidas por calidad.

Lee `datos/corpus_oro.json` (que a su vez sale de `atlas.escanear`) y reparte cada
pista de guitarra en un cajon segun cuantos de los cuatro filtros pasa. Sirve para
dos cosas distintas:

  - a Bruno, para saber que borrar y que no tocar;
  - al generador, para saber a que apuntar.

    python tools/elegir_oro.py      # primero, que produce el json
    python tools/catalogo_md.py     # despues, que produce el md
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "datos" / "corpus_oro.json"
SALIDA = RAIZ / "docs" / "CATALOGO_BIBLIOTECA.md"

# packs oficiales: si una cancion salio en un Guitar Hero o un Rock Band,
# es conocida por definicion y no se descarta por "no se conoce"
OFICIALES = ("01_", "02_", "03_", "04_", "05_", "06_", "07_", "08_", "09_", "15_")
MEMES = ("13_",)


def es_oficial(pack: str) -> bool:
    return pack.startswith(OFICIALES)


def es_meme(pack: str) -> bool:
    return pack.startswith(MEMES)


def cajon(f: dict) -> str:
    if f["oro"]:
        return "oro"
    fallos = set(f["descartada_por"])
    if "vacia" in fallos and len(fallos) >= 2:
        return "vacia"
    if "machacona" in fallos:
        if es_meme(f["pack"]):
            return "machacona_meme"
        return "machacona_gusta" if es_oficial(f["pack"]) else "machacona_fuera"
    if len(fallos) == 1:
        return "buena"
    if len(fallos) == 2:
        return "correcta"
    return "floja"


TITULOS = {
    "oro": ("Oro — la vara del generador",
            "Pasan los cinco filtros. Ni machaconas, ni vacias, con vocabulario por "
            "encima de la mediana, sin agujeros y con dinamica de verdad. Son estas "
            "las que el generador tiene que querer parecerse."),
    "buena": ("Buenas — fallan un solo filtro",
              "A un paso del oro. Utiles como referencia de segunda linea."),
    "correcta": ("Correctas — cumplen, sin mas",
                 "Ni molestan ni ensenan nada. Se quedan."),
    "machacona_gusta": ("Machaconas pero te gustan",
                        "Repiten traste por encima del p75, pero salieron en un Guitar "
                        "Hero o un Rock Band oficial. El punk y el pop machacan un "
                        "traste por diseno: eso no es un defecto del chart. **No las "
                        "borres.**"),
    "machacona_meme": ("Machaconas y memes",
                       "Repetitivas, si. Pero son memes, y los memes se quedan."),
    "machacona_fuera": ("Machaconas y prescindibles",
                        "Repiten traste por encima del p75 **y** no salieron en ningun "
                        "juego oficial. Estas son las candidatas reales a borrar."),
    "vacia": ("Vacias — casi no tocas",
              "Por debajo del p25 de notas por segundo y fallando algo mas. Si la "
              "cancion te gusta, busca otro chart en Chorus en vez de borrarla."),
    "floja": ("Flojas — fallan tres o cuatro filtros",
              "Poco vocabulario, poca dinamica. Revisables."),
}

ORDEN = ["oro", "buena", "machacona_gusta", "machacona_meme", "correcta",
         "floja", "machacona_fuera", "vacia"]


def fila(f: dict) -> str:
    motivos = ", ".join(f["descartada_por"]) or "—"
    return (f"| {f['cancion']} | {f['artista']} | {f['notas']} | {f['nps']:.2f} | "
            f"{f['repeticion']:.0%} | {f['cobertura']:.2f} | {f['variacion']:.3f} | "
            f"{motivos} |")


def main() -> int:
    if not ENTRADA.exists():
        print(f"falta {ENTRADA}. Corre antes: python tools/elegir_oro.py", file=sys.stderr)
        return 1
    d = json.loads(ENTRADA.read_text(encoding="utf-8"))
    u = d["umbrales"]

    cajones: dict[str, list] = defaultdict(list)
    for f in d["canciones"]:
        cajones[cajon(f)].append(f)

    out = []
    w = out.append
    w("# Catalogo de la biblioteca — las 396 por calidad medida\n")
    w(f"Generado por `tools/catalogo_md.py` sobre `datos/corpus_oro.json`. "
      f"{d['pistas_guitarra_evaluadas']} pistas de guitarra en Experto con al menos "
      f"{u['min_notas']} notas, medidas con `atlas.escanear` — la misma funcion que "
      f"alimenta `atlas_patrones.json`.\n")

    w("## Los cuatro filtros\n")
    w("Los umbrales no son una opinion: salen de los percentiles de esta misma "
      "biblioteca.\n")
    w("| Filtro | Falla si | Umbral | Cuantas caen |")
    w("|---|---|---|---|")
    n_mach = sum(1 for f in d["canciones"] if "machacona" in f["descartada_por"])
    n_vac = sum(1 for f in d["canciones"] if "vacia" in f["descartada_por"])
    n_voc = sum(1 for f in d["canciones"] if "poco vocabulario" in f["descartada_por"])
    n_mue = sum(1 for f in d["canciones"] if "zonas muertas" in f["descartada_por"])
    n_pla = sum(1 for f in d["canciones"] if "plana" in f["descartada_por"])
    w(f"| **machacona** | repite traste demasiado | > p75 = {u['repeticion_p75']:.1%} | {n_mach} |")
    w(f"| **vacia** | casi no tocas | < p25 = {u['nps_p25']:.2f} notas/s | {n_vac} |")
    w(f"| **poco vocabulario** | usa pocos gestos distintos | < p50 = {u['cobertura_p50']:.2f} | {n_voc} |")
    w(f"| **zonas muertas** | tramos donde no se toca casi nada | > 1 tramo de 12 | {n_mue} |")
    w(f"| **plana** | la densidad no se mueve en toda la cancion | < p25 = {u['variacion_p25']:.3f} | {n_pla} |")
    w("")
    w(f"**Pasan los cinco: {d['oro']} de {d['pistas_guitarra_evaluadas']} "
      f"({100 * d['oro'] / d['pistas_guitarra_evaluadas']:.0f} %).**\n")
    w("Lo que mas se cae es *vocabulario* y *dinamica*, no la repeticion. Es decir: "
      "el chart medio de la biblioteca no es machacon, es **plano** — toca siempre "
      "lo mismo con la misma intensidad. Eso es exactamente lo que un generador "
      "tiende a producir solo, asi que es la trampa a vigilar.\n")

    w("## Indice\n")
    for k in ORDEN:
        if cajones[k]:
            w(f"- [{TITULOS[k][0]}](#{TITULOS[k][0].split(' — ')[0].lower().replace(' ', '-')}) "
              f"— {len(cajones[k])}")
    w("")

    for k in ORDEN:
        grupo = cajones[k]
        if not grupo:
            continue
        titulo, explica = TITULOS[k]
        w(f"## {titulo}\n")
        w(f"{explica}\n")
        w(f"**{len(grupo)} canciones.**\n")
        grupo.sort(key=lambda f: -f["expresividad"])
        w("| Cancion | Artista | Notas | n/s | Repite | Vocab. | Respira | Falla |")
        w("|---|---|---:|---:|---:|---:|---:|---|")
        for f in grupo:
            w(fila(f))
        w("")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(out), encoding="utf-8")
    print(f"escrito: {SALIDA}")
    for k in ORDEN:
        if cajones[k]:
            print(f"  {TITULOS[k][0].split(' — ')[0]:<34} {len(cajones[k]):>4}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
