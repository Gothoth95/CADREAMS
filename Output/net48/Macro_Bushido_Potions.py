# -*- coding: utf-8 -*-
# Name: Bushido — pozioni / Confidence
# Description: Poison → debuff → HP o Confidence (se timer HP attivo) → stat → Confidence.
# Author: Local
# Era: Any
#
# DEBUG = True → messaggi [DBG] in chat (timer, ramo, azione). Metti False per disattivare.
#
# Abilitazioni DO_* : True = esegui quel comportamento; False = salta e valuta il ramo successivo
# (stessa priorità: morte → veleno → debuff → HP → stat → Confidence).
#
# Rilevamento DETECT_* : cosa considerare "presente" per entrare nel ramo (es. Mortal rilevato ma ignorato).
# In gioco puoi avere molti stati insieme (veleno+Mortal+Curse+HP bassi+...): sono combinazioni esponenziali,
# ma una sola azione per tick; la priorità sopra decide sempre cosa fare per primo.
#
# HP: timer "hp_pot" assente → heal + crea timer | timer presente → skip heal → Confidence.
# A fine cooldown: RemoveTimer. Con 2H: Create Food -> UseType -> EquipItem("found","TwoHanded").
#
# Combinazioni (una sola azione per tick; il loop esterno ripete):
#   Priorità fissa: morte → veleno → debuff → HP bassi → stat → Confidence
#   - solo veleno / veleno+HP / veleno+debuff → sempre arancio prima
#   - solo debuff (niente veleno) → mela
#   - solo HP bassi (niente veleno/debuff) → gialla o Confidence se cooldown HP
#   - HP bassi + stat basse → prima gialla/Conf; poi (tick dopo) STR/DEX quando HP ok
#   - tutto ok, no Confidence → cast Confidence

# ---------------------------------------------------------------------------
# Opzioni: rilevamento (cosa conta come "attivo" per i rami if/elif)
# ---------------------------------------------------------------------------
DEBUG = True

DETECT_POISON = True
DETECT_MORTAL_STRIKE = True
DETECT_CORPSE_SKIN = True
DETECT_CURSE = True
# Opzionale: altri buff spesso in PvP (la mela può non pulirli su tutti gli shard — prova in game)
DETECT_STRANGLE = False
DETECT_BLEED = False

# ---------------------------------------------------------------------------
# Opzioni: azioni DO_* (True = esegui, False = salta e passa al ramo successivo)
# ---------------------------------------------------------------------------
DO_CURE_POISON = True
DO_REMOVE_DEBUFF = True
DO_HEAL_HP = True
DO_CONFIDENCE_WHEN_HEAL_ON_COOLDOWN = True
DO_STAT_POTIONS = True
DO_STR_POTION = True
DO_DEX_POTION = True
DO_CONFIDENCE = True

# Matrice pratica (non serve un flag per ogni combinazione):
#   - Stati RAW: veleno, Mortal, Corpse Skin, Curse, (Strangle, Bleed), HP bassi, Str/Dex bassi, Confidence assente…
#   - Possono combinarsi in molti modi (es. veleno+Mortal+Curse+HP bassi). Il macro non ha 2^N rami:
#     applica PRIORITÀ fissa e un’azione per tick.
#   - DETECT_* = quali stati RAW fanno entrare nel relativo “tipo” (es. senza Mortal nel rilevamento, il ramo mela non parte).
#   - DO_* = se quel ramo, quando selezionato, esegue davvero l’azione.
#   - STR/DEX: DO_STR_POTION / DO_DEX_POTION affinano cosa bere dentro al ramo stat.

# ---------------------------------------------------------------------------
# Costanti
# ---------------------------------------------------------------------------
DBG_HUE = 1153

HP_SOGLIA = 80
HP_COOLDOWN_MS = 10000
STR_SOGLIA = 150
DEX_SOGLIA = 150

GRAPHIC_ORANGE = 0xF07
GRAPHIC_YELLOW = 0xF0C
GRAPHIC_APPLE = 0x2FD8
GRAPHIC_STR = 0xF08
GRAPHIC_DEX = 0xF09


def _dbg(msg):
    if DEBUG:
        SysMessage("[DBG] %s" % msg, DBG_HUE)


def _dbg_timer_hp():
    """Stato timer hp_pot prima di eventuale RemoveTimer."""
    if not DEBUG or not DO_HEAL_HP:
        return
    if not TimerExists("hp_pot"):
        _dbg("Timer hp_pot: non esiste (puoi bere heal se HP bassi).")
        return
    trascorso = Timer("hp_pot")
    if trascorso >= HP_COOLDOWN_MS:
        _dbg(
            "Timer hp_pot: SI | trascorso=%dms (>= %dms) -> verra rimosso."
            % (trascorso, HP_COOLDOWN_MS)
        )
    else:
        restante = max(0, HP_COOLDOWN_MS - trascorso)
        _dbg(
            "Timer hp_pot: SI | trascorso=%dms | restante ~%dms / %dms"
            % (trascorso, restante, HP_COOLDOWN_MS)
        )


def ha_2h_equippata():
    try:
        return bool(FindLayer("TwoHanded"))
    except Exception:
        return False


def usa_pozione_da_zaino(graphic, nome):
    if DEBUG:
        _dbg("Uso pozione: %s (0x%X)" % (nome, graphic))
    if ha_2h_equippata():
        Cast("Create Food")
        UseType(graphic, -1, "backpack")
        Pause(100)
        EquipItem("found", "TwoHanded")
        Pause(550)
    else:
        UseType(graphic, -1, "backpack")
        Pause(550)
    return True


def stat_bassa():
    """True se Str o Dex sotto soglia (prima di filtrare STR/DEX pot)."""
    return Str() < STR_SOGLIA or Dex() < DEX_SOGLIA


def stat_richiede_pozione():
    """True se serve almeno una pozione stat consentita dalle opzioni."""
    if not DO_STAT_POTIONS:
        return False
    if DO_STR_POTION and Str() < STR_SOGLIA:
        return True
    if DO_DEX_POTION and Dex() < DEX_SOGLIA:
        return True
    return False


def debuff_attivi():
    """Elenco debuff rilevati (secondo DETECT_*). Nomi buff come in BuffExists del client."""
    out = []
    if DETECT_MORTAL_STRIKE and BuffExists("Mortal Strike"):
        out.append("Mortal")
    if DETECT_CORPSE_SKIN and BuffExists("Corpse Skin"):
        out.append("CorpseSkin")
    if DETECT_CURSE and BuffExists("Curse"):
        out.append("Curse")
    if DETECT_STRANGLE and BuffExists("Strangle"):
        out.append("Strangle")
    if DETECT_BLEED and BuffExists("Bleeding"):
        out.append("Bleed")
    return out


def ha_debuff():
    return len(debuff_attivi()) > 0


def snapshot_condizioni():
    """Ritorna dict con tutti i flag per log e per leggere lo scenario."""
    poison_raw = Poisoned("self")
    return {
        "poison": poison_raw and DETECT_POISON,
        "poison_raw": poison_raw,
        "hp_low": Hits("self") < HP_SOGLIA,
        "debuff": ha_debuff(),
        "debuff_tags": debuff_attivi(),
        "stat_low": stat_richiede_pozione(),
        "stat_low_raw": stat_bassa(),
        "conf": BuffExists("Confidence"),
        "hits": Hits("self"),
    }


def dbg_scenario(c):
    """Spiega quale mix è attivo e quale ramo avrà la precedenza (stesso ordine degli elif sotto)."""
    if not DEBUG:
        return
    if c["poison_raw"] and not DETECT_POISON:
        _dbg("Nota: veleno RAW presente ma DETECT_POISON=False (non entra nel ramo veleno).")
    pezzi = []
    if c["poison_raw"]:
        if not DETECT_POISON:
            pezzi.append("veleno[DETECT off]")
        elif not DO_CURE_POISON:
            pezzi.append("veleno[DO off]")
        else:
            pezzi.append("veleno")
    if c["hp_low"]:
        pezzi.append("HP<%d" % HP_SOGLIA + ("" if DO_HEAL_HP else "[OFF]"))
    if c["debuff_tags"]:
        pezzi.append(
            "debuff[%s]" % "+".join(c["debuff_tags"])
            + ("" if DO_REMOVE_DEBUFF else "[OFF]")
        )
    if c.get("stat_low_raw") and not c["stat_low"]:
        pezzi.append("stat_basse[filtrato: solo STR/DEX disatt.]")
    elif c["stat_low"]:
        pezzi.append("stat" + ("" if DO_STAT_POTIONS else "[OFF]"))
    if not pezzi:
        pezzi.append("nessun problema urgente")
    mix = " + ".join(pezzi)

    if Dead("self"):
        ramo = "STOP (morto)"
    elif c["poison"] and DO_CURE_POISON:
        ramo = "arancio"
    elif c["debuff"] and DO_REMOVE_DEBUFF:
        ramo = "mela"
    elif c["hp_low"] and DO_HEAL_HP:
        if TimerExists("hp_pot"):
            ramo = (
                "Confidence (cooldown HP)"
                if DO_CONFIDENCE_WHEN_HEAL_ON_COOLDOWN
                else "nulla (HP in CD, DO_CONF...=False)"
            )
        else:
            ramo = "gialla heal"
    elif c["stat_low"] and DO_STAT_POTIONS:
        ramo = "STR/DEX (solo quelli con DO_STR/DO_DEX)"
    elif not c["conf"] and DO_CONFIDENCE:
        ramo = "Confidence"
    else:
        ramo = "nessuna azione (condizioni ok / tutto disattivo / Confidence gia su)"

    _dbg("Scenario: [%s] -> eseguo: %s" % (mix, ramo))


# --- Snapshot debug + cooldown ---
COND = snapshot_condizioni()
_dbg("--- Bushido tick | Hits=%d ---" % COND["hits"])
dbg_scenario(COND)
_dbg_timer_hp()

if DO_HEAL_HP and TimerExists("hp_pot") and Timer("hp_pot") >= HP_COOLDOWN_MS:
    if DEBUG:
        _dbg("Azione: RemoveTimer(hp_pot) (cooldown finito).")
    RemoveTimer("hp_pot")

# ---------------------------------------------------------------------------
# Priorità: un solo ramo per esecuzione (elif)
# ---------------------------------------------------------------------------
if Dead("self"):
    _dbg("Ramo: MORTO — stop logica pozioni.")
    SysMessage("Macro pozioni: sei morto.", 33)

elif COND["poison"] and DO_CURE_POISON:
    _dbg("Ramo: VELENO -> pozione arancione.")
    if COND["hp_low"]:
        _dbg("(anche HP bassi: al prossimo tick, se non più avvelenato, cura HP.)")
    usa_pozione_da_zaino(GRAPHIC_ORANGE, "cure poison (arancio)")

elif COND["debuff"] and DO_REMOVE_DEBUFF:
    _dbg(
        "Ramo: DEBUFF [%s] -> mela."
        % "+".join(COND["debuff_tags"])
    )
    usa_pozione_da_zaino(GRAPHIC_APPLE, "remove curse / apple")

elif COND["hp_low"] and DO_HEAL_HP:
    _dbg(
        "Ramo: HP BASSI (%d < %d)."
        % (COND["hits"], HP_SOGLIA)
    )
    if not TimerExists("hp_pot"):
        _dbg("Timer hp assente -> tento pozione HEAL gialla.")
        if usa_pozione_da_zaino(GRAPHIC_YELLOW, "heal (gialla)"):
            CreateTimer("hp_pot")
            SetTimer("hp_pot", 0)
            _dbg("Timer hp_pot creato e reset (cooldown %dms)." % HP_COOLDOWN_MS)
    else:
        tr = Timer("hp_pot")
        rest = max(0, HP_COOLDOWN_MS - tr)
        _dbg(
            "Timer hp attivo (trascorso=%dms, restante ~%dms) -> NO heal, provo Confidence."
            % (tr, rest)
        )
        if DO_CONFIDENCE_WHEN_HEAL_ON_COOLDOWN and not BuffExists("Confidence"):
            _dbg("Cast: Confidence (HP in cooldown).")
            Cast("Confidence")
        elif DO_CONFIDENCE_WHEN_HEAL_ON_COOLDOWN:
            _dbg("Confidence gia attivo: niente cast.")
        else:
            _dbg("HP in cooldown: skip Confidence (DO_CONFIDENCE_WHEN_HEAL_ON_COOLDOWN=False).")

elif COND["stat_low"] and DO_STAT_POTIONS:
    _dbg(
        "Ramo: STAT (Str=%d Dex=%d, soglie %d/%d | STRpot=%s DEXpot=%s)."
        % (
            Str(),
            Dex(),
            STR_SOGLIA,
            DEX_SOGLIA,
            DO_STR_POTION,
            DO_DEX_POTION,
        )
    )
    need_str = Str() < STR_SOGLIA and DO_STR_POTION
    need_dex = Dex() < DEX_SOGLIA and DO_DEX_POTION
    if ha_2h_equippata():
        _dbg("Con 2H: Create Food poi STR/DEX (UseType) -> EquipItem found TwoHanded.")
        Cast("Create Food")
        if need_str:
            _dbg("UseType STR (0x%X)." % GRAPHIC_STR)
            UseType(GRAPHIC_STR, -1, "backpack")
        if need_dex:
            _dbg("UseType DEX (0x%X)." % GRAPHIC_DEX)
            UseType(GRAPHIC_DEX, -1, "backpack")
        Pause(100)
        EquipItem("found", "TwoHanded")
        Pause(550)
    else:
        if need_str:
            _dbg("UseType STR senza 2H.")
            UseType(GRAPHIC_STR, -1, "backpack")
            Pause(300)
        if need_dex:
            _dbg("UseType DEX senza 2H.")
            UseType(GRAPHIC_DEX, -1, "backpack")
            Pause(300)

elif not COND["conf"] and DO_CONFIDENCE:
    _dbg("Ramo: Confidence (HP ok, stat ok).")
    Cast("Confidence")
else:
    if DEBUG:
        _dbg("Nessuna azione: Confidence gia attivo e nessun altro ramo.")
