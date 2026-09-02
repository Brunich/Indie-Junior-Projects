"""Turn an audio analysis into a playable five-fret chart.

The pipeline, in order:

1. **Quantise** every detected onset onto the beat grid. Anything that will not
   sit on a subdivision the difficulty allows is dropped rather than nudged --
   a note in the wrong place is worse than a missing note.
2. **Thin** the survivors down to a density the corpus says is normal for this
   tempo, keeping the loudest attacks in each window and enforcing a minimum
   gap so nothing becomes unplayable.
3. **Assign frets** from the pitch contour: the riff going up moves the hand
   right, going down moves it left, a repeated note stays put. Where the audio
   has no usable pitch (drums, wall-of-noise), fall back to motifs sampled from
   the trigram table mined off real charts.
4. **Repeat what repeats.** A bar whose rhythm and contour match an earlier bar
   in the same section reuses that bar's frets, which is what makes a chart feel
   written instead of sprinkled.
5. **Decorate**: chords on accents, sustains on gaps, star power on phrases.
6. **Reduce** to Hard / Medium / Easy from the Expert pass.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field

import numpy as np

from . import chartio
from .audio import AudioAnalysis, Onset
from .chartio import Chart, Note, SpecialPhrase, TimeSignature, Track, hopo_ratio
from .timing import TempoMap, build_tempo_map

RESOLUTION = 192


@dataclass
class DifficultySpec:
    """The playing envelope for one difficulty."""

    name: str
    divisions: tuple[int, ...]  # allowed subdivisions of a beat
    min_gap_beats: float
    lanes: int
    max_jump: int
    chord_ratio: float
    max_chord_size: int
    sustain_ratio: float
    density_scale: float  # fraction of the Expert note budget
    # Multipliers applied to the mined corpus medians when a profile exists.
    chord_scale: float = 1.0
    sustain_scale: float = 1.0
    # Cuanto sigue el presupuesto de notas a la energia de la cancion, en ESTA
    # dificultad. Ver CONTRASTE_ALFA.
    contraste_alfa: float = 0.75


# Las tres ultimas columnas de cada fila (densidad, acordes, sostenidos) NO
# estan puestas a ojo: son la mediana de cada dificultad contra SU PROPIO
# Experto en 250 charts humanos emparejados de la biblioteca. Lo que estaba
# antes escrito a mano dejaba las dificultades bajas casi vacias -- Facil a un
# 24 % de Experto cuando el humano la charterea al 46 % -- y le metia acordes a
# Facil, donde un humano practicamente no pone ninguno (0.3 % de las notas).
DIFFICULTY_SPECS: dict[str, DifficultySpec] = {
    "Expert": DifficultySpec("Expert", (1, 2, 3, 4), 0.235, 5, 4, 0.344, 3, 0.120, 1.000, 1.000, 1.000, 0.95),
    "Hard": DifficultySpec("Hard", (1, 2, 3), 0.32, 5, 3, 0.274, 2, 0.139, 0.865, 0.999, 1.133, 1.05),
    "Medium": DifficultySpec("Medium", (1, 2), 0.49, 4, 2, 0.160, 2, 0.186, 0.641, 0.716, 1.499, 1.25),
    "Easy": DifficultySpec("Easy", (1,), 0.98, 3, 1, 0.003, 2, 0.234, 0.457, 0.013, 2.051, 1.45),
}

# Two-fret shapes, ordered by how often they turn up in real charts.
CHORD_SHAPES = ((0, 1), (1, 2), (2, 3), (3, 4), (0, 2), (1, 3), (2, 4), (0, 4))


def _shift_chord_shape(shape: tuple[int, ...], lane: int, lanes: int) -> tuple[int, ...] | None:
    """Mover la misma postura para que caiga sobre `lane`, si cabe en el mastil."""
    offsets = tuple(fret - min(shape) for fret in shape)
    for offset in offsets:
        shifted = tuple(lane - offset + value for value in offsets)
        if all(0 <= fret < lanes for fret in shifted):
            return shifted
    return None

QUANTISE_TOLERANCE_BEATS = 0.115
# A sustain is worth holding when the guitar actually rings out, which is a
# length in *seconds* -- the detected beat can land an octave off the tempo a
# charter would have written, so a threshold in beats is not the same thing.
SUSTAIN_MIN_GAP_S = 0.45
# ...pero el hueco tambien vale si es lo bastante grande EN TIEMPOS. Manda el
# menor de los dos, para que una cancion rapida no se quede sin un solo
# sostenido solo por ir rapida.
SUSTAIN_MIN_GAP_BEATS = 0.5
SUSTAIN_MIN_LENGTH_BEATS = chartio.SOSTENIDO_MIN_TIEMPOS
SUSTAIN_TAIL_BEATS = 0.22
# p95 de los 118.927 sostenidos humanos medidos en la biblioteca. La mediana es
# 0.75 tiempos y practicamente no cambia entre dificultades: un sostenido no es
# "lo que queda hasta la nota siguiente", es lo que la cuerda aguanta sonando.
SUSTAIN_MAX_BEATS = 3.75
# DESCARTADO CON NUMERO (23-08-2026): exigir ademas que el sonido de la nota
# cubriera el hueco entero (`ring_beats >= hueco * X`) para que ese hueco
# contara como sostenido. Barrido sobre 12 canciones con guitarra aislada, el
# ratio medio se movia de 0.103 (sin la regla) a 0.098 (con ella al 100 %) y el
# error contra el humano se quedaba igual en 0.208. El ring ya manda por donde
# tiene que mandar: recortando el LARGO del sostenido.
# Cuanto tiene que moverse el tono para sacar la mano de un traste repetido.
REPEAT_BREAK_SEMITONES = 3.0

# --- Memoria del gesto ------------------------------------------------------
# Un salto ancho es, para el atlas, tres carriles o mas entre dos notas que no
# esten separadas por mas de un tiempo (`atlas.py`, seccion "saltos anchos").
# Aqui se usan las MISMAS dos cifras a proposito: lo que el generador produce y
# lo que la medida cuenta tienen que ser la misma cosa.
SALTO_ANCHO_CARRILES = 3
SALTO_RACHA_HUECO = 1.0
# Cuantos saltos seguidos como mucho. Medido en 391 charts humanos, un salto
# ancho va seguido de otro el 68 % de las veces (`tools/transiciones.py`), que
# es una racha media de 1/(1-0.68) = 3.1 saltos. Cortar en 4 deja que la figura
# se agote sin convertir la autopista en un zigzag perpetuo.
SALTO_RACHA_MAXIMA = 4

# El juego no puede ensenar una nota que ya esta encima de la linea al arrancar.
# En la biblioteca, el 95 % de los charts humanos no pone la primera nota antes
# del segundo 2.0 (mediana 3.7); por debajo de un segundo es directamente
# infumable, asi que ahi esta el corte.
LEAD_IN_MIN_S = 1.0
# Y al otro extremo: si una nota (o su sostenido) sobrevive al final del audio,
# la cancion termina con la nota todavia pulsada y se pierde.
END_MARGIN_S = 0.25

# Star Power medido en la biblioteca: mediana de 10 frases por pista, en TODAS
# las dificultades, y 6.97 tiempos de largo.
SP_PHRASE_BEATS = 7.0
SP_TARGET_PHRASES = 10

# Cuanto pesa "aqui esta sonando la solista" al elegir que ataques sobreviven al
# filtro de densidad. Comparable al peso del tiempo fuerte (0.35): manda, pero no
# tanto como para dejar fuera un acento claro donde la solista calla.
LEAD_PRIORITY = 0.40

# Cuanto sigue el presupuesto de notas a la energia de la cancion.
#   0.0 = plano, el mismo numero de notas por ventana pase lo que pase
#   1.0 = proporcional del todo a los ataques que hay en esa ventana
# Medido: con 0.0 (lo que habia) el contraste pico/valle del chart generado sale
# en 1.1-1.2 en LAS CUATRO dificultades, contra 2.05 (Facil) a 2.85 (Experto)
# de 284 charts humanos con las cuatro. Un chart plano no es mas facil: es que
# no pasa nada en el, y por eso Medio y Dificil se sentian Experto descafeinado.
# El total de notas NO cambia: el reparto se renormaliza despues.
#
# Cada dificultad lleva el suyo en `DIFFICULTY_SPECS` y **las faciles llevan MAS
# que las dificiles**, que es lo contrario de lo que hace el humano (su contraste
# va de 2.05 en Facil a 2.85 en Experto). Es una decision de Bruno y esta bien
# razonada: en Experto ya pasan cosas todo el rato, y lo que aburre es un Facil
# que va al mismo trote de principio a fin. Subiendo el alfa en Facil y Medio, en
# los tramos flojos casi no hay notas y el estribillo se nota de verdad.
# Este es el unico sitio del proyecto donde se apunta a proposito FUERA de la
# mediana humana, y por eso queda escrito aqui.
#
# Y se PROBO subirlo tambien en Dificil y Experto (1.40 / 1.35). Funciona para
# lo que se pedia -- el contraste sube a 2.50 y 2.60, clavando el 2.52 humano de
# Dificil -- pero cuesta: el banco baja de f1 0.670 a 0.656 y el recall de 0.689
# a 0.647, porque los valles mas hondos se dejan notas que el humano si escribio.
# Se queda en 1.05 / 0.95 por dos razones: el numero lo dice, y Bruno pidio los
# momentos SOLO para las faciles. Si algun dia se quiere el Experto mas
# accidentado, esos son los valores y ese es el precio.
CONTRASTE_ALFA = 0.75
# Ninguna ventana puede quedarse por debajo de esto respecto a su parte plana,
# o aparecen agujeros de varios compases sin una nota.
# DESCARTADO CON NUMERO (24-08-2026) bajar este suelo para dejar agujeros: con
# 0.20 los huecos de 2.22 tiempos pasan de 0.18 % a 0.19 % y con 0.10 a 0.24 %
# (el humano tiene 1.45 %), o sea que no es por aqui, y "todas iguales" se va de
# 6.9 a 8.2 y 8.1 porque todas las canciones adoptan la misma forma.
CONTRASTE_SUELO = 0.35
# Cuanto premia `thin` que un ataque caiga en el tiempo o en el medio tiempo.
# Es lo que hace que los supervivientes queden repartidos parejo: si la rejilla
# manda, las notas que sobreviven son las metricamente regulares.
#
# DESCARTADO CON NUMERO (24-08-2026) bajarla para que aparezcan agujeros. Los
# hace -- huecos de 2.22 tiempos 0.18 % -> 0.28 % con 0.12/0.04 y -> 0.79 % con
# 0.0/0.0 -- y el F1 del panel sube mucho (0.505 -> 0.536 y 0.533), pero la
# distancia de gestos empeora (0.401 y 0.411) y "todas iguales" se va a 7.2 y
# 8.8. La rejilla no sobra: es la que hace que el chart caiga donde se toca.
REJILLA_TIEMPO = 0.35
REJILLA_MEDIO = 0.12
# EL PREMIO A LA CADENA. Cuando `thin` elige un ataque, sus vecinos a distancia
# de LIGADURA suben de puntuacion, para que las notas rapidas salgan en TIRADA y
# no sueltas. Medido el 24-08-2026: el humano encadena 3.04 notas de hueco corto
# (mediana de 164 charts) y nosotros 1.94, y de ahi salen las rachas de ligadura
# -- 3.16 suyas contra 1.66 nuestras -- porque una ligadura natural necesita
# hueco corto. El 74.9 % de nuestras rachas se rompen por hueco largo (el humano,
# 59.1 %).
#
# Dos cosas que NO son esto y ya estan medidas:
#   - `RACHA_VENTANA` suaviza la puntuacion y AGRUPA: mueve el histograma de
#     huecos (semicorcheas 21.6 % -> 31.5 %) y NO alarga la cadena (1.94 -> 2.02).
#   - un escalon de rejilla para la semicorchea (`REJILLA_CUARTO = 0.06`): con la
#     jerarquia que hay (tiempo 0.35, medio 0.06) es ruido y no movio nada
#     (Pride & Joy, cadena 1.48 -> 1.45).
# La distancia es la del juego y vive en `chartio`, no se copia aqui.
# MEDIDO Y NO ADOPTADO (24-08-2026). Mueve la palanca que se queria mover y
# cuesta lo que no se puede pagar. Panel de 10, mismas semillas:
#
#                        hoy (0)   premio 0.10   humano
#   cadena de ritmo         1.94       2.18        3.04
#   racha de ligadura       1.60       1.66        1.78 (los diez del panel)
#   ligadura                0.186      0.212       0.114
#   error de ligadas        0.105      0.124
#   F1                      0.505      0.528
#   distancia de gestos     0.384      0.412
#   mejoran                              4 de 10
#
# Sube el F1 y empeora la distancia de gestos: la misma firma que quitar el
# premio a la rejilla. Y en el panel las dos mitades del objetivo escrito tiran
# en direcciones contrarias -- alargar la cadena SUBE la ligadura (0.186 ->
# 0.212) y el humano de estas diez esta en 0.114, asi que el error empeora por
# acercarse a la cadena. En Pride & Joy si gana entero (distancia 0.066 -> 0.061
# y ligadura 0.217 -> 0.264 contra su 0.390), y una cancion no decide nada.
#
# Se enciende cambiando este numero.
CADENA_PREMIO = 0.0
# Un charter no elige notas sueltas: elige FRASES. Suavizar la puntuacion de
# `thin` sobre las notas vecinas antes de cortar hace que una racha entre o
# salga junta, y con eso el chart deja agujeros de verdad -- que es lo que le
# falta: huecos de 2.22 tiempos o mas, humano 1.45 % contra 0.18 % nuestro.
#
# MEDIDO Y NO ADOPTADO (24-08-2026). Funciona exactamente como se esperaba y
# aun asi no pasa la puerta, panel de 10 canciones:
#
#                            hoy(1)    racha 2   racha 3   racha 5
#   huecos >= 2.22t          0.18 %    0.77 %    1.45 %    2.08 %   (humano 1.45)
#   sostenidos >= 2t         0.17 %    0.54 %    0.84 %    1.19 %   (humano 1.13)
#   panel, distancia          0.384     0.396     0.397     0.418
#   panel, F1                 0.505     0.543     0.523     0.508
#   "todas iguales"            6.9       7.0       7.1       9.6
#   error de ligadas          0.115     0.132     0.150     0.137
#
# Con 3 el agujero sale CLAVADO al humano y el F1 sube, pero la distancia de
# gestos empeora en las dos y las ligadas se estropean. Se deja en 1 (apagado)
# y se enciende cambiando este numero el dia que las ligadas no dependan de que
# las notas vayan seguidas.
RACHA_VENTANA = 1
CONTRASTE_TECHO = 2.4

# --- la voz como ancla (PLAN_MELODIA F1) -----------------------------------
# Una silaba cantada es un sitio donde el humano pone nota 6 de cada 10 veces
# (medido en 126 canciones con chart y voz humanos). Nosotros ibamos por 4 de
# cada 10, y eso es lo que se siente como "la letra esta en otra parte".
SILABA_TOLERANCIA_S = 0.06   # +-60 ms: lo mismo que usa la medida
SILABA_PRIORIDAD = 1.60      # cuanto sube en la cola de `thin`
# Fuerza que se le da a una silaba que el detector de ataques NO vio. Va por
# encima de la mediana para que sobreviva al filtro, pero no tanto como para
# tapar un ataque real fuerte.
SILABA_FUERZA_INVENTADA = 0.55
# Cuanto silencio separa dos frases cantadas. Por debajo de esto se considera la
# misma tirada de voz y no se mete instrumento en medio.
VOZ_HUECO_DE_FRASE_S = 1.2
# Margen alrededor de la voz donde el instrumento no entra, para que no suene a
# dos cosas a la vez.
VOZ_MARGEN_S = 0.18
# En un tramo cantado se permite algun ataque de instrumento MUY fuerte, para
# que un acento de bateria o un acorde no desaparezca. Es una fraccion de las
# silabas de ese tramo.
VOZ_RELLENO_MAXIMO = 0.15
# Cuanta fuerza de instrumento tiene que haber en una frase para que merezca la
# pena cedersela, en relacion con la fuerza media de la cancion. Por debajo, el
# instrumento no esta diciendo nada y la frase se queda con la voz.
INSTRUMENTO_MANDA = 1.15
# Y ademas, un suelo absoluto: menos de esto por segundo no es un instrumento
# tocando, es relleno.
INSTRUMENTO_MINIMO_POR_S = 2.2
# Ninguna parte de la cancion se queda muda tanto tiempo mientras hay musica.
# El humano tiene respiros, pero de 4 tiempos, no de cuatro segundos con la voz
# cantando encima.
HUECO_MUDO_MAXIMO_S = 1.6
# Nunca dos frases seguidas del instrumento: lo que se busca es turnarse.
FRASES_SEGUIDAS_INSTRUMENTO = 1

# NO existe un MAPA_VOZ aqui, y es una decision medida. Ver
# docs/DECISIONES_MEDIDAS.md seccion 11: usar la letra alineada para decidir
# donde cargar la mano empeora la forma del chart en las DOS direcciones
# (0.25 -> 0.18 cargando donde no se canta, 0.25 -> -0.05 cargando donde se
# canta). La correlacion con la curva humana no mejora: empeora.

# Acumulados que reparten los intervalos de la cancion en pasos de carril
# (0, ±1, ±2, ±3). El corpus dice 31/47/14/6, pero assign_frets retoca despues
# --motivos, limite de salto, anti-repeticion-- asi que los cortes que dejan la
# distribucion FINAL mas cerca de la humana no son los del corpus tal cual.
# Calibrado sobre dos canciones (electronica y metal): 38/85/95.
CONTOUR_CUTS = (38.0, 85.0, 95.0)

# Sobre cuantas notas se promedia la puntuacion de acorde antes de decidir. Es lo
# que hace que los acordes salgan en TRAMOS en vez de salpicados: un guitarrista
# acompana un rato y luego hace una linea. Medido en 120 charts humanos, las
# rachas son de 4.76 acordes y 10.51 sueltas.
CHORD_RUN_WINDOW = 8
# Con que probabilidad se mantiene la postura del acorde anterior, y con cual se
# desplaza cuando el carril nuevo no cabe en ella. El humano encadena la misma
# forma exacta el 61.8 % de las veces, la misma desplazada el 13.3 %, y cambia
# de postura el 24.9 % restante.
# Calibrado sobre dos canciones: sale 58.3/16.6/25.2 y 59.8/12.9/27.3.
CHORD_SHAPE_KEEP = 1.0
CHORD_SHAPE_SHIFT = 0.08

# Cuando el juego liga una nota solo esta en `chartio.is_natural_hopo`: es la
# regla del juego, no una decision de este generador, y la herramienta de medida
# tiene que usar exactamente la misma o los numeros no comparan nada.
#
# Hasta donde estira un humano una ligadura ESCRITA. Medido sobre las 6.668
# marcas de ligar de 254 charts: el hueco es 0.50 tiempos en el p25, el p50 y el
# p75 -- la corchea recta, que es justo lo que el juego no liga solo. No es un
# umbral elegido, es una sola cosa repetida 6.668 veces.
FORCE_LINK_MAX_BEATS = 0.53
# Con que frecuencia marca un humano cada caso ELEGIBLE (no cuantas marcas pone:
# de cada cien sitios donde PODRIA marcar, en cuantos marca). Medido en los
# mismos 254 charts, sobre ExpertSingle.
#
# Cortar una ligadura -- obligar a rasguear -- es cuatro veces mas frecuente en
# la PRIMERA nota de una racha ligada que en una de en medio: el guitarrista
# ataca la frase y a partir de ahi ya liga.
FORCE_CUT_RUN_START = 0.214
FORCE_CUT_IN_RUN = 0.055
# Y al ligar manda cuanto se mueve la mano, que es la definicion fisica de un
# martilleo: no vuelves a picar la cuerda porque el dedo solo se mueve un
# traste. Un carril 11.9 %, dos 5.3 %, tres o mas 2.8 %.
FORCE_LINK_STEP1 = 0.119
FORCE_LINK_STEP2 = 0.053
FORCE_LINK_FAR = 0.028
FORCE_LINK_AFTER_CHORD = 0.042


@dataclass
class Candidate:
    """An onset that survived quantisation."""

    beat: float  # snapped position, in beats on the grid
    tick: int
    strength: float
    midi: float
    low: float
    mid: float
    high: float
    time: float
    section: int = 0
    division: int = 1
    ring: float = 0.0  # segundos que sigue sonando el ataque
    lead: float = 0.0  # 0..1: cuanto manda la banda melodica sobre la grave
    silaba: bool = False  # cae sobre una silaba cantada de la letra alineada


@dataclass
class GenerationReport:
    """What the generator actually did -- printed by the CLI, saved next to the chart."""

    tempo: float = 0.0
    duration: float = 0.0
    onsets_detected: int = 0
    onsets_quantised: int = 0
    sections: int = 0
    tempo_events: int = 0
    per_difficulty: dict[str, dict] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Step 1 -- quantise
# ---------------------------------------------------------------------------


def quantise(
    onsets: list[Onset],
    tempo_map: TempoMap,
    divisions: tuple[int, ...] = (1, 2, 3, 4),
    tolerance: float = QUANTISE_TOLERANCE_BEATS,
) -> list[Candidate]:
    """Snap onsets to the grid, dropping anything that lands too far off it."""
    out: list[Candidate] = []
    for onset in onsets:
        beat = tempo_map.time_to_beat(onset.time)
        best: tuple[float, float, int] | None = None  # (cost, snapped, division)
        for division in divisions:
            snapped = round(beat * division) / division
            error = abs(beat - snapped)
            # Coarser grids win ties: an eighth note beats a triplet that is
            # only marginally closer.
            cost = error + 0.004 * division
            if best is None or cost < best[0]:
                best = (cost, snapped, division)
        if best is None:
            continue
        _, snapped, division = best
        if abs(beat - snapped) > tolerance or snapped < 0:
            continue
        out.append(
            Candidate(
                beat=snapped,
                tick=tempo_map.beat_to_tick(snapped),
                strength=onset.strength,
                midi=onset.midi,
                low=onset.low,
                mid=onset.mid,
                high=onset.high,
                time=onset.time,
                division=division,
                ring=onset.ring,
                lead=onset.lead,
            )
        )

    # Collapse onsets that snapped onto the same slot, keeping the loudest.
    merged: dict[int, Candidate] = {}
    for candidate in out:
        existing = merged.get(candidate.tick)
        if existing is None or candidate.strength > existing.strength:
            merged[candidate.tick] = candidate
    return [merged[tick] for tick in sorted(merged)]


# ---------------------------------------------------------------------------
# Step 2 -- density
# ---------------------------------------------------------------------------


def target_notes_per_second(
    profile: dict | None,
    bpm: float,
    spec: DifficultySpec,
    multiplier: float = 1.0,
    percentile: str = "p50",
) -> float:
    """How dense this chart should be, taken from the mined corpus when present.

    `percentile` picks which point of the human distribution to aim at, and
    `multiplier` scales it afterwards. Both exist because the median of 882
    charts is not the same thing as the median of the songs somebody actually
    wants charted -- old, slow and easy charts drag the corpus median down.
    """
    fallback = min(6.5, max(1.6, bpm / 60.0 * 1.15))
    if not profile:
        return fallback * spec.density_scale * multiplier
    bucket = None
    for key, data in (profile.get("by_bpm") or {}).items():
        low, high = key.split("-")
        high_value = float("inf") if high == "inf" else float(high)
        if float(low) <= bpm < high_value:
            bucket = data
            break
    # DESCARTADA CON NUMERO (24-08-2026) la RECTA sobre el BPM que el perfil
    # trae en `nps_por_bpm`, aplicada como factor sobre la mediana. Sobre los
    # 392 charts humanos era la mejor regla que se ha medido -- error 1.002 de
    # la regla tonta -> 0.865, correlacion +0.038 -> +0.481, y el rango del
    # objetivo pasaba de 1.4 a 2.7 veces --, pero en el chart pierde:
    #
    #                          hoy     con la recta
    #   panel, distancia      0.384       0.412        (mejoran 3 de 10)
    #   panel, F1             0.505       0.518
    #   panel, error de nps   1.033       1.009
    #   "todas iguales"        6.9         6.0
    #   Pride & Joy, distancia 0.066      0.053        <- la mejor de siempre
    #
    # El dano se concentra donde la recta no puede acertar: Thunderhorse va a
    # 92 BPM y su humano escribio 5.94 notas/s, asi que cualquier regla que baje
    # la densidad de lo lento le da de lleno (0.278 -> 0.459).
    # Y el control tonto lo remata: sobre las 22 canciones con guitarra aislada,
    # decir SIEMPRE la mediana da error 0.862 y le gana a la recta (0.974), a lo
    # mejor posible con los ataques del detector (0.931) y a todas las mezclas
    # de las dos (0.915-0.941). La densidad de una cancion no se predice con lo
    # que tenemos. La recta se sigue minando porque la medida es buena.
    source = bucket or profile
    nps = (source.get("notes_per_second") or {}).get(percentile)
    if not nps:
        return fallback * spec.density_scale * multiplier
    return float(nps) * spec.density_scale * multiplier


# Metricas donde el GENERO manda y la velocidad no dice nada. Medido sobre los
# 392 charts humanos de la biblioteca (varianza explicada, `eta cuadrado`):
#
#                      genero   BPM
#   acordes             0.112  0.007   <- el genero es lo unico que la explica
#   notas/s             0.116  0.159   <- las dos, y son independientes
#   sostenidos          0.024  0.012   <- NINGUNA de las dos: no se toca aqui
#   repeticion          0.026  0.016
#
# Por eso el genero NO sustituye la mediana: la MUEVE. Se aplica el desvio del
# genero contra la mediana global (`p50 del genero / p50 global`) sobre lo que
# diga el perfil activo. Dos razones y las dos medidas:
#   - el perfil activo puede ser el del oro (60 charts), donde ningun genero
#     llega solo a los 12 charts que hacen falta para tener mediana propia;
#   - el bucket de BPM ya explica mas densidad que el genero, y sustituir
#     tiraria ese efecto en vez de componerlo.
# Los sostenidos se quedan como estan a proposito: el genero explica el 2.4 %
# de su varianza, o sea nada. Ponerlos por genero seria inventar precision.
CLAVES_POR_FACTOR = ("chord_ratio", "repeat_ratio", "cambio_seguidas")


def _p50(bloque: dict | None, clave: str) -> float:
    return float(((bloque or {}).get(clave) or {}).get("p50") or 0.0)


def perfil_del_genero(profile: dict | None, genero: str | None) -> dict | None:
    """El perfil visto desde un genero: sus desvios mueven las medianas.

    Cae al perfil tal cual cuando la cancion no trae `genre` en su `song.ini`
    (la mayoria de las de Bruno) o cuando ese genero no llega a los 12 charts
    que `corpus.MINIMO_POR_GENERO` exige.
    """
    if not profile or not genero:
        return profile
    bloque = (profile.get("by_genre") or {}).get(genero)
    factores = (bloque or {}).get("factores") or {}
    if not factores:
        return profile
    efectivo = dict(profile)
    for clave in CLAVES_POR_FACTOR:
        factor = float(factores.get(clave) or 0.0)
        if factor <= 0:
            continue
        if clave == "cambio_seguidas":
            # No es un objetivo que nadie persiga: mueve `ALTERNANCIA_PROB`.
            efectivo["_factor_genero_alternancia"] = factor
            continue
        efectivo[clave] = {punto: round(float(valor) * factor, 4)
                           for punto, valor in (profile.get(clave) or {}).items()}
    # La DENSIDAD por genero esta minada y NO se aplica, medido el 23-08-2026
    # sobre el panel de 10 canciones: componer el factor del genero encima del
    # bucket de BPM deja el error de densidad igual (1.033 -> 1.037) y baja el
    # F1 medio de 0.505 a 0.488. El genero acierta la familia y falla la
    # cancion -- las dos latinas del panel van a 3.85 y 4.11 notas/s y la
    # mediana de las 25 latinas es 2.91, asi que el factor las FRENABA. El BPM
    # ya explica mas densidad (0.159 contra 0.116) y explica la cancion, no la
    # familia. El factor se sigue guardando en el perfil porque es una medida
    # buena; simplemente no manda aqui.
    if bloque.get("trigrams"):
        # Los trigramas son cuentas, no niveles: aqui si se sustituye. Son las
        # formas de tres notas que el banco de motivos reparte, y las de un
        # genero son otras (punk casi no tiene escaleras, metal es todo tremolo).
        efectivo["trigrams"] = bloque["trigrams"]
    efectivo["_genero"] = genero
    return efectivo


def target_ratio(profile: dict | None, key: str, fallback: float, scale: float) -> float:
    """Read a corpus median (chords, sustains) and scale it for this difficulty."""
    median = ((profile or {}).get(key) or {}).get("p50")
    if not median:
        return fallback
    return float(min(0.6, max(0.0, float(median) * scale)))


def anclar_silabas(
    candidates: list[Candidate],
    silabas: list[float] | None,
    tempo_map: TempoMap,
) -> list[Candidate]:
    """Marca los candidatos que caen sobre una silaba, y crea los que faltan.

    Dos cosas distintas y las dos hacen falta:

    - **Marcar**: un ataque que coincide con una silaba deja de valer lo mismo
      que un golpe de caja. `thin` lo antepone.
    - **Crear**: si en esa silaba el detector no vio nada, la voz esta ahi
      igual. Se inventa el candidato en la rejilla mas cercana. Sin esto, las
      silabas suaves (una vocal que entra sin ataque) se pierden siempre.

    Si no hay letra, devuelve la lista tal cual: es informacion extra, no un
    requisito.
    """
    if not silabas:
        return candidates
    por_tick = {c.tick: c for c in candidates}
    tiempos = sorted(candidates, key=lambda c: c.time)
    marcados = 0
    creados = 0
    for momento in silabas:
        # el candidato mas cercano en el tiempo
        mejor = None
        for candidato in tiempos:
            diferencia = abs(candidato.time - momento)
            if mejor is None or diferencia < mejor[0]:
                mejor = (diferencia, candidato)
            elif candidato.time - momento > SILABA_TOLERANCIA_S:
                break
        if mejor is not None and mejor[0] <= SILABA_TOLERANCIA_S:
            if not mejor[1].silaba:
                mejor[1].silaba = True
                marcados += 1
            continue
        # nadie: se crea sobre la rejilla
        beat = tempo_map.time_to_beat(momento)
        snapped = round(beat * 4) / 4.0          # semicorchea, la rejilla fina
        if snapped < 0:
            continue
        tick = tempo_map.beat_to_tick(snapped)
        if tick in por_tick:
            por_tick[tick].silaba = True
            continue
        vecino = min(tiempos, key=lambda c: abs(c.time - momento)) if tiempos else None
        nuevo = Candidate(
            beat=snapped, tick=tick, strength=SILABA_FUERZA_INVENTADA,
            midi=vecino.midi if vecino else 0.0,
            low=vecino.low if vecino else 0.3,
            mid=vecino.mid if vecino else 0.5,
            high=vecino.high if vecino else 0.3,
            time=momento, division=4,
            ring=vecino.ring if vecino else 0.0,
            lead=max(0.6, vecino.lead if vecino else 0.6),
            silaba=True,
        )
        por_tick[tick] = nuevo
        creados += 1
    anclar_silabas.marcados = marcados
    anclar_silabas.creados = creados
    return sorted(por_tick.values(), key=lambda c: c.beat)


# Ninguna frase puede durar mas que esto. Si una tirada de canto es mas larga,
# se parte por su hueco mas grande. Sin este tope, una cancion que se canta casi
# sin parar (un corrido, por ejemplo) daba UNA sola frase de tres minutos, y el
# reparto voz/instrumento pasaba a ser todo o nada: DALI salio con el 4 % de las
# silabas tocadas porque esa unica frase le toco al instrumento.
FRASE_MAXIMA_S = 7.0


def _partir_larga(inicio: float, fin: float, silabas: list[float]) -> list[tuple[float, float]]:
    if fin - inicio <= FRASE_MAXIMA_S:
        return [(inicio, fin)]
    dentro = [s for s in silabas if inicio <= s <= fin]
    if len(dentro) < 4:
        return [(inicio, fin)]
    huecos = [(b - a, i) for i, (a, b) in enumerate(zip(dentro, dentro[1:]))]
    # cortar por el hueco mas grande de la mitad central, para no dejar un trozo
    # de una silaba
    centro = [h for h in huecos if len(dentro) * 0.25 <= h[1] <= len(dentro) * 0.75]
    if not centro:
        return [(inicio, fin)]
    _, indice = max(centro)
    corte = (dentro[indice] + dentro[indice + 1]) / 2
    return (_partir_larga(inicio, corte, silabas)
            + _partir_larga(corte, fin, silabas))


def tramos_de_voz(silabas: list[float]) -> list[tuple[float, float]]:
    """Agrupa las silabas en frases cantadas, con su margen.

    Dos silabas separadas por mas de `VOZ_HUECO_DE_FRASE_S` son dos frases
    distintas, y el hueco de en medio es del instrumento. Una tirada mas larga
    que `FRASE_MAXIMA_S` se parte: la unidad de reparto tiene que ser una frase,
    no toda la cancion.
    """
    if not silabas:
        return []
    orden = sorted(silabas)
    tiradas: list[list[float]] = [[orden[0], orden[0]]]
    for momento in orden[1:]:
        if momento - tiradas[-1][1] > VOZ_HUECO_DE_FRASE_S:
            tiradas.append([momento, momento])
        else:
            tiradas[-1][1] = momento
    tramos: list[tuple[float, float]] = []
    for a, b in tiradas:
        tramos.extend(_partir_larga(a, b, orden))
    return [(a - VOZ_MARGEN_S, b + VOZ_MARGEN_S) for a, b in tramos]


def _dentro(momento: float, tramos: list[tuple[float, float]]) -> bool:
    for inicio, fin in tramos:
        if inicio <= momento <= fin:
            return True
        if inicio > momento:
            break
    return False


def repartir_frases(
    candidates: list[Candidate],
    tramos: list[tuple[float, float]],
) -> list[bool]:
    """Decide, frase a frase, si la toca la VOZ (True) o el instrumento (False).

    Dos condiciones, y hacen falta las dos. Se llego a ellas probando:

    1. **Un suelo absoluto**: en esa frase tiene que haber instrumento de
       verdad -- al menos `INSTRUMENTO_MINIMO_POR_S` ataques melodicos por
       segundo que no sean silaba. Sin este suelo, un criterio relativo siempre
       encuentra frases "por encima de la media" aunque no haya nada, y en Gil
       -- un rap donde la guitarra "no toca mucho" -- el instrumento se llevaba
       la mitad de las frases y la voz se quedaba sin tocar.
    2. **Que destaque**: ademas tiene que estar por encima de la media de la
       cancion, o cederiamos frases donde el instrumento solo acompana.

    Y nunca dos frases seguidas: la gracia es turnarse.

    Se probaron y se descartaron: el criterio relativo solo (Gil 0.48 de silabas
    tocadas cuando se pedia casi todas) y el reparto proporcional al peso del
    instrumento (todo se hundio a 0.40-0.50).
    """
    if not tramos:
        return []
    melodico = [c.strength * max(0.0, c.lead) for c in candidates if not c.silaba]
    media = (sum(melodico) / len(melodico)) if melodico else 0.0

    de_la_voz: list[bool] = []
    seguidas = 0
    for inicio, fin in tramos:
        largo = max(0.5, fin - inicio)
        sueltos = [c.strength * max(0.0, c.lead) for c in candidates
                   if not c.silaba and inicio <= c.time <= fin]
        por_segundo = len(sueltos) / largo
        aporta = (sum(sueltos) / len(sueltos)) if sueltos else 0.0
        instrumento = (
            por_segundo >= INSTRUMENTO_MINIMO_POR_S
            and media > 1e-6
            and aporta >= media * INSTRUMENTO_MANDA
            and seguidas < FRASES_SEGUIDAS_INSTRUMENTO
        )
        de_la_voz.append(not instrumento)
        seguidas = seguidas + 1 if instrumento else 0
    return de_la_voz


def elegir_por_melodia(
    candidates: list[Candidate],
    tramos: list[tuple[float, float]],
    spec: DifficultySpec,
) -> tuple[list[Candidate], list[Candidate]]:
    """Separa lo que toca la VOZ de lo que puede tocar el instrumento.

    Devuelve `(obligatorias, sueltas)`:

    - **obligatorias**: las silabas. Mientras alguien canta, la guitarra toca lo
      que se canta y punto. Es lo que pidio Bruno para Gil -- cada silaba una
      nota -- y de paso arregla que la cancion saliera "estupidamente dificil",
      porque la densidad la pone la letra y no el presupuesto del corpus.
    - **sueltas**: los ataques que caen FUERA de los tramos de voz. Esos son del
      instrumento secundario y se filtran por densidad como siempre.

    Los ataques que caen dentro de un tramo de voz pero NO son silaba se tiran
    casi todos: son justo los que hacian que sonara a dos cosas a la vez. Se
    deja pasar un `VOZ_RELLENO_MAXIMO` de los mas fuertes para no perder un
    acento gordo.
    """
    de_la_voz = repartir_frases(candidates, tramos)
    del_instrumento = [tr for tr, voz in zip(tramos, de_la_voz) if not voz]
    de_voz = [tr for tr, voz in zip(tramos, de_la_voz) if voz]

    obligatorias: list[Candidate] = []
    fuera: list[Candidate] = []
    dentro_no_silaba: list[Candidate] = []
    for candidato in candidates:
        if candidato.silaba:
            # una silaba en una frase cedida al instrumento no se toca: si no,
            # sonarian las dos cosas a la vez, que es justo lo que hay que evitar
            if _dentro(candidato.time, de_voz):
                obligatorias.append(candidato)
            continue
        if _dentro(candidato.time, de_voz):
            dentro_no_silaba.append(candidato)
        else:
            fuera.append(candidato)   # hueco, o frase del instrumento

    if dentro_no_silaba and obligatorias:
        cuantos = int(len(obligatorias) * VOZ_RELLENO_MAXIMO)
        if cuantos:
            fuertes = sorted(dentro_no_silaba, key=lambda c: c.strength, reverse=True)[:cuantos]
            obligatorias.extend(fuertes)
    obligatorias.sort(key=lambda c: c.beat)
    return obligatorias, fuera


def rellenar_huecos(
    elegidas: list[Candidate],
    todas: list[Candidate],
    spec: DifficultySpec,
    tempo_map: TempoMap,
) -> list[Candidate]:
    """Tapa los tramos donde no se toca nada y si esta sonando la cancion.

    Un respiro es bueno; un agujero de cuatro segundos con la voz cantando
    encima es un fallo. Se rellena con lo que haya en ese hueco, empezando por
    las silabas -- si alguien canta, eso es lo que hay que tocar.
    """
    if not elegidas or not todas:
        return elegidas
    por_tick = {c.tick for c in elegidas}
    salida = list(elegidas)
    for anterior, siguiente in zip(elegidas, elegidas[1:]):
        hueco = siguiente.time - anterior.time
        if hueco <= HUECO_MUDO_MAXIMO_S:
            continue
        dentro = [c for c in todas
                  if anterior.time + 0.15 < c.time < siguiente.time - 0.15
                  and c.tick not in por_tick]
        if not dentro:
            continue
        # cuantas caben sin pasarse: una cada ~0.55 s, que es un ritmo comodo
        cabe = max(1, int(hueco / 0.55))
        # las silabas primero; entre iguales, las mas fuertes
        dentro.sort(key=lambda c: (not c.silaba, -c.strength))
        puestas = 0
        ultimo = anterior.time
        for candidato in dentro:
            if puestas >= cabe:
                break
            if candidato.time - ultimo < 0.30:
                continue
            salida.append(candidato)
            por_tick.add(candidato.tick)
            ultimo = candidato.time
            puestas += 1
    salida.sort(key=lambda c: c.beat)
    return salida


def thin(
    candidates: list[Candidate],
    tempo_map: TempoMap,
    spec: DifficultySpec,
    target_nps: float,
    window_beats: float = 8.0,
    tramos_voz: list[tuple[float, float]] | None = None,
) -> list[Candidate]:
    """Keep the strongest onsets per window, then enforce the minimum gap."""
    if not candidates:
        return []

    obligatorias_por_tick = None
    if tramos_voz:
        obligatorias, sueltas = elegir_por_melodia(candidates, tramos_voz, spec)
        obligatorias_por_tick = {c.tick for c in obligatorias}
        # Los ataques que caen dentro del canto y no son silaba ya no compiten:
        # esos eran los que hacian sonar dos cosas a la vez.
        candidates = sorted(obligatorias + sueltas, key=lambda c: c.beat)

    # Primero se parten las ventanas, porque el presupuesto de cada una depende
    # de las demas: hay que saber cuanta musica hay en total para repartir.
    ventanas: list[tuple[list[Candidate], float]] = []
    cursor = candidates[0].beat
    end = candidates[-1].beat
    while cursor <= end:
        window = [c for c in candidates if cursor <= c.beat < cursor + window_beats]
        cursor += window_beats
        if not window:
            continue
        seconds = max(
            0.2,
            tempo_map.beat_to_time(window[-1].beat) - tempo_map.beat_to_time(window[0].beat) + 0.2,
        )
        ventanas.append((window, seconds))
    if not ventanas:
        return []

    # Cuanta cosa pide cada ventana. Medido en Song 2: el NUMERO de ataques por
    # ventana apenas varia (desviacion/media 0.75) porque el detector va con
    # umbral 0 y dispara en todas partes; la SUMA DE FUERZA varia mucho mas
    # (1.05) porque en el silencio los ataques son debiles aunque los haya.
    # Con el numero, el contraste no se movia de 1.2.
    demandas = [sum(c.strength for c in w) / s for w, s in ventanas]
    total_segundos = sum(s for _, s in ventanas)
    media = sum(d * s for d, (_, s) in zip(demandas, ventanas)) / max(total_segundos, 1e-6)

    alfa = getattr(spec, "contraste_alfa", CONTRASTE_ALFA)
    factores = []
    for demanda in demandas:
        relativo = (demanda / media) ** alfa if media > 1e-6 else 1.0
        factores.append(min(CONTRASTE_TECHO, max(CONTRASTE_SUELO, relativo)))

    # Renormalizar: el chart entero tiene que tener las mismas notas que antes,
    # solo repartidas distinto. Sin esto, subir el contraste seria subir la
    # densidad, y el banco lo premiaria por la razon equivocada.
    peso = sum(f * s for f, (_, s) in zip(factores, ventanas)) / max(total_segundos, 1e-6)
    if peso > 1e-6:
        factores = [f / peso for f in factores]

    kept: list[Candidate] = []
    for (window, seconds), factor in zip(ventanas, factores):
        if obligatorias_por_tick is not None:
            # Ventana con canto: la melodia es la letra y no se rellena. La
            # densidad la pone la cancion, no el presupuesto.
            cantadas = [c for c in window if c.tick in obligatorias_por_tick]
            if cantadas:
                kept.extend(cantadas)
                continue
        budget = max(1, int(round(target_nps * seconds * factor)))
        if len(window) <= budget:
            kept.extend(window)
            continue
        # Downbeats and accents survive first -- y, sobre todo, los ataques donde
        # esta sonando la guitarra solista. Sin el termino `lead`, el filtro se
        # queda con los golpes mas fuertes, que en una mezcla son la bateria: el
        # chart acababa siguiendo el acompanamiento en vez del riff.
        def priority(c: Candidate) -> float:
            on_beat = 1.0 if abs(c.beat - round(c.beat)) < 1e-6 else 0.0
            on_half = 0.5 if abs(c.beat * 2 - round(c.beat * 2)) < 1e-6 else 0.0
            return (c.strength + REJILLA_TIEMPO * on_beat + REJILLA_MEDIO * on_half
                    + LEAD_PRIORITY * c.lead
                    + (SILABA_PRIORIDAD if c.silaba else 0.0))

        puntos = [priority(c) for c in window]
        if RACHA_VENTANA > 1 and len(puntos) > RACHA_VENTANA:
            pad = RACHA_VENTANA // 2
            arr = np.array(puntos, dtype=float)
            nucleo = np.ones(RACHA_VENTANA) / RACHA_VENTANA
            puntos = np.convolve(np.pad(arr, pad, mode="edge"), nucleo,
                                 mode="valid")[:len(window)].tolist()

        # MEDIDO Y NO ADOPTADO (23-08-2026): gastar el presupuesto solo en
        # notas que sobrevivan al recorte de "demasiado juntas", cogiendo por
        # prioridad y comprobando el hueco minimo sobre la marcha (bisect sobre
        # los beats ya elegidos). Arregla una fuga real -- Pride & Joy pasa de
        # 819 notas a 859 de las 982 del humano, el recorte baja de 74 a 18, y
        # la cancion de aceptacion mejora entera: F1 0.586 -> 0.595, distancia
        # 0.066 -> 0.055, ligadas 0.217 -> 0.226.
        #
        # Y NO SE PUEDE ADOPTAR TODAVIA, porque el objetivo de densidad es casi
        # constante (3.9-4.4) y entregarlo de verdad hace que todas las
        # canciones converjan en el mismo sitio. En el panel de 10:
        #     distancia 0.384 -> 0.420, "todas iguales" 6.9 -> 8.3 veces,
        #     error de densidad 1.033 -> 1.072, mejoran 2 de 10.
        # El desglose lo dice claro: donde ibamos cortos el error de densidad
        # baja de 0.950 a 0.803, y donde ya ibamos pasados sube de 1.116 a
        # 1.341. O sea que la fuga estaba TAPANDO un objetivo malo, y cada
        # cancion perdia una cantidad distinta -- variedad por accidente.
        # Primero que el objetivo varie; esto se vuelve a poner despues.
        if CADENA_PREMIO > 0.0:
            # Se elige de uno en uno para que cada nota tire de la siguiente.
            cerca = chartio.HOPO_TICKS_AT_192 / 192.0
            puntos = list(puntos)
            libres = set(range(len(window)))
            elegidos: list[int] = []
            for _ in range(min(budget, len(window))):
                i = max(libres, key=lambda k: puntos[k])
                libres.discard(i)
                elegidos.append(i)
                for k in libres:
                    if abs(window[k].beat - window[i].beat) <= cerca + 1e-9:
                        puntos[k] += CADENA_PREMIO
            chosen = [window[i] for i in elegidos]
        else:
            orden = sorted(range(len(window)), key=lambda i: puntos[i], reverse=True)
            chosen = [window[i] for i in orden[:budget]]
        kept.extend(sorted(chosen, key=lambda c: c.beat))

    kept.sort(key=lambda c: c.beat)
    _pierde("ataques detectados", len(candidates))
    _pierde("presupuesto de densidad", sum(
        max(1, int(round(target_nps * s2 * f))) for (_, s2), f in zip(ventanas, factores)))
    _pierde("sobreviven al presupuesto", len(kept))
    kept = rellenar_huecos(kept, candidates, spec, tempo_map)
    _pierde("tras rellenar huecos", len(kept))

    spaced: list[Candidate] = []
    for candidate in kept:
        if spaced and candidate.beat - spaced[-1].beat < spec.min_gap_beats - 1e-6:
            if candidate.strength > spaced[-1].strength * 1.25:
                spaced[-1] = candidate
            continue
        spaced.append(candidate)
    _pierde("tiradas por el hueco minimo", len(kept) - len(spaced))
    _pierde("notas finales", len(spaced))
    return spaced


# ---------------------------------------------------------------------------
# Step 3 -- frets
# ---------------------------------------------------------------------------


def _fill_missing_pitch(candidates: list[Candidate]) -> np.ndarray:
    """Interpolate a pitch contour across onsets where the CQT found nothing."""
    values = np.array([c.midi if c.midi > 0 else np.nan for c in candidates], dtype=float)
    if np.all(np.isnan(values)):
        return np.zeros(len(candidates))
    indices = np.arange(len(values))
    known = ~np.isnan(values)
    values[~known] = np.interp(indices[~known], indices[known], values[known])
    return values


def _contour_to_lanes(pitches: np.ndarray, lanes: int, cuts: tuple[float, ...] = CONTOUR_CUTS) -> list[int]:
    """Map the pitch INTERVAL onto a change of lane, not the pitch onto a lane.

    El corpus no dice donde pone un humano la mano, dice cuanto la MUEVE entre
    nota y nota: se queda 31 %, ±1 47 %, ±2 14 %, ±3 6 %. Asi que los umbrales
    salen de la distribucion de intervalos de la propia cancion, cortada por esos
    acumulados.

    Antes se mapeaba el tono absoluto a un carril con el minimo y el maximo de
    una ventana movil. Eso es un mapeo SIN MEMORIA: dos notas seguidas con tonos
    moderadamente distintos caian a dos carriles de distancia, y salian un 25.8 %
    de saltos de ±2 contra el 14 % humano. Medido sobre dos canciones, el error
    total contra la distribucion humana baja de 23.9 y 30.2 puntos a 14.6 y 10.2.

    Probado y descartado: normalizar por percentiles en vez de min/max lo empeora
    (hasta 43 puntos de error), porque recortar el rango manda mas notas a los
    carriles de los extremos.
    """
    count = len(pitches)
    if count == 0:
        return []
    deltas = np.diff(np.asarray(pitches, dtype=float))
    magnitude = np.abs(deltas)
    moving = magnitude[magnitude > 1e-9]
    if moving.size < 4:
        return [lanes // 2] * count
    low_cut, mid_cut, high_cut = (float(np.percentile(moving, c)) for c in cuts)

    out = [lanes // 2]
    for delta in deltas:
        size = abs(float(delta))
        if size < low_cut:
            step = 0
        elif size < mid_cut:
            step = 1
        elif size < high_cut:
            step = 2
        else:
            step = 3
        direction = 1 if delta > 0 else -1
        target = out[-1] + direction * step
        if not 0 <= target <= lanes - 1:
            # Rebotar en vez de recortar: conserva el TAMANO del salto, que es lo
            # que se esta calibrando. Recortar aplasta los saltos contra el borde.
            target = out[-1] - direction * step
        out.append(int(min(lanes - 1, max(0, target))))
    return out


# Quien decide el traste de cada nota. Seis reglas actuan una detras de otra y
# la ultima que cambia el valor es la que manda; hasta el 22-08-2026 nadie habia
# contado cuantas notas decide cada una, asi que "el chart sigue la melodia" era
# una creencia, no una medida. Lo lee tools/quien_decide.py.
# Cuando la nota se REPITE, el humano mueve la mano casi la mitad de las veces.
# Medido en Pride & Joy (981 parejas, guitarra aislada): de las parejas en las
# que el tono no se mueve, el charter cambia de traste el **46,5 %**; este
# generador solo el 31,2 %. De ahi salen sus dos defectos gemelos en esa
# cancion: repite traste el 39,5 % contra el 14,1 % del humano, y liga el 15 %
# contra su 39 % -- que son la misma cosa, porque si el traste no cambia no
# puede haber martilleo.
#
# Solo se alterna en notas seguidas (hueco corto): en una nota larga o aislada
# repetir el traste es lo natural y lo que hace el humano.
# El valor sale de las DOCE canciones, no de una: la mediana de lo que mueve el
# humano cuando la nota se repite es 53,6 % (media 51,2 %, y va de 7,7 % en
# Aliens Exist a 86,4 % en Thunderstruck). Con 0.45 el generador da 51,9 % en
# Pride & Joy. Calibrar con la sola Pride & Joy habria dado 0.25, y su 46,5 %
# esta en la parte baja de la distribucion (CLAUDE.md: una sola cancion no
# decide nada).
# DESCARTADO CON NUMERO (24-08-2026) tomar esta decision UNA VEZ POR TIRADA en vez
# de nota a nota. La idea salia de una medida buena: la tasa ya es correcta (pasos
# de traste repetido, 24.5 % nuestro contra 29.8 % humano) y lo que falla es el
# reparto -- el humano es bimodal (45 % de sus tiradas largas sin un solo repetido
# y 19 % con cuatro o mas) y un sorteo independiente por nota no puede serlo, asi
# que nos quedabamos en el 33 % de 'exactamente uno', justo donde el casi no esta.
# En el panel de 10: error de repeticion 0.150 -> 0.143 y de ligadas sin cambio,
# F1 igual, y la distancia de gestos 0.384 -> 0.399, mejorando 1 de 10.
# La causa de que no baste esta medida: la alternancia solo decide el 9.0 % de los
# carriles (`tools/quien_decide.py`; el contorno pone el 72.5 % y el banco el
# 15.4 %), asi que comprometerse no puede escribir un tremolo que el contorno no
# ofrezca ni salvar el que el banco se lleva.
ALTERNANCIA_PROB = 0.45
ALTERNANCIA_HUECO = 0.55   # tiempos; una corchea a 120 BPM es 0.5


def alternancia_del_perfil(profile: dict | None) -> float:
    """`ALTERNANCIA_PROB` movida por el genero, cuando el genero se sabe.

    El 0.45 esta calibrado contra las doce canciones con guitarra aislada, donde
    la vara es "cuando la nota SE REPITE, cuantas veces mueve la mano el
    humano". El corpus entero no puede medir eso (hace falta el tono del audio),
    pero si mide una vara hermana en los 392 charts: cuantas veces cambia de
    traste entre dos notas SEGUIDAS. Su mediana global es 0.760 y por genero va
    de 0.638 (punk) a 0.917 (latino). Se aplica ese desvio sobre el 0.45
    calibrado, que asi se mantiene intacto para la mediana.
    """
    if not profile:
        return ALTERNANCIA_PROB
    factor = float((profile or {}).get("_factor_genero_alternancia") or 1.0)
    return float(min(0.9, max(0.05, ALTERNANCIA_PROB * factor)))

REPARTO: dict[str, int] = {}


def _apunta(motivo: str) -> None:
    REPARTO[motivo] = REPARTO.get(motivo, 0) + 1


# Cuantas notas pierde la etapa de densidad y donde. Medido en Pride & Joy el
# 22-08-2026: se detectan 2026 ataques, el objetivo son 912 notas y el chart
# sale con 661. O sea que el problema de "no detecta todas las notas" no esta en
# el detector -- detecta el doble de las que escribio el humano -- sino en lo
# que se tira despues. Lo lee tools/quien_decide.py.
PERDIDAS: dict[str, int] = {}

# Por que una nota acaba (o no) siendo sostenido. Lo mismo, para la pregunta
# hermana: los sostenidos salian seis veces de mas y el objetivo del perfil se
# cumplia a rajatabla, asi que hay que poder ver cuantas notas se caen en cada
# criba antes de tocar ninguna. Lo lee tools/quien_decide.py.
SOSTENIDOS: dict[str, int] = {}


def _pierde(motivo: str, cuantas: int = 1) -> None:
    if cuantas:
        PERDIDAS[motivo] = PERDIDAS.get(motivo, 0) + cuantas


def _motif_bank(profile: dict | None, lanes: int, rng: random.Random) -> list[tuple[int, ...]]:
    """Three-note shapes sampled from the corpus, filtered to the usable lanes."""
    trigrams = (profile or {}).get("trigrams") or {}
    bank: list[tuple[int, ...]] = []
    for key, count in trigrams.items():
        if len(key) != 3 or not key.isdigit():
            continue
        shape = tuple(int(ch) for ch in key)
        if any(value >= lanes for value in shape):
            continue
        bank.extend([shape] * max(1, min(6, int(count) // 40)))
    if not bank:
        base = [(0, 1, 2), (2, 1, 0), (1, 2, 3), (3, 2, 1), (0, 1, 0), (2, 3, 2), (1, 0, 1)]
        bank = [s for s in base if all(v < lanes for v in s)] or [(0, 1, 0)]
    rng.shuffle(bank)
    return bank


def assign_frets(
    candidates: list[Candidate],
    spec: DifficultySpec,
    profile: dict | None,
    rng: random.Random,
) -> list[int]:
    """Give every candidate a lane, honouring contour, jump limits and motifs."""
    alternancia = alternancia_del_perfil(profile)
    if not candidates:
        return []

    pitches = _fill_missing_pitch(candidates)
    raw_lanes = _contour_to_lanes(pitches, spec.lanes)
    motifs = _motif_bank(profile, spec.lanes, rng)
    motif_cursor = 0

    lanes: list[int] = []
    previous = raw_lanes[0]
    flat_run = 0
    salto_racha = 0  # saltos anchos seguidos que lleva la mano ahora mismo
    for index, candidate in enumerate(candidates):
        wanted = raw_lanes[index]
        if index == 0:
            lanes.append(wanted)
            previous = wanted
            continue

        pitch_moved = abs(float(pitches[index]) - float(pitches[index - 1])) >= 0.75
        gap = candidate.beat - candidates[index - 1].beat

        if not pitch_moved:
            flat_run += 1
        else:
            flat_run = 0

        decide = "contorno"
        if flat_run >= 3:
            # The audio stopped telling us anything useful; borrow a shape.
            #
            # DESCARTADO CON NUMERO (24-08-2026) no prestar la forma cuando las
            # notas van PEGADAS (`gap <= ALTERNANCIA_HUECO`). El razonamiento era
            # bueno y la medida tambien: un tono plano con las notas juntas no es
            # el audio callandose, es el audio diciendo TREMOLO, y este `if` lo
            # borra -- de las rachas de largo >= 4, las que van a un solo traste
            # son el 19.9 % de las humanas de largo 4 y el 0.7 % de las nuestras.
            # Con el cambio: tremolo 0.7 % -> 2.8 %, error de repeticion 0.150 ->
            # 0.117, de ligadas 0.115 -> 0.097, F1 igual, distancia 0.384 -> 0.399
            # y mejoran 4 de 10.
            #
            # Y lo mata la metrica que le importa a Bruno: "todas iguales" se va
            # de 6.9 a 10.6 veces. La causa es que este `if` hace DOS trabajos --
            # sin el, todas las tiradas rapidas de todas las canciones hacen lo
            # mismo (aguantar el traste), y era el banco el que las hacia
            # distintas. Matar el tremolo era el precio de esa variedad.
            #
            # Asi que el arreglo no es quitar el banco: es que el banco sepa hacer
            # tremolo. Dos cosas medidas y sin tocar -- `000` es el trigrama MAS
            # frecuente del corpus (2.560) y las formas planas el 16.7 % de su
            # peso, pero el tope `min(6, count // 40)` las deja en el 8.5 %; y sus
            # formas son carriles ABSOLUTOS, asi que un `000` a mitad de cancion
            # tira la mano al verde en vez de dejarla quieta.
            decide = "motivo del banco"
            motif = motifs[motif_cursor % len(motifs)]
            wanted = motif[flat_run % 3]
            if flat_run % 3 == 2:
                motif_cursor += 1

        # Fast notes stay under the fingers; slow notes may leap. A que
        # velocidad pone un salto ancho el humano, medido en 168 charts de la
        # biblioteca (105.303 pares de notas sueltas en Experto):
        #   negra       (>= 0.45)  9.8 % de sus pares -- 46 % de todos sus saltos
        #   corchea     (>= 0.24)  6.6 %              -- 32 %
        #   semicorchea (<  0.24)  3.6 %              --  6 %
        # Cortar en dos carriles a velocidad de corchea prohibia **un tercio de
        # los saltos anchos que un humano escribe**. La mano si salta deprisa;
        # salta menos, y eso ya lo decide el contorno (solo el 5 % de los
        # intervalos de una cancion pide tres carriles). El limite solo tenia
        # que dejar de impedirlo.
        allowed = spec.max_jump if gap >= 0.45 else min(spec.max_jump, 3 if gap >= 0.24 else 1)
        delta = wanted - previous

        # Memoria del gesto. El limite de arriba se recalcula nota a nota
        # mirando solo el hueco, y un limite por nota no puede producir rachas:
        # produce saltos sueltos, que jugando son "un cambio que no ves venir".
        # El humano encadena -- 68 % de los saltos anchos van seguidos de otro,
        # medido en 391 charts (`tools/transiciones.py`) -- y este generador se
        # quedaba en el 39 %. Mientras dura la racha no se prohibe seguir
        # saltando, y un movimiento que YA iba a ser grande se completa hasta
        # salto ancho. No se inventa ninguna nota: solo cambia el carril.
        if 0 < salto_racha < SALTO_RACHA_MAXIMA and gap <= SALTO_RACHA_HUECO:
            allowed = max(allowed, SALTO_ANCHO_CARRILES)
            if abs(delta) >= SALTO_ANCHO_CARRILES - 1:
                direction = 1 if delta > 0 else -1
                target = previous + SALTO_ANCHO_CARRILES * direction
                if not 0 <= target <= spec.lanes - 1:
                    # Rebotar, como hace el contorno: un salto contra el borde
                    # recortado deja de ser un salto.
                    target = previous - SALTO_ANCHO_CARRILES * direction
                if 0 <= target <= spec.lanes - 1:
                    if target != wanted:
                        decide = "racha de gesto"
                    wanted = target
                    delta = wanted - previous

        if abs(delta) > allowed:
            wanted = previous + allowed * (1 if delta > 0 else -1)
            decide = "limite de velocidad"
        recortado = int(min(spec.lanes - 1, max(0, wanted)))
        if recortado != wanted:
            decide = "borde del mastil"
        wanted = recortado

        # Staying on the same fret is not a failure -- human charters do it 27 %
        # of the time, and forcing a move on every semitone made this generator
        # restless (12.5 % repeats measured). Only a real melodic step moves the
        # hand when the contour rounded to the same lane.
        if wanted == previous and abs(float(pitches[index]) - float(pitches[index - 1])) >= REPEAT_BREAK_SEMITONES:
            direction = 1 if previous < spec.lanes - 1 else -1
            wanted = previous + direction
            decide = "anti-repeticion"
        elif (wanted == previous and not pitch_moved and gap <= ALTERNANCIA_HUECO
              and alternancia > 0 and rng.random() < alternancia):
            # la nota se repite y va seguida: el humano mueve la mano aqui
            direction = 1 if previous < spec.lanes - 1 else -1
            wanted = previous + direction
            decide = "alternancia de nota repetida"

        # La racha se cuenta sobre el carril que de verdad sale, no sobre el que
        # se pidio: si el recorte lo dejo en dos carriles, no hubo salto ancho.
        if abs(wanted - previous) >= SALTO_ANCHO_CARRILES and gap <= SALTO_RACHA_HUECO:
            salto_racha += 1
        else:
            salto_racha = 0

        _apunta(decide)
        lanes.append(wanted)
        previous = wanted
    return lanes


# ---------------------------------------------------------------------------
# Step 4 -- reuse repeated bars
# ---------------------------------------------------------------------------


def _bar_key(bar: list[Candidate], pitches: np.ndarray, offset: int) -> str:
    rhythm = ",".join(f"{c.beat % 4:.3f}" for c in bar)
    contour = []
    for index in range(1, len(bar)):
        delta = float(pitches[offset + index]) - float(pitches[offset + index - 1])
        contour.append("u" if delta > 0.75 else ("d" if delta < -0.75 else "="))
    return hashlib.md5(f"{rhythm}|{''.join(contour)}".encode()).hexdigest()[:12]


def reuse_repeated_bars(
    candidates: list[Candidate],
    lanes: list[int],
    beats_per_bar: float = 4.0,
) -> list[int]:
    """Copy the fret shape of an earlier identical bar so riffs read as riffs."""
    if len(candidates) < 8:
        return lanes

    pitches = _fill_missing_pitch(candidates)
    out = list(lanes)
    memory: dict[str, list[int]] = {}
    index = 0
    while index < len(candidates):
        bar_index = int(candidates[index].beat // beats_per_bar)
        end = index
        while end < len(candidates) and int(candidates[end].beat // beats_per_bar) == bar_index:
            end += 1
        bar = candidates[index:end]
        if len(bar) >= 3:
            key = _bar_key(bar, pitches, index)
            remembered = memory.get(key)
            if remembered is not None and len(remembered) == len(bar):
                for salto, valor in enumerate(remembered):
                    if out[index + salto] != valor:
                        _apunta("compas repetido")
                out[index:end] = remembered
            else:
                memory[key] = out[index:end]
        index = end
    return out


def inherit_expert_lanes(
    candidates: list[Candidate],
    lanes: list[int],
    expert_frets: dict[int, list[int]],
    max_lanes: int,
) -> list[int]:
    """Reuse Expert's fret wherever this difficulty plays the same instant.

    Las posiciones ya coincidian: medido, el 99-100 % de las notas de Facil caen
    en un tick que Experto tambien toca (el humano esta en 99.5 %). Lo que no
    coincidia era el TRASTE, porque cada dificultad se asignaba por su cuenta.
    Heredarlo es lo que hace que Facil se reconozca como la misma cancion.

    Cuando el traste de Experto no cabe (Facil tiene 3 carriles, Medio 4) se
    acerca al que pedia el contorno. Eso reproduce solo la escalera que ya hacen
    los humanos: Dificil comparte traste el 91 % de las veces, Medio el 62 % y
    Facil el 44 %.
    """
    if not expert_frets:
        return lanes
    out = list(lanes)
    for index, candidate in enumerate(candidates):
        frets = expert_frets.get(candidate.tick)
        if not frets:
            continue
        wanted = out[index]
        fits = [fret for fret in frets if fret < max_lanes]
        if fits:
            out[index] = min(fits, key=lambda fret: (abs(fret - wanted), fret))
        else:
            closest = min(frets, key=lambda fret: abs(fret - wanted))
            out[index] = max(0, min(max_lanes - 1, closest))
    return out


# ---------------------------------------------------------------------------
# Step 5 -- chords, sustains, star power
# ---------------------------------------------------------------------------


def build_notes(
    candidates: list[Candidate],
    lanes: list[int],
    spec: DifficultySpec,
    tempo_map: TempoMap,
    rng: random.Random,
    chord_ratio: float | None = None,
    sustain_ratio: float | None = None,
    end_beat: float | None = None,
) -> list[Note]:
    """Emit the actual note events, adding chords on accents and sustains on gaps.

    `end_beat` is where the audio stops. Nothing may ring past it: cuando la
    cancion acaba con un sostenido a medias, el juego corta el audio y la nota
    se pierde sin que el jugador pueda hacer nada.
    """
    notes: list[Note] = []
    if not candidates:
        return notes

    resolution = tempo_map.resolution
    chord_target = spec.chord_ratio if chord_ratio is None else chord_ratio
    sustain_target = spec.sustain_ratio if sustain_ratio is None else sustain_ratio

    # Chords land on the loudest, most isolated, low-heavy attacks -- y donde la
    # banda melodica NO manda, porque ahi la guitarra esta acompanando.
    def chord_score(index: int) -> float:
        candidate = candidates[index]
        gap_before = candidate.beat - candidates[index - 1].beat if index else 4.0
        gap_after = candidates[index + 1].beat - candidate.beat if index + 1 < len(candidates) else 4.0
        room = min(2.0, min(gap_before, gap_after))
        downbeat = 1.0 if abs(candidate.beat % 4.0) < 1e-6 else 0.0
        return (
            candidate.strength * 1.0 + room * 0.6 + candidate.low * 0.5
            + downbeat * 0.4 - candidate.lead * 0.8
        )

    chord_count = int(round(len(candidates) * chord_target))
    chord_indices: set[int] = set()
    if chord_count:
        scores = np.array([chord_score(index) for index in range(len(candidates))])
        # Suavizar antes de cortar. Un guitarrista no alterna acorde y nota
        # suelta cada dos notas: toca un tramo de acordes y luego una linea.
        # Medido en 120 charts humanos, las rachas son de 4.76 acordes y 10.51
        # notas sueltas; puntuando cada nota por su cuenta salian 1.58 y 2.97,
        # que es lo que hacia que no se sintiera un instrumento tocado.
        if CHORD_RUN_WINDOW > 1 and scores.size > CHORD_RUN_WINDOW:
            pad = CHORD_RUN_WINDOW // 2
            kernel = np.ones(CHORD_RUN_WINDOW) / CHORD_RUN_WINDOW
            scores = np.convolve(np.pad(scores, pad, mode="edge"), kernel, mode="valid")[:len(candidates)]
        chord_indices = set(np.argsort(scores)[::-1][:chord_count].tolist())

    # Sustains go on the widest gaps, which is where the audio is ringing out.
    last_beat = candidates[-1].beat + 4.0
    if end_beat is not None:
        last_beat = max(candidates[-1].beat, min(last_beat, end_beat))
    gaps: list[tuple[float, int]] = []
    gap_seconds: list[float] = []
    for index, candidate in enumerate(candidates):
        next_beat = candidates[index + 1].beat if index + 1 < len(candidates) else last_beat
        gaps.append((next_beat - candidate.beat, index))
        gap_seconds.append(tempo_map.beat_to_time(next_beat) - tempo_map.beat_to_time(candidate.beat))
    # Cuanto puede durar cada sostenido: lo que quepa antes de la nota siguiente,
    # pero nunca mas de lo que la cuerda sigue sonando. Los sostenidos se eligen
    # por ESO, no por el hueco: un hueco ancho puede ser un silencio, y estirar
    # una nota sobre un silencio es lo que daba medianas de 3.8 tiempos en Facil.
    lengths: list[float] = []
    for index, candidate in enumerate(candidates):
        room = min(SUSTAIN_MAX_BEATS, gaps[index][0] - SUSTAIN_TAIL_BEATS)
        if candidate.ring > 0.0:
            ring_beats = tempo_map.time_to_beat(candidate.time + candidate.ring) - candidate.beat
            room = min(room, ring_beats)
        if end_beat is not None:
            room = min(room, end_beat - candidate.beat)
        lengths.append(room)

    # El hueco minimo para que una nota merezca sostenido es una relacion
    # MUSICAL, no una duracion fisica. Puesto solo en segundos, a 151 BPM pedia
    # 1.14 tiempos de hueco y Teddy Picker salia con un 0.2 % de sostenidos
    # contra el 12.9 % de su charter humano: cuanto mas rapida la cancion, menos
    # sostenidos, que es justo al reves de lo que hacen los humanos.
    # **El objetivo del perfil es un TOPE, no una cuota.** Antes se cogian las N
    # notas de hueco mas ancho hasta llenar el ratio del corpus, asi que TODAS
    # las canciones salian con el mismo 15 % de sostenidos -- medido en seis
    # canciones humanas cuya realidad iba de 0.00 (Blur) a 0.76 (Thunderhorse),
    # y en Pride & Joy daba 0.106 contra los 0.017 que escribio su charter.
    # Ahora manda el audio: solo entran las notas que de verdad siguen sonando,
    # y el ratio del perfil solo pone el maximo.
    sustain_count = int(round(len(candidates) * sustain_target))
    elegibles = []
    for index, candidate in enumerate(candidates):
        beat_seconds = max(
            1e-6,
            tempo_map.beat_to_time(candidate.beat + 1.0) - tempo_map.beat_to_time(candidate.beat),
        )
        min_gap = min(SUSTAIN_MIN_GAP_S, SUSTAIN_MIN_GAP_BEATS * beat_seconds)
        if (gap_seconds[index] >= min_gap
                and lengths[index] >= SUSTAIN_MIN_LENGTH_BEATS):
            elegibles.append(index)
    # DESCARTADO CON NUMERO (23-08-2026): ordenar los elegibles por el RING en
    # vez de por `lengths`. La idea venia de una medida buena -- entre las notas
    # con sitio, el ring separa (AUC 0.727) y el hueco no (0.580) -- pero no
    # cambia nada, y la razon esta en la propia formula: `lengths` es
    # `min(hueco, ring)`, y en una nota elegible el hueco es ancho por
    # definicion, asi que `lengths` YA es el ring. Medido: Pride & Joy identica
    # (F1 0.586, distancia 0.066, sostenidos 0.095) y el lote de control de 4
    # algo peor (parecidas 9.3 -> 9.9, sostenido_largo por 100 notas 0.10 ->
    # 0.06). El ring ya mandaba donde podia mandar.
    elegibles.sort(key=lambda i: lengths[i], reverse=True)
    sustain_indices = set(elegibles[:sustain_count])
    # NO HACE FALTA eximir al sostenido largo de la cuota, y esta escrito porque
    # parecia que si: `elegibles` va ordenada por largo, asi que el tope corta
    # por abajo y los largos ya estaban todos dentro. Medido: exentarlos no
    # movio ni una milesima del panel. Que solo se aproveche el 57.9 % de los
    # huecos donde cabe uno (el humano 77.8 %) no lo causa la cuota sino el
    # `ring`: en el resto de esos huecos la cuerda ya no suena.
    if spec.name == "Expert":
        SOSTENIDOS.update({
            "candidatos": len(candidates),
            "tope_del_perfil": sustain_count,
            "hueco_suficiente": sum(1 for i in range(len(candidates))
                                    if gap_seconds[i] >= min(
                                        SUSTAIN_MIN_GAP_S,
                                        SUSTAIN_MIN_GAP_BEATS * max(1e-6,
                                            tempo_map.beat_to_time(candidates[i].beat + 1.0)
                                            - tempo_map.beat_to_time(candidates[i].beat)))),
            "largo_suficiente": sum(1 for i in range(len(candidates))
                                    if lengths[i] >= SUSTAIN_MIN_LENGTH_BEATS),
            "sin_tono": sum(1 for c in candidates if c.ring <= 0.0),
            "elegibles": len(elegibles),
            "escritos": len(sustain_indices),
        })

    previous_chord: tuple[int, ...] | None = None
    for index, candidate in enumerate(candidates):
        lane = int(min(spec.lanes - 1, max(0, lanes[index])))
        sustain_ticks = 0
        if index in sustain_indices:
            sustain_ticks = int(round(lengths[index] * resolution))

        frets = [lane]
        if index in chord_indices and spec.max_chord_size >= 2:
            # Mantener la forma mientras dure el tramo. Medido en 120 charts
            # humanos, cuando un acorde sigue a otro el 61.8 % es la MISMA forma
            # exacta y un 13.3 % la misma desplazada: un guitarrista agarra una
            # postura y la mueve. Sorteando una forma nueva cada vez salia un
            # 15.2 % de repeticion, y cinco acordes seguidos al azar no suenan a
            # riff.
            shape: tuple[int, ...] | None = None
            if previous_chord is not None:
                if lane in previous_chord:
                    if rng.random() < CHORD_SHAPE_KEEP:
                        shape = previous_chord
                elif rng.random() < CHORD_SHAPE_SHIFT:
                    # Mover la postura solo a veces: si se desplaza siempre que
                    # el carril no encaja salen un 33 % de acordes desplazados
                    # contra el 13.3 % humano, y el humano lo que hace el resto
                    # de las veces es cambiar de postura.
                    shape = _shift_chord_shape(previous_chord, lane, spec.lanes)
            if shape is None:
                options = [s for s in CHORD_SHAPES if lane in s and max(s) < spec.lanes]
                if options:
                    shape = options[rng.randrange(len(options))]
            if shape is not None:
                frets = sorted(set(shape))
            # La postura que se hereda es la BASE, antes de engordarla a tres
            # notas. Guardando la engordada, cada vuelta le anadia una nota mas
            # y salian acordes de cinco (lo canto el validador).
            previous_chord = tuple(frets)
            if spec.max_chord_size >= 3 and candidate.strength > 0.75 and rng.random() < 0.18:
                extra = max(frets) + 1 if max(frets) + 1 < spec.lanes else min(frets) - 1
                if 0 <= extra < spec.lanes:
                    frets = sorted(set(frets + [extra]))
            if len(frets) > spec.max_chord_size:
                frets = frets[: spec.max_chord_size]
        else:
            previous_chord = None

        for fret in frets:
            notes.append(Note(candidate.tick, fret, sustain_ticks))
    return notes


def hopo_flags(notes: list[Note], resolution: int, rng: random.Random) -> list[Note]:
    """Escribir las marcas de forzado (`N 5`) que escribiria un charter humano.

    Sin ninguna marca, el juego liga todo lo que cae junto y no liga nada de lo
    que cae separado. Un humano no hace eso: de las 13.524 marcas medidas en
    ExpertSingle, la mitad **corta** una ligadura que el juego habria hecho sola
    y la otra mitad **liga** dos notas que el juego dejaria sueltas. Es lo que
    mas se nota en la mano, porque decide si un tramo se toca con la izquierda
    sola o hay que rasguear cada nota.

    Las dos cosas que hace un humano, con las tasas medidas:

    * **cortar la primera de la racha** (21.4 % de los casos, contra 5.5 % en
      una de en medio): rasguear la nota que abre la frase y ligar el resto.
    * **ligar la corchea recta** cuando la mano se mueve poco (11.9 % a un
      carril, 5.3 % a dos, 2.8 % mas lejos).

    Las tasas se sortean en vez de aplicarse siempre porque **el humano tampoco
    marca siempre**: forzar todos los casos elegibles daria cinco veces mas
    marcas de las que pone una persona, y un chart donde cada corchea esta
    ligada se toca tan plano como uno donde no lo esta ninguna.

    Lo que NO se escribe, y es una decision, no un olvido:

    * **Taps (`N 6`)**: la mediana de la biblioteca es **cero** por chart y solo
      el 26 % de los charts pone alguno. Escribirlos seria inventarse un idioma
      que tres de cada cuatro charters no usan.
    * **Acordes ligados**: un humano los escribe (918 veces), pero es un gesto
      avanzado y el juego no los liga nunca por su cuenta.
    * **Repetir traste ligado**: cero casos de 6.668. No se puede martillear una
      nota que ya estaba pulsada.
    """
    groups = chartio.group_notes(notes)
    if len(groups) < 2:
        return []

    threshold = chartio.hopo_distance(resolution)
    link_max = FORCE_LINK_MAX_BEATS * resolution

    flags: list[Note] = []
    previous_natural = False
    for index in range(1, len(groups)):
        group = groups[index]
        previous = groups[index - 1]
        gap = group.tick - previous.tick
        natural = chartio.is_natural_hopo(previous, group, threshold)

        if natural:
            chance = FORCE_CUT_RUN_START if not previous_natural else FORCE_CUT_IN_RUN
        elif group.is_chord or gap <= threshold or gap > link_max:
            # Un acorde, una nota repetida (que ya cae cerca y el juego no liga),
            # o un hueco que ningun humano estira.
            chance = 0.0
        elif previous.is_chord:
            chance = FORCE_LINK_AFTER_CHORD
        else:
            step = abs(group.frets[0] - previous.frets[0])
            chance = (
                FORCE_LINK_STEP1 if step == 1
                else FORCE_LINK_STEP2 if step == 2
                else FORCE_LINK_FAR
            )

        if chance > 0.0 and rng.random() < chance:
            flags.append(Note(group.tick, chartio.FLAG_FORCE, 0))
        previous_natural = natural
    return flags


def star_power_phrases(
    candidates: list[Candidate],
    tempo_map: TempoMap,
    target_phrases: int = SP_TARGET_PHRASES,
    phrase_beats: float = SP_PHRASE_BEATS,
) -> list[SpecialPhrase]:
    """Phrases of a fixed musical length, spread evenly over the song.

    Medido en la biblioteca: una frase dura 6.97 tiempos de mediana y hay 10 por
    pista, **en las cuatro dificultades**. Contarlas por numero de notas -- como
    se hacia antes -- las dejaba en 4 o 5 en Experto y en cero en Facil y Medio,
    donde el medidor de Star Power no llegaba a llenarse nunca.
    """
    if len(candidates) < 8:
        return []
    start_time = tempo_map.beat_to_time(candidates[0].beat)
    span = tempo_map.beat_to_time(candidates[-1].beat) - start_time
    if span <= 0 or target_phrases < 1:
        return []
    every = span / target_phrases

    phrases: list[SpecialPhrase] = []
    next_allowed = start_time + every * 0.5
    index = 0
    while index < len(candidates):
        candidate = candidates[index]
        time = tempo_map.beat_to_time(candidate.beat)
        if time < next_allowed:
            index += 1
            continue
        end_beat = candidate.beat + phrase_beats
        inside = index
        while inside + 1 < len(candidates) and candidates[inside + 1].beat < end_beat:
            inside += 1
        # Una frase sin notas dentro es un fallo de carga en el juego, y dos
        # frases solapadas tambien: el final real manda sobre el teorico.
        length = max(tempo_map.resolution, tempo_map.beat_to_tick(end_beat) - candidate.tick)
        phrases.append(SpecialPhrase(candidate.tick, 2, length))
        next_allowed = max(time + every, tempo_map.beat_to_time(end_beat) + 0.25)
        index = inside + 1
    return phrases


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def generate_chart(
    analysis: AudioAnalysis,
    metadata: dict[str, str] | None = None,
    profile: dict | None = None,
    difficulties: tuple[str, ...] = ("Expert", "Hard", "Medium", "Easy"),
    seed: int = 7,
    resolution: int = RESOLUTION,
    density: float = 1.0,
    density_percentile: str = "p50",
    silabas: list[float] | None = None,
    genero: str | None = None,
) -> tuple[Chart, GenerationReport]:
    """Full audio -> chart pass. Returns the chart and a report of what it did."""
    rng = random.Random(seed)
    # El genero llega crudo de `song.ini` y se normaliza con la misma tabla que
    # el atlas, para que "Thrash Metal" y "Nu-Metal" caigan en el mismo sitio.
    if genero:
        from .atlas import normalizar_genero

        profile = perfil_del_genero(profile, normalizar_genero(genero))
    tempo_map = build_tempo_map(analysis.beat_times, resolution)
    tramos_voz = tramos_de_voz(silabas or [])

    chart = Chart(resolution=resolution)
    chart.metadata = {
        "Name": "Sin titulo",
        "Artist": "Desconocido",
        "Charter": "AutoChart",
        "Album": "",
        "Year": "",
        "Offset": "0",
        "Player2": "bass",
        "Difficulty": "0",
        "PreviewStart": "0",
        "PreviewEnd": "0",
        "Genre": "",
        "MediaType": "cd",
        "MusicStream": "song.ogg",
    }
    chart.metadata.update(metadata or {})
    chart.tempos = tempo_map.events
    chart.time_signatures = [TimeSignature(0, 4, 4)]

    for section in analysis.sections:
        beat = tempo_map.time_to_beat(section.start)
        tick = max(0, tempo_map.beat_to_tick(round(beat)))
        chart.events.append((tick, f"section {section.label}"))

    report = GenerationReport(
        tempo=round(tempo_map.average_bpm, 2),
        duration=round(analysis.duration, 2),
        onsets_detected=len(analysis.onsets),
        sections=len(analysis.sections),
        tempo_events=len(tempo_map.events),
    )

    bpm = tempo_map.average_bpm
    # La ventana en la que el juego puede ensenar una nota: ni antes de que la
    # autopista haya bajado nada, ni despues de que se acabe el audio.
    first_beat = tempo_map.time_to_beat(LEAD_IN_MIN_S)
    end_beat = (
        tempo_map.time_to_beat(analysis.duration - END_MARGIN_S)
        if analysis.duration > END_MARGIN_S
        else float("inf")
    )

    # Experto primero, siempre: las demas dificultades heredan su traste.
    ordered = sorted(difficulties, key=lambda name: name != "Expert")
    expert_frets: dict[int, list[int]] = {}

    for order, difficulty in enumerate(ordered):
        spec = DIFFICULTY_SPECS[difficulty]
        candidates = quantise(analysis.onsets, tempo_map, spec.divisions)
        candidates = [c for c in candidates if first_beat <= c.beat <= end_beat]
        # El anclaje va DESPUES del recorte: si no, se crean candidatos en
        # silabas que caen fuera del tramo jugable y se tiran acto seguido.
        anclados = [c for c in anclar_silabas(candidates, silabas, tempo_map)
                    if first_beat <= c.beat <= end_beat]
        if difficulty == "Expert":
            report.onsets_quantised = len(candidates)
        target_nps = target_notes_per_second(profile, bpm, spec, density, density_percentile)
        selected = thin(anclados, tempo_map, spec, target_nps,
                        tramos_voz=tramos_voz)
        if not selected:
            report.warnings.append(f"{difficulty}: no quedaron notas tras el filtrado")
            continue

        lanes = assign_frets(selected, spec, profile, rng)
        lanes = reuse_repeated_bars(selected, lanes)
        if difficulty != "Expert":
            lanes = inherit_expert_lanes(selected, lanes, expert_frets, spec.lanes)
        notes = build_notes(
            selected, lanes, spec, tempo_map, rng,
            chord_ratio=target_ratio(profile, "chord_ratio", spec.chord_ratio, spec.chord_scale),
            sustain_ratio=target_ratio(profile, "sustain_ratio", spec.sustain_ratio, spec.sustain_scale),
            end_beat=end_beat,
        )
        if difficulty == "Expert":
            for note in notes:
                expert_frets.setdefault(note.tick, []).append(note.fret)

        # Las marcas de forzado se sortean en su PROPIA tirada de dados. Si
        # salieran de la comun, anadirlas correria el sorteo de las dificultades
        # siguientes y les cambiaria los trastes: una comparacion contra el banco
        # de ayer estaria midiendo dos cambios en vez de uno.
        flags = hopo_flags(notes, resolution, random.Random(seed + 1009 * (order + 1)))

        track = Track(difficulty=difficulty, instrument="Single", notes=notes + flags)
        track.specials = star_power_phrases(selected, tempo_map)
        chart.tracks[track.name] = track

        span = max(1e-6, tempo_map.beat_to_time(selected[-1].beat) - tempo_map.beat_to_time(selected[0].beat))
        groups: dict[int, int] = {}
        for note in notes:
            groups[note.tick] = groups.get(note.tick, 0) + 1
        report.per_difficulty[difficulty] = {
            "notas": len(groups),
            "gemas": len(notes),
            "notas_por_segundo": round(len(groups) / span, 2),
            "acordes_pct": round(100 * sum(1 for v in groups.values() if v > 1) / max(1, len(groups)), 1),
            "sostenidos_pct": round(100 * sum(1 for n in notes if n.sustain > 0) / max(1, len(notes)), 1),
            "forzadas": len(flags),
            "ligadas_pct": round(100 * hopo_ratio(track.notes, resolution), 1),
            "star_power": len(track.specials),
        }

    return chart, report
