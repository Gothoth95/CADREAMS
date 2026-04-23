# -*- coding: utf-8 -*-
# Name: Timer heal (WPF) + durability min/max live
# Description: Finestra WPF (DispatcherTimer): cooldown pozza come nel tuo esempio + barra/etichetta durability cur/max da tooltip ClassicAssist.
# Author: Local
# Era: Any
#
# ClassicAssist: FindLayer → "found"; Property / PropertyValue su "Durability".
# WaitForProperties solo quando cambia il serial in "found" (non ogni 100 ms).

import clr
import threading

clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")

from System.Windows import Window, Application, Thickness, HorizontalAlignment
from System.Windows.Controls import StackPanel, TextBlock, ProgressBar
from System.Windows.Media import Brushes
from System.Windows.Threading import DispatcherTimer
from System.Threading import Thread, ThreadStart, ApartmentState
from System import TimeSpan

# ---------------------------------------------------------------------------
# Timer pozza (stessa logica del tuo snippet)
# ---------------------------------------------------------------------------
HEAL_TIMER_NAME = "hp_pot"
HEAL_DURATION_MS = 10000.0

# ---------------------------------------------------------------------------
# Durability: primo layer in lista con item + riga Durability leggibile
# ---------------------------------------------------------------------------
DURABILITY_LAYER_ORDER = [
    "TwoHanded",
    "OneHanded",
    "Helm",
    "OuterTorso",
    "Gloves",
    "Arms",
    "Pants",
    "Shoes",
]

# Soglie % (cur/max) per colore barra
DUR_PCT_OK = 40.0
DUR_PCT_WARN = 15.0

# Ogni N tick UI (tick = POLL_MS) aggiorna solo la durability (meno pressione sui tooltip)
DUR_POLL_TICKS = 5

# Riga tooltip tipo «Durability 252 / 255» — sottostringhe per Property (EN/IT)
DURABILITY_PROP_NAMES = ("Durability", "durability", "Durabilità", "durabilità")

POLL_MS = 100


def _durability_cur_max(alias):
    """Ritorna (current, max) o (None, None) se assente / errore."""
    for prop in DURABILITY_PROP_NAMES:
        try:
            if not Property(alias, prop):
                continue
            cur = PropertyValue(alias, prop, 0)
            mx = PropertyValue(alias, prop, 1)
            c = int(cur)
            m = int(mx)
            if m > 0:
                return c, m
        except Exception:
            continue
    return None, None


def _find_durability_target():
    """Trova il primo layer con item; imposta alias ClassicAssist 'found'. Ritorna nome layer o None."""
    for layer in DURABILITY_LAYER_ORDER:
        try:
            if FindLayer(layer, "self"):
                return layer
        except Exception:
            continue
    return None


class CooldownWindow(Window):
    def __init__(self):
        self.Title = "Timer + Durability"
        self.Width = 220
        self.Height = 150
        self.Topmost = True
        self.Background = Brushes.Black
        self.Opacity = 0.88

        self._dur_tick = 0
        self._last_found_serial = -1

        root = StackPanel()
        root.Margin = Thickness(6)

        self.label_heal = TextBlock()
        self.label_heal.Text = "Pozza Heal: PRONTA"
        self.label_heal.Foreground = Brushes.LimeGreen
        self.label_heal.HorizontalAlignment = HorizontalAlignment.Center

        self.pb_heal = ProgressBar()
        self.pb_heal.Minimum = 0
        self.pb_heal.Maximum = 100
        self.pb_heal.Value = 0
        self.pb_heal.Height = 14
        self.pb_heal.Foreground = Brushes.Gold

        self.label_dur = TextBlock()
        self.label_dur.Text = "Dur: —"
        self.label_dur.Foreground = Brushes.Gray
        self.label_dur.Margin = Thickness(0, 8, 0, 0)
        self.label_dur.HorizontalAlignment = HorizontalAlignment.Center

        self.pb_dur = ProgressBar()
        self.pb_dur.Minimum = 0
        self.pb_dur.Maximum = 100
        self.pb_dur.Value = 0
        self.pb_dur.Height = 14
        self.pb_dur.Foreground = Brushes.DodgerBlue

        root.Children.Add(self.label_heal)
        root.Children.Add(self.pb_heal)
        root.Children.Add(self.label_dur)
        root.Children.Add(self.pb_dur)
        self.Content = root

        self.ui_timer = DispatcherTimer()
        self.ui_timer.Interval = TimeSpan.FromMilliseconds(POLL_MS)
        self.ui_timer.Tick += self.update_status
        self.ui_timer.Start()

    def _refresh_durability_ui(self):
        layer = _find_durability_target()
        if layer is None:
            self.label_dur.Text = "Dur: (nessun layer)"
            self.pb_dur.Value = 0
            self.pb_dur.Foreground = Brushes.Gray
            self._last_found_serial = -1
            return

        try:
            serial = GetAlias("found")
        except Exception:
            serial = 0

        if serial != self._last_found_serial:
            self._last_found_serial = serial
            try:
                WaitForProperties("found", 2500)
            except Exception:
                pass

        cur, mx = _durability_cur_max("found")
        try:
            item_name = Name("found")
        except Exception:
            item_name = ""

        if cur is None or mx is None or mx <= 0:
            self.label_dur.Text = (layer + ": " + (item_name or "?") + " | dur n/d").strip()
            self.pb_dur.Value = 0
            self.pb_dur.Foreground = Brushes.Gray
            return

        pct = 100.0 * float(cur) / float(mx)
        self.pb_dur.Value = pct
        self.label_dur.Text = "%s: %d / %d  (%.0f%%)" % (layer, cur, mx, pct)

        if pct <= DUR_PCT_WARN:
            self.pb_dur.Foreground = Brushes.OrangeRed
            self.label_dur.Foreground = Brushes.OrangeRed
        elif pct <= DUR_PCT_OK:
            self.pb_dur.Foreground = Brushes.Gold
            self.label_dur.Foreground = Brushes.Gold
        else:
            self.pb_dur.Foreground = Brushes.LimeGreen
            self.label_dur.Foreground = Brushes.White

    def update_status(self, sender, e):
        # --- Heal timer ---
        if TimerExists(HEAL_TIMER_NAME):
            current_ms = Timer(HEAL_TIMER_NAME)
            if current_ms < HEAL_DURATION_MS:
                remaining = (HEAL_DURATION_MS - current_ms) / 1000.0
                percent = (current_ms / HEAL_DURATION_MS) * 100.0
                self.pb_heal.Value = 100.0 - percent
                self.label_heal.Text = "Pozza Heal: %.1fs" % remaining
                self.label_heal.Foreground = Brushes.White
                self.pb_heal.Foreground = Brushes.Gold
            else:
                self.pb_heal.Value = 0
                self.label_heal.Text = "Pozza Heal: PRONTA"
                self.label_heal.Foreground = Brushes.LimeGreen
        else:
            self.pb_heal.Value = 0
            self.label_heal.Text = "Heal: in attesa timer…"
            self.label_heal.Foreground = Brushes.Gray

        # --- Durability (meno frequente) ---
        self._dur_tick += 1
        if self._dur_tick >= DUR_POLL_TICKS:
            self._dur_tick = 0
            try:
                self._refresh_durability_ui()
            except Exception:
                self.label_dur.Text = "Dur: (errore lettura)"
                self.pb_dur.Foreground = Brushes.Gray


def _start_app():
    app = Application()
    win = CooldownWindow()
    app.Run(win)


try:
    _t = Thread(ThreadStart(_start_app))
    _t.SetApartmentState(ApartmentState.STA)
    _t.IsBackground = True
    _t.Start()
except Exception as _ex:
    try:
        SysMessage("WPF timer+dur: " + str(_ex), 33)
    except Exception:
        pass
