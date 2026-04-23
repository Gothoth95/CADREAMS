# -*- coding: utf-8 -*-
# Name: Magery — Harm (vicino) / Magic Arrow + Fireball (lontano)
# Description: Se last target è a ≤ N tile: Harm. Altrimenti Magic Arrow → Fireball. Target automatico su "last".
# Author: Local
# Era: Any
#
# Una esecuzione per attivazione (nessun loop). ClassicAssist: Distance, Cast, WaitForTarget, Target("last").
#
# Cast «in corso»: ClassicAssist non espone IsCasting nel wiki; vedi WaitingForTarget() (solo fase target).
# Blocco input: Hotkeys("off") disattiva le hotkey dell'assistant (non è un freeze PG garantito).

# ---------------------------------------------------------------------------
# True = durante tutta la sequenza spell: Hotkeys("off"), poi ripristino in finally
LOCK_ASSISTANT_HOTKEYS_DURING_SEQUENCE = False

# True = se WaitingForTarget() è già True all'avvio, non lanciare (evita sovrapposizione)
ABORT_IF_ALREADY_WAITING_FOR_TARGET = False
# ---------------------------------------------------------------------------

# Se distanza dal last target ≤ questa (tile), usa solo Harm
CLOSE_RANGE_TILES = 2

# Pausa tra un cast e l’altro (ms) — richiesto 1 ms
PAUSE_BETWEEN_CASTS_MS = 1

WAIT_FOR_TARGET_MS = 5000
# ---------------------------------------------------------------------------

SPELL_CLOSE = "Harm"
SPELL_FAR_1 = "Magic Arrow"
SPELL_FAR_2 = "Fireball"


def _assistant_hotkeys(enable):
    """enable True = Hotkeys on, False = off (Main#Hotkeys)."""
    if enable:
        Hotkeys("on")
    else:
        Hotkeys("off")


def cast_on_last_target(spell_name):
    Cast(spell_name)
    WaitForTarget(WAIT_FOR_TARGET_MS)
    Target("last")


def distance_to_last():
    """Distanza in tile dal player al last target; se non valido, valore alto."""
    try:
        return int(Distance("last"))
    except Exception:
        return 999


def main():
    if ABORT_IF_ALREADY_WAITING_FOR_TARGET and WaitingForTarget():
        return

    if LOCK_ASSISTANT_HOTKEYS_DURING_SEQUENCE:
        _assistant_hotkeys(False)

    try:
        d = distance_to_last()
        if d <= CLOSE_RANGE_TILES:
            cast_on_last_target(SPELL_CLOSE)
            Pause(PAUSE_BETWEEN_CASTS_MS)
            return

        cast_on_last_target(SPELL_FAR_1)
        Pause(PAUSE_BETWEEN_CASTS_MS)
        cast_on_last_target(SPELL_FAR_2)
        Pause(PAUSE_BETWEEN_CASTS_MS)
    finally:
        if LOCK_ASSISTANT_HOTKEYS_DURING_SEQUENCE:
            _assistant_hotkeys(True)


main()
