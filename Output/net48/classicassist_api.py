# -*- coding: utf-8 -*-
"""
Riferimento ClassicAssist (ClassicUO) — firme ed esempi per macro Python.

In-game i comandi sono funzioni GLOBALI fornite dall'host IronPython: NON fare
``import classicassist_api`` nel client. Usa questo file in Cursor/VS Code per
autocomplete e come cheat sheet; copia gli esempi nel macro.

Indice ufficiale: https://github.com/Reetus/ClassicAssist/wiki/Macro-Commands

**Cast in corso / blocco movimento:** nel wiki non risulta un comando pubblico tipo
``IsCasting()`` / ``Casting()``. Indicatore parziale: ``WaitingForTarget()`` (fase target
dopo un cast). Per ridurre input da hotkey durante un macro: ``Hotkeys("off")`` e poi
``Hotkeys("on")`` (Main#Hotkeys); non è un freeze garantito del personaggio (vedi sezione
in fondo al file e ``set_assistant_hotkeys_enabled``).

Alias predefiniti (non sono funzioni): dopo il login ClassicAssist imposta gli
alias ``"self"``, ``"backpack"`` e ``"bank"`` sui serial corrispondenti. Usali
come stringhe dove serve un SerialOrAlias, oppure ``GetAlias("self")`` ecc.
"""

from __future__ import print_function

# ---------------------------------------------------------------------------
# Main
# https://github.com/Reetus/ClassicAssist/wiki/Main
# ---------------------------------------------------------------------------


def Pause(ms):
    """
    Pausa l'esecuzione del macro per ``ms`` millisecondi.

    Esempio::
        Pause(500)
    """
    pass


def SysMessage(msg, hue=-1):
    """
    Messaggio di sistema (chat di sistema).

    Esempio::
        SysMessage("OK", 68)
    """
    pass


def MessageBox(msg, title=""):
    """
    Finestra di dialogo con messaggio.

    Esempio::
        MessageBox("Fatto", "Macro")
    """
    pass


def WarMode(on=None):
    """
    Legge o imposta la modalità guerra.
    ``on`` True/False oppure omesso per toggle secondo implementazione.

    Esempio::
        WarMode(True)
    """
    pass


def Resync():
    """Forza un resync con il server."""
    pass


def Playing():
    """Restituisce True se un macro è in esecuzione (utile da altri macro)."""
    pass


def Hotkeys(onoff=None):
    """
    Abilita/disabilita le **hotkey ClassicAssist** (non solo movimento).

    Parametro opzionale ``onoff``: ``"on"`` o ``"off"`` (vedi Main#Hotkeys).

    Esempio::
        Hotkeys("off")  # disattiva tutte le hotkey dell'assistant
        Hotkeys("on")   # riattiva
    """
    pass


def SetQuietMode(quiet):
    """Riduce messaggi/feedback se supportato."""
    pass


# ---------------------------------------------------------------------------
# Entity
# https://github.com/Reetus/ClassicAssist/wiki/Entity
# ---------------------------------------------------------------------------


def BuffExists(name):
    """
    True se il buff è attivo. ``name`` deve coincidere con BuffIcons.json.

    Esempio::
        if BuffExists("Bless"):
            SysMessage("Bless ON")
    """
    pass


def BuffTime(name):
    """
    Millisecondi rimanenti per il buff, o 0 se assente/scaduto (vedi wiki).

    Esempio::
        t = BuffTime("Bless")
        SysMessage(str(t))
    """
    pass


def Distance(serial):
    """Distanza in tile dal giocatore all'entità ``serial``."""
    pass


def Hits(serial=None):
    """HP correnti (target/self secondo wiki)."""
    pass


def MaxHits(serial=None):
    pass


def Mana(serial=None):
    pass


def MaxMana(serial=None):
    pass


def Stam(serial=None):
    pass


def MaxStam(serial=None):
    pass


def Dead(serial=None):
    pass


def Poisoned(serial=None):
    pass


def Hidden(serial=None):
    pass


def Mounted(serial=None):
    pass


def Weight(serial=None):
    pass


def MaxWeight(serial=None):
    pass


def Gold(serial=None):
    pass


def Name(serial=None):
    pass


def Graphic(serial=None):
    pass


def Hue(serial=None):
    pass


def X(serial=None):
    pass


def Y(serial=None):
    pass


def Z(serial=None):
    pass


def Map(serial=None):
    pass


def FindType(graphic, hue=-1, container=None, name=None):
    """
    Cerca un tipo di oggetto nello zaino/contenitore.

    Esempio::
        FindType(0xf0f, -1, "backpack")
        # Poi l'alias macro "found" punta all'oggetto trovato (wiki Entity).
    """
    pass


def FindObject(serial):
    pass


def CountType(graphic, hue=-1, source=None):
    pass


def MoveItem(item_serial, amount, dest, x=0, y=0):
    """Sposta oggetti tra contenitori."""
    pass


# ---------------------------------------------------------------------------
# Target
# https://github.com/Reetus/ClassicAssist/wiki/Target
# ---------------------------------------------------------------------------


def Target(obj, *args):
    """
    Invia il cursore target a serial o alias (``"self"``, ``"last"``, …).
    Parametri aggiuntivi opzionali: vedi wiki Target.

    Esempio dopo ``Cast``::
        WaitForTarget(5000)
        Target("self")

    Esempio con serial::
        Target(0x4012ABCD)
    """
    pass


def WaitForTarget(ms):
    """Attende fino a ``ms`` ms un cursore target."""
    pass


def CancelTarget():
    pass


def TargetExists():
    pass


def SetLastTarget(serial):
    pass


def TargetType(graphic, hue, qty, backpack):
    """Target per tipo."""
    pass


def TargetGround(graphic, hue):
    pass


def TargetTileRelative(serial, xoffs, yoffs):
    pass


# ---------------------------------------------------------------------------
# Spells
# https://github.com/Reetus/ClassicAssist/wiki/Spells
# ---------------------------------------------------------------------------


def Cast(name):
    """
    Lancia incantesimo per nome (stringa).

    Esempio::
        Cast("Bless")
        WaitForTarget(3000)
        Target("self")
    """
    pass


def InterruptSpell():
    """
    Tenta di interrompere il cast sollevando un oggetto (wiki Spells).

    Per sapere se «si sta castando»: il wiki Macro-Commands non documenta un comando
    dedicato; vedi ``WaitingForTarget()`` e la sezione *Casting e blocco input* in fondo.
    """
    pass


# ---------------------------------------------------------------------------
# Skills
# https://github.com/Reetus/ClassicAssist/wiki/Skills
# ---------------------------------------------------------------------------


def UseSkill(name):
    """
    Esempio::
        UseSkill("Hiding")
    """
    pass


def Skill(name):
    """Valore skill numerico."""
    pass


def SkillCap(name):
    pass


def SkillState(name):
    pass


def SetSkill(skillname, lockstate):
    """Lock skill up/down/locked se disponibile."""
    pass


# ---------------------------------------------------------------------------
# Movement
# https://github.com/Reetus/ClassicAssist/wiki/Movement
# ---------------------------------------------------------------------------


def Pathfind(x, y, z=None):
    pass


def Walk(direction):
    pass


def Run(direction):
    pass


def Turn(direction):
    pass


def SetForceWalk(on):
    pass


def Follow(serial):
    pass


# ---------------------------------------------------------------------------
# Journal
# https://github.com/Reetus/ClassicAssist/wiki/Journal
# ---------------------------------------------------------------------------


def ClearJournal():
    pass


def InJournal(text):
    """True se ``text`` compare nel journal (match parziale secondo wiki)."""
    pass


def WaitForJournal(text, timeout):
    """Attende una riga di journal per ``timeout`` ms."""
    pass


# ---------------------------------------------------------------------------
# Gumps
# https://github.com/Reetus/ClassicAssist/wiki/Gumps
# ---------------------------------------------------------------------------


def WaitForGump(gumpid, timeout):
    pass


def GumpExists(gumpid):
    pass


def ReplyGump(gumpid, buttonid, *switchids):
    pass


def CloseGump(gumpid):
    pass


def InGump(text):
    pass


# ---------------------------------------------------------------------------
# Aliases
# https://github.com/Reetus/ClassicAssist/wiki/Aliases
# ---------------------------------------------------------------------------


def SetAlias(name, serial):
    pass


def GetAlias(name):
    """
    Restituisce il serial (int) per un alias.

    Alias predefiniti dopo il login: ``"self"``, ``"backpack"``, ``"bank"``.

    Esempio::
        if GetAlias("backpack"):
            UseObject(GetAlias("backpack"))
    """
    pass


def UnsetAlias(name):
    pass


def PromptAlias(name):
    """Chiede al player di selezionare un target e salva in alias."""
    pass


# ---------------------------------------------------------------------------
# Timers
# https://github.com/Reetus/ClassicAssist/wiki/Timers
# ---------------------------------------------------------------------------


def CreateTimer(name):
    pass


def SetTimer(name, ms):
    pass


def Timer(name):
    """Millisecondi trascorsi dall'ultimo SetTimer/reset."""
    pass


def TimerExists(name):
    pass


def RemoveTimer(name):
    pass


# ---------------------------------------------------------------------------
# Actions / Items
# https://github.com/Reetus/ClassicAssist/wiki/Actions
# ---------------------------------------------------------------------------


def UseObject(serial):
    pass


def UseType(graphic, hue=-1, container=None):
    pass


def EquipItem(serial, layer):
    pass


def BandageSelf():
    pass


def Attack(serial):
    pass


def ClickObject(serial):
    pass


# ---------------------------------------------------------------------------
# Agents (estratti)
# https://github.com/Reetus/ClassicAssist/wiki/Agents
# ---------------------------------------------------------------------------


def Organizer(index):
    pass


def Autoloot(on):
    pass


def Dress(name=None):
    """
    Esegue l'agent Dress. ``name``: nome entry (opzionale), es. ``Dress(\"Dress-1\")``.
    """
    pass


# ---------------------------------------------------------------------------
# Messaggi
# https://github.com/Reetus/ClassicAssist/wiki/Messages
# ---------------------------------------------------------------------------


def Msg(text):
    """Messaggio normale."""
    pass


def HeadMsg(text, serial):
    pass


def PartyMsg(text):
    pass


# ---------------------------------------------------------------------------
# Liste
# https://github.com/Reetus/ClassicAssist/wiki/Lists
# ---------------------------------------------------------------------------


def CreateList(name):
    pass


def List(name):
    pass


def PushList(name, value):
    pass


def InList(name, value):
    pass


# ---------------------------------------------------------------------------
# Macro
# https://github.com/Reetus/ClassicAssist/wiki/Macros
# ---------------------------------------------------------------------------


def Stop():
    """Ferma il macro corrente."""
    pass


def PlayMacro(name):
    pass


def IsRunning(name):
    """True se il macro di nome ``name`` è in esecuzione."""
    pass


def PlayCUOMacro(name):
    """Esegue un macro interno ClassicUO per nome."""
    pass


def Replay(*args):
    """Rilancia il macro corrente (opz. argomenti)."""
    pass


def StopAll():
    """Ferma tutti i macro in esecuzione."""
    pass


# ---------------------------------------------------------------------------
# Main (aggiuntivi)
# https://github.com/Reetus/ClassicAssist/wiki/Main
# ---------------------------------------------------------------------------


def BringClientWindowToFront():
    pass


def DisplayQuestPointer(x, y, z, map_id):
    pass


def Info():
    pass


def InvokeVirtue(name):
    """
    Invoca una virtù per nome (enum ``Virtues`` lato client, es. ``\"Honor\"``).
    Non esiste un comando ``Virtues()`` in macro — solo ``InvokeVirtue``.
    """
    pass


def Logout():
    pass


def OpenECV():
    pass


def PlaySound(name):
    pass


def Quit():
    pass


def SetAutologin(on):
    pass


def Snapshot():
    pass


# ---------------------------------------------------------------------------
# Abilities
# https://github.com/Reetus/ClassicAssist/wiki/Abilities
# ---------------------------------------------------------------------------


def ActiveAbility():
    """
    **Boolean:** True se è attiva la primaria **oppure** la secondaria (non indica quale).

    Esempio (wiki)::

        if not ActiveAbility():
            SetAbility("primary", "on")
    """
    pass


def ClearAbility():
    pass


def Fly():
    pass


def Flying():
    pass


def Land():
    pass


def SetAbility(name, onoff=None):
    """
    ``name``: ``\"primary\"``, ``\"secondary\"``, ``\"stun\"`` o ``\"disarm\"``.
    ``onoff`` (opzionale): ``\"on\"`` o ``\"off\"`` — es. ``SetAbility(\"primary\", \"on\")``.
    """
    pass


# ---------------------------------------------------------------------------
# Actions (aggiuntivi)
# https://github.com/Reetus/ClassicAssist/wiki/Actions
# ---------------------------------------------------------------------------


def ClearHands(which):
    pass


def ClearUseOnce():
    pass


def Contents(serial):
    pass


def ContextMenu(serial, entry):
    """``entry`` indice o nome voce menu (wiki)."""
    pass


def EquipLastWeapon():
    pass


def EquipType(graphic, layer):
    pass


def Feed(serial, food):
    pass


def FindLayer(layer, owner="self"):
    """
    True se c'è un item nel layer; aggiorna l'alias ``found`` con quell'item.

    ``layer``: stringa enum (es. ``\"OneHanded\"``, ``\"TwoHanded\"``, ``\"Helm\"`` …).
    ``owner``: serial, hex o alias del mobile (default ``\"self\"``).

    Wiki: https://github.com/Reetus/ClassicAssist/wiki/Actions (FindLayer).
    """
    pass


def Ping():
    """Ping approssimativo verso il server (ms, -1 se errore)."""
    pass


def Rename(serial, new_name):
    pass


def ShowNames(on):
    pass


def ToggleMounted():
    pass


def UseOnce(serial):
    pass


def UseTargetedItem(item, target):
    pass


def WaitForContents(serial, timeout):
    pass


def WaitForContext(serial, entry, timeout):
    pass


# ---------------------------------------------------------------------------
# Agents
# https://github.com/Reetus/ClassicAssist/wiki/Agents
# ---------------------------------------------------------------------------


def Autolooting():
    pass


def ClearTrapPouch():
    pass


def Counter(*args):
    pass


def DressConfig(*args):
    pass


def Dressing():
    pass


def Organizing():
    pass


def SetAutoloot(on):
    pass


def SetAutolootContainer(serial):
    pass


def SetOrganizerContainers(*args):
    pass


def SetScavenger(*args):
    pass


def SetTrapPouch(serial):
    pass


def SetVendorBuyAutoBuy(*args):
    pass


def StopDress():
    pass


def StopOrganizer():
    pass


def Undress():
    pass


def UseTrapPouch():
    pass


# ---------------------------------------------------------------------------
# Aliases (aggiuntivi)
# ---------------------------------------------------------------------------


def FindAlias(name):
    pass


def GetPlayerAlias(name):
    pass


def PromptMacroAlias(name):
    pass


def PromptPlayerAlias(name):
    pass


def SetMacroAlias(name, serial):
    pass


def SetPlayerAlias(name, serial):
    pass


def UnsetPlayerAlias(name):
    pass


# ---------------------------------------------------------------------------
# Entity (aggiuntivi)
# ---------------------------------------------------------------------------


def AddFriend(serial=None):
    pass


def Ally(serial):
    pass


def AutoColorPick(hue):
    pass


def ClearIgnoreList():
    pass


def ClearObjectQueue():
    pass


def CountTypeGround(graphic, hue=-1, tile_range=-1):
    """``tile_range``: in CA spesso ``range`` (tile). Vedi wiki Entity."""
    pass


def Criminal(serial):
    pass


def Dex():
    pass


def DiffHits(serial=None):
    pass


def DiffHitsPercent(serial=None):
    pass


def DiffWeight():
    pass


def Direction(serial=None):
    pass


def DirectionTo(serial):
    pass


def FindWand(name):
    pass


def Followers():
    pass


def Gray(serial):
    pass


def IgnoreObject(serial):
    pass


def InFriendList(serial):
    pass


def InIgnoreList(serial):
    pass


def Innocent(serial):
    pass


def InParty(serial):
    pass


def InRange(serial, distance):
    pass


def Int():
    pass


def Invulnerable(serial):
    pass


def Luck():
    pass


def MaxFollowers():
    pass


def MoveItemOffset(item, xoff, yoff, zoff, amount=-1):
    pass


def MoveItemXYZ(item, x, y, z, amount=-1):
    pass


def MoveType(id, source, dest, x=-1, y=-1, z=0, hue=-1, amount=-1):
    pass


def MoveTypeOffset(id, find_loc, xoff, yoff, zoff, amount=-1, hue=-1, range=-1):
    pass


def MoveTypeXYZ(id, find_loc, x, y, z, amount=-1, hue=-1, range=-1):
    pass


def Murderer(serial):
    pass


def Paralyzed(serial):
    pass


def Rehue(serial, hue):
    pass


def RemoveFriend(serial=None):
    pass


def SpecialMoveExists(name):
    pass


def Str():
    pass


def SwingSpeedIncrease():
    pass


def TithingPoints():
    pass


def UseLayer(layer, serial=None):
    pass


def War(serial):
    pass


def YellowHits(serial):
    pass


def FasterCasting():
    pass


def FasterCastRecovery():
    pass


def HideEntity(serial):
    """Nasconde entità lato client (Main/Entity a seconda versione)."""
    pass


# ---------------------------------------------------------------------------
# Gumps (aggiuntivi)
# ---------------------------------------------------------------------------


def ConfirmPrompt(*args):
    pass


def ItemArrayGump(*args):
    pass


def MessagePrompt(*args):
    pass


def OpenGuildGump():
    pass


def OpenHelpGump():
    pass


def OpenQuestsGump():
    pass


def OpenVirtueGump():
    pass


def SelectionPrompt(*args):
    pass


# ---------------------------------------------------------------------------
# Liste (aggiuntivi)
# ---------------------------------------------------------------------------


def ClearList(name):
    pass


def GetList(name):
    pass


def ListExists(name):
    pass


def PopList(name):
    pass


def RemoveList(name):
    pass


# ---------------------------------------------------------------------------
# Menus
# https://github.com/Reetus/ClassicAssist/wiki/Menus
# ---------------------------------------------------------------------------


def CloseMenu():
    pass


def InMenu(text):
    pass


def MenuExists(menuid):
    pass


def ReplyMenu(menuid, index):
    pass


def WaitForMenu(menuid, timeout):
    pass


# ---------------------------------------------------------------------------
# Messages (aggiuntivi)
# ---------------------------------------------------------------------------


def AllyMsg(text):
    pass


def CancelPrompt():
    pass


def ChatMsg(text):
    pass


def EmoteMsg(text):
    pass


def GetText(serial):
    pass


def GuildMsg(text):
    pass


def PromptMsg(*args):
    pass


def WaitForPrompt(timeout):
    pass


def WhisperMsg(text):
    pass


def YellMsg(text):
    pass


# ---------------------------------------------------------------------------
# Movement (aggiuntivi)
# ---------------------------------------------------------------------------


def Following():
    pass


def Pathfinding():
    pass


def ToggleForceWalk():
    pass


# ---------------------------------------------------------------------------
# Map / World
# ---------------------------------------------------------------------------


def AddMapMarker(*args):
    pass


def ClearMapMarkers():
    pass


def RemoveMapMarker(*args):
    pass


# ---------------------------------------------------------------------------
# Notoriety
# ---------------------------------------------------------------------------


def Enemy(serial):
    pass


# ---------------------------------------------------------------------------
# Properties
# https://github.com/Reetus/ClassicAssist/wiki/Properties
# ---------------------------------------------------------------------------
#
# **Durability (equip / item)** — pattern per stampare attuale / massimo da tooltip:
#
# Nel client la riga è di solito una sola, es. ``Durability 252 / 255`` (attuale, slash, massimo).
#
# 1. ``FindLayer("OneHanded", "self")`` (o altro layer) → item in alias ``found``.
# 2. ``WaitForProperties("found", 2500)`` così le righe proprietà arrivano dal server.
# 3. ``Property("found", "Durability")`` — match per **sottostringa** sul testo tooltip
#    (stessa riga che vedi a video; aggiungi ``\"Durabilità\"`` se il client è in IT).
# 4. ``PropertyValue("found", "Durability", 0)`` e ``(..., 1)`` — in genere **attuale** e **massimo**
#    (come i due numeri attorno allo ``/`` nel tooltip); se lo shard li mappa diversamente, prova in gioco.
#
# Esempio minimale in macro::
#
#     if FindLayer("OneHanded", "self"):
#         WaitForProperties("found", 2500)
#         if Property("found", "Durability"):
#             SysMessage(
#                 "Dur %s / %s" % (
#                     PropertyValue("found", "Durability", 0),
#                     PropertyValue("found", "Durability", 1),
#                 ),
#                 946,
#             )
#
# Esempio con più etichette (client IT / EN)::
#
#     _labels = ("Durability", "durability", "Durabilità", "durabilità")
#     if FindLayer("OneHanded", "self"):
#         WaitForProperties("found", 2500)
#         for _lbl in _labels:
#             if Property("found", _lbl):
#                 SysMessage(
#                     "%s / %s"
#                     % (
#                         PropertyValue("found", _lbl, 0),
#                         PropertyValue("found", _lbl, 1),
#                     ),
#                     946,
#                 )
#                 break
#
def Property(serial, name):
    """
    True se ``name`` compare come sottostringa nelle proprietà (tooltip) dell'oggetto.

    ``serial``: serial, hex o alias (es. ``\"found\"`` dopo ``FindLayer``).
    """
    pass


def PropertyValue(serial, name, argument=0):
    """
    Valore numerico/stringa da una riga proprietà; ``argument`` seleziona il componente
    quando la riga ha più valori (es. Durability 120 / 255 → indici 0 e 1).

    Esempi::

        v = PropertyValue("self", "Strength", 0)
        cur = PropertyValue("found", "Durability", 0)
        mx = PropertyValue("found", "Durability", 1)
    """
    pass


def WaitForProperties(serial, timeout):
    """
    Invia la query proprietà al server e attende la risposta (pacchetto filtrato su ``serial``).

    In ClassicAssist ritorna **bool** (True se la risposta è arrivata entro ``timeout`` ms).
    Se ritorna False, ``Property`` / ``PropertyValue`` possono ancora vedere OPL vuote: ripeti
    la chiamata o aumenta ``timeout`` prima di leggere Durability.

    Chiamalo prima di ``Property`` / ``PropertyValue`` su item appena referenziati.
    """
    pass


# ---------------------------------------------------------------------------
# Region
# ---------------------------------------------------------------------------


def InRegion(region_name, serial=None):
    pass


# ---------------------------------------------------------------------------
# Skills (aggiuntivi)
# ---------------------------------------------------------------------------


def SetStatus(*args):
    pass


def SkillDelta(name):
    pass


def UseLastSkill():
    pass


# ---------------------------------------------------------------------------
# Target (aggiuntivi)
# ---------------------------------------------------------------------------


def ClearTargetQueue():
    pass


def GetEnemy(*args):
    pass


def GetFriend(*args):
    pass


def GetFriendListOnly(*args):
    pass


def SetEnemy(serial):
    pass


def SetFriend(serial):
    pass


def TargetByResource(tool, resource_type):
    pass


def TargetTileOffset(xoff, yoff, zoff):
    pass


def TargetTileOffsetResource(*args):
    pass


def TargetXYZ(x, y, z):
    pass


def WaitForTargetOrFizzle(timeout):
    pass


def WaitingForTarget():
    """
    True quando il core è in attesa di un target dal server (wiki Target).

    Può essere vero subito dopo ``Cast`` mentre è atteso il cursore target; non copre
    l'intera animazione di lancio della magia.
    """
    pass


# ---------------------------------------------------------------------------
# Timers (aggiuntivi)
# ---------------------------------------------------------------------------


def TimerMsg(*args):
    pass


# ---------------------------------------------------------------------------
# Trade
# ---------------------------------------------------------------------------


def TradeAccept():
    pass


def TradeClose():
    pass


def TradeCurrency(*args):
    pass


def TradeReject():
    pass


def WaitForTradeWindow(timeout):
    pass


# ---------------------------------------------------------------------------
# Wand
# ---------------------------------------------------------------------------


def EquipWand(name):
    pass


# ---------------------------------------------------------------------------
# Casting e blocco input (helper)
# ---------------------------------------------------------------------------
#
# - **IsCasting:** non elencato nell'indice Macro-Commands; non usare stub non documentati.
# - **WaitingForTarget():** proxy parziale (solo fase «attendo cursore target»).
# - **Hotkeys("off"):** disattiva le hotkey dell'assistant; ripristino ``Hotkeys("on")``.
#   Il movimento da tasti può ancora essere gestito dal client; non è un lock assoluto.
#


def set_assistant_hotkeys_enabled(enabled):
    """
    ``enabled`` True → ``Hotkeys("on")``, False → ``Hotkeys("off")``.

    Utile con un flag nel macro, es.::

        LOCK = True
        if LOCK:
            set_assistant_hotkeys_enabled(False)
        try:
            Cast("Fireball")
            WaitForTarget(3000)
            Target("last")
        finally:
            if LOCK:
                set_assistant_hotkeys_enabled(True)
    """
    if enabled:
        Hotkeys("on")
    else:
        Hotkeys("off")


# ---------------------------------------------------------------------------
# Indice: altri nomi e overload → wiki Macro-Commands
# ---------------------------------------------------------------------------
# Comandi aggiuntivi rari o varianti di firma: sempre
# https://github.com/Reetus/ClassicAssist/wiki/Macro-Commands
