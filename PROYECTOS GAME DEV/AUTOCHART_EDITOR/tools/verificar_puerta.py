"""Vigila la puerta de entrada del proyecto.

Una IA que abre un chat nuevo aqui lee `CLAUDE.md` y `docs/SIGUIENTE_CHAT.md`
antes de mirar una sola linea de codigo. Si esos dos crecen sin control, cada
arranque se come el contexto que hacia falta para trabajar.

El criterio es el que funciono: **se queda lo que se LEE, se va lo que se
CONSULTA**. Esta bateria pone numeros a eso, porque una regla que depende de que
alguien se acuerde no es una regla.

    python tools/verificar_puerta.py

Comprueba cuatro cosas:

1. La ruta obligatoria (`CLAUDE.md` + `docs/SIGUIENTE_CHAT.md`) no pasa del tope.
2. Hay **exactamente un** bloque de tarea siguiente, no dos.
3. Todos los enlaces a `.md` apuntan a ficheros que existen.
4. Los comandos que la documentacion manda correr existen de verdad.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Topes en KB. Salen de medir lo que costaba orientarse el 09-08-2026: la ruta
# obligatoria eran 32 KB (~8.000 tokens) y se bajo a ~21 KB moviendo el historial
# de decisiones a un documento que se consulta. El margen es para que quepa
# crecer un poco sin que salte a la primera.
PUERTA = [
    ("CLAUDE.md", 9),
    ("docs/SIGUIENTE_CHAT.md", 20),
]
TOPE_RUTA_KB = 26
BLOQUES_DE_TAREA = 1


def revisar() -> list[str]:
    fallos: list[str] = []
    total = 0.0

    for nombre, tope_kb in PUERTA:
        ruta = RAIZ / nombre
        if not ruta.is_file():
            fallos.append(f"falta {nombre}, que es parte de la puerta de entrada")
            continue
        kb = ruta.stat().st_size / 1024
        total += kb
        estado = "OK " if kb <= tope_kb else "MAL"
        print(f"  [{estado}] {nombre:26} {kb:5.1f} KB  (tope {tope_kb})")
        if kb > tope_kb:
            fallos.append(
                f"{nombre} ocupa {kb:.1f} KB y el tope son {tope_kb}. "
                f"Lo que se consulta va a docs/DECISIONES_MEDIDAS.md, no aqui."
            )

    print(f"  {'':7}{'ruta obligatoria':26} {total:5.1f} KB  (tope {TOPE_RUTA_KB})")
    if total > TOPE_RUTA_KB:
        fallos.append(
            f"la ruta de entrada entera ocupa {total:.1f} KB y el tope son {TOPE_RUTA_KB}"
        )

    siguiente = RAIZ / "docs" / "SIGUIENTE_CHAT.md"
    if siguiente.is_file():
        texto = siguiente.read_text(encoding="utf-8", errors="replace")
        bloques = len(re.findall(r"^TAREA:", texto, flags=re.MULTILINE))
        print(f"  [{'OK ' if bloques == BLOQUES_DE_TAREA else 'MAL'}] bloques de tarea      {bloques}")
        if bloques != BLOQUES_DE_TAREA:
            fallos.append(
                f"hay {bloques} bloques de tarea siguiente y tiene que haber "
                f"{BLOQUES_DE_TAREA}: el nuevo SUSTITUYE al viejo"
            )

    rotos: list[str] = []
    for doc in [RAIZ / "CLAUDE.md", *(RAIZ / "docs").glob("*.md"), RAIZ / "README.md"]:
        if not doc.is_file():
            continue
        for destino in re.findall(r"\]\(([^)]+\.md)\)", doc.read_text(encoding="utf-8", errors="replace")):
            if destino.startswith(("http://", "https://")):
                continue
            if not (doc.parent / destino).is_file():
                rotos.append(f"{doc.relative_to(RAIZ)} -> {destino}")
    print(f"  [{'OK ' if not rotos else 'MAL'}] enlaces .md           {len(rotos)} rotos")
    fallos.extend(f"enlace roto: {r}" for r in rotos)

    prometidos = ["tools/banco.py", "tools/ver_patron.py", "tools/revisar_in_game.py",
                  "tools/medir_hopo.py", "tests/test_basico.py",
                  "docs/DECISIONES_MEDIDAS.md"]
    faltan = [p for p in prometidos if not (RAIZ / p).is_file()]
    print(f"  [{'OK ' if not faltan else 'MAL'}] ficheros citados      {len(faltan)} faltan")
    fallos.extend(f"la documentacion manda usar {p} y no existe" for p in faltan)

    return fallos


def main() -> int:
    print("[*] Puerta de entrada del proyecto")
    fallos = revisar()
    print()
    if fallos:
        for fallo in fallos:
            print(f"[X] {fallo}")
        return 1
    print("[OK] La puerta sigue barata de leer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
