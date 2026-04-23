# -*- coding: utf-8 -*-
# Name: Hotkey ClassicAssist — stato + messaggio overhead
# Description: Imposta le hotkey dell'assistant (on/off/toggle) e mostra sopra il PG se sono attive o no.
# Author: Local
# Era: Any
#
# ClassicAssist: Hotkeys() invia già un messaggio di sistema nel journal; qui si aggiunge HeadMsg su "self".
#
# IMPORTANTE — Come riattivare dopo Hotkeys("off"):
# Con le hotkey globali spente, ClassicAssist NON esegue le macro richiamate da tasti (tranne eccezioni).
# Per questa macro, nel profilo ClassicAssist imposta sul macro stesso:
#   "Disableable": false
# (Profilo → solitamente Profiles/settings.json → sezione "Macros" → oggetto del macro con questo script.)
# Così il tasto assegnato resta valido anche con hotkey disattivate e puoi fare di nuovo toggle.
# Alternativa senza modificare il profilo: riaccendi da interfaccia ClassicAssist (tab Macro → Play) o dal Macros Gump in gioco.

# ---------------------------------------------------------------------------
# "toggle" = alterna on/off | "on" = sempre attive | "off" = sempre disattive
MODE = "toggle"
# ---------------------------------------------------------------------------

# Hue allineate al comportamento interno di Hotkeys() (MainCommands): ~verde se on, ~rosso se off
HUE_ON = 0x3F
HUE_OFF = 36


def _headmsg_state():
    """Legge HotkeyManager.Enabled e mostra il messaggio overhead sul personaggio."""
    try:
        from ClassicAssist.Data.Hotkeys import HotkeyManager

        enabled = HotkeyManager.GetInstance().Enabled
    except Exception:
        HeadMsg("Hotkey: aggiornato (dettaglio nel journal)", "self", 0x03B2)
        return

    if enabled:
        HeadMsg("Hotkey ClassicAssist: ATTIVE", "self", HUE_ON)
    else:
        HeadMsg("Hotkey ClassicAssist: DISATTIVATE", "self", HUE_OFF)


def main():
    m = (MODE or "toggle").strip().lower()
    if m == "toggle":
        Hotkeys()
    elif m == "on":
        Hotkeys("on")
    elif m == "off":
        Hotkeys("off")
    else:
        SysMessage('MODE: usa "toggle", "on" o "off".', HUE_OFF)
        return

    _headmsg_state()


main()
