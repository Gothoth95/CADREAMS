using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Windows;
using System.Windows.Input;
using System.Windows.Threading;
using ClassicAssist.Shared.UI;
using ClassicAssist.UI.Views.Timers;

namespace ClassicAssist.UI.ViewModels
{
    public class TimerTabViewModel : BaseViewModel
    {
        private readonly Dictionary<TimerEntryViewModel, DispatcherTimer> _runningTimers =
            new Dictionary<TimerEntryViewModel, DispatcherTimer>();

        private readonly Dictionary<TimerEntryViewModel, TimerOverlayWindow> _timerWindows =
            new Dictionary<TimerEntryViewModel, TimerOverlayWindow>();

        private ICommand _addTimerCommand;
        private ICommand _removeTimerCommand;
        private ICommand _startTimerCommand;
        private ICommand _stopTimerCommand;
        private TimerEntryViewModel _selectedTimer;

        public TimerTabViewModel()
        {
            NewTimerName = "Timer";
            NewTimerSeconds = 30;
            NewTimerX = 100;
            NewTimerY = 100;
        }

        public ICommand AddTimerCommand =>
            _addTimerCommand ?? ( _addTimerCommand = new RelayCommand( AddTimer, o => NewTimerSeconds > 0 ) );

        public string NewTimerName { get; set; }
        public int NewTimerSeconds { get; set; }
        public int NewTimerX { get; set; }
        public int NewTimerY { get; set; }

        public ICommand RemoveTimerCommand =>
            _removeTimerCommand ?? ( _removeTimerCommand = new RelayCommand( RemoveTimer, o => SelectedTimer != null ) );

        public TimerEntryViewModel SelectedTimer
        {
            get => _selectedTimer;
            set => SetProperty( ref _selectedTimer, value );
        }

        public ICommand StartTimerCommand =>
            _startTimerCommand ?? ( _startTimerCommand = new RelayCommand( StartTimer, o => SelectedTimer != null ) );

        public ICommand StopTimerCommand =>
            _stopTimerCommand ?? ( _stopTimerCommand = new RelayCommand( StopTimer, o => SelectedTimer != null ) );

        public ObservableCollection<TimerEntryViewModel> Timers { get; } = new ObservableCollection<TimerEntryViewModel>();

        private void AddTimer( object _ )
        {
            string timerName = string.IsNullOrWhiteSpace( NewTimerName ) ? $"Timer {Timers.Count + 1}" : NewTimerName.Trim();

            TimerEntryViewModel timer = new TimerEntryViewModel
            {
                Name = timerName,
                DurationSeconds = Math.Max( 1, NewTimerSeconds ),
                RemainingSeconds = Math.Max( 1, NewTimerSeconds ),
                X = NewTimerX,
                Y = NewTimerY
            };

            Timers.Add( timer );
            SelectedTimer = timer;
        }

        private void RemoveTimer( object _ )
        {
            if ( SelectedTimer == null )
            {
                return;
            }

            StopAndCloseTimer( SelectedTimer );
            Timers.Remove( SelectedTimer );
            SelectedTimer = Timers.FirstOrDefault();
        }

        private void StartTimer( object _ )
        {
            if ( SelectedTimer == null )
            {
                return;
            }

            try
            {
                TimerEntryViewModel timer = SelectedTimer;

                StopAndCloseTimer( timer );

                timer.DurationSeconds = Math.Max( 1, timer.DurationSeconds );
                timer.RemainingSeconds = timer.DurationSeconds;
                timer.IsRunning = true;

                TimerOverlayWindow window = new TimerOverlayWindow
                {
                    DataContext = timer,
                    Left = timer.X,
                    Top = timer.Y,
                    Title = $"Timer - {timer.Name}"
                };

                window.Closed += ( s, e ) =>
                {
                    timer.X = (int) window.Left;
                    timer.Y = (int) window.Top;
                };

                window.Show();
                _timerWindows[timer] = window;

                DispatcherTimer dispatcherTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds( 1 ) };
                dispatcherTimer.Tick += ( s, e ) =>
                {
                    try
                    {
                        if ( timer.RemainingSeconds > 0 )
                        {
                            timer.RemainingSeconds--;
                        }

                        if ( timer.RemainingSeconds > 0 )
                        {
                            return;
                        }

                        timer.IsRunning = false;
                        dispatcherTimer.Stop();

                        if ( _runningTimers.ContainsKey( timer ) )
                        {
                            _runningTimers.Remove( timer );
                        }

                        if ( _timerWindows.TryGetValue( timer, out TimerOverlayWindow overlayWindow ) )
                        {
                            timer.X = (int) overlayWindow.Left;
                            timer.Y = (int) overlayWindow.Top;
                            overlayWindow.Close();
                            _timerWindows.Remove( timer );
                        }
                    }
                    catch ( Exception ex )
                    {
                        dispatcherTimer.Stop();
                        timer.IsRunning = false;
                        MessageBox.Show( $"Errore timer: {ex.Message}", "Timer Error", MessageBoxButton.OK,
                            MessageBoxImage.Error );
                    }
                };

                _runningTimers[timer] = dispatcherTimer;
                dispatcherTimer.Start();
            }
            catch ( Exception ex )
            {
                MessageBox.Show( $"Errore avvio timer: {ex.Message}", "Timer Error", MessageBoxButton.OK,
                    MessageBoxImage.Error );
            }
        }

        private void StopTimer( object _ )
        {
            if ( SelectedTimer == null )
            {
                return;
            }

            StopAndCloseTimer( SelectedTimer );
        }

        private void StopAndCloseTimer( TimerEntryViewModel timer )
        {
            try
            {
                timer.IsRunning = false;

                if ( _runningTimers.TryGetValue( timer, out DispatcherTimer runningTimer ) )
                {
                    runningTimer.Stop();
                    _runningTimers.Remove( timer );
                }

                if ( _timerWindows.TryGetValue( timer, out TimerOverlayWindow window ) )
                {
                    timer.X = (int) window.Left;
                    timer.Y = (int) window.Top;
                    window.Close();
                    _timerWindows.Remove( timer );
                }
            }
            catch
            {
                // Swallow to avoid destabilizing the assistant/game when window lifecycle races.
            }
        }
    }
}
