# -*- coding: utf-8 -*-
"""
Helper leggeri per macro ClassicAssist (IronPython 2.x).

Uso:
    import uo_helpers
    uo_helpers.clamp(Player.Hits, 0, 100)

Non sostituisce i comandi dell'assistant (Cast, Target, ecc.).
"""


def clamp(value, low, high):
    """Ritorna value limitato all'intervallo [low, high]."""
    if value < low:
        return low
    if value > high:
        return high
    return value


def serial_hex(serial):
    """Formatta un serial numerico come stringa esadecimale 0x........"""
    try:
        return "0x%08X" % (int(serial) & 0xFFFFFFFF)
    except Exception:
        return "0x00000000"


def safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default
