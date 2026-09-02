"""Poner letra de karaoke a una cancion: buscarla, verificarla y escribirla.

Es el nivel B de `docs/PLAN_VOZ.md`: la linea aparece a tiempo Y se colorea
silaba a silaba. La animacion no se programa -- Clone Hero colorea solo si el
chart trae **un evento `lyric` por silaba**; lo unico que hay que hacer es
partir bien y colocar bien.

De donde sale la letra, en orden:

    0. la cancion ya la trae            -> no se toca (voz.leer_voz)
    1. LRCLIB (lrclib.net)              -> letra YA SINCRONIZADA por linea
    2. un `.lrc` al lado del audio      -> igual que 1
    3. un `.txt` al lado del audio      -> sin tiempos, hay que alinear

**Nada de lo que se baja se acepta sin verificar.** El fallo numero uno de esto
es que la letra este cronometrada contra otro master: otra edicion, otro intro,
otra remasterizacion. Aplicada tal cual, va corrida toda la cancion y parece que
el programa esta roto. Las comprobaciones estan en `verificar()`.

Nada de esto escribe en la biblioteca. La salida va a `salida/`.
"""

from __future__ import annotations

import json
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from . import silabas

API = "https://lrclib.net/api"
AGENTE = "AutoChart/0.1 (uso personal; https://github.com/Brunich/clonehero-autochart)"
_RE_PARENTESIS = re.compile(r"\([^)]*\)")

# La firma que deja AutoChart en la letra que escribe. Sirve para una sola cosa
# y es importante: distinguir "esta letra la puse yo" de "esta letra la escribio
# una persona". Sin ella, `--forzar` sobre la biblioteca entera piso 112 letras
# hechas a mano -- 42 655 silabas cronometradas oyendo la cancion. Que exista un
# boton de deshacer no basta: eso no deberia poder pasar.
MARCA_AUTOCHART = "autochart_lyrics"

# --- topes sacados de las 128 canciones con voz humana de la biblioteca -----
SILABAS_POR_SEGUNDO_P50 = 2.9
SILABAS_POR_SEGUNDO_P75 = 3.74
SILABAS_POR_SEGUNDO_P95 = 5.55
# El humano escribe 8 silabas por frase para 6 palabras (medianas medidas): o
# sea 1.33 trozos por palabra, no todos los que caben. Partirlas todas da un
# 33 % de silabas enlazadas contra el 13.9 % humano -- se nota como una linea
# troceada de mas. Este factor es el freno.
TROZOS_POR_PALABRA = 8.0 / 6.0
DURACION_SILABA_P5 = 0.126      # s: por debajo de esto no es una silaba cantada
AVISO_DE_FRASE_S = 0.06         # medido: es la mediana de los 128 charts humanos
SEGUNDOS_POR_FRASE_P95 = 5.82
# Cuanto dura la ULTIMA silaba de una frase, cuando no hay con que medirlo.
# Es la mediana humana de duracion de silaba. Antes aqui habia un
# HUECO_FIN_DE_FRASE_S = 0.30 que cerraba la frase 0.30 s antes de la linea
# siguiente: eso hacia el hueco CONSTANTE (0.15 s en las 198 canciones puestas)
# cuando en los charts humanos va de 0.07 a 0.73 segun la musica. El hueco no
# se elige: la frase acaba cuando se deja de cantar y el hueco es lo que quede.
DURACION_ULTIMA_SILABA_S = 0.28
HUECO_MINIMO_ENTRE_FRASES_S = 0.05

# --- limites de la verificacion --------------------------------------------
TOLERANCIA_DURACION = 0.03       # sin audio: 3 %, y no hay segunda opinion
TOLERANCIA_CON_AUDIO = 0.08      # con audio: 8 %, porque despues juzga el canto
DERIVA_MAXIMA = 0.005           # 0.5 % de estiramiento
RESIDUO_MAXIMO_S = 0.40
FRACCION_MALA_MAXIMA = 0.20


@dataclass
class LineaLetra:
    segundos: float
    texto: str


@dataclass
class Candidata:
    artista: str = ""
    titulo: str = ""
    duracion: float = 0.0
    sincronizada: str = ""
    plana: str = ""
    instrumental: bool = False

    @property
    def tiene_tiempos(self) -> bool:
        return bool(self.sincronizada)


# ---------------------------------------------------------------------------
# 1. Buscar
# ---------------------------------------------------------------------------


def _pedir(ruta: str, parametros: dict) -> list | dict | None:
    url = f"{API}/{ruta}?" + urllib.parse.urlencode(parametros)
    peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    try:
        with urllib.request.urlopen(peticion, timeout=20) as respuesta:
            return json.load(respuesta)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None
    except json.JSONDecodeError:
        return None


def _sin_adornos(texto: str) -> str:
    """Quita tildes, parentesis y todo lo que no sea letra, para comparar."""
    texto = re.sub(r"\((?:feat|ft|con|with)[^)]*\)", " ", texto, flags=re.I)
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", texto.lower())


def buscar(artista: str, titulo: str, duracion: float = 0.0) -> list[Candidata]:
    """Busca en LRCLIB y devuelve las candidatas ordenadas por lo bien que encajan.

    La duracion es lo que separa la version del disco de la del directo, del
    remix y de la de 11 minutos que alguien subio.
    """
    crudas = _pedir("search", {"track_name": titulo, "artist_name": artista})
    if not crudas:
        # Los rips de Guitar Hero traen la banda de estudio metida en el nombre
        # del artista: `Audioslave (WaveGroup)`, `KISS (Steve Ouimette)`. LRCLIB
        # tiene "Audioslave", y asi 62 de las 74 canciones que "no existian"
        # aparecen. OJO: son COVERS, o sea otra grabacion -- la letra sera la
        # correcta pero los tiempos son los del original, y de eso ya se encarga
        # la verificacion contra el audio.
        limpio = _RE_PARENTESIS.sub(" ", artista).strip()
        if limpio and limpio != artista:
            crudas = _pedir("search", {"track_name": titulo, "artist_name": limpio})
    if not crudas:
        crudas = _pedir("search", {"q": f"{artista} {titulo}"}) or []
    candidatas: list[Candidata] = []
    for item in crudas:
        if not isinstance(item, dict):
            continue
        candidatas.append(Candidata(
            artista=item.get("artistName") or "",
            titulo=item.get("trackName") or "",
            duracion=float(item.get("duration") or 0.0),
            sincronizada=item.get("syncedLyrics") or "",
            plana=item.get("plainLyrics") or "",
            instrumental=bool(item.get("instrumental")),
        ))

    objetivo_t, objetivo_a = _sin_adornos(titulo), _sin_adornos(artista)

    def puntuar(c: Candidata) -> tuple:
        cerca = abs(c.duracion - duracion) if duracion and c.duracion else 9999
        titulo_ok = _sin_adornos(c.titulo) == objetivo_t
        artista_ok = objetivo_a in _sin_adornos(c.artista) or _sin_adornos(c.artista) in objetivo_a
        # primero las que tienen tiempos, luego titulo/artista exactos, luego duracion
        return (not c.tiene_tiempos, not titulo_ok, not artista_ok, cerca)

    return sorted(candidatas, key=puntuar)


def elegir(candidatas: list[Candidata], duracion: float,
           habra_audio: bool = False) -> Candidata | None:
    """La mejor candidata que ademas cuadre en duracion. Si ninguna cuadra, None.

    La duracion es un **prefiltro barato**, no el juez. Cuando despues se va a
    verificar contra el audio, se puede aflojar: el que decide de verdad es si
    se canta donde la letra dice. Sin audio no hay segunda opinion y hay que
    ser estricto, porque una letra corrida es peor que no tener letra.
    """
    tope = TOLERANCIA_CON_AUDIO if habra_audio else TOLERANCIA_DURACION
    for c in candidatas:
        if c.instrumental or not c.tiene_tiempos:
            continue
        if duracion and c.duracion:
            if abs(c.duracion - duracion) / duracion > tope:
                continue
        return c
    return None


# ---------------------------------------------------------------------------
# 2. Leer el .lrc
# ---------------------------------------------------------------------------

_RE_MARCA = re.compile(r"\[(\d+):(\d+(?:[.:]\d+)?)\]")


def leer_lrc(texto: str) -> list[LineaLetra]:
    """Convierte un `.lrc` en lineas con su segundo. Una linea puede tener varias marcas."""
    lineas: list[LineaLetra] = []
    for cruda in texto.splitlines():
        marcas = list(_RE_MARCA.finditer(cruda))
        if not marcas:
            continue
        contenido = cruda[marcas[-1].end():].strip()
        if not contenido:
            continue  # una marca sin texto es un silencio, no una linea
        for marca in marcas:
            minutos = int(marca.group(1))
            segundos = float(marca.group(2).replace(":", "."))
            lineas.append(LineaLetra(minutos * 60 + segundos, contenido))
    lineas.sort(key=lambda l: l.segundos)
    return lineas


# ---------------------------------------------------------------------------
# 3. Verificar contra el audio
# ---------------------------------------------------------------------------


@dataclass
class Veredicto:
    vale: bool = False
    motivo: str = ""
    desfase: float = 0.0
    deriva: float = 1.0
    residuo: float = 0.0
    lineas_malas: float = 0.0


def energia_de_voz(ruta_audio: Path, hasta_segundos: float = 0.0):
    """Envolvente de energia en la banda donde vive la voz (200-4000 Hz).

    Se usa solo para VERIFICAR que la letra bajada cuadra con este audio, no
    para colocar silabas. Por eso se carga a 11 kHz: sobra y es cuatro veces
    mas rapido.
    """
    import numpy as np
    import librosa

    y, sr = librosa.load(str(ruta_audio), sr=11025, mono=True,
                         duration=hasta_segundos or None)
    if y.size == 0:
        return None, None
    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256))
    frecuencias = librosa.fft_frequencies(sr=sr, n_fft=1024)
    banda = (frecuencias >= 200) & (frecuencias <= 4000)
    envolvente = S[banda].sum(axis=0)
    if envolvente.max() > 0:
        envolvente = envolvente / envolvente.max()
    tiempos = librosa.frames_to_time(np.arange(envolvente.size), sr=sr, hop_length=256)
    return tiempos, envolvente


def verificar(
    lineas: list[LineaLetra],
    duracion_audio: float,
    duracion_declarada: float = 0.0,
    ruta_audio: Path | None = None,
) -> Veredicto:
    """Las cuatro comprobaciones del plan, en orden de coste."""
    if not lineas:
        return Veredicto(False, "la letra no trae ni una linea con tiempo")

    # 1) duracion declarada por la fuente
    if duracion_declarada and duracion_audio:
        error = abs(duracion_declarada - duracion_audio) / duracion_audio
        tope = TOLERANCIA_CON_AUDIO if (ruta_audio and ruta_audio.is_file()) else TOLERANCIA_DURACION
        if error > tope:
            return Veredicto(False, f"otra version: {error * 100:.1f} % de diferencia "
                                    f"de duracion ({duracion_declarada:.0f}s contra "
                                    f"{duracion_audio:.0f}s)")

    # 2) que la letra no se salga del audio
    if duracion_audio and lineas[-1].segundos > duracion_audio + 5:
        return Veredicto(False, f"la ultima linea cae en {lineas[-1].segundos:.0f}s y la "
                                f"cancion dura {duracion_audio:.0f}s")

    if ruta_audio is None or not ruta_audio.is_file():
        return Veredicto(True, "solo verificada por duracion (sin audio)")

    # 3) desfase y deriva contra la energia de voz
    import numpy as np

    tiempos, envolvente = energia_de_voz(ruta_audio)
    if tiempos is None:
        return Veredicto(True, "solo verificada por duracion (audio ilegible)")

    subida = np.diff(envolvente, prepend=envolvente[0]).clip(min=0)
    marcas = np.array([l.segundos for l in lineas if l.segundos < tiempos[-1]])
    if marcas.size < 4:
        return Veredicto(True, "pocas lineas dentro del audio para verificar")

    def puntuacion(desfase: float) -> float:
        indices = np.searchsorted(tiempos, marcas + desfase)
        indices = indices[(indices > 0) & (indices < subida.size - 4)]
        if indices.size == 0:
            return 0.0
        # cuanta energia de ataque hay justo donde la letra dice que se canta
        ventana = np.stack([subida[indices + k] for k in range(-2, 5)])
        return float(ventana.max(axis=0).mean())

    rejilla = np.arange(-3.0, 3.01, 0.05)
    puntos = np.array([puntuacion(d) for d in rejilla])
    mejor = float(rejilla[int(puntos.argmax())])
    base = float(np.median(puntos))
    if puntos.max() <= base * 1.05:
        return Veredicto(False, "la letra no cuadra con ningun desfase: "
                                "no se canta donde dice", desfase=mejor)

    # 4) residuo: cuantas lineas siguen lejos de un arranque de canto
    indices = np.searchsorted(tiempos, marcas + mejor).clip(3, subida.size - 6)
    cerca = np.stack([subida[indices + k] for k in range(-3, 6)]).max(axis=0)
    malas = float((cerca < np.percentile(subida, 60)).mean())
    veredicto = Veredicto(
        vale=malas <= FRACCION_MALA_MAXIMA,
        desfase=mejor,
        lineas_malas=malas,
    )
    veredicto.motivo = (f"desfase {mejor:+.2f}s, {malas * 100:.0f} % de lineas sin canto cerca"
                        if veredicto.vale else
                        f"{malas * 100:.0f} % de las lineas no tienen canto cerca "
                        f"(tope {FRACCION_MALA_MAXIMA * 100:.0f} %)")
    return veredicto


# ---------------------------------------------------------------------------
# 4. De lineas a silabas colocadas
# ---------------------------------------------------------------------------


@dataclass
class FraseKaraoke:
    inicio_s: float
    fin_s: float
    silabas: list[tuple[float, str, bool]] = field(default_factory=list)  # (s, texto, enlaza)


def _reparto(trozos: list[str]) -> list[float]:
    """Peso de cada silaba: las que tienen mas vocales duran mas al cantarse."""
    pesos = []
    for trozo in trozos:
        vocales = sum(1 for c in trozo.lower() if c in "aeiouáéíóúü")
        pesos.append(1.0 + 0.35 * max(0, vocales - 1) + 0.05 * len(trozo))
    total = sum(pesos) or 1.0
    return [p / total for p in pesos]


def _partir_en_palabras(texto: str, idioma: str) -> list[list[str]]:
    """La linea partida en palabras, y cada palabra en sus silabas."""
    palabras = []
    for bruta in texto.split():
        trozos = [t for t in silabas.dividir_linea(bruta, idioma) if t]
        if trozos:
            palabras.append(trozos)
    return palabras


def _pegar_hasta(palabras: list[list[str]], maximo: int) -> list[list[str]]:
    """Reduce el numero de silabas pegandolas DENTRO de cada palabra.

    Nunca se pegan dos palabras distintas: una palabra partida a medias se lee
    mal, pero dos palabras enteras juntas se leen bien. Se recorta siempre por
    la palabra que mas trozos tenga, que es la que menos se nota.
    """
    palabras = [list(p) for p in palabras]
    while sum(len(p) for p in palabras) > maximo:
        candidatas = [i for i, p in enumerate(palabras) if len(p) > 1]
        if not candidatas:
            break
        mas_larga = max(candidatas, key=lambda i: len(palabras[i]))
        trozos = palabras[mas_larga]
        palabras[mas_larga] = [trozos[0] + trozos[1], *trozos[2:]]
    return palabras


def repartir_linea(
    linea: LineaLetra,
    fin_s: float,
    idioma: str,
    ajustar=None,
) -> FraseKaraoke:
    """Parte la linea y reparte las silabas dentro de su ventana.

    **El silabeador es el techo, no el que decide.** Medido contra los cortes
    humanos: partir cada palabra da el doble de eventos que un humano, porque el
    humano parte segun la MELODIA y una palabra cantada en una nota se queda
    entera. Aqui, sin melodia por silaba, el freno lo pone la velocidad de canto
    medida: si no caben a p95 (5.55 silabas/s), se vuelven a pegar.
    """
    disponible = max(0.35, min(fin_s - linea.segundos, SEGUNDOS_POR_FRASE_P95))
    palabras = _partir_en_palabras(linea.texto, idioma)
    if not palabras:
        return FraseKaraoke(linea.segundos, linea.segundos + disponible)

    # Un humano canta la frase y CALLA. Repartir las silabas por toda la ventana
    # hasta la linea siguiente deja la ultima pegada a la siguiente y el hueco
    # entre frases sale de 0.2 s cuando el humano esta en 0.36 (p75 0.73). Lo
    # que dura cantar una linea es su numero de silabas a la velocidad medida.
    cantando = sum(len(p) for p in palabras) / SILABAS_POR_SEGUNDO_P50
    ventana = max(0.35, min(disponible, cantando))

    # Dos frenos, manda el mas estricto: lo que se puede CANTAR en la ventana
    # y lo que un humano PARTIRIA para ese numero de palabras.
    por_tiempo = int(ventana * SILABAS_POR_SEGUNDO_P75)
    por_palabras = round(len(palabras) * TROZOS_POR_PALABRA)
    caben = max(len(palabras), min(por_tiempo, por_palabras))
    if sum(len(p) for p in palabras) > caben:
        palabras = _pegar_hasta(palabras, caben)

    # Aplanar guardando quien es la ULTIMA silaba de su palabra: esa no enlaza.
    plano: list[tuple[str, bool]] = []
    for trozos in palabras:
        for indice, trozo in enumerate(trozos):
            plano.append((trozo, indice < len(trozos) - 1))

    pesos = _reparto([t for t, _ in plano])
    colocadas: list[tuple[float, str, bool]] = []
    transcurrido = 0.0
    for (trozo, enlaza), peso in zip(plano, pesos):
        momento = linea.segundos + transcurrido * ventana
        if ajustar is not None:
            momento = ajustar(momento)
        colocadas.append((momento, trozo.strip(), enlaza))
        transcurrido += peso
    return FraseKaraoke(linea.segundos, linea.segundos + ventana, colocadas)


SILABAS_POR_FRASE_P95 = 15      # por encima de esto no cabe en pantalla
JUNTAR_SI_MENOS_DE_S = 0.35     # dos marcas tan pegadas son el mismo momento


def _juntar_pegadas(lineas: list[LineaLetra]) -> list[LineaLetra]:
    """Une las lineas del `.lrc` que caen practicamente a la vez.

    Pasa a menudo: el que sincronizo puso dos marcas casi iguales, o la misma
    linea dos veces seguidas. Si se dejan tal cual salen frases solapadas, y el
    juego borra la anterior a media palabra.
    """
    salida: list[LineaLetra] = []
    for linea in lineas:
        if salida and linea.segundos - salida[-1].segundos < JUNTAR_SI_MENOS_DE_S:
            salida[-1] = LineaLetra(salida[-1].segundos,
                                    f"{salida[-1].texto} {linea.texto}".strip())
        else:
            salida.append(linea)
    return salida


def _partir_frase_larga(frase: FraseKaraoke) -> list[FraseKaraoke]:
    """Una linea de 30 silabas no es una linea de karaoke: son dos.

    El humano no pasa de 15 silabas por frase (p95 medido). Se corta por un
    final de palabra, para no dejar media palabra en cada linea.
    """
    if len(frase.silabas) <= SILABAS_POR_FRASE_P95:
        return [frase]
    # ceil, no round: con 16 silabas y round() salia 1 trozo y no partia nada.
    trozos = max(2, -(-len(frase.silabas) // SILABAS_POR_FRASE_P95))
    objetivo = len(frase.silabas) / trozos
    finales = [i + 1 for i, (_, _, enlaza) in enumerate(frase.silabas[:-1]) if not enlaza]
    if not finales:
        return [frase]
    cortes: list[int] = []
    for numero in range(1, trozos):
        ideal = objetivo * numero
        mejor = min(finales, key=lambda i: abs(i - ideal))
        if mejor not in cortes:
            cortes.append(mejor)

    salida: list[FraseKaraoke] = []
    limites = [0, *sorted(cortes), len(frase.silabas)]
    for desde, hasta in zip(limites, limites[1:]):
        grupo = frase.silabas[desde:hasta]
        if not grupo:
            continue
        fin = (frase.silabas[hasta][0] - HUECO_MINIMO_ENTRE_FRASES_S
               if hasta < len(frase.silabas) else frase.fin_s)
        salida.append(FraseKaraoke(grupo[0][0], max(grupo[-1][0] + 0.2, fin), grupo))
    return salida


def construir_frases(
    lineas: list[LineaLetra],
    idioma: str,
    desfase: float = 0.0,
    ajustar: callable = None,
    duracion: float = 0.0,
) -> list[FraseKaraoke]:
    """Todas las lineas convertidas en frases con sus silabas colocadas.

    Tres cosas que hay que hacer aqui y que el `.lrc` no trae hechas: juntar las
    marcas pegadas, partir las lineas que no caben en pantalla, y **garantizar
    que ninguna frase pisa a la siguiente** -- el juego borra la linea anterior
    en cuanto empieza la nueva, asi que un solapamiento se ve como texto que
    desaparece a media palabra.
    """
    lineas = _juntar_pegadas(sorted(lineas, key=lambda l: l.segundos))
    frases: list[FraseKaraoke] = []
    for indice, linea in enumerate(lineas):
        corrida = LineaLetra(linea.segundos + desfase, linea.texto)
        if indice + 1 < len(lineas):
            siguiente = lineas[indice + 1].segundos + desfase
            fin = max(corrida.segundos + 0.4, siguiente - DURACION_ULTIMA_SILABA_S)
        else:
            fin = corrida.segundos + SEGUNDOS_POR_FRASE_P95
            if duracion:
                fin = min(fin, duracion - 0.1)
        if duracion and corrida.segundos >= duracion - 0.2:
            continue   # una linea que empieza despues del final no existe
        frase = repartir_linea(corrida, fin, idioma, ajustar)
        if frase.silabas:
            frases.extend(_partir_frase_larga(frase))

    # La frase acaba cuando se acaba de cantar, no cuando toca la siguiente.
    # Asi el hueco lo pone la musica, que es lo que hace el humano.
    for frase in frases:
        if not frase.silabas:
            continue
        if len(frase.silabas) >= 2:
            ultima = frase.silabas[-1][0] - frase.silabas[-2][0]
            dura = min(max(ultima, DURACION_SILABA_P5), 1.2)
        else:
            dura = DURACION_ULTIMA_SILABA_S
        frase.fin_s = frase.silabas[-1][0] + dura

    # Nadie pisa a nadie: se recorta el final contra la frase siguiente.
    for actual, siguiente in zip(frases, frases[1:]):
        tope = siguiente.silabas[0][0] - HUECO_MINIMO_ENTRE_FRASES_S
        if actual.fin_s > tope:
            actual.fin_s = max(actual.silabas[-1][0] + 0.05, tope)
        actual.silabas = [(min(momento, tope - 0.02), texto, enlaza)
                          for momento, texto, enlaza in actual.silabas]

    # Garantia final: las silabas van en orden estricto de principio a fin de la
    # cancion. Los recortes de arriba son por parejas de frases, y al aplastar
    # varias silabas contra el mismo tope dos frases seguidas podian cruzarse.
    # El juego pinta eso como texto que salta hacia atras; `revisar-letra` lo
    # caza como "silabas fuera de orden" y era lo unico que fallaba de 312.
    anterior = -1.0
    for frase in frases:
        arregladas = []
        for momento, texto, enlaza in frase.silabas:
            if momento <= anterior:
                momento = anterior + 0.01
            arregladas.append((momento, texto, enlaza))
            anterior = momento
        frase.silabas = arregladas
        if arregladas:
            frase.fin_s = max(frase.fin_s, arregladas[-1][0] + 0.05)

    # Y nada puede sobrepasar el final de la cancion. Sin esto, la ultima frase
    # se estira SEGUNDOS_POR_FRASE_P95 mas alla y el validador canta "la letra
    # acaba despues que la cancion" -- paso en 4 de 199.
    if duracion:
        limite = duracion - 0.1
        for frase in frases:
            frase.silabas = [(m, x, e) for m, x, e in frase.silabas if m < limite]
            if frase.silabas:
                frase.fin_s = min(frase.fin_s, limite)
    return [f for f in frases if f.silabas]


# ---------------------------------------------------------------------------
# 5. Escribir
# ---------------------------------------------------------------------------


def escribir_en_chart(chart, frases: list[FraseKaraoke]) -> int:
    """Mete la letra en `[Events]`. Devuelve cuantas silabas escribio.

    Formato, que es lo que Clone Hero lee y anima:
        tick = E "phrase_start"
        tick = E "lyric si-"      <- el guion pega esta silaba con la siguiente
        tick = E "phrase_end"
    """
    otros = [(t, e) for t, e in chart.events
             if not (e.startswith("lyric ") or e in ("phrase_start", "phrase_end")
                     or e == MARCA_AUTOCHART)]
    nuevos: list[tuple[int, str]] = [(0, MARCA_AUTOCHART)]
    escritas = 0
    for frase in frases:
        if not frase.silabas:
            continue
        primera = frase.silabas[0][0]
        tick_inicio = chart.seconds_to_tick(max(0.0, primera - AVISO_DE_FRASE_S))
        nuevos.append((tick_inicio, "phrase_start"))
        ultimo_tick = tick_inicio
        for momento, texto, enlaza in frase.silabas:
            tick = max(tick_inicio + 1, chart.seconds_to_tick(momento))
            tick = max(tick, ultimo_tick + 1)      # dos silabas nunca en el mismo tick
            cuerpo = texto + ("-" if enlaza else "")
            nuevos.append((tick, f"lyric {cuerpo}"))
            ultimo_tick = tick
            escritas += 1
        nuevos.append((chart.seconds_to_tick(frase.fin_s), "phrase_end"))
    chart.events = sorted(otros + nuevos, key=lambda item: item[0])
    return escritas


def la_escribio_autochart(carpeta: Path) -> bool:
    """True si la letra que hay en esa carpeta la puso AutoChart.

    Se busca la firma que deja `escribir_en_chart` / `escribir_en_midi`. Si no
    esta, la letra es de una persona y no se pisa sin permiso explicito.
    """
    chart = carpeta / "notes.chart"
    if chart.is_file():
        try:
            crudo = chart.read_bytes().decode("utf-8", errors="replace")
        except OSError:
            return False
        return MARCA_AUTOCHART in crudo
    mid = carpeta / "notes.mid"
    if mid.is_file():
        try:
            import mido

            midi = mido.MidiFile(str(mid), clip=True)
        except Exception:
            return False
        for pista in midi.tracks:
            for mensaje in pista:
                if mensaje.type in ("text", "lyrics") and MARCA_AUTOCHART in mensaje.text:
                    return True
    return False


def quitar_letra(chart) -> None:
    chart.events = [(t, e) for t, e in chart.events
                    if not (e.startswith("lyric ") or e in ("phrase_start", "phrase_end"))]


# ---------------------------------------------------------------------------
# 5b. Escribir en un notes.mid  (pista PART VOCALS)
# ---------------------------------------------------------------------------

# Altura de la nota de voz. No se puntua en Clone Hero, pero tiene que haber
# nota: el texto solo se muestra si hay un note_on en su mismo tick. Se escribe
# en el centro del registro medido en la biblioteca (mediana p50 = 55 grave,
# 69 agudo), o sea nada raro si algun dia alguien mira la pista.
PITCH_VOZ = 62
VOZ_FRASE = 105
VELOCIDAD = 96


class _MapaTempo:
    """Convierte segundos a ticks con el mapa de tempo real del fichero."""

    def __init__(self, tempos: list[tuple[int, float]], resolucion: int):
        self.tempos = sorted(tempos) or [(0, 120.0)]
        self.resolucion = resolucion

    def tick_a_s(self, tick: int) -> float:
        segundos, tick_previo, bpm = 0.0, 0, self.tempos[0][1]
        for en, siguiente in self.tempos:
            if en >= tick:
                break
            segundos += (en - tick_previo) / self.resolucion * (60.0 / bpm)
            tick_previo, bpm = en, siguiente
        return segundos + (tick - tick_previo) / self.resolucion * (60.0 / bpm)

    def s_a_tick(self, segundos: float) -> int:
        transcurrido, tick_previo, bpm = 0.0, 0, self.tempos[0][1]
        for en, siguiente in self.tempos[1:]:
            tramo = (en - tick_previo) / self.resolucion * (60.0 / bpm)
            if transcurrido + tramo >= segundos:
                break
            transcurrido += tramo
            tick_previo, bpm = en, siguiente
        resto = max(0.0, segundos - transcurrido)
        return int(round(tick_previo + resto * bpm / 60.0 * self.resolucion))


def escribir_en_midi(origen: Path, frases: list[FraseKaraoke], destino: Path) -> int:
    """Anade una pista `PART VOCALS` con la letra a una copia del `notes.mid`.

    Se sustituye la pista de voz que hubiera; el resto del fichero no se toca,
    o sea que las notas de guitarra, bajo y bateria salen byte a byte iguales.
    """
    import mido

    midi = mido.MidiFile(str(origen), clip=True)
    resolucion = midi.ticks_per_beat or 480

    tempos: list[tuple[int, float]] = []
    for pista in midi.tracks:
        transcurrido = 0
        for mensaje in pista:
            transcurrido += mensaje.time
            if mensaje.type == "set_tempo":
                tempos.append((transcurrido, mido.tempo2bpm(mensaje.tempo)))
    mapa = _MapaTempo(tempos, resolucion)

    # Fuera la voz vieja Y sus armonias: si se deja un HARM1 con la letra
    # anterior, queda un fichero con dos versiones de la misma cancion y no esta
    # claro cual pinta el juego.
    _VIEJAS = {"PART VOCALS", "HARM1", "HARM2", "HARM3"}
    midi.tracks = [t for t in midi.tracks
                   if not any(m.type == "track_name" and m.name.strip().upper() in _VIEJAS
                              for m in t)]

    # Se construye en tiempo absoluto y se pasa a delta al final: mezclar
    # marcadores de frase, notas y texto a mano es donde se cuelan los fallos.
    absolutos: list[tuple[int, int, object]] = []   # (tick, orden, mensaje)
    escritas = 0
    utiles = [f for f in frases if f.silabas]
    # Los arranques de todas las frases, para que el marcador de una no se
    # trague a la siguiente: el minimo de longitud del marcador puede empujarlo
    # mas alla del arranque de la de al lado, y entonces el juego pinta las dos
    # lineas como una sola larguisima.
    arranques = [mapa.s_a_tick(max(0.0, f.silabas[0][0] - AVISO_DE_FRASE_S))
                 for f in utiles]
    for indice, frase in enumerate(utiles):
        inicio = arranques[indice]
        fin = max(inicio + resolucion // 4, mapa.s_a_tick(frase.fin_s))
        if indice + 1 < len(arranques):
            fin = min(fin, max(inicio + 1, arranques[indice + 1] - 1))
        absolutos.append((inicio, 0, mido.Message("note_on", note=VOZ_FRASE,
                                                  velocity=VELOCIDAD, time=0)))
        absolutos.append((fin, 3, mido.Message("note_off", note=VOZ_FRASE,
                                               velocity=0, time=0)))
        ultimo = inicio
        for indice, (momento, texto, enlaza) in enumerate(frase.silabas):
            tick = max(ultimo + 1, mapa.s_a_tick(momento))
            siguiente = (frase.silabas[indice + 1][0] if indice + 1 < len(frase.silabas)
                         else frase.fin_s)
            largo = max(resolucion // 8, mapa.s_a_tick(siguiente) - tick - 1)
            cuerpo = texto + ("-" if enlaza else "")
            absolutos.append((tick, 1, mido.MetaMessage("lyrics", text=cuerpo, time=0)))
            absolutos.append((tick, 2, mido.Message("note_on", note=PITCH_VOZ,
                                                    velocity=VELOCIDAD, time=0)))
            absolutos.append((tick + largo, 2, mido.Message("note_off", note=PITCH_VOZ,
                                                            velocity=0, time=0)))
            ultimo = tick
            escritas += 1

    pista = mido.MidiTrack()
    pista.append(mido.MetaMessage("track_name", name="PART VOCALS", time=0))
    pista.append(mido.MetaMessage("text", text=f"[{MARCA_AUTOCHART}]", time=0))
    anterior = 0
    for tick, _, mensaje in sorted(absolutos, key=lambda x: (x[0], x[1])):
        mensaje.time = max(0, tick - anterior)
        anterior = tick
        pista.append(mensaje)
    pista.append(mido.MetaMessage("end_of_track", time=0))
    midi.tracks.append(pista)

    destino.parent.mkdir(parents=True, exist_ok=True)
    midi.save(str(destino))
    return escritas


# ---------------------------------------------------------------------------
# 6. Instrumental o cantada
# ---------------------------------------------------------------------------

# Cuantas de las candidatas del mismo artista y duracion tienen que estar
# marcadas como instrumental para creerselo.
MAYORIA_INSTRUMENTAL = 0.7


@dataclass
class Naturaleza:
    """Que es esta cancion: se canta, es instrumental, o no se sabe."""

    instrumental: bool = False
    seguro: bool = False
    motivo: str = ""
    candidatas: int = 0

    @property
    def etiqueta(self) -> str:
        if not self.candidatas:
            return "desconocida"
        return "instrumental" if self.instrumental else "cantada"


def parece_instrumental(candidatas: list[Candidata], artista: str,
                        duracion: float) -> Naturaleza:
    """Decide si la cancion es instrumental, usando lo que sabe LRCLIB.

    **Por que asi y no midiendo el audio:** se midieron cinco rasgos del audio
    (energia en la banda de la voz, planitud, modulacion silabica, contraste
    espectral y centro del estereo) contra 8 instrumentales conocidos y 24
    cantadas. El mejor separaba con d de Cohen 0.74 y etiquetaba mal 7 de las 24
    cantadas: **no sirve para decidir**. Esta escrito en DECISIONES_MEDIDAS.md
    para que nadie lo reintente. La guitarra distorsionada vive en la misma
    banda que la voz, y por ahi no se sale sin separar pistas de verdad.

    La marca de LRCLIB, en cambio, la pone una persona. Medido sobre los mismos
    8: seis salen marcados por unanimidad, y los dos que no es porque LRCLIB no
    tiene la cancion, no porque se equivoque. Por eso "no hay candidatas" es
    **desconocida**, no instrumental: son cosas distintas y confundirlas
    convierte un hueco de la base de datos en una conclusion.
    """
    objetivo = _sin_adornos(artista)
    cercanas = []
    for c in candidatas:
        if duracion and c.duracion and abs(c.duracion - duracion) / duracion > TOLERANCIA_CON_AUDIO:
            continue
        suyo = _sin_adornos(c.artista)
        if objetivo and suyo and not (objetivo in suyo or suyo in objetivo):
            continue  # otra cancion que se llama igual
        cercanas.append(c)

    if not cercanas:
        return Naturaleza(False, False, "LRCLIB no tiene esta cancion", 0)

    marcadas = sum(1 for c in cercanas if c.instrumental)
    con_letra = sum(1 for c in cercanas if c.tiene_tiempos or c.plana)
    parte = marcadas / len(cercanas)
    if parte >= MAYORIA_INSTRUMENTAL and con_letra == 0:
        return Naturaleza(True, True,
                          f"{marcadas} de {len(cercanas)} versiones marcadas instrumental "
                          f"y ninguna con letra", len(cercanas))
    if parte >= MAYORIA_INSTRUMENTAL:
        return Naturaleza(True, False,
                          f"{marcadas} de {len(cercanas)} marcadas instrumental, "
                          f"pero {con_letra} traen letra", len(cercanas))
    return Naturaleza(False, con_letra > 0,
                      f"{con_letra} de {len(cercanas)} versiones traen letra",
                      len(cercanas))
