# -*- coding: utf-8 -*-
# Name: Prova ClassicAssist
# Description: Test esteso: alias, statistiche, posizione, skill, buff, timer, liste, journal, ping, FindType/CountType (solo lettura).
# Author: Local
# Era: Any
#
# Nessuno spell, target ostile, movimento o uso oggetti. Se una riga fallisce, le altre continuano.
# Sintassi compatibile IronPython 2.7 (nessuna f-string).

Pause(80)
SysMessage("========== PROVA CLASSICASSIST (esteso) ==========", 88)


def _line(tag, text, ok=True):
    hue = 68 if ok else 33
    SysMessage("[%s] %s" % (tag, text), hue)


def _safe(tag, fn):
    try:
        return fn()
    except Exception:
        _line(tag, "eccezione (vedi client log se disponibile)", False)
        return None


# --- Alias ---
_sec = lambda t: (Pause(40), SysMessage("-- %s --" % t, 88))
_sec("Alias")

_line("GetAlias", "self=0x%X" % GetAlias("self") if GetAlias("self") else "self=0")
_line("GetAlias", "backpack=0x%X" % GetAlias("backpack") if GetAlias("backpack") else "backpack=0")
_line("GetAlias", "bank=0x%X" % GetAlias("bank") if GetAlias("bank") else "bank=0")
_safe(
    "FindAlias",
    lambda: _line(
        "FindAlias",
        "self=%s" % FindAlias("self"),
        bool(FindAlias("self")),
    ),
)

# --- Vitali / risorse (serial implicito o "self") ---
_sec("Vitali e risorse")

for label, call in [
    ("Hits", lambda: Hits("self")),
    ("MaxHits", lambda: MaxHits("self")),
    ("Mana", lambda: Mana("self")),
    ("MaxMana", lambda: MaxMana("self")),
    ("Stam", lambda: Stam("self")),
    ("MaxStam", lambda: MaxStam("self")),
    ("Weight", lambda: Weight()),
    ("MaxWeight", lambda: MaxWeight()),
    ("Gold", lambda: Gold()),
]:
    v = _safe(label, call)
    if v is not None:
        _line(label, str(v))

_safe("DiffWeight", lambda: _line("DiffWeight", str(DiffWeight())))
_safe("Luck", lambda: _line("Luck", str(Luck())))
_safe("TithingPoints", lambda: _line("TithingPoints", str(TithingPoints())))

# --- Attributi primari ---
_sec("Str / Dex / Int")
_safe("Str", lambda: _line("Str", str(Str())))
_safe("Dex", lambda: _line("Dex", str(Dex())))
_safe("Int", lambda: _line("Int", str(Int())))

# --- Map / coordinate ---
_sec("Mappa e coordinate")
_safe("Map", lambda: _line("Map", str(Map())))
_safe("X", lambda: _line("X", str(X("self"))))
_safe("Y", lambda: _line("Y", str(Y("self"))))
_safe("Z", lambda: _line("Z", str(Z("self"))))
_safe("Distance", lambda: _line("Distance(self)", str(Distance("self"))))

# --- Nome / corpo / notorieta ---
_sec("Nome, grafico, stato")
_safe("Name", lambda: _line("Name", str(Name("self"))))
_safe("Graphic", lambda: _line("Graphic", str(Graphic("self"))))
_safe("Hue", lambda: _line("Hue", str(Hue("self"))))
_safe("War", lambda: _line("War(self)", str(War("self"))))
_safe("Poisoned", lambda: _line("Poisoned", str(Poisoned("self"))))
_safe("Dead", lambda: _line("Dead", str(Dead("self"))))
_safe("Hidden", lambda: _line("Hidden", str(Hidden("self"))))
_safe("Mounted", lambda: _line("Mounted", str(Mounted("self"))))
_safe("YellowHits", lambda: _line("YellowHits", str(YellowHits("self"))))
_safe("Paralyzed", lambda: _line("Paralyzed", str(Paralyzed("self"))))
_safe("Criminal", lambda: _line("Criminal(self)", str(Criminal("self"))))
_safe("Innocent", lambda: _line("Innocent(self)", str(Innocent("self"))))
_safe("InFriendList", lambda: _line("InFriendList(self)", str(InFriendList("self"))))
_safe("InParty", lambda: _line("InParty(self)", str(InParty("self"))))
_safe("Direction", lambda: _line("Direction(self)", str(Direction("self"))))
_safe("DiffHits", lambda: _line("DiffHits(self)", str(DiffHits("self"))))
_safe(
    "DiffHitsPercent",
    lambda: _line("DiffHitsPercent(self)", str(DiffHitsPercent("self"))),
)

# --- Followers / casting ---
_sec("Followers e mod. casting")
_safe("Followers", lambda: _line("Followers", str(Followers())))
_safe("MaxFollowers", lambda: _line("MaxFollowers", str(MaxFollowers())))
_safe(
    "FasterCasting",
    lambda: _line("FasterCasting", str(FasterCasting())),
)
_safe(
    "FasterCastRecovery",
    lambda: _line("FasterCastRecovery", str(FasterCastRecovery())),
)
_safe(
    "SwingSpeedIncrease",
    lambda: _line("SwingSpeedIncrease", str(SwingSpeedIncrease())),
)

# --- Skill (lettura) ---
_sec("Skill (lettura)")
for sk in ("Magery", "Swordsmanship", "Meditation"):
    sv = _safe(sk, lambda s=sk: Skill(s))
    if sv is not None:
        _line("Skill", "%s = %s" % (sk, sv))
    sc = _safe(sk + "Cap", lambda s=sk: SkillCap(s))
    if sc is not None:
        _line("SkillCap", "%s cap = %s" % (sk, sc))

# --- Buff ---
_sec("Buff")
_safe(
    "BuffExists",
    lambda: _line("BuffExists(Bless)", str(BuffExists("Bless"))),
)
_safe(
    "BuffTime",
    lambda: _line("BuffTime(Bless) ms", str(BuffTime("Bless"))),
)
_safe(
    "SpecialMoveExists",
    lambda: _line("SpecialMoveExists(Armor Ignore)", str(SpecialMoveExists("Armor Ignore"))),
)

# --- Timer ---
_sec("Timer")
_safe("RemoveTimer", lambda: RemoveTimer("ca_probe") or True)
_safe("CreateTimer", lambda: CreateTimer("ca_probe"))
_safe("SetTimer", lambda: SetTimer("ca_probe", 0))
Pause(30)
_safe("Timer", lambda: _line("Timer(ca_probe)", str(Timer("ca_probe"))))
_safe(
    "TimerExists",
    lambda: _line("TimerExists(ca_probe)", str(TimerExists("ca_probe"))),
)

# --- Liste ---
_sec("Liste")
LIST_NAME = "ca_probe_list"
if _safe("ListExists", lambda: ListExists(LIST_NAME)):
    _safe("ClearList", lambda: ClearList(LIST_NAME))
_safe("CreateList", lambda: CreateList(LIST_NAME))
_safe("PushList", lambda: PushList(LIST_NAME, "test"))
_safe("InList", lambda: _line("InList", str(InList(LIST_NAME, "test"))))
_safe("List", lambda: _line("List", str(List(LIST_NAME))))
_safe("GetList", lambda: _line("GetList", str(GetList(LIST_NAME))))

# --- Journal (timeout breve, nessun ClearJournal) ---
_sec("Journal")
_safe(
    "WaitForJournal",
    lambda: _line(
        "WaitForJournal(falso, 250ms)",
        str(WaitForJournal("___no_match_ca___", 250)),
    ),
)

# --- Ping / stato macro ---
_sec("Ping e Playing")
_safe("Ping", lambda: _line("Ping", str(Ping())))
_safe("Playing", lambda: _line("Playing()", str(Playing())))
_safe(
    "WaitingForTarget",
    lambda: _line("WaitingForTarget()", str(WaitingForTarget())),
)

# --- Oggetti: conteggio oro nello zaino, ricerca tipo ---
_sec("CountType / FindType (zaino)")
GOLD_GRAPHIC = 0xEED
ct = _safe(
    "CountType",
    lambda: CountType(GOLD_GRAPHIC, "backpack", -1),
)
if ct is not None:
    _line("CountType(0xEED, backpack)", str(ct))

ft = _safe(
    "FindType",
    lambda: FindType(GOLD_GRAPHIC, -1, "backpack", -1),
)
if ft is not None:
    _line("FindType(oro)", str(ft))
    if FindAlias("found"):
        _line("found", "0x%X" % GetAlias("found"))

# --- Fine ---
Pause(120)
SysMessage("========== PROVA CLASSICASSIST: FINE ==========", 88)
