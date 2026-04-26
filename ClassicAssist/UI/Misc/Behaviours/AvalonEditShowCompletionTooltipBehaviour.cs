#region License

// Copyright (C) 2025 Reetus
// 
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using ClassicAssist.Data.Macros;
using ICSharpCode.AvalonEdit;
using ICSharpCode.AvalonEdit.CodeCompletion;
using ICSharpCode.AvalonEdit.Document;
using IronPython.Runtime;
using Microsoft.Scripting.Utils;
using Microsoft.Xaml.Behaviors;

namespace ClassicAssist.UI.Misc.Behaviours
{
    public class AvalonEditShowCompletionTooltipBehaviour : Behavior<TextEditor>
    {
        public static readonly DependencyProperty FrameVariablesProperty = DependencyProperty.Register( nameof( FrameVariables ), typeof( Dictionary<string, object> ),
            typeof( AvalonEditShowCompletionTooltipBehaviour ), new PropertyMetadata( default( Dictionary<string, object> ) ) );

        public static readonly DependencyProperty IsPausedProperty =
            DependencyProperty.Register( nameof( IsPaused ), typeof( bool ), typeof( AvalonEditShowCompletionTooltipBehaviour ), new PropertyMetadata( false ) );

        private static readonly object SharedCompletionDataLock = new object();
        private static List<PythonCompletionData> _sharedCompletionData;

        private readonly ToolTip _toolTip = new ToolTip();
        private CompletionWindow _completionWindow;
        private TextEditor _textEditor;

        public Dictionary<string, object> FrameVariables
        {
            get => (Dictionary<string, object>) GetValue( FrameVariablesProperty );
            set => SetValue( FrameVariablesProperty, value );
        }

        public bool IsPaused
        {
            get => (bool) GetValue( IsPausedProperty );
            set => SetValue( IsPausedProperty, value );
        }

        private static bool IsWordChar( char c )
        {
            return char.IsLetterOrDigit( c ) || c == '_';
        }

        private static List<PythonCompletionData> GetSharedCompletionData()
        {
            if ( _sharedCompletionData != null )
            {
                return _sharedCompletionData;
            }

            lock ( SharedCompletionDataLock )
            {
                if ( _sharedCompletionData != null )
                {
                    return _sharedCompletionData;
                }

                var list = new List<PythonCompletionData>();

                IEnumerable<Type> namespaces = Assembly.GetExecutingAssembly().GetTypes().Where( t =>
                    t.Namespace != null && t.IsPublic && t.IsClass && t.Namespace.EndsWith( "Macros.Commands" ) );

                foreach ( Type type in namespaces )
                {
                    MethodInfo[] methods = type.GetMethods( BindingFlags.Public | BindingFlags.Static );

                    foreach ( MethodInfo methodInfo in methods )
                    {
                        CommandsDisplayAttribute attr = methodInfo.GetCustomAttribute<CommandsDisplayAttribute>();

                        if ( attr == null )
                        {
                            continue;
                        }

                        string fullName = $"{methodInfo.Name}(";
                        bool first = true;

                        foreach ( ParameterInfo parameterInfo in methodInfo.GetParameters() )
                        {
                            if ( first )
                            {
                                first = false;
                            }
                            else
                            {
                                fullName += ", ";
                            }

                            bool optional = parameterInfo.RawDefaultValue == null || parameterInfo.RawDefaultValue.GetType() != typeof( DBNull );

                            fullName += $"{( optional ? "[" : "" )}{parameterInfo.ParameterType.Name} {parameterInfo.Name}{( optional ? "]" : "" )}";
                        }

                        fullName += $"):{methodInfo.ReturnType.Name}";

                        list.Add( new PythonCompletionData( methodInfo.Name, fullName, attr.Description, attr.InsertText ) );
                    }
                }

                _sharedCompletionData = list.Distinct( new CompletionSignatureEqualityComparer() ).ToList();
                return _sharedCompletionData;
            }
        }

        protected override void OnAttached()
        {
            _textEditor = AssociatedObject;

            _textEditor.TextArea.TextEntered += OnTextEntered;
            _textEditor.MouseHover += OnMouseHover;
            _textEditor.MouseHoverStopped += OnMouseHoverStopped;
        }

        protected override void OnDetaching()
        {
            if ( _textEditor != null )
            {
                _textEditor.TextArea.TextEntered -= OnTextEntered;
                _textEditor.MouseHover -= OnMouseHover;
                _textEditor.MouseHoverStopped -= OnMouseHoverStopped;
            }

            _completionWindow?.Close();
            _completionWindow = null;
            base.OnDetaching();
        }

        private void ApplyCompletionWindowChrome( CompletionWindow window )
        {
            if ( window == null || _textEditor == null )
            {
                return;
            }

            // CompletionWindow is a separate top-level window: it does not inherit MainWindow.Resources,
            // so DynamicResource in styles would not resolve and the popup stays SystemColors (white) while
            // text uses theme foreground (invisible). Merge theme dictionaries onto the popup first.
            string asmName = Assembly.GetExecutingAssembly().GetName().Name;
            var themeUri = new Uri( $"pack://application:,,,/{asmName};component/Resources/DarkTheme.xaml", UriKind.Absolute );
            window.Resources.MergedDictionaries.Add( new ResourceDictionary { Source = themeUri } );

            window.SetResourceReference( Control.BackgroundProperty, "ThemeInnerControlBackgroundBrush" );
            window.SetResourceReference( Control.BorderBrushProperty, "ThemeBorderBrush" );

            if ( window.TryFindResource( typeof( CompletionWindow ) ) is Style style )
            {
                window.Style = style;
            }

            // AvalonEdit creates a ToolTip in code (description pane). It does not inherit CompletionWindow
            // resources when opened, so it stays system-themed (white + gray text). Theme it after load.
            window.Loaded -= CompletionWindow_Loaded;
            window.Loaded += CompletionWindow_Loaded;
        }

        private void CompletionWindow_Loaded( object sender, RoutedEventArgs e )
        {
            CompletionWindow w = sender as CompletionWindow;
            if ( w == null )
            {
                return;
            }

            w.Loaded -= CompletionWindow_Loaded;

            // CompletionList is a separate logical tree: theme ListBox styles may bind Foreground to resources that do not resolve on this window.
            SolidColorBrush itemFg = new SolidColorBrush( Color.FromRgb( 0xF1, 0xF5, 0xF9 ) );
            w.CompletionList.Foreground = itemFg;
            w.CompletionList.ApplyTemplate();
            if ( w.CompletionList.ListBox != null )
            {
                w.CompletionList.ListBox.Foreground = itemFg;
            }

            FieldInfo toolTipField = typeof( CompletionWindow ).GetField( "toolTip", BindingFlags.Instance | BindingFlags.NonPublic );
            ToolTip tip = toolTipField?.GetValue( w ) as ToolTip;
            if ( tip == null )
            {
                return;
            }

            foreach ( ResourceDictionary dict in w.Resources.MergedDictionaries )
            {
                tip.Resources.MergedDictionaries.Add( dict );
            }

            if ( w.TryFindResource( typeof( ToolTip ) ) is Style tooltipStyle )
            {
                tip.Style = tooltipStyle;
            }
            else
            {
                tip.SetResourceReference( Control.BackgroundProperty, "ThemeBackgroundBrush" );
                tip.SetResourceReference( TextElement.ForegroundProperty, "ForegroundColor1Brush" );
            }
        }

        private void OnMouseHoverStopped( object sender, MouseEventArgs e )
        {
            _toolTip.IsOpen = false;
        }

        private void OnMouseHover( object sender, MouseEventArgs e )
        {
            //https://stackoverflow.com/questions/51711692/how-to-fire-an-event-when-mouse-hover-over-a-specific-text-in-avalonedit
            TextViewPosition? pos = _textEditor.GetPositionFromPoint( e.GetPosition( _textEditor ) );

            if ( !pos.HasValue )
            {
                return;
            }

            DocumentLine line = _textEditor.TextArea.Document.GetLineByNumber( pos.Value.Line );

            if ( line == null )
            {
                return;
            }

            try
            {
                string fullLine = _textEditor.Document.GetText( line.Offset, line.Length );

                int startPosition = 0;
                int endPosition = fullLine.Length;

                for ( int i = pos.Value.Column; i > -1; i-- )
                {
                    if ( IsWordChar( fullLine[i] ) )
                    {
                        continue;
                    }

                    startPosition = i + 1;
                    break;
                }

                for ( int i = pos.Value.Column; i < fullLine.Length; i++ )
                {
                    if ( IsWordChar( fullLine[i] ) )
                    {
                        continue;
                    }

                    endPosition = i;
                    break;
                }

                if ( endPosition <= startPosition )
                {
                    return;
                }

                string word = fullLine.Substring( startPosition, endPosition - startPosition );

                IEnumerable<PythonCompletionData> matches = GetSharedCompletionData().Where( i => i.MethodName.Equals( word ) ).ToArray();

                if ( matches.Any() )
                {
                    StackPanel panel = new StackPanel { Orientation = Orientation.Vertical, Margin = new Thickness( 5 ) };

                    foreach ( PythonCompletionData match in matches )
                    {
                        TextBlock descriptionText = new TextBlock { Text = match.Description.ToString(), TextWrapping = TextWrapping.Wrap, Margin = new Thickness( 0, 2, 0, 5 ) };
                        panel.Children.Add( descriptionText );
                        TextBlock nameText = new TextBlock { Text = match.Name, FontWeight = FontWeights.Bold, Margin = new Thickness( 0, 5, 0, 0 ) };
                        panel.Children.Add( nameText );
                    }

                    _toolTip.PlacementTarget = _textEditor;
                    _toolTip.Content = panel;
                    _toolTip.IsOpen = true;
                }
                else if ( IsPaused )
                {
                    KeyValuePair<string, object>[] frameVariables = FrameVariables.Where( kvp => kvp.Key.Equals( word ) ).ToArray();

                    if ( frameVariables.Any() )
                    {
                        StackPanel panel = new StackPanel { Orientation = Orientation.Vertical, Margin = new Thickness( 5 ) };

                        foreach ( KeyValuePair<string, object> variable in frameVariables )
                        {
                            TextBlock nameText = new TextBlock
                            {
                                Text = $"{variable.Key} : {variable.Value?.GetType().Name ?? "null"}", FontWeight = FontWeights.Bold, Margin = new Thickness( 0, 5, 0, 0 )
                            };
                            panel.Children.Add( nameText );
                            TextBlock valueText = new TextBlock
                            {
                                Text = MacroInvoker.GetDisplayValue( variable.Value ), TextWrapping = TextWrapping.Wrap, Margin = new Thickness( 0, 2, 0, 5 )
                            };
                            panel.Children.Add( valueText );
                        }

                        _toolTip.PlacementTarget = _textEditor;
                        _toolTip.Content = panel;
                        _toolTip.IsOpen = true;
                    }
                }

                e.Handled = true;
            }
            catch ( Exception )
            {
                // ignored
            }
        }

        private void OnTextEntered( object sender, TextCompositionEventArgs e )
        {
            if ( _textEditor?.Document == null )
            {
                return;
            }

            if ( _completionWindow != null )
            {
                return;
            }

            TextDocument document = _textEditor.Document;
            int caret = _textEditor.CaretOffset;
            int wordStart = caret;

            while ( wordStart > 0 && IsWordChar( document.GetCharAt( wordStart - 1 ) ) )
            {
                wordStart--;
            }

            if ( caret - wordStart < 3 )
            {
                return;
            }

            CompletionWindow window = new CompletionWindow( _textEditor.TextArea );
            ApplyCompletionWindowChrome( window );
            window.CloseWhenCaretAtBeginning = true;
            // Must be true so the popup closes when the caret leaves the word, on Escape, and when focus leaves the editor (see CompletionWindow.CloseOnFocusLost).
            window.CloseAutomatically = true;

            window.StartOffset = wordStart;
            window.EndOffset = caret;

            foreach ( PythonCompletionData item in GetSharedCompletionData() )
            {
                window.CompletionList.CompletionData.Add( item );
            }

            _completionWindow = window;
            window.Closed += ( _, __ ) =>
            {
                if ( ReferenceEquals( _completionWindow, window ) )
                {
                    _completionWindow = null;
                }
            };

            window.Show();
        }

        private sealed class CompletionSignatureEqualityComparer : IEqualityComparer<PythonCompletionData>
        {
            public bool Equals( PythonCompletionData x, PythonCompletionData y )
            {
                return !ReferenceEquals( x, null ) && !ReferenceEquals( y, null ) && x.Name.Equals( y.Name, StringComparison.Ordinal );
            }

            public int GetHashCode( PythonCompletionData obj )
            {
                return obj.Name.GetHashCode();
            }
        }
    }
}
