# -*- coding: utf-8 -*-
# Name: Rehue last target (1152)
# Description: Ricolora il Last Target con hue 1152 (solo visivo lato client — Rehue).
# Author: Local
# Era: Any
#
# ClassicAssist: Rehue(serial, hue) non modifica l'hue sul server.

REHUE_HUE = 1152

# True = esegue FindObject solo se il mobile è in schermo entro N tile (consigliato).
# False = prova Rehue sul serial del last anche senza FindObject.
REQUIRE_ON_SCREEN = True
MAX_RANGE_TILES = 18

HUE_ERR = 33


try:
    _last = GetAlias("last")
except Exception:
    _last = 0

if _last == 0:
    HeadMsg("No last target", "self", HUE_ERR)
else:
    SetAlias("tgt", _last)
    if REQUIRE_ON_SCREEN and not FindObject("tgt", MAX_RANGE_TILES):
        HeadMsg("Last target fuori range / assente", "self", HUE_ERR)
    else:
        Rehue("tgt", REHUE_HUE)
