# -*- coding: utf-8 -*-
"""
Dashboard timer — WinForms + IronPython 2.x (ClassicAssist).

UI compatta: nome | CD (es. 10s) | residuo | barra. Senza colonna chiave script.

Tema scuro, testo opaco. Bordo trasparente opzionale (TRANSPARENT_MARGIN).
"""

from __future__ import division
from __future__ import print_function

import sys
import clr

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Windows.Forms import (
    Application,
    Form,
    Label,
    Panel,
    FlowLayoutPanel,
    FlowDirection,
    DockStyle,
    Timer as WinTimer,
    ProgressBar,
    ProgressBarStyle,
    Padding,
    FormBorderStyle,
    AnchorStyles,
    MessageBox,
    MessageBoxButtons,
    MessageBoxIcon,
    FormStartPosition,
)
from System.Drawing import Size, Point, Font, FontStyle, ContentAlignment, Color

clr.AddReference("System.Threading")
from System.Threading import Thread, ThreadStart, ApartmentState

# ---------------------------------------------------------------------------
# --- Impostazioni utente ---
# ---------------------------------------------------------------------------
FONT_SIZE = 8
TIMER_ROW_FONT_BOOST = 2
FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"
WINDOW_ALWAYS_ON_TOP = True
UPDATE_INTERVAL_MS = 100

COLOR_BG = Color.Black
COLOR_TEXT = Color.White
COLOR_TEXT_MUTED = Color.FromArgb(190, 190, 190)
COLOR_PROGRESS_TRACK = Color.FromArgb(45, 45, 45)

# Margine trasparente intorno al pannello (chroma). Più piccolo = più compatto.
TRANSPARENT_MARGIN = 4
# Colore che non deve comparire nei controlli (né nelle icone della barra).
CHROMA_KEY = Color.FromArgb(255, 255, 0, 255)

# Una riga per elemento — allinea a pvp_auto_potions.py (T_HEAL_CD, *_COOLDOWN_MS).
PRESET_AUTO_POT = [
    ("Heal", "pvp_auto_pots_heal_cd", 10000),
    ("Str", "pvp_auto_pots_str_cd", 30000),
    ("Agi", "pvp_auto_pots_agi_cd", 30000),
]

# ---------------------------------------------------------------------------


def _fmt_cd_config(ms):
    """Cooldown impostato, compatto (es. 10s, 5m, 1m30s)."""
    ms = int(ms)
    if ms <= 0:
        return "—"
    if ms < 60000:
        if ms % 1000 == 0:
            return "{0}s".format(ms // 1000)
        return "{0:.1f}s".format(ms / 1000.0)
    minutes = ms // 60000
    sec = (ms % 60000) // 1000
    if sec == 0:
        return "{0}m".format(minutes)
    return "{0}m{1}s".format(minutes, sec)


def _fmt_remaining(seconds):
    seconds = max(0.0, float(seconds))
    total = int(seconds)
    frac = seconds - total
    centis = int(frac * 100)
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    if h:
        return "{0:d}:{1:02d}:{2:02d}.{3:d}".format(h, m, s, centis // 10)
    return "{0:d}:{1:02d}.{2:d}".format(m, s, centis // 10)


def _get_classicassist_timer_api():
    g = globals()
    t = g.get("Timer")
    e = g.get("TimerExists")
    if t is None or e is None:
        main = sys.modules.get("__main__", None)
        if main is not None:
            if t is None:
                t = getattr(main, "Timer", None)
            if e is None:
                e = getattr(main, "TimerExists", None)
    if t is None or e is None:
        try:
            import __builtin__ as bi

            if t is None:
                t = getattr(bi, "Timer", None)
            if e is None:
                e = getattr(bi, "TimerExists", None)
        except Exception:
            pass
    return t, e


def _classicassist_remaining_ms(ca_timer_name, cooldown_ms):
    fn_t, fn_e = _get_classicassist_timer_api()
    if fn_t is None or fn_e is None:
        return "n/a", 0.0
    try:
        if int(cooldown_ms) <= 0:
            if not fn_e(ca_timer_name):
                return "ready", 0.0
            elapsed = float(fn_t(ca_timer_name))
            return "track", elapsed

        if not fn_e(ca_timer_name):
            return "ready", 0.0
        elapsed = float(fn_t(ca_timer_name))
        cd = float(cooldown_ms)
        if elapsed >= cd:
            return "ready", 0.0
        return "cooldown", max(0.0, cd - elapsed)
    except Exception:
        return "n/a", 0.0


class ClassicAssistTimerRow(Panel):
    """Riga compatta: nome | CD | residuo | barra (niente chiave script)."""

    def __init__(self, display_name, ca_timer_name, cooldown_ms):
        Panel.__init__(self)
        row_fs = float(FONT_SIZE + TIMER_ROW_FONT_BOOST)
        lh = max(16, int(14 + row_fs))
        self.Height = lh + 4
        self.Width = 300
        self._ca_name = str(ca_timer_name)
        self._cd_ms = int(cooldown_ms)

        self.BackColor = COLOR_BG

        self._font_name = Font(FONT_FAMILY, row_fs, FontStyle.Bold)
        self._font_time = Font(FONT_FAMILY_MONO, row_fs + 0.5, FontStyle.Bold)
        self._font_cfg = Font(FONT_FAMILY, max(row_fs - 1.0, 7.0), FontStyle.Italic)

        fl = FlowLayoutPanel()
        fl.FlowDirection = FlowDirection.LeftToRight
        fl.WrapContents = False
        fl.Dock = DockStyle.Fill
        fl.AutoSize = True
        fl.Padding = Padding(0, 1, 0, 1)
        fl.BackColor = COLOR_BG

        self._lbl_name = Label()
        self._lbl_name.Text = display_name
        self._lbl_name.Font = self._font_name
        self._lbl_name.ForeColor = COLOR_TEXT
        self._lbl_name.BackColor = COLOR_BG
        self._lbl_name.AutoSize = False
        self._lbl_name.TextAlign = ContentAlignment.MiddleLeft
        self._lbl_name.Size = Size(58, lh)

        self._lbl_cfg = Label()
        self._lbl_cfg.Text = _fmt_cd_config(self._cd_ms)
        self._lbl_cfg.Font = self._font_cfg
        self._lbl_cfg.ForeColor = COLOR_TEXT_MUTED
        self._lbl_cfg.BackColor = COLOR_BG
        self._lbl_cfg.AutoSize = False
        self._lbl_cfg.TextAlign = ContentAlignment.MiddleLeft
        self._lbl_cfg.Size = Size(52, lh)

        self._lbl_remain = Label()
        self._lbl_remain.Text = "…"
        self._lbl_remain.Font = self._font_time
        self._lbl_remain.ForeColor = COLOR_TEXT
        self._lbl_remain.BackColor = COLOR_BG
        self._lbl_remain.AutoSize = False
        self._lbl_remain.TextAlign = ContentAlignment.MiddleRight
        self._lbl_remain.Size = Size(72, lh)

        self._pb = ProgressBar()
        self._pb.Minimum = 0
        self._pb.Maximum = 1000
        self._pb.Value = 1000
        self._pb.Size = Size(118, max(12, lh - 2))
        self._pb.Style = ProgressBarStyle.Continuous
        try:
            self._pb.BackColor = COLOR_PROGRESS_TRACK
            self._pb.ForeColor = Color.FromArgb(80, 220, 100)
        except Exception:
            pass

        fl.Controls.Add(self._lbl_name)
        fl.Controls.Add(self._lbl_cfg)
        fl.Controls.Add(self._lbl_remain)
        fl.Controls.Add(self._pb)

        self.Controls.Add(fl)
        self.PollClassicAssist()

    def PollClassicAssist(self):
        state, val = _classicassist_remaining_ms(self._ca_name, self._cd_ms)
        if state == "n/a":
            self._lbl_remain.Text = "no API"
            self._pb.Value = 0
            return
        if state == "ready":
            self._lbl_remain.Text = "Pronto"
            self._pb.Value = 1000
            return
        if state == "track":
            self._lbl_remain.Text = "{0:.1f}s".format(val / 1000.0)
            self._pb.Value = 500
            return
        rem_ms = val
        self._lbl_remain.Text = _fmt_remaining(rem_ms / 1000.0)
        cd = float(self._cd_ms)
        if cd > 0:
            v = int(round(1000.0 * rem_ms / cd))
            self._pb.Value = max(0, min(1000, v))

    def Tick(self, dt):
        self.PollClassicAssist()


class MainForm(Form):
    def __init__(self):
        Form.__init__(self)
        self.Text = ""
        n = len(PRESET_AUTO_POT)
        row_fs = float(FONT_SIZE + TIMER_ROW_FONT_BOOST)
        row_h = max(16, int(14 + row_fs)) + 4
        win_w = 300
        self.ClientSize = Size(win_w, max(48, 4 + n * row_h + 8))
        self.MinimumSize = Size(260, max(48, 4 + n * row_h + 8))
        self.FormBorderStyle = FormBorderStyle.SizableToolWindow
        self.StartPosition = FormStartPosition.CenterScreen
        self.TopMost = WINDOW_ALWAYS_ON_TOP
        self.ShowInTaskbar = False
        self.Visible = True
        self.ForeColor = COLOR_TEXT
        # Testo/timer sempre nitidi: niente Opacity < 1 su tutta la Form.
        self.Opacity = 1.0

        m = int(TRANSPARENT_MARGIN)
        if m < 0:
            m = 0
        self._chrome_margin = m

        if m > 0:
            try:
                self.AllowTransparency = True
                self.BackColor = CHROMA_KEY
                self.TransparencyKey = CHROMA_KEY
            except Exception:
                self._chrome_margin = 0
                m = 0
                self.AllowTransparency = False
                self.BackColor = COLOR_BG
        else:
            self.AllowTransparency = False
            self.BackColor = COLOR_BG

        self._rows = []

        self._inner = Panel()
        self._inner.BackColor = COLOR_BG
        self._inner.Location = Point(m, m)
        self._inner.Anchor = (
            AnchorStyles.Top
            | AnchorStyles.Left
            | AnchorStyles.Right
            | AnchorStyles.Bottom
        )

        self._scroll = Panel()
        self._scroll.Dock = DockStyle.Fill
        self._scroll.AutoScroll = True
        self._scroll.Padding = Padding(3, 3, 3, 3)
        self._scroll.BackColor = COLOR_BG

        self._flow = FlowLayoutPanel()
        self._flow.FlowDirection = FlowDirection.TopDown
        self._flow.WrapContents = False
        self._flow.AutoSize = True
        self._flow.Location = Point(2, 2)
        self._flow.Anchor = AnchorStyles.Left | AnchorStyles.Top | AnchorStyles.Right
        self._flow.Width = max(200, self._scroll.ClientSize.Width - 8)
        self._flow.BackColor = COLOR_BG

        self._scroll.Controls.Add(self._flow)
        self._scroll.Resize += self._on_scroll_resize

        self._inner.Controls.Add(self._scroll)
        self.Controls.Add(self._inner)

        self.Resize += self._on_form_resize
        self._sync_inner_bounds()

        self._populate_preset_rows()

        self._tick = WinTimer()
        self._tick.Interval = UPDATE_INTERVAL_MS
        self._tick.Tick += self._on_tick
        self._tick.Enabled = True
        self.FormClosed += self._on_form_closed

    def _populate_preset_rows(self):
        for display, ca_name, ms in PRESET_AUTO_POT:
            row = ClassicAssistTimerRow(display, ca_name, int(ms))
            row.Width = self._flow.Width
            self._flow.Controls.Add(row)
            self._rows.append(row)

    def _on_form_closed(self, sender, args):
        if self._tick is not None:
            self._tick.Enabled = False
            self._tick.Dispose()
            self._tick = None

    def _on_form_resize(self, sender, args):
        self._sync_inner_bounds()

    def _sync_inner_bounds(self):
        m = self._chrome_margin
        cw = self.ClientSize.Width
        ch = self.ClientSize.Height
        iw = max(80, cw - 2 * m)
        ih = max(60, ch - 2 * m)
        self._inner.Location = Point(m, m)
        self._inner.Size = Size(iw, ih)

    def _on_scroll_resize(self, sender, args):
        w = max(200, self._scroll.ClientSize.Width - 8)
        self._flow.Width = w
        for row in self._rows:
            row.Width = w

    def _on_tick(self, sender, args):
        dt = self._tick.Interval / 1000.0
        for row in self._rows:
            row.Tick(dt)


def _run_message_loop():
    Application.EnableVisualStyles()
    Application.SetCompatibleTextRenderingDefault(False)
    form = MainForm()
    Application.Run(form)


def main():
    errors = []

    def runner():
        try:
            _run_message_loop()
        except Exception as ex:
            errors.append(ex)

    t = Thread(ThreadStart(runner))
    t.SetApartmentState(ApartmentState.STA)
    t.IsBackground = False
    t.Start()
    t.Join()

    if errors:
        raise errors[0]


def _report_fatal(ex):
    msg = str(ex)
    try:
        MessageBox.Show(
            msg,
            "Timer dashboard - errore",
            MessageBoxButtons.OK,
            MessageBoxIcon.Error,
        )
    except Exception:
        pass
    try:
        import os

        log = os.path.join(
            os.environ.get("USERPROFILE", "."),
            "Desktop",
            "timer_dashboard_ironpython_error.txt",
        )
        f = open(log, "w")
        try:
            f.write(msg)
        finally:
            f.close()
    except Exception:
        pass


try:
    main()
except Exception as _fatal:
    _report_fatal(_fatal)