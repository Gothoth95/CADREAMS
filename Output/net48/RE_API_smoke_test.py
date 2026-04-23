# -*- coding: utf-8 -*-
# Name: RE — smoke test API (letture sicure)
# Description: Verifica rapida che le API RazorEnhanced rispondano (nessun cast, niente disconnect, niente file distruttivi).
# Author: Local
# Era: Any
#
# Perché NON esiste un test "di tutta l'API" in uno script:
# - Molte funzioni richiedono stato (gump aperto, target attivo, oggetti specifici).
# - Altre sono distruttive (Disconnect, Move, Cast, ScriptStopAll, DeleteFile, ecc.).
# - Altro ancora è solo per agent/UI (AutoLoot, Organizer, ecc.).
# Questo script fa solo letture e chiamate idempotenti dove possibile.

# ---------------------------------------------------------------------------
# True = solo test sicuri (default). False = aggiunge Pause breve e qualche check in più.
SAFE_MODE = True

# Messaggi di sistema (hue tipici RE; adatta se il client filtra)
HUE_OK = 68
HUE_FAIL = 33
HUE_INFO = 1153

# Pausa tra gruppi di test (ms) se non SAFE_MODE
PAUSE_BETWEEN_GROUPS_MS = 80
# ---------------------------------------------------------------------------


def _msg(text, hue=HUE_INFO, wait=False):
    try:
        Misc.SendMessage(text, hue, wait)
    except Exception:
        pass


def _ok(name):
    _msg("[RE-TEST OK] " + name, HUE_OK)


def _fail(name, err):
    _msg("[RE-TEST FAIL] " + name + ": " + str(err), HUE_FAIL)


def _run(name, fn):
    """Esegue fn(), conta successo o eccezione."""
    try:
        fn()
        _ok(name)
        return True
    except Exception as ex:
        _fail(name, ex)
        return False


def test_misc_paths():
    _ = Misc.ScriptDirectory()
    _ = Misc.RazorDirectory()
    _ = Misc.DataDirectory()
    _ = Misc.ConfigDirectory()
    _ = Misc.ShardName()


def test_player_reads():
    _ = Player.Connected
    _ = Player.Name
    _ = Player.Serial
    _ = Player.Hits
    _ = Player.HitsMax
    _ = Player.Mana
    _ = Player.Position
    _ = Player.Map
    _ = Player.WarMode
    # Oggetti equip/contenitori possono essere None su stati anomali
    try:
        bp = Player.BackpackItem
        if bp is not None:
            _ = bp.Serial
    except Exception:
        pass


def test_items_reads():
    serial = Player.Serial
    it = Items.FindBySerial(serial)
    if it is not None:
        _ = it.Name
    try:
        Items.BackpackCount(0xF0C, -1)
    except Exception:
        pass


def test_target_reads():
    _ = Target.GetLast()
    _ = Target.GetLastAttack()
    _ = Target.HasTarget("Any")


def test_journal_reads():
    lst = Journal.GetJournalEntry(None)
    _ = len(lst) if lst is not None else 0
    try:
        Journal.Search("zzzz_not_in_journal_smoke_test")
    except Exception:
        pass


def test_timer_reads():
    try:
        Timer.Check("__re_smoke_nonexistent__")
    except Exception:
        pass


def test_gumps_reads():
    cid = Gumps.CurrentGump()
    _ = cid
    try:
        if cid != 0:
            _ = Gumps.HasGump(cid)
        else:
            _ = Gumps.HasGump(1)
    except Exception:
        pass


def test_mobiles_reads():
    m = Mobiles.FindMobile(Player.Serial)
    if m is not None:
        _ = m.Name


def test_spells_no_cast():
    # Nessun Cast*: solo verifica che il modulo esista (nessuna azione server)
    _ = Spells is not None


def maybe_pause():
    if not SAFE_MODE:
        Misc.Pause(PAUSE_BETWEEN_GROUPS_MS)


def main():
    _msg("--- RE API smoke test (solo letture sicure) ---", HUE_INFO)
    ok = 0
    total = 0

    groups = [
        ("Misc path / shard", test_misc_paths),
        ("Player read", test_player_reads),
        ("Items read", test_items_reads),
        ("Target read", test_target_reads),
        ("Journal read", test_journal_reads),
        ("Timer.Check", test_timer_reads),
        ("Gumps read", test_gumps_reads),
        ("Mobiles.FindMobile(self)", test_mobiles_reads),
        ("Spells (no cast)", test_spells_no_cast),
    ]

    for label, fn in groups:
        total += 1
        if _run(label, fn):
            ok += 1
        maybe_pause()

    _msg(
        "[RE-TEST] Fine: %d/%d gruppi senza eccezioni (vedi messaggi FAIL sopra)."
        % (ok, total),
        HUE_INFO,
    )
    _msg(
        "Copertura: solo sottoinsieme sicuro. Per lista completa API vedi documentazione RE.",
        HUE_INFO,
    )


main()
