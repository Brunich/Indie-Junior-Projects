"""Write a finished chart out as a folder Clone Hero can load directly."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from .chartio import Chart, write_chart

AUDIO_EXTENSIONS = (".ogg", ".mp3", ".opus", ".wav", ".flac")
ART_NAMES = ("album.png", "album.jpg", "album.jpeg")
# Clone Hero recognises these stem names; anything else is ignored by the game.
KNOWN_STEMS = {
    "song", "guitar", "bass", "rhythm", "vocals", "keys", "drums",
    "drums_1", "drums_2", "drums_3", "drums_4", "crowd", "preview",
}

_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_name(text: str) -> str:
    cleaned = _UNSAFE.sub("_", text).strip().rstrip(".")
    return cleaned or "Sin titulo"


# Windows no admite  < > : " / \ | ? *  en un nombre de carpeta, ni que acabe en
# punto o espacio. El titulo sale de `song.ini`, que SI los lleva: la carpeta de
# la biblioteca los tiene ya sustituidos, pero el `name` de dentro no. Sin esto,
# cualquier cancion con `?` en el titulo revienta el exportador con un WinError
# 123 ("syntax is incorrect") que no dice nada de lo que pasa de verdad.
_PROHIBIDOS = re.compile(r'[<>:"/\\|?*]')
_RESERVADOS = {"CON", "PRN", "AUX", "NUL",
               *(f"COM{i}" for i in range(1, 10)),
               *(f"LPT{i}" for i in range(1, 10))}


def nombre_seguro(nombre: str) -> str:
    """Un nombre de carpeta que Windows acepte, sin perder de que cancion es."""
    limpio = _PROHIBIDOS.sub("_", nombre).rstrip(". ")
    if limpio.split(".")[0].upper() in _RESERVADOS:
        limpio = "_" + limpio
    return limpio or "sin_nombre"


# Basura que traen los nombres de los ficheros bajados de YouTube. Si se deja,
# el titulo que va al `song.ini` es "DALI (Video Oficial)" y LRCLIB no encuentra
# la letra: busca por titulo exacto y ese parentesis lo tira todo.
_RUIDO_DE_TITULO = re.compile(
    r"\s*[\(\[]?\s*(video\s*oficial|videoclip\s*oficial|official\s*(music\s*)?video|"
    r"official\s*audio|audio\s*oficial|con\s*letra|letra[s]?|lyrics?|"
    r"sub\.?\s*espa\w*|subtitulad\w*|hd|4k|hq|full\s*hd|en\s*vivo\s*hd|"
    r"visualizer|remaster\w*|\d{4}\s*remaster\w*)\s*[\)\]]?\s*",
    re.IGNORECASE)
_SEPARADORES = ("｜｜", "||", "｜", "|")


def artista_y_titulo(nombre: str) -> tuple[str, str]:
    """De `MARCOS YTZ - DALI (Video Oficial)` saca `("MARCOS YTZ", "DALI")`.

    Si no hay un guion que separe, devuelve artista vacio y el nombre limpio:
    inventarse un artista es peor que no ponerlo, porque la busqueda de letra
    filtra por artista y un artista falso descarta las candidatas buenas.
    """
    limpio = nombre
    for separador in _SEPARADORES:
        limpio = limpio.split(separador)[0]
    limpio = _RUIDO_DE_TITULO.sub(" ", limpio)
    limpio = re.sub(r"[\(\[]\s*[\)\]]", " ", limpio)      # parentesis que quedaron vacios
    limpio = re.sub(r"\s{2,}", " ", limpio).strip(" -_.")

    for guion in (" - ", " – ", " — "):
        if guion in limpio:
            artista, _, titulo = limpio.partition(guion)
            return artista.strip(" -_."), titulo.strip(" -_.")
    return "", limpio


def read_song_ini(song_dir: Path) -> dict[str, str]:
    """Read an existing song.ini so generated charts keep the real metadata."""
    path = song_dir / "song.ini"
    if not path.is_file():
        return {}
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:  # pragma: no cover
        text = raw.decode("latin-1", errors="replace")
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("[", ";", "#")) or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip().lower()] = value.strip().strip('"')
    return values


def write_song_ini(
    path: Path,
    name: str,
    artist: str,
    album: str = "",
    genre: str = "",
    year: str = "",
    charter: str = "AutoChart",
    song_length_ms: int = 0,
    diff_guitar: int = 3,
    preview_start_ms: int = 0,
    delay_ms: int = 0,
) -> Path:
    lines = [
        "[Song]",
        f"name = {name}",
        f"artist = {artist}",
        f"album = {album}",
        f"genre = {genre}",
        f"year = {year}",
        f"charter = {charter}",
        f"song_length = {int(song_length_ms)}",
        f"diff_guitar = {int(diff_guitar)}",
        "diff_bass = -1",
        "diff_drums = -1",
        "diff_keys = -1",
        "diff_guitarghl = -1",
        "diff_bassghl = -1",
        f"preview_start_time = {int(preview_start_ms)}",
        f"delay = {int(delay_ms)}",
        "count = 0",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def export_song(
    chart: Chart,
    destination: Path,
    audio_source: Path,
    source_dir: Path | None = None,
    name: str = "Sin titulo",
    artist: str = "Desconocido",
    album: str = "",
    genre: str = "",
    year: str = "",
    charter: str = "AutoChart",
    duration_s: float = 0.0,
    copy_all_stems: bool = True,
    copy_audio: bool = True,
    diff_guitar: int = 3,
) -> Path:
    """Build `destination` with notes.chart, song.ini, audio and cover art.

    `copy_audio=False` writes only the chart and the ini. The benchmark uses it:
    it compares note positions and never plays anything, so copying gigabytes of
    ogg around would only cost time and disk.
    """
    destination = destination.parent / nombre_seguro(destination.name)
    destination.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    if source_dir is not None and copy_all_stems and copy_audio and source_dir.is_dir():
        for item in source_dir.iterdir():
            if item.is_file() and item.suffix.lower() in AUDIO_EXTENSIONS:
                if item.stem.lower() in KNOWN_STEMS:
                    shutil.copy2(item, destination / item.name)
                    copied.append(item.name)
        for art in ART_NAMES:
            candidate = source_dir / art
            if candidate.is_file():
                shutil.copy2(candidate, destination / art)
                break

    if not copied:
        target = destination / f"song{audio_source.suffix.lower()}"
        if copy_audio and audio_source.resolve() != target.resolve():
            shutil.copy2(audio_source, target)
        copied.append(target.name)

    stream = "song.ogg" if any(c.lower() == "song.ogg" for c in copied) else copied[0]
    chart.metadata["MusicStream"] = stream
    chart.metadata["Name"] = name
    chart.metadata["Artist"] = artist
    chart.metadata["Album"] = album
    chart.metadata["Genre"] = genre
    chart.metadata["Year"] = year
    chart.metadata["Charter"] = charter

    write_chart(chart, destination / "notes.chart")
    write_song_ini(
        destination / "song.ini",
        name=name,
        artist=artist,
        album=album,
        genre=genre,
        year=year,
        charter=charter,
        song_length_ms=int(duration_s * 1000),
        diff_guitar=diff_guitar,
    )
    return destination
