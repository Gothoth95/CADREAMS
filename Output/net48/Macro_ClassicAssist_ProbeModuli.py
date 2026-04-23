"""
Author: Effy

Macro ClassicAssist (IronPython 2.x): prova gli import dei moduli nella cartella
Modules e di una lista extra; salva un report su file e avvisa con SysMessage.

Impostazione minima:
- MODULES_PATH: percorso della cartella Modules (quella con collections.py, ecc.).
- REPORT_PATH: dove salvare il .txt (percorso completo).
- LIMIT (0 = nessun limite): se troppi moduli, imposta es. 150 per prova rapida.
"""

from __future__ import print_function

import os
import sys

MODULES_PATH = r"c:\Users\MennE\Desktop\aaaaaaaa\Modules"
REPORT_PATH = r"c:\Users\MennE\Desktop\aaaaaaaa\ironpython_modules_report.txt"
LIMIT = 0

EXTRA_NAMES = (
    "json",
    "re",
    "itertools",
    "functools",
    "operator",
    "collections",
    "heapq",
    "bisect",
    "copy",
    "struct",
    "array",
    "math",
    "random",
    "string",
    "StringIO",
    "cStringIO",
    "urlparse",
    "urllib",
    "urllib2",
    "datetime",
    "calendar",
    "hashlib",
    "hmac",
    "base64",
    "threading",
    "Queue",
    "socket",
    "email",
)


def _scopri_nomi_da_cartella(root):
    nomi = set()
    if not os.path.isdir(root):
        return nomi
    for voce in os.listdir(root):
        percorso = os.path.join(root, voce)
        if voce.endswith(".py") and os.path.isfile(percorso):
            base = voce[:-3]
            if base != "__init__":
                nomi.add(base)
        elif os.path.isdir(percorso):
            init_py = os.path.join(percorso, "__init__.py")
            if os.path.isfile(init_py):
                nomi.add(voce)
    return nomi


def _prova_import(nome):
    __import__(nome)
    return True, ""


def main():
    root = os.path.normpath(MODULES_PATH)
    out = os.path.normpath(REPORT_PATH)

    if root not in sys.path:
        sys.path.insert(0, root)

    da_cartella = _scopri_nomi_da_cartella(root)
    tutti = sorted(set(da_cartella).union(EXTRA_NAMES))
    if LIMIT and LIMIT > 0:
        tutti = tutti[:LIMIT]

    righe = []
    righe.append("Probe moduli (ClassicAssist / IronPython)")
    righe.append("sys.version: " + sys.version.replace("\n", " "))
    righe.append("Cartella Modules: " + root)
    righe.append("")

    ok = 0
    fail = 0
    righe.append("nome;origine;esito;errore")

    for nome in tutti:
        origine = "cartella" if nome in da_cartella else "lista_extra"
        try:
            _prova_import(nome)
            righe.append("{0};{1};OK;".format(nome, origine))
            ok += 1
        except Exception as ex:
            err = repr(ex).replace(";", ",")
            righe.append("{0};{1};FAIL;{2}".format(nome, origine, err))
            fail += 1

    righe.append("")
    righe.append("Totale {0}  OK {1}  FAIL {2}".format(len(tutti), ok, fail))

    testo = "\r\n".join(righe)
    try:
        cartella_out = os.path.dirname(out)
        if cartella_out and not os.path.isdir(cartella_out):
            os.makedirs(cartella_out)
        f = open(out, "wb")
        try:
            f.write(testo.encode("utf-8"))
        finally:
            f.close()
        SysMessage("Probe moduli: OK={0} FAIL={1}. Report: {2}".format(ok, fail, out), 68)
    except Exception as ex:
        SysMessage("Probe moduli: errore scrittura file: {0}".format(ex), 33)


main()
