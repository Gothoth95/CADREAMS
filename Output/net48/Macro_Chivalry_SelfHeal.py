"""
Author: Effy

Cura rapida su te stesso: Close Wounds / Cleanse By Fire, Remove Curse se gialli,
Confidence se HP bassi. Salta tutto se sei a HP pieni.

Regola SOGLIA_CONFIDENCE e le pause in base al tuo ping / shard.
"""

SOGLIA_CONFIDENCE = 60
PAUSA_DOPO_CAST_MS = 550
PAUSA_CLEANSE_MS = 50
TIMEOUT_TARGET_MS = 2500


def _cast_su_self(incantesimo):
    """Lancia e bersaglia sé; prova firma Cast(nome, \"self\") se il client la supporta."""
    CancelTarget()
    try:
        Cast(incantesimo, "self")
    except TypeError:
        Cast(incantesimo)
        if WaitForTarget(TIMEOUT_TARGET_MS):
            Target("self")
    Pause(PAUSA_DOPO_CAST_MS)


def _cura_veleno_o_vita():
    if Poisoned("self"):
        _cast_su_self("Cleanse By Fire")
        Pause(PAUSA_CLEANSE_MS)
    else:
        _cast_su_self("Close Wounds")


Pause(10)
CancelTarget()

if Hits("self") >= MaxHits("self"):
    HeadMsg("*FULL HP*", "self")
else:
    _cura_veleno_o_vita()

    if YellowHits("self"):
        _cast_su_self("Remove Curse")

    if Hits("self") < SOGLIA_CONFIDENCE:
        _cast_su_self("Confidence")
        _cura_veleno_o_vita()
