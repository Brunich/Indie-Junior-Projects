"""Pruebas que no necesitan audio ni biblioteca.

    python tests/test_basico.py      (o  python -m pytest tests/ )
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autochart import chartio  # noqa: E402
from autochart.audio import Onset  # noqa: E402
from autochart.chartio import Chart, Note, TempoEvent, TimeSignature, Track  # noqa: E402
from autochart.generate import (  # noqa: E402
    DIFFICULTY_SPECS, assign_frets, build_notes, hopo_flags, quantise, thin,
)
from autochart.timing import (  # noqa: E402
    build_tempo_map, normalise_tempo_octave, prepare_beat_grid, smooth_beat_grid,
)
from autochart.validate import validate_chart  # noqa: E402
from autochart import atlas, editar, grabar, letras, midiio, silabas, voz  # noqa: E402


def test_chart_roundtrip() -> None:
    chart = Chart(resolution=192)
    chart.metadata = {"Name": "Prueba", "Artist": "Nadie", "MusicStream": "song.ogg"}
    chart.tempos = [TempoEvent(0, 120.0), TempoEvent(768, 150.5)]
    chart.time_signatures = [TimeSignature(0, 4, 4)]
    chart.events = [(192, "section Intro")]
    track = Track("Expert", "Single")
    track.notes = [Note(0, 0, 0), Note(96, 2, 192), Note(192, 4, 0), Note(192, 3, 0)]
    chart.tracks[track.name] = track

    with tempfile.TemporaryDirectory() as folder:
        path = chartio.write_chart(chart, Path(folder) / "notes.chart")
        again = chartio.parse_chart(path)

    assert again.resolution == 192
    assert again.metadata["Name"] == "Prueba"
    assert [(t.tick, round(t.bpm, 3)) for t in again.tempos] == [(0, 120.0), (768, 150.5)]
    assert again.events == [(192, "section Intro")]
    written = sorted((n.tick, n.fret, n.sustain) for n in again.tracks["ExpertSingle"].notes)
    assert written == sorted((n.tick, n.fret, n.sustain) for n in track.notes)
    print("ok  test_chart_roundtrip")


def test_tick_seconds_roundtrip() -> None:
    chart = Chart(resolution=192)
    chart.tempos = [TempoEvent(0, 120.0), TempoEvent(768, 60.0)]
    assert abs(chart.tick_to_seconds(192) - 0.5) < 1e-9
    assert abs(chart.tick_to_seconds(768) - 2.0) < 1e-9
    assert abs(chart.tick_to_seconds(960) - 3.0) < 1e-9
    for tick in (0, 96, 768, 1500, 4000):
        assert abs(chart.seconds_to_tick(chart.tick_to_seconds(tick)) - tick) <= 1
    print("ok  test_tick_seconds_roundtrip")


def test_beat_grid_leaves_lead_in() -> None:
    beats = np.arange(2.0, 12.0, 0.5)  # primer pulso tarde a proposito
    grid = prepare_beat_grid(beats)
    assert grid[0] >= 0.18
    assert grid[0] < 0.7
    assert np.all(np.diff(grid) > 0)
    print("ok  test_beat_grid_leaves_lead_in")


def test_tempo_map_lands_on_every_beat() -> None:
    # Tempo que acelera: 120 BPM derivando hasta ~132.
    gaps = np.linspace(0.5, 0.455, 200)
    beats = np.concatenate([[0.62], 0.62 + np.cumsum(gaps)])
    tempo_map = build_tempo_map(beats, resolution=192)

    chart = Chart(resolution=192)
    chart.tempos = tempo_map.events
    drift = [
        abs(chart.tick_to_seconds(tempo_map.beat_to_tick(index)) - float(time))
        for index, time in enumerate(tempo_map.beat_times)
    ]
    assert max(drift) < 0.010, f"deriva maxima {max(drift) * 1000:.1f} ms"
    assert len(tempo_map.events) < len(beats), "el mapa no deberia tener un evento por pulso"
    print(f"ok  test_tempo_map_lands_on_every_beat (deriva max {max(drift) * 1000:.2f} ms, "
          f"{len(tempo_map.events)} eventos para {len(beats)} pulsos)")


def test_smooth_beat_grid_removes_jitter_but_keeps_drift() -> None:
    rng = np.random.default_rng(3)
    # 120 BPM acelerando a ~130, con ruido de +-15 ms como el de un detector.
    clean_gaps = np.linspace(0.5, 0.46, 240)
    clean = np.concatenate([[0.7], 0.7 + np.cumsum(clean_gaps)])
    noisy = clean + rng.normal(0.0, 0.015, clean.size)
    noisy = np.sort(noisy)

    smoothed = smooth_beat_grid(noisy)
    assert np.all(np.diff(smoothed) > 0), "la rejilla tiene que ser creciente"

    def jitter(beats: np.ndarray) -> float:
        gaps = np.diff(beats)
        return float(np.abs(np.diff(gaps)).mean())

    assert jitter(smoothed) < jitter(noisy) / 2, "el suavizado no quita bastante ruido"
    # Sigue la aceleracion real en vez de escaparse. Se mide la mediana: la
    # media movil de la correccion va por detras en los extremos y en los
    # cambios de pendiente, asi que el peor pulso suelto no dice nada.
    error = np.abs(smoothed - clean)
    assert float(np.median(error)) < 0.025, f"mediana {np.median(error) * 1000:.1f} ms"
    assert float(np.percentile(error, 95)) < 0.055
    print(f"ok  test_smooth_beat_grid_removes_jitter_but_keeps_drift "
          f"(ruido {jitter(noisy) * 1000:.1f} -> {jitter(smoothed) * 1000:.1f} ms, "
          f"error mediano {np.median(error) * 1000:.1f} ms)")


def test_tempo_octave_lands_in_band() -> None:
    slow = np.arange(0.0, 60.0, 60.0 / 55.0)  # 55 BPM
    fast = np.arange(0.0, 60.0, 60.0 / 300.0)  # 300 BPM
    for beats, expected in ((slow, 110.0), (fast, 150.0)):
        fixed = normalise_tempo_octave(beats)
        bpm = 60.0 / float(np.median(np.diff(fixed)))
        assert abs(bpm - expected) < 1.0, f"{bpm} no es {expected}"
        assert 85.0 <= bpm <= 200.0
    unchanged = np.arange(0.0, 60.0, 60.0 / 140.0)
    assert np.allclose(normalise_tempo_octave(unchanged), unchanged)
    print("ok  test_tempo_octave_lands_in_band")


def _fake_onsets(count: int = 64, tempo: float = 120.0) -> list[Onset]:
    step = 60.0 / tempo / 2.0  # corcheas
    onsets = []
    for index in range(count):
        onsets.append(
            Onset(
                time=0.62 + index * step,
                strength=0.5 + 0.5 * (index % 4 == 0),
                midi=52 + (index % 8),
                low=0.4, mid=0.6, high=0.3,
            )
        )
    return onsets


def test_quantise_keeps_grid_and_drops_strays() -> None:
    beats = np.arange(0.62, 40.0, 0.5)
    tempo_map = build_tempo_map(beats, 192)
    onsets = _fake_onsets()
    onsets.append(Onset(time=onsets[10].time + 0.19, strength=0.9, midi=60))  # fuera de rejilla
    candidates = quantise(onsets, tempo_map, (1, 2, 4))
    assert candidates, "no se cuantizo nada"
    for candidate in candidates:
        assert abs(candidate.beat * 4 - round(candidate.beat * 4)) < 1e-6
    assert len(candidates) <= len(onsets)
    print(f"ok  test_quantise_keeps_grid_and_drops_strays ({len(candidates)} de {len(onsets)})")


def test_generated_track_is_valid() -> None:
    beats = np.arange(0.62, 40.0, 0.5)
    tempo_map = build_tempo_map(beats, 192)
    spec = DIFFICULTY_SPECS["Expert"]
    candidates = thin(quantise(_fake_onsets(), tempo_map, spec.divisions), tempo_map, spec, 4.0)
    import random

    rng = random.Random(1)
    lanes = assign_frets(candidates, spec, None, rng)
    assert all(0 <= lane < spec.lanes for lane in lanes)
    notes = build_notes(candidates, lanes, spec, tempo_map, rng)

    chart = Chart(resolution=192)
    chart.tempos = tempo_map.events
    chart.tracks["ExpertSingle"] = Track("Expert", "Single", notes=notes)
    report = validate_chart(chart)
    assert report.ok, report.errors
    print(f"ok  test_generated_track_is_valid ({len(notes)} gemas)")


def test_hopo_flags_solo_donde_marca_un_humano() -> None:
    import random

    # Corcheas (96 ticks a resolucion 192) subiendo y bajando la mano, con un
    # acorde y una nota repetida metidos a proposito: son los dos casos que un
    # humano no marca nunca -- 0 de 6.668 marcas medidas en la biblioteca.
    notes: list[Note] = []
    acordes, repetidas = set(), set()
    for index in range(120):
        tick = index * 96
        if index % 17 == 5:
            notes += [Note(tick, 1, 0), Note(tick, 2, 0)]
            acordes.add(tick)
        elif index % 13 == 3:
            notes.append(Note(tick, notes[-1].fret, 0))
            repetidas.add(tick)
        else:
            notes.append(Note(tick, index % 5, 0))

    flags = hopo_flags(notes, 192, random.Random(4))
    assert flags, "con 120 corcheas tendria que salir alguna marca"
    ticks = {n.tick for n in notes}
    marcados = {n.tick for n in flags}
    assert all(n.fret == chartio.FLAG_FORCE for n in flags), "no se escriben taps"
    assert marcados <= ticks, "una marca sin nota debajo el juego no la lee"
    assert not (marcados & acordes), "el juego no liga acordes"
    assert not (marcados & repetidas), "no se puede martillear el traste que ya estaba pulsado"

    ratio = chartio.hopo_ratio(notes + flags, 192)
    assert 0.012 <= ratio <= 0.684, f"ligadura {ratio:.1%} fuera del rango humano p5-p95"
    print(f"ok  test_hopo_flags_solo_donde_marca_un_humano "
          f"({len(flags)} marcas, {ratio:.1%} ligadas)")


def test_las_marcas_no_cuentan_como_notas() -> None:
    # Si una marca se cuenta como nota, una nota suelta forzada parece un acorde
    # y todas las medidas del chart se van al garete sin que nada falle.
    chart = Chart(resolution=192)
    chart.tempos = [TempoEvent(0, 120.0)]
    notes = [Note(tick, tick // 96 % 5, 0) for tick in range(0, 96 * 40, 96)]
    flags = [Note(96 * index, chartio.FLAG_FORCE, 0) for index in (3, 7, 11)]
    chart.tracks["ExpertSingle"] = Track("Expert", "Single", notes=notes + flags)

    report = validate_chart(chart)
    assert report.ok, report.errors
    metrics = report.metrics["ExpertSingle"]
    assert metrics["notas"] == len(notes), "las marcas se colaron en el conteo"
    assert metrics["acordes"] == 0.0, "una nota forzada se conto como acorde"
    print("ok  test_las_marcas_no_cuentan_como_notas")


def test_validator_catches_broken_charts() -> None:
    chart = Chart(resolution=192)
    chart.tempos = [TempoEvent(0, 120.0)]
    chart.tracks["ExpertSingle"] = Track(
        "Expert", "Single",
        notes=[Note(0, 0, 400), Note(192, 0, 0), Note(193, 1, 0), Note(193, 1, 0)],
    )
    report = validate_chart(chart)
    assert not report.ok
    joined = " ".join(report.errors)
    assert "sostenidos" in joined  # el sostenido de 400 ticks pisa la nota del tick 192
    assert "repetida" in joined  # dos veces la misma nota en el tick 193
    print("ok  test_validator_catches_broken_charts")


def test_silabeo_espanol() -> None:
    """Las reglas del espanol son deterministas: o salen, o estan mal."""
    casos = {
        "corazon": "co-ra-zon", "guitarra": "gui-ta-rra", "construir": "cons-truir",
        "abstracto": "abs-trac-to", "ciudad": "ciu-dad", "transporte": "trans-por-te",
        "quiero": "quie-ro", "desarrollo": "de-sa-rro-llo", "ahora": "a-ho-ra",
        "buey": "buey", "instrumento": "ins-tru-men-to",
    }
    for palabra, esperado in casos.items():
        salida = "-".join(silabas.dividir_espanol(palabra))
        assert salida == esperado, f"{palabra}: sale {salida}, deberia {esperado}"
    print("ok  test_silabeo_espanol")


def test_silabeo_respeta_el_guion_a_mano() -> None:
    """Un guion escrito a mano manda sobre cualquier regla: es la valvula de escape."""
    assert silabas.dividir_linea("co-ra-zon mio", "es")[:3] == ["co", "ra", "zon"]
    assert silabas.dividir_palabra("gui-tarra", "es") == ["gui", "tarra"]
    print("ok  test_silabeo_respeta_el_guion_a_mano")


def test_voz_lee_la_letra_de_un_chart() -> None:
    """Una silaba por evento entre phrase_start y phrase_end: eso es el karaoke."""
    chart = Chart(resolution=192)
    chart.metadata = {"Name": "Prueba", "Resolution": "192"}
    chart.tempos = [TempoEvent(0, 120.0)]
    chart.events = [
        (0, "phrase_start"), (0, "lyric la-"), (96, "lyric la"),
        (192, "lyric le-"), (288, "lyric ro"), (384, "phrase_end"),
    ]
    with tempfile.TemporaryDirectory() as carpeta:
        destino = Path(carpeta) / "notes.chart"
        chartio.write_chart(chart, destino)
        pista = voz.leer_voz_chart(destino)
    assert pista is not None
    assert len(pista.frases) == 1, "phrase_start/phrase_end delimitan UNA frase"
    assert len(pista.frases[0].silabas) == 4
    assert pista.frases[0].silabas[0].enlaza, "la silaba con '-' se pega a la siguiente"
    assert pista.frases[0].texto == "lala lero", "el guion une, el resto separa"
    print("ok  test_voz_lee_la_letra_de_un_chart")


def test_atlas_reconoce_los_gestos() -> None:
    """Los detectores tienen que ver lo que un humano llamaria por su nombre."""
    def golpes(pares):
        return [atlas.Golpe(tick, trastes, 0) for tick, trastes in pares]

    # ocho semicorcheas en el mismo traste = tremolo (y ademas rafaga)
    tremolo = golpes([(i * 48, (0,)) for i in range(8)])
    veces, _, _ = atlas.detectar_licks(tremolo, 192)
    assert veces["tremolo"] == 1, "ocho iguales seguidas son un tremolo"
    assert veces["rafaga"] == 1, "ocho a semicorchea son ademas una rafaga"

    # subir de carril en carril = escalera
    escalera = golpes([(i * 96, (min(i, 4),)) for i in range(5)])
    veces, _, _ = atlas.detectar_licks(escalera, 192)
    assert veces["escalera_sube"] == 1 and veces["escalera_baja"] == 0

    # el mismo acorde repetido no es lo mismo que la misma forma desplazada
    martillo = golpes([(i * 96, (0, 1)) for i in range(4)])
    veces, _, _ = atlas.detectar_licks(martillo, 192)
    assert veces["acorde_martillo"] == 1 and veces["acorde_movil"] == 0
    print("ok  test_atlas_reconoce_los_gestos")


def test_atlas_un_galope_suelto_no_es_un_galope() -> None:
    """Larga-corta-corta una sola vez sale por casualidad en cualquier cancion.

    El gesto que la mano reconoce es el grupo REPETIDO. Sin esta regla el
    detector daba galope en el 22 % de las notas de la biblioteca entera.
    """
    def golpes(ticks):
        return [atlas.Golpe(t, (0,), 0) for t in ticks]

    # un solo grupo (96, 48, 48) y luego corcheas: no es galope
    suelto = golpes([0, 96, 144, 192, 288, 384, 480, 576])
    veces, _, _ = atlas.detectar_licks(suelto, 192)
    assert veces["galope"] == 0, "un larga-corta-corta suelto no es un galope"

    # tres grupos seguidos: si lo es
    ticks, t = [], 0
    for _ in range(3):
        ticks += [t, t + 96, t + 144]
        t += 192
    veces, _, _ = atlas.detectar_licks(golpes(ticks), 192)
    assert veces["galope"] == 1, "el grupo repetido si es un galope"
    print("ok  test_atlas_un_galope_suelto_no_es_un_galope")


def test_atlas_normaliza_los_generos_torcidos() -> None:
    """La etiqueta de song.ini no es de fiar: hay que normalizarla y auditarla."""
    assert atlas.normalizar_genero("Nu-Metal") == "metal"
    assert atlas.normalizar_genero("Nu Metal") == "metal"
    assert atlas.normalizar_genero("Pop/Rock") == "rock"   # gana la marca mas larga
    assert atlas.normalizar_genero("Pop") == "pop"
    assert atlas.normalizar_genero("Corrido Tumbado") == "latino"
    assert atlas.normalizar_genero("Hardcore Punk") == "punk"
    # lo que no dice nada tiene que quedar marcado, no colocado a la fuerza
    assert atlas.normalizar_genero("M3M3S") == "sin_clasificar"
    assert atlas.normalizar_genero("") == "sin_clasificar"
    print("ok  test_atlas_normaliza_los_generos_torcidos")


def test_lrc_se_lee_con_sus_variantes() -> None:
    """Los .lrc reales traen centesimas, milesimas y varias marcas por linea."""
    crudo = chr(10).join([
        "[ar:Alguien]",
        "[00:12.34]primera",
        "[00:15.5]segunda",
        "[01:00.00]",                      # marca sin texto: es un silencio
        "[01:02.10][02:04.20]estribillo",  # la misma linea en dos sitios
    ])
    lineas = letras.leer_lrc(crudo)
    assert [round(l.segundos, 2) for l in lineas] == [12.34, 15.5, 62.1, 124.2]
    assert lineas[0].texto == "primera"
    assert lineas[2].texto == lineas[3].texto, "una linea con dos marcas sale dos veces"


def test_no_trocea_mas_que_un_humano() -> None:
    """El silabeador es el techo, no el que decide.

    Medido: partir cada palabra deja el 33 % de silabas enlazadas y el humano
    esta en el 13.9 % (p25 0.086, p75 0.183). El freno es 1.33 trozos por
    palabra, que son las 8 silabas por 6 palabras que escribe un humano.
    """
    linea = letras.LineaLetra(0.0, "corazon partido de la madrugada")
    frase = letras.repartir_linea(linea, 4.0, "es")
    palabras = len(linea.texto.split())
    assert len(frase.silabas) <= round(palabras * letras.TROZOS_POR_PALABRA) + 1
    enlazan = sum(1 for _, _, e in frase.silabas if e) / len(frase.silabas)
    assert enlazan <= 0.45, f"trocea de mas: {enlazan:.2f} enlazadas"
    # y las silabas van en orden, sin dos en el mismo sitio
    momentos = [m for m, _, _ in frase.silabas]
    assert momentos == sorted(momentos)


def test_la_letra_escrita_se_vuelve_a_leer() -> None:
    """Ida y vuelta: lo que escribo en [Events] lo lee el mismo lector del corpus."""
    chart = Chart(resolution=192)
    chart.metadata = {"Name": "Prueba", "Resolution": "192"}
    chart.tempos = [TempoEvent(0, 120.0)]
    lineas = [letras.LineaLetra(1.0, "una cancion sencilla"),
              letras.LineaLetra(5.0, "y otra linea mas")]
    frases = letras.construir_frases(lineas, "es")
    escritas = letras.escribir_en_chart(chart, frases)
    assert escritas > 0

    with tempfile.TemporaryDirectory() as carpeta:
        destino = Path(carpeta) / "notes.chart"
        chartio.write_chart(chart, destino)
        leida = voz.leer_voz_chart(destino)
    assert leida is not None
    assert len(leida.frases) == 2, "cada linea es una frase de karaoke"
    assert len(leida.silabas) == escritas
    # el texto reconstruido tiene que ser la linea original
    assert leida.frases[0].texto.replace(" ", "") == "unacancionsencilla"
    # y ninguna silaba puede caer antes de que la frase empiece
    for frase in leida.frases:
        assert frase.silabas[0].tick >= frase.inicio


def test_la_letra_que_no_cuadra_se_rechaza() -> None:
    """Una letra de otra version tiene que caerse sola, no colarse corrida."""
    lineas = [letras.LineaLetra(i * 10.0, "linea") for i in range(8)]
    # duracion declarada muy distinta de la del audio -> otra version
    malo = letras.verificar(lineas, duracion_audio=200.0, duracion_declarada=340.0)
    assert not malo.vale and "otra version" in malo.motivo
    # la letra se sale por el final del audio
    tarde = letras.verificar(lineas, duracion_audio=30.0, duracion_declarada=30.0)
    assert not tarde.vale
    # y una que si cuadra pasa (sin audio, solo por duracion)
    bueno = letras.verificar(lineas, duracion_audio=90.0, duracion_declarada=90.0)
    assert bueno.vale


def test_nombre_de_carpeta_que_windows_acepte() -> None:
    """El titulo sale de song.ini y ahi los caracteres prohibidos estan crudos."""
    from autochart.export import nombre_seguro
    assert nombre_seguro("What's My Age Again?") == "What's My Age Again_"
    assert nombre_seguro("AC/DC") == "AC_DC"
    assert nombre_seguro("acaba en punto.") == "acaba en punto"
    assert nombre_seguro("CON").startswith("_"), "CON es un nombre reservado"
    assert nombre_seguro("") == "sin_nombre"


def _candidata(**kwargs):
    base = dict(artista="Buckethead", titulo="Jordan", duracion=200.0,
                sincronizada="", plana="", instrumental=False)
    base.update(kwargs)
    return letras.Candidata(**base)


def test_sin_candidatas_no_es_instrumental() -> None:
    """Que LRCLIB no conozca la cancion NO significa que sea instrumental.

    Son cosas distintas y confundirlas convierte un hueco de la base de datos
    en una conclusion. Por eso hay tres estados y no dos.
    """
    vacio = letras.parece_instrumental([], "Buckethead", 200.0)
    assert not vacio.instrumental
    assert vacio.etiqueta == "desconocida"
    assert not vacio.seguro


def test_instrumental_por_mayoria_y_sin_letra() -> None:
    """Medido en la biblioteca: los instrumentales salen marcados por unanimidad."""
    todas = [_candidata(instrumental=True) for _ in range(8)]
    veredicto = letras.parece_instrumental(todas, "Buckethead", 200.0)
    assert veredicto.instrumental and veredicto.seguro
    assert veredicto.etiqueta == "instrumental"

    # si alguna trae letra, ya no es seguro aunque la mayoria diga instrumental
    mezcla = [_candidata(instrumental=True) for _ in range(8)]
    mezcla.append(_candidata(sincronizada="[00:01.00]algo"))
    dudoso = letras.parece_instrumental(mezcla, "Buckethead", 200.0)
    assert dudoso.instrumental and not dudoso.seguro


def test_otra_cancion_con_el_mismo_titulo_no_cuenta() -> None:
    """Filtrar por artista: hay muchas canciones que se llaman igual."""
    otras = [_candidata(artista="Otro Grupo", instrumental=True) for _ in range(6)]
    veredicto = letras.parece_instrumental(otras, "Buckethead", 200.0)
    assert veredicto.etiqueta == "desconocida", "no son del mismo artista"


def test_la_duracion_descarta_la_version_larga() -> None:
    largas = [_candidata(duracion=600.0, instrumental=True) for _ in range(6)]
    veredicto = letras.parece_instrumental(largas, "Buckethead", 200.0)
    assert veredicto.etiqueta == "desconocida", "600 s no es la misma grabacion que 200 s"


def test_el_lector_de_mid_no_tira_las_marcas_de_forzado() -> None:
    """Un `.mid` escribe DOS marcas y un `.chart` UNA: la traduccion tiene que
    contradecir al juego solo cuando el charter lo contradice.

    Hasta el 24-08-2026 el lector se quedaba con los cinco trastes y tiraba las
    84.462 marcas de la biblioteca, asi que la ligadura de un `.mid` salia medida
    con media regla: 0.106 de mediana cuando es 0.142.
    """
    import mido

    midi = mido.MidiFile(ticks_per_beat=192)
    pista = mido.MidiTrack()
    pista.append(mido.MetaMessage('track_name', name='PART GUITAR', time=0))

    # Tres notas: la segunda cae lejos (el juego NO la liga) y el charter la LIGA;
    # la tercera cae cerca y cambia de traste (el juego SI la liga) y el charter
    # la manda RASGUEAR. Las dos son marcas, y en las dos el .chart escribe `N 5`.
    eventos = [(0, 96), (384, 97), (384 + 32, 98)]
    marcas = [(384, 96 + midiio.MARCA_LIGAR), (384 + 32, 96 + midiio.MARCA_RASGUEAR)]
    absolutos = []
    for tick, pitch in eventos + marcas:
        absolutos.append((tick, mido.Message('note_on', note=pitch, velocity=100)))
        absolutos.append((tick + 16, mido.Message('note_off', note=pitch, velocity=0)))
    absolutos.sort(key=lambda par: par[0])
    anterior = 0
    for tick, mensaje in absolutos:
        mensaje.time = tick - anterior
        anterior = tick
        pista.append(mensaje)
    midi.tracks.append(pista)

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / 'notes.mid'
        midi.save(str(ruta))
        chart, pistas = midiio.parse_midi_multi(ruta)

    notas = pistas['guitarra']['Expert']
    marcadas = sorted(n.tick for n in notas if n.fret == chartio.FLAG_FORCE)
    assert marcadas == [384, 384 + 32], f'las dos marcas tienen que llegar: {marcadas}'

    # Y lo que cuenta: no cuantas se ligan, sino CUAL. Sin las marcas tambien
    # sale 1 de 3 -- pero es la tercera, que es justo la que el charter mando
    # rasguear. El ratio solo no distingue el arreglo del fallo.
    grupos = chartio.group_notes([Note(n.tick, n.fret, n.sustain) for n in notas])
    umbral = chartio.hopo_distance(chart.resolution)
    ligadas, previo = [], None
    for grupo in grupos:
        if grupo.tap or (chartio.is_natural_hopo(previo, grupo, umbral) != grupo.forced):
            ligadas.append(grupo.tick)
        previo = grupo
    assert ligadas == [384], f'se liga la que el charter ligo, no otra: {ligadas}'
    print('ok  test_el_lector_de_mid_no_tira_las_marcas_de_forzado')


def _chart_de_prueba(resolucion: int = 192, golpes: int = 400) -> Chart:
    """Un chart clavado a la semicorchea, para poder romperlo a proposito."""
    chart = Chart(resolution=resolucion)
    chart.tempos = [TempoEvent(0, 120.0)]
    chart.signatures = [TimeSignature(0, 4, 4)]
    notas = []
    for i in range(golpes):
        notas.append(Note(i * (resolucion // 4), i % 5, 0))
    chart.tracks['ExpertSingle'] = Track('Expert', 'Single', notas)
    return chart


def test_alinear_devuelve_las_notas_temblorosas_a_su_sitio() -> None:
    """El temblor SI lo arregla alinear: la rejilla es la buena."""
    import random
    chart = _chart_de_prueba()
    buenos = [n.tick for n in chart.tracks['ExpertSingle'].notes]
    rng = random.Random(11)
    for nota in chart.tracks['ExpertSingle'].notes:
        nota.tick += rng.randint(-9, 9)
    chart.tracks['ExpertSingle'].notes.sort(key=lambda n: (n.tick, n.fret))

    informe = editar.alinear(chart, 4)
    ahora = [n.tick for n in chart.tracks['ExpertSingle'].notes]
    exactas = sum(1 for a, b in zip(buenos, ahora) if a == b)
    assert exactas >= 0.9 * len(buenos), f'solo volvieron {exactas} de {len(buenos)}'
    assert informe.movidos > 0
    print('ok  test_alinear_devuelve_las_notas_temblorosas_a_su_sitio')


def test_alinear_no_junta_dos_golpes_en_uno() -> None:
    """Pegar no puede fusionar: dos acordes distintos no son uno."""
    chart = Chart(resolution=192)
    chart.tempos = [TempoEvent(0, 120.0)]
    # dos golpes a 10 ticks: los dos caen mas cerca del 0 que del 48
    chart.tracks['ExpertSingle'] = Track('Expert', 'Single',
                                         [Note(2, 0, 0), Note(10, 3, 0)])
    informe = editar.alinear(chart, 4)
    ticks = sorted({n.tick for n in chart.tracks['ExpertSingle'].notes})
    assert len(ticks) == 2, f'se fusionaron: {ticks}'
    assert informe.chocan == 1, f'tenia que avisar del choque, chocan={informe.chocan}'
    print('ok  test_alinear_no_junta_dos_golpes_en_uno')


def test_un_tempo_malo_no_se_confunde_con_temblor() -> None:
    """La comprobacion que fallaba: mirar principio contra final deja pasar esto.

    Un tempo estirado un 3 % encaja mal desde el primer compas, asi que 'al
    principio bien y al final mal' no lo caza. Probar factores si.
    """
    import random
    tembloroso = _chart_de_prueba()
    rng = random.Random(3)
    for nota in tembloroso.tracks['ExpertSingle'].notes:
        nota.tick += rng.randint(-9, 9)
    veredicto = editar.buscar_tempo(tembloroso, 4)
    assert not veredicto.esta_mal, 'el temblor no es un tempo malo'

    estirado = _chart_de_prueba()
    for nota in estirado.tracks['ExpertSingle'].notes:
        nota.tick = int(round(nota.tick * 1.03))
    veredicto = editar.buscar_tempo(estirado, 4)
    assert veredicto.esta_mal, 'un tempo estirado un 3 % tiene que cazarse'
    assert abs(veredicto.factor - 1 / 1.03) < 0.005, f'factor {veredicto.factor}'

    buenos = [n.tick for n in _chart_de_prueba().tracks['ExpertSingle'].notes]
    editar.reescalar(estirado, veredicto.factor)
    editar.alinear(estirado, 4)
    ahora = [n.tick for n in estirado.tracks['ExpertSingle'].notes]
    exactas = sum(1 for a, b in zip(buenos, ahora) if a == b)
    assert exactas >= 0.9 * len(buenos), f'el arreglo dejo {exactas} de {len(buenos)}'
    print('ok  test_un_tempo_malo_no_se_confunde_con_temblor')


def test_grabar_tocando_recupera_lo_que_se_toco() -> None:
    """Alguien toca el chart con latencia y pulso tembloroso: hay que recuperarlo.

    Es la prueba honesta de grabar: lo que llega del teclado NO son las notas,
    son las notas mas la latencia del equipo mas el temblor de una mano. La
    latencia GORDA se calibra y se pasa -- desde la fase es indistinguible modulo
    una subdivision, y eso lo comprueba la prueba de abajo.
    """
    import random
    chart = _chart_de_prueba(golpes=200)
    buenos = [(n.tick, n.fret) for n in chart.tracks['ExpertSingle'].notes]

    rng = random.Random(5)
    toques = []
    for tick, carril in buenos:
        segundo = chart.tick_to_seconds(tick) - 0.080 + rng.uniform(-0.025, 0.025)
        toques.append((max(0.0, segundo), carril))

    notas, informe = editar.desde_toques(toques, chart, 4, desfase_ms=80.0)
    assert not informe.desfase_automatico
    recuperadas = set((n.tick, n.fret) for n in notas)
    exactas = sum(1 for x in buenos if x in recuperadas)
    assert exactas >= 0.9 * len(buenos), f'solo {exactas} de {len(buenos)}'
    print('ok  test_grabar_tocando_recupera_lo_que_se_toco')


def test_la_latencia_solo_se_afina_dentro_de_media_subdivision() -> None:
    """Lo que SI se puede prometer, y lo que no.

    Desde la fase, correr un chart una subdivision entera lo deja exactamente
    igual de en fase: ninguna medida de fase puede decidir entre las dos. Asi que
    `adivinar_desfase` solo busca dentro de +-media subdivision, que es el unico
    tramo donde la respuesta es unica -- y ahi si acierta.
    """
    import random
    chart = _chart_de_prueba(golpes=200)
    rng = random.Random(9)
    resto_ms = 30.0
    toques = []
    for nota in chart.tracks['ExpertSingle'].notes:
        segundo = chart.tick_to_seconds(nota.tick) - resto_ms / 1000.0
        toques.append((max(0.0, segundo + rng.uniform(-0.008, 0.008)), nota.fret))

    hallado, en_fase = editar.adivinar_desfase(toques, chart, 4)
    assert abs(hallado - resto_ms) <= 10.0, f'resto {hallado}, esperaba {resto_ms}'
    # 0.78 es lo que TIENE que salir, no un liston de gusto: con temblor
    # uniforme de +-8 ms y una ventana de +-6.25 ms (tol = paso * 0.05),
    # lo esperable es 6.25/8 = 0.78. Medido: 0.77.
    assert en_fase >= 0.70, f'en fase {en_fase}'

    # y con pocos toques dice 0 en vez de inventarse una cifra
    pocos, _ = editar.adivinar_desfase(toques[:8], chart, 4)
    assert pocos == 0.0
    print('ok  test_la_latencia_solo_se_afina_dentro_de_media_subdivision')


def test_sobrescribir_un_tramo_no_toca_el_resto() -> None:
    """Cambiar un trozo es cambiar ESE trozo: lo de fuera no se mueve ni un tick."""
    chart = _chart_de_prueba(golpes=200)
    antes = [(n.tick, n.fret) for n in chart.tracks['ExpertSingle'].notes]
    desde, hasta = 960, 1920
    nuevas = [Note(t, 2, 0) for t in range(desde, hasta + 1, 96)]

    informe = editar.sustituir_tramo(chart, nuevas, desde, hasta)
    ahora = [(n.tick, n.fret) for n in chart.tracks['ExpertSingle'].notes]

    fuera_antes = [x for x in antes if x[0] < desde or x[0] > hasta]
    fuera_ahora = [x for x in ahora if x[0] < desde or x[0] > hasta]
    assert fuera_antes == fuera_ahora, 'se toco algo fuera del tramo'
    dentro_ahora = [x for x in ahora if desde <= x[0] <= hasta]
    assert dentro_ahora == [(n.tick, n.fret) for n in nuevas], 'el tramo no quedo como se pidio'
    assert informe.movidos == len(nuevas)
    print('ok  test_sobrescribir_un_tramo_no_toca_el_resto')


def test_el_reloj_de_grabar_cuenta_desde_el_tramo() -> None:
    """Si grabas desde el minuto 0:30, el primer golpe es a 0:30, no a 0:00."""
    sesion = grabar.SesionDeGrabacion(desde_s=30.0)
    assert sesion.golpe(0) is None, 'no puede apuntar nada antes de empezar'
    sesion.empezar(reloj=100.0)
    sesion.golpe(0, reloj=100.5)
    sesion.golpe(3, reloj=101.25)
    assert sesion.parar() == [(30.5, 0), (31.25, 3)]
    print('ok  test_el_reloj_de_grabar_cuenta_desde_el_tramo')


def test_calibrar_aguanta_una_pulsacion_perdida_y_una_de_mas() -> None:
    """Es lo que pasa de verdad al calibrar: se falla una y se cuela otra.

    Por eso va con MEDIANA y no con media, y por eso se tira lo que cae a mas de
    medio hueco entre clics: mas alla no se sabe a que clic pertenecia.
    """
    import random
    rng = random.Random(4)
    clics = [1.0 * (i + 1) for i in range(16)]
    taps = [c - 0.090 + rng.uniform(-0.020, 0.020) for c in clics]

    ms, valen, dispersion = grabar.calibrar_desfase(taps, clics)
    assert valen == 16
    assert abs(ms - 90.0) <= 15.0, f'latencia {ms}'
    assert dispersion > 0.0, 'la dispersion tiene que decirse: sin ella parece exacta'

    # una perdida y una de mas, muy lejos de cualquier clic
    rotos = taps[:7] + taps[8:] + [0.05]
    ms2, valen2, _ = grabar.calibrar_desfase(rotos, clics)
    assert valen2 == 15, f'valieron {valen2}: la de 0.05 s tenia que descartarse'
    assert abs(ms2 - 90.0) <= 15.0, f'latencia {ms2}'
    print('ok  test_calibrar_aguanta_una_pulsacion_perdida_y_una_de_mas')


def test_la_pista_de_clics_suena_donde_dice_y_no_revienta_los_oidos() -> None:
    """Un arnes que no comprueba lo que consiguio, miente.

    Y la amplitud no es un detalle de gusto: esto se toca con auriculares.
    """
    import struct
    import tempfile
    import wave
    with tempfile.TemporaryDirectory() as tmp:
        ruta, momentos = grabar.pista_de_calibrado(
            Path(tmp) / 'clics.wav', clics=4, cada_s=0.5)
        assert momentos == [0.5, 1.0, 1.5, 2.0]
        with wave.open(str(ruta)) as w:
            hz = w.getframerate()
            n = w.getnframes()
            datos = w.readframes(n)
        picos = [abs(struct.unpack_from('<h', datos, 2 * i)[0]) for i in range(n)]
        assert max(picos) <= 16400, f'pico {max(picos)}: pasa de media amplitud'
        for m in momentos:
            ventana = picos[int(m * hz):int((m + 0.025) * hz)]
            assert max(ventana) > 8000, f'no suena el clic de {m} s'
        silencio = picos[int(0.1 * hz):int(0.4 * hz)]
        assert max(silencio) < 100, 'suena algo donde no toca'
    print('ok  test_la_pista_de_clics_suena_donde_dice_y_no_revienta_los_oidos')


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"\n{len(tests)} pruebas OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
