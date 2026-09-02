"""Atlas de patrones: QUE se toca, no solo cuanto.

`corpus.py` mide *cantidades* (densidad, acordes, sostenidos). Eso basto para
que el chart generado cayera donde cae uno humano, pero no dice nada de lo que
de verdad se siente en la mano: si eso son escaleras, trinos, galopes,
martilleo de acordes o rafagas de semicorcheas. Un chart puede clavar las cuatro
medianas del corpus y aun asi sentirse a ruido, porque lo que hace que una
cancion sea divertida de tocar es su **vocabulario**, no su media.

Este modulo saca ese vocabulario y lo clasifica por:

    genero (normalizado)  x  instrumento  x  velocidad  x  dificultad

y guarda `datos/atlas_patrones.json`, que es al patron lo que
`perfil_corpus.json` es a la densidad: el criterio medido, no el gusto de nadie.

Tres decisiones que conviene saber antes de leer nada:

1. **La etiqueta de genero de `song.ini` no es de fiar.** En la biblioteca hay
   generos que dicen `M3M3S`, `Rata` y `pa acabar la fiesta siono raza`. Se
   normaliza a familias y se guarda SIEMPRE la etiqueta cruda al lado, para que
   se pueda auditar. Un patron que solo aparece en un genero mal etiquetado no
   es un hallazgo, es un error de datos.
2. **Un lick se cuenta por sus notas, no por sus veces.** Una escalera de 12
   notas y una de 3 no valen igual. Por eso ademas del recuento se guarda la
   COBERTURA: que porcentaje de las notas del chart cae dentro de algun patron
   reconocido. Un chart con cobertura baja es un chart sin vocabulario.
3. **Todo se mide en TIEMPOS, no en segundos.** Un galope a 90 BPM y otro a 200
   son el mismo gesto; en segundos parecen cosas distintas.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from . import chartio, midiio

# ---------------------------------------------------------------------------
# Familias de genero
# ---------------------------------------------------------------------------

# Se mira por subcadena y **gana la marca mas larga**, no el orden de la lista.
# Sin esa regla, `Pop/Rock` caia en "rock" solo porque la familia rock estaba
# escrita antes, y `pop/rock` (que es mas especifico) no llegaba a mirarse nunca.
# Los hibridos con guitarra (`pop rock`, `pop-rock`) van a `rock` a proposito:
# es como se TOCAN, que es lo que mide este atlas.
FAMILIAS = (
    ("metal", ("thrash", "death metal", "heavy metal", "nu-metal", "nu metal",
               "groove metal", "symphonic metal", "melodic death", "black metal",
               "progressive metal", "alternative metal", "metalcore", "metal")),
    ("punk", ("hardcore punk", "pop punk", "punk", "emo", "ska")),
    ("rock", ("classic rock", "hard rock", "psychedelic", "garage rock",
              "surf rock", "indie rock", "glam rock", "blues rock",
              "progressive rock", "instrumental rock", "alternative rock",
              "urban rock", "pop/rock", "pop-rock", "pop rock",
              "grunge", "alternative", "rock")),
    ("pop", ("dance", "electronic", "disco", "funk", "soul", "r&b", "pop")),
    ("latino", ("corrido", "cumbia", "tex-mex", "regional mexicana",
                "mexican music", "norteno", "banda", "mariachi", "salsa",
                "reggaeton", "latin")),
    ("urbano", ("hip-hop", "hip hop", "rap", "trap")),
    ("acustico", ("folk", "acoustic", "country", "blues", "relaxing", "jazz")),
)


def normalizar_genero(crudo: str) -> str:
    """Familia de genero, o 'sin_clasificar' si la etiqueta no dice nada util."""
    if not crudo:
        return "sin_clasificar"
    bajo = crudo.strip().lower()
    mejor_familia, mejor_largo = "sin_clasificar", 0
    for familia, marcas in FAMILIAS:
        for marca in marcas:
            if marca in bajo and len(marca) > mejor_largo:
                mejor_familia, mejor_largo = familia, len(marca)
    return mejor_familia


BANDAS_BPM = ((0, 100, "lenta"), (100, 140, "media"), (140, 180, "rapida"),
              (180, 10_000, "muy_rapida"))


def banda_bpm(bpm: float) -> str:
    for bajo, alto, nombre in BANDAS_BPM:
        if bajo <= bpm < alto:
            return nombre
    return "media"


# ---------------------------------------------------------------------------
# Vocabulario de patrones
# ---------------------------------------------------------------------------

# Cada patron es un gesto que la mano reconoce. Los umbrales estan en TIEMPOS.
CORCHEA = 0.5
SEMICORCHEA = 0.25

TIPOS_LICK = (
    "tremolo",            # la misma nota repetida rapido
    "trino",              # dos trastes alternandose
    "escalera_sube",      # tres o mas pasos seguidos hacia el agudo
    "escalera_baja",      # ... hacia el grave
    "zigzag",             # cambia de sentido en cada nota, mas de dos carriles
    "galope",             # larga-corta-corta, el gesto del metal
    "rafaga",             # seis o mas notas a semicorchea
    "salto_ancho",        # tres carriles o mas de un golpe
    "acorde_martillo",    # el mismo acorde repetido
    "acorde_movil",       # la misma forma de acorde desplazada
    "acorde_alterno",     # acorde / suelta / acorde / suelta
    "anclado",            # un carril se queda mientras el otro se mueve
    "abierta_bombeo",     # la abierta usada como bombo
    "sostenido_largo",    # un sostenido de dos tiempos o mas
    "cadena_sostenidos",  # tres sostenidos seguidos
    "respiro",            # cuatro tiempos o mas sin una nota
)


@dataclass
class Golpe:
    """Un golpe ya normalizado: da igual que venga de `.chart` o de `.mid`."""

    tick: int
    trastes: tuple[int, ...]
    sustain: int
    forzado: bool = False
    tap: bool = False

    @property
    def es_acorde(self) -> bool:
        return len(self.trastes) > 1

    @property
    def carril(self) -> int | None:
        """El carril de una nota suelta. None si es acorde o abierta."""
        if len(self.trastes) != 1:
            return None
        return self.trastes[0] if self.trastes[0] <= chartio.FRET_ORANGE else None

    @property
    def abierta(self) -> bool:
        return chartio.FRET_OPEN in self.trastes

    @property
    def forma(self) -> tuple[int, ...]:
        """La forma del acorde sin su posicion: (0,1) es lo mismo en G-R que en R-Y."""
        base = min(self.trastes)
        return tuple(t - base for t in self.trastes)


def _golpes_desde_notas(notas) -> list[Golpe]:
    grupos: dict[int, dict] = {}
    for nota in notas:
        fret = getattr(nota, "fret")
        entrada = grupos.setdefault(nota.tick, {"trastes": set(), "sustain": 0,
                                                "forzado": False, "tap": False})
        if fret == chartio.FLAG_FORCE:
            entrada["forzado"] = True
        elif fret == chartio.FLAG_TAP:
            entrada["tap"] = True
        else:
            entrada["trastes"].add(fret)
            entrada["sustain"] = max(entrada["sustain"], nota.sustain)
    salida = []
    for tick in sorted(grupos):
        entrada = grupos[tick]
        if not entrada["trastes"]:
            continue
        salida.append(Golpe(tick, tuple(sorted(entrada["trastes"])), entrada["sustain"],
                            entrada["forzado"], entrada["tap"]))
    return salida


def detectar_licks(golpes: list[Golpe], resolucion: int,
                   secuencia: list | None = None) -> tuple[Counter, dict[str, int], int]:
    """Recorre el chart y marca los gestos que reconoce una mano.

    Devuelve `(cuantas veces cada tipo, cuantas NOTAS cubre cada tipo, notas
    cubiertas por alguno)`. Los patrones pueden solaparse a proposito: una
    rafaga puede ser ademas una escalera, y las dos cosas son verdad.

    Si se pasa una lista en `secuencia`, se rellena con `(desde, hasta, tipo)`
    de cada gesto encontrado. **Eso es el ORDEN, que hasta ahora se tiraba.**
    Sin el orden se puede decir que gestos usa un charter, pero no cual pone
    despues de cual -- y lo segundo es lo que hace que un chart se sienta
    escrito en vez de sorteado. Es opcional para no tocar a quien ya llama a
    esto esperando tres valores.
    """
    veces: Counter[str] = Counter()
    notas_de: Counter[str] = Counter()
    cubiertas: set[int] = set()
    n = len(golpes)
    if n < 3:
        return veces, dict(notas_de), 0

    def hueco(i: int) -> float:
        """Tiempos entre el golpe i y el i+1."""
        return (golpes[i + 1].tick - golpes[i].tick) / resolucion

    def anotar(tipo: str, desde: int, hasta: int) -> None:
        veces[tipo] += 1
        notas_de[tipo] += hasta - desde + 1
        cubiertas.update(range(desde, hasta + 1))
        if secuencia is not None:
            secuencia.append((desde, hasta, tipo))

    # --- rachas de notas sueltas -------------------------------------------
    i = 0
    while i < n:
        if golpes[i].carril is None:
            i += 1
            continue
        j = i
        while (j + 1 < n and golpes[j + 1].carril is not None
               and hueco(j) <= CORCHEA + 1e-6):
            j += 1
        largo = j - i + 1
        if largo >= 3:
            carriles = [golpes[k].carril for k in range(i, j + 1)]
            pasos = [b - a for a, b in zip(carriles, carriles[1:])]
            distintos = len(set(carriles))

            if largo >= 4 and distintos == 1:
                anotar("tremolo", i, j)
            elif largo >= 4 and distintos == 2 and all(p != 0 for p in pasos) \
                    and all(a == b for a, b in zip(pasos, pasos[2:])):
                anotar("trino", i, j)

            # escaleras y zigzags: se buscan dentro de la racha
            k = 0
            while k < len(pasos):
                if pasos[k] == 0:
                    k += 1
                    continue
                m = k
                while (m + 1 < len(pasos) and pasos[m + 1] != 0
                       and (pasos[m + 1] > 0) == (pasos[k] > 0)
                       and abs(pasos[m + 1]) <= 2):
                    m += 1
                if m - k + 1 >= 3:
                    anotar("escalera_sube" if pasos[k] > 0 else "escalera_baja",
                           i + k, i + m + 1)
                k = m + 1

            if largo >= 5 and distintos >= 3:
                alternos = sum(1 for a, b in zip(pasos, pasos[1:])
                               if a * b < 0)
                if alternos >= len(pasos) - 2:
                    anotar("zigzag", i, j)

            # rafaga: seis o mas a semicorchea
            if largo >= 6 and all(hueco(k) <= SEMICORCHEA + 1e-6 for k in range(i, j)):
                anotar("rafaga", i, j)
        i = max(j, i) + 1

    # --- galope: larga-corta-corta, REPETIDO --------------------------------
    # Un solo larga-corta-corta no es un galope, es una figura suelta: aparece
    # en cualquier cancion por casualidad. El gesto que la mano reconoce como
    # galope es el mismo grupo repetido al menos dos veces seguidas.
    def es_grupo_de_galope(k: int) -> bool:
        # hueco(k + 2) mira ya el golpe k + 3: el limite es ese, no k + 2.
        if k + 3 >= n:
            return False
        a, b, c = hueco(k), hueco(k + 1), hueco(k + 2)
        if b <= 1e-6 or a > 1.0:
            return False
        return 1.7 <= a / b <= 2.4 and abs(b - c) <= b * 0.25

    i = 0
    while i < n - 5:
        if not es_grupo_de_galope(i):
            i += 1
            continue
        grupos = 1
        j = i
        while es_grupo_de_galope(j + 3) and abs(hueco(j + 3) - hueco(i)) <= hueco(i) * 0.25:
            j += 3
            grupos += 1
        if grupos >= 2:
            anotar("galope", i, min(j + 2, n - 1))
            i = j + 3
        else:
            i += 1

    # --- saltos anchos -------------------------------------------------------
    for i in range(n - 1):
        a, b = golpes[i].carril, golpes[i + 1].carril
        if a is not None and b is not None and abs(b - a) >= 3 and hueco(i) <= 1.0:
            anotar("salto_ancho", i, i + 1)

    # --- acordes -------------------------------------------------------------
    i = 0
    while i < n:
        if not golpes[i].es_acorde:
            i += 1
            continue
        j = i
        while (j + 1 < n and golpes[j + 1].es_acorde and hueco(j) <= 1.0 + 1e-6):
            j += 1
        if j - i + 1 >= 3:
            formas = [golpes[k].forma for k in range(i, j + 1)]
            bases = [min(golpes[k].trastes) for k in range(i, j + 1)]
            if len(set(formas)) == 1 and len(set(bases)) == 1:
                anotar("acorde_martillo", i, j)
            elif len(set(formas)) == 1:
                anotar("acorde_movil", i, j)
        i = max(j, i) + 1

    # --- acorde alterno y anclado -------------------------------------------
    i = 0
    while i < n - 3:
        patron = [golpes[k].es_acorde for k in range(i, min(i + 4, n))]
        if patron == [True, False, True, False] and all(hueco(k) <= CORCHEA + 1e-6
                                                        for k in range(i, i + 3)):
            j = i
            while (j + 2 < n and golpes[j + 2].es_acorde == golpes[j].es_acorde
                   and hueco(j) <= CORCHEA + 1e-6):
                j += 2
            anotar("acorde_alterno", i, min(j + 1, n - 1))
            i = j + 2
        else:
            i += 1

    for i in range(n - 1):
        a, b = golpes[i], golpes[i + 1]
        if a.es_acorde and b.es_acorde and a.trastes != b.trastes \
                and set(a.trastes) & set(b.trastes) and hueco(i) <= 1.0:
            anotar("anclado", i, i + 1)

    # --- abiertas usadas como bombo -----------------------------------------
    i = 0
    while i < n:
        if not golpes[i].abierta:
            i += 1
            continue
        j = i
        cuantas = 1
        while j + 1 < n and hueco(j) <= 1.0 + 1e-6:
            j += 1
            if golpes[j].abierta:
                cuantas += 1
        if cuantas >= 3:
            anotar("abierta_bombeo", i, j)
        i = max(j, i) + 1

    # --- sostenidos ----------------------------------------------------------
    largo_minimo = resolucion * 2
    cadena_minima = resolucion * 0.5
    for i, golpe in enumerate(golpes):
        if golpe.sustain >= largo_minimo:
            anotar("sostenido_largo", i, i)
    i = 0
    while i < n:
        if golpes[i].sustain < cadena_minima:
            i += 1
            continue
        j = i
        while j + 1 < n and golpes[j + 1].sustain >= cadena_minima and hueco(j) <= 2.0:
            j += 1
        if j - i + 1 >= 3:
            anotar("cadena_sostenidos", i, j)
        i = max(j, i) + 1

    # --- respiros ------------------------------------------------------------
    for i in range(n - 1):
        if hueco(i) >= 4.0:
            veces["respiro"] += 1

    return veces, dict(notas_de), len(cubiertas)


# ---------------------------------------------------------------------------
# Rasgos de una pista
# ---------------------------------------------------------------------------

REJILLA = (1, 2, 3, 4, 6, 8, 12, 16)
# Huecos que se reconocen como figura, en tiempos.
FIGURAS = ((0.125, "1/32"), (0.1667, "1/24"), (0.25, "1/16"), (0.3333, "1/12"),
           (0.5, "1/8"), (0.6667, "1/6"), (0.75, "1/8."), (1.0, "1/4"),
           (1.5, "1/4."), (2.0, "1/2"), (3.0, "1/2."), (4.0, "1"))


def _figura(tiempos: float) -> str:
    mejor, nombre = None, "raro"
    for valor, etiqueta in FIGURAS:
        error = abs(tiempos - valor) / max(valor, 1e-6)
        if mejor is None or error < mejor:
            mejor, nombre = error, etiqueta
    return nombre if mejor is not None and mejor <= 0.18 else "raro"


@dataclass
class RasgosPista:
    cancion: str = ""
    artista: str = ""
    charter: str = ""
    pack: str = ""
    genero_crudo: str = ""
    genero: str = ""
    anio: str = ""
    instrumento: str = ""
    dificultad: str = "Expert"
    fuente: str = ""
    bpm: float = 0.0
    banda: str = ""
    duracion_s: float = 0.0
    notas: int = 0
    nps: float = 0.0
    npb: float = 0.0
    acordes: float = 0.0
    tam_acordes: dict[int, int] = field(default_factory=dict)
    abiertas: float = 0.0
    sostenidos: float = 0.0
    repeticion: float = 0.0
    ligadas: float = 0.0
    forzadas: float = 0.0
    taps: float = 0.0
    sincopa: float = 0.0
    intervalos: dict[int, int] = field(default_factory=dict)
    figuras: dict[str, int] = field(default_factory=dict)
    posiciones: dict[str, int] = field(default_factory=dict)
    ritmo_4gramas: dict[str, int] = field(default_factory=dict)
    forma_3gramas: dict[str, int] = field(default_factory=dict)
    licks: dict[str, int] = field(default_factory=dict)
    licks_notas: dict[str, int] = field(default_factory=dict)
    cobertura: float = 0.0
    curva: list[float] = field(default_factory=list)
    contraste: float = 0.0   # pico / valle de densidad: cuanto respira la cancion
    # Las dos que sustituyen al contraste para elegir el corpus de oro, porque
    # el contraste resulto ser un artefacto: mide max/min de doce tramos, o sea
    # dos puntos sueltos, y como el minimo va en el divisor, **una zona casi
    # vacia dispara la nota**. Medido sobre 392 pistas: correlacion +0.60 entre
    # contraste y tramos casi muertos, y el 55 % de la biblioteca se mueve mas
    # de 50 puestos si la medida no depende de los extremos.
    variacion: float = 0.0        # desviacion/media de la curva: dinamica real
    tramos_muertos: float = 0.0   # fraccion de tramos por debajo del 25 % de la mediana
    # Los gestos EN ORDEN, `(desde, hasta, tipo)`. No se agrega ni se guarda en
    # el atlas: se usa en vivo para minar que gesto sigue a cual.
    secuencia_licks: list = field(default_factory=list)


def medir_pista(
    golpes: list[Golpe],
    resolucion: int,
    tick_a_segundos,
    bpm: float,
) -> RasgosPista:
    rasgos = RasgosPista(bpm=bpm, banda=banda_bpm(bpm))
    if len(golpes) < 16:
        return rasgos

    primero = tick_a_segundos(golpes[0].tick)
    ultimo = tick_a_segundos(golpes[-1].tick)
    rasgos.duracion_s = max(1e-6, ultimo - primero)
    rasgos.notas = len(golpes)
    rasgos.nps = rasgos.notas / rasgos.duracion_s
    rasgos.npb = rasgos.nps * 60.0 / max(bpm, 1.0)

    acordes = sum(1 for g in golpes if g.es_acorde)
    rasgos.acordes = acordes / len(golpes)
    rasgos.tam_acordes = dict(Counter(len(g.trastes) for g in golpes))
    rasgos.abiertas = sum(1 for g in golpes if g.abierta) / len(golpes)
    rasgos.sostenidos = sum(1 for g in golpes
                            if g.sustain >= resolucion * chartio.SOSTENIDO_MIN_TIEMPOS) / len(golpes)
    rasgos.forzadas = sum(1 for g in golpes if g.forzado) / len(golpes)
    rasgos.taps = sum(1 for g in golpes if g.tap) / len(golpes)

    grupos = [chartio.NoteGroup(g.tick, g.trastes, g.forzado, g.tap) for g in golpes]
    umbral = chartio.hopo_distance(resolucion)
    ligadas = 0
    anterior = None
    for grupo in grupos:
        natural = chartio.is_natural_hopo(anterior, grupo, umbral)
        ligadas += int(grupo.tap or (natural != grupo.forced))
        anterior = grupo
    rasgos.ligadas = ligadas / len(grupos)

    sueltas = [(g.tick, g.carril) for g in golpes if g.carril is not None]
    intervalos: Counter[int] = Counter()
    repeticiones = 0
    for (_, a), (_, b) in zip(sueltas, sueltas[1:]):
        intervalos[b - a] += 1
        repeticiones += int(a == b)
    rasgos.intervalos = dict(intervalos)
    rasgos.repeticion = repeticiones / max(1, len(sueltas) - 1)

    formas: Counter[str] = Counter()
    for (_, a), (_, b), (_, c) in zip(sueltas, sueltas[1:], sueltas[2:]):
        formas[f"{b - a:+d},{c - b:+d}"] += 1
    rasgos.forma_3gramas = dict(formas.most_common(40))

    figuras: Counter[str] = Counter()
    huecos: list[str] = []
    for a, b in zip(golpes, golpes[1:]):
        figura = _figura((b.tick - a.tick) / resolucion)
        figuras[figura] += 1
        huecos.append(figura)
    rasgos.figuras = dict(figuras)

    # Donde cae la nota DENTRO del tiempo. No es lo mismo tocar rapido que
    # tocar a contratiempo: lo primero cansa, lo segundo es lo que baila.
    posiciones: Counter[str] = Counter()
    for golpe in golpes:
        r = (golpe.tick % resolucion) / resolucion
        if min(r, 1 - r) <= 0.06:
            posiciones["pulso"] += 1
        elif abs(r - 0.5) <= 0.06:
            posiciones["contratiempo"] += 1
        elif min(abs(r - 0.25), abs(r - 0.75)) <= 0.06:
            posiciones["semicorchea"] += 1
        elif min(abs(r - 1 / 3), abs(r - 2 / 3)) <= 0.05:
            posiciones["tresillo"] += 1
        else:
            posiciones["fuera"] += 1
    rasgos.posiciones = dict(posiciones)
    rasgos.sincopa = posiciones["contratiempo"] / len(golpes)

    ritmos: Counter[str] = Counter()
    for cuatro in zip(huecos, huecos[1:], huecos[2:], huecos[3:]):
        if "raro" not in cuatro:
            ritmos[" ".join(cuatro)] += 1
    rasgos.ritmo_4gramas = dict(ritmos.most_common(40))

    secuencia: list = []
    veces, notas_de, cubiertas = detectar_licks(golpes, resolucion, secuencia)
    secuencia.sort(key=lambda t: (t[0], t[1]))
    rasgos.secuencia_licks = secuencia
    rasgos.licks = dict(veces)
    rasgos.licks_notas = notas_de
    rasgos.cobertura = cubiertas / len(golpes)

    # curva de densidad en 12 tramos: como se reparte el esfuerzo
    tramos = 12
    curva = []
    for t in range(tramos):
        desde = primero + rasgos.duracion_s * t / tramos
        hasta = primero + rasgos.duracion_s * (t + 1) / tramos
        cuantas = sum(1 for g in golpes if desde <= tick_a_segundos(g.tick) < hasta)
        curva.append(round(cuantas / max(1e-6, hasta - desde), 2))
    rasgos.curva = curva
    vivos = [c for c in curva if c > 0]
    rasgos.contraste = round(max(curva) / max(0.1, min(vivos) if vivos else 0.1), 2)
    if vivos:
        media = sum(curva) / len(curva)
        mediana_viva = sorted(vivos)[len(vivos) // 2]
        varianza = sum((c - media) ** 2 for c in curva) / len(curva)
        rasgos.variacion = round(varianza ** 0.5 / max(0.01, media), 3)
        rasgos.tramos_muertos = round(
            sum(1 for c in curva if c < 0.25 * mediana_viva) / len(curva), 3)
    return rasgos


# ---------------------------------------------------------------------------
# Lectura de una carpeta
# ---------------------------------------------------------------------------

INSTRUMENTOS_CHART = {
    "Single": "guitarra",
    "DoubleGuitar": "guitarra_coop",
    "DoubleBass": "bajo",
    "DoubleRhythm": "ritmica",
    "Keyboard": "teclado",
}


def analizar_carpeta(carpeta: Path, dificultades=("Expert",)) -> list[RasgosPista]:
    """Mide todas las pistas de 5 trastes de una cancion."""
    from .export import read_song_ini

    info = read_song_ini(carpeta)
    salida: list[RasgosPista] = []

    def sellar(rasgos: RasgosPista, instrumento: str, dificultad: str, fuente: str) -> None:
        rasgos.cancion = carpeta.name
        rasgos.artista = info.get("artist", "")
        rasgos.charter = info.get("charter", "")
        rasgos.genero_crudo = info.get("genre", "")
        rasgos.genero = normalizar_genero(rasgos.genero_crudo)
        rasgos.anio = info.get("year", "")
        rasgos.instrumento = instrumento
        rasgos.dificultad = dificultad
        rasgos.fuente = fuente
        salida.append(rasgos)

    chart_path = carpeta / "notes.chart"
    mid_path = carpeta / "notes.mid"

    if chart_path.is_file():
        chart = chartio.parse_chart(chart_path)
        bpm = _mediana([t.bpm for t in chart.tempos] or [120.0])
        for nombre, track in chart.tracks.items():
            dificultad = next((d for d in chartio.DIFFICULTIES if nombre.startswith(d)), "")
            instrumento = INSTRUMENTOS_CHART.get(nombre[len(dificultad):])
            if instrumento is None or dificultad not in dificultades:
                continue
            golpes = _golpes_desde_notas(track.notes)
            rasgos = medir_pista(golpes, chart.resolution, chart.tick_to_seconds, bpm)
            if rasgos.notas:
                sellar(rasgos, instrumento, dificultad, "chart")
        if salida:
            return salida

    if mid_path.is_file():
        chart, pistas = midiio.parse_midi_multi(mid_path)
        bpm = _mediana([b for _, b in chart.tempos] or [120.0])
        for instrumento, por_dificultad in pistas.items():
            for dificultad, notas in por_dificultad.items():
                if dificultad not in dificultades:
                    continue
                golpes = _golpes_desde_notas(notas)
                rasgos = medir_pista(golpes, chart.resolution, chart.tick_to_seconds, bpm)
                if rasgos.notas:
                    sellar(rasgos, instrumento, dificultad, "midi")
    return salida


def _mediana(valores: list[float]) -> float:
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    mitad = len(ordenados) // 2
    if len(ordenados) % 2:
        return ordenados[mitad]
    return (ordenados[mitad - 1] + ordenados[mitad]) / 2.0


def escanear(songs_dir: str | Path, dificultades=("Expert",), al_progresar=None) -> list[RasgosPista]:
    raiz = Path(songs_dir)
    carpetas = sorted({p.parent for patron in ("**/notes.chart", "**/notes.mid")
                       for p in raiz.glob(patron)})
    salida: list[RasgosPista] = []
    # Un chart que revienta no puede desaparecer en silencio: durante semanas un
    # desbordamiento tiraba 35 charts enteros y el unico sintoma era un total mas
    # bajo. Se cuentan y se devuelven en `escanear.fallos`.
    fallos: list[tuple[str, str]] = []
    for indice, carpeta in enumerate(carpetas, 1):
        try:
            pistas = analizar_carpeta(carpeta, dificultades)
        except Exception as error:
            pistas = []
            fallos.append((carpeta.name, f"{type(error).__name__}: {error}"))
        try:
            rel = carpeta.relative_to(raiz).parts
            pack = rel[0] if rel else ""
        except ValueError:
            pack = ""
        for rasgos in pistas:
            rasgos.pack = pack
        salida.extend(pistas)
        if al_progresar is not None:
            al_progresar(indice, len(carpetas), carpeta.name, len(pistas))
    escanear.fallos = fallos
    return salida


# ---------------------------------------------------------------------------
# Agregacion
# ---------------------------------------------------------------------------


def _percentiles(valores: list[float], puntos=(5, 25, 50, 75, 95)) -> dict[str, float]:
    if not valores:
        return {f"p{p}": 0.0 for p in puntos}
    ordenados = sorted(valores)
    salida = {}
    for punto in puntos:
        indice = min(len(ordenados) - 1, max(0, int(round((punto / 100.0) * (len(ordenados) - 1)))))
        salida[f"p{punto}"] = round(float(ordenados[indice]), 4)
    return salida


def _mezclar(dicts: list[dict], top: int | None = None) -> dict[str, float]:
    total: Counter[str] = Counter()
    for item in dicts:
        for clave, cuenta in item.items():
            total[str(clave)] += cuenta
    grande = sum(total.values()) or 1
    pares = total.most_common(top) if top else total.most_common()
    return {clave: round(cuenta / grande, 5) for clave, cuenta in pares}


def _resumen(grupo: list[RasgosPista]) -> dict:
    """Lo que define a un grupo: cuanto, que vocabulario, y como respira."""
    notas_totales = sum(r.notas for r in grupo) or 1
    licks_por_100 = {
        tipo: round(sum(r.licks.get(tipo, 0) for r in grupo) / notas_totales * 100, 3)
        for tipo in TIPOS_LICK
    }
    licks_cobertura = {
        tipo: round(sum(r.licks_notas.get(tipo, 0) for r in grupo) / notas_totales, 4)
        for tipo in TIPOS_LICK
    }
    return {
        "pistas": len(grupo),
        "canciones": len({r.cancion for r in grupo}),
        "notas": sum(r.notas for r in grupo),
        "bpm": _percentiles([r.bpm for r in grupo]),
        "nps": _percentiles([r.nps for r in grupo]),
        "npb": _percentiles([r.npb for r in grupo]),
        "acordes": _percentiles([r.acordes for r in grupo]),
        "abiertas": _percentiles([r.abiertas for r in grupo]),
        "sostenidos": _percentiles([r.sostenidos for r in grupo]),
        "repeticion": _percentiles([r.repeticion for r in grupo]),
        "ligadas": _percentiles([r.ligadas for r in grupo]),
        "sincopa": _percentiles([r.sincopa for r in grupo]),
        "cobertura_licks": _percentiles([r.cobertura for r in grupo]),
        "contraste": _percentiles([r.contraste for r in grupo]),
        "variacion": _percentiles([r.variacion for r in grupo]),
        "tramos_muertos": _percentiles([r.tramos_muertos for r in grupo]),
        "licks_por_100_notas": licks_por_100,
        "licks_cobertura": licks_cobertura,
        "figuras": _mezclar([r.figuras for r in grupo], 12),
        "posiciones": _mezclar([r.posiciones for r in grupo]),
        "intervalos": _mezclar([r.intervalos for r in grupo], 11),
        "ritmo_4gramas": _mezclar([r.ritmo_4gramas for r in grupo], 15),
        "forma_3gramas": _mezclar([r.forma_3gramas for r in grupo], 15),
        "tam_acordes": _mezclar([r.tam_acordes for r in grupo]),
    }


MINIMO_POR_GRUPO = 4


def agregar(rasgos: list[RasgosPista]) -> dict:
    usables = [r for r in rasgos if r.notas >= 32 and 30 <= r.bpm <= 400]
    atlas: dict = {
        "pistas_analizadas": len(usables),
        "pistas_leidas": len(rasgos),
        "global": _resumen(usables),
        "por_instrumento": {},
        "por_genero": {},
        "por_genero_instrumento": {},
        "por_velocidad": {},
        "por_pack": {},
        "por_dificultad": {},
        "generos_crudos": {},
    }

    crudos: Counter[str] = Counter()
    for r in usables:
        crudos[f"{r.genero} <- {r.genero_crudo or '(vacio)'}"] += 1
    atlas["generos_crudos"] = dict(crudos.most_common(60))

    def agrupar(clave: str, funcion) -> None:
        cubos: dict[str, list[RasgosPista]] = {}
        for r in usables:
            cubos.setdefault(funcion(r), []).append(r)
        atlas[clave] = {
            nombre: _resumen(grupo)
            for nombre, grupo in sorted(cubos.items())
            if len(grupo) >= MINIMO_POR_GRUPO
        }

    agrupar("por_instrumento", lambda r: r.instrumento)
    agrupar("por_genero", lambda r: r.genero)
    agrupar("por_velocidad", lambda r: r.banda)
    agrupar("por_pack", lambda r: r.pack)
    agrupar("por_dificultad", lambda r: r.dificultad)
    agrupar("por_genero_instrumento", lambda r: f"{r.genero}/{r.instrumento}")
    return atlas


def guardar(atlas: dict, path: str | Path) -> Path:
    destino = Path(path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(atlas, indent=2, ensure_ascii=False), encoding="utf-8")
    return destino


def cargar(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
