"""El `ring` del audio, puesto a prueba contra lo que el humano SI sostuvo.

El ring es la senal que deberia decidir los sostenidos: cuanto sigue sonando la
cuerda despues del ataque. La medida vieja (`ring_times`, la energia de TODA la
mezcla) no media nada -- medida el 23-08-2026 en Pride & Joy daba p50 5.99 s con
tope de 6.00, o sea la mitad de los ataques clavados en el techo -- porque en una
pista donde se toca sin parar esa energia no baja nunca.

Esta herramienta contesta dos preguntas, y la segunda es la que manda:

1. La forma de la medida: percentiles y cuantos ataques mueren en el tope. Una
   medida cuyo p50 es su propio techo no esta midiendo.
2. **Si SEPARA.** Se cogen las notas que el charter humano escribio sostenidas
   (`chartio.SOSTENIDO_MIN_TIEMPOS`, el mismo umbral que usa el corpus) y las
   que pico, se
   emparejan con el ataque mas cercano, y se pregunta: al coger una de cada
   clase al azar, cuantas veces la sostenida tiene mas ring? Eso es el AUC.
   0.50 es no separar nada -- da igual el ring, es una moneda -- y 1.00 seria
   separarlas perfectamente.

    python tools/mide_el_ring.py                  # Pride & Joy, la de referencia
    python tools/mide_el_ring.py "<carpeta>"
    python tools/mide_el_ring.py --humanos 12     # las 12 con guitarra aislada
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))

from autochart import audio, chartio, midiio  # noqa: E402
from sigue_la_melodia import _con_guitarra_aislada  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
PRIDE = (BIBLIOTECA / "03_Guitar Hero 3 Legends of Rock"
         / "Stevie Ray Vaughan (Steve Ouimette) - Pride & Joy")

# Lo que cuenta como sostenido lo dice `chartio`, no esta herramienta: la vara y
# el generador tienen que usar la MISMA regla o se mide otra cosa.
SOSTENIDO_MIN_TIEMPOS = chartio.SOSTENIDO_MIN_TIEMPOS
# Cuanto puede separar a una nota humana de su ataque para darlos por el mismo.
EMPAREJA_S = 0.06
# A partir de que hueco se considera que la nota "tiene sitio" para sostenerse.
# Medio segundo es holgado: a 120 BPM es una corchea larga.
HUECO_CON_SITIO_S = 0.5


def notas_humanas(carpeta: Path, dificultad: str = "Expert") -> list[tuple[float, float]]:
    """`(segundo, tiempos de sostenido)` por golpe, quedandose con el mas largo."""
    chart_path = carpeta / "notes.chart"
    if chart_path.is_file():
        chart = chartio.parse_chart(chart_path)
        track = chart.tracks.get(f"{dificultad}Single")
        if track:
            por_tick: dict[int, int] = {}
            for n in track.notes:
                if n.fret > chartio.FRET_ORANGE:
                    continue
                por_tick[n.tick] = max(por_tick.get(n.tick, 0), n.sustain)
            return [(chart.tick_to_seconds(t), s / chart.resolution)
                    for t, s in sorted(por_tick.items())]
    midi_path = carpeta / "notes.mid"
    if midi_path.is_file():
        midi = midiio.parse_midi(midi_path)
        por_tick = {}
        for n in midi.tracks.get(dificultad, []):
            por_tick[n.tick] = max(por_tick.get(n.tick, 0), n.sustain)
        return [(midi.tick_to_seconds(t), s / midi.resolution)
                for t, s in sorted(por_tick.items())]
    return []


def auc(sostenidas: np.ndarray, picadas: np.ndarray) -> float:
    """Mann-Whitney: al coger una de cada clase, cuantas veces gana la sostenida.

    Se calcula por rangos y no comparando todas las parejas, que con mil notas
    serian un millon. Los empates cuentan medio punto, que es lo que hace que
    una medida saturada (todo el mundo en el tope) de exactamente 0.50 y no un
    numero optimista.
    """
    if sostenidas.size == 0 or picadas.size == 0:
        return float("nan")
    todo = np.concatenate([sostenidas, picadas])
    orden = todo.argsort()
    rangos = np.empty(todo.size, dtype=float)
    rangos[orden] = np.arange(1, todo.size + 1, dtype=float)
    # Empates: todos comparten el rango medio del grupo.
    valores, inicio, cuenta = np.unique(todo, return_index=True, return_counts=True)
    for i, c in zip(inicio, cuenta):
        if c > 1:
            iguales = todo == todo[i]
            rangos[iguales] = rangos[iguales].mean()
    n1, n2 = sostenidas.size, picadas.size
    u = rangos[:n1].sum() - n1 * (n1 + 1) / 2.0
    return float(u / (n1 * n2))


def medir(carpeta: Path, nombre_audio: str = "guitar.ogg") -> dict | None:
    ruta = carpeta / nombre_audio
    if not ruta.is_file():
        ruta = audio.pick_audio(carpeta)
        if ruta is None:
            return None
    analisis = audio.analyse(str(ruta))
    rings = np.array([o.ring for o in analisis.onsets], dtype=float)
    tonos = np.array([o.tono_firme for o in analisis.onsets], dtype=float)
    tiempos = np.array([o.time for o in analisis.onsets], dtype=float)
    if rings.size == 0:
        return None
    # Las senales candidatas se miden TODAS en la misma pasada y con el mismo
    # emparejamiento. Comparar AUCs de dos corridas distintas no vale: el
    # desfase de autoria se busca cancion a cancion y mueve que notas entran.
    senales = {
        "ring": rings,
        "tono": tonos,
        # El minimo es "y las dos cosas": la cuerda sigue sonando Y el contorno
        # sigue diciendo esa nota. Es la combinacion mas exigente y la que
        # deberia separar si cada una aporta algo que la otra no ve.
        "ambas": np.minimum(rings, tonos),
    }

    fila = {
        "cancion": carpeta.name,
        "audio": ruta.name,
        "ataques": int(rings.size),
        "p25": round(float(np.percentile(rings, 25)), 2),
        "p50": round(float(np.percentile(rings, 50)), 2),
        "p75": round(float(np.percentile(rings, 75)), 2),
        "en_el_tope": round(float((rings >= audio.RING_MAX_S - 0.01).mean()), 4),
    }

    humanas = notas_humanas(carpeta)
    if humanas:
        # El humano y el audio no comparten reloj: los charts venidos de MIDI
        # llevan desfase de autoria (+65/+70 ms medidos). Se busca el que mas
        # notas empareja antes de decidir cual es cual.
        h_tiempos = np.array([t for t, _ in humanas], dtype=float)
        h_sostenes = np.array([s for _, s in humanas], dtype=float)
        mejor, mejor_cuenta = 0.0, -1
        for desfase in np.arange(-0.15, 0.151, 0.005):
            idx = np.searchsorted(tiempos, h_tiempos + desfase)
            idx = np.clip(idx, 1, tiempos.size - 1)
            cerca = np.minimum(np.abs(tiempos[idx] - (h_tiempos + desfase)),
                               np.abs(tiempos[idx - 1] - (h_tiempos + desfase)))
            cuenta = int((cerca <= EMPAREJA_S).sum())
            if cuenta > mejor_cuenta:
                mejor, mejor_cuenta = float(desfase), cuenta
        objetivo = h_tiempos + mejor
        idx = np.clip(np.searchsorted(tiempos, objetivo), 1, tiempos.size - 1)
        izq = np.abs(tiempos[idx - 1] - objetivo)
        der = np.abs(tiempos[idx] - objetivo)
        elegido = np.where(izq <= der, idx - 1, idx)
        distancia = np.minimum(izq, der)
        vale = distancia <= EMPAREJA_S
        es_sostenida = h_sostenes >= SOSTENIDO_MIN_TIEMPOS
        # La REFERENCIA, y no es una senal del audio: el hueco hasta la nota
        # siguiente del propio humano. Sirve para saber si la pregunta "que
        # nota se sostiene" se contesta oyendo o se contesta mirando el sitio
        # que hay. El generador no tiene las notas del humano, pero si tiene
        # sus propios huecos, que son casi los mismos donde acierta.
        huecos_h = np.diff(np.append(h_tiempos, h_tiempos[-1] + 2.0))
        idx_sost = elegido[vale & es_sostenida]
        idx_pica = elegido[vale & ~es_sostenida]
        fila["auc_hueco"] = round(auc(huecos_h[vale & es_sostenida],
                                      huecos_h[vale & ~es_sostenida]), 3)
        r_sost, r_pica = rings[idx_sost], rings[idx_pica]
        fila["auc_por_senal"] = {
            nombre: round(auc(valores[idx_sost], valores[idx_pica]), 3)
            for nombre, valores in senales.items()
        }
        fila["auc_por_senal"]["hueco"] = fila["auc_hueco"]

        # OJO, y es la trampa de esta medida: un sostenido OCUPA el hueco. No se
        # puede escribir una nota de 1.2 tiempos donde la siguiente entra a 0.1
        # s, asi que el hueco no "predice" el sostenido, lo PERMITE. Para saber
        # si ademas lo decide, se repite la pregunta solo entre las notas que
        # tienen sitio de sobra: ahi las dos clases existen y la respuesta ya no
        # es mecanica.
        con_sitio = huecos_h >= HUECO_CON_SITIO_S
        sost_sitio = vale & es_sostenida & con_sitio
        pica_sitio = vale & ~es_sostenida & con_sitio
        if sost_sitio.sum() >= 5 and pica_sitio.sum() >= 5:
            fila["con_sitio"] = [int(sost_sitio.sum()), int(pica_sitio.sum())]
            fila["auc_con_sitio"] = {
                nombre: round(auc(valores[elegido[sost_sitio]],
                                  valores[elegido[pica_sitio]]), 3)
                for nombre, valores in senales.items()
            }
            fila["auc_con_sitio"]["hueco"] = round(
                auc(huecos_h[sost_sitio], huecos_h[pica_sitio]), 3)
        fila.update({
            "desfase_ms": int(round(mejor * 1000)),
            "notas_humanas": len(humanas),
            "emparejadas": int(vale.sum()),
            "sostenidas": int(r_sost.size),
            "picadas": int(r_pica.size),
            "ring_sostenidas": round(float(np.median(r_sost)), 2) if r_sost.size else None,
            "ring_picadas": round(float(np.median(r_pica)), 2) if r_pica.size else None,
            "auc": round(auc(r_sost, r_pica), 3),
            "sostenidos_humano": round(float(es_sostenida.mean()), 4),
        })
    return fila


def imprimir(fila: dict) -> None:
    print("\n[*] {}   ({}, {} ataques)".format(
        fila["cancion"][:60], fila["audio"], fila["ataques"]))
    print("    ring   p25 {:.2f}  p50 {:.2f}  p75 {:.2f}   en el tope de {:.1f} s: {:.1f} %".format(
        fila["p25"], fila["p50"], fila["p75"], audio.RING_MAX_S, 100 * fila["en_el_tope"]))
    if "auc" in fila:
        print("    humano {} notas, {} sostenidas / {} picadas  (desfase {:+d} ms)".format(
            fila["notas_humanas"], fila["sostenidas"], fila["picadas"], fila["desfase_ms"]))
        print("    ring mediano   sostenidas {}   picadas {}".format(
            fila["ring_sostenidas"], fila["ring_picadas"]))
        print("    SEPARA?  AUC {:.3f}   (0.50 = una moneda)".format(fila["auc"]))
    if fila.get("auc_por_senal"):
        print("    por senal:  " + "   ".join(
            "{} {:.3f}".format(nombre, valor)
            for nombre, valor in fila["auc_por_senal"].items()))
    if fila.get("auc_con_sitio"):
        print("    con sitio ({} sost / {} pic):  ".format(*fila["con_sitio"]) + "   ".join(
            "{} {:.3f}".format(nombre, valor)
            for nombre, valor in fila["auc_con_sitio"].items()))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("carpeta", nargs="?", default=None)
    p.add_argument("--humanos", type=int, default=0,
                   help="mide N canciones con guitarra aislada, una por pack")
    p.add_argument("--audio", default="guitar.ogg")
    args = p.parse_args(argv)

    if args.humanos:
        carpetas = _con_guitarra_aislada(BIBLIOTECA, args.humanos)
    elif args.carpeta:
        carpetas = [Path(args.carpeta)]
    else:
        carpetas = [PRIDE]

    filas = []
    for carpeta in carpetas:
        fila = medir(carpeta, args.audio)
        if fila is None:
            print("[!] sin audio: " + carpeta.name)
            continue
        filas.append(fila)
        imprimir(fila)

    con_auc = [f for f in filas if f.get("auc") == f.get("auc") and "auc" in f]
    if len(con_auc) > 1:
        aucs = np.array([f["auc"] for f in con_auc], dtype=float)
        topes = np.array([f["en_el_tope"] for f in con_auc], dtype=float)
        print("\n=== {} canciones ===".format(len(con_auc)))
        print("AUC mediano {:.3f}   (min {:.3f}  max {:.3f})".format(
            float(np.median(aucs)), float(aucs.min()), float(aucs.max())))
        print("ataques en el tope, mediano {:.1f} %".format(100 * float(np.median(topes))))
        print("canciones que separan (AUC >= 0.70): {} de {}".format(
            int((aucs >= 0.70).sum()), len(con_auc)))
        nombres = list((con_auc[0].get("auc_por_senal") or {}).keys())
        if nombres:
            print()
            print("{:8s} {:>9s} {:>9s} {:>9s} {:>9s}".format(
                "senal", "mediano", "minimo", "maximo", "separan"))
            for nombre in nombres:
                v = np.array([f["auc_por_senal"][nombre] for f in con_auc
                              if nombre in (f.get("auc_por_senal") or {})], dtype=float)
                v = v[v == v]
                if not v.size:
                    continue
                print("{:8s} {:9.3f} {:9.3f} {:9.3f} {:6d}/{:d}".format(
                    nombre, float(np.median(v)), float(v.min()), float(v.max()),
                    int((v >= 0.70).sum()), v.size))
        con_sitio = [f for f in con_auc if f.get("auc_con_sitio")]
        if con_sitio:
            print()
            print("--- solo entre notas CON SITIO (hueco >= {:.1f} s), {} canciones ---"
                  .format(HUECO_CON_SITIO_S, len(con_sitio)))
            for nombre in list(con_sitio[0]["auc_con_sitio"].keys()):
                v = np.array([f["auc_con_sitio"][nombre] for f in con_sitio
                              if nombre in f["auc_con_sitio"]], dtype=float)
                v = v[v == v]
                if not v.size:
                    continue
                print("{:8s} {:9.3f} {:9.3f} {:9.3f} {:6d}/{:d}".format(
                    nombre, float(np.median(v)), float(v.min()), float(v.max()),
                    int((v >= 0.70).sum()), v.size))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
