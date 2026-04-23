# -*- coding: utf-8 -*-
# Name: Stato timer (live)
# Description: Timer configurati: snapshot una tantum oppure loop che avvisa sotto soglia (es. ultimi 2s).
# Author: Local
# Era: Any
#
# Nota: Razor/UOStealth non espongono di solito "lista di tutti i timer". Qui controlli solo i NOMI che aggiungi sotto.
# Per "quanto manca" serve la durata del cooldown (ms) uguale a quella usata nel macro che fa SetTimer.

# ---------------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------------
# Lista: (nome_timer, durata_ms, etichetta_opzionale)
# - durata_ms > 0  -> restante = durata - Timer(nome)
# - durata_ms None -> in modalità loop non può calcolare "manca" (saltato per avvisi)
TIMERS = [
    ("hp_pot", 10000, "Heal giallo"),
    # ("bandage", 5000, "Bende"),
]

MSG_HUE = 1153

# Modalità: "once" = un solo riepilogo come prima | "loop" = ciclo continuo
MODE = "loop"

# --- Solo MODE == "loop" ---
POLL_MS = 300
# Pausa tra un giro e l’altro (ms). Più basso = aggiornamenti più frequenti (più messaggi in chat).

ALERT_BELOW_MS = 2000
# Se il tempo rimanente è > 0 e <= questo valore, manda SysMessage con quanto manca (es. ultimi 2 secondi).

MIN_ALERT_GAP_MS = 400
# Evita spam: non ripetere lo stesso timer prima di N ms dall’ultimo messaggio (0 = messaggio a ogni giro).

# --- Solo MODE == "once" ---
ONE_LINE = False
SHOW_INACTIVE = True


def _parse_entry(entry):
    if len(entry) >= 3:
        return entry[0], entry[1], entry[2]
    return entry[0], entry[1], entry[0]


def _fmt_ms(ms):
    if ms < 0:
        ms = 0
    s = ms / 1000.0
    if s >= 120:
        m = int(s // 60)
        sec = s - 60 * m
        return "%dm %.1fs" % (m, sec)
    if s >= 60:
        return "%.1f s" % s
    return "%.1f s" % s


def _remaining_ms(name, durata_ms):
    if durata_ms is None or not TimerExists(name):
        return None
    tr = Timer(name)
    return durata_ms - tr


def run_once():
    if not TIMERS:
        SysMessage("[Timer] Lista TIMERS vuota: aggiungi tuple (nome, ms, etichetta).", MSG_HUE)
        return

    lines = []
    active = 0

    for entry in TIMERS:
        name, durata_ms, label = _parse_entry(entry)

        if not TimerExists(name):
            if SHOW_INACTIVE:
                lines.append("%s: non attivo" % label)
            continue

        active += 1
        tr = Timer(name)

        if durata_ms is None:
            lines.append("%s: trascorso %s" % (label, _fmt_ms(tr)))
            continue

        if tr >= durata_ms:
            lines.append("%s: pronto (timer ancora presente, trascorso %s)" % (label, _fmt_ms(tr)))
        else:
            rest = durata_ms - tr
            lines.append("%s: mancano ~%s (su %s)" % (label, _fmt_ms(rest), _fmt_ms(durata_ms)))

    if active == 0 and not SHOW_INACTIVE:
        SysMessage(
            "[Timer] Nessuno dei timer configurati risulta attivo.",
            MSG_HUE,
        )
        return

    if not lines:
        SysMessage("[Timer] Nessuna riga da mostrare.", MSG_HUE)
        return

    if ONE_LINE:
        SysMessage("[Timer] " + " | ".join(lines), MSG_HUE)
    else:
        SysMessage("[Timer] Riepilogo (attivi: %d)" % active, MSG_HUE)
        for ln in lines:
            SysMessage("  " + ln, MSG_HUE)


# Valore Timer("__timer_status") all’ultimo avviso per nome (anti-spam)
_last_alert_at = {}


def _ensure_master_tick():
    try:
        if not TimerExists("__timer_status"):
            CreateTimer("__timer_status")
            SetTimer("__timer_status", 0)
    except Exception:
        pass


def _now_ms():
    try:
        if TimerExists("__timer_status"):
            return Timer("__timer_status")
    except Exception:
        pass
    return 0


def run_loop():
    """Ciclo continuo: avvisa quando rest <= ALERT_BELOW_MS (e > 0)."""
    if not TIMERS:
        SysMessage("[Timer] Lista TIMERS vuota.", MSG_HUE)
        return

    _ensure_master_tick()
    SysMessage(
        "[Timer] Monitor avviato (avvisi sotto %s). Stop = ferma macro."
        % _fmt_ms(ALERT_BELOW_MS),
        MSG_HUE,
    )

    while True:
        now = _now_ms()

        for entry in TIMERS:
            name, durata_ms, label = _parse_entry(entry)
            if durata_ms is None:
                continue

            rest = _remaining_ms(name, durata_ms)
            if rest is None:
                continue
            if rest <= 0:
                continue
            if rest > ALERT_BELOW_MS:
                continue

            last_at = _last_alert_at.get(name)
            if (
                MIN_ALERT_GAP_MS > 0
                and last_at is not None
                and (now - last_at) < MIN_ALERT_GAP_MS
            ):
                continue

            SysMessage(
                "[Timer] %s: mancano ~%s" % (label, _fmt_ms(rest)),
                MSG_HUE,
            )
            _last_alert_at[name] = now

        Pause(POLL_MS)


def main():
    if MODE == "loop":
        run_loop()
    else:
        run_once()


main()
