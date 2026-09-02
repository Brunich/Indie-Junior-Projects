"""Grabar un chart tocando encima de la cancion.

    autochart grabar <carpeta>              toca y se escribe lo que toques
    autochart grabar <carpeta> --calibrar   mide TU latencia, una vez

La logica esta aqui y la ventana solo llama, igual que en `interfaz.py`: asi lo
que decide algo se puede probar sin abrir una ventana ni tener un mando.

**Cero dependencias nuevas.** El audio suena con `winsound`, que viene con
Python en Windows, y `ffmpeg` -- que el proyecto ya exige para los mp3 -- lo
convierte a WAV y recorta el tramo. `winsound` no sabe buscar dentro de un
fichero, asi que grabar solo un tramo se hace recortandolo antes: sale gratis y
ademas evita esperar a que llegue el minuto tres.

## Por que hace falta calibrar, y por que no se puede adivinar

Entre que se llama a reproducir y que el sonido sale de los cascos pasa un
tiempo, y entre que se oye y que la mano llega, otro. Los dos suman siempre lo
mismo, asi que **todas** las notas salen corridas.

Y ese corrimiento **no se puede adivinar del todo**: desde la fase es
indistinguible modulo una subdivision -- correr un chart una semicorchea entera
lo deja exactamente igual de en fase (medido, `editar.adivinar_desfase`). Por eso
esto se calibra UNA vez, como hace Editor on Fire, y a partir de ahi
`editar.desde_toques` solo afina el resto.
"""

from __future__ import annotations

import statistics
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

AUDIO = (".ogg", ".mp3", ".opus", ".wav", ".flac")

## Las cinco teclas, en el orden de los carriles del chart (verde a naranja).
## Son las de Clone Hero por defecto, para que la mano ya se las sepa.
TECLAS_POR_CARRIL: dict[str, int] = {"a": 0, "s": 1, "j": 2, "k": 3, "l": 4}

## Cuantos clics tiene la pista de calibrado y cada cuanto van. Un segundo entre
## clics deja sitio de sobra para cualquier latencia creible sin que una pulsacion
## se confunda con el clic siguiente.
CALIBRADO_CLICS = 16
CALIBRADO_SEGUNDOS = 1.0


@dataclass
class SesionDeGrabacion:
    """El reloj y la lista de lo tocado. No sabe nada de ventanas ni de audio."""

    desde_s: float = 0.0          # a que segundo de la cancion empieza lo grabado
    _t0: float | None = None
    toques: list[tuple[float, int]] = field(default_factory=list)

    def empezar(self, reloj: float | None = None) -> None:
        self._t0 = time.perf_counter() if reloj is None else reloj

    @property
    def en_marcha(self) -> bool:
        return self._t0 is not None

    def golpe(self, carril: int, reloj: float | None = None) -> float | None:
        """Apuntar un golpe. Devuelve el segundo DE LA CANCION, o None si no corre."""
        if self._t0 is None:
            return None
        ahora = time.perf_counter() if reloj is None else reloj
        segundo = self.desde_s + (ahora - self._t0)
        self.toques.append((segundo, int(carril)))
        return segundo

    def parar(self) -> list[tuple[float, int]]:
        self._t0 = None
        return sorted(self.toques)


def calibrar_desfase(taps: list[float], clics: list[float]) -> tuple[float, int, float]:
    """Tu latencia, medida. Devuelve `(ms, cuantos_valieron, dispersion_ms)`.

    Suena una pista de clics en segundos conocidos y se teclea encima. Cada
    pulsacion se empareja con el clic MAS CERCANO y la latencia es la mediana de
    las diferencias.

    Tres decisiones que hacen que esto no mienta:

    * **Mediana y no media.** Una pulsacion perdida o un doble golpe arrastran la
      media y no mueven la mediana.
    * **Se tira lo que cae a mas de medio hueco entre clics.** Mas alla de eso no
      se sabe a que clic pertenecia, y adivinarlo es inventar.
    * **Se devuelve la dispersion.** Si tus pulsaciones bailan 80 ms entre ellas,
      la mediana es una cifra bonita sobre un pulso que no existe, y quien lea
      esto tiene que poder verlo. Sin ese numero, la latencia parece exacta.
    """
    if not taps or not clics:
        return (0.0, 0, 0.0)
    medio_hueco = (max(clics) - min(clics)) / max(1, len(clics) - 1) / 2.0
    diferencias: list[float] = []
    for tap in taps:
        cerca = min(clics, key=lambda c: abs(tap - c))
        if abs(tap - cerca) <= medio_hueco:
            diferencias.append(cerca - tap)
    if not diferencias:
        return (0.0, 0, 0.0)
    ms = statistics.median(diferencias) * 1000.0
    dispersion = (statistics.pstdev(diferencias) * 1000.0) if len(diferencias) > 1 else 0.0
    return (ms, len(diferencias), dispersion)


def elegir_audio(carpeta: Path) -> Path | None:
    """El audio de una carpeta de cancion, con la guitarra la ultima.

    Para grabar interesa la mezcla COMPLETA, no el stem: se toca contra lo que
    suena en el juego. El generador prefiere `guitar.ogg` porque mide ataques;
    aqui es al reves.
    """
    if carpeta.is_file():
        return carpeta if carpeta.suffix.lower() in AUDIO else None
    for nombre in ("song.ogg", "song.mp3", "song.opus", "song.wav"):
        if (carpeta / nombre).is_file():
            return carpeta / nombre
    sueltos = [p for p in sorted(carpeta.iterdir())
               if p.is_file() and p.suffix.lower() in AUDIO and p.stem.lower() != "guitar"]
    return sueltos[0] if sueltos else None


def preparar_wav(origen: Path, destino: Path, desde_s: float = 0.0,
                 hasta_s: float | None = None) -> Path:
    """Pasar el audio a WAV (y recortarlo) para que `winsound` pueda con el.

    `winsound` solo reproduce WAV y no sabe buscar dentro del fichero, asi que el
    tramo se recorta AQUI. `-ss` va antes de `-i` a proposito: asi ffmpeg salta
    sin decodificar lo anterior, que en una cancion de cinco minutos es la
    diferencia entre esperar y no esperar.
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    orden = ["ffmpeg", "-y", "-loglevel", "error"]
    if desde_s > 0.0:
        orden += ["-ss", f"{desde_s:.3f}"]
    orden += ["-i", str(origen)]
    if hasta_s is not None and hasta_s > desde_s:
        orden += ["-t", f"{hasta_s - desde_s:.3f}"]
    orden += ["-ac", "2", "-ar", "44100", str(destino)]
    subprocess.run(orden, check=True, capture_output=True)
    return destino


def pista_de_calibrado(destino: Path, clics: int = CALIBRADO_CLICS,
                       cada_s: float = CALIBRADO_SEGUNDOS) -> tuple[Path, list[float]]:
    """Un WAV con clics en segundos conocidos, y la lista de esos segundos.

    Se sintetiza aqui para no meter un asset nuevo al repo por algo que es una
    cuenta, y **con `wave` en vez de con ffmpeg**: el filtro `aevalsrc` necesita
    `between(t,a,b)` y esas comas chocan con la sintaxis de filtros de ffmpeg, que
    las lee como separador. Escaparlas es fragil para algo que son treinta lineas
    de libreria estandar.

    El primer clic va en `cada_s` y no en 0: nadie llega a tiempo al que suena en
    el instante en que le das al boton, y ese tap arrastraria la medida.

    El clic es una senoide de 1 kHz de 25 ms con entrada y salida suaves. La
    rampa no es un adorno: un pulso cortado en seco chasquea, y **este proyecto
    tiene una regla de oidos** -- se toca con auriculares. Va ademas a media
    amplitud por lo mismo.
    """
    import math
    import wave

    destino.parent.mkdir(parents=True, exist_ok=True)
    momentos = [cada_s * (i + 1) for i in range(clics)]
    hz = 44100
    total = cada_s * (clics + 1)
    muestras = bytearray()
    largo_clic = int(0.025 * hz)
    n_total = int(total * hz)
    valores = [0.0] * n_total
    for m in momentos:
        inicio = int(m * hz)
        for i in range(largo_clic):
            if inicio + i >= n_total:
                break
            ## rampa de subida y bajada, para que no chasquee
            sobre = i / largo_clic
            envolvente = min(1.0, 8.0 * min(sobre, 1.0 - sobre))
            valores[inicio + i] = 0.5 * envolvente * math.sin(2.0 * math.pi * 1000.0 * i / hz)
    for v in valores:
        entero = max(-32767, min(32767, int(v * 32767)))
        muestras += int(entero).to_bytes(2, "little", signed=True)

    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(hz)
        w.writeframes(bytes(muestras))
    return (destino, momentos)


def sonar(wav: Path) -> None:
    """Empezar a sonar sin bloquear. Solo Windows, que es donde se juega esto."""
    import winsound
    winsound.PlaySound(str(wav), winsound.SND_FILENAME | winsound.SND_ASYNC)


def callar() -> None:
    import winsound
    winsound.PlaySound(None, winsound.SND_PURGE)
