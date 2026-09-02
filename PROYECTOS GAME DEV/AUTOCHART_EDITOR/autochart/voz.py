"""Leer las pistas de VOZ que ya existen en la biblioteca, y medirlas.

Esto es el equivalente de `corpus.py` pero para la letra. La idea es la misma
del proyecto: **lo que cuenta como buena letra karaoke no se inventa, se mide**.
En la biblioteca hay 80 canciones con voz escrita a mano (62 en `notes.mid` con
`PART VOCALS` y 18 en `notes.chart` con eventos `lyric`), y esas son el criterio.

Los dos formatos guardan lo mismo con nombres distintos.

`notes.mid`, pista `PART VOCALS` (convencion de Rock Band, que Clone Hero lee):

    nota 36..84   una silaba cantada; la altura ES la nota de la melodia
    nota 96       percusion vocal (palmada), sin altura
    nota 105/106  MARCADOR DE FRASE: abarca la linea entera de karaoke
    nota 116      overdrive / Star Power de la frase
    meta `lyrics` el texto de la silaba, en el MISMO tick que su note_on

`notes.chart`, seccion `[Events]` (lo unico que Clone Hero necesita):

    N = E "phrase_start"    empieza la linea
    N = E "lyric si-"       una silaba, en su tick
    N = E "phrase_end"      la borra de pantalla

Marcadores dentro del texto de la silaba, contados en la biblioteca:

    -    la silaba se pega a la siguiente sin espacio  (4199 veces)
    +    no es silaba nueva: la anterior se desliza a otra altura  (2570)
    #    hablada, sin altura que acertar  (1467)
    ^    hablada tolerante  (217)
    =    guion de verdad, se imprime  (63)
    *    variante rara de hablada  (18)

Todo aqui es de solo lectura. La biblioteca no se toca nunca.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import mido

# --- numeros MIDI de la pista de voz ---------------------------------------
VOZ_MIN = 36
VOZ_MAX = 84
VOZ_PERCUSION = 96
VOZ_PERCUSION_MUDA = 97
VOZ_FRASE = 105
VOZ_FRASE_P2 = 106
VOZ_OVERDRIVE = 116

NOMBRES_PISTA_VOZ = ("PART VOCALS", "HARM1")

# Marcadores que NO forman parte de la palabra.
_RE_MARCAS = re.compile(r"[-+#^*$/]")


@dataclass
class Silaba:
    """Una silaba cantada, tal y como esta escrita en el chart."""

    tick: int
    sustain: int = 0
    texto: str = ""           # crudo, con sus marcadores
    pitch: int | None = None  # None = hablada o sin altura
    enlaza: bool = False      # acaba en '-': se pega a la siguiente
    desliza: bool = False     # es un '+': prolonga la silaba anterior
    hablada: bool = False     # '#', '^' o '*'

    @property
    def palabra(self) -> str:
        """El texto limpio, sin marcadores y con el guion de verdad puesto."""
        return _RE_MARCAS.sub("", self.texto).replace("=", "-").strip()


@dataclass
class Frase:
    """Una linea de karaoke: lo que aparece de golpe en pantalla."""

    inicio: int
    fin: int
    silabas: list[Silaba] = field(default_factory=list)
    overdrive: bool = False

    @property
    def texto(self) -> str:
        """Reconstruye la linea uniendo las silabas como hace el juego."""
        salida = ""
        for silaba in self.silabas:
            if silaba.desliza:
                continue
            salida += silaba.palabra
            if not silaba.enlaza:
                salida += " "
        return salida.strip()


@dataclass
class PistaVoz:
    resolucion: int = 480
    tempos: list[tuple[int, float]] = field(default_factory=lambda: [(0, 120.0)])
    frases: list[Frase] = field(default_factory=list)
    fuente: str = ""          # "midi" | "chart"
    cancion: str = ""

    def tick_to_seconds(self, tick: int) -> float:
        tempos = self.tempos or [(0, 120.0)]
        segundos = 0.0
        tick_previo, bpm_previo = 0, tempos[0][1]
        for en, bpm in tempos:
            if en >= tick:
                break
            segundos += (en - tick_previo) / self.resolucion * (60.0 / bpm_previo)
            tick_previo, bpm_previo = en, bpm
        return segundos + (tick - tick_previo) / self.resolucion * (60.0 / bpm_previo)

    @property
    def silabas(self) -> list[Silaba]:
        return [s for f in self.frases for s in f.silabas]


# ---------------------------------------------------------------------------
# Lectura de notes.mid  (PART VOCALS)
# ---------------------------------------------------------------------------


def _abrir_midi(path: str | Path) -> mido.MidiFile:
    """mido decodifica el texto en latin-1 por defecto y los charts en espanol
    vienen en UTF-8. Se prueba UTF-8 y se cae a latin-1, que nunca falla."""
    try:
        return mido.MidiFile(str(path), clip=True, charset="utf-8")
    except Exception:
        return mido.MidiFile(str(path), clip=True, charset="latin-1")


def _nombre_pista(track) -> str:
    for mensaje in track:
        if mensaje.type == "track_name":
            return mensaje.name.strip().upper()
    return ""


def leer_voz_midi(path: str | Path) -> PistaVoz | None:
    """Saca la pista de voz de un `notes.mid`. Devuelve None si no la trae."""
    midi = _abrir_midi(path)
    pista = PistaVoz(resolucion=midi.ticks_per_beat or 480, fuente="midi")

    tempos: list[tuple[int, float]] = []
    for track in midi.tracks:
        transcurrido = 0
        for mensaje in track:
            transcurrido += mensaje.time
            if mensaje.type == "set_tempo":
                tempos.append((transcurrido, mido.tempo2bpm(mensaje.tempo)))
    pista.tempos = sorted(tempos) or [(0, 120.0)]

    # PART VOCALS manda sobre HARM1 SIEMPRE, no la que aparezca antes en el
    # fichero. HARM1 es la armonia, no la linea principal, y en los charts que
    # traen las dos venia antes: el lector se quedaba con la voz de acompanamiento
    # y, peor, al escribir letra nueva seguia leyendo la vieja de HARM1.
    por_nombre = {}
    for track in midi.tracks:
        nombre = _nombre_pista(track)
        if nombre in NOMBRES_PISTA_VOZ and nombre not in por_nombre:
            por_nombre[nombre] = track
    voz = next((por_nombre[n] for n in NOMBRES_PISTA_VOZ if n in por_nombre), None)
    if voz is None:
        return None

    abiertas: dict[int, int] = {}
    notas: list[tuple[int, int, int]] = []      # (tick, pitch, duracion)
    textos: list[tuple[int, str]] = []          # (tick, texto)
    transcurrido = 0
    for mensaje in voz:
        transcurrido += mensaje.time
        if mensaje.type == "note_on" and mensaje.velocity > 0:
            abiertas[mensaje.note] = transcurrido
        elif mensaje.type in ("note_off", "note_on"):
            inicio = abiertas.pop(mensaje.note, None)
            if inicio is not None:
                notas.append((inicio, mensaje.note, transcurrido - inicio))
        elif mensaje.type == "lyrics":
            textos.append((transcurrido, mensaje.text))
        elif mensaje.type == "text" and not mensaje.text.strip().startswith("["):
            # Los rips de Lego Rock Band (27 canciones aqui) escriben la silaba
            # como meta `text` (0x01) en vez de `lyrics` (0x05). Sin esta rama
            # esas canciones salen con las notas de voz y sin una sola palabra.
            # Lo que va entre corchetes son marcas de escenario, no letra.
            textos.append((transcurrido, mensaje.text))

    cantadas = sorted(n for n in notas if VOZ_MIN <= n[1] <= VOZ_MAX or n[1] == VOZ_PERCUSION)
    marcadores = sorted(n for n in notas if n[1] in (VOZ_FRASE, VOZ_FRASE_P2))
    overdrive = sorted(n for n in notas if n[1] == VOZ_OVERDRIVE)

    # Cada texto se pega a la nota que cae en su mismo tick (el 96 % de los
    # casos medidos) o, si no la hay, a la mas cercana dentro de medio tiempo.
    por_tick: dict[int, list[tuple[int, int, int]]] = {}
    for nota in cantadas:
        por_tick.setdefault(nota[0], []).append(nota)

    silabas: list[Silaba] = []
    usados: set[int] = set()
    for tick, texto in textos:
        if not texto.strip():
            continue
        candidata = por_tick.get(tick)
        if candidata:
            _, pitch, duracion = candidata[0]
        else:
            cercanas = [n for n in cantadas if abs(n[0] - tick) <= pista.resolucion // 2]
            if cercanas:
                elegida = min(cercanas, key=lambda n: abs(n[0] - tick))
                _, pitch, duracion = elegida
                tick = elegida[0]
            else:
                pitch, duracion = None, 0
        usados.add(tick)
        silabas.append(_silaba(tick, duracion, texto, pitch))

    # Notas cantadas sin texto (pasa poco): entran igual, con texto vacio.
    for tick, pitch, duracion in cantadas:
        if tick not in usados:
            silabas.append(_silaba(tick, duracion, "", pitch))
    silabas.sort(key=lambda s: s.tick)

    pista.frases = _agrupar_en_frases(silabas, marcadores, overdrive, pista.resolucion)
    pista.cancion = Path(path).parent.name
    return pista if pista.frases else None


def _silaba(tick: int, duracion: int, texto: str, pitch: int | None) -> Silaba:
    limpio = texto.strip()
    hablada = any(marca in limpio for marca in "#^*")
    return Silaba(
        tick=tick,
        sustain=duracion,
        texto=limpio,
        pitch=None if (hablada or pitch == VOZ_PERCUSION) else pitch,
        enlaza=limpio.endswith("-"),
        desliza=limpio == "+",
        hablada=hablada,
    )


def _agrupar_en_frases(
    silabas: list[Silaba],
    marcadores: list[tuple[int, int, int]],
    overdrive: list[tuple[int, int, int]],
    resolucion: int,
) -> list[Frase]:
    """Reparte las silabas en las lineas que marca la pista.

    Si el chart no trae marcadores de frase, se corta por hueco: mas de dos
    tiempos en silencio empieza linea nueva.
    """
    if not silabas:
        return []
    frases: list[Frase] = []
    if marcadores:
        for inicio, _, largo in marcadores:
            fin = inicio + max(largo, 1)
            dentro = [s for s in silabas if inicio <= s.tick < fin]
            if not dentro:
                continue
            frases.append(Frase(
                inicio=inicio,
                fin=fin,
                silabas=dentro,
                overdrive=any(inicio <= o[0] < fin for o in overdrive),
            ))
        colocadas = {id(s) for f in frases for s in f.silabas}
        sueltas = [s for s in silabas if id(s) not in colocadas]
        if sueltas:
            frases.extend(_cortar_por_hueco(sueltas, resolucion))
        frases.sort(key=lambda f: f.inicio)
        return frases
    return _cortar_por_hueco(silabas, resolucion)


HUECO_DE_FRASE_TIEMPOS = 2.0


def _cortar_por_hueco(silabas: list[Silaba], resolucion: int) -> list[Frase]:
    corte = HUECO_DE_FRASE_TIEMPOS * resolucion
    grupos: list[list[Silaba]] = [[]]
    anterior: Silaba | None = None
    for actual in silabas:
        if anterior is not None and actual.tick - (anterior.tick + anterior.sustain) > corte:
            grupos.append([])
        grupos[-1].append(actual)
        anterior = actual
    salida = []
    for grupo in grupos:
        if not grupo:
            continue
        salida.append(Frase(
            inicio=grupo[0].tick,
            fin=grupo[-1].tick + max(grupo[-1].sustain, resolucion // 4),
            silabas=grupo,
        ))
    return salida


# ---------------------------------------------------------------------------
# Lectura de notes.chart  ([Events])
# ---------------------------------------------------------------------------


def leer_voz_chart(path: str | Path) -> PistaVoz | None:
    """Saca la letra de la seccion `[Events]` de un `.chart`."""
    from . import chartio

    chart = chartio.parse_chart(path)
    pista = PistaVoz(
        resolucion=chart.resolution,
        tempos=[(t.tick, t.bpm) for t in chart.tempos] or [(0, 120.0)],
        fuente="chart",
        cancion=Path(path).parent.name,
    )

    frases: list[Frase] = []
    abierta: Frase | None = None
    for tick, texto in sorted(chart.events, key=lambda e: e[0]):
        cuerpo = texto.strip()
        if cuerpo == "phrase_start":
            if abierta is not None and abierta.silabas:
                abierta.fin = max(abierta.fin, tick)
                frases.append(abierta)
            abierta = Frase(inicio=tick, fin=tick)
        elif cuerpo == "phrase_end":
            if abierta is not None:
                abierta.fin = tick
                if abierta.silabas:
                    frases.append(abierta)
                abierta = None
        elif cuerpo.startswith("lyric "):
            crudo = cuerpo[6:]
            if abierta is None:
                abierta = Frase(inicio=tick, fin=tick)
            abierta.silabas.append(_silaba(tick, 0, crudo, None))
            abierta.fin = max(abierta.fin, tick)
    if abierta is not None and abierta.silabas:
        frases.append(abierta)

    # El sustain no existe en `.chart`: se estima hasta la silaba siguiente.
    todas = [s for f in frases for s in f.silabas]
    for actual, siguiente in zip(todas, todas[1:]):
        actual.sustain = max(0, min(siguiente.tick - actual.tick, chart.resolution * 2))

    pista.frases = frases
    return pista if frases else None


def leer_voz(carpeta: str | Path) -> PistaVoz | None:
    """Lee la voz de una carpeta de cancion, venga en `.mid` o en `.chart`."""
    carpeta = Path(carpeta)
    mid = carpeta / "notes.mid"
    cht = carpeta / "notes.chart"
    if mid.is_file():
        try:
            pista = leer_voz_midi(mid)
            if pista:
                return pista
        except Exception:
            pass
    if cht.is_file():
        try:
            return leer_voz_chart(cht)
        except Exception:
            return None
    return None


# ---------------------------------------------------------------------------
# Medida
# ---------------------------------------------------------------------------


@dataclass
class EstadisticasVoz:
    cancion: str = ""
    origen: str = ""      # la carpeta numerada de la biblioteca
    genero: str = ""
    fuente: str = ""
    frases: int = 0
    silabas: int = 0
    duracion_s: float = 0.0
    silabas_por_frase: list[int] = field(default_factory=list)
    segundos_por_frase: list[float] = field(default_factory=list)
    hueco_entre_frases: list[float] = field(default_factory=list)
    aviso_de_frase: list[float] = field(default_factory=list)   # cuanto antes aparece la linea
    duracion_silaba: list[float] = field(default_factory=list)
    silabas_por_segundo: list[float] = field(default_factory=list)
    ratio_sin_texto: float = 0.0   # notas de voz que no llevan silaba escrita
    ratio_enlaza: float = 0.0
    ratio_desliza: float = 0.0
    ratio_hablada: float = 0.0
    ratio_overdrive: float = 0.0
    pitch_min: int = 0
    pitch_max: int = 0
    pitch_mediana: float = 0.0
    saltos_semitono: dict[int, int] = field(default_factory=dict)
    rejilla: dict[int, int] = field(default_factory=dict)
    palabras_por_frase: list[int] = field(default_factory=list)
    caracteres_por_frase: list[int] = field(default_factory=list)


DIVISIONES = (1, 2, 3, 4, 6, 8, 12, 16)


def _division(tick: int, resolucion: int) -> int:
    for division in DIVISIONES:
        paso = resolucion / division
        offset = tick % paso
        if min(offset, paso - offset) <= max(1.0, resolucion * 0.02):
            return division
    return 0


def medir(pista: PistaVoz) -> EstadisticasVoz:
    est = EstadisticasVoz(cancion=pista.cancion, fuente=pista.fuente)
    silabas = pista.silabas
    if not silabas:
        return est

    est.frases = len(pista.frases)
    est.silabas = len(silabas)
    primera = pista.tick_to_seconds(silabas[0].tick)
    ultima = pista.tick_to_seconds(silabas[-1].tick)
    est.duracion_s = max(1e-6, ultima - primera)

    fin_anterior = None
    for frase in pista.frases:
        cuenta = len(frase.silabas)
        if not cuenta:
            continue
        est.silabas_por_frase.append(cuenta)
        ini_s = pista.tick_to_seconds(frase.silabas[0].tick)
        fin_s = pista.tick_to_seconds(max(frase.fin, frase.silabas[-1].tick))
        largo = max(1e-3, fin_s - ini_s)
        est.segundos_por_frase.append(round(largo, 3))
        est.silabas_por_segundo.append(round(cuenta / largo, 3))
        est.aviso_de_frase.append(round(ini_s - pista.tick_to_seconds(frase.inicio), 3))
        if fin_anterior is not None:
            est.hueco_entre_frases.append(round(max(0.0, ini_s - fin_anterior), 3))
        fin_anterior = fin_s
        texto = frase.texto
        est.palabras_por_frase.append(len(texto.split()))
        est.caracteres_por_frase.append(len(texto))

    est.ratio_sin_texto = sum(1 for s in silabas if not s.palabra) / len(silabas)
    est.ratio_enlaza = sum(1 for s in silabas if s.enlaza) / len(silabas)
    est.ratio_desliza = sum(1 for s in silabas if s.desliza) / len(silabas)
    est.ratio_hablada = sum(1 for s in silabas if s.hablada) / len(silabas)
    est.ratio_overdrive = (
        sum(1 for f in pista.frases if f.overdrive) / max(1, len(pista.frases))
    )

    for anterior, actual in zip(silabas, silabas[1:]):
        hueco = pista.tick_to_seconds(actual.tick) - pista.tick_to_seconds(anterior.tick)
        if 0 < hueco < 4:
            est.duracion_silaba.append(round(hueco, 3))
    rejilla: Counter[int] = Counter()
    for silaba in silabas:
        rejilla[_division(silaba.tick, pista.resolucion)] += 1
    est.rejilla = dict(rejilla)

    alturas = [s.pitch for s in silabas if s.pitch]
    if alturas:
        est.pitch_min = min(alturas)
        est.pitch_max = max(alturas)
        ordenadas = sorted(alturas)
        est.pitch_mediana = ordenadas[len(ordenadas) // 2]
        saltos: Counter[int] = Counter()
        for a, b in zip(alturas, alturas[1:]):
            salto = b - a
            if abs(salto) <= 24:
                saltos[salto] += 1
        est.saltos_semitono = dict(saltos)
    return est


def escanear_biblioteca(songs_dir: str | Path, al_progresar=None) -> list[EstadisticasVoz]:
    """Recorre la biblioteca y mide toda la voz escrita a mano que encuentre."""
    from .export import read_song_ini

    raiz = Path(songs_dir)
    salida: list[EstadisticasVoz] = []
    carpetas = sorted({p.parent for patron in ("**/notes.mid", "**/notes.chart")
                       for p in raiz.glob(patron)})
    for carpeta in carpetas:
        try:
            pista = leer_voz(carpeta)
        except Exception:
            pista = None
        if pista is None or len(pista.silabas) < 20:
            continue
        est = medir(pista)
        try:
            rel = carpeta.relative_to(raiz).parts
            est.origen = rel[0] if rel else ""
        except ValueError:
            est.origen = ""
        try:
            info = read_song_ini(carpeta)
            est.genero = info.get("genre", "")
        except Exception:
            est.genero = ""
        salida.append(est)
        if al_progresar is not None:
            al_progresar(len(salida), est)
    return salida


def _percentiles(valores: list[float], puntos=(5, 25, 50, 75, 95)) -> dict[str, float]:
    if not valores:
        return {f"p{p}": 0.0 for p in puntos}
    ordenados = sorted(valores)
    fuera = {}
    for punto in puntos:
        indice = min(len(ordenados) - 1, max(0, int(round((punto / 100.0) * (len(ordenados) - 1)))))
        fuera[f"p{punto}"] = round(float(ordenados[indice]), 4)
    return fuera


def _mezclar(dicts: list[dict]) -> dict[str, float]:
    total: Counter[str] = Counter()
    for item in dicts:
        for clave, cuenta in item.items():
            total[str(clave)] += cuenta
    grande = sum(total.values()) or 1
    return {clave: round(cuenta / grande, 5) for clave, cuenta in total.most_common()}


def agregar(estadisticas: list[EstadisticasVoz]) -> dict:
    """El perfil de voz que leera el generador de karaoke."""
    usables = [e for e in estadisticas if e.silabas >= 40]
    perfil: dict = {
        "canciones_con_voz": len(usables),
        "canciones_leidas": len(estadisticas),
        "silabas_totales": sum(e.silabas for e in usables),
        "silabas_por_frase": _percentiles([v for e in usables for v in e.silabas_por_frase]),
        "segundos_por_frase": _percentiles([v for e in usables for v in e.segundos_por_frase]),
        "hueco_entre_frases": _percentiles([v for e in usables for v in e.hueco_entre_frases]),
        "aviso_de_frase": _percentiles([v for e in usables for v in e.aviso_de_frase]),
        "duracion_silaba": _percentiles([v for e in usables for v in e.duracion_silaba]),
        "silabas_por_segundo": _percentiles([v for e in usables for v in e.silabas_por_segundo]),
        "palabras_por_frase": _percentiles([v for e in usables for v in e.palabras_por_frase]),
        "caracteres_por_frase": _percentiles([v for e in usables for v in e.caracteres_por_frase]),
        "ratio_sin_texto": _percentiles([e.ratio_sin_texto for e in usables]),
        "ratio_enlaza": _percentiles([e.ratio_enlaza for e in usables]),
        "ratio_desliza": _percentiles([e.ratio_desliza for e in usables]),
        "ratio_hablada": _percentiles([e.ratio_hablada for e in usables]),
        "ratio_overdrive": _percentiles([e.ratio_overdrive for e in usables]),
        "pitch_mediana": _percentiles([e.pitch_mediana for e in usables if e.pitch_mediana]),
        "pitch_min": _percentiles([e.pitch_min for e in usables if e.pitch_min]),
        "pitch_max": _percentiles([e.pitch_max for e in usables if e.pitch_max]),
        "saltos_semitono": _mezclar([e.saltos_semitono for e in usables]),
        "rejilla": _mezclar([e.rejilla for e in usables]),
        "por_origen": {},
    }
    for origen in sorted({e.origen for e in usables if e.origen}):
        grupo = [e for e in usables if e.origen == origen]
        if len(grupo) < 2:
            continue
        perfil["por_origen"][origen] = {
            "canciones": len(grupo),
            "silabas_por_frase": _percentiles([v for e in grupo for v in e.silabas_por_frase]),
            "silabas_por_segundo": _percentiles([v for e in grupo for v in e.silabas_por_segundo]),
            "ratio_enlaza": _percentiles([e.ratio_enlaza for e in grupo]),
        }
    return perfil


def guardar_perfil(perfil: dict, path: str | Path) -> Path:
    destino = Path(path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(perfil, indent=2, ensure_ascii=False), encoding="utf-8")
    return destino


def cargar_perfil(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
