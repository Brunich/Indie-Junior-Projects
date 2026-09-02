"""Poner cada silaba donde de verdad se canta, midiendolo en el audio.

**El problema que resuelve, medido.** Un `.lrc` trae una sola marca por linea.
Hasta ahora las silabas de dentro se repartian por peso de letras -- adivinando.
Contra 41 canciones con voz humana (14 650 silabas con su tiempo real al lado):

    error del reparto por peso:  mediana 148 ms   p75 284 ms   p95 597 ms
    linea de 3-5 silabas: 114 ms       linea de 15-17: 186 ms (p95 706 ms)

Las lineas cortas cuadran y las largas se van medio segundo, que es exactamente
lo que se nota jugando: "a veces va muy bien y a veces no".

**Como se arregla.** Cantar deja marcas en el audio: cada silaba abre con un
golpe de aire y eso sube la energia en la banda de la voz, incluso cuando la
nota anterior sigue sonando. Se detectan esos arranques y se emparejan con las
silabas **en orden**, resolviendo el emparejamiento entero de una vez en vez de
ir cogiendo el mas cercano -- que es lo que se rompe cuando el cantante se come
una silaba o alarga una vocal.

Objetivo, y esta puesto antes de escribir el codigo: bajar de 148 ms a **menos
de 60 ms** de error mediano, que es la ventana con la que se mide si una nota
del chart coincide con una silaba. Si no baja de ahi, esto no sirve.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# La banda donde vive la voz cantada. Por debajo manda el bajo y el bombo; por
# encima, los platos.
BANDA_BAJA = 200.0
BANDA_ALTA = 4000.0
# Resolucion de la envolvente. 256 muestras a 22050 Hz son 11.6 ms por cuadro:
# hace falta esto para poder acertar por debajo de 60 ms.
SALTO = 256
MUESTREO = 22050

# Dos arranques mas juntos que esto son el mismo: nadie canta dos silabas en
# 80 ms. Sale del p5 de duracion de silaba humana medido (0.126 s), con margen.
ARRANQUES_MINIMO_S = 0.08

# Cuanto pesa la fuerza del arranque frente a lo lejos que este de donde se
# esperaba la silaba. Calibrado con el banco, no a ojo: ver tools/banco_alineado.py
PESO_FUERZA = 0.45


@dataclass
class Arranques:
    """Los arranques de canto de una cancion, ya medidos una sola vez."""

    tiempos: list[float]
    fuerzas: list[float]

    def entre(self, desde: float, hasta: float) -> tuple[list[float], list[float]]:
        import bisect

        i = bisect.bisect_left(self.tiempos, desde)
        j = bisect.bisect_right(self.tiempos, hasta)
        return self.tiempos[i:j], self.fuerzas[i:j]


def arranques_de_voz(ruta_audio: str | Path) -> Arranques | None:
    """Donde arranca cada silaba cantada, en toda la cancion.

    Se mide sobre la banda de la voz y con la envolvente de **subida**: lo que
    marca una silaba nueva no es que suene fuerte, es que sube de golpe.
    """
    import numpy as np
    import librosa

    try:
        y, sr = librosa.load(str(ruta_audio), sr=MUESTREO, mono=True)
    except Exception:
        return None
    if y.size == 0:
        return None

    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=SALTO))
    frecuencias = librosa.fft_frequencies(sr=sr, n_fft=1024)
    banda = (frecuencias >= BANDA_BAJA) & (frecuencias <= BANDA_ALTA)
    if not banda.any():
        return None

    # Flujo espectral solo en la banda de voz: la suma de lo que SUBE de un
    # cuadro al siguiente. Un sostenido no sube, asi que no marca silaba.
    trozo = S[banda]
    subida = np.diff(trozo, axis=1, prepend=trozo[:, :1]).clip(min=0).sum(axis=0)
    if subida.max() > 0:
        subida = subida / subida.max()

    distancia = max(1, int(ARRANQUES_MINIMO_S * sr / SALTO))
    picos = librosa.util.peak_pick(
        subida, pre_max=distancia, post_max=distancia,
        pre_avg=distancia * 3, post_avg=distancia * 3,
        delta=0.01, wait=distancia,
    )
    if len(picos) == 0:
        return None
    tiempos = librosa.frames_to_time(picos, sr=sr, hop_length=SALTO).tolist()
    return Arranques(tiempos=tiempos, fuerzas=[float(subida[i]) for i in picos])


def _reparto_plano(inicio: float, fin: float, cuantas: int,
                   pesos: list[float] | None = None) -> list[float]:
    """El reparto de siempre, que se usa como esperanza y como respaldo."""
    if cuantas <= 0:
        return []
    if cuantas == 1:
        return [inicio]
    if pesos and len(pesos) == cuantas:
        salida, acumulado = [], 0.0
        for peso in pesos:
            salida.append(inicio + acumulado * (fin - inicio))
            acumulado += peso
        return salida
    paso = (fin - inicio) / cuantas
    return [inicio + paso * i for i in range(cuantas)]


def emparejar(
    inicio: float,
    fin: float,
    cuantas: int,
    arranques: list[float],
    fuerzas: list[float],
    pesos: list[float] | None = None,
    escala: str = "ventana",
    peso_fuerza: float = PESO_FUERZA,
) -> list[float]:
    """Coloca `cuantas` silabas usando los arranques de canto que haya.

    Es un emparejamiento **en orden y de una vez**, no "coge el mas cercano".
    La diferencia importa: si el cantante se come una silaba o alarga una vocal,
    el vecino mas cercano encadena mal todas las siguientes, y una solucion
    global no.

    Coste de poner la silaba i en el arranque j:
        lo lejos que esta de donde se esperaba  -  lo fuerte que es el arranque

    Si no hay arranques suficientes, las que sobran se reparten entre los
    anclajes que si se encontraron: mejor un tramo estimado entre dos anclas
    buenas que toda la linea estimada.
    """
    if cuantas <= 0:
        return []
    esperado = _reparto_plano(inicio, fin, cuantas, pesos)
    if not arranques:
        return esperado

    n, m = cuantas, len(arranques)
    # La escala con la que se mide "esta lejos". Dividir por la frase entera
    # (lo que se hacia) hace que en una frase de 10 s un error de 300 ms cueste
    # 0.03 y la fuerza del pico decida sola: por eso las lineas largas salian a
    # 162 ms y las de 6-8 silabas a 55 ms. La escala buena es el hueco que se
    # espera ENTRE silabas, que es comparable en toda frase.
    # `escala` decide con que se compara "esta lejos", y esta MEDIDO cual gana:
    #   ventana (la frase entera)   117 ms   <- se queda esta
    #   espaciado (el hueco entre silabas)  143 ms
    # Es al reves de lo que parece: con la escala fina el coste de posicion
    # domina, el emparejador se pega a la expectativa y devuelve justo el
    # reparto a ojo del que se venia huyendo (151 ms). Se deja el parametro
    # para que el experimento se pueda repetir, no para tocarlo.
    if escala == "espaciado":
        ventana = max(1e-3, (fin - inicio) / max(1, n - 1))
    else:
        ventana = max(1e-3, fin - inicio)
    if m < n:
        # No hay para todas: se emparejan las que se pueda y se interpola.
        elegidos = _mejor_subconjunto(esperado, arranques, fuerzas, ventana)
        return _interpolar(esperado, elegidos, inicio, fin)

    # DP: silaba i -> arranque j, con j creciente.
    INF = float("inf")
    coste = [[INF] * (m + 1) for _ in range(n + 1)]
    de_donde = [[0] * (m + 1) for _ in range(n + 1)]
    coste[0][0] = 0.0
    for j in range(m + 1):
        coste[0][j] = 0.0
    for i in range(1, n + 1):
        for j in range(i, m + 1):
            local = (abs(arranques[j - 1] - esperado[i - 1]) / ventana
                     - peso_fuerza * fuerzas[j - 1])
            mejor, origen = INF, j - 1
            for k in range(i - 1, j):
                if coste[i - 1][k] + local < mejor:
                    mejor, origen = coste[i - 1][k] + local, k
            coste[i][j] = mejor
            de_donde[i][j] = origen

    final = min(range(n, m + 1), key=lambda j: coste[n][j])
    salida: list[float] = []
    j = final
    for i in range(n, 0, -1):
        salida.append(arranques[j - 1])
        j = de_donde[i][j]
    salida.reverse()
    return salida


def _mejor_subconjunto(esperado: list[float], arranques: list[float],
                       fuerzas: list[float], ventana: float) -> dict[int, float]:
    """Empareja los pocos arranques que hay con las silabas que mejor encajen."""
    usados: dict[int, float] = {}
    tomados: set[int] = set()
    orden = sorted(range(len(arranques)), key=lambda j: -fuerzas[j])
    for j in orden:
        mejor, indice = None, None
        for i, momento in enumerate(esperado):
            if i in tomados:
                continue
            # respetar el orden: no puede ir antes que una silaba ya colocada
            if any(k < i and usados[k] > arranques[j] for k in usados):
                continue
            if any(k > i and usados[k] < arranques[j] for k in usados):
                continue
            distancia = abs(arranques[j] - momento)
            if mejor is None or distancia < mejor:
                mejor, indice = distancia, i
        if indice is not None and mejor is not None and mejor <= ventana * 0.35:
            usados[indice] = arranques[j]
            tomados.add(indice)
    return usados


def _interpolar(esperado: list[float], anclas: dict[int, float],
                inicio: float, fin: float) -> list[float]:
    """Rellena las silabas sin ancla estirando entre las que si la tienen."""
    if not anclas:
        return esperado
    indices = sorted(anclas)
    salida = list(esperado)
    for i in indices:
        salida[i] = anclas[i]
    # antes de la primera ancla
    primera = indices[0]
    if primera > 0:
        paso = (anclas[primera] - inicio) / (primera + 1)
        for i in range(primera):
            salida[i] = inicio + paso * i
    # entre anclas
    for a, b in zip(indices, indices[1:]):
        if b - a <= 1:
            continue
        paso = (anclas[b] - anclas[a]) / (b - a)
        for i in range(a + 1, b):
            salida[i] = anclas[a] + paso * (i - a)
    # despues de la ultima
    ultima = indices[-1]
    if ultima < len(salida) - 1:
        resto = len(salida) - 1 - ultima
        paso = max(0.05, (fin - anclas[ultima]) / (resto + 1))
        for i in range(ultima + 1, len(salida)):
            salida[i] = anclas[ultima] + paso * (i - ultima)
    # y que quede creciente pase lo que pase
    for i in range(1, len(salida)):
        if salida[i] <= salida[i - 1]:
            salida[i] = salida[i - 1] + 0.02
    return salida
