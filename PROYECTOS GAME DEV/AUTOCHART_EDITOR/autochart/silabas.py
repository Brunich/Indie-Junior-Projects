"""Partir la letra en silabas. Es lo que hace que el karaoke se ANIME.

Por que importa tanto: Clone Hero pinta la linea entera de la frase y va
coloreando **evento a evento**. Si el chart escribe la linea de golpe (un solo
evento `lyric` con la frase entera), la linea se ilumina toda a la vez y no hay
karaoke; si escribe una silaba por evento, la linea se colorea al ritmo de lo
que se canta. Las dos cosas pasan en la biblioteca de Bruno:

  - `Ed Maverick - Fuentes de Ortiz` escribe una silaba por evento -> se anima.
  - `Cardenales De Nuevo Leon - Belleza De Cantina` mete la linea entera en un
    evento, pegando las palabras con espacios duros (U+00A0) para que el juego
    no las separe -> se lee, pero no se anima.

O sea que la animacion no es un efecto que haya que programar: es la
consecuencia de partir bien. Este modulo es esa parte.

Espanol: las reglas son deterministas y salen bien casi siempre (diptongos,
hiatos, grupos consonanticos inseparables). Ingles: no hay reglas, hay
costumbre; se usa `pyphen` si esta instalado y si no un heuristico. Y siempre
manda lo que escriba Bruno a mano: si en la letra pone `co-ra-zon`, se respeta.
"""

from __future__ import annotations

import re
import unicodedata

VOCALES_FUERTES = set("aeoáéó")
VOCALES_DEBILES = set("iuü")
VOCALES_DEBILES_TONICAS = set("íú")
VOCALES = VOCALES_FUERTES | VOCALES_DEBILES | VOCALES_DEBILES_TONICAS

# Pares de consonantes que NUNCA se separan en espanol.
INSEPARABLES = {
    "pr", "pl", "br", "bl", "tr", "dr", "cr", "cl", "gr", "gl", "fr", "fl",
    "tl", "ll", "rr", "ch",
}

# El guion entra DENTRO de la palabra a proposito: si Bruno escribe `co-ra-zon`
# en la letra, eso es un corte puesto a mano y manda sobre cualquier regla.
_RE_PALABRA = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)


def _sin_tildes(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def detectar_idioma(texto: str) -> str:
    """es / en, decidido por rasgos que solo aparecen en uno de los dos."""
    bajo = texto.lower()
    marcas_es = len(re.findall(r"[ñáéíóúü¿¡]", bajo))
    palabras = set(_RE_PALABRA.findall(bajo))
    comunes_es = {"que", "de", "la", "el", "y", "en", "no", "por", "con", "mi",
                  "tu", "un", "una", "los", "las", "es", "se", "te", "me", "al"}
    comunes_en = {"the", "and", "you", "to", "of", "in", "it", "is", "that",
                  "for", "on", "with", "my", "your", "all", "we", "be", "not"}
    puntos_es = marcas_es * 2 + len(palabras & comunes_es)
    puntos_en = len(palabras & comunes_en)
    return "es" if puntos_es >= puntos_en else "en"


# ---------------------------------------------------------------------------
# Espanol
# ---------------------------------------------------------------------------


def _es_vocal(ch: str) -> bool:
    return ch in VOCALES


def _mismo_nucleo(a: str, b: str) -> bool:
    """True si dos vocales seguidas van en la MISMA silaba (diptongo)."""
    debil_a = a in VOCALES_DEBILES
    debil_b = b in VOCALES_DEBILES
    if debil_a and debil_b:
        return a != b            # 'iu', 'ui' si; 'ii' no
    if debil_a != debil_b:
        return True              # fuerte + debil atona
    return False                 # dos fuertes -> hiato


def dividir_espanol(palabra: str) -> list[str]:
    """Silabea una palabra espanola. Devuelve la palabra entera si no hay vocal."""
    if len(palabra) <= 2:
        return [palabra]
    bajo = palabra.lower()
    n = len(bajo)

    # 1) nucleos: posiciones (inicio, fin) de cada grupo vocalico
    nucleos: list[tuple[int, int]] = []
    i = 0
    while i < n:
        if not _es_vocal(bajo[i]):
            i += 1
            continue
        inicio = i
        i += 1
        while i < n and _es_vocal(bajo[i]):
            # 'u' muda en que/qui/gue/gui no abre nucleo nuevo
            if bajo[i - 1] == "u" and inicio > 0 and bajo[inicio - 1] in "qg" and bajo[inicio] == "u":
                i += 1
                continue
            if _mismo_nucleo(bajo[i - 1], bajo[i]):
                i += 1
            else:
                break
        nucleos.append((inicio, i))
    if len(nucleos) <= 1:
        return [palabra]

    # 2) cortes: repartir las consonantes que hay entre dos nucleos
    cortes: list[int] = []
    for (_, fin_a), (ini_b, _) in zip(nucleos, nucleos[1:]):
        consonantes = bajo[fin_a:ini_b]
        cuantas = len(consonantes)
        if cuantas == 0:
            corte = ini_b                      # hiato: pa-is
        elif cuantas == 1:
            corte = fin_a                      # V-CV
        elif cuantas == 2:
            corte = fin_a if consonantes in INSEPARABLES else fin_a + 1
        elif cuantas == 3:
            corte = fin_a + 1 if consonantes[1:] in INSEPARABLES else fin_a + 2
        else:
            corte = fin_a + 2                  # abs-trac-to
        cortes.append(corte)

    trozos = []
    anterior = 0
    for corte in cortes:
        if corte <= anterior or corte >= n:
            continue
        trozos.append(palabra[anterior:corte])
        anterior = corte
    trozos.append(palabra[anterior:])
    return [t for t in trozos if t]


# ---------------------------------------------------------------------------
# Ingles
# ---------------------------------------------------------------------------

_VOCALES_EN = set("aeiouy")
# Digrafos que suenan a una sola vocal.
_DIGRAFOS_EN = ("ai", "au", "aw", "ay", "ea", "ee", "ei", "eu", "ew", "ey",
                "ie", "oa", "oe", "oi", "oo", "ou", "ow", "oy", "ue", "ui")
_SUFIJOS_EN = ("tion", "sion", "ment", "ness", "less", "ful", "ing", "ed",
               "er", "est", "ly", "able", "ible")

_pyphen = None
_pyphen_probado = False


def _cargar_pyphen():
    """pyphen si esta instalado. Es opcional a proposito: sin el, heuristico."""
    global _pyphen, _pyphen_probado
    if _pyphen_probado:
        return _pyphen
    _pyphen_probado = True
    try:
        import pyphen  # type: ignore

        _pyphen = pyphen.Pyphen(lang="en_US")
    except Exception:
        _pyphen = None
    return _pyphen


def dividir_ingles(palabra: str) -> list[str]:
    guionador = _cargar_pyphen()
    if guionador is not None:
        trozos = guionador.inserted(palabra, hyphen="\x00").split("\x00")
        return [t for t in trozos if t] or [palabra]
    return _dividir_ingles_heuristico(palabra)


# Consonantes que suenan como una sola y NUNCA se parten por la mitad.
_DIGRAFOS_CONS_EN = ("th", "ch", "sh", "ph", "wh", "gh", "ck", "ng", "qu",
                     "kn", "wr", "gn", "sc")


def _dividir_ingles_heuristico(palabra: str) -> list[str]:
    """Sin diccionario: grupos vocalicos, digrafos y la regla de la 'e' muda.

    No pretende ser correcto siempre; pretende no ser ridiculo. Para el karaoke
    un corte de mas o de menos se nota mucho menos que una linea sin animar.
    """
    if len(palabra) <= 3:
        return [palabra]
    bajo = palabra.lower()
    n = len(bajo)

    def es_vocal(indice: int) -> bool:
        ch = bajo[indice]
        if ch != "y":
            return ch in _VOCALES_EN
        # 'y' es consonante al principio de palabra o antes de vocal (yes, yellow)
        if indice == 0:
            return False
        if indice + 1 < n and bajo[indice + 1] in "aeiou":
            return False
        return True

    nucleos: list[tuple[int, int]] = []
    i = 0
    while i < n:
        if not es_vocal(i):
            i += 1
            continue
        inicio = i
        i += 1
        while i < n and es_vocal(i) and bajo[i - 1:i + 1] in _DIGRAFOS_EN:
            i += 1
        nucleos.append((inicio, i))
    # 'e' muda final: 'ho-pe' se lee 'hope', pero 'ta-ble' y 'fi-re' se cantan.
    if len(nucleos) >= 2 and nucleos[-1][1] == n and bajo.endswith("e"):
        if not bajo.endswith(("le", "re")):
            nucleos.pop()
    if len(nucleos) <= 1:
        return [palabra]

    cortes: list[int] = []
    for (_, fin_a), (ini_b, _) in zip(nucleos, nucleos[1:]):
        consonantes = bajo[fin_a:ini_b]
        cuantas = len(consonantes)
        if cuantas == 0:
            corte = ini_b
        elif cuantas == 1:
            corte = fin_a                      # V-CV, la costumbre inglesa
        elif consonantes in _DIGRAFOS_CONS_EN:
            corte = fin_a                      # no-thing, tea-cher
        elif consonantes.endswith("le") or consonantes.endswith("re"):
            corte = fin_a + cuantas - 2        # ta-ble, ap-ple
        else:
            corte = fin_a + cuantas // 2       # dobles: run-ning
            # nunca partir un digrafo por la mitad
            if bajo[corte - 1:corte + 1] in _DIGRAFOS_CONS_EN:
                corte -= 1
        cortes.append(corte)

    trozos, anterior = [], 0
    for corte in cortes:
        if corte <= anterior or corte >= n:
            continue
        trozos.append(palabra[anterior:corte])
        anterior = corte
    trozos.append(palabra[anterior:])
    trozos = [t for t in trozos if t]
    # Un trozo sin vocal no es una silaba: se pega al anterior.
    fusionados: list[str] = []
    for trozo in trozos:
        if fusionados and not any(c in _VOCALES_EN for c in trozo.lower()):
            fusionados[-1] += trozo
        else:
            fusionados.append(trozo)
    return fusionados or [palabra]


# ---------------------------------------------------------------------------
# Interfaz
# ---------------------------------------------------------------------------


def dividir_palabra(palabra: str, idioma: str = "es") -> list[str]:
    """Parte una palabra. Si ya trae guiones puestos a mano, se respetan."""
    if "-" in palabra and len(palabra) > 2:
        # Guion escrito por Bruno: manda sobre cualquier regla.
        return [p for p in palabra.split("-") if p]
    return dividir_espanol(palabra) if idioma == "es" else dividir_ingles(palabra)


def dividir_linea(linea: str, idioma: str = "es") -> list[str]:
    """Parte una linea entera y devuelve las silabas EN CRUDO, sin marcadores.

    La puntuacion se queda pegada a la silaba que la lleva, que es lo que hace
    el humano: la coma va con la silaba anterior, no en un evento aparte.
    """
    salida: list[str] = []
    for bruto in linea.split():
        casco = _RE_PALABRA.search(bruto)
        if casco is None:
            if salida:
                salida[-1] += bruto
            else:
                salida.append(bruto)
            continue
        antes = bruto[:casco.start()]
        nucleo = casco.group(0)
        despues = bruto[casco.end():]
        trozos = dividir_palabra(nucleo, idioma)
        trozos[0] = antes + trozos[0]
        trozos[-1] = trozos[-1] + despues
        salida.extend(trozos)
    return salida


def contar(linea: str, idioma: str = "es") -> int:
    return len(dividir_linea(linea, idioma))
