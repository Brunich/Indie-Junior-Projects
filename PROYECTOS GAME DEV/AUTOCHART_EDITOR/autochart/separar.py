"""Partir la cancion en pistas antes de escuchar nada.

POR QUE, con el numero que lo obligo
------------------------------------
Medido el 22-08-2026 con `tools/quien_toca.py`: el **58-63 %** de las notas que
escribia el generador caian en un instante mas percusivo que armonico, y en
`Brunich - Electro_guitar_Cyber_Club_v1` -- una cancion de guitarra -- el filtro
de densidad elegia ataques **menos** melodicos que la media de la propia cancion
(lead 0.668 contra 0.692). El chart estaba escribiendo la bateria, y una bateria
suena igual en todas las canciones: por eso los 15 charts generados se parecian
entre si 7.5 veces mas que 16 humanos (`tools/parecidas.py`).

Esto no se arregla subiendo `LEAD_PRIORITY`. Mientras la fuente sea la mezcla,
lo mas fuerte de cada ventana sigue siendo el bombo.

Separar se habia despriorizado con el F1 del banco ("forzando la mezcla solo baja
de 0.648 a 0.618"), pero el F1 compara **cuando** suena una nota, no **cual**
(CLAUDE.md §2, trampa 1): bateria y guitarra atacan en el mismo sitio de la
rejilla, asi que esa medida no podia ver la diferencia. Ver
`docs/PLAN_TOCAR_LA_CANCION.md` §4.

COMO
----
`demucs` (htdemucs, 4 pistas) sobre CPU: **~1 min 22 s por cada 2:44 de
cancion**, una sola vez. Las pistas se guardan en mono a 22 050 Hz -- que es
exactamente lo que usa el analisis -- en vez de los 44.1 kHz estereo que saca
demucs: **109 MB por cancion pasan a unos 7**.

    python -m autochart separar "<carpeta de cancion>"
    python -m autochart separar "<carpeta>" --forzar
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

PISTAS = ("vocals", "drums", "bass", "other")
MODELO = "htdemucs"
DESTINO = Path("salida") / "stems"
# Lo unico que usa el analisis (audio.ANALYSIS_SR). Guardar mas es guardar peso.
MUESTREO = 22050
# Las pistas de las que puede salir una nota. La bateria y el bajo no: el bajo
# es lo que arrastraba el contorno hacia MIDI 52 y por debajo (ver docs/AUDITORIA_POR_QUE_NO_SUENA.md
# en audio.py), y la bateria es justamente el problema que se esta quitando.
PISTAS_DE_NOTAS = ("other", "vocals")


def _ffmpeg(args: list[str]) -> bool:
    if shutil.which("ffmpeg") is None:
        return False
    return subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args]).returncode == 0


def carpeta_de(nombre: str, destino: Path | str = DESTINO) -> Path:
    return Path(destino) / nombre


def stems_de(nombre: str, destino: Path | str = DESTINO) -> dict[str, Path] | None:
    """Las pistas ya separadas de esta cancion, o None si no estan las cuatro."""
    carpeta = carpeta_de(nombre, destino)
    encontradas = {p: carpeta / f"{p}.ogg" for p in PISTAS}
    if all(f.exists() for f in encontradas.values()):
        return encontradas
    return None


def separar(mezcla: str | Path, nombre: str | None = None,
            destino: Path | str = DESTINO, forzar: bool = False,
            modelo: str = MODELO) -> dict[str, Path] | None:
    """Saca las cuatro pistas de `mezcla`. Si ya estan, no repite el trabajo."""
    mezcla = Path(mezcla)
    nombre = nombre or mezcla.parent.name
    ya = stems_de(nombre, destino)
    if ya and not forzar:
        return ya

    carpeta = carpeta_de(nombre, destino)
    carpeta.mkdir(parents=True, exist_ok=True)
    crudo = carpeta / "_crudo"
    if crudo.exists():
        shutil.rmtree(crudo, ignore_errors=True)

    hecho = subprocess.run(
        ["python", "-m", "demucs", "-n", modelo, "-d", "cpu",
         "-o", str(crudo), "--filename", "{stem}.{ext}", str(mezcla)],
        capture_output=True, text=True,
    )
    if hecho.returncode != 0:
        print(f"[X] demucs fallo en {nombre}: {(hecho.stderr or '').strip()[-300:]}")
        shutil.rmtree(crudo, ignore_errors=True)
        return None

    origen = crudo / modelo
    salida: dict[str, Path] = {}
    for pista in PISTAS:
        wav = origen / f"{pista}.wav"
        if not wav.exists():
            continue
        destino_ogg = carpeta / f"{pista}.ogg"
        if _ffmpeg(["-i", str(wav), "-ac", "1", "-ar", str(MUESTREO),
                    "-c:a", "libvorbis", "-q:a", "4", str(destino_ogg)]):
            salida[pista] = destino_ogg
    shutil.rmtree(crudo, ignore_errors=True)

    if len(salida) != len(PISTAS):
        print(f"[X] {nombre}: solo salieron {len(salida)} de {len(PISTAS)} pistas")
        return None
    return salida


def pista_de_notas(nombre: str, destino: Path | str = DESTINO,
                   incluir: tuple[str, ...] = PISTAS_DE_NOTAS) -> Path | None:
    """La pista de la que salen los ataques: todo menos bateria y bajo.

    Se mezcla una sola vez y se guarda como `notas.ogg`. Quien manda en cada
    tramo -- la voz o el instrumento -- lo decide S2; aqui todavia van juntos,
    que ya es infinitamente mejor que ir con el bombo.
    """
    carpeta = carpeta_de(nombre, destino)
    salida = carpeta / "notas.ogg"
    if salida.exists():
        return salida
    stems = stems_de(nombre, destino)
    if stems is None:
        return None
    fuentes = [stems[p] for p in incluir if p in stems]
    if not fuentes:
        return None
    if len(fuentes) == 1:
        shutil.copy2(fuentes[0], salida)
        return salida
    args: list[str] = []
    for f in fuentes:
        args += ["-i", str(f)]
    # `normalize=0`: amix baja el volumen de cada entrada por defecto, y eso
    # aplana los ataques justo antes de medirlos.
    args += ["-filter_complex", f"amix=inputs={len(fuentes)}:normalize=0",
             "-ac", "1", "-ar", str(MUESTREO), "-c:a", "libvorbis", "-q:a", "4",
             str(salida)]
    return salida if _ffmpeg(args) else None
