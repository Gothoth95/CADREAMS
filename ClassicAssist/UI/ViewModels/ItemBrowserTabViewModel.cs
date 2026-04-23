using System;
using System.ComponentModel;
using System.Collections.ObjectModel;
using System.Drawing;
using System.Linq;
using System.Windows.Data;
using System.Windows.Input;
using ClassicAssist.Misc;
using ClassicAssist.Shared.UI;
using ClassicAssist.UO.Data;

namespace ClassicAssist.UI.ViewModels
{
    public class ItemBrowserTabViewModel : BaseViewModel
    {
        private ICommand _loadItemsCommand;
        private string _nameFilter = string.Empty;
        private int _rangeEnd = 256;
        private int _rangeStart;
        private string _status = "Pronto";

        private ICollectionView _itemsView;

        public ItemBrowserTabViewModel()
        {
            _itemsView = CollectionViewSource.GetDefaultView( Items );
            _itemsView.Filter = FilterByName;
        }

        public ObservableCollection<ItemGraphicEntryViewModel> Items { get; } =
            new ObservableCollection<ItemGraphicEntryViewModel>();

        public ICollectionView ItemsView
        {
            get => _itemsView;
            set => SetProperty( ref _itemsView, value );
        }

        public ICommand LoadItemsCommand =>
            _loadItemsCommand ?? ( _loadItemsCommand = new RelayCommand( LoadItems, o => true ) );

        public string NameFilter
        {
            get => _nameFilter;
            set
            {
                SetProperty( ref _nameFilter, value );
                ItemsView?.Refresh();
                UpdateStatus();
            }
        }

        public int RangeEnd
        {
            get => _rangeEnd;
            set => SetProperty( ref _rangeEnd, value );
        }

        public int RangeStart
        {
            get => _rangeStart;
            set => SetProperty( ref _rangeStart, value );
        }

        public string Status
        {
            get => _status;
            set => SetProperty( ref _status, value );
        }

        private void LoadItems( object _ )
        {
            try
            {
                int start = Math.Max( 0, RangeStart );
                int end = Math.Max( start, RangeEnd );
                bool hasSearchQuery = !string.IsNullOrWhiteSpace( NameFilter );

                // Keep UI responsive: cap loaded entries per request unless user is actively searching.
                if ( !hasSearchQuery && end - start > 1000 )
                {
                    end = start + 1000;
                }

                Items.Clear();

                for ( int itemId = start; itemId <= end; itemId++ )
                {
                    StaticTile tile = TileData.GetStaticTile( itemId );

                    if ( tile.Name == null || tile.Name.Equals( "unknown", StringComparison.OrdinalIgnoreCase ) )
                    {
                        continue;
                    }

                    Bitmap bitmap = Art.GetStatic( itemId );

                    ItemGraphicEntryViewModel entry = new ItemGraphicEntryViewModel
                    {
                        ItemID = itemId,
                        Name = tile.Name,
                        Image = bitmap?.ToImageSource()
                    };

                    Items.Add( entry );
                }

                ItemsView?.Refresh();
                UpdateStatus( start, end );
            }
            catch ( Exception ex )
            {
                Status = $"Errore caricamento item: {ex.Message}";
            }
        }

        private bool FilterByName( object obj )
        {
            if ( !( obj is ItemGraphicEntryViewModel entry ) )
            {
                return false;
            }

            if ( string.IsNullOrWhiteSpace( NameFilter ) )
            {
                return true;
            }

            string query = NameFilter.Trim();
            string queryLower = query.ToLowerInvariant();

            // Name match (tiledata name via TileData.GetStaticTile)
            if ( entry.Name?.IndexOf( query, StringComparison.OrdinalIgnoreCase ) >= 0 )
            {
                return true;
            }

            // Decimal ItemID match
            string itemIdDecimal = entry.ItemID.ToString();

            if ( itemIdDecimal.Contains( query ) )
            {
                return true;
            }

            // Hex Graphic match: supports 0x0EED and 0EED
            string itemIdHex = entry.ItemID.ToString( "X4" );
            string itemIdHexPrefixed = $"0x{itemIdHex}".ToLowerInvariant();

            return itemIdHex.ToLowerInvariant().Contains( queryLower ) || itemIdHexPrefixed.Contains( queryLower );
        }

        private void UpdateStatus( int? start = null, int? end = null )
        {
            int visible = ItemsView?.Cast<object>().Count() ?? 0;
            int total = Items.Count;

            if ( start.HasValue && end.HasValue )
            {
                bool hasSearchQuery = !string.IsNullOrWhiteSpace( NameFilter );
                string capInfo = hasSearchQuery ? " (ricerca completa)" : string.Empty;
                Status = $"Caricati {total} item ({start} - {end}), visibili {visible}.{capInfo}";
                return;
            }

            Status = $"Item visibili {visible} su {total}.";
        }
    }
}
