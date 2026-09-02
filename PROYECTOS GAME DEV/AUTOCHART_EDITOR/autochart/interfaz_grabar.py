"""La ventana de grabar tocando.

    python -m autochart grabar

Eliges la cancion, le das a grabar y tocas con las teclas de Clone Hero. Al
parar se escribe el chart -- entero, o solo el tramo que hayas puesto.

**Esta ventana no decide nada.** Todo lo que piensa esta en `grabar.py` y
`editar.py`, que se prueban sin abrir una ventana ni tener un mando. Si algun dia
esta ventana hace algo que no se puede hacer sin ella, esta mal hecha.

`tkinter` viene con Python y el audio suena con `winsound`: cero dependencias
nuevas, igual que `interfaz.py`.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LATENCIA = RAIZ / "datos" / "latencia.json"


def leer_latencia() -> float:
    """La latencia calibrada, en ms. 0 si nadie la ha medido todavia."""
    try:
        return float(json.loads(LATENCIA.read_text(encoding="utf-8"))["ms"])
    except Exception:
        return 0.0


def guardar_latencia(ms: float, dispersion: float, cuantos: int) -> None:
    """Guardar la latencia medida, con la prueba de lo buena que es.

    Se guardan tambien la dispersion y cuantas pulsaciones valieron **porque una
    latencia sin eso parece exacta**: 90 ms medidos con 4 taps que bailan 80 ms
    entre ellos no es lo mismo que 90 ms con 16 que bailan 10, y quien lo lea
    dentro de un mes tiene que poder distinguirlo.
    """
    LATENCIA.parent.mkdir(parents=True, exist_ok=True)
    LATENCIA.write_text(json.dumps(
        {"ms": round(ms, 1), "dispersion_ms": round(dispersion, 1), "pulsaciones": cuantos},
        indent=2), encoding="utf-8")


def abrir() -> int:
    import tkinter as tk
    from tkinter import filedialog, ttk

    from . import chartio, editar, grabar

    raiz = tk.Tk()
    raiz.title("AutoChart — grabar tocando")
    raiz.geometry("640x460")

    estado = {"carpeta": None, "sesion": None, "clics": None, "modo": None, "tmp": None}
    marco = ttk.Frame(raiz, padding=10)
    marco.pack(fill="both", expand=True)

    v_cancion = tk.StringVar(value="(ninguna)")
    v_latencia = tk.StringVar()
    v_desde = tk.StringVar(value="0")
    v_hasta = tk.StringVar(value="")
    v_division = tk.StringVar(value="4")
    v_pista = tk.StringVar(value="ExpertSingle")

    registro = tk.Text(marco, height=12, wrap="word")

    def decir(texto: str) -> None:
        registro.insert("end", texto + "\n")
        registro.see("end")
        raiz.update_idletasks()

    def refrescar_latencia() -> None:
        ms = leer_latencia()
        v_latencia.set(f"latencia calibrada: {ms:.0f} ms" if ms
                       else "latencia SIN calibrar — hazlo antes de grabar")

    def elegir() -> None:
        ruta = filedialog.askdirectory(title="La carpeta de la cancion")
        if not ruta:
            return
        carpeta = Path(ruta)
        audio = grabar.elegir_audio(carpeta)
        if audio is None:
            decir(f"[X] {carpeta.name}: no encuentro audio ahi dentro")
            return
        estado["carpeta"] = carpeta
        v_cancion.set(carpeta.name)
        decir(f"[*] {carpeta.name}  (audio: {audio.name})")
        chart = carpeta / "notes.chart"
        if chart.is_file():
            existente = chartio.parse_chart(chart)
            golpes = len(existente.tracks.get(v_pista.get(), chartio.Track("", "")).notes)
            decir(f"    ya tiene chart: {golpes} notas en {v_pista.get()}. "
                  f"Si pones un tramo, solo se cambia ese.")

    def calibrar() -> None:
        if estado["modo"]:
            return
        tmp = Path(tempfile.mkdtemp(prefix="autochart_cal_"))
        wav, momentos = grabar.pista_de_calibrado(tmp / "clics.wav")
        estado.update(modo="calibrar", clics=momentos, tmp=tmp,
                      sesion=grabar.SesionDeGrabacion())
        decir("")
        decir(f"[CALIBRAR] van a sonar {len(momentos)} clics, uno por segundo.")
        decir("           dale a CUALQUIERA de las cinco teclas con cada clic.")
        estado["sesion"].empezar()
        grabar.sonar(wav)
        raiz.after(int((momentos[-1] + 1.5) * 1000), terminar_calibrado)

    def terminar_calibrado() -> None:
        if estado["modo"] != "calibrar":
            return
        grabar.callar()
        toques = estado["sesion"].parar()
        estado["modo"] = None
        ms, valen, dispersion = grabar.calibrar_desfase(
            [t for t, _ in toques], estado["clics"])
        if valen < 4:
            decir(f"[X] solo valieron {valen} pulsaciones: no me fio. Repitelo.")
            return
        guardar_latencia(ms, dispersion, valen)
        refrescar_latencia()
        decir(f"[OK] tu latencia son {ms:.0f} ms  "
              f"({valen} pulsaciones, bailan {dispersion:.0f} ms entre ellas)")
        if dispersion > 40.0:
            decir("     OJO: bailan mucho. La cifra es la mediana de un pulso "
                  "irregular, asi que vale menos de lo que parece.")

    def grabar_ya() -> None:
        if estado["modo"] or estado["carpeta"] is None:
            if estado["carpeta"] is None:
                decir("[X] elige antes una cancion")
            return
        audio = grabar.elegir_audio(estado["carpeta"])
        desde = float(v_desde.get() or 0)
        hasta = float(v_hasta.get()) if v_hasta.get().strip() else None
        tmp = Path(tempfile.mkdtemp(prefix="autochart_grab_"))
        decir("")
        decir(f"[GRABAR] preparando el audio{'' if hasta is None else f' ({desde:.0f}-{hasta:.0f} s)'}...")
        wav = grabar.preparar_wav(audio, tmp / "tramo.wav", desde, hasta)
        estado.update(modo="grabar", tmp=tmp,
                      sesion=grabar.SesionDeGrabacion(desde_s=desde))
        decir("         toca con A S J K L. Dale a PARAR cuando acabes.")
        estado["sesion"].empezar()
        grabar.sonar(wav)
        boton_grabar.config(text="PARAR", command=parar_grabacion)

    def parar_grabacion() -> None:
        if estado["modo"] != "grabar":
            return
        grabar.callar()
        toques = estado["sesion"].parar()
        estado["modo"] = None
        boton_grabar.config(text="Grabar", command=grabar_ya)
        if not toques:
            decir("[X] no tocaste nada")
            return

        carpeta: Path = estado["carpeta"]
        ruta = carpeta / "notes.chart"
        division = int(v_division.get() or 4)
        pista = v_pista.get()
        if ruta.is_file():
            chart = chartio.parse_chart(ruta)
        else:
            chart = chartio.Chart(resolution=192)
            chart.tempos = [chartio.TempoEvent(0, 120.0)]
            chart.tracks[pista] = chartio.Track(pista.replace("Single", ""), "Single", [])
            decir("     no habia chart: se crea uno nuevo a 120 BPM. "
                  "Si la cancion no va a 120, arreglalo con `autochart alinear --tempo`.")

        notas, informe = editar.desde_toques(
            toques, chart, division, desfase_ms=leer_latencia())
        decir(f"[OK] {informe.toques} golpes -> {informe.notas} notas "
              f"(latencia {informe.desfase_ms:.0f} ms, rejilla 1/{division})")
        for aviso in informe.avisos:
            decir(f"     [aviso] {aviso}")

        if v_hasta.get().strip():
            desde_tick = chart.seconds_to_tick(float(v_desde.get() or 0))
            hasta_tick = chart.seconds_to_tick(float(v_hasta.get()))
            inf2 = editar.sustituir_tramo(chart, notas, desde_tick, hasta_tick, pista)
            for aviso in inf2.avisos:
                decir(f"     {aviso}")
        else:
            chart.tracks[pista] = chartio.Track(
                pista.replace("Single", ""), "Single", notas)
            decir("     el chart entero se sustituye por lo tocado")

        chartio.write_chart(chart, ruta)
        decir(f"[OK] escrito en {ruta}")
        decir("     Haz SCAN SONGS en Clone Hero o sigue sonando el de la cache.")

    def tecla(evento) -> None:
        sesion = estado["sesion"]
        if sesion is None or not sesion.en_marcha:
            return
        carril = grabar.TECLAS_POR_CARRIL.get(evento.keysym.lower())
        if estado["modo"] == "calibrar":
            if carril is not None or evento.keysym == "space":
                sesion.golpe(0)
        elif carril is not None:
            sesion.golpe(carril)

    # ── la ventana ─────────────────────────────────────────────────────────
    arriba = ttk.Frame(marco)
    arriba.pack(fill="x")
    ttk.Button(arriba, text="Elegir cancion...", command=elegir).pack(side="left")
    ttk.Label(arriba, textvariable=v_cancion).pack(side="left", padx=8)

    fila = ttk.Frame(marco)
    fila.pack(fill="x", pady=8)
    ttk.Label(fila, text="tramo, en segundos   desde").pack(side="left")
    ttk.Entry(fila, textvariable=v_desde, width=7).pack(side="left", padx=4)
    ttk.Label(fila, text="hasta").pack(side="left")
    ttk.Entry(fila, textvariable=v_hasta, width=7).pack(side="left", padx=4)
    ttk.Label(fila, text="(vacio = la cancion entera)").pack(side="left", padx=4)

    fila2 = ttk.Frame(marco)
    fila2.pack(fill="x")
    ttk.Label(fila2, text="rejilla 1/").pack(side="left")
    ttk.Combobox(fila2, textvariable=v_division, width=4,
                 values=["1", "2", "3", "4", "6", "8"]).pack(side="left", padx=4)
    ttk.Label(fila2, text="pista").pack(side="left", padx=(12, 0))
    ttk.Combobox(fila2, textvariable=v_pista, width=16,
                 values=["ExpertSingle", "HardSingle", "MediumSingle", "EasySingle"]
                 ).pack(side="left", padx=4)

    fila3 = ttk.Frame(marco)
    fila3.pack(fill="x", pady=10)
    ttk.Button(fila3, text="Calibrar mi latencia", command=calibrar).pack(side="left")
    ttk.Label(fila3, textvariable=v_latencia).pack(side="left", padx=10)

    boton_grabar = ttk.Button(marco, text="Grabar", command=grabar_ya)
    boton_grabar.pack(pady=4)

    ttk.Label(marco, text="teclas:  A S J K L   (las de Clone Hero)").pack()
    registro.pack(fill="both", expand=True, pady=(10, 0))

    refrescar_latencia()
    decir("Primero calibra tu latencia. Sin eso, todo lo que toques sale corrido")
    decir("y no se puede adivinar: desde la fase, la latencia es indistinguible")
    decir("modulo una subdivision. Se mide una vez y ya queda guardada.")
    raiz.bind("<Key>", tecla)
    raiz.mainloop()
    return 0
