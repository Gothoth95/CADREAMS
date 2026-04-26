using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using ClassicAssist.Resources;
using ICSharpCode.AvalonEdit.CodeCompletion;
using ICSharpCode.AvalonEdit.Document;
using ICSharpCode.AvalonEdit.Editing;

namespace ClassicAssist.Data.Macros
{
    public class PythonCompletionData : ICompletionData
    {
        public PythonCompletionData( string name, string fullName, string description, string insertText )
        {
            MethodName = name;
            Name = fullName;
            Description = description;
            Text = insertText;

            Example = MacroCommandHelp.ResourceManager.GetString( $"{name.ToUpper()}_COMMAND_EXAMPLE" );

            // Default completion UI binds Content; keep a concrete TextBlock so rows stay visible without popup-specific styles.
            var row = new TextBlock
            {
                Text = fullName,
                FontFamily = new FontFamily( "Consolas" ),
                FontSize = 12,
                TextTrimming = TextTrimming.CharacterEllipsis,
                TextWrapping = TextWrapping.NoWrap,
                Foreground = new SolidColorBrush( Color.FromRgb( 0xF1, 0xF5, 0xF9 ) )
            };
            if ( description != null )
            {
                row.ToolTip = description;
            }

            Content = row;
        }

        public string Example { get; set; }

        public string MethodName { get; set; }
        public string Name { get; set; }

        public void Complete( TextArea textArea, ISegment completionSegment, EventArgs insertionRequestEventArgs )
        {
            DocumentLine line = textArea.Document.Lines[textArea.Caret.Line - 1];

            string text = textArea.Document.GetText( line );

            int offset = completionSegment.Offset;

            // Walk backwards decrementing the offset if not ' ' || '\t'
            for ( int i = completionSegment.Offset; i > line.Offset; i-- )
            {
                int stringOffset = i - line.Offset - 1;

                if ( text[stringOffset] != ' ' && text[stringOffset] != '\t' )
                {
                    offset--;
                    continue;
                }

                break;
            }

            ISegment segment = new AnchorSegment( textArea.Document, offset, line.EndOffset - offset );

            textArea.Document.Replace( segment, Text );
        }

        public ImageSource Image => null;

        public string Text { get; }

        public object Content { get; set; }
        public object Description { get; }
        public double Priority { get; }
    }
}