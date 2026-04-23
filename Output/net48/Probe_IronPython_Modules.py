"""
Author: Effy

Sonda quali moduli IronPython 2.x si importano con successo.

Esecuzione (da prompt, nella cartella di IronPython o con ipy nel PATH):

    ipy.exe Probe_IronPython_Modules.py
    ipy.exe Probe_IronPython_Modules.py --modules "C:\\Users\\...\\aaaaaaaa\\Modules"
    ipy.exe Probe_IronPython_Modules.py --out "C:\\Users\\...\\Desktop\\iron_modules_report.txt"

Senza --modules usa la cartella Modules accanto a questo file (..\\Modules).

Non eseguire con python.exe 3.x: i risultati non sarebbero quelli di IronPython.
"""

from __future__ import print_function

import os
import sys
import time
import traceback


DEFAULT_EXTRA_NAMES = (
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
    "sqlite3",
    "xml",
    "xml.etree",
    "xml.etree.ElementTree",
    "datetime",
    "calendar",
    "hashlib",
    "hmac",
    "base64",
    "uuid",
    "threading",
    "Queue",
    "SocketServer",
    "socket",
    "ssl",
    "email",
    "email.message",
)


def _script_dir():
    return os.path.dirname(os.path.abspath(__file__))


def _default_modules_root():
    return os.path.normpath(os.path.join(_script_dir(), "Modules"))


def _discover_local_names(modules_root):
    names = set()
    if not os.path.isdir(modules_root):
        return names
    for entry in os.listdir(modules_root):
        path = os.path.join(modules_root, entry)
        if entry.endswith(".py") and os.path.isfile(path):
            base = entry[:-3]
            if base != "__init__":
                names.add(base)
        elif os.path.isdir(path):
            init_py = os.path.join(path, "__init__.py")
            if os.path.isfile(init_py):
                names.add(entry)
    return names


def _parse_args(argv):
    modules_root = None
    out_path = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--modules" and i + 1 < len(argv):
            modules_root = os.path.normpath(argv[i + 1])
            i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_path = os.path.normpath(argv[i + 1])
            i += 2
        else:
            i += 1
    if modules_root is None:
        modules_root = _default_modules_root()
    if out_path is None:
        out_path = os.path.join(
            _script_dir(),
            "ironpython_modules_report_{0}.txt".format(time.strftime("%Y%m%d_%H%M%S")),
        )
    return modules_root, out_path


def _iron_hint():
    v = sys.version.lower()
    return ("ironpython" in v) or (sys.platform == "cli")


def _try_import(name):
    __import__(name)
    return True, ""


def main():
    modules_root, out_path = _parse_args(sys.argv[1:])

    lines = []
    lines.append("IronPython probe")
    lines.append("sys.version: {0}".format(sys.version.replace("\n", " ")))
    lines.append("sys.executable: {0}".format(sys.executable))
    lines.append("IronPython hint: {0}".format(_iron_hint()))
    lines.append("Modules root: {0}".format(modules_root))
    lines.append("")

    if modules_root not in sys.path:
        sys.path.insert(0, modules_root)

    local_names = _discover_local_names(modules_root)
    all_names = sorted(set(local_names).union(DEFAULT_EXTRA_NAMES))

    ok_n = 0
    fail_n = 0
    lines.append("RISULTATI (nome; origine; ok; errore)")
    lines.append("")

    for name in all_names:
        origin = "cartella" if name in local_names else "solo_nome"
        try:
            if name in sys.modules:
                del sys.modules[name]
        except Exception:
            pass
        try:
            _try_import(name)
            lines.append("{0};{1};OK;".format(name, origin))
            ok_n += 1
        except Exception as ex:
            err = repr(ex).replace(";", ",")
            lines.append("{0};{1};FAIL;{2}".format(name, origin, err))
            fail_n += 1

    lines.append("")
    lines.append("Totale: {0}  OK: {1}  FAIL: {2}".format(len(all_names), ok_n, fail_n))

    text = "\n".join(lines)
    print(text)

    try:
        parent = os.path.dirname(out_path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(out_path, "wb") as f:
            f.write(text.encode("utf-8"))
        print("\nReport scritto in: {0}".format(out_path))
    except Exception as ex:
        print("\nImpossibile scrivere il report: {0}".format(ex))


if __name__ == "__main__":
    if not _iron_hint():
        print(
            "ATTENZIONE: non sembra IronPython. Esegui con ipy.exe per risultati attendibili."
        )
    main()
