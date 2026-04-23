"""
Author: Effy

Macro ClassicAssist: rileva il disarm solo con BuffExists (Disarm / Disarmed ecc.),
nessun controllo sul journal. Quando il buff cade, riarma dalla lista.

Impostazione minima:
- WAKI e WEAPON_REEQUIP_LIST con i serial delle tue armi.
- Verifica i nomi in DISARM_BUFF_NAMES con BuffIcons / tooltip (devono coincidere con BuffExists).
- Percorso suono: adatta BEEP_WAV se usi PlaySound.
"""

WAKI = 0x4069268E

WEAPON_REEQUIP_LIST = [
    0x4069268E,
    0x402937DE,
]

# Nomi possibili del debuff disarm nel client; tieni solo quello che risponde a BuffExists in gioco.
DISARM_BUFF_NAMES = (
    "Disarm",
    "Disarmed",
    "Disarm (new)",
)

BEEP_WAV = r"C:\Orion Launcher\OA\beep.wav"

waiting_rearm = False

SysMessage("Check Disarm avviato", 68)


def _buff_disarm_attivo():
    for nome in DISARM_BUFF_NAMES:
        if BuffExists(nome):
            return True
    return False


while True:
    if Dead("self"):
        Pause(500)
        continue

    disarmato = _buff_disarm_attivo()

    if disarmato:
        if not waiting_rearm:
            waiting_rearm = True
            HeadMsg("DISARMATO", "self")
            try:
                PlaySound(BEEP_WAV, True)
            except TypeError:
                PlaySound(BEEP_WAV)
        Pause(100)
        continue

    if waiting_rearm:
        for arma in WEAPON_REEQUIP_LIST:
            EquipItem(arma, "TwoHanded")
            Pause(200)
            if FindLayer("TwoHanded", "self"):
                HeadMsg("ARMATO", "self")
                break
        waiting_rearm = False

    if not FindLayer("TwoHanded", "self"):
        EquipItem(WAKI, "TwoHanded")
        Pause(200)

    Pause(100)
