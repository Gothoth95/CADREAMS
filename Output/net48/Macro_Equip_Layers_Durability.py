# -*- coding: utf-8 -*-
# Name: Equip — layer + durability (journal)
# Description: Elenca i layer indossati dal PG e, per ogni pezzo, prova a leggere la Durability dai tooltip (SysMessage).
# Author: Local
# Era: Any
#
# ClassicAssist: FindLayer(layer, "self") → alias "found" con l'item nel layer.
# Property / PropertyValue leggono le righe proprietà (tooltip). Serve che i tooltip siano già noti al client:
# al primo giro WaitForProperties può essere lento.
#
# In gioco la riga è tipicamente una sola, es. «Durability 252 / 255» (attuale / massimo).
# ClassicAssist espone i due numeri con PropertyValue(..., "Durability", 0) e (..., 1).
#
# Se i numeri non escono: (1) le proprietà non sono ancora caricate — vedi WaitForProperties sotto;
# (2) la lingua del tooltip — adatta DURABILITY_LABELS;
# (3) molti oggetti (es. alcune canne da pesca) non hanno proprio la riga «Durability» nel tooltip: in quel caso «-» è corretto.
#
# WaitForProperties in ClassicAssist invia la query al server e ritorna True/False: se False, conviene ripetere.

PRINT_EMPTY_LAYERS = False

# Sottostringhe per trovare la riga tooltip (prima = quella del tuo client EN «Durability …»)
DURABILITY_LABELS = ("Durability", "durability", "Durabilità", "durabilità")

# Richiesta proprietà (BatchQueryProperties): più tentativi se il server risponde tardi
WAIT_PROPERTIES_MS = 5000
WAIT_PROPERTIES_TRIES = 3
PAUSE_BETWEEN_TRIES_MS = 250

# True = una SysMessage extra se c'è «Weight» ma non «Durability» (capisci se le OPL sono caricate)
DEBUG_NO_DURABILITY = False

# Layer da controllare (enum ClassicAssist / UO — vedi wiki Actions → Layer)
LAYERS = [
    "OneHanded",
    "TwoHanded",
    "Shoes",
    "Pants",
    "Shirt",
    "Helm",
    "Gloves",
    "Ring",
    "Talisman",
    "Neck",
    "Hair",
    "Waist",
    "InnerTorso",
    "Bracelet",
    "FacialHair",
    "MiddleTorso",
    "Earrings",
    "Arms",
    "Cloak",
    "Backpack",
    "OuterTorso",
    "OuterLegs",
    "InnerLegs",
    "Mount",
    "Bank",
]


def _wait_properties(alias):
    """Chiede le OPL al server fino a WAIT_PROPERTIES_TRIES; ignora eccezioni."""
    for _t in range(WAIT_PROPERTIES_TRIES):
        try:
            if WaitForProperties(alias, WAIT_PROPERTIES_MS):
                return True
        except Exception:
            pass
        Pause(PAUSE_BETWEEN_TRIES_MS)
    return False


def _durability_display(alias):
    """Ritorna «attuale / massimo» come in tooltip (es. 252 / 255), o '-' se assente."""
    _wait_properties(alias)

    for label in DURABILITY_LABELS:
        try:
            if Property(alias, label):
                try:
                    cur = PropertyValue(alias, label, 0)
                    mx = PropertyValue(alias, label, 1)
                    return str(cur) + " / " + str(mx)
                except Exception:
                    try:
                        v0 = PropertyValue(alias, label, 0)
                        return str(v0)
                    except Exception:
                        return "(" + label + ")"
        except Exception:
            continue

    if DEBUG_NO_DURABILITY:
        try:
            if Property(alias, "Weight"):
                SysMessage(
                    "[DBG] OPL presenti (es. Weight) ma nessuna riga Durability per questo oggetto.",
                    53,
                )
            else:
                SysMessage("[DBG] OPL ancora vuote o oggetto senza Weight in lista.", 33)
        except Exception:
            SysMessage("[DBG] Lettura proprietà fallita.", 33)

    return "-"


def _item_label(alias):
    try:
        n = Name(alias)
        if n:
            return n
    except Exception:
        pass
    return "?"


SysMessage("--- Equip (layer → nome | durability) ---", 68)

for _layer in LAYERS:
    try:
        has = FindLayer(_layer, "self")
    except Exception:
        has = False

    if not has:
        if PRINT_EMPTY_LAYERS:
            SysMessage(_layer + ": (vuoto)", 902)
        continue

    _nm = _item_label("found")
    _du = _durability_display("found")
    SysMessage(_layer + ": " + _nm + " | " + _du, 946)

SysMessage("--- fine ---", 68)
