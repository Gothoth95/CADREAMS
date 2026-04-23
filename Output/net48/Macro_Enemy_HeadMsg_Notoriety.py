# -*- coding: utf-8 -*-
# Name: Enemy scan — HeadMsg hue da notorietà
# Description: HeadMsg hue da notorietà; bersaglio via ACQUIRE_MODE (getenemy / last / prompt).
# Author: Local
# Era: Any
#
# ClassicAssist Entity: Innocent → messaggi blu sopra nemico + PG; non innocent → nessun HeadMsg.
#
# La riga «Target: Nome» ROSSA che vedi spesso NON viene da questo script: è quasi sempre
# l’overlay del client (ClassicUO / TazUO: nome sopra il last target / salute) oppure
# un’opzione di visualizzazione in ClassicAssist. L’hue dei HeadMsg qui non la modifica.
# Soluzione: disattiva quell’overlay nelle opzioni del client / assistant (cerca «target»,
# «overhead», «name», «health») oppure convivi con due righe finché resta attivo.
#
# SHOW_TARGET_PREFIX: aggiunge una riga «Target: …» via HeadMsg con hue da notorietà
# (così hai almeno una «Target:» colorata correttamente). Se disattivi l’overlay rosso,
# resta solo questa.

SHOW_TARGET_PREFIX = True

# ---------------------------------------------------------------------------
# Come ottenere il «nemico» (alias "enemy")
# ---------------------------------------------------------------------------
# "getenemy" — scansione automatica ClassicAssist (come prima).
# "last"     — usa solo il Last Target del client (nessun GetEnemy).
# "prompt"   — cursore in gioco: scegli tu il mobile (PromptMacroAlias).
#
ACQUIRE_MODE = "getenemy"
MAX_RANGE_FIND = 18  # solo per "last": FindObject("enemy", range)

# Hue messaggi (solo per Innocent)
HUE_INNOCENT = 88   # blu
HUE_NO_ENEMY = 33   # feedback errori su "self" (nessun nemico / prompt ecc.)


def _head_both(text, hue):
    """Stesso messaggio sopra il nemico e sopra il PG, stesso colore (notorietà nemico)."""
    HeadMsg(text, "enemy", hue)
    HeadMsg(text, "self", hue)


def _acquire_enemy():
    """
    Imposta l'alias "enemy" e verifica che il mobile sia valido in schermo.
    Ritorna True se ok, False altrimenti.
    """
    m = (ACQUIRE_MODE or "getenemy").strip().lower()

    if m == "getenemy":
        if not GetEnemy(["Any"], "Both", "Next", "Any"):
            return False
        return bool(FindObject("enemy"))

    if m == "last":
        try:
            last_serial = GetAlias("last")
        except Exception:
            last_serial = 0
        if last_serial == 0:
            HeadMsg("No last target", "self", HUE_NO_ENEMY)
            return False
        SetAlias("enemy", last_serial)
        if not FindObject("enemy", MAX_RANGE_FIND):
            HeadMsg("Last target fuori range / assente", "self", HUE_NO_ENEMY)
            return False
        return True

    if m == "prompt":
        try:
            ret = PromptMacroAlias("enemy")
        except Exception:
            ret = 0
        if ret == 0:
            HeadMsg("Target annullato", "self", HUE_NO_ENEMY)
            return False
        if not FindAlias("enemy"):
            HeadMsg("Bersaglio non valido", "self", HUE_NO_ENEMY)
            return False
        return True

    HeadMsg("ACQUIRE_MODE sconosciuto", "self", HUE_NO_ENEMY)
    return False


if _acquire_enemy():
    try:
        _is_innocent = Innocent("enemy")
    except Exception:
        _is_innocent = False

    # Non innocent (rossi / grigi / criminal / murderer): nessun messaggio sopra la testa
    if not _is_innocent:
        pass
    else:
        hue = HUE_INNOCENT

        if SHOW_TARGET_PREFIX:
            try:
                _tn = Name("enemy")
            except Exception:
                _tn = "?"
            _head_both("Target: " + _tn, hue)

        if InRegion("Guarded", "self") and Innocent("enemy"):
            _head_both("[Blue in Guards]", hue)
            UnsetAlias("enemy")
        elif InRegion("Guarded", "enemy") and Innocent("enemy"):
            _head_both("[Blue in Guards]", hue)
            UnsetAlias("enemy")
        elif Property("enemy", "wandering healer") or Property("enemy", "priest of"):
            _head_both("[Healer Cunt]", hue)
            IgnoreObject("enemy")
            UnsetAlias("enemy")
        elif Property("enemy", ".dps") or Property("enemy", "Hz"):
            _head_both("[Ally - Peru Pequenho]", hue)
            UnsetAlias("enemy")
        elif Property("enemy", "the piper"):
            _head_both("[Coon Gay]", hue)
            UnsetAlias("enemy")
        elif InRange("enemy", 16):
            _head_both("▼ Under Attack ▼", hue)
            # Attack('enemy')
else:
    if (ACQUIRE_MODE or "").strip().lower() == "getenemy":
        HeadMsg("No Enemy found", "self", HUE_NO_ENEMY)
