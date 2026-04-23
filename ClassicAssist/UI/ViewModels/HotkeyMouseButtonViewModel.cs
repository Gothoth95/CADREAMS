using ClassicAssist.Data.Hotkeys;
using ClassicAssist.Shared.UI;

namespace ClassicAssist.UI.ViewModels
{
    public class HotkeyMouseButtonViewModel : SetPropertyNotifyChanged
    {
        private int _bindCount;
        private bool _isSelected;
        private string _tooltipText;

        public HotkeyMouseButtonViewModel( string label, MouseOptions mouse, int row, int column, int columnSpan = 1 )
        {
            Label = label;
            Mouse = mouse;
            Row = row;
            Column = column;
            ColumnSpan = columnSpan;
            TooltipText = "Nessun bind";
        }

        public int BindCount
        {
            get => _bindCount;
            set
            {
                SetProperty( ref _bindCount, value );
                OnPropertyChanged( nameof( HasBind ) );
                OnPropertyChanged( nameof( DisplayText ) );
            }
        }

        public string DisplayText => HasBind ? $"{Label} ({BindCount})" : Label;
        public bool HasBind => BindCount > 0;

        public bool IsSelected
        {
            get => _isSelected;
            set => SetProperty( ref _isSelected, value );
        }

        public string Label { get; }
        public MouseOptions Mouse { get; }
        public int Row { get; }
        public int Column { get; }
        public int ColumnSpan { get; }

        public string TooltipText
        {
            get => _tooltipText;
            set => SetProperty( ref _tooltipText, value );
        }
    }
}
