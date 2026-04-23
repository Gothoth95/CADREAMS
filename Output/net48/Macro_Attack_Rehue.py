# -*- coding: utf-8 -*-
# Name: Attack + Rehue (hue 1152)
# Description: Attacca il bersaglio e lo colora con hue 1152 (Rehue = solo visivo lato client).
# Author: Local
# Era: Any
#
# ClassicAssist: Rehue(serial, hue) non cambia l'hue reale sul server; è un filtro sul client
# (come «tinta» sul modello) per riconoscere il target a colpo d'occhio.

# ---------------------------------------------------------------------------
# "last"  — usa il Last Target del client (deve esserci un bersaglio valido).
# "prompt" — cursore: scegli il mobile da attaccare e colorare.
# ---------------------------------------------------------------------------
TARGET_MODE = "last"

REHUE_HUE = 1152
MAX_RANGE_TILES = 18

HUE_ERR = 33


def _resolve_target():
    """Imposta l'alias 'tgt' e ritorna True se il mobile è in schermo/range."""
    m = (TARGET_MODE or "last").strip().lower()

    if m == "last":
        try:
            last_serial = GetAlias("last")
        except Exception:
            last_serial = 0
        if last_serial == 0:
            HeadMsg("No last target", "self", HUE_ERR)
            return False
        SetAlias("tgt", last_serial)
        if not FindObject("tgt", MAX_RANGE_TILES):
            HeadMsg("Last target fuori range / assente", "self", HUE_ERR)
            return False
        return True

    if m == "prompt":
        try:
            ret = PromptMacroAlias("tgt")
        except Exception:
            ret = 0
        if ret == 0:
            HeadMsg("Target annullato", "self", HUE_ERR)
            return False
        if not FindAlias("tgt"):
            HeadMsg("Bersaglio non valido", "self", HUE_ERR)
            return False
        return True

    HeadMsg("TARGET_MODE sconosciuto (last / prompt)", "self", HUE_ERR)
    return False


if _resolve_target():
    Rehue("tgt", REHUE_HUE)
    Attack("tgt")
