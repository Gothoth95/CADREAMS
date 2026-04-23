# -*- coding: utf-8 -*-
"""
Confronta i nomi in classicassist_api.py con i comandi macro reali in ClassicAssist.

Fonti (online, repository ufficiale):
  - ClassicAssist/Data/Macros/Commands/*.cs — metodi public static esposti al motore Python
  - wiki Macro-Commands.md — indice generato (incrocio opzionale)

Uso::
    python verify_classicassist_api.py

Output::
    classicassist_api_verify_report.txt (stessa cartella dello script)

Gli alias predefiniti (self, backpack, bank) sono documentati nel docstring di
classicassist_api.py, non come ``def`` fittizie.
"""

from __future__ import print_function

import ast
import json
import os
import re
import sys
from datetime import datetime

try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
except ImportError:
    urlopen = None  # type: ignore

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_STUB = os.path.join(SCRIPT_DIR, "classicassist_api.py")
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "classicassist_api_verify_report.txt")

RAW_BASE = (
    "https://raw.githubusercontent.com/Reetus/ClassicAssist/master/"
    "ClassicAssist/Data/Macros/Commands/"
)
WIKI_MD = (
    "https://raw.githubusercontent.com/wiki/Reetus/ClassicAssist/Macro-Commands.md"
)

GITHUB_API_LIST = (
    "https://api.github.com/repos/Reetus/ClassicAssist/contents/"
    "ClassicAssist/Data/Macros/Commands?ref=master"
)

METHOD_RE = re.compile(
    r"^\s*public\s+static\s+.+\s+(\w+)\s*\(",
    re.MULTILINE,
)

# Il regex sopra non cattura ``PropertyValue`` (firma ``public static T PropertyValue``).
CS_EXTRA_MACRO_NAMES = frozenset(["PropertyValue"])

WIKI_LINK_RE = re.compile(r"\[([A-Za-z0-9_]+)\]\([^)]+\)")


def fetch_text(url, timeout=45):
    req = Request(url, headers={"User-Agent": "classicassist-api-verify/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def list_command_cs_files():
    req = Request(GITHUB_API_LIST, headers={"User-Agent": "classicassist-api-verify/1.0"})
    with urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return sorted(
        x["name"] for x in data if x.get("type") == "file" and x["name"].endswith(".cs")
    )


def extract_methods_from_cs(text):
    return set(METHOD_RE.findall(text))


def load_stub_function_names(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read(), filename=path)
    names = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            names.append(node.name)
    return names


def main():
    if urlopen is None:
        print("urllib non disponibile", file=sys.stderr)
        return 2

    stub_path = DEFAULT_STUB
    out_path = DEFAULT_OUT

    try:
        cs_files = list_command_cs_files()
    except (URLError, HTTPError, OSError, ValueError) as e:
        print("Impossibile elencare i file .cs da GitHub: %s" % e, file=sys.stderr)
        return 1

    source_names = set()
    per_file = {}
    for fn in cs_files:
        url = RAW_BASE + fn
        try:
            text = fetch_text(url)
        except (URLError, HTTPError, OSError) as e:
            print("Errore scaricando %s: %s" % (url, e), file=sys.stderr)
            return 1
        methods = extract_methods_from_cs(text)
        per_file[fn] = sorted(methods)
        source_names |= methods

    source_names |= CS_EXTRA_MACRO_NAMES

    wiki_names = set()
    try:
        wiki_text = fetch_text(WIKI_MD)
        wiki_names = set()
        for line in wiki_text.splitlines():
            s = line.strip()
            if s.startswith("#"):
                continue
            wiki_names.update(WIKI_LINK_RE.findall(line))
    except (URLError, HTTPError, OSError) as e:
        wiki_names = set()
        wiki_err = str(e)
    else:
        wiki_err = None

    try:
        stub_names = load_stub_function_names(stub_path)
    except (OSError, SyntaxError) as e:
        print("Errore leggendo %s: %s" % (stub_path, e), file=sys.stderr)
        return 1

    stub_set = set(stub_names)

    lines = []
    lines.append("ClassicAssist — verifica classicassist_api.py")
    lines.append("Generato: %s" % datetime.now().isoformat(timespec="seconds"))
    lines.append("Stub file: %s" % stub_path)
    lines.append(
        "Fonte comandi: GitHub Reetus/ClassicAssist (branch master), cartella "
        "ClassicAssist/Data/Macros/Commands/"
    )
    lines.append("File .cs analizzati: %d" % len(cs_files))
    lines.append("Comandi unici trovati nel sorgente C#: %d" % len(source_names))
    if wiki_err:
        lines.append("Wiki Macro-Commands.md: non scaricato (%s)" % wiki_err)
    else:
        lines.append("Voci indice wiki (link): %d" % len(wiki_names))

    lines.append("")
    lines.append("=== Riepilogo ===")
    ok = sorted(stub_set & source_names)
    missing = sorted(stub_set - source_names)

    lines.append("Stub definiti: %d" % len(stub_set))
    lines.append("Presenti nel sorgente C# (public static): %d" % len(ok))
    lines.append("NON trovati come comando macro nel sorgente C#: %d" % len(missing))
    lines.append("")

    lines.append("=== OK — nome stub presente nel sorgente ClassicAssist ===")
    for n in ok:
        lines.append("  %s" % n)

    lines.append("")
    lines.append("=== Problemi — stub non trovato come public static in Commands/*.cs ===")
    if not missing:
        lines.append("  (nessuno)")
    else:
        for n in missing:
            lines.append("  %s" % n)

    if wiki_names:
        lines.append("")
        lines.append("=== Incrocio wiki (opzionale) ===")
        in_wiki_not_stub = sorted(wiki_names - stub_set)
        lines.append(
            "Comandi nell'indice wiki ma non come def nello stub: %d (campione max 40)"
            % len(in_wiki_not_stub)
        )
        for n in in_wiki_not_stub[:40]:
            lines.append("  %s" % n)
        if len(in_wiki_not_stub) > 40:
            lines.append("  ...")

        stub_not_in_wiki = sorted(stub_set - wiki_names)
        lines.append("")
        lines.append(
            "Def nello stub ma non trovati come link nell'indice wiki: %d"
            % len(stub_not_in_wiki)
        )
        for n in stub_not_in_wiki:
            lines.append("  %s" % n)

    lines.append("")
    lines.append("=== File C# e metodi estratti (per ispezione) ===")
    for fn in sorted(per_file.keys()):
        lines.append("-- %s (%d metodi)" % (fn, len(per_file[fn])))
        lines.append("   %s" % ", ".join(per_file[fn]))

    report = "\n".join(lines) + "\n"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(report)

    print(report)
    print("Report salvato in: %s" % out_path, file=sys.stderr)
    return 3 if missing else 0


if __name__ == "__main__":
    sys.exit(main() or 0)
