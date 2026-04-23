"""
Author: Effy

Lancia Clumsy su te stesso, poi esegue l'agent Dress (profilo con ascia / equip).

Impostazione minima:
- In ClassicAssist crea un profilo Dress con l'arma e i pezzi voluti.
- Imposta DRESS_NAME uguale al nome dell'entry (es. \"Dress-1\"), copiato dalla lista Dress.
- Regola le pause se il client è lento o la rete alta latenza.
"""

# Nome entry Dress (Agents → Dress), identico a quello in lista.
DRESS_NAME = "Dress-1"

PAUSA_DOPO_CAST_MS = 600
TIMEOUT_DRESS_MS = 20000
PASSO_POLL_MS = 100

SysMessage("Clumsy + Dress avviato", 68)

Cast("Clumsy")
if WaitForTarget(4000):
    Target("self")
Pause(PAUSA_DOPO_CAST_MS)

Dress(DRESS_NAME)

attesa = TIMEOUT_DRESS_MS
while Dressing() and attesa > 0:
    Pause(PASSO_POLL_MS)
    attesa -= PASSO_POLL_MS

if Dressing():
    StopDress()
    SysMessage("Dress: timeout, StopDress", 33)
else:
    HeadMsg("Dress OK", "self")
