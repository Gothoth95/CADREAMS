using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Collections.Specialized;
using System.Linq;
using System.Reflection;
using System.Windows;
using System.Windows.Input;
using ClassicAssist.Data;
using ClassicAssist.Data.Hotkeys;
using ClassicAssist.Data.Hotkeys.Commands;
using ClassicAssist.Data.Macros;
using ClassicAssist.Data.Spells;
using ClassicAssist.Misc;
using ClassicAssist.Shared.Resources;
using ClassicAssist.Shared.UI;
using ClassicAssist.UI.Views.Hotkeys;
using Newtonsoft.Json.Linq;
using Sentry;

namespace ClassicAssist.UI.ViewModels
{
    public class HotkeysTabViewModel : BaseViewModel, IGlobalSettingProvider
    {
        private const string GLOBAL_HOTKEYS_FILENAME = "Hotkeys.json";
        private readonly HotkeyManager _hotkeyManager;
        private readonly List<HotkeyCommand> _serializeCategories = new List<HotkeyCommand>();
        private ICommand _clearHotkeyCommand;
        private ICommand _configureHotkeyCommand;
        private ICommand _createMacroButtonCommand;
        private ICommand _executeCommand;
        private ObservableCollection<HotkeyCommand> _filterItems;
        private string _filterText;
        private HotkeyCommand _masteriesCategory;
        private ObservableCollection<HotkeyMouseButtonViewModel> _mouseButtons;
        private HotkeyEntry _selectedItem;
        private HotkeyCommand _spellsCategory;
        private readonly HashSet<HotkeyEntry> _trackedHotkeyEntries = new HashSet<HotkeyEntry>();
        private ObservableCollection<HotkeyKeyboardKeyViewModel> _virtualKeyboardKeys;
        private int _virtualKeyboardTabIndex;

        public HotkeysTabViewModel()
        {
            _hotkeyManager = HotkeyManager.GetInstance();
            _hotkeyManager.ClearAllHotkeys = ClearAllHotkeys;
            _hotkeyManager.InvokeByName = InvokeByName;

            Items.CollectionChanged += ItemsOnCollectionChanged;

            VirtualKeyboardKeys = new ObservableCollection<HotkeyKeyboardKeyViewModel>( BuildVirtualKeyboardLayout() );
            MouseButtons = new ObservableCollection<HotkeyMouseButtonViewModel>( BuildVirtualMouseLayout() );
            RebindHotkeyEntrySubscriptions();
            ApplyVirtualKeyboardLabelMode( VirtualKeyboardLabelMode.Normal );
            UpdateVirtualKeyboardState();
        }

        public ICommand ClearHotkeyCommand =>
            _clearHotkeyCommand ?? ( _clearHotkeyCommand = new RelayCommand( ClearHotkey, o => SelectedItem != null ) );

        public ICommand ConfigureHotkeyCommand =>
            _configureHotkeyCommand ?? ( _configureHotkeyCommand = new RelayCommand( ConfigureHotkey,
                o => SelectedItem != null && SelectedItem.Configurable ) );

        public ICommand CreateMacroButtonCommand =>
            _createMacroButtonCommand ?? ( _createMacroButtonCommand =
                new RelayCommand( CreateMacroButton, o => SelectedItem != null ) );

        public ICommand ExecuteCommand =>
            _executeCommand ?? ( _executeCommand = new RelayCommand( ExecuteHotkey, o => SelectedItem != null ) );

        public ObservableCollection<HotkeyCommand> FilterItems
        {
            get => _filterItems;
            set => SetProperty( ref _filterItems, value );
        }

        public ObservableCollection<HotkeyKeyboardKeyViewModel> VirtualKeyboardKeys
        {
            get => _virtualKeyboardKeys;
            set => SetProperty( ref _virtualKeyboardKeys, value );
        }

        /// <summary>0 = Predefinita (solo bind senza Maiusc né Alt), 1 = Maiusc, 2 = Alt / AltGr.</summary>
        public int VirtualKeyboardTabIndex
        {
            get => _virtualKeyboardTabIndex;
            set
            {
                SetProperty( ref _virtualKeyboardTabIndex, value, afterChange: idx =>
                {
                    VirtualKeyboardLabelMode mode = VirtualKeyboardLabelMode.Normal;

                    if ( idx == 1 )
                    {
                        mode = VirtualKeyboardLabelMode.Shift;
                    }
                    else if ( idx == 2 )
                    {
                        mode = VirtualKeyboardLabelMode.AltGr;
                    }

                    ApplyVirtualKeyboardLabelMode( mode );
                    UpdateVirtualKeyboardModifierVisualState();
                    UpdateVirtualKeyboardState();
                } );
            }
        }

        public string FilterText
        {
            get => _filterText;
            set
            {
                SetProperty( ref _filterText, value );
                UpdateFilteredItems();
            }
        }

        public ShortcutKeys Hotkey
        {
            get => SelectedItem?.Hotkey;
            set => CheckOverwriteHotkey( SelectedItem, value );
        }

        public ObservableCollectionEx<HotkeyCommand> Items
        {
            get => _hotkeyManager.Items;
            set => _hotkeyManager.Items = value;
        }

        public bool Searching { get; set; }

        public ObservableCollection<HotkeyMouseButtonViewModel> MouseButtons
        {
            get => _mouseButtons;
            set => SetProperty( ref _mouseButtons, value );
        }

        public HotkeyEntry SelectedItem
        {
            get => _selectedItem;
            set
            {
                SetProperty( ref _selectedItem, value );
                OnPropertyChanged( nameof( Hotkey ) );
                UpdateVirtualKeyboardState();
            }
        }

        public string GetGlobalFilename()
        {
            return GLOBAL_HOTKEYS_FILENAME;
        }

        public void Serialize( JObject json, bool global = false )
        {
            JObject hotkeys = new JObject();

            JArray commandsArray = SerializeCommands( e => e.IsGlobal == global );

            hotkeys.Add( "Commands", commandsArray );

            JArray optionsArray = SerializeOptions( e => e.IsGlobal == global );

            hotkeys.Add( "Options", optionsArray );

            JArray spellsArray = SerializeSpells( e => e.IsGlobal == global );

            hotkeys.Add( "Spells", spellsArray );

            JArray masteryArray = SerializeMasteries( e => e.IsGlobal == global );

            hotkeys.Add( "Masteries", masteryArray );

            json?.Add( "Hotkeys", hotkeys );
        }

        public void Deserialize( JObject json, Options options, bool global = false )
        {
            if ( !global )
            {
                IEnumerable<Type> hotkeyCommands = Assembly.GetExecutingAssembly().GetTypes()
                    .Where( i => i.IsSubclassOf( typeof( HotkeyCommand ) ) );

                foreach ( Type hotkeyCommand in hotkeyCommands )
                {
                    HotkeyCommand hkc = (HotkeyCommand) Activator.CreateInstance( hotkeyCommand );

                    HotkeyCommandAttribute attr = hkc.GetType().GetCustomAttribute<HotkeyCommandAttribute>();

                    string categoryName = Strings.Commands;

                    if ( attr != null && !string.IsNullOrEmpty( attr.Category ) )
                    {
                        categoryName = Strings.ResourceManager.GetString( attr.Category );
                    }

                    HotkeyCommand category = Items.FirstOrDefault( hke => hke.Name == categoryName && hke.IsCategory );

                    if ( category != null )
                    {
                        if ( category.Children == null )
                        {
                            category.Children = new ObservableCollectionEx<HotkeyEntry>();
                        }

                        if ( category.Children.Contains( hkc ) )
                        {
                            category.Children.Remove( hkc );
                        }

                        category.Children.Add( hkc );
                    }
                    else
                    {
                        category = new HotkeyCommand
                        {
                            Name = categoryName,
                            IsCategory = true,
                            Children = new ObservableCollectionEx<HotkeyEntry> { hkc }
                        };

                        _hotkeyManager.AddCategory( category );
                        _serializeCategories.Add( category );
                    }
                }
            }

            JToken hotkeys = json?["Hotkeys"];

            if ( hotkeys?["Commands"] != null )
            {
                foreach ( JToken token in hotkeys["Commands"] )
                {
                    JToken type = token["Type"];

                    foreach ( HotkeyCommand category in _serializeCategories )
                    {
                        HotkeyEntry entry =
                            category.Children.FirstOrDefault( o => o.GetType().FullName == type.ToObject<string>() );

                        if ( entry == null )
                        {
                            continue;
                        }

                        JToken keys = token["Keys"];

                        entry.Hotkey = new ShortcutKeys( keys );
                        entry.PassToUO = token["PassToUO"]?.ToObject<bool>() ?? true;
                        entry.Disableable = token["Disableable"]?.ToObject<bool>() ?? entry.Disableable;
                        entry.IsGlobal = global;
                    }
                }
            }

            if ( hotkeys?["Options"] != null )
            {
                foreach ( JToken token in hotkeys["Options"] )
                {
                    JToken type = token["Type"];
                    JToken propertyName = token["Property"];
                    JToken value = token["Value"];

                    foreach ( HotkeyCommand category in _serializeCategories )
                    {
                        HotkeyEntry entry =
                            category.Children.FirstOrDefault( o => o.GetType().FullName == type?.ToObject<string>() );

                        if ( entry == null )
                        {
                            continue;
                        }

                        if ( string.IsNullOrEmpty( propertyName.ToString() ) )
                        {
                            continue;
                        }

                        PropertyInfo property = entry.GetType().GetProperty( propertyName.ToString(),
                            BindingFlags.Instance | BindingFlags.Public );

                        HotkeyConfigurationAttribute attribute =
                            property.GetCustomAttribute<HotkeyConfigurationAttribute>();

                        if ( attribute == null )
                        {
                            continue;
                        }

                        try
                        {
                            object val = value?.ToObject( attribute.Type );

                            property.SetValue( entry, val );

                            if ( global )
                            {
                                entry.IsGlobal = true;
                            }
                        }
                        catch ( Exception ex )
                        {
                            SentrySdk.CaptureException( ex );
                        }
                    }
                }
            }

            if ( _spellsCategory != null && !global )
            {
                _hotkeyManager.Items.Remove( _spellsCategory );
            }

            SpellManager spellManager = SpellManager.GetInstance();

            if ( !global )
            {
                _spellsCategory = new HotkeyCommand { Name = Strings.Spells, IsCategory = true };

                SpellData[] spells = spellManager.GetSpellData();

                ObservableCollectionEx<HotkeyEntry> children = new ObservableCollectionEx<HotkeyEntry>();

                foreach ( SpellData spell in spells )
                {
                    HotkeyCommand hkc = new HotkeyCommand
                    {
                        Name = spell.Name,
                        Action = ( hks, _ ) => spellManager.CastSpell( spell.ID ),
                        Hotkey = ShortcutKeys.Default,
                        PassToUO = true
                    };

                    children.Add( hkc );
                }

                _spellsCategory.Children = children;

                _hotkeyManager.AddCategory( _spellsCategory );
            }

            JToken spellsObj = hotkeys?["Spells"];

            if ( spellsObj != null )
            {
                foreach ( JToken token in spellsObj )
                {
                    JToken name = token["Name"];

                    HotkeyEntry entry =
                        _spellsCategory.Children.FirstOrDefault( s => s.Name == name.ToObject<string>() );

                    if ( entry == null )
                    {
                        continue;
                    }

                    entry.Hotkey = new ShortcutKeys( token["Keys"] );
                    entry.PassToUO = token["PassToUO"]?.ToObject<bool>() ?? true;
                    entry.IsGlobal = global;
                }
            }

            if ( _masteriesCategory != null && !global )
            {
                _hotkeyManager.Items.Remove( _masteriesCategory );
            }

            if ( !global )
            {
                _masteriesCategory = new HotkeyCommand { Name = Strings.Masteries, IsCategory = true };

                SpellData[] masteries = spellManager.GetMasteryData();

                ObservableCollectionEx<HotkeyEntry> masteryChildren = new ObservableCollectionEx<HotkeyEntry>();

                foreach ( SpellData mastery in masteries )
                {
                    HotkeyCommand hkc = new HotkeyCommand
                    {
                        Name = mastery.Name,
                        Action = ( hks, _ ) => spellManager.CastSpell( mastery.ID ),
                        Hotkey = ShortcutKeys.Default,
                        PassToUO = true
                    };

                    masteryChildren.Add( hkc );
                }

                _masteriesCategory.Children = masteryChildren;

                _hotkeyManager.AddCategory( _masteriesCategory );
            }

            JToken masteryObj = hotkeys?["Masteries"];

            if ( masteryObj != null )
            {
                foreach ( JToken token in masteryObj )
                {
                    JToken name = token["Name"];

                    HotkeyEntry entry =
                        _masteriesCategory.Children.FirstOrDefault( s => s.Name == name.ToObject<string>() );

                    if ( entry == null )
                    {
                        continue;
                    }

                    entry.Hotkey = new ShortcutKeys( token["Keys"] );
                    entry.PassToUO = token["PassToUO"]?.ToObject<bool>() ?? true;
                    entry.IsGlobal = global;
                }
            }

            RebindHotkeyEntrySubscriptions();
            UpdateVirtualKeyboardState();
        }

        private void InvokeByName( string name, Type type )
        {
            foreach ( HotkeyCommand item in Items )
            {
                HotkeyEntry hotkey = item.Children.FirstOrDefault( e => e.GetType() == type && e.Name == name );

                if ( hotkey == null )
                {
                    continue;
                }

                hotkey.Action( hotkey, null );
                break;
            }
        }

        private JArray SerializeOptions( Func<HotkeyEntry, bool> predicate )
        {
            JArray optionsArray = new JArray();

            foreach ( JObject jObject in from serializeCategory in _serializeCategories
                     from hotkeyEntry in serializeCategory.Children.Where( e => e.Configurable && predicate( e ) )
                     let properties =
                         hotkeyEntry.GetType().GetProperties().Where( prop =>
                             prop.IsDefined( typeof( HotkeyConfigurationAttribute ), false ) )
                     from propertyInfo in properties
                     select new JObject
                     {
                         { "Type", hotkeyEntry.GetType().FullName },
                         { "Property", propertyInfo.Name },
                         { "Value", propertyInfo.GetValue( hotkeyEntry ).ToString() }
                     } )
            {
                optionsArray.Add( jObject );
            }

            return optionsArray;
        }

        private void CreateMacroButton( object obj )
        {
            if ( !( SelectedItem is HotkeyEntry hotkeyEntry ) )
            {
                return;
            }

            Data.ClassicUO.Macros.CreateMacroButton( hotkeyEntry );
        }

        private JArray SerializeMasteries( Func<HotkeyEntry, bool> predicate )
        {
            JArray masteryArray = new JArray();

            foreach ( HotkeyEntry masteriesCategoryChild in _masteriesCategory.Children.Where( predicate ) )
            {
                if ( Equals( masteriesCategoryChild.Hotkey, ShortcutKeys.Default ) )
                {
                    continue;
                }

                JObject entry = new JObject
                {
                    { "Name", masteriesCategoryChild.Name },
                    { "Keys", masteriesCategoryChild.Hotkey.ToJObject() },
                    { "PassToUO", masteriesCategoryChild.PassToUO }
                };

                masteryArray.Add( entry );
            }

            return masteryArray;
        }

        private JArray SerializeSpells( Func<HotkeyEntry, bool> predicate )
        {
            JArray spellsArray = new JArray();

            foreach ( HotkeyEntry spellsCategoryChild in _spellsCategory.Children.Where( predicate ) )
            {
                if ( Equals( spellsCategoryChild.Hotkey, ShortcutKeys.Default ) )
                {
                    continue;
                }

                JObject entry = new JObject
                {
                    { "Name", spellsCategoryChild.Name },
                    { "Keys", spellsCategoryChild.Hotkey.ToJObject() },
                    { "PassToUO", spellsCategoryChild.PassToUO }
                };

                spellsArray.Add( entry );
            }

            return spellsArray;
        }

        private JArray SerializeCommands( Func<HotkeyEntry, bool> predicate )
        {
            JArray commandsArray = new JArray();

            foreach ( JObject entry in from category in _serializeCategories
                     from categoryChild in category.Children.Where( predicate )
                     where !Equals( categoryChild.Hotkey, ShortcutKeys.Default )
                     select new JObject
                     {
                         { "Type", categoryChild.GetType().FullName },
                         { "Keys", categoryChild.Hotkey.ToJObject() },
                         { "PassToUO", categoryChild.PassToUO },
                         { "Disableable", categoryChild.Disableable }
                     } )
            {
                commandsArray.Add( entry );
            }

            return commandsArray;
        }

        private void UpdateFilteredItems()
        {
            _dispatcher.Invoke( () =>
            {
                HotkeyEntry selectedItem = SelectedItem;

                if ( string.IsNullOrEmpty( FilterText ) )
                {
                    FilterItems = Items;
                    return;
                }

                if ( Searching )
                {
                    return;
                }

                Searching = true;

                bool Predicate( HotkeyEntry hke )
                {
                    return hke.Name.ToLower().Contains( FilterText.ToLower() );
                }

                FilterItems = new ObservableCollectionEx<HotkeyCommand>( Items.Where( e => e.Children.Any( Predicate ) )
                    .Select( e =>
                    {
                        HotkeyCommand hkc = new HotkeyCommand
                        {
                            Tooltip = e.Tooltip,
                            Name = e.Name,
                            Action = e.Action,
                            Disableable = e.Disableable,
                            Hotkey = e.Hotkey,
                            IsCategory = e.IsCategory,
                            PassToUO = e.PassToUO,
                            IsExpanded = true
                        };

                        IEnumerable<HotkeyEntry> children = e.Children.Where( Predicate ).ToList();

                        foreach ( HotkeyEntry child in children )
                        {
                            child.PropertyChanged += ( s, ea ) => UpdateFilteredItems();
                        }

                        hkc.Children = new ObservableCollectionEx<HotkeyEntry>( children );

                        return hkc;
                    } ) );

                if ( selectedItem != null )
                {
                    foreach ( HotkeyCommand filterItem in FilterItems )
                    {
                        foreach ( HotkeyEntry child in filterItem.Children )
                        {
                            if ( ReferenceEquals( child, selectedItem ) )
                            {
                                SelectedItem = child;
                            }
                        }
                    }
                }

                Searching = false;
            } );
        }

        private void CheckOverwriteHotkey( HotkeyEntry selectedItem, ShortcutKeys hotkey )
        {
            if ( selectedItem == null )
            {
                return;
            }

            HotkeyEntry conflict = null;

            foreach ( HotkeyCommand hotkeyEntry in Items )
            {
                foreach ( HotkeyEntry entry in hotkeyEntry.Children )
                {
                    if ( entry.Hotkey.Equals( hotkey ) )
                    {
                        conflict = entry;
                    }
                }
            }

            if ( conflict != null && !ReferenceEquals( selectedItem, conflict ) )
            {
                MessageBoxResult result =
                    MessageBox.Show( string.Format( Strings.Overwrite_existing_hotkey___0____, conflict ),
                        Strings.Warning, MessageBoxButton.YesNo );

                if ( result == MessageBoxResult.No )
                {
                    OnPropertyChanged( nameof( Hotkey ) );
                    return;
                }
            }

            SelectedItem.Hotkey = hotkey;
            OnPropertyChanged( nameof( Hotkey ) );
            UpdateVirtualKeyboardState();
        }

        private void ClearAllHotkeys()
        {
            foreach ( HotkeyEntry entryChild in _serializeCategories.SelectMany( hotkeyEntry => hotkeyEntry.Children ) )
            {
                entryChild.Hotkey = ShortcutKeys.Default;
            }

            foreach ( HotkeyEntry spellEntry in _spellsCategory.Children )
            {
                spellEntry.Hotkey = ShortcutKeys.Default;
            }

            UpdateVirtualKeyboardState();
        }

        private void ClearHotkey( object obj )
        {
            if ( obj is HotkeyEntry cmd )
            {
                cmd.Hotkey = ShortcutKeys.Default;
                UpdateVirtualKeyboardState();
            }
        }

        private static void ExecuteHotkey( object obj )
        {
            if ( obj is HotkeyEntry cmd )
            {
                cmd.Action( cmd, null );
            }
        }

        private static void ConfigureHotkey( object obj )
        {
            if ( !( obj is HotkeyCommand hotkeyCommand ) )
            {
                return;
            }

            HotkeyOptionsWindow window = new HotkeyOptionsWindow( hotkeyCommand );

            window.ShowDialog();
        }

        private void ItemsOnCollectionChanged( object sender, NotifyCollectionChangedEventArgs e )
        {
            UpdateFilteredItems();
            RebindHotkeyEntrySubscriptions();
            UpdateVirtualKeyboardState();
        }

        private void RebindHotkeyEntrySubscriptions()
        {
            List<HotkeyEntry> entries = Items
                .Where( i => i.Children != null )
                .SelectMany( i => i.Children )
                .ToList();

            foreach ( HotkeyEntry entry in _trackedHotkeyEntries.Where( tracked => !entries.Contains( tracked ) ).ToList() )
            {
                entry.PropertyChanged -= HotkeyEntryOnPropertyChanged;
                _trackedHotkeyEntries.Remove( entry );
            }

            foreach ( HotkeyEntry entry in entries.Where( entry => !_trackedHotkeyEntries.Contains( entry ) ) )
            {
                entry.PropertyChanged += HotkeyEntryOnPropertyChanged;
                _trackedHotkeyEntries.Add( entry );
            }
        }

        private void HotkeyEntryOnPropertyChanged( object sender, System.ComponentModel.PropertyChangedEventArgs e )
        {
            if ( e.PropertyName != nameof( HotkeyEntry.Hotkey ) )
            {
                return;
            }

            UpdateVirtualKeyboardState();
        }

        private void ApplyVirtualKeyboardLabelMode( VirtualKeyboardLabelMode mode )
        {
            if ( VirtualKeyboardKeys == null )
            {
                return;
            }

            foreach ( HotkeyKeyboardKeyViewModel k in VirtualKeyboardKeys )
            {
                k.LabelMode = mode;
            }
        }

        private static bool ModifierIncludesShift( SDLKeys.ModKey m )
        {
            return ( m & ( SDLKeys.ModKey.LeftShift | SDLKeys.ModKey.RightShift ) ) != 0;
        }

        /// <summary>Left or Right Alt (incluso AltGr come Ctrl+Alt destro).</summary>
        private static bool ModifierIncludesAnyAlt( SDLKeys.ModKey m )
        {
            return ( m & ( SDLKeys.ModKey.LeftAlt | SDLKeys.ModKey.RightAlt ) ) != 0;
        }

        /// <summary>Conteggi tab Predefinita: nessun modificatore Maiusc né Alt.</summary>
        private static bool ModifierIsPlainForDefaultVirtualTab( SDLKeys.ModKey m )
        {
            return !ModifierIncludesShift( m ) && !ModifierIncludesAnyAlt( m );
        }

        private static IEnumerable<HotkeyEntry> FilterHotkeyEntriesForVirtualTab( IEnumerable<HotkeyEntry> entries,
            int virtualKeyboardTabIndex )
        {
            switch ( virtualKeyboardTabIndex )
            {
                case 1:
                    return entries.Where( e => e.Hotkey != null && ModifierIncludesShift( e.Hotkey.Modifier ) );
                case 2:
                    return entries.Where( e => e.Hotkey != null && ModifierIncludesAnyAlt( e.Hotkey.Modifier ) );
                default:
                    return entries.Where( e => e.Hotkey != null && ModifierIsPlainForDefaultVirtualTab( e.Hotkey.Modifier ) );
            }
        }

        private void UpdateVirtualKeyboardModifierVisualState()
        {
            if ( VirtualKeyboardKeys == null )
            {
                return;
            }

            foreach ( HotkeyKeyboardKeyViewModel k in VirtualKeyboardKeys )
            {
                bool pressed = false;

                if ( VirtualKeyboardTabIndex == 1 && ( k.Key == Key.LeftShift || k.Key == Key.RightShift ) )
                {
                    pressed = true;
                }
                else if ( VirtualKeyboardTabIndex == 2 && k.Key == Key.LeftAlt )
                {
                    pressed = true;
                }

                k.ModifierVisualPressed = pressed;
            }
        }

        private IEnumerable<HotkeyKeyboardKeyViewModel> BuildVirtualKeyboardLayout()
        {
            List<HotkeyKeyboardKeyViewModel> keys = new List<HotkeyKeyboardKeyViewModel>();

            HotkeyKeyboardKeyViewModel K( Key key, int row, int col, string b, string s, string a = null, int span = 1,
                int rowSpan = 1 )
            {
                return new HotkeyKeyboardKeyViewModel( key, row, col, span, b, s, a, rowSpan );
            }

            // Function row
            keys.Add( K( Key.Escape, 0, 0, "Esc", "Esc", null, 2 ) );
            keys.Add( K( Key.F1, 0, 3, "F1", "F1" ) );
            keys.Add( K( Key.F2, 0, 4, "F2", "F2" ) );
            keys.Add( K( Key.F3, 0, 5, "F3", "F3" ) );
            keys.Add( K( Key.F4, 0, 6, "F4", "F4" ) );
            keys.Add( K( Key.F5, 0, 8, "F5", "F5" ) );
            keys.Add( K( Key.F6, 0, 9, "F6", "F6" ) );
            keys.Add( K( Key.F7, 0, 10, "F7", "F7" ) );
            keys.Add( K( Key.F8, 0, 11, "F8", "F8" ) );
            keys.Add( K( Key.F9, 0, 13, "F9", "F9" ) );
            keys.Add( K( Key.F10, 0, 14, "F10", "F10" ) );
            keys.Add( K( Key.F11, 0, 15, "F11", "F11" ) );
            keys.Add( K( Key.F12, 0, 16, "F12", "F12" ) );

            // Number row — Italian QWERTY (come tastiera fisica IT: base / Maiusc / terzo livello)
            keys.Add( K( Key.Oem5, 1, 0, "\\", "|", "¬" ) );
            keys.Add( K( Key.D1, 1, 1, "1", "!" ) );
            keys.Add( K( Key.D2, 1, 2, "2", "\"", "@" ) );
            keys.Add( K( Key.D3, 1, 3, "3", "£", "#" ) );
            keys.Add( K( Key.D4, 1, 4, "4", "$" ) );
            keys.Add( K( Key.D5, 1, 5, "5", "%", "€" ) );
            keys.Add( K( Key.D6, 1, 6, "6", "&" ) );
            keys.Add( K( Key.D7, 1, 7, "7", "/" ) );
            keys.Add( K( Key.D8, 1, 8, "8", "(" ) );
            keys.Add( K( Key.D9, 1, 9, "9", ")" ) );
            keys.Add( K( Key.D0, 1, 10, "0", "=" ) );
            keys.Add( K( Key.OemOpenBrackets, 1, 11, "'", "?", null ) );
            keys.Add( K( Key.Oem6, 1, 12, "ì", "^", null ) );
            keys.Add( K( Key.Back, 1, 13, "Back", "Back", null, 4 ) );

            // Q row
            keys.Add( K( Key.Tab, 2, 0, "Tab", "Tab", null, 2 ) );
            keys.Add( K( Key.Q, 2, 2, "Q", "Q" ) );
            keys.Add( K( Key.W, 2, 3, "W", "W" ) );
            keys.Add( K( Key.E, 2, 4, "E", "E" ) );
            keys.Add( K( Key.R, 2, 5, "R", "R" ) );
            keys.Add( K( Key.T, 2, 6, "T", "T" ) );
            keys.Add( K( Key.Y, 2, 7, "Y", "Y" ) );
            keys.Add( K( Key.U, 2, 8, "U", "U" ) );
            keys.Add( K( Key.I, 2, 9, "I", "I" ) );
            keys.Add( K( Key.O, 2, 10, "O", "O" ) );
            keys.Add( K( Key.P, 2, 11, "P", "P" ) );
            keys.Add( K( Key.Oem1, 2, 12, "è", "é", "[" ) );
            keys.Add( K( Key.OemPlus, 2, 13, "+", "*", "]" ) );

            // A row
            keys.Add( K( Key.CapsLock, 3, 0, "Caps", "Caps", null, 2 ) );
            keys.Add( K( Key.A, 3, 2, "A", "A" ) );
            keys.Add( K( Key.S, 3, 3, "S", "S" ) );
            keys.Add( K( Key.D, 3, 4, "D", "D" ) );
            keys.Add( K( Key.F, 3, 5, "F", "F" ) );
            keys.Add( K( Key.G, 3, 6, "G", "G" ) );
            keys.Add( K( Key.H, 3, 7, "H", "H" ) );
            keys.Add( K( Key.J, 3, 8, "J", "J" ) );
            keys.Add( K( Key.K, 3, 9, "K", "K" ) );
            keys.Add( K( Key.L, 3, 10, "L", "L" ) );
            keys.Add( K( Key.Oem3, 3, 11, "ò", "ç", "@" ) );
            keys.Add( K( Key.OemQuotes, 3, 12, "à", "°", "#" ) );
            keys.Add( K( Key.OemQuestion, 3, 13, "ù", "§", null ) );
            keys.Add( K( Key.Enter, 3, 14, "Invio", "Invio", null, 3 ) );

            // Z row
            keys.Add( K( Key.LeftShift, 4, 0, "Shift", "Shift", null, 2 ) );
            keys.Add( K( Key.OemBackslash, 4, 2, "<", ">", null ) );
            keys.Add( K( Key.Z, 4, 3, "Z", "Z" ) );
            keys.Add( K( Key.X, 4, 4, "X", "X" ) );
            keys.Add( K( Key.C, 4, 5, "C", "C" ) );
            keys.Add( K( Key.V, 4, 6, "V", "V" ) );
            keys.Add( K( Key.B, 4, 7, "B", "B" ) );
            keys.Add( K( Key.N, 4, 8, "N", "N" ) );
            keys.Add( K( Key.M, 4, 9, "M", "M" ) );
            keys.Add( K( Key.OemComma, 4, 10, ",", ";", null ) );
            keys.Add( K( Key.OemPeriod, 4, 11, ".", ":", null ) );
            keys.Add( K( Key.OemMinus, 4, 12, "-", "_", null ) );
            keys.Add( K( Key.RightShift, 4, 13, "Shift", "Shift", null, 4 ) );

            // Bottom row + navigation
            keys.Add( K( Key.LeftCtrl, 5, 0, "Ctrl", "Ctrl", null, 2 ) );
            keys.Add( K( Key.LeftAlt, 5, 2, "Alt", "Alt", null, 2 ) );
            keys.Add( K( Key.Space, 5, 4, "Space", "Space", null, 6 ) );
            keys.Add( K( Key.RightAlt, 5, 10, "AltGr", "AltGr", null, 2 ) );
            keys.Add( K( Key.RightCtrl, 5, 12, "Ctrl", "Ctrl", null, 2 ) );
            keys.Add( K( Key.Insert, 5, 14, "Ins", "Ins" ) );
            keys.Add( K( Key.Home, 5, 15, "Home", "Home" ) );
            keys.Add( K( Key.PageUp, 5, 16, "PgUp", "PgUp" ) );
            keys.Add( K( Key.Delete, 6, 14, "Del", "Del" ) );
            keys.Add( K( Key.End, 6, 15, "End", "End" ) );
            keys.Add( K( Key.PageDown, 6, 16, "PgDn", "PgDn" ) );
            keys.Add( K( Key.Up, 5, 18, "↑", "↑" ) );
            keys.Add( K( Key.Left, 6, 17, "←", "←" ) );
            keys.Add( K( Key.Down, 6, 18, "↓", "↓" ) );
            keys.Add( K( Key.Right, 6, 19, "→", "→" ) );

            // Tastierino numerico (col. 20–24). Con Bloc Num spento molti tasti coincidono con Home/Frecce/Pag (stessi Key WPF).
            // Invio numerico = stesso Key.Enter dell’Invio principale; KP+ = Key.Add (il + italiano è spesso OemPlus).
            const int np = 20;
            keys.Add( K( Key.NumLock, 2, np + 0, "Bloc Num", "Bloc Num" ) );
            keys.Add( K( Key.Divide, 2, np + 1, "NP /", "NP /" ) );
            keys.Add( K( Key.Multiply, 2, np + 2, "NP *", "NP *" ) );
            keys.Add( K( Key.Subtract, 2, np + 3, "NP −", "NP −" ) );
            keys.Add( K( Key.Clear, 2, np + 4, "Canc", "Canc" ) );

            keys.Add( K( Key.NumPad7, 3, np + 0, "NP 7", "NP 7" ) );
            keys.Add( K( Key.NumPad8, 3, np + 1, "NP 8", "NP 8" ) );
            keys.Add( K( Key.NumPad9, 3, np + 2, "NP 9", "NP 9" ) );
            keys.Add( K( Key.Add, 3, np + 3, "NP +", "NP +", null, 1, 2 ) );

            keys.Add( K( Key.NumPad4, 4, np + 0, "NP 4", "NP 4" ) );
            keys.Add( K( Key.NumPad5, 4, np + 1, "NP 5", "NP 5" ) );
            keys.Add( K( Key.NumPad6, 4, np + 2, "NP 6", "NP 6" ) );
            keys.Add( K( Key.OemClear, 4, np + 4, "C·SDL", "C·SDL" ) );

            keys.Add( K( Key.NumPad1, 5, np + 0, "NP 1", "NP 1" ) );
            keys.Add( K( Key.NumPad2, 5, np + 1, "NP 2", "NP 2" ) );
            keys.Add( K( Key.NumPad3, 5, np + 2, "NP 3", "NP 3" ) );
            keys.Add( K( Key.Enter, 5, np + 3, "↵ NP", "↵ NP", null, 1, 2 ) );

            keys.Add( K( Key.NumPad0, 6, np + 0, "NP 0", "NP 0", null, 2 ) );
            keys.Add( K( Key.Decimal, 6, np + 2, "NP .", "NP ." ) );

            return keys;
        }

        private IEnumerable<HotkeyMouseButtonViewModel> BuildVirtualMouseLayout()
        {
            return new[]
            {
                new HotkeyMouseButtonViewModel( "LMB", MouseOptions.LeftButton, 0, 0, 2 ),
                new HotkeyMouseButtonViewModel( "Wheel Up", MouseOptions.MouseWheelUp, 0, 2 ),
                new HotkeyMouseButtonViewModel( "RMB", MouseOptions.RightButton, 0, 3, 2 ),
                new HotkeyMouseButtonViewModel( "X1", MouseOptions.XButton1, 1, 0, 2 ),
                new HotkeyMouseButtonViewModel( "MMB", MouseOptions.MiddleButton, 1, 2 ),
                new HotkeyMouseButtonViewModel( "X2", MouseOptions.XButton2, 1, 3, 2 ),
                new HotkeyMouseButtonViewModel( "Wheel Down", MouseOptions.MouseWheelDown, 2, 2 )
            };
        }

        private void UpdateVirtualKeyboardState()
        {
            if ( VirtualKeyboardKeys == null )
            {
                return;
            }

            List<HotkeyEntry> keyboardHotkeyEntries = Items
                .Where( i => i.Children != null )
                .SelectMany( i => i.Children )
                .ToList();

            Dictionary<Key, int> keyCounts = keyboardHotkeyEntries
                .Where( entry =>
                    entry.Hotkey != null && entry.Hotkey.Key != Key.None && entry.Hotkey.Mouse == MouseOptions.None &&
                    ModifierIsPlainForDefaultVirtualTab( entry.Hotkey.Modifier ) )
                .GroupBy( entry => entry.Hotkey.Key )
                .ToDictionary( g => g.Key, g => g.Count() );

            Dictionary<Key, List<HotkeyEntry>> keyEntries = keyboardHotkeyEntries
                .Where( entry => entry.Hotkey != null && entry.Hotkey.Key != Key.None && entry.Hotkey.Mouse == MouseOptions.None )
                .GroupBy( entry => entry.Hotkey.Key )
                .ToDictionary( g => g.Key, g => g.OrderBy( e => e.Name ).ToList() );

            Key selectedKey = Key.None;

            if ( SelectedItem?.Hotkey != null && SelectedItem.Hotkey.Mouse == MouseOptions.None )
            {
                selectedKey = SelectedItem.Hotkey.Key;
            }

            foreach ( HotkeyKeyboardKeyViewModel virtualKey in VirtualKeyboardKeys )
            {
                virtualKey.BindCount = keyCounts.TryGetValue( virtualKey.Key, out int count ) ? count : 0;

                virtualKey.ShiftModifierBindCount = keyboardHotkeyEntries.Count( e =>
                    e.Hotkey != null && e.Hotkey.Key == virtualKey.Key && e.Hotkey.Mouse == MouseOptions.None &&
                    ModifierIncludesShift( e.Hotkey.Modifier ) );

                virtualKey.LeftAltModifierBindCount = keyboardHotkeyEntries.Count( e =>
                    e.Hotkey != null && e.Hotkey.Key == virtualKey.Key && e.Hotkey.Mouse == MouseOptions.None &&
                    ModifierIncludesAnyAlt( e.Hotkey.Modifier ) );

                virtualKey.IsSelected = selectedKey != Key.None && virtualKey.Key == selectedKey;

                if ( keyEntries.TryGetValue( virtualKey.Key, out List<HotkeyEntry> entries ) && entries.Count > 0 )
                {
                    List<HotkeyEntry> tabEntries = FilterHotkeyEntriesForVirtualTab( entries, VirtualKeyboardTabIndex )
                        .OrderBy( e => e.Name )
                        .ToList();

                    if ( tabEntries.Count > 0 )
                    {
                        virtualKey.TooltipText = string.Join( Environment.NewLine,
                            tabEntries.Select( e => $"{e.Hotkey} -> {GetVirtualBindLabel( e )}" ) );
                    }
                    else
                    {
                        virtualKey.TooltipText = "Nessun bind";
                    }
                }
                else
                {
                    virtualKey.TooltipText = "Nessun bind";
                }
            }

            UpdateVirtualKeyboardModifierVisualState();

            UpdateVirtualMouseState();
        }

        private void UpdateVirtualMouseState()
        {
            if ( MouseButtons == null )
            {
                return;
            }

            Dictionary<MouseOptions, int> mouseCounts = Items
                .Where( i => i.Children != null )
                .SelectMany( i => i.Children )
                .Select( entry => entry.Hotkey )
                .Where( hk => hk != null && hk.Mouse != MouseOptions.None )
                .GroupBy( hk => hk.Mouse )
                .ToDictionary( g => g.Key, g => g.Count() );

            Dictionary<MouseOptions, List<HotkeyEntry>> mouseEntries = Items
                .Where( i => i.Children != null )
                .SelectMany( i => i.Children )
                .Where( entry => entry.Hotkey != null && entry.Hotkey.Mouse != MouseOptions.None )
                .GroupBy( entry => entry.Hotkey.Mouse )
                .ToDictionary( g => g.Key, g => g.OrderBy( e => e.Name ).ToList() );

            MouseOptions selectedMouse = SelectedItem?.Hotkey?.Mouse ?? MouseOptions.None;

            foreach ( HotkeyMouseButtonViewModel button in MouseButtons )
            {
                button.BindCount = mouseCounts.TryGetValue( button.Mouse, out int count ) ? count : 0;
                button.IsSelected = selectedMouse != MouseOptions.None && button.Mouse == selectedMouse;

                if ( mouseEntries.TryGetValue( button.Mouse, out List<HotkeyEntry> entries ) && entries.Count > 0 )
                {
                    button.TooltipText = string.Join( Environment.NewLine,
                        entries.Select( e => $"{e.Hotkey} -> {GetVirtualBindLabel( e )}" ) );
                }
                else
                {
                    button.TooltipText = "Nessun bind";
                }
            }
        }

        private static string GetVirtualBindLabel( HotkeyEntry entry )
        {
            if ( entry is MacroEntry )
            {
                return $"{entry.Name} (SCRIPT)";
            }

            return entry.Name;
        }
    }
}