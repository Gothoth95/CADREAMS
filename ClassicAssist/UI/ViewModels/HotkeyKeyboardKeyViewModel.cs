using System.Windows.Input;
using ClassicAssist.Shared.UI;

namespace ClassicAssist.UI.ViewModels
{
    public enum VirtualKeyboardLabelMode
    {
        Normal,
        Shift,
        AltGr
    }

    public class HotkeyKeyboardKeyViewModel : SetPropertyNotifyChanged
    {
        private int _bindCount;
        private bool _isSelected;
        private int _leftAltModifierBindCount;
        private VirtualKeyboardLabelMode _labelMode = VirtualKeyboardLabelMode.Normal;
        private bool _modifierVisualPressed;
        private int _shiftModifierBindCount;
        private string _tooltipText;

        public HotkeyKeyboardKeyViewModel( Key key, int row, int column, int columnSpan, string baseLabel,
            string shiftLabel, string altGrLabel = null, int rowSpan = 1 )
        {
            Key = key;
            Row = row;
            Column = column;
            ColumnSpan = columnSpan;
            RowSpan = rowSpan < 1 ? 1 : rowSpan;
            BaseLabel = baseLabel ?? string.Empty;
            ShiftLabel = string.IsNullOrEmpty( shiftLabel ) ? BaseLabel : shiftLabel;
            AltGrLabel = altGrLabel ?? string.Empty;
            TooltipText = "Nessun bind";
        }

        public string AltGrLabel { get; }
        public string BaseLabel { get; }
        public string ShiftLabel { get; }

        public int BindCount
        {
            get => _bindCount;
            set
            {
                SetProperty( ref _bindCount, value );
                OnPropertyChanged( nameof( HasBind ) );
                OnPropertyChanged( nameof( MainDisplay ) );
            }
        }

        public bool HasBind => GetEffectiveBindCount() > 0;

        public int ShiftModifierBindCount
        {
            get => _shiftModifierBindCount;
            set
            {
                SetProperty( ref _shiftModifierBindCount, value );
                OnPropertyChanged( nameof( HasBind ) );
                OnPropertyChanged( nameof( MainDisplay ) );
            }
        }

        public bool IsSelected
        {
            get => _isSelected;
            set => SetProperty( ref _isSelected, value );
        }

        public int LeftAltModifierBindCount
        {
            get => _leftAltModifierBindCount;
            set
            {
                SetProperty( ref _leftAltModifierBindCount, value );
                OnPropertyChanged( nameof( HasBind ) );
                OnPropertyChanged( nameof( MainDisplay ) );
            }
        }

        public bool ModifierVisualPressed
        {
            get => _modifierVisualPressed;
            set => SetProperty( ref _modifierVisualPressed, value );
        }

        public VirtualKeyboardLabelMode LabelMode
        {
            get => _labelMode;
            set
            {
                SetProperty( ref _labelMode, value, afterChange: _ =>
                {
                    OnPropertyChanged( nameof( PrimaryLine ) );
                    OnPropertyChanged( nameof( ShowSubLine ) );
                    OnPropertyChanged( nameof( SubLine ) );
                    OnPropertyChanged( nameof( MainDisplay ) );
                    OnPropertyChanged( nameof( HasBind ) );
                } );
            }
        }

        public string PrimaryLine
        {
            get
            {
                switch ( LabelMode )
                {
                    case VirtualKeyboardLabelMode.Normal:
                        return BaseLabel;
                    case VirtualKeyboardLabelMode.Shift:
                        return ShiftLabel;
                    case VirtualKeyboardLabelMode.AltGr:
                        return string.IsNullOrEmpty( AltGrLabel ) ? BaseLabel : AltGrLabel;
                    default:
                        return BaseLabel;
                }
            }
        }

        public string MainDisplay
        {
            get
            {
                int n = GetEffectiveBindCount();

                return n > 0 ? $"{PrimaryLine} ({n})" : PrimaryLine;
            }
        }

        private int GetEffectiveBindCount()
        {
            switch ( LabelMode )
            {
                case VirtualKeyboardLabelMode.Normal:
                    return BindCount;
                case VirtualKeyboardLabelMode.Shift:
                    return ShiftModifierBindCount;
                case VirtualKeyboardLabelMode.AltGr:
                    return LeftAltModifierBindCount;
                default:
                    return BindCount;
            }
        }

        public bool ShowSubLine =>
            LabelMode == VirtualKeyboardLabelMode.Normal && !string.IsNullOrEmpty( ShiftLabel ) &&
            ShiftLabel != BaseLabel;

        public string SubLine => ShiftLabel;

        public string TooltipText
        {
            get => _tooltipText;
            set => SetProperty( ref _tooltipText, value );
        }

        public int Column { get; }
        public int ColumnSpan { get; }
        public Key Key { get; }
        public int Row { get; }
        public int RowSpan { get; }
    }
}
