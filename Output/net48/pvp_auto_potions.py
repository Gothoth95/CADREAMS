# -*- coding: utf-8 -*-
"""
Macro ClassicAssist (IronPython) — pozioni PvP (cure / heal / refresh / str / agi).

Incolla in ClassicAssist ed esegui in game. Non avviare con Python desktop.

Priorità in ogni giro: Greater Cure se avvelenato → Greater Heal (con CD) →
Greater Refreshment se stamina bassa → coppia Greater Strength + Greater Agility.

Heal: se Hits() <= soglia (default 150) e CD heal OK.
Agility: se Dex() <= soglia (default 80), CD agi OK, e c’è la pozione.
Strength / Agility: un solo ciclo mani — togli TwoHanded, bevi STR, bevi AGI (se servono),
poi rimetti l’arma. CD str/agi restano indipendenti.

Tutte le pozioni: se TwoHanded è occupato, togli → bevi → rimetti (cure/heal/refresh
una alla volta; str+agi in sequenza nello stesso ciclo mani).
"""

# ---------------------------------------------------------------------------
# --- IMPOSTA QUI ---
# ---------------------------------------------------------------------------

# True = ciclo infinito | False = esegue un solo passaggio e termina
LOOP_FOREVER = False

# True = SysMessage di debug (non influisce sulle pozioni)
DEBUG_MSG = False

# Greater Heal: bevi se Hits() <= questo valore (0 = disattivato)
HEAL_IF_HITS_AT_OR_BELOW = 150

# Greater Agility: bevi se Dex() <= questo valore (0 = nessun check Dex, solo CD + pozione)
AGI_IF_DEX_AT_OR_BELOW = 80

# Refresh: se Stam() < questo valore (0 = disattivato)
STAM_IF_STAMINA_BELOW = 0  # es. 20

# Cooldown SOLO Greater Strength (ms). 0 = nessun cooldown tra uno Strength e il successivo.
STR_POTION_COOLDOWN_MS = 0

# Cooldown SOLO Greater Agility (ms). 0 = nessun cooldown.
AGI_POTION_COOLDOWN_MS = 0

# Cooldown Greater Heal (fisso richiesto: 10 secondi). Modifica solo se ti serve.
HEAL_POTION_COOLDOWN_MS = 10000

# Ritardo tra un giro e l’altro (ms) quando LOOP_FOREVER è True
LOOP_PAUSE_MS = 300

# Grafici tipici OSI / molti shard (verifica hue se sul tuo server “greater” = hue diversa)
GRAPH_GREATER_CURE = 0xF07
GRAPH_GREATER_HEAL = 0xF0C
GRAPH_GREATER_REFRESH = 0xF0B  # Total refresh / refreshment
GRAPH_GREATER_STRENGTH = 0xF09
GRAPH_GREATER_AGILITY = 0xF08

# -1 = qualsiasi hue (ATTENZIONE: potresti bevere pozioni non-“greater” se condividono ID)
HUE_ANY = -1

# ---------------------------------------------------------------------------
# Timer names (interni; non servono variabili utente)
# ---------------------------------------------------------------------------
# Stessi nomi in timer_dashboard_ironpython.py (righe ClassicAssist) + ms = *_POTION_COOLDOWN_MS
T_HEAL_CD = "pvp_auto_pots_heal_cd"
T_STR_CD = "pvp_auto_pots_str_cd"
T_AGI_CD = "pvp_auto_pots_agi_cd"


def dbg(msg):
    if DEBUG_MSG:
        SysMessage(str(msg), 946)


def cooling_down(timer_name, cd_ms):
    if cd_ms <= 0:
        return False
    if not TimerExists(timer_name):
        return False
    return Timer(timer_name) < cd_ms


def start_cooldown(timer_name):
    if not TimerExists(timer_name):
        CreateTimer(timer_name)
    SetTimer(timer_name, 0)


def drink_from_backpack(potion_serial):
    UseObject(potion_serial)
    Pause(550)


def twohanded_unequip_to_backpack():
    """Ritorna il serial dell'arma TwoHanded messa in zaino, o None."""
    if not FindLayer("TwoHanded", "self"):
        return None
    wpn = GetAlias("found")
    MoveItem(wpn, 1, "backpack", 0, 0)
    Pause(750)
    return wpn


def twohanded_requip(serial):
    if serial:
        EquipItem(serial, "TwoHanded")
        Pause(750)


def drink_potion_serial_with_hands_free(pot_serial, after_drink=None):
    """
    Toglie TwoHanded se serve, beve, rimette l'arma.
    after_drink: callable da eseguire solo se UseObject è andato a buon fine (es. start CD).
    """
    wpn = twohanded_unequip_to_backpack()
    try:
        drink_from_backpack(pot_serial)
        if after_drink:
            after_drink()
    finally:
        twohanded_requip(wpn)


def _poisoned():
    """ClassicAssist: prova Poisoned() poi Poisoned('self')."""
    try:
        return bool(Poisoned())
    except Exception:
        pass
    return bool(Poisoned("self"))


def _hits():
    try:
        return Hits()
    except Exception:
        pass
    return Hits("self")


def _stam():
    try:
        return Stam()
    except Exception:
        pass
    return Stam("self")


def _dex():
    return Dex()


def try_greater_cure():
    if not _poisoned():
        return
    if not FindType(GRAPH_GREATER_CURE, HUE_ANY, "backpack"):
        dbg("Cure: nessuna pozione in zaino")
        return
    pot = GetAlias("found")
    dbg("Cure: uso")
    drink_potion_serial_with_hands_free(pot, None)


def try_greater_heal():
    if HEAL_IF_HITS_AT_OR_BELOW <= 0:
        return
    h = _hits()
    if h > HEAL_IF_HITS_AT_OR_BELOW:
        return
    if cooling_down(T_HEAL_CD, HEAL_POTION_COOLDOWN_MS):
        dbg("Heal: in cooldown")
        return
    if not FindType(GRAPH_GREATER_HEAL, HUE_ANY, "backpack"):
        dbg("Heal: nessuna pozione")
        return
    pot = GetAlias("found")
    dbg("Heal: uso (HP %s)" % h)

    def _after():
        start_cooldown(T_HEAL_CD)

    drink_potion_serial_with_hands_free(pot, _after)


def try_refreshment():
    if STAM_IF_STAMINA_BELOW <= 0:
        return
    s = _stam()
    if s >= STAM_IF_STAMINA_BELOW:
        return
    if not FindType(GRAPH_GREATER_REFRESH, HUE_ANY, "backpack"):
        dbg("Refresh: nessuna pozione")
        return
    pot = GetAlias("found")
    dbg("Refresh: uso")
    drink_potion_serial_with_hands_free(pot, None)


def _want_strength_potion():
    if cooling_down(T_STR_CD, STR_POTION_COOLDOWN_MS):
        dbg("Strength: in cooldown")
        return False
    return True


def _want_agility_potion():
    if cooling_down(T_AGI_CD, AGI_POTION_COOLDOWN_MS):
        dbg("Agility: in cooldown")
        return False
    if AGI_IF_DEX_AT_OR_BELOW > 0:
        d = _dex()
        if d > AGI_IF_DEX_AT_OR_BELOW:
            return False
    return True


def try_greater_str_then_agility():
    """
    Una sola volta: togli TwoHanded, bevi STR (se eleggibile e c’è in zaino),
    poi AGI (se eleggibile e c’è), poi rimetti arma.
    """
    do_str = _want_strength_potion()
    do_agi = _want_agility_potion()

    str_serial = None
    agi_serial = None

    if do_str and FindType(GRAPH_GREATER_STRENGTH, HUE_ANY, "backpack"):
        str_serial = GetAlias("found")
    elif do_str:
        dbg("Strength: nessuna pozione")

    if do_agi and FindType(GRAPH_GREATER_AGILITY, HUE_ANY, "backpack"):
        agi_serial = GetAlias("found")
    elif do_agi:
        dbg("Agility: nessuna pozione")

    if str_serial is None and agi_serial is None:
        return

    wpn = twohanded_unequip_to_backpack()
    try:
        if str_serial is not None:
            dbg("Strength: uso")
            drink_from_backpack(str_serial)
            start_cooldown(T_STR_CD)
            Pause(400)
        if agi_serial is not None:
            dbg("Agility: uso")
            drink_from_backpack(agi_serial)
            start_cooldown(T_AGI_CD)
    finally:
        twohanded_requip(wpn)


def run_once():
    WaitForContents("backpack", 3000)
    try_greater_cure()
    try_greater_heal()
    try_refreshment()
    try_greater_str_then_agility()


def main():
    if LOOP_FOREVER:
        while True:
            run_once()
            Pause(LOOP_PAUSE_MS)
    else:
        run_once()


main()
