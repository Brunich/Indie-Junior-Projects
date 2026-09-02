"""Copia las letras generadas a la biblioteca, con respaldo y con vuelta atras.

    python tools/instalar_letras.py --probar     # dice que haria, sin tocar nada
    python tools/instalar_letras.py              # instala
    python tools/instalar_letras.py --deshacer          # devuelve TODOS los originales
    python tools/instalar_letras.py --devolver-humanas  # solo las que ya estaban a mano

**Esta es la unica herramienta del repo que escribe en la biblioteca**, y por eso
hace tres cosas antes:

1. **Guarda el original** en `salida/respaldo_letras/` ANTES de pisarlo. Si ya
   hay respaldo de esa cancion no lo vuelve a guardar: el respaldo es siempre el
   chart de antes de que AutoChart tocara nada.
2. **Solo escribe el `notes.chart` / `notes.mid`.** No toca el audio, ni el
   `song.ini`, ni las portadas.
3. **Comprueba que el destino existe** y que el fichero nuevo se lee bien antes
   de copiarlo encima.

Despues hay que hacer **SCAN SONGS** en el juego, o sigue sonando el de la cache.

Nota de entorno: hasta el 21-08-2026 estaba escrito que `OneDrive\\Documents`
rechazaba las escrituras de consola. **Ya no es cierto** -- comprobado
escribiendo y borrando un fichero de prueba. Por eso existe esta herramienta.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import json  # noqa: E402

from autochart import voz  # noqa: E402

BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
LETRAS = RAIZ / "salida" / "letras"
RESPALDO = RAIZ / "salida" / "respaldo_letras"


_REVISOR = None
_PERFIL = None


def _revisor():
    """El mismo validador que `autochart revisar-letra`, no una copia."""
    global _REVISOR
    if _REVISOR is None:
        import importlib.util

        fichero = Path(__file__).resolve().parent / "revisar_letra.py"
        spec = importlib.util.spec_from_file_location("_revisar_letra", fichero)
        _REVISOR = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_REVISOR)
    return _REVISOR


def _perfil() -> dict:
    global _PERFIL
    if _PERFIL is None:
        ruta = Path(__file__).resolve().parent.parent / "datos" / "perfil_voz.json"
        _PERFIL = json.loads(ruta.read_text(encoding="utf-8"))
    return _PERFIL


def destino_de(nombre: str, biblioteca: Path) -> Path | None:
    for pack in sorted(p for p in biblioteca.iterdir() if p.is_dir()):
        candidata = pack / nombre
        if candidata.is_dir():
            return candidata
    return None


def instalar(args) -> int:
    biblioteca = Path(args.biblioteca)
    origen = Path(args.letras)
    respaldo = Path(args.respaldo)
    if not origen.is_dir():
        print(f"[X] No hay letras generadas en {origen}")
        return 2

    puestas = saltadas = fallos = 0
    for carpeta in sorted(d for d in origen.iterdir() if d.is_dir()):
        ficheros = [f for f in carpeta.iterdir() if f.name in ("notes.chart", "notes.mid")]
        if not ficheros:
            continue
        destino = destino_de(carpeta.name, biblioteca)
        if destino is None:
            print(f"  [X] {carpeta.name[:46]:46} ya no esta en la biblioteca")
            fallos += 1
            continue

        # que lo que voy a copiar se lea bien ANTES de pisar nada
        try:
            leida = voz.leer_voz(carpeta)
            if leida is None or len(leida.silabas) < 10:
                raise ValueError("la letra no se lee")
        except Exception as error:
            print(f"  [X] {carpeta.name[:46]:46} no se puede leer: {error}")
            fallos += 1
            continue

        # Y que PASE el validador. Antes solo se comprobaba que se leyera, y en
        # la primera tanda se instalaron 4 charts que revisar_letra marcaba con
        # error: leerse y estar bien no son lo mismo.
        errores, _, _ = _revisor().revisar(carpeta, _perfil())
        if errores:
            print(f"  [X] {carpeta.name[:46]:46} NO se instala: {errores[0]}")
            fallos += 1
            continue

        for fichero in ficheros:
            actual = destino / fichero.name
            copia = respaldo / carpeta.name / fichero.name
            if args.probar:
                print(f"  [..] {carpeta.name[:46]:46} -> {destino.parent.name}/")
                saltadas += 1
                continue
            if actual.is_file() and not copia.is_file():
                copia.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(actual, copia)
            try:
                shutil.copy2(fichero, actual)
                puestas += 1
                print(f"  [OK] {carpeta.name[:46]:46} {len(leida.silabas):4d} silabas")
            except Exception as error:
                print(f"  [X] {carpeta.name[:46]:46} no se pudo copiar: {error}")
                fallos += 1

    if args.probar:
        print(f"\n[..] Prueba: se instalarian {saltadas}. Nada tocado.")
        return 0
    print(f"\n[OK] {puestas} instaladas | {fallos} fallos")
    print(f"     respaldo de los originales en: {respaldo}")
    print(f"\n     Ahora, SCAN SONGS en Clone Hero o sigue sonando el de la cache.")
    print(f"     Para volver atras:  python tools/instalar_letras.py --deshacer")
    return 1 if fallos else 0


def deshacer(args) -> int:
    biblioteca = Path(args.biblioteca)
    respaldo = Path(args.respaldo)
    if not respaldo.is_dir():
        print(f"[X] No hay respaldo en {respaldo}")
        return 2
    vueltas = fallos = 0
    for carpeta in sorted(d for d in respaldo.iterdir() if d.is_dir()):
        destino = destino_de(carpeta.name, biblioteca)
        if destino is None:
            print(f"  [X] {carpeta.name[:46]:46} ya no esta en la biblioteca")
            fallos += 1
            continue
        for fichero in carpeta.iterdir():
            try:
                shutil.copy2(fichero, destino / fichero.name)
                vueltas += 1
                print(f"  [OK] {carpeta.name[:46]:46} original devuelto")
            except Exception as error:
                print(f"  [X] {carpeta.name[:46]:46} {error}")
                fallos += 1
    print(f"\n[OK] {vueltas} devueltas | {fallos} fallos.  Haz SCAN SONGS.")
    return 1 if fallos else 0


def devolver_humanas(args) -> int:
    """Devuelve los originales que YA tenian letra escrita a mano.

    Por que hace falta: `poner_letra --forzar` sobre la biblioteca entera
    reescribe TODO, y 112 de las 312 canciones ya tenian letra hecha por una
    persona -- 42 655 silabas cronometradas a mano, con su altura de melodia.
    La nuestra esta verificada contra el audio, pero la de un charter es mejor:
    la puso oyendo la cancion, no midiendo energia.

    Esto separa las dos cosas: donde el original tenia letra, se devuelve; donde
    no habia nada, se deja la nuestra. `--deshacer` lo tira todo; esto no.
    """
    biblioteca = Path(args.biblioteca)
    respaldo = Path(args.respaldo)
    if not respaldo.is_dir():
        print(f"[X] No hay respaldo en {respaldo}")
        return 2

    devueltas = dejadas = fallos = 0
    for carpeta in sorted(d for d in respaldo.iterdir() if d.is_dir()):
        try:
            original = voz.leer_voz(carpeta)
        except Exception:
            original = None
        if original is None or len(original.silabas) < 20:
            dejadas += 1
            continue                      # no habia letra: la nuestra se queda

        destino = destino_de(carpeta.name, biblioteca)
        if destino is None:
            print(f"  [X] {carpeta.name[:46]:46} ya no esta en la biblioteca")
            fallos += 1
            continue
        for fichero in carpeta.iterdir():
            try:
                shutil.copy2(fichero, destino / fichero.name)
                devueltas += 1
                print(f"  [OK] {carpeta.name[:46]:46} devuelta la humana "
                      f"({len(original.silabas)} silabas)")
            except Exception as error:
                print(f"  [X] {carpeta.name[:46]:46} {error}")
                fallos += 1

    print(f"\n[OK] {devueltas} letras humanas devueltas | {dejadas} se quedan con la nuestra "
          f"| {fallos} fallos")
    print("     Haz SCAN SONGS en Clone Hero.")
    return 1 if fallos else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Instala las letras en la biblioteca")
    parser.add_argument("--biblioteca", default=str(BIBLIOTECA))
    parser.add_argument("--letras", default=str(LETRAS))
    parser.add_argument("--respaldo", default=str(RESPALDO))
    parser.add_argument("--probar", action="store_true", help="Dice que haria, sin tocar")
    parser.add_argument("--deshacer", action="store_true", help="Devuelve TODOS los originales")
    parser.add_argument("--devolver-humanas", action="store_true",
                        help="Devuelve solo las que ya tenian letra hecha a mano")
    args = parser.parse_args(argv)
    if args.deshacer:
        return deshacer(args)
    if args.devolver_humanas:
        return devolver_humanas(args)
    return instalar(args)


if __name__ == "__main__":
    raise SystemExit(main())
