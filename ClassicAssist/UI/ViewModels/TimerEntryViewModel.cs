using ClassicAssist.Shared.UI;

namespace ClassicAssist.UI.ViewModels
{
    public class TimerEntryViewModel : SetPropertyNotifyChanged
    {
        private int _durationSeconds;
        private bool _isRunning;
        private string _name;
        private int _remainingSeconds;
        private int _x;
        private int _y;

        public int DurationSeconds
        {
            get => _durationSeconds;
            set
            {
                SetProperty( ref _durationSeconds, value );
                OnPropertyChanged( nameof( ElapsedSeconds ) );
                OnPropertyChanged( nameof( ProgressPercent ) );
            }
        }

        public int ElapsedSeconds => DurationSeconds > 0 ? DurationSeconds - RemainingSeconds : 0;

        public bool IsRunning
        {
            get => _isRunning;
            set => SetProperty( ref _isRunning, value );
        }

        public string Name
        {
            get => _name;
            set => SetProperty( ref _name, value );
        }

        public int ProgressPercent => DurationSeconds <= 0 ? 0 : (int) ( ElapsedSeconds * 100.0 / DurationSeconds );

        public int RemainingSeconds
        {
            get => _remainingSeconds;
            set
            {
                SetProperty( ref _remainingSeconds, value );
                OnPropertyChanged( nameof( ElapsedSeconds ) );
                OnPropertyChanged( nameof( ProgressPercent ) );
            }
        }

        public int X
        {
            get => _x;
            set => SetProperty( ref _x, value );
        }

        public int Y
        {
            get => _y;
            set => SetProperty( ref _y, value );
        }
    }
}
