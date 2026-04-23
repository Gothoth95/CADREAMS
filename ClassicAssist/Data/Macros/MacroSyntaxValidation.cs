#region License

// Copyright (C) 2025 Reetus
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

#endregion

using System;
using System.Collections.Generic;
using System.IO;
using Assistant;
using ClassicAssist.Shared.Resources;
using IronPython.Hosting;
using IronPython.Runtime.Exceptions;
using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;

namespace ClassicAssist.Data.Macros
{
    /// <summary>
    ///     Compila il sorgente IronPython senza eseguirlo (solo errori di sintassi / parser).
    /// </summary>
    public static class MacroSyntaxValidation
    {
        public static bool TryValidate( string source, out string errorMessage )
        {
            errorMessage = null;

            if ( string.IsNullOrWhiteSpace( source ) )
            {
                return true;
            }

            try
            {
                ScriptEngine engine = Python.CreateEngine();
                string modulePath = Path.Combine( Engine.StartupPath ?? Environment.CurrentDirectory, "Modules" );
                List<string> paths = new List<string>( engine.GetSearchPaths() );

                if ( !paths.Contains( modulePath ) )
                {
                    paths.Add( modulePath );
                }

                string startup = Engine.StartupPath;

                if ( !string.IsNullOrEmpty( startup ) && !paths.Contains( startup ) )
                {
                    paths.Add( startup );
                }

                engine.SetSearchPaths( paths );

                ScriptSource scriptSource = engine.CreateScriptSourceFromString( source, SourceCodeKind.Statements );
                scriptSource.Compile();
                return true;
            }
            catch ( SyntaxErrorException ex )
            {
                errorMessage = $"{Strings.Line_Number} {ex.RawSpan.Start.Line}: {ex.Message}";
                return false;
            }
            catch ( Exception ex )
            {
                errorMessage = ex.Message;
                return false;
            }
        }
    }
}
