# -*- coding: utf-8 -*-
# Name: Journal — ultimi messaggi (SysMessage)
# Description: Stampa in chat (SysMessage) le ultime righe del buffer journal di ClassicAssist.
# Author: Local
# Era: Any
#
# Usa Assistant.Engine.Journal.GetEntireBuffer() (buffer circolare interno, tipicamente fino a ~1024 voci).
# Ordine: dal più vecchio al più recente nell'array; qui mostriamo i più recenti per primi.
#
# IMPORTANTE — «Journal» visivo ≠ journal ClassicAssist:
# Enhanced Map (e altri tool che mandano SysMessage all'assistant) usano SendMessage → ClassicUO
# gestisce UOAMessage.DISPLAY_TEXT e disegna il testo in game (MessageManager / journal UI) senza
# passare dal flusso pacchetti che ClassicAssist registra in Engine.Journal. Per questo quei
# messaggi li vedi nel journal del client ma spesso NON compaiono qui né in InJournal/WaitForJournal.

Engine = None
try:
    from Assistant import Engine as _Eng
    Engine = _Eng
except Exception:
    try:
        import Assistant as _Asst
        Engine = _Asst.Engine
    except Exception:
        pass

# Quante righe stampare (dal più recente)
LAST_COUNT = 20

# Hue per riga (journal system spesso hue 945/946; cambia a piacere)
HUE_LINE = 946
HUE_HEADER = 68
HUE_ERR = 33


def _journal_entries():
    if Engine is None:
        return None
    try:
        buf = Engine.Journal
        if buf is None:
            return None
        return buf.GetEntireBuffer()
    except Exception:
        return None


def _fmt_line(je):
    try:
        name = je.Name
    except Exception:
        name = None
    if not name:
        name = "?"
    try:
        txt = je.Text
    except Exception:
        txt = ""
    if txt is None:
        txt = ""
    return name + ": " + txt


def main():
    arr = _journal_entries()
    if arr is None:
        SysMessage(
            "[Journal] Impossibile leggere Engine.Journal (import Assistant fallito o buffer assente).",
            HUE_ERR,
        )
        return

    try:
        n = len(arr)
    except Exception:
        SysMessage("[Journal] Buffer non iterabile.", HUE_ERR)
        return

    SysMessage("[Journal] ultime %d / %d righe (più recente in alto):" % (min(LAST_COUNT, n), n), HUE_HEADER)

    start = max(0, n - LAST_COUNT)
    # indici da n-1 verso start (più recente prima)
    for i in range(n - 1, start - 1, -1):
        try:
            line = _fmt_line(arr[i])
        except Exception as ex:
            line = "(errore riga: %s)" % ex
        if len(line) > 230:
            line = line[:227] + "..."
        SysMessage(line, HUE_LINE)


main()
