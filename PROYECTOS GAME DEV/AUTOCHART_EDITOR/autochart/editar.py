"""Editar un chart que ya existe, sin volver a generarlo.

El generador escribe charts enteros. Esto es lo otro: coger uno que ya esta
hecho -- nuestro o de quien sea -- y arreglarle una parte.

    autochart alinear <carpeta>                que rejilla tiene de verdad
    autochart alinear <carpeta> --division 4   y pegarlo a ella

**Aqui no se genera nada.** Este modulo solo mueve, borra y pega notas que ya
existen; si hace falta inventarse una nota, eso es del generador.

La primera herramienta es la rejilla, porque es la queja mas barata de arreglar:
un chart con el tempo mal puesto tiene las notas bien de ORDEN y mal de SITIO, y
pegarlas a la subdivision mas cercana lo deja jugable sin tocar nada mas. Es lo
mismo que hace el "Grid Snap" de Editor on Fire cuando grabas tocando.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import chartio
from .chartio import Chart, Note

# Las subdivisiones que tiene sentido probar, en golpes por tiempo. La rejilla
# de un chart de guitarra vive casi siempre en una de estas: negra, corchea,
# tresillo de corchea, semicorchea, tresillo de semicorchea y fusa.
DIVISIONES = (1, 2, 3, 4, 6, 8)


@dataclass
class Desvio:
    """Cuanto se aparta un chart de una rejilla concreta."""

    division: int
    p50_ticks: float          # desvio mediano a la posicion mas cercana
    p95_ticks: float
    encajan: float            # fraccion de golpes que ya caen clavados
    golpes: int

    @property
    def p50_fraccion(self) -> float:
        """El desvio mediano, en fraccion de la propia subdivision."""
        return self.p50_ticks / self.paso if self.paso else 0.0

    paso: float = 0.0         # ticks que mide una subdivision


@dataclass
class InformeAlinear:
    pista: str = ""
    division: int = 0
    golpes: int = 0
    movidos: int = 0
    chocan: int = 0           # se quedaron donde estaban: el sitio ya estaba cogido
    desvio_p50_ms: float = 0.0
    desvio_max_ms: float = 0.0
    avisos: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.chocan


def _paso(resolution: int, division: int) -> float:
    """Ticks que mide una subdivision. Puede no ser entero (tresillos)."""
    return resolution / float(division)


def _ticks_de_golpes(track_notes: list[Note]) -> list[int]:
    """Los ticks donde hay un golpe de verdad, sin contar las marcas sueltas."""
    return sorted({n.tick for n in track_notes if not n.is_flag})


def medir_rejilla(chart: Chart, pista: str = "ExpertSingle") -> list[Desvio]:
    """En que subdivision vive este chart, medido y no supuesto.

    Para cada division se mira a que distancia esta cada golpe de su posicion
    mas cercana. La buena es la que deja el desvio pequeno CON pocas divisiones:
    una rejilla de fusas siempre encaja mejor que una de negras, asi que el
    numero que hay que leer es el desvio en fraccion de la propia subdivision.
    """
    track = chart.tracks.get(pista)
    if track is None:
        return []
    ticks = _ticks_de_golpes(track.notes)
    if len(ticks) < 8:
        return []

    salida: list[Desvio] = []
    for division in DIVISIONES:
        paso = _paso(chart.resolution, division)
        desvios = []
        clavados = 0
        for tick in ticks:
            resto = tick % paso
            d = min(resto, paso - resto)
            desvios.append(d)
            if d <= 1e-6:
                clavados += 1
        desvios.sort()
        salida.append(Desvio(
            division=division,
            p50_ticks=desvios[len(desvios) // 2],
            p95_ticks=desvios[min(len(desvios) - 1, int(0.95 * len(desvios)))],
            encajan=clavados / len(ticks),
            golpes=len(ticks),
            paso=paso,
        ))
    return salida


ENCAJAN_MINIMO = 0.90


def mejor_division(desvios: list[Desvio]) -> int | None:
    """La rejilla mas GRUESA donde ya cae casi todo el chart.

    Manda `encajan`, no el desvio mediano. Con la mediana se elige mal: en un
    chart nuestro medido el 24-08-2026, 1/2 daba desvio mediano 0.0 y aun asi
    solo el 69.3 % de los golpes caia ahi -- la mediana en cero solo dice que
    mas de la mitad encaja. Con `encajan` sale 1/4, que es la de verdad (97.4 %).

    Y de gruesa a fina, porque una rejilla de fusas SIEMPRE encaja mejor: coger
    la que menos desvio deja seria coger siempre la mas fina, que no dice nada.
    """
    for d in desvios:
        if d.encajan >= ENCAJAN_MINIMO:
            return d.division
    return None


@dataclass
class Tempo:
    """Que factor de tempo hace encajar el chart, si es que hay uno."""

    factor: float          # 1.0 = el tempo escrito ya es el bueno
    concentracion: float   # que fraccion de golpes cae en fase con ese factor
    ahora: float           # la misma medida con el tempo tal como esta
    division: int

    @property
    def esta_mal(self) -> bool:
        """Hay OTRO tempo que explica el chart mucho mejor que el escrito."""
        return abs(self.factor - 1.0) > 0.004 and self.concentracion - self.ahora >= 0.20


def _concentracion(ticks: list[int], paso: float, factor: float, tol: float) -> float:
    """Que fraccion de los golpes cae en la MISMA fase de la rejilla.

    No mira si caen en el sitio, sino si caen todos en el mismo sitio relativo:
    un chart entero corrido medio tiempo esta perfecto, solo mal colocado. Por
    eso se busca la fase mas poblada en vez de exigir resto cero.
    """
    if not ticks:
        return 0.0
    cubos = 64
    hist = [0] * cubos
    for tick in ticks:
        fase = (tick * factor) % paso / paso
        hist[int(fase * cubos) % cubos] += 1
    ancho = max(1, int(tol / paso * cubos))
    mejor = 0
    for centro in range(cubos):
        dentro = sum(hist[(centro + k) % cubos] for k in range(-ancho, ancho + 1))
        mejor = max(mejor, dentro)
    return mejor / len(ticks)


def _en_rejilla(ticks: list[int], paso: float, tol: float) -> float:
    """Que fraccion cae en la rejilla DE VERDAD, con la fase en cero.

    La hermana de `_concentracion` y su contraria: aquella busca la fase mas
    poblada sea cual sea (y por eso sirve para el tempo y NO para la latencia),
    esta exige caer donde manda la rejilla.
    """
    if not ticks:
        return 0.0
    dentro = 0
    for tick in ticks:
        resto = tick % paso
        if min(resto, paso - resto) <= tol:
            dentro += 1
    return dentro / len(ticks)


def buscar_tempo(chart: Chart, division: int, pista: str = "ExpertSingle",
                 rango: float = 0.20, paso_busqueda: float = 0.0005) -> Tempo | None:
    """Distinguir el TEMBLOR de un TEMPO equivocado, y dar el factor que lo arregla.

    Son dos averias que se confunden y el arreglo no es el mismo:

    * **Temblor:** las notas bailan alrededor de su sitio. Encajan mal, pero
      **en fase**: la rejilla es la buena y solo hay que pegarlas. Eso lo arregla
      `alinear`.
    * **Tempo equivocado:** la rejilla y la musica van a velocidades distintas,
      asi que la fase GIRA a lo largo de la cancion. Alinear ahi no arregla nada
      -- pega las notas a una rejilla que tampoco es la buena.

    Lo que NO sirve para distinguirlas, medido el 24-08-2026: mirar si encaja
    mejor al principio que al final. Un tempo estirado un 3 % encaja mal desde el
    primer compas (2 % al principio y 3 % al final), asi que esa comprobacion deja
    pasar justo el caso que buscaba.

    Lo que si sirve es probar factores: si hay uno distinto de 1 que concentra
    mucho mejor los golpes, el tempo escrito no es el de la cancion -- y ese
    factor **es el arreglo**, no solo el diagnostico.
    """
    track = chart.tracks.get(pista)
    if track is None:
        return None
    ticks = _ticks_de_golpes(track.notes)
    if len(ticks) < 24:
        return None

    paso = _paso(chart.resolution, division)
    tol = paso * 0.05
    ahora = _concentracion(ticks, paso, 1.0, tol)

    mejor_factor, mejor_conc = 1.0, ahora
    pasos = int(rango / paso_busqueda)
    for k in range(-pasos, pasos + 1):
        factor = 1.0 + k * paso_busqueda
        if factor <= 0:
            continue
        conc = _concentracion(ticks, paso, factor, tol)
        if conc > mejor_conc + 1e-9:
            mejor_factor, mejor_conc = factor, conc
    return Tempo(factor=mejor_factor, concentracion=mejor_conc, ahora=ahora, division=division)


def reescalar(chart: Chart, factor: float, pista: str | None = None) -> int:
    """Estirar o encoger el chart entero por `factor`. Devuelve golpes tocados.

    Es lo que arregla un tempo mal puesto: las notas estan en el orden bueno y en
    el sitio malo, y todas por el mismo motivo. Se tocan TODAS las pistas por
    defecto, porque un chart con Experto estirado y Facil no lo esta ya no es el
    mismo chart.
    """
    tocados = 0
    for nombre, track in chart.tracks.items():
        if pista is not None and nombre != pista:
            continue
        for nota in track.notes:
            nota.tick = int(round(nota.tick * factor))
            nota.sustain = int(round(nota.sustain * factor))
            tocados += 1
        track.notes.sort(key=lambda n: (n.tick, n.fret))
        for frase in track.specials:
            frase.tick = int(round(frase.tick * factor))
            frase.length = int(round(frase.length * factor))
    return tocados


def alinear(chart: Chart, division: int, pista: str = "ExpertSingle",
            desde_tick: int | None = None, hasta_tick: int | None = None) -> InformeAlinear:
    """Pegar los golpes a la subdivision mas cercana. Cambia `chart` en el sitio.

    Dos cosas que NO hace, a proposito:

    * **No junta dos golpes en uno.** Si al pegarlo caeria encima de otro que ya
      estaba, se queda donde esta y se cuenta en `chocan`. Fusionarlos cambiaria
      el chart de verdad -- dos acordes distintos pasarian a ser uno -- y eso no
      es alinear, es reescribir. Si salen muchos choques, la division es
      demasiado gruesa para ese chart y hay que bajarla.
    * **No toca las marcas huerfanas.** Una marca (`N 5`, `N 6`) viaja con su
      nota porque comparten tick, y se mueven las dos juntas.

    El sostenido se mueve entero: se pega el principio y el final por separado,
    asi que un sostenido que iba de corchea a corchea sigue yendo de corchea a
    corchea. Nunca queda negativo.
    """
    informe = InformeAlinear(pista=pista, division=division)
    track = chart.tracks.get(pista)
    if track is None:
        informe.avisos.append(f"no hay pista {pista}")
        return informe
    if division <= 0:
        informe.avisos.append("la division tiene que ser 1 o mas")
        return informe

    paso = _paso(chart.resolution, division)
    ticks = _ticks_de_golpes(track.notes)
    informe.golpes = len(ticks)
    if not ticks:
        return informe

    en_rango = [t for t in ticks
                if (desde_tick is None or t >= desde_tick)
                and (hasta_tick is None or t <= hasta_tick)]
    fuera = {t for t in ticks if t not in set(en_rango)}

    # A donde iria cada tick. Se resuelve TODO antes de mover nada, porque un
    # movimiento no puede depender de si otro ya se hizo.
    destino: dict[int, int] = {}
    ocupados = set(fuera)
    for tick in sorted(en_rango, key=lambda t: (min(t % paso, paso - t % paso), t)):
        nuevo = int(round(tick / paso) * paso)
        if nuevo != tick and nuevo in ocupados:
            informe.chocan += 1
            nuevo = tick
        destino[tick] = nuevo
        ocupados.add(nuevo)

    segundos = chart.tick_to_seconds
    desvios_ms = []
    for nota in track.notes:
        nuevo = destino.get(nota.tick)
        if nuevo is None or nuevo == nota.tick:
            continue
        if not nota.is_flag:
            desvios_ms.append(abs(segundos(nuevo) - segundos(nota.tick)) * 1000.0)
        if nota.sustain > 0:
            fin = int(round((nota.tick + nota.sustain) / paso) * paso)
            nota.sustain = max(0, fin - nuevo)
        nota.tick = nuevo

    informe.movidos = sum(1 for t, n in destino.items() if t != n)
    if desvios_ms:
        desvios_ms.sort()
        informe.desvio_p50_ms = desvios_ms[len(desvios_ms) // 2]
        informe.desvio_max_ms = desvios_ms[-1]
    if informe.chocan:
        informe.avisos.append(
            f"{informe.chocan} golpes se quedaron donde estaban porque el sitio ya "
            f"estaba cogido: 1/{division} es demasiado gruesa para este chart")
    track.notes.sort(key=lambda n: (n.tick, n.fret))
    return informe


def alinear_carpeta(carpeta: str | Path, division: int | None = None,
                    pista: str = "ExpertSingle", probar: bool = False,
                    destino: str | Path | None = None) -> tuple[InformeAlinear, list[Desvio]]:
    """Leer, alinear y escribir. Con `probar` no escribe nada.

    Sin `division` se mide la rejilla y se usa la mas gruesa que ya explique el
    chart: alinear a una rejilla que no es la suya lo estropea en vez de
    arreglarlo.
    """
    ruta = Path(carpeta)
    if ruta.is_dir():
        ruta = ruta / "notes.chart"
    chart = chartio.parse_chart(ruta)
    desvios = medir_rejilla(chart, pista)
    if division is None:
        division = mejor_division(desvios)
        if division is None:
            informe = InformeAlinear(pista=pista)
            informe.avisos.append(
                "ninguna rejilla de 1 a 8 explica este chart: o el tempo esta muy "
                "mal o las notas no van a compas. Elige la division a mano.")
            return informe, desvios
    tempo = buscar_tempo(chart, division, pista)
    informe = alinear(chart, division, pista)
    if tempo is not None and tempo.esta_mal:
        informe.avisos.append(
            f"OJO: esto no es temblor. Con el tempo escrito los golpes caen en fase el "
            f"{100*tempo.ahora:.0f} % de las veces, y estirando el chart por "
            f"{tempo.factor:.4f} suben al {100*tempo.concentracion:.0f} %. El TEMPO no es "
            f"el de la cancion, y alinear no lo arregla: primero `--tempo {tempo.factor:.4f}`.")
    if not probar and informe.golpes:
        chartio.write_chart(chart, Path(destino) if destino else ruta)
    return informe, desvios


# ---------------------------------------------------------------------------
# Grabar tocando, y sobrescribir solo un tramo
# ---------------------------------------------------------------------------


@dataclass
class InformeGrabar:
    toques: int = 0
    notas: int = 0
    desfase_ms: float = 0.0      # la latencia que se le quito a lo tocado
    desfase_automatico: bool = False
    en_fase: float = 0.0         # que fraccion cae en la rejilla ya corregida
    avisos: list[str] = field(default_factory=list)


## Cuanto se busca a cada lado al adivinar la latencia, y con que finura.
## +-300 ms cubre de sobra lo que tarda un equipo en sacar el sonido y lo que
## tarda una mano en llegar; 5 ms es mas fino que la propia rejilla mas corta
## (una semicorchea a 190 BPM son 79 ms).
DESFASE_BUSQUEDA_MS = 300.0
DESFASE_PASO_MS = 5.0
## Dos desfases que concentran dentro de esto se consideran empatados, y entre
## empatados gana el mas cercano a cero. No es un umbral de gusto: es que la
## ambiguedad es de una subdivision entera, y de todas las respuestas igual de
## buenas la unica fisicamente creible es la pequenia.
DESFASE_EMPATE = 0.02


def adivinar_desfase(toques: list[tuple[float, int]], chart: Chart,
                     division: int) -> tuple[float, float]:
    """Cuanta latencia hay entre lo que sono y lo que se toco. `(ms, en_fase)`.

    **Grabar tocando siempre trae un desfase constante** y no es culpa de nadie:
    el equipo tarda en sacar el sonido, la mano tarda en llegar, y las dos cosas
    suman siempre lo mismo. Si no se quita, TODAS las notas quedan corridas y el
    chart parece mal tocado cuando lo que esta mal es el reloj.

    No hace falta pedirle al que toca que lo calibre: la latencia es la que deja
    los golpes MAS en fase con la rejilla, y eso se mide igual que el tempo --
    con `_concentracion`, que ya existe para lo mismo. Se prueba de -300 a
    +300 ms y gana el que mas concentra.

    ## ⚠️ ESTO SOLO ARREGLA EL RESTO, NO LA LATENCIA ENTERA. Y no es una
    limitacion de esta funcion: **desde la fase, la latencia es indistinguible
    modulo una subdivision**, siempre. Correr un chart una semicorchea entera lo
    deja EXACTAMENTE igual de en fase, asi que ninguna medida de fase puede
    decidir entre las dos. Medido el 24-08-2026 sobre 200 notas tocadas 80 ms
    tarde: el buscador devolvia -180 ms, que es el mismo sitio dos semicorcheas
    mas alla (125 ms cada una a 120 BPM), y con el desempate hacia cero devolvia
    0 ms -- las dos respuestas igual de validas para la fase y las dos dejando el
    chart corrido.

    Por eso los editores que graban tocando -- EOF incluido -- **piden calibrar
    la latencia una vez** en vez de adivinarla. Aqui igual: `desfase_ms` se pasa,
    y esto solo afina el resto dentro de +-media subdivision, que es el unico
    tramo donde la respuesta es unica.

    Ojo con la trampa de siempre: esto es honesto **si hay golpes suficientes**.
    Con cuatro notas cualquier desfase concentra igual de bien, asi que por
    debajo de 24 se devuelve 0 y se dice.
    """
    if len(toques) < 24:
        return (0.0, 0.0)
    ## ⚠️ Y NO se puede usar `_concentracion` aqui, aunque lo parezca. Esa mide
    ## la fase MAS POBLADA sea cual sea, o sea que es invariante al corrimiento a
    ## proposito -- se hizo para el tempo, donde el desplazamiento hay que
    ## ignorarlo. Da exactamente lo mismo para cualquier latencia, asi que
    ## buscando con ella salia el borde del rango (60 ms cuando el resto era 30).
    ## Para una latencia hace falta la medida contraria: cuantos caen en la
    ## rejilla DE VERDAD, con la fase en cero.
    paso = _paso(chart.resolution, division)
    tol = paso * 0.05
    ## El tramo donde la respuesta es unica: media subdivision a cada lado.
    media_sub_ms = 1000.0 * (chart.tick_to_seconds(int(round(paso))) - chart.tick_to_seconds(0)) / 2.0
    pasos = max(1, int(media_sub_ms / DESFASE_PASO_MS))
    mejor_ms, mejor_enc = 0.0, -1.0
    for k in range(-pasos, pasos + 1):
        ms = k * DESFASE_PASO_MS
        ticks = [chart.seconds_to_tick(max(0.0, t + ms / 1000.0)) for t, _ in toques]
        enc = _en_rejilla(ticks, paso, tol)
        if enc > mejor_enc + 1e-9 or (abs(enc - mejor_enc) <= DESFASE_EMPATE
                                      and abs(ms) < abs(mejor_ms)):
            mejor_ms, mejor_enc = ms, enc
    return (mejor_ms, mejor_enc)


def desde_toques(toques: list[tuple[float, int]], chart: Chart, division: int = 4,
                 desfase_ms: float | None = None,
                 sostenido_min_s: float = 0.0) -> tuple[list[Note], InformeGrabar]:
    """Convertir lo que alguien TOCO en notas de chart, pegadas a la rejilla.

    `toques` son pares `(segundo, carril)` tal como llegaron del teclado o del
    mando: sin cuantizar, con la latencia dentro y con el temblor de una mano.
    Aqui se les quita el desfase, se pasan a ticks y se pegan a la subdivision.

    **No se inventa ni una nota.** Si dos toques caen en el mismo sitio de la
    rejilla y en el mismo carril, se quedan en uno -- eso no es fusionar acordes
    (que `alinear` se niega a hacer), es que la mano dio dos veces dentro de la
    misma semicorchea y el juego solo puede leer una.
    """
    informe = InformeGrabar(toques=len(toques))
    if not toques:
        return ([], informe)

    if desfase_ms is None:
        desfase_ms, en_fase = adivinar_desfase(toques, chart, division)
        informe.desfase_automatico = True
        informe.en_fase = en_fase
        if len(toques) < 24:
            informe.avisos.append(
                f"solo {len(toques)} toques: son pocos para adivinar la latencia, "
                f"asi que se deja en 0. Ponla a mano si sabes cual es.")
    informe.desfase_ms = desfase_ms

    paso = _paso(chart.resolution, division)
    vistos: set[tuple[int, int]] = set()
    notas: list[Note] = []
    for segundo, carril in sorted(toques):
        tick_crudo = chart.seconds_to_tick(max(0.0, segundo + desfase_ms / 1000.0))
        tick = int(round(tick_crudo / paso) * paso)
        clave = (tick, int(carril))
        if clave in vistos:
            continue
        vistos.add(clave)
        notas.append(Note(tick, int(carril), 0))
    notas.sort(key=lambda n: (n.tick, n.fret))
    informe.notas = len(notas)
    return (notas, informe)


def sustituir_tramo(chart: Chart, notas_nuevas: list[Note], desde_tick: int,
                    hasta_tick: int, pista: str = "ExpertSingle") -> InformeAlinear:
    """Cambiar SOLO un tramo del chart y dejar el resto intacto.

    Es lo que se pide cuando un chart quedo bien pero hay un trozo que no: se
    vuelve a tocar ese trozo y se pega encima, sin volver a generar nada.

    Lo que se borra son los golpes del tramo **y sus marcas**, porque una marca
    (`N 5`, `N 6`) sin su nota debajo es basura que `group_notes` ya tiene que
    saltarse. Lo de fuera del tramo no se toca ni un tick, y las notas nuevas que
    caigan fuera se descartan con aviso: pediste cambiar un tramo, no el chart.
    """
    informe = InformeAlinear(pista=pista, division=0)
    track = chart.tracks.get(pista)
    if track is None:
        informe.avisos.append(f"no hay pista {pista}")
        return informe
    if hasta_tick < desde_tick:
        desde_tick, hasta_tick = hasta_tick, desde_tick

    antes = len(track.notes)
    fuera = [n for n in track.notes if n.tick < desde_tick or n.tick > hasta_tick]
    borradas = antes - len(fuera)

    dentro = [n for n in notas_nuevas if desde_tick <= n.tick <= hasta_tick]
    if len(dentro) != len(notas_nuevas):
        informe.avisos.append(
            f"{len(notas_nuevas) - len(dentro)} notas nuevas caian fuera del tramo "
            f"y no se han puesto")

    track.notes = fuera + dentro
    track.notes.sort(key=lambda n: (n.tick, n.fret))
    informe.golpes = len({n.tick for n in track.notes if not n.is_flag})
    informe.movidos = len(dentro)
    informe.chocan = 0
    informe.avisos.append(
        f"tramo {desde_tick}-{hasta_tick}: fuera {borradas} golpes viejos, "
        f"dentro {len(dentro)} nuevos; el resto del chart no se ha tocado")
    return informe
