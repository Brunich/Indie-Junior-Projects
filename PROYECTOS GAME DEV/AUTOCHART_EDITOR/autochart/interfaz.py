"""Una ventana pequena para no tener que escribir comandos.

    python -m autochart interfaz

Metes canciones, marcas que quieres (chart, letra, instalar), eliges
dificultades y le das al boton. Lo que sale en pantalla es lo que dicen los
validadores, no un "listo": si algo salio torcido, se lee ahi.

**La interfaz no tiene logica propia.** Llama exactamente a lo mismo que la
consola (`generate`, `letras`, `instalar_letras`). Si algun dia hace algo que
`autochart` no puede hacer desde la terminal, esta mal hecha: eso significa que
la regla se escribio aqui en vez de en su sitio.

`tkinter` viene con Python. Cero dependencias nuevas.
"""

from __future__ import annotations

import queue
import threading
import traceback
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BIBLIOTECA = Path.home() / "OneDrive" / "Documents" / "Clone Hero" / "Songs"
AUDIO = (".ogg", ".mp3", ".opus", ".wav", ".flac")


# ---------------------------------------------------------------------------
# El trabajo, sin nada de interfaz: se puede probar sin abrir una ventana
# ---------------------------------------------------------------------------


def procesar_una(entrada: Path, ajustes: dict, decir) -> None:
    """Una cancion, con lo que se haya marcado. `decir` escribe en el registro."""
    from .audio import analyse, pick_audio, pick_beat_audio
    from .export import export_song, read_song_ini
    from .generate import generate_chart
    from .validate import validate_chart

    nombre = entrada.name
    carpeta = entrada if entrada.is_dir() else None

    if ajustes["chart"]:
        audio = pick_audio(entrada)
        if audio is None:
            decir(f"  [X] {nombre}: no encuentro audio dentro")
            return
        pulso = pick_beat_audio(entrada) or audio
        info = read_song_ini(carpeta) if carpeta else {}
        titulo = info.get("name") or (carpeta.name if carpeta else entrada.stem)
        artista = info.get("artist") or "Desconocido"

        decir(f"  ... {nombre}: escuchando")
        analisis = analyse(audio, beat_audio_path=pulso)
        chart, informe = generate_chart(
            analisis, metadata={"Name": titulo, "Artist": artista}, profile=ajustes["perfil"],
            difficulties=tuple(ajustes["dificultades"]), seed=7,
        )
        destino = Path(ajustes["salida"]) / f"{artista} - {titulo} (AutoChart)"
        destino = export_song(chart, destino, audio, source_dir=carpeta,
                              name=titulo, artist=artista,
                              album=info.get("album", ""), genre=info.get("genre", ""),
                              year=info.get("year", ""), duration_s=analisis.duration)
        revision = validate_chart(chart, ajustes["perfil"])
        for dificultad, datos in informe.per_difficulty.items():
            decir(f"      {dificultad:<7} {datos['notas']:>5} notas  "
                  f"{datos['notas_por_segundo']:.2f} n/s  "
                  f"acordes {datos['acordes_pct']:.0f}%  SP {datos['star_power']}")
        for aviso in revision.warnings:
            decir(f"      [aviso] {aviso}")
        for error in revision.errors:
            decir(f"      [ERROR] {error}")
        decir(f"  [OK] {nombre}: chart en {destino.name}")

    if ajustes["letra"]:
        if carpeta is None:
            decir(f"  [--] {nombre}: la letra necesita una carpeta con song.ini")
        else:
            import sys as _sys

            _sys.path.insert(0, str(RAIZ / "tools"))
            import poner_letra  # type: ignore

            class _Args:
                pass

            args = _Args()
            args.salida = str(Path(ajustes["salida"]) / "letras")
            args.forzar = ajustes["forzar_letra"]
            args.sin_audio = False
            args.carpeta = str(carpeta)
            estado, detalle = poner_letra.procesar(carpeta, args)
            marca = {"ok": "[OK]", "ya": "[--]", "instrumental": "[IN]",
                     "sin_letra": "[  ]", "no_cuadra": "[!!]", "error": "[XX]"}.get(estado, "[?]")
            decir(f"  {marca} {nombre}: {detalle}")


def trabajar(entradas: list[Path], ajustes: dict, decir) -> None:
    from .corpus import load_profile

    perfil_path = RAIZ / "datos" / "perfil_corpus.json"
    ajustes["perfil"] = load_profile(perfil_path) if perfil_path.is_file() else None
    if ajustes["perfil"] is None:
        decir("[!] Sin perfil del corpus: corre `autochart minar` para afinar la densidad.")

    for indice, entrada in enumerate(entradas, 1):
        decir(f"[{indice}/{len(entradas)}] {entrada.name}")
        try:
            procesar_una(entrada, ajustes, decir)
        except Exception as fallo:
            decir(f"  [XX] {entrada.name}: {type(fallo).__name__}: {fallo}")
            decir("       " + traceback.format_exc().splitlines()[-2].strip())

    if ajustes["instalar"]:
        decir("")
        decir("Instalando las letras en la biblioteca (con respaldo)...")
        import sys as _sys

        _sys.path.insert(0, str(RAIZ / "tools"))
        import instalar_letras  # type: ignore

        class _Args:
            pass

        args = _Args()
        args.biblioteca = str(BIBLIOTECA)
        args.letras = str(Path(ajustes["salida"]) / "letras")
        args.respaldo = str(RAIZ / "salida" / "respaldo_letras")
        args.probar = False
        args.deshacer = False
        import io
        import contextlib

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            instalar_letras.instalar(args)
        for linea in buffer.getvalue().splitlines():
            decir("  " + linea)

    decir("")
    decir("Listo. Si instalaste algo: SCAN SONGS en Clone Hero.")


# ---------------------------------------------------------------------------
# La ventana
# ---------------------------------------------------------------------------


def abrir() -> int:
    import tkinter as tk
    from tkinter import filedialog, ttk

    raiz = tk.Tk()
    raiz.title("AutoChart")
    raiz.geometry("880x620")

    entradas: list[Path] = []
    mensajes: queue.Queue = queue.Queue()

    marco = ttk.Frame(raiz, padding=10)
    marco.pack(fill="both", expand=True)

    # --- canciones ---------------------------------------------------------
    ttk.Label(marco, text="Canciones", font=("", 10, "bold")).pack(anchor="w")
    caja = tk.Listbox(marco, height=7, selectmode="extended")
    caja.pack(fill="x", pady=(2, 6))

    def refrescar() -> None:
        caja.delete(0, "end")
        for ruta in entradas:
            caja.insert("end", f"{ruta.name}    [{ruta.parent.name}]")

    def anadir_carpetas() -> None:
        elegida = filedialog.askdirectory(title="Carpeta de cancion, o una que las contenga",
                                          initialdir=str(BIBLIOTECA))
        if not elegida:
            return
        ruta = Path(elegida)
        hijas = [d for d in sorted(ruta.iterdir()) if d.is_dir()
                 and ((d / "song.ini").is_file() or any(d.glob("*.ogg")) or any(d.glob("*.mp3")))]
        nuevas = hijas if hijas else [ruta]
        for r in nuevas:
            if r not in entradas:
                entradas.append(r)
        refrescar()

    def anadir_audio() -> None:
        for elegido in filedialog.askopenfilenames(
                title="Archivos de audio",
                filetypes=[("Audio", " ".join(f"*{e}" for e in AUDIO)), ("Todos", "*.*")]):
            ruta = Path(elegido)
            if ruta not in entradas:
                entradas.append(ruta)
        refrescar()

    def quitar() -> None:
        for indice in sorted(caja.curselection(), reverse=True):
            entradas.pop(indice)
        refrescar()

    botones = ttk.Frame(marco)
    botones.pack(fill="x")
    ttk.Button(botones, text="Anadir carpeta...", command=anadir_carpetas).pack(side="left")
    ttk.Button(botones, text="Anadir audio...", command=anadir_audio).pack(side="left", padx=4)
    ttk.Button(botones, text="Quitar", command=quitar).pack(side="left")
    ttk.Button(botones, text="Vaciar",
               command=lambda: (entradas.clear(), refrescar())).pack(side="left", padx=4)

    # --- que hacer ---------------------------------------------------------
    opciones = ttk.LabelFrame(marco, text="Que hacer", padding=8)
    opciones.pack(fill="x", pady=8)

    v_chart = tk.BooleanVar(value=True)
    v_letra = tk.BooleanVar(value=True)
    v_instalar = tk.BooleanVar(value=False)
    v_forzar = tk.BooleanVar(value=False)
    ttk.Checkbutton(opciones, text="Generar el chart", variable=v_chart).grid(row=0, column=0, sticky="w")
    ttk.Checkbutton(opciones, text="Poner letra de karaoke", variable=v_letra).grid(row=0, column=1, sticky="w", padx=14)
    ttk.Checkbutton(opciones, text="Rehacer la letra que ya tenga", variable=v_forzar).grid(row=1, column=1, sticky="w", padx=14)
    ttk.Checkbutton(opciones, text="Instalar en la biblioteca (guarda el original)",
                    variable=v_instalar).grid(row=1, column=0, sticky="w")

    dif = ttk.LabelFrame(marco, text="Dificultades", padding=8)
    dif.pack(fill="x")
    v_dif = {d: tk.BooleanVar(value=True) for d in ("Easy", "Medium", "Hard", "Expert")}
    nombres = {"Easy": "Facil", "Medium": "Medio", "Hard": "Dificil", "Expert": "Experto"}
    for columna, clave in enumerate(v_dif):
        ttk.Checkbutton(dif, text=nombres[clave], variable=v_dif[clave]).grid(row=0, column=columna, padx=8)

    # --- registro ----------------------------------------------------------
    ttk.Label(marco, text="Lo que va pasando", font=("", 10, "bold")).pack(anchor="w", pady=(8, 0))
    registro = tk.Text(marco, height=15, wrap="none", font=("Consolas", 9))
    registro.pack(fill="both", expand=True, pady=(2, 6))
    barra = ttk.Progressbar(marco, mode="indeterminate")
    barra.pack(fill="x")

    def decir(texto: str) -> None:
        mensajes.put(texto)

    def vaciar_cola() -> None:
        while True:
            try:
                texto = mensajes.get_nowait()
            except queue.Empty:
                break
            registro.insert("end", texto + "\n")
            registro.see("end")
        raiz.after(120, vaciar_cola)

    boton = ttk.Button(marco, text="Hacerlo")
    boton.pack(pady=8)

    def lanzar() -> None:
        if not entradas:
            decir("[!] No has metido ninguna cancion.")
            return
        elegidas = [d for d, v in v_dif.items() if v.get()]
        if v_chart.get() and not elegidas:
            decir("[!] Marca al menos una dificultad.")
            return
        ajustes = {
            "chart": v_chart.get(), "letra": v_letra.get(), "instalar": v_instalar.get(),
            "forzar_letra": v_forzar.get(), "dificultades": elegidas,
            "salida": str(RAIZ / "salida"),
        }
        boton.state(["disabled"])
        barra.start(12)
        registro.delete("1.0", "end")

        def hilo() -> None:
            try:
                trabajar(list(entradas), ajustes, decir)
            finally:
                raiz.after(0, lambda: (barra.stop(), boton.state(["!disabled"])))

        threading.Thread(target=hilo, daemon=True).start()

    boton.configure(command=lanzar)
    vaciar_cola()
    decir("Mete canciones, marca que quieres y dale a Hacerlo.")
    decir("Lo generado va a salida/. Instalar guarda el original y se puede deshacer con:")
    decir("    python -m autochart instalar --deshacer")
    raiz.mainloop()
    return 0
