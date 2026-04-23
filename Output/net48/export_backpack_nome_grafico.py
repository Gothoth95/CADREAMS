# -*- coding: utf-8 -*-
"""
Macro ClassicAssist (IronPython): esporta zaino in .txt come base per variabili fisse.

USO: incolla questo script in un macro Python in ClassicAssist e avvialo in game.
NON eseguire con python.exe sul PC: Engine, SysMessage, ecc. esistono solo nel client.

Output: C:\\Users\\MennE\\Desktop\\script CUO + file\\pvp_pack.txt
Contiene un blocco Python pronto da copiare: dizionario PVP_PACK con righe tipo:
    'nome oggetto': '0xGRAFICO',
"""

from Assistant import Engine

import clr

clr.AddReference("System")
from System.IO import Directory, File
from System.Text import Encoding

OUT_DIR = r"C:\Users\MennE\Desktop\script CUO + file"
OUT_FILE = "pvp_pack.txt"


def _py_quote(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def main():
    if Engine.Player is None:
        SysMessage("Nessun personaggio in game.", 33)
        return

    bp = Engine.Player.Backpack
    if bp is None:
        SysMessage("Zaino non trovato.", 33)
        return

    if bp.Container is None:
        UseObject("backpack")
        if not WaitForContents("backpack", 5000):
            SysMessage("Timeout contenuti zaino.", 33)
            return

    items = bp.Container.SelectEntities(lambda i: True)
    seen_pair = set()
    pairs = []
    if items is not None:
        for it in items:
            if it is None:
                continue
            raw = it.Name if it.Name else ""
            name = raw.strip() if raw else ""
            if not name:
                name = "senza_nome_0x%X" % it.ID
            pair = (name, it.ID)
            if pair in seen_pair:
                continue
            seen_pair.add(pair)
            pairs.append(pair)

    by_name = {}
    for name, gid in pairs:
        if name not in by_name:
            by_name[name] = []
        by_name[name].append(gid)

    entries = []
    for name in sorted(by_name.keys()):
        gids = sorted(set(by_name[name]))
        if len(gids) == 1:
            entries.append((name, gids[0]))
        else:
            for gid in gids:
                entries.append(("%s (0x%X)" % (name, gid), gid))

    dict_lines = []
    for name, gid in entries:
        dict_lines.append(
            "    %s: %s," % (_py_quote(name), _py_quote("0x%X" % gid))
        )

    body_dict = "\r\n".join(dict_lines)
    header = (
        "# -*- coding: utf-8 -*-\r\n"
        "# Lista variabili fisse — PVP pack (generato dallo zaino)\r\n"
        "# Copia PVP_PACK nei tuoi script ClassicAssist.\r\n"
        "# Oggetti unici (nome + grafico): %d\r\n"
        "\r\n"
        "PVP_PACK = {\r\n"
        "%s\r\n"
        "}\r\n"
    ) % (len(entries), body_dict)

    Directory.CreateDirectory(OUT_DIR)
    full = OUT_DIR + "\\" + OUT_FILE
    File.WriteAllText(full, header, Encoding.UTF8)

    SysMessage("Salvato PVP_PACK: %s (%d voci)" % (full, len(entries)), 68)


main()
