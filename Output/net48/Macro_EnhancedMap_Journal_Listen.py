# -*- coding: utf-8 -*-
# Name: Enhanced Map — ascolto testo via journal UO
# Description: Enhanced Map (andreakarasho) non è leggibile come finestra da ClassicAssist: quando è agganciato
#   all'assistant, molti eventi vengono inoltrati al client come messaggi di sistema nel journal (vedi sorgente
#   EnhancedMap Core/Network/Packets/PacketHandlers.cs → UOClientManager.SysMessage).
#   Questa macro intercetta quelle righe e le interpreta (chat server, messaggi server, etichetta generica, panic, …).
#
# Limite importante: per le **SharedLabel** sulla mappa il testo descrittivo resta solo nel tool Enhanced Map;
#   nel journal compare solo una riga generica tipo «Added a shared label!», non il contenuto dell'etichetta.
#
# Inoltre: i SysMessage che Enhanced Map manda al client (SendMessage → ClassicUO DISPLAY_TEXT) sono
# «reali» nel journal *grafico* del client, ma spesso NON entrano in Assistant.Engine.Journal: ClassicAssist
# popola quel buffer dai pacchetti di rete / pipeline assist, non da ogni riga disegnata via UOAssist.
# Quindi InJournal / WaitForJournal / dump GetEntireBuffer possono non vedere proprio quella chat EM.
#
# Nel client il journal spesso mostra:
#   System: [Chat][Glory]: sa sa sa
#   prova
# cioè prefisso "System: " sulla prima riga; il testo può andare a capo (seconda riga senza [Chat][...]).
# Questa macro normalizza "System: " e legge tutto ciò che sta sulla *stessa* riga dopo i due punti della chat.
# Le righe di wrap successive non matchano i trigger WaitForJournal ([Chat][, …): ClassicAssist non espone
# una API tipo «ultima riga journal» per unirle automaticamente.

import re

# ---------------------------------------------------------------------------
# Modalità
# ---------------------------------------------------------------------------
# "once"   — una sola attesa (WAIT_MS) poi esce
# "listen" — ripete LISTEN_ROUNDS volte (utile come macro in loop dal profilo)
MODE = "once"
LISTEN_ROUNDS = 60
ROUND_WAIT_MS = 500

# Prefissi che Enhanced Map invia spesso al journal (match parziale InJournal / WaitForJournal)
JOURNAL_TRIGGERS = [
    "[Chat][",
    "[EnhancedMapServer]:",
    "[SharedLabel]",
    "[Panic]",
    "[Alert]",
    "[Login]",
    "[Logout]",
]

# Autore journal: su molti shard i SysMessage sono "System" (prova anche "" se non matcha)
JOURNAL_AUTHOR = "System"

HUE_INFO = 946
HUE_CHAT = 88
HUE_ALERT = 43


def _normalize_journal_line(text):
    """Rimuove il prefisso visivo «System: » che il journal aggiunge davanti al testo."""
    if not text:
        return ""
    s = text.strip()
    low = s.lower()
    if low.startswith("system:"):
        s = s[7:].lstrip()
    return s


def _unpack_wait_result(t):
    """Compat IronPython / ValueTuple."""
    if t is None:
        return None, None
    try:
        return t[0], t[1]
    except Exception:
        pass
    try:
        return t.Item1, t.Item2
    except Exception:
        pass
    return None, None


def parse_enhanced_map_line(text):
    """
    Ritorna (tipo, payload_dict) se la riga sembra Enhanced Map, altrimenti (None, None).

    Formati da PacketHandlers / CommandManager (versione tipica repo GitHub):
      System: [Chat][username]: messaggio   (prefisso journal)
      [Chat][username]: messaggio
      [EnhancedMapServer]: testo
      [SharedLabel][user] ...
      [Panic][user] ...
      [Alert][user] ...
    """
    if not text:
        return None, None

    s = _normalize_journal_line(text)

    if s.startswith("[Chat]["):
        m = re.match(r"^\[Chat\]\[([^\]]+)\]:\s*(.*)$", s, re.DOTALL)
        if m:
            return "chat", {"user": m.group(1), "message": m.group(2)}
        return "chat_raw", {"line": s}

    if s.startswith("[EnhancedMapServer]:"):
        rest = s[len("[EnhancedMapServer]:") :].lstrip()
        if rest.startswith(":"):
            rest = rest[1:].lstrip()
        return "server", {"message": rest}

    if "[SharedLabel]" in s:
        return "shared_label_notice", {"line": s}

    if "[Panic]" in s:
        return "panic", {"line": s}

    if "[Alert]" in s:
        return "alert", {"line": s}

    if s.startswith("[Login]") or s.startswith("[Logout]"):
        return "presence", {"line": s}

    return None, None


def _emit(kind, data):
    if kind == "chat":
        SysMessage(
            "[EM] Chat da %s: %s" % (data["user"], data["message"]),
            HUE_CHAT,
        )
    elif kind == "server":
        SysMessage("[EM] Server: " + data["message"], HUE_INFO)
    elif kind in ("shared_label_notice", "panic", "alert", "presence", "chat_raw"):
        SysMessage("[EM] " + kind + ": " + data.get("line", str(data)), HUE_ALERT)
    else:
        SysMessage("[EM] evento: " + str(data), HUE_INFO)


def _one_wait(timeout_ms):
    try:
        tup = WaitForJournal(JOURNAL_TRIGGERS, timeout_ms, JOURNAL_AUTHOR)
    except TypeError:
        try:
            tup = WaitForJournal(JOURNAL_TRIGGERS, timeout_ms)
        except Exception:
            tup = None
    except Exception:
        tup = None

    idx, line = _unpack_wait_result(tup)
    if idx is None or line is None:
        return False

    kind, payload = parse_enhanced_map_line(line)
    if kind is None:
        SysMessage("[EM] journal (non parsato): " + str(line), HUE_INFO)
        return True

    _emit(kind, payload)
    return True


def main():
    if MODE.strip().lower() == "listen":
        for _ in range(LISTEN_ROUNDS):
            _one_wait(ROUND_WAIT_MS)
            Pause(50)
    else:
        if not _one_wait(8000):
            SysMessage(
                "[EM] Nessun messaggio Enhanced Map nel timeout. "
                "Controlla che la mappa sia agganciata all'assistant e che l'autore journal sia corretto "
                "(costante JOURNAL_AUTHOR).",
                33,
            )


main()
