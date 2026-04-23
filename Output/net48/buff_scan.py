# -*- coding: utf-8 -*-
# ClassicAssist — elenco buff attivi con tempo residuo
# Comandi macro (tutti, con esempi): https://github.com/Reetus/ClassicAssist/wiki/Macro-Commands
# BuffExists / BuffTime: sezione Entity — https://github.com/Reetus/ClassicAssist/wiki/Entity
# BuffTime() in millisecondi. Nomi buff = BuffIcons.json in Data/ del progetto ClassicAssist.
#
# IronPython in ClassicAssist spesso NON ha moduli json/os: nessuna importazione di quelli.
# Modifica _BUFFICONS_PATHS con il percorso completo al tuo BuffIcons.json.

_BUFFICONS_PATHS = [
    r"C:\Users\MennE\Desktop\aaaaaaaa\BuffIcons.json",
]


def _is_readable_file(path):
    try:
        f = open(path, "r")
        f.close()
        return True
    except Exception:
        return False


def _find_bufficons_path():
    for p in _BUFFICONS_PATHS:
        if p and _is_readable_file(p):
            return p
    return None


def _basename(path):
    path = path.replace("/", "\\")
    if "\\" in path:
        return path.rsplit("\\", 1)[-1]
    return path


def _load_names_from_json_text(text):
    """Estrae i valori Name da BuffIcons.json senza json/re."""
    out = []
    key = '"Name"'
    pos = 0
    while True:
        i = text.find(key, pos)
        if i < 0:
            break
        colon = text.find(":", i + len(key))
        if colon < 0:
            break
        k = colon + 1
        while k < len(text) and text[k] in " \t\r\n":
            k += 1
        if k >= len(text) or text[k] != '"':
            pos = i + 1
            continue
        start = k + 1
        end = text.find('"', start)
        if end < 0:
            break
        out.append(text[start:end])
        pos = end + 1
    return out


def _load_names(path):
    f = open(path, "r")
    try:
        text = f.read()
    finally:
        f.close()
    return _load_names_from_json_text(text)


def _fmt_remain(ms):
    try:
        ms = float(ms)
    except Exception:
        return "?"
    if ms <= 0:
        return "attivo (timer n/d)"
    sec = int(ms // 1000)
    if sec < 60:
        return "%ds" % sec
    if sec < 3600:
        return "%dm %02ds" % (sec // 60, sec % 60)
    if sec < 86400:
        h = sec // 3600
        m = (sec % 3600) // 60
        return "%dh %02dm" % (h, m)
    d = sec // 86400
    h = (sec % 86400) // 3600
    return "%dg %dh" % (d, h)


def main():
    path = _find_bufficons_path()
    if not path:
        SysMessage(
            "buff_scan: BuffIcons.json non trovato. Imposta _BUFFICONS_PATHS in cima allo script.",
            33,
        )
        return

    try:
        names = _load_names(path)
    except Exception as e:
        SysMessage("buff_scan: errore lettura file: %s" % e, 33)
        return

    if not names:
        SysMessage("buff_scan: nessun nome estratto da BuffIcons.json", 33)
        return

    active = []
    for name in names:
        try:
            if BuffExists(name):
                t = BuffTime(name)
                active.append((name, t))
        except Exception:
            pass

    if not active:
        SysMessage(
            "Nessun buff attivo tra i %d tipi noti (fonte: %s)."
            % (len(names), _basename(path)),
            68,
        )
        return

    def _sort_key(item):
        name, t = item
        try:
            tt = float(t)
        except Exception:
            tt = 0.0
        if tt <= 0:
            return (1, name)
        return (0, tt)

    active.sort(key=_sort_key)

    lines = []
    for name, t in active:
        lines.append("%s  ->  %s" % (name, _fmt_remain(t)))
    body = "\n".join(lines)
    title = "Buff attivi: %d (da %s)" % (len(active), _basename(path))

    try:
        MessageBox(title, body)
    except Exception:
        pass

    SysMessage("Buff scan: %d attivi — apri il messaggio." % len(active), 88)


main()
