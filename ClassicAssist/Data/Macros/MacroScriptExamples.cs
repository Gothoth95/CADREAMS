#region License

// Copyright (C) 2025 Reetus
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

#endregion

namespace ClassicAssist.Data.Macros
{
    public sealed class MacroExampleItem
    {
        public string MenuHeader { get; set; }
        public string Code { get; set; }
    }

    /// <summary>
    ///     Snippet didattici per il menu "Esempi" nell'editor macro.
    /// </summary>
    public static class MacroScriptExamples
    {
        public static readonly MacroExampleItem[] All =
        {
            new MacroExampleItem
            {
                MenuHeader = "1. Messaggio in chat",
                Code =
                    "# Invia un messaggio nel gioco (funzione Msg importata da ClassicAssist)\r\nMsg( \"Ciao da ClassicAssist!\" )\r\n"
            },
            new MacroExampleItem
            {
                MenuHeader = "2. Pausa tra due azioni",
                Code =
                    "# Pause( millisecondi ) — aspetta senza bloccare il client come time.sleep globale\r\nMsg( \"Aspetto 1 secondo...\" )\r\nPause( 1000 )\r\nMsg( \"Fatto.\" )\r\n"
            },
            new MacroExampleItem
            {
                MenuHeader = "3. Ciclo for",
                Code =
                    "# Ripeti un blocco più volte\r\nfor i in range( 3 ):\r\n    Msg( \"Conteggio: \" + str( i ) )\r\n    Pause( 400 )\r\n"
            },
            new MacroExampleItem
            {
                MenuHeader = "4. Variabile e if",
                Code =
                    "# Uso base di variabili Python\r\nnome = \"Avatar\"\r\nif nome:\r\n    Msg( \"Benvenuto, \" + nome + \"!\" )\r\n"
            },
            new MacroExampleItem
            {
                MenuHeader = "5. Commenti e righe vuote",
                Code =
                    "# Le righe che iniziano con # sono commenti\r\n# Puoi lasciare righe vuote per leggibilità\r\n\r\nMsg( \"Script minimale OK\" )\r\n"
            }
        };
    }
}
