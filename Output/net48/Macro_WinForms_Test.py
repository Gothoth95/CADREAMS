# -*- coding: utf-8 -*-
# Name: Stato timer (live) — finestra WinForms + ClassicAssist
# Description: Monitora i timer in una finestra sempre in primo piano; opzionale HeadMsg/ SysMessage sotto soglia.
# Author: Local
# Era: Any
#
# La finestra gira su thread STA (.NET). Timer di gioco letti con Timer() / TimerExists() di ClassicAssist.

import clr

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReference("System")

import System.Threading
from System import Environment
from System.Threading import Thread, ThreadStart, ApartmentState
from System.Windows.Forms import Application, Form, Button, Label, FormStartPosition
from System.Windows.Forms import Timer as WinFormsTimer
from System.Drawing import Size, Point, Color, Font, FontStyle

# ---------------------------------------------------------------------------
# TABELLA COLORI (HUE) — messaggi UO
# ---------------------------------------------------------------------------
BIANCO = 1153
ROSSO = 38
VERDE = 68
GIALLO = 53
BLU = 88
VIOLA = 1359
ARANCIO = 43
GRIGIO = 912

# ---------------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------------
# Formato: (nome_timer, durata_ms, etichetta, colore_hue_UO)
TIMERS = [
    ("hp_pot", 10000, "Pozza Heal", GIALLO),
]

USE_OVERHEAD = True
MODE = "loop"
POLL_MS = 300
ALERT_BELOW_MS = 2000
MIN_ALERT_GAP_MS = 1000

# ---------------------------------------------------------------------------
# Logica timer (ClassicAssist)
# ---------------------------------------------------------------------------

_last_alert_at = {}


def _parse_entry(entry):
    name = entry[0]
    durata = entry[1]
    label = entry[2] if len(entry) >= 3 else name
    hue = entry[3] if len(entry) >= 4 else BIANCO
    return name, durata, label, hue


def _fmt_ms(ms):
    if ms < 0:
        ms = 0
    return "%.1fs" % (ms / 1000.0)


def _remaining_ms(name, durata_ms):
    if durata_ms is None or not TimerExists(name):
        return None
    return durata_ms - Timer(name)


def _notify_uo(msg, hue):
    try:
        SysMessage(msg, hue)
    except Exception:
        pass


def _head_if_enabled(msg, hue):
    if not USE_OVERHEAD:
        return
    try:
        HeadMsg(msg, GetAlias("self"), hue)
    except Exception:
        try:
            HeadMsg(msg, "self", hue)
        except Exception:
            _notify_uo(msg, hue)


def _run_form():
    Application.EnableVisualStyles()
    Application.SetCompatibleTextRenderingDefault(False)

    f = Form()
    f.Text = "Timer — ClassicAssist"
    f.StartPosition = FormStartPosition.CenterScreen
    f.TopMost = True

    n = len(TIMERS) if TIMERS else 1
    f.Height = 110 + max(1, n) * 28
    f.Width = 420

    title = Label()
    title.Text = "Stato timer (live)"
    title.Location = Point(12, 10)
    title.Size = Size(390, 22)
    title.Font = Font("Segoe UI", 10, FontStyle.Bold)
    f.Controls.Add(title)

    row_labels = []
    y0 = 38
    for i, entry in enumerate(TIMERS):
        name, durata_ms, label, _hue = _parse_entry(entry)
        lab = Label()
        lab.Name = "row_" + name
        lab.Location = Point(12, y0 + i * 26)
        lab.Size = Size(390, 22)
        lab.Text = "%s: —" % label
        lab.Font = Font("Consolas", 9)
        f.Controls.Add(lab)
        row_labels.append((lab, entry))

    btn = Button()
    btn.Text = "Chiudi"
    btn.Location = Point(160, f.Height - 70)
    btn.Size = Size(100, 30)

    win_timer = WinFormsTimer()
    win_timer.Interval = POLL_MS

    def refresh_all():
        now_ms = Environment.TickCount
        for lab, entry in row_labels:
            name, durata_ms, label, hue_uo = _parse_entry(entry)
            rest = _remaining_ms(name, durata_ms)

            if rest is None:
                lab.Text = "%s: (timer assente)" % label
                lab.ForeColor = Color.Gray
                continue

            if rest <= 0:
                lab.Text = "%s: pronto / scaduto" % label
                lab.ForeColor = Color.DarkGreen
                continue

            lab.Text = "%s: %s rimanenti" % (label, _fmt_ms(rest))
            if rest <= ALERT_BELOW_MS:
                lab.ForeColor = Color.DarkOrange
            else:
                lab.ForeColor = Color.Black

            if 0 < rest <= ALERT_BELOW_MS:
                last_at = _last_alert_at.get(name)
                if last_at is None or (now_ms - last_at) >= MIN_ALERT_GAP_MS:
                    msg = "%s: %s" % (label, _fmt_ms(rest))
                    if USE_OVERHEAD:
                        _head_if_enabled(msg, hue_uo)
                    else:
                        _notify_uo("[Timer] " + msg, hue_uo)
                    _last_alert_at[name] = now_ms

    def on_tick(sender, event):
        refresh_all()

    def on_shown(sender, event):
        refresh_all()
        if MODE != "loop":
            win_timer.Stop()

    def on_close(sender, event):
        try:
            win_timer.Stop()
        except Exception:
            pass

    win_timer.Tick += on_tick
    f.Shown += on_shown
    f.FormClosing += on_close

    def on_click(sender, event):
        f.Close()

    btn.Click += on_click
    f.Controls.Add(btn)

    if MODE == "loop":
        win_timer.Start()

    Application.Run(f)


def main():
    try:
        SysMessage("[Timer] Apertura finestra stato timer…", BIANCO)
    except Exception:
        pass

    t = Thread(ThreadStart(_run_form))
    t.SetApartmentState(ApartmentState.STA)
    t.IsBackground = True
    t.Start()


main()
