"""Decidir si una cancion lleva voz o es puramente instrumental.

Para que sirve: cuando no se encuentra letra, no es lo mismo *"esta cancion no
tiene letra porque es instrumental"* que *"esta cancion se canta pero LRCLIB no
la tiene"*. La primera esta terminada; la segunda es trabajo pendiente. Sin
distinguirlas, las dos salen como un hueco y no se sabe cual perseguir.

**Lo que NO sirve como criterio**, y se comprobo antes de escribir esto:
`diff_vocals = -1` en `song.ini`. Hay 135 canciones asi en la biblioteca y entre
ellas estan *Iron Man*, *Cowboys from Hell* y *More Than A Feeling*. Ese campo
significa "no hay pista de voz charteada", no "no se canta".

Asi que se mide en el audio. Todos los rasgos salen de una lectura a 11 kHz de
un trozo del centro de la cancion: sobra para esto y es cuatro veces mas rapido
que cargarla entera.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Donde vive la voz cantada: los formantes que la hacen reconocible.
BANDA_BAJA = 300.0
BANDA_ALTA = 3400.0
# Ritmo silabico del canto. El pulso de la cancion tambien cae aqui, por eso
# este rasgo solo no basta y se combina con los otros.
MOD_BAJA = 2.0
MOD_ALTA = 8.0

SEGUNDOS_DE_MUESTRA = 75.0


@dataclass
class RasgosVoz:
    ruta: str = ""
    duracion: float = 0.0
    banda_voz: float = 0.0      # energia 300-3400 Hz sobre el total
    planitud: float = 0.0       # que "plano" es el espectro ahi (voz = formantes = menos plano)
    modulacion: float = 0.0     # energia de la envolvente en 2-8 Hz sobre el total
    contraste: float = 0.0      # contraste espectral medio en las bandas de la voz
    centro: float = 0.0         # cuanto de la banda de voz esta en el centro del estereo
    estereo: bool = False


def rasgos(ruta_audio: str | Path, segundos: float = SEGUNDOS_DE_MUESTRA) -> RasgosVoz | None:
    """Mide los cinco rasgos en un trozo del centro de la cancion."""
    import numpy as np
    import librosa

    ruta = Path(ruta_audio)
    salida = RasgosVoz(ruta=ruta.name)
    try:
        duracion_total = librosa.get_duration(path=str(ruta))
    except Exception:
        return None
    salida.duracion = float(duracion_total)
    desde = max(0.0, duracion_total / 2 - segundos / 2)

    try:
        estereo, sr = librosa.load(str(ruta), sr=11025, mono=False,
                                   offset=desde, duration=segundos)
    except Exception:
        return None
    if estereo.size == 0:
        return None

    if estereo.ndim == 2 and estereo.shape[0] == 2:
        salida.estereo = True
        medio = (estereo[0] + estereo[1]) / 2.0
        lado = (estereo[0] - estereo[1]) / 2.0
        y = medio
    else:
        y = estereo if estereo.ndim == 1 else estereo[0]
        lado = None

    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256))
    frecuencias = librosa.fft_frequencies(sr=sr, n_fft=1024)
    banda = (frecuencias >= BANDA_BAJA) & (frecuencias <= BANDA_ALTA)
    total = S.sum() + 1e-9
    salida.banda_voz = float(S[banda].sum() / total)

    trozo = S[banda] + 1e-10
    geometrica = np.exp(np.log(trozo).mean(axis=0))
    aritmetica = trozo.mean(axis=0)
    salida.planitud = float((geometrica / aritmetica).mean())

    envolvente = S[banda].sum(axis=0)
    envolvente = envolvente - envolvente.mean()
    if envolvente.size > 16:
        espectro = np.abs(np.fft.rfft(envolvente))
        tasa = sr / 256.0
        modulaciones = np.fft.rfftfreq(envolvente.size, d=1.0 / tasa)
        ventana = (modulaciones >= MOD_BAJA) & (modulaciones <= MOD_ALTA)
        salida.modulacion = float(espectro[ventana].sum() / (espectro.sum() + 1e-9))

    try:
        contraste = librosa.feature.spectral_contrast(S=S, sr=sr, n_bands=5)
        # las bandas 2 y 3 cubren mas o menos 250-4000 Hz
        salida.contraste = float(contraste[2:4].mean())
    except Exception:
        salida.contraste = 0.0

    if lado is not None:
        Sl = np.abs(librosa.stft(lado, n_fft=1024, hop_length=256))
        energia_lado = Sl[banda].sum() + 1e-9
        salida.centro = float(S[banda].sum() / energia_lado)
    return salida


# ---------------------------------------------------------------------------
# La decision
# ---------------------------------------------------------------------------

# Umbrales CALIBRADOS, no inventados: ver tools/banco_instrumental.py y
# docs/DECISIONES_MEDIDAS.md. Se rellenan cuando el banco los mida.
UMBRAL_CONTRASTE = 0.0
UMBRAL_MODULACION = 0.0


@dataclass
class Veredicto:
    instrumental: bool = False
    confianza: float = 0.0
    motivo: str = ""


def decidir(medida: RasgosVoz | None) -> Veredicto:
    """Instrumental o cantada, con la confianza que da la distancia al umbral."""
    if medida is None:
        return Veredicto(False, 0.0, "no se pudo leer el audio")
    if not UMBRAL_CONTRASTE:
        return Veredicto(False, 0.0, "sin calibrar: corre tools/banco_instrumental.py")
    puntos = 0
    razones = []
    if medida.contraste < UMBRAL_CONTRASTE:
        puntos += 1
        razones.append(f"contraste {medida.contraste:.2f} < {UMBRAL_CONTRASTE:.2f}")
    if medida.modulacion < UMBRAL_MODULACION:
        puntos += 1
        razones.append(f"modulacion {medida.modulacion:.3f} < {UMBRAL_MODULACION:.3f}")
    return Veredicto(
        instrumental=puntos >= 2,
        confianza=puntos / 2.0,
        motivo="; ".join(razones) or "tiene rasgos de voz",
    )
