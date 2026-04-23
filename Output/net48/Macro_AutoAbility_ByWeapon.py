"""
Author: Effy

Macro ClassicAssist (background): in base all’arma equipaggiata mantiene accesa
la special primaria o secondaria. Lascia attiva la modalità silenziosa (SetQuietMode).

Impostazione minima:
- Modifica il dizionario WEAPON_ABILITY: chiave = serial dell’arma (int), valore = "primary" o "secondary".
- Avvia il macro in background; non importare questo file nel client.

Nota: ActiveAbility() è True/False (special accesa o no), non indica quale slot;
per evitare spam si tiene traccia dell’ultimo slot applicato.
"""


# serial arma -> "primary" | "secondary"
WEAPON_ABILITY = {
    0x4060624A: "secondary",
    0x404B3178: "primary",
}

POLL_MS = 120
SHOW_DEBUG = False


def _msg(testo, hue=946):
    if SHOW_DEBUG:
        SysMessage(testo, hue)


def _arma_equipaggiata():
    if FindLayer("OneHanded", "self"):
        return GetAlias("found")
    if FindLayer("TwoHanded", "self"):
        return GetAlias("found")
    return 0


def _accendi_slot(slot):
    try:
        SetAbility(slot, "on")
    except TypeError:
        SetAbility(slot)


def _forza_slot(slot):
    ClearAbility()
    Pause(25)
    _accendi_slot(slot)


def main():
    ultima_arma = None
    ultimo_slot = None

    SetQuietMode(True)
    _msg("AutoAbility avviato", 68)

    try:
        while True:
            seriale = _arma_equipaggiata()
            voluto = WEAPON_ABILITY.get(seriale, None)

            if seriale != ultima_arma:
                ultima_arma = seriale
                ultimo_slot = None

                if voluto:
                    _forza_slot(voluto)
                    ultimo_slot = voluto
                    _msg("Arma {0:#x} -> {1}".format(seriale, voluto), 68)
                else:
                    ClearAbility()
                    _msg("Arma non in lista -> special pulita", 53)

            elif voluto:
                if ActiveAbility() and ultimo_slot == voluto:
                    pass
                elif not ActiveAbility():
                    _accendi_slot(voluto)
                    ultimo_slot = voluto
                    _msg("Riattivato {0}".format(voluto), 68)

            Pause(POLL_MS)
    finally:
        SetQuietMode(True)
        _msg("AutoAbility fermato (quiet mode resta ON)", 33)


main()
