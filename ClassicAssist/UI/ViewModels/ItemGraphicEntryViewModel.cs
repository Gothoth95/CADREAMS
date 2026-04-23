using System.Windows.Media;
using ClassicAssist.Shared.UI;

namespace ClassicAssist.UI.ViewModels
{
    public class ItemGraphicEntryViewModel : SetPropertyNotifyChanged
    {
        private ImageSource _image;
        private string _name;

        public ImageSource Image
        {
            get => _image;
            set => SetProperty( ref _image, value );
        }

        public int ItemID { get; set; }

        public string Name
        {
            get => _name;
            set => SetProperty( ref _name, value );
        }
    }
}
