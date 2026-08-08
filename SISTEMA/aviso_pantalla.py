# -*- coding: utf-8 -*-
"""AURORA · Un aviso que sale ENCIMA de lo que estés haciendo

Anuar lo pidió el 2026-08-06, con la campaña escolar ya enviándose: *"no solo
en panel, el aviso que aparezca encima de lo que esté en pantalla"*. Y tiene
razón: él pasa el día en Aspire y en Corel, no mirando el panel de AURORA. Un
aviso que vive dentro del panel no lo ve nunca.

Sale abajo a la derecha, sobre cualquier ventana, y se quita solo. No roba el
foco del teclado —eso sería peor que no avisar: le comería una tecla en medio
de un trazo— solo se pone al frente.

Corre en su PROPIO proceso a propósito: si algo falla al dibujar la ventana,
AURORA no se entera y sigue contestando. Un aviso jamás debe tumbar lo que
está avisando.

Correr:
    python SISTEMA/aviso_pantalla.py "Fernanda" "quiere el de primaria"
"""
from __future__ import annotations
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

SEGUNDOS = 25           # cuánto se queda antes de irse solo
ANCHO, ALTO = 380, 150

COLORES = {
    "cliente":  ("#0b3d2e", "#34d399", "💬"),   # una clienta escribió
    "atencion": ("#4a2c00", "#fbbf24", "⚠️"),   # AURORA no pudo sola
    "venta":    ("#12324f", "#60a5fa", "💰"),   # hay dinero de por medio
}


def mostrar(titulo: str, cuerpo: str, tipo: str = "cliente",
            segundos: int = SEGUNDOS) -> dict:
    """Saca el aviso sobre todo lo demás. Devuelve qué pasó, sin reventar."""
    try:
        import tkinter as tk
    except Exception as e:
        return {"status": "SIN_TKINTER", "detalle": str(e)[:80]}

    fondo, acento, icono = COLORES.get(tipo, COLORES["cliente"])

    try:
        v = tk.Tk()
        v.overrideredirect(True)            # sin barra de título
        v.attributes("-topmost", True)      # ENCIMA DE TODO
        v.attributes("-alpha", 0.97)
        v.configure(bg=acento)

        # Abajo a la derecha, sin taparle la barra de tareas.
        x = v.winfo_screenwidth() - ANCHO - 20
        y = v.winfo_screenheight() - ALTO - 70
        v.geometry(f"{ANCHO}x{ALTO}+{x}+{y}")

        marco = tk.Frame(v, bg=fondo)
        marco.place(x=4, y=4, width=ANCHO - 8, height=ALTO - 8)

        tk.Label(marco, text=f"{icono}  {titulo}", bg=fondo, fg=acento,
                 font=("Segoe UI", 12, "bold"), anchor="w",
                 wraplength=ANCHO - 40, justify="left").place(x=14, y=12)

        tk.Label(marco, text=cuerpo, bg=fondo, fg="#e5e7eb",
                 font=("Segoe UI", 10), anchor="nw", justify="left",
                 wraplength=ANCHO - 40).place(x=14, y=46, width=ANCHO - 40,
                                              height=ALTO - 70)

        tk.Label(marco, text="✕", bg=fondo, fg="#9ca3af",
                 font=("Segoe UI", 11), cursor="hand2").place(
                     x=ANCHO - 40, y=10)

        # Un clic en cualquier parte lo quita: si ya lo leyó, que se vaya.
        for w in (v, marco):
            w.bind("<Button-1>", lambda _e: v.destroy())

        v.after(max(3, segundos) * 1000, v.destroy)
        # NO se roba el foco del teclado: si le come una tecla mientras
        # traza en Aspire, el aviso hace más daño del que evita.
        v.mainloop()
        return {"status": "OK"}
    except Exception as e:
        return {"status": "ERROR", "detalle": f"{type(e).__name__}: {str(e)[:90]}"}


def avisar(titulo: str, cuerpo: str, tipo: str = "cliente") -> dict:
    """Lanza el aviso SIN esperar a que se cierre.

    AURORA no se puede quedar parada 25 segundos mirando una ventanita: tiene
    que seguir contestando WhatsApp. Por eso el aviso se va a otro proceso.
    """
    import subprocess
    try:
        return {"status": "LANZADO", "pid": subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()),
             titulo, cuerpo, tipo],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).pid}
    except Exception as e:
        return {"status": "ERROR", "detalle": f"{type(e).__name__}: {str(e)[:90]}"}


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    titulo = args[0]
    cuerpo = args[1] if len(args) > 1 else ""
    tipo = args[2] if len(args) > 2 else "cliente"
    mostrar(titulo, cuerpo, tipo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
