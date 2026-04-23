# -*- coding: utf-8 -*-
"""
Dashboard timer — GUI tkinter (CPython su PC).

Per IronPython 2.x / ClassicAssist usa invece:
    timer_dashboard_ironpython.py  (WinForms, niente tkinter)

Avvio tkinter: python timer_dashboard_gui.py

Imposta in cima al file FONT_SIZE e WINDOW_ALWAYS_ON_TOP.
"""

from __future__ import print_function

# Nome modulo: tkinter (T-K-I-N-T-E-R). Non "tktinker".
# Avvia con il Python di sistema:  python timer_dashboard_gui.py
# Non eseguire dentro ClassicAssist / IronPython (lì non c'è tkinter).
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError as _e:
    import sys

    sys.stderr.write(
        "\n*** Impossibile importare tkinter ***\n\n"
        "1) Controlla di aver scritto tkinter (non tktinker).\n"
        "2) Usa il comando:  python timer_dashboard_gui.py  (terminal / PowerShell).\n"
        "3) Windows: reinstalla Python da https://www.python.org/downloads/\n"
        "   e in Customize assicurati che Tcl/Tk sia incluso (di default sì).\n"
        "4) Linux:  sudo apt install python3-tk   (Debian/Ubuntu)\n\n"
        "Errore originale: %s\n" % (_e,)
    )
    raise

# ---------------------------------------------------------------------------
# --- Impostazioni utente ---
# ---------------------------------------------------------------------------
FONT_SIZE = 12
FONT_FAMILY = "Segoe UI"

# True = finestra sempre sopra le altre (sempre visibile in primo piano)
WINDOW_ALWAYS_ON_TOP = True

# Aggiornamento display (ms); 100 = decimi di secondo visibili
UPDATE_INTERVAL_MS = 100

# ---------------------------------------------------------------------------


def _fmt_remaining(seconds):
    seconds = max(0.0, float(seconds))
    total = int(seconds)
    frac = seconds - total
    centis = int(frac * 100)  # 2 cifre
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    if h:
        return "{:d}:{:02d}:{:02d}.{:02d}".format(h, m, s, centis // 10)
    return "{:d}:{:02d}.{:02d}".format(m, s, centis // 10)


class TimerDashboard(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Timer dashboard")
        self.minsize(420, 320)
        self._base_font = (FONT_FAMILY, FONT_SIZE)
        self._bold_font = (FONT_FAMILY, FONT_SIZE, "bold")
        self._mono_font = ("Consolas", max(FONT_SIZE, 10))

        self.option_add("*Font", self._base_font)

        if WINDOW_ALWAYS_ON_TOP:
            self.attributes("-topmost", True)

        self._timers = []
        self._after_id = None

        self._build_add_bar()
        self._build_list_frame()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._schedule_tick()

    def _build_add_bar(self):
        f = ttk.Frame(self, padding=8)
        f.pack(fill=tk.X)

        ttk.Label(f, text="Nome:", font=self._base_font).pack(side=tk.LEFT, padx=(0, 4))
        self._name_var = tk.StringVar()
        ttk.Entry(f, textvariable=self._name_var, width=18, font=self._base_font).pack(
            side=tk.LEFT, padx=(0, 8)
        )

        ttk.Label(f, text="Secondi:", font=self._base_font).pack(side=tk.LEFT, padx=(0, 4))
        self._sec_var = tk.StringVar(value="60")
        ttk.Entry(f, textvariable=self._sec_var, width=8, font=self._base_font).pack(
            side=tk.LEFT, padx=(0, 8)
        )

        ttk.Button(f, text="Aggiungi timer", command=self._add_timer).pack(side=tk.LEFT)

    def _build_list_frame(self):
        outer = ttk.Frame(self, padding=(8, 0, 8, 8))
        outer.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(outer, highlightthickness=0)
        scroll = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=self._canvas.yview)
        self._inner = ttk.Frame(self._canvas)
        self._inner.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._win_inner = self._canvas.create_window((0, 0), window=self._inner, anchor=tk.NW)
        self._canvas.configure(yscrollcommand=scroll.set)

        def _sync_canvas_width(event):
            self._canvas.itemconfigure(self._win_inner, width=event.width)

        self._canvas.bind("<Configure>", _sync_canvas_width)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        def _wheel(event):
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self._canvas.bind("<MouseWheel>", _wheel)
        self._inner.bind("<MouseWheel>", _wheel)

    def _add_timer(self):
        name = (self._name_var.get() or "").strip()
        if not name:
            messagebox.showwarning("Nome mancante", "Inserisci un nome per il timer.")
            return
        try:
            sec = float((self._sec_var.get() or "0").replace(",", "."))
        except ValueError:
            messagebox.showerror("Valore non valido", "I secondi devono essere un numero.")
            return
        if sec <= 0:
            messagebox.showwarning("Durata", "La durata deve essere maggiore di zero.")
            return

        row = TimerRow(
            self._inner,
            name,
            sec,
            self._base_font,
            self._bold_font,
            self._mono_font,
            self._drop_timer_row,
        )
        row.pack(fill=tk.X, pady=4)
        self._timers.append(row)
        self._name_var.set("")
        self._canvas.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _drop_timer_row(self, row):
        if row in self._timers:
            self._timers.remove(row)
        row.destroy()
        self._canvas.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _schedule_tick(self):
        for t in self._timers:
            t.tick(UPDATE_INTERVAL_MS / 1000.0)
        self._after_id = self.after(UPDATE_INTERVAL_MS, self._schedule_tick)

    def _on_close(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        self.destroy()


class TimerRow(ttk.Frame):
    def __init__(
        self, parent, name, duration_sec, base_font, bold_font, mono_font, on_remove
    ):
        ttk.Frame.__init__(self, parent)
        self._on_remove = on_remove
        self._name = name
        self._total = float(duration_sec)
        self._remaining = float(duration_sec)
        self._running = False

        self._lbl_name = ttk.Label(self, text=name, font=bold_font, width=20, anchor=tk.W)
        self._lbl_name.pack(side=tk.LEFT, padx=(0, 8))

        self._lbl_time = ttk.Label(
            self, text=_fmt_remaining(self._remaining), font=mono_font, width=14, anchor=tk.E
        )
        self._lbl_time.pack(side=tk.LEFT, padx=(0, 8))

        self._pb = ttk.Progressbar(
            self, length=120, mode="determinate", maximum=100, value=100
        )
        self._pb.pack(side=tk.LEFT, padx=(0, 8), fill=tk.X, expand=True)

        ttk.Button(self, text="Start", width=7, command=self._start).pack(side=tk.LEFT, padx=2)
        ttk.Button(self, text="Pausa", width=7, command=self._pause).pack(side=tk.LEFT, padx=2)
        ttk.Button(self, text="Reset", width=7, command=self._reset).pack(side=tk.LEFT, padx=2)
        ttk.Button(self, text="Rimuovi", width=8, command=self._remove).pack(side=tk.LEFT, padx=2)

        self._update_progress()

    def tick(self, dt):
        if not self._running:
            return
        self._remaining -= dt
        if self._remaining <= 0:
            self._remaining = 0.0
            self._running = False
        self._lbl_time.configure(text=_fmt_remaining(self._remaining))
        self._update_progress()

    def _update_progress(self):
        if self._total <= 0:
            self._pb["value"] = 0
            return
        pct = 100.0 * (self._remaining / self._total)
        self._pb["value"] = max(0.0, min(100.0, pct))

    def _start(self):
        if self._remaining <= 0:
            self._remaining = self._total
        self._running = True
        self._update_progress()

    def _pause(self):
        self._running = not self._running

    def _reset(self):
        self._running = False
        self._remaining = self._total
        self._lbl_time.configure(text=_fmt_remaining(self._remaining))
        self._update_progress()

    def _remove(self):
        self._on_remove(self)


def main():
    app = TimerDashboard()
    app.mainloop()


if __name__ == "__main__":
    main()
