"""
Author: Effy

Background: mantiene Counter Attack se c'è un enemy in range.
Non casta mentre sono attivi Evasion o Confidence; quando spariscono, riprova.

Impostazione: alias \"enemy\", ENEMY_RANGE, MANA_MINIMA, pause.
"""

ENEMY_RANGE = 10
LOOP_DELAY = 150
PAUSA_DOPO_CAST_MS = 900
MANA_MINIMA = 15

HeadMsg("Auto Counter Attack avviato", "self")


def nemico_in_range():
    if not FindAlias("enemy"):
        return False
    s = GetAlias("enemy")
    if not s or Dead(s):
        return False
    return InRange(s, ENEMY_RANGE)


while True:
    if Dead("self"):
        Pause(500)
    elif nemico_in_range():
        evasione = BuffExists("Evasion")
        confidenza = BuffExists("Confidence")
        counter = BuffExists("Counter Attack")

        if not evasione and not confidenza and not counter:
            if Mana("self") >= MANA_MINIMA:
                WarMode("on")
                Cast("Counter Attack")
                Pause(PAUSA_DOPO_CAST_MS)

    Pause(LOOP_DELAY)
