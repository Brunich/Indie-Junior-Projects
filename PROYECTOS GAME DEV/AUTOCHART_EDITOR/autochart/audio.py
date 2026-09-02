"""Listen to the song: tempo, beats, onsets, pitch contour and sections.

Everything the generator needs to know about the audio is produced here and
handed over as plain data, so the charting logic can be tested without ever
decoding a file.

The pitch estimate is deliberately cheap: a constant-Q transform restricted to
the guitar's range, then the loudest bin in a short window after each onset.
We do not need the *correct* note, only a contour that rises and falls the way
the riff does -- that is what makes the fret pattern feel like the song.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# Stems in a Clone Hero folder, best first: an isolated guitar gives a far
# cleaner onset train than the full mix.
STEM_PREFERENCE = (
    "guitar.ogg", "guitar.mp3", "guitar.opus",
    "rhythm.ogg", "rhythm.mp3",
    "song.ogg", "song.mp3", "song.opus",
)

# Los stems que ya venian con la cancion. Ganan a cualquier separacion nuestra:
# un `guitar.ogg` de verdad es mas limpio que lo que saca demucs, y ademas es lo
# que se uso para calibrar el banco. Solo cuando NO hay ninguno entra la pista
# separada, y solo entonces se deja de mirar la mezcla.
STEM_PROPIO = (
    "guitar.ogg", "guitar.mp3", "guitar.opus",
    "rhythm.ogg", "rhythm.mp3",
)

# For finding the pulse it is the opposite: the full mix has the drums, and beat
# trackers are built for drums. An isolated guitar stem can be tracked wrong by
# a whole beat, which shifts every note in the chart.
BEAT_STEM_PREFERENCE = (
    "song.ogg", "song.mp3", "song.opus",
    "drums.ogg", "drums_1.ogg", "drums.mp3",
    "guitar.ogg", "guitar.mp3",
)

ANALYSIS_SR = 22050
HOP_LENGTH = 256  # ~11.6 ms at 22.05 kHz, fine enough for 16ths at 200 BPM
CQT_FMIN_NOTE = "E2"
CQT_BINS = 60  # five octaves, one bin per semitone

# Cuanto tiene que caer la energia para dar la nota por apagada, y hasta donde
# se busca. Un sostenido dura lo que suena la cuerda, no lo que tarda en llegar
# la nota siguiente: en Facil el hueco es de varios compases y rellenarlo entero
# daba sostenidos de 3.8 tiempos cuando la mediana humana es 0.80.
RING_DECAY = 0.35
RING_MAX_S = 6.0
# DESCARTADO CON NUMERO (23-08-2026): exigir N cuadros seguidos por debajo del
# umbral para dar la nota por muerta. Se probo porque con uno solo el metal de
# alta ganancia se quedaba sin un solo sostenido largo (Thunderhorse: el humano
# sostiene 15 notas de 1.30 s y el ring daba 0.03). Lo arregla, pero cobrandolo
# en AUC (0.805 -> 0.748 en Pride & Joy), y la ENVOLVENTE de aqui abajo hace lo
# mismo mejor: mismo ring en el metal (1.14 s) y AUC 0.763.
# Antes de mirar si la nota se apago, se toma la ENVOLVENTE de su banda: el
# maximo de una ventana movil. Una nota con tremolo o con palm mute se re-ataca
# diez veces por segundo, asi que su banda sube y baja aunque la cuerda no haya
# parado; sin envolvente, el ring la mata en el primer valle.
RING_ENVOLVENTE_S = 0.10

# El ring dice cuanto SUENA la banda de una nota. Lo que no sabe decir es si el
# humano la sostuvo: medido el 23-08-2026 en las 12 canciones con guitarra
# aislada, AUC mediano 0.586 y una sola separa (0.50 es una moneda). El
# candidato para eso es otra cosa: cuanto tiempo el CONTORNO sigue diciendo esa
# misma nota. Una cuerda que se deja sonar mantiene su tono; una nota picada
# deja el sitio a la siguiente aunque su banda tarde en apagarse.
TONO_FIRME_TOLERANCIA = 0.5   # semitonos; medio bin del CQT es la misma nota
TONO_FIRME_GRACIA_S = 0.10    # cuanto puede irse el contorno sin dar por muerta

# Cuanto tiene que sonar la banda melodica frente a la grave para dar el ataque
# por "de guitarra solista" y no por golpe de bateria o pisada de bajo. Esto
# sigue vivo: es el rasgo `lead` de cada ataque, que usa la etapa de densidad.
LEAD_BAND_FLOOR = 0.08

# RETIRADO el 22-08-2026: LEAD_MIDI_LOW = 55 (G3) y LEAD_MIDI_HIGH = 96. El
# suelo se puso porque "el 61 % de los tonos caia por debajo de MIDI 52 y el
# contorno seguia al acompanamiento", pero la sexta cuerda al aire es MIDI 40:
# prohibia el registro de la guitarra y obligaba al estimador a devolver un
# armonico. Ahora lo grave se atenua en vez de prohibirse, y de seguir al bajo
# se encarga la continuidad. Medido en docs/AUDITORIA_POR_QUE_NO_SUENA.md.

# --- El contorno de tono, con continuidad -----------------------------------
# Medido el 22-08-2026 (docs/AUDITORIA_POR_QUE_NO_SUENA.md): coger el bin mas
# fuerte cuadro a cuadro daba un contorno que saltaba la octava el 20 % de las
# veces, y el 40 % en Thunderstruck con la guitarra aislada. Una melodia humana
# lo hace el 0,55 %. Contra librosa.pyin el error mediano era de 12,6 a 17,0
# semitonos. La direccion del intervalo -- que es lo que el generador convierte
# en movimiento de la mano -- salia al azar.
#
# Tres cosas lo arreglan, y ninguna es "afinar un umbral":
#   1. SUMA ARMONICA: un armonico de octava suena fuerte, pero su fundamental
#      tambien suena. Sumando al bin b la energia de b+12 y b+19, el fundamental
#      gana a su propio armonico.
#   2. PESO GRAVE SUAVE en vez del suelo duro de G3. El suelo se puso para dejar
#      de seguir al bajo, pero la sexta al aire es MIDI 40: prohibia el registro
#      de la guitarra y obligaba a devolver un armonico.
#   3. CONTINUIDAD (Viterbi) con el prior de intervalos MEDIDO en las pistas de
#      voz humanas de la biblioteca. El tono ya no salta de octava entre dos
#      cuadros solo porque el armonico gane un instante.
PESO_GRAVE_MINIMO = 0.25   # cuanto se atenua MIDI 38 y por debajo
PESO_GRAVE_DESDE = 38.0
PESO_GRAVE_HASTA = 52.0    # de aqui arriba no se atenua nada
ARMONICOS = ((12, 0.5), (19, 0.33))   # octava y octava+quinta
# Y al reves: a un bin que parece el armonico de una nota mas grave que suena
# fuerte se le quita energia. Sumar los armonicos hacia abajo no basta -- con
# distorsion, la octava de arriba sigue ganando y el contorno se va con ella.
SUPRESION_OCTAVA = 0.0
# Probabilidad de que el tono cambie de bin entre dos cuadros (11,6 ms). Con
# 0.08 la nota media dura ~145 ms, del orden de la silaba humana medida.
# No es un numero libre: subirlo devuelve el contorno saltarin, bajarlo pega el
# tono a una sola nota.
PROB_DE_MOVERSE = 0.08
SILENCIO_RELATIVO = 0.02   # cuadros por debajo de esto no tienen tono


@dataclass
class Onset:
    """One detected attack in the audio."""

    time: float
    strength: float
    midi: float = 0.0  # estimated dominant pitch, MIDI number (0 = unknown)
    low: float = 0.0  # band energies at the attack, normalised 0..1
    mid: float = 0.0
    high: float = 0.0
    beat: float = 0.0  # position on the beat grid, in beats (fractional)
    ring: float = 0.0  # seconds the attack keeps sounding before it decays
    tono_firme: float = 0.0  # segundos que el contorno sigue diciendo esa nota
    lead: float = 0.0  # 0..1: cuanto manda la banda melodica sobre la grave


@dataclass
class Section:
    start: float
    end: float
    label: str
    energy: float = 0.0


@dataclass
class AudioAnalysis:
    path: Path
    sr: int
    duration: float
    tempo: float
    beat_times: np.ndarray
    onsets: list[Onset] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)
    stem_used: str = ""

    def beats_per_second(self) -> float:
        return self.tempo / 60.0


def _pick(song_dir: Path, preference: tuple[str, ...]) -> Path | None:
    lowered = {p.name.lower(): p for p in song_dir.iterdir() if p.is_file()}
    for name in preference:
        if name in lowered:
            return lowered[name]
    for path in sorted(song_dir.iterdir()):
        if path.suffix.lower() in (".ogg", ".mp3", ".wav", ".opus", ".flac"):
            return path
    return None


def pick_audio(song_dir: str | Path, nombre: str | None = None) -> Path | None:
    """De donde salen las NOTAS, mejor primero.

    Orden, y cada escalon tiene su razon medida:

    1. El stem que ya traia la cancion (`guitar.ogg`). Es mas limpio que
       cualquier separacion y es con lo que esta calibrado el banco.
    2. **La pista separada con demucs** (`salida/stems/<nombre>/notas.ogg`, que
       es `other` + `vocals`). Entra aqui porque medido con `tools/quien_toca.py`
       el 58-63 % de las notas que salian de la mezcla caian en un instante mas
       percusivo que armonico: el chart escribia la bateria, y una bateria suena
       igual en todas las canciones.
    3. La mezcla, que es lo que habia y lo que hay cuando no se ha separado.

    El pulso NO pasa por aqui: sigue saliendo de la mezcla (`pick_beat_audio`),
    porque sobre un stem aislado el detector se equivoca de compas entero.
    """
    folder = Path(song_dir)
    if folder.is_file():
        return folder

    lowered = {f.name.lower(): f for f in folder.iterdir() if f.is_file()}
    for name in STEM_PROPIO:
        if name in lowered:
            return lowered[name]

    try:
        from .separar import pista_de_notas
        separada = pista_de_notas(nombre or folder.name)
    except Exception:
        separada = None
    if separada is not None and separada.exists():
        return separada

    return _pick(folder, STEM_PREFERENCE)


def pick_beat_audio(song_dir: str | Path) -> Path | None:
    """Best stem for finding the *pulse*: the full mix, when the folder has one."""
    folder = Path(song_dir)
    if folder.is_file():
        return folder
    return _pick(folder, BEAT_STEM_PREFERENCE)


def build_beat_grid(beat_times: np.ndarray) -> np.ndarray:
    """Put the detected beats into the shape the tempo map expects.

    Fix the octave first (a tracker that reports half tempo makes every
    beat-relative setting mean twice what it should), then smooth out the
    tracker's per-beat jitter, then extend backwards so beat 0 sits near t=0
    with room for the lead-in beat.
    """
    from .timing import normalise_tempo_octave, prepare_beat_grid, smooth_beat_grid

    beats = normalise_tempo_octave(np.asarray(beat_times, dtype=float))
    return prepare_beat_grid(smooth_beat_grid(beats))


def _sections_from_features(y, sr, duration: float, beat_times: np.ndarray) -> list[Section]:
    import librosa

    target = max(3, min(14, int(duration // 22)))
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=HOP_LENGTH)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, hop_length=HOP_LENGTH, n_mfcc=13)
    features = np.vstack([librosa.util.normalize(chroma, axis=0), librosa.util.normalize(mfcc, axis=0)])
    boundaries = librosa.segment.agglomerative(features, target)
    times = librosa.frames_to_time(boundaries, sr=sr, hop_length=HOP_LENGTH)
    times = np.unique(np.concatenate([[0.0], times, [duration]]))

    rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=HOP_LENGTH)
    peak = float(rms.max()) or 1.0

    sections: list[Section] = []
    for index, (start, end) in enumerate(zip(times, times[1:])):
        if end - start < 4.0 and sections:
            sections[-1].end = float(end)
            continue
        window = rms[(rms_times >= start) & (rms_times < end)]
        energy = float(window.mean() / peak) if window.size else 0.0
        sections.append(Section(float(start), float(end), f"Parte {index + 1}", energy))
    return sections


def ring_por_tono(
    cqt: np.ndarray,
    midi_base: float,
    onset_times: np.ndarray,
    midis: np.ndarray,
    sr: int,
    hop_length: int = HOP_LENGTH,
    decay: float = RING_DECAY,
    max_seconds: float = RING_MAX_S,
    envolvente_s: float | None = None,
) -> np.ndarray:
    """Cuanto sigue sonando cada ataque **en su propia nota**, no en la mezcla.

    `ring_times` mide la energia de todo lo que suena, y por eso en una pista
    donde se toca sin parar no mide nada: medido el 23-08-2026 en Pride & Joy,
    su mediana era 5.99 s con un tope de 6.00 -- la mitad de los ataques
    clavados en el techo -- y el ring de las notas que el humano sostuvo era
    identico al de las que pico.

    Aqui se mira solo el bin del CQT donde vive la nota, mas su octava (la misma
    suma armonica que usa `contorno_de_tono`, para que un armonico fuerte no
    parezca otra nota). Esa banda SI se apaga cuando la cuerda deja de sonar,
    aunque la cancion siga atronando alrededor. Las notas sin tono conocido
    (`midi <= 0`) se devuelven a 0 y el generador cae al hueco, como antes.
    """
    n_bins, n_frames = cqt.shape
    out = np.zeros(onset_times.size)
    if n_frames == 0 or onset_times.size == 0:
        return out
    from scipy.ndimage import maximum_filter1d

    frames_per_second = sr / hop_length
    peak_window = max(2, int(0.05 * frames_per_second))
    limit = max(2, int(max_seconds * frames_per_second))
    if envolvente_s is None:
        envolvente_s = RING_ENVOLVENTE_S
    envolvente = max(1, int(round(envolvente_s * frames_per_second)))

    for index, time in enumerate(onset_times):
        midi = float(midis[index]) if index < len(midis) else 0.0
        if midi <= 0.0:
            continue
        start = int(round(time * frames_per_second))
        if start >= n_frames:
            continue
        bin_index = int(round(midi - midi_base))
        if bin_index < 0 or bin_index >= n_bins:
            continue
        stop = min(n_frames, start + limit)
        banda = cqt[bin_index, start:stop].astype(float)
        if bin_index + 12 < n_bins:
            banda = banda + 0.5 * cqt[bin_index + 12, start:stop]
        if banda.size == 0:
            continue
        if envolvente > 1:
            banda = maximum_filter1d(banda, size=envolvente, mode="nearest")
        peak = float(banda[:min(banda.size, peak_window)].max())
        if peak <= 0.0:
            continue
        apagada = np.nonzero(banda < peak * decay)[0]
        frames = int(apagada[0]) if apagada.size else banda.size
        out[index] = frames / frames_per_second
    return out


def tono_firme_por_ataque(
    contorno: np.ndarray,
    onset_times: np.ndarray,
    midis: np.ndarray,
    sr: int,
    hop_length: int = HOP_LENGTH,
    max_seconds: float = RING_MAX_S,
    tolerancia: float = TONO_FIRME_TOLERANCIA,
    gracia_s: float = TONO_FIRME_GRACIA_S,
) -> np.ndarray:
    """Cuanto sigue el contorno diciendo la nota del ataque, en segundos.

    Es la senal hermana del ring y pregunta otra cosa: el ring mira si la banda
    de la nota sigue teniendo energia, y esto mira si el estimador de tono sigue
    eligiendo esa nota. Una cuerda dejada sonar mantiene su tono hasta que otra
    la tapa; una nota picada cede el sitio a la siguiente aunque su banda tarde
    en apagarse por la reverberacion o por la distorsion de al lado.

    No cuesta nada: `analyse` ya calcula el contorno ANTES del ring, porque el
    ring necesita saber en que bin vive cada nota.
    """
    salida = np.zeros(onset_times.size)
    if contorno.size == 0 or onset_times.size == 0:
        return salida
    frames_per_second = sr / hop_length
    limite = max(2, int(max_seconds * frames_per_second))
    gracia = max(1, int(round(gracia_s * frames_per_second)))

    for index, time in enumerate(onset_times):
        midi = float(midis[index]) if index < len(midis) else 0.0
        if midi <= 0.0:
            continue
        start = int(round(time * frames_per_second))
        if start >= contorno.size:
            continue
        stop = min(contorno.size, start + limite)
        tramo = contorno[start:stop]
        if tramo.size == 0:
            continue
        # Un cuadro cuenta si el contorno sigue en esa nota. Se permite que se
        # vaya un momento (`gracia`): el Viterbi salta un cuadro suelto cuando
        # entra un golpe de bateria encima, y cortar ahi seria medir el ruido.
        en_la_nota = np.abs(tramo - midi) <= tolerancia
        fuera = 0
        frames = tramo.size
        for offset, dentro in enumerate(en_la_nota):
            if dentro:
                fuera = 0
                continue
            fuera += 1
            if fuera > gracia:
                frames = offset - fuera + 1
                break
        salida[index] = max(0, frames) / frames_per_second
    return salida


def _load(path: Path, sr: int, max_seconds: float | None):
    import librosa

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        y, sr = librosa.load(str(path), sr=sr, mono=True, duration=max_seconds)
    if y.size == 0:
        raise ValueError(f"El audio esta vacio o no se pudo leer: {path}")
    return librosa.util.normalize(y), sr


def onset_envelope(y, sr: int, band: tuple[float, float] | None = None):
    """Fuerza de ataque, opcionalmente mirando solo una banda de frecuencias.

    **`band` esta MEDIDO Y DESCARTADO como opcion por defecto.** La idea era que,
    detectando en todo el espectro, un golpe de bateria sin guitarra encima da un
    ataque tan fuerte como una nota del riff, y que mirando solo la banda de la
    solista el tren de ataques se pareceria mas a lo que toca el instrumento
    principal. No sale a cuenta: sobre 6 canciones con chart humano, el espectro
    completo gana en 5.

        banda            F1 medio (6 canciones)
        todo (actual)    0.684
        300-2500 Hz      0.683
        200-3000 Hz      0.681

    La razon es que la seleccion de instrumento ya la hace la etapa de densidad
    con `Onset.lead`; recortar la banda solo pierde informacion. Se deja el
    parametro porque hace el experimento reproducible, pero por defecto va a None.
    """
    import librosa

    if band is None:
        return librosa.onset.onset_strength(
            y=y, sr=sr, hop_length=HOP_LENGTH, aggregate=np.median
        )
    spectrum = np.abs(librosa.stft(y=y, n_fft=2048, hop_length=HOP_LENGTH))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    keep = (freqs >= band[0]) & (freqs <= band[1])
    if not keep.any():
        return librosa.onset.onset_strength(
            y=y, sr=sr, hop_length=HOP_LENGTH, aggregate=np.median
        )
    return librosa.onset.onset_strength(
        S=librosa.power_to_db(spectrum[keep] ** 2, ref=np.max),
        sr=sr, hop_length=HOP_LENGTH, aggregate=np.median,
    )


def _prior_de_intervalos(n_bins: int, ruta_perfil: Path | None = None,
                         prob_moverse: float | None = None) -> np.ndarray:
    """Matriz de transicion sacada de como se mueve una melodia humana.

    Los intervalos salen de `datos/perfil_voz.json`, minado de las pistas
    `PART VOCALS` escritas a mano de la biblioteca: tono MIDI real, no estimado.
    El 35 % se queda en la nota, el 87 % de los saltos son de 3 semitonos o
    menos y solo el 0,55 % llega a la octava.
    """
    import json

    forma = {0: 0.35, 1: 0.05, 2: 0.15, 3: 0.05, 4: 0.02, 5: 0.02, 7: 0.013}
    ruta = ruta_perfil or (Path(__file__).resolve().parent.parent / "datos" / "perfil_voz.json")
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8")).get("saltos_semitono") or {}
        medida = {}
        for clave, valor in datos.items():
            medida[abs(int(clave))] = medida.get(abs(int(clave)), 0.0) + float(valor)
        if medida:
            forma = medida
    except Exception:  # sin perfil se usa la forma de respaldo, no se revienta
        pass

    mover = PROB_DE_MOVERSE if prob_moverse is None else prob_moverse
    fuera = np.zeros(n_bins, dtype=float)
    for distancia in range(1, n_bins):
        fuera[distancia] = forma.get(distancia, 0.0)
    if fuera.sum() <= 0:
        fuera[1:] = 1.0
    fuera = fuera / fuera.sum()

    indices = np.arange(n_bins)
    transicion = np.zeros((n_bins, n_bins), dtype=float)
    for origen in range(n_bins):
        fila = mover * fuera[np.abs(indices - origen)]
        fila[origen] = 1.0 - mover
        fila += 1e-9
        transicion[origen] = fila / fila.sum()
    return transicion


def contorno_de_tono(cqt: np.ndarray, midi_base: float,
                     supresion_octava: float | None = None,
                     prob_moverse: float | None = None) -> np.ndarray:
    """Un tono por cuadro, en MIDI, con continuidad. 0 = ese cuadro no suena.

    Suma armonica + peso grave suave + Viterbi con el prior humano. Sustituye
    al argmax por cuadro, que devolvia armonicos: ver el bloque de constantes y
    docs/AUDITORIA_POR_QUE_NO_SUENA.md.
    """
    import librosa

    supresion = SUPRESION_OCTAVA if supresion_octava is None else supresion_octava
    mover = PROB_DE_MOVERSE if prob_moverse is None else prob_moverse

    n_bins, n_frames = cqt.shape
    if n_frames == 0:
        return np.zeros(0, dtype=float)

    # 1. suma armonica: el fundamental recupera parte de la energia de sus armonicos
    fuerza = np.asarray(cqt, dtype=float).copy()
    for distancia, peso in ARMONICOS:
        if distancia < n_bins:
            fuerza[: n_bins - distancia] += peso * cqt[distancia:]
    # 1bis. y se le quita a quien parece el armonico de una nota mas grave
    if supresion > 0 and n_bins > 12:
        fuerza[12:] -= supresion * cqt[:-12]
        np.clip(fuerza, 0.0, None, out=fuerza)

    # 2. peso grave suave (antes era un corte duro en G3)
    midis = midi_base + np.arange(n_bins)
    rampa = np.clip((midis - PESO_GRAVE_DESDE) / (PESO_GRAVE_HASTA - PESO_GRAVE_DESDE), 0.0, 1.0)
    fuerza *= (PESO_GRAVE_MINIMO + (1.0 - PESO_GRAVE_MINIMO) * rampa)[:, None]

    # 3. cuadros sin nada que oir
    energia = fuerza.sum(axis=0)
    techo = float(np.percentile(energia, 95)) or 1.0
    mudo = energia < techo * SILENCIO_RELATIVO

    seguro = np.where(energia > 0, energia, 1.0)
    prob = fuerza / seguro
    prob[:, mudo] = 1.0 / n_bins
    prob[:, energia <= 0] = 1.0 / n_bins

    camino = librosa.sequence.viterbi(prob, _prior_de_intervalos(n_bins, prob_moverse=mover))
    salida = midi_base + camino.astype(float)
    salida[mudo] = 0.0
    return salida


def analyse(
    audio_path: str | Path,
    sr: int = ANALYSIS_SR,
    onset_delta: float = 0.0,
    max_seconds: float | None = None,
    beat_audio_path: str | Path | None = None,
    onset_band: tuple[float, float] | None = None,
) -> AudioAnalysis:
    """Run the full listening pass.

    `audio_path` is where the notes come from (the guitar stem when there is
    one). `beat_audio_path` is where the pulse comes from (the full mix); when
    it is omitted the same file is used for both.

    `onset_delta` defaults to 0: detect generously and let the density stage
    choose. Measured across the library, a permissive threshold puts a detected
    attack under ~99 % of the notes a human charter wrote, while any threshold
    high enough to look "clean" throws away most of the song.
    """
    import librosa

    path = Path(audio_path)
    y, sr = _load(path, sr, max_seconds)
    duration = float(librosa.get_duration(y=y, sr=sr))

    onset_env = onset_envelope(y, sr, onset_band)
    onset_env = onset_env / (float(np.percentile(onset_env, 99)) or 1.0)

    beat_path = Path(beat_audio_path) if beat_audio_path else path
    if beat_path != path:
        beat_y, _ = _load(beat_path, sr, max_seconds)
        beat_env = librosa.onset.onset_strength(
            y=beat_y, sr=sr, hop_length=HOP_LENGTH, aggregate=np.median
        )
    else:
        beat_env = onset_env

    tempo, beat_frames = librosa.beat.beat_track(
        onset_envelope=beat_env, sr=sr, hop_length=HOP_LENGTH, trim=False
    )
    tempo = float(np.atleast_1d(tempo)[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=HOP_LENGTH)
    beat_times = build_beat_grid(np.asarray(beat_times, dtype=float))
    if beat_times.size < 2:
        beat_times = np.arange(0.0, duration, 60.0 / max(tempo, 1.0))
    else:
        tempo = float(60.0 / np.median(np.diff(beat_times)))

    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=HOP_LENGTH,
        backtrack=False,
        delta=onset_delta,
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=HOP_LENGTH)

    # Spectral material for pitch and band energies, computed once.
    cqt = np.abs(
        librosa.cqt(
            y=y, sr=sr, hop_length=HOP_LENGTH,
            fmin=librosa.note_to_hz(CQT_FMIN_NOTE), n_bins=CQT_BINS, bins_per_octave=12,
        )
    )
    cqt_midi_base = float(librosa.note_to_midi(CQT_FMIN_NOTE))
    spectrogram = np.abs(librosa.stft(y=y, n_fft=1024, hop_length=HOP_LENGTH))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)
    low_band = spectrogram[freqs < 250].sum(axis=0)
    mid_band = spectrogram[(freqs >= 250) & (freqs < 2000)].sum(axis=0)
    high_band = spectrogram[freqs >= 2000].sum(axis=0)

    def _norm(band: np.ndarray) -> np.ndarray:
        top = float(np.percentile(band, 99)) or 1.0
        return np.clip(band / top, 0.0, 1.0)

    low_band, mid_band, high_band = _norm(low_band), _norm(mid_band), _norm(high_band)
    # Cuanto manda lo melodico sobre lo grave en cada instante. Un golpe de bombo
    # o una pisada de bajo dan 0; un riff de guitarra da cerca de 1.
    lead_band = np.clip(
        (mid_band + 0.5 * high_band) / (mid_band + 0.5 * high_band + low_band + 1e-6),
        0.0, 1.0,
    )
    strength_peak = float(np.percentile(onset_env, 99)) or 1.0

    frames_total = cqt.shape[1]
    window_frames = max(2, int(0.07 * sr / HOP_LENGTH))
    contorno = contorno_de_tono(cqt, cqt_midi_base)

    # El tono de cada ataque hace falta ANTES que el ring, porque el ring se
    # mide en la banda de esa nota. Es la mediana de los cuadros que suenan
    # justo despues del ataque; si ninguno suena, la nota se queda sin tono.
    midis = np.zeros(len(onset_times))
    for position, time in enumerate(onset_times):
        frame = int(round(time * sr / HOP_LENGTH))
        if frame >= frames_total:
            continue
        tramo = contorno[frame:min(frames_total, frame + window_frames)]
        vivos = tramo[tramo > 0]
        midis[position] = float(np.median(vivos)) if vivos.size else 0.0
    rings = ring_por_tono(cqt, cqt_midi_base, np.asarray(onset_times, dtype=float),
                          midis, sr)
    tonos_firmes = tono_firme_por_ataque(contorno, np.asarray(onset_times, dtype=float),
                                         midis, sr)

    onsets: list[Onset] = []
    for position, time in enumerate(onset_times):
        frame = int(round(time * sr / HOP_LENGTH))
        if frame >= frames_total:
            continue
        midi = float(midis[position])
        env_index = min(len(onset_env) - 1, frame)
        onsets.append(
            Onset(
                time=float(time),
                strength=float(min(1.0, onset_env[env_index] / strength_peak)),
                midi=midi,
                low=float(low_band[min(len(low_band) - 1, frame)]),
                mid=float(mid_band[min(len(mid_band) - 1, frame)]),
                high=float(high_band[min(len(high_band) - 1, frame)]),
                ring=float(rings[position]),
                tono_firme=float(tonos_firmes[position]),
                lead=float(lead_band[min(len(lead_band) - 1, frame)]),
            )
        )

    sections = _sections_from_features(y, sr, duration, beat_times)

    return AudioAnalysis(
        path=path,
        sr=sr,
        duration=duration,
        tempo=tempo,
        beat_times=beat_times,
        onsets=onsets,
        sections=sections,
        stem_used=path.name,
    )
