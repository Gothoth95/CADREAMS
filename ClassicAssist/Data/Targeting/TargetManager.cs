using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Assistant;
using ClassicAssist.Data.Macros;
using ClassicAssist.Data.Macros.Commands;
using ClassicAssist.Data.Regions;
using ClassicAssist.Shared.Resources;
using ClassicAssist.UO;
using ClassicAssist.UO.Data;
using ClassicAssist.UO.Network.Packets;
using ClassicAssist.UO.Objects;
using Newtonsoft.Json;
using UOC = ClassicAssist.UO.Commands;

namespace ClassicAssist.Data.Targeting
{
    public class TargetManager
    {
        public delegate void dTargetChanged( int newSerial, int oldSerial );

        private const int MAX_DISTANCE = 18;
        private const int DefaultTargetHeadHue = 34;

        /// <summary>Packet body ids are unsigned 16-bit; normalize for comparisons against Bodies.json.</summary>
        private static int NormalizeMobileBodyId( int bodyId ) => bodyId & 0xFFFF;

        private static int TargetHeadMessageHue( Mobile mobile )
        {
#if CAPVP
            return DefaultTargetHeadHue;
#else
            return mobile != null ? Options.CurrentOptions.GetNotorietyHue( mobile.Notoriety ) : DefaultTargetHeadHue;
#endif
        }
        private static TargetManager _instance;
        private static readonly object _lock = new object();
        private static readonly List<Mobile> _ignoreList = new List<Mobile>();

        /// <summary>
        ///     Default creature names for ambient spawns that share Animal Form / Necro / Mysticism bodies listed in
        ///     Bodies.json. Players keep their character name, so they are not filtered. Not shown in UI.
        /// </summary>
        private static readonly HashSet<string> TransformationSpawnNpcNames =
            new HashSet<string>( StringComparer.OrdinalIgnoreCase )
            {
                // Necro / forms
                "a horrific beast",
                "a wraith",
                "a lich",
                "a vampire",
                "a reaper",
                // Ostard / llama / wolf (Animal Form bodies)
                "a desert ostard",
                "a forest ostard",
                "a frenzied ostard",
                "a llama",
                "a grey wolf",
                "a gray wolf",
                "a wolf",
                "a timber wolf",
                "a dire wolf",
                "a hell hound",
                // Other transformation graphics in Bodies.json
                "a goblin",
                "a savage",
                "a savage warrior",
                "a savage shaman",
                "a tribal chief",
                // Italian (common freeshard / client strings)
                "un lama",
                "un lupo",
                "un lupo grigio",
                "un ostard",
                "un ostard del deserto",
                "un ostard della foresta",
                "un ostard frenetico",
                "un goblin",
                "un lich",
                "un vampiro",
                "un segugio infernale"
            };

        private readonly HashSet<int> _transformationBodyGraphics;

        private TargetManager()
        {
            string dataPath = Path.Combine( Engine.StartupPath ?? Environment.CurrentDirectory, "Data" );

            BodyData = JsonConvert
                .DeserializeObject<TargetBodyData[]>( File.ReadAllText( Path.Combine( dataPath, "Bodies.json" ) ) )
                .ToList();

            _transformationBodyGraphics = new HashSet<int>(
                BodyData.Where( bd => bd.BodyType == TargetBodyType.Transformation ).Select( bd => bd.Graphic ) );
        }

        public List<TargetBodyData> BodyData { get; set; }

        /// <summary>
        ///     Skips world mobs that use the same body id as PvP transformation entries but still have a default NPC name.
        /// </summary>
        private bool IsAmbientSpawnNpcForTransformationBody( Mobile m )
        {
            if ( m == null )
            {
                return false;
            }

            if ( !_transformationBodyGraphics.Contains( NormalizeMobileBodyId( m.ID ) ) )
            {
                return false;
            }

            string name = m.Name?.Trim();

            if ( string.IsNullOrEmpty( name ) )
            {
                return false;
            }

            return TransformationSpawnNpcNames.Contains( name );
        }

        public static event dTargetChanged EnemyChangedEvent;
        public static event dTargetChanged FriendChangedEvent;
        public static event dTargetChanged LastTargetChangedEvent;

        public void SetEnemy( Entity m )
        {
            if ( !UOMath.IsMobile( m.Serial ) )
            {
                return;
            }

            int previousEnemySerial = Engine.Player?.EnemyTargetSerial ?? 0;

            Mobile mobile = m as Mobile ?? Engine.Mobiles.GetMobile( m.Serial );
            int hue = TargetHeadMessageHue( mobile );
            string targetName = m.Name?.Trim() ?? "Unknown";

            if ( !MacroManager.QuietMode )
            {
                if ( mobile != null && mobile.Notoriety == Notoriety.Innocent )
                {
                    Region guardRegion = mobile.GetRegion();

                    if ( guardRegion != null && guardRegion.Attributes.HasFlag( RegionAttributes.Guarded ) )
                    {
                        string warn = Options.CurrentOptions.TargetNextInnocentGuardWarningMessage;

                        if ( !string.IsNullOrWhiteSpace( warn ) )
                        {
                            int warnHue = Options.CurrentOptions.TargetNextInnocentGuardWarningHue;
                            MsgCommands.HeadMsg( warn, m.Serial, warnHue );

                            if ( Engine.Player != null )
                            {
                                MsgCommands.HeadMsg( warn, Engine.Player.Serial, warnHue );
                            }
                        }
                    }
                }

                string targetMessage = BuildTargetMessage( Options.CurrentOptions.EnemyTargetMessage, targetName );
                string selfMessage = BuildTargetMessage( Options.CurrentOptions.EnemyTargetSelfMessage, targetName );

                if ( !string.IsNullOrWhiteSpace( targetMessage ) )
                {
                    MsgCommands.HeadMsg( targetMessage, m.Serial, hue );
                }

                if ( !string.IsNullOrWhiteSpace( selfMessage ) && Engine.Player != null )
                {
                    MsgCommands.HeadMsg( selfMessage, Engine.Player.Serial, hue );
                }
            }

            if ( m.Serial != Engine.Player.EnemyTargetSerial )
            {
                if ( previousEnemySerial != 0 && previousEnemySerial != m.Serial )
                {
                    // When cycling target, remove old attack rehue and force visual reset.
                    Engine.RehueList.RemoveByType( RehueType.Enemies, true );
                }

                EnemyChangedEvent?.Invoke( m.Serial, Engine.Player.EnemyTargetSerial );
                LastTargetChangedEvent?.Invoke( m.Serial, Engine.Player.LastTargetSerial );
            }

            Engine.Player.LastTargetSerial = m.Serial;
            Engine.Player.EnemyTargetSerial = m.Serial;
            Engine.SendPacketToClient( new ChangeCombatant( m.Serial ) );
        }

        public void SetFriend( Entity m )
        {
            if ( !UOMath.IsMobile( m.Serial ) )
            {
                return;
            }

            Mobile mobile = m as Mobile ?? Engine.Mobiles.GetMobile( m.Serial );
            int hueOnFriend = Options.CurrentOptions.FriendTargetMessageHue;
            int hueOnSelf = Options.CurrentOptions.FriendTargetSelfMessageHue;

            string targetName = m.Name?.Trim() ?? "Unknown";

            if ( !MacroManager.QuietMode )
            {
                string onFriend =
                    BuildMobileTargetMessage( Options.CurrentOptions.FriendTargetMessage, mobile, targetName );
                string onSelf =
                    BuildMobileTargetMessage( Options.CurrentOptions.FriendTargetSelfMessage, mobile, targetName );

                if ( !string.IsNullOrWhiteSpace( onFriend ) )
                {
                    MsgCommands.HeadMsg( onFriend, m.Serial, hueOnFriend );
                }

                if ( !string.IsNullOrWhiteSpace( onSelf ) && Engine.Player != null )
                {
                    MsgCommands.HeadMsg( onSelf, Engine.Player.Serial, hueOnSelf );
                }
            }

            if ( m.Serial != Engine.Player.FriendTargetSerial )
            {
                MsgCommands.HeadMsg( $"Target: {targetName}", m.Serial, hueOnFriend );
                FriendChangedEvent?.Invoke( m.Serial, Engine.Player.FriendTargetSerial );
                LastTargetChangedEvent?.Invoke( m.Serial, Engine.Player.LastTargetSerial );
            }

            Engine.Player.LastTargetSerial = m.Serial;
            Engine.Player.FriendTargetSerial = m.Serial;
            Engine.SendPacketToClient( new ChangeCombatant( m.Serial ) );
        }

        public void SetLastTarget( Entity m )
        {
            Mobile mobile = UOMath.IsMobile( m.Serial ) ? ( m as Mobile ?? Engine.Mobiles.GetMobile( m.Serial ) ) : null;
            int hue = TargetHeadMessageHue( mobile );

            if ( m.Serial != Engine.Player.LastTargetSerial )
            {
                LastTargetChangedEvent?.Invoke( m.Serial, Engine.Player.LastTargetSerial );
            }

            Engine.Player.LastTargetSerial = m.Serial;

            if ( !UOMath.IsMobile( m.Serial ) )
            {
                return;
            }

            if ( !MacroManager.QuietMode )
            {
                MsgCommands.HeadMsg( Options.CurrentOptions.LastTargetMessage, m.Serial, hue );
            }

            MsgCommands.HeadMsg( $"Target: {m.Name?.Trim() ?? "Unknown"}", m.Serial, hue );
            Engine.SendPacketToClient( new ChangeCombatant( m.Serial ) );
        }

        public Mobile GetClosestMobile( IEnumerable<Notoriety> notoriety, TargetBodyType bodyType = TargetBodyType.Any,
            TargetFriendType friendType = TargetFriendType.Include,
            TargetInfliction inflictionType = TargetInfliction.Any, int maxDistance = -1 )
        {
            Mobile mobile;

            Func<int, bool> bodyTypePredicate;

            switch ( bodyType )
            {
                case TargetBodyType.Any:
                    bodyTypePredicate = i => true;
                    break;
                case TargetBodyType.Humanoid:
                    bodyTypePredicate = i =>
                        BodyData.Where( bd => bd.BodyType == TargetBodyType.Humanoid ).Select( bd => bd.Graphic )
                            .Contains( i );
                    break;
                case TargetBodyType.Transformation:
                    bodyTypePredicate = i =>
                        BodyData.Where( bd => bd.BodyType == TargetBodyType.Transformation ).Select( bd => bd.Graphic )
                            .Contains( i );
                    break;
                case TargetBodyType.Both:
                    bodyTypePredicate = i =>
                        BodyData.Where( bd =>
                                bd.BodyType == TargetBodyType.Humanoid || bd.BodyType == TargetBodyType.Transformation )
                            .Select( bd => bd.Graphic ).Contains( i );
                    break;
                default:
                    throw new ArgumentOutOfRangeException( nameof( bodyType ), bodyType, null );
            }

            if ( friendType == TargetFriendType.Only )
            {
                mobile = Engine.Mobiles.SelectEntities( m =>
                        MobileCommands.InFriendList( m.Serial ) &&
                        bodyTypePredicate( NormalizeMobileBodyId( m.ID ) ) &&
                        !IsAmbientSpawnNpcForTransformationBody( m ) &&
                        ( !Options.CurrentOptions.GetFriendEnemyUsesIgnoreList ||
                          !ObjectCommands.IgnoreList.Contains( m.Serial ) ) && m.Serial != Engine.Player?.Serial &&
                        ( maxDistance == -1 || m.Distance <= maxDistance ) ).OrderBy( m => m.Distance )
                    .ByInflication( inflictionType ).FirstOrDefault();
            }
            else
            {
                mobile = Engine.Mobiles.SelectEntities( m =>
                        notoriety.Contains( m.Notoriety ) && m.Distance < MAX_DISTANCE &&
                        bodyTypePredicate( NormalizeMobileBodyId( m.ID ) ) &&
                        !IsAmbientSpawnNpcForTransformationBody( m ) &&
                        ( friendType == TargetFriendType.Include || !MobileCommands.InFriendList( m.Serial ) ) &&
                        ( !Options.CurrentOptions.GetFriendEnemyUsesIgnoreList ||
                          !ObjectCommands.IgnoreList.Contains( m.Serial ) ) && m.Serial != Engine.Player?.Serial &&
                        ( maxDistance == -1 || m.Distance <= maxDistance ) ).OrderBy( m => m.Distance )
                    .ByInflication( inflictionType )?.FirstOrDefault();
            }

            return mobile;
        }

        public Mobile GetNextMobile( IEnumerable<Notoriety> notoriety, TargetBodyType bodyType = TargetBodyType.Any,
            int distance = MAX_DISTANCE, TargetFriendType friendType = TargetFriendType.Include,
            TargetInfliction inflictionType = TargetInfliction.Any, bool reverse = false, Mobile previousMobile = null )
        {
            bool looped = false;

            while ( true )
            {
                Mobile[] mobiles;

                Func<int, bool> bodyTypePredicate;

                switch ( bodyType )
                {
                    case TargetBodyType.Any:
                        bodyTypePredicate = i => true;
                        break;
                    case TargetBodyType.Humanoid:
                        bodyTypePredicate = i =>
                            BodyData.Where( bd => bd.BodyType == TargetBodyType.Humanoid ).Select( bd => bd.Graphic )
                                .Contains( i );
                        break;
                    case TargetBodyType.Transformation:
                        bodyTypePredicate = i =>
                            BodyData.Where( bd => bd.BodyType == TargetBodyType.Transformation )
                                .Select( bd => bd.Graphic ).Contains( i );
                        break;
                    case TargetBodyType.Both:
                        bodyTypePredicate = i =>
                            BodyData.Where( bd =>
                                    bd.BodyType == TargetBodyType.Humanoid ||
                                    bd.BodyType == TargetBodyType.Transformation )
                                .Select( bd => bd.Graphic ).Contains( i );
                        break;
                    default:
                        throw new ArgumentOutOfRangeException( nameof( bodyType ), bodyType, null );
                }

                if ( previousMobile != null )
                {
                    _ignoreList.Clear();
                }

                if ( friendType == TargetFriendType.Only )
                {
                    //Notoriety, bodyType ignored
                    mobiles = Engine.Mobiles.SelectEntities( m =>
                        m.Distance <= distance && MobileCommands.InFriendList( m.Serial ) &&
                        bodyTypePredicate( NormalizeMobileBodyId( m.ID ) ) &&
                        !IsAmbientSpawnNpcForTransformationBody( m ) && !_ignoreList.Contains( m ) &&
                        ( !Options.CurrentOptions.GetFriendEnemyUsesIgnoreList ||
                          !ObjectCommands.IgnoreList.Contains( m.Serial ) ) && m.Serial != Engine.Player?.Serial &&
                        m.Distance <= distance );
                }
                else
                {
                    mobiles = Engine.Mobiles.SelectEntities( m =>
                        notoriety.Contains( m.Notoriety ) && m.Distance <= distance &&
                        bodyTypePredicate( NormalizeMobileBodyId( m.ID ) ) &&
                        !IsAmbientSpawnNpcForTransformationBody( m ) &&
                        !_ignoreList.Contains( m ) &&
                        ( friendType == TargetFriendType.Include || !MobileCommands.InFriendList( m.Serial ) ) &&
                        ( !Options.CurrentOptions.GetFriendEnemyUsesIgnoreList ||
                          !ObjectCommands.IgnoreList.Contains( m.Serial ) ) && m.Serial != Engine.Player?.Serial );
                }

                if ( previousMobile != null )
                {
                    mobiles = mobiles.Where( m => m.Serial != previousMobile.Serial && m.Serial != Engine.Player?.Serial ).OrderBy( m => m.Distance ).ToArray();

                    if ( mobiles.Length == 0 )
                    {
                        mobiles = new[] { previousMobile };
                    }
                }

                if ( reverse )
                {
                    mobiles = mobiles.Reverse().ToArray();
                }

                mobiles = mobiles.ByInflication( inflictionType );

                if ( mobiles == null || mobiles.Length == 0 )
                {
                    _ignoreList.Clear();

                    if ( looped )
                    {
                        return null;
                    }

                    looped = true;
                    continue;
                }

                Mobile mobile = mobiles.FirstOrDefault();
                _ignoreList.Add( mobile );
                return mobile;
            }
        }

        public Entity PromptTarget()
        {
            int serial = UOC.GetTargetSerialAsync( Strings.Target_object___ ).Result;

            if ( serial == 0 )
            {
                UOC.SystemMessage( Strings.Invalid_or_unknown_object_id, true );
                return null;
            }

            Entity entity = UOMath.IsMobile( serial )
                ? (Entity) Engine.Mobiles.GetMobile( serial )
                : Engine.Items.GetItem( serial );

            if ( entity != null )
            {
                return entity;
            }

            UOC.SystemMessage( UOMath.IsMobile( serial ) ? Strings.Mobile_not_found___ : Strings.Cannot_find_item___,
                true );

            return null;
        }

        public static TargetManager GetInstance()
        {
            // ReSharper disable once InvertIf
            if ( _instance == null )
            {
                lock ( _lock )
                {
                    if ( _instance != null )
                    {
                        return _instance;
                    }

                    _instance = new TargetManager();
                    return _instance;
                }
            }

            return _instance;
        }

        public bool GetEnemy( TargetNotoriety notoFlags, TargetBodyType bodyType, TargetDistance targetDistance,
            TargetFriendType friendType = TargetFriendType.None, TargetInfliction inflictionType = TargetInfliction.Any,
            int maxDistance = -1 )
        {
            Mobile m = GetMobile( notoFlags, bodyType, targetDistance, friendType, inflictionType,
                targetDistance == TargetDistance.Nearest ? AliasCommands.GetAlias( "enemy" ) : 0, maxDistance );

            if ( m == null )
            {
                return false;
            }

            SetEnemy( m );
            return true;
        }

        public bool GetFriend( TargetNotoriety notoFlags, TargetBodyType bodyType, TargetDistance targetDistance,
            TargetFriendType friendType = TargetFriendType.Include,
            TargetInfliction inflictionType = TargetInfliction.Any, int maxDistance = -1 )
        {
            Mobile m = GetMobile( notoFlags, bodyType, targetDistance, friendType, inflictionType,
                targetDistance == TargetDistance.Nearest ? AliasCommands.GetAlias( "friend" ) : 0, maxDistance );

            if ( m == null )
            {
                return false;
            }

            SetFriend( m );
            return true;
        }

        public bool GetFriendlyNext( TargetBodyType bodyType = TargetBodyType.Both, int maxDistance = -1 )
        {
            if ( Engine.Player == null )
            {
                return false;
            }

            if ( maxDistance < 0 )
            {
                maxDistance = MAX_DISTANCE;
            }

            bool includeAlly = Options.CurrentOptions.TargetNextFriendlyIncludeAlly;
            bool includeFriends = Options.CurrentOptions.TargetNextFriendlyIncludeFriends;

            if ( !includeAlly && !includeFriends )
            {
                includeAlly = true;
                includeFriends = true;
            }

            Func<int, bool> bodyTypePredicate;

            switch ( bodyType )
            {
                case TargetBodyType.Any:
                    bodyTypePredicate = i => true;
                    break;
                case TargetBodyType.Humanoid:
                    bodyTypePredicate = i =>
                        BodyData.Where( bd => bd.BodyType == TargetBodyType.Humanoid ).Select( bd => bd.Graphic )
                            .Contains( i );
                    break;
                case TargetBodyType.Transformation:
                    bodyTypePredicate = i =>
                        BodyData.Where( bd => bd.BodyType == TargetBodyType.Transformation )
                            .Select( bd => bd.Graphic ).Contains( i );
                    break;
                case TargetBodyType.Both:
                    bodyTypePredicate = i =>
                        BodyData.Where( bd =>
                                bd.BodyType == TargetBodyType.Humanoid || bd.BodyType == TargetBodyType.Transformation )
                            .Select( bd => bd.Graphic ).Contains( i );
                    break;
                default:
                    throw new ArgumentOutOfRangeException( nameof( bodyType ), bodyType, null );
            }

            Mobile[] candidates = Engine.Mobiles.SelectEntities( m =>
                m.Distance <= maxDistance && bodyTypePredicate( NormalizeMobileBodyId( m.ID ) ) &&
                !IsAmbientSpawnNpcForTransformationBody( m ) &&
                m.Serial != Engine.Player.Serial &&
                ( !Options.CurrentOptions.GetFriendEnemyUsesIgnoreList ||
                  !ObjectCommands.IgnoreList.Contains( m.Serial ) ) &&
                ( ( includeAlly && m.Notoriety == Notoriety.Ally ) ||
                  ( includeFriends && MobileCommands.InFriendList( m.Serial ) ) ) ).OrderBy( m => m.Distance )
                .ByInflication( TargetInfliction.Any );

            if ( candidates == null || candidates.Length == 0 )
            {
                return false;
            }

            int prevSerial = Engine.Player.FriendTargetSerial;
            int idx = Array.FindIndex( candidates, c => c.Serial == prevSerial );
            Mobile next = idx < 0 ? candidates[0] : candidates[( idx + 1 ) % candidates.Length];

            SetFriend( next );
            return true;
        }

        public Mobile GetMobile( TargetNotoriety notoFlags, TargetBodyType bodyType, TargetDistance targetDistance,
            TargetFriendType friendType, TargetInfliction inflictionType, int previousSerial = 0, int maxDistance = -1 )
        {
            Notoriety[] noto = NotoFlagsToArray( notoFlags );

            Mobile m;

            if ( maxDistance == -1 )
            {
                maxDistance = MAX_DISTANCE;
            }

            switch ( targetDistance )
            {
                case TargetDistance.Next:

                    m = GetNextMobile( noto, bodyType, maxDistance, friendType, inflictionType );

                    break;
                case TargetDistance.Nearest:

                    Mobile previousMobile = Engine.Mobiles.GetMobile( previousSerial );

                    if ( previousMobile == null || previousMobile.Distance > MAX_DISTANCE )
                    {
                        m = GetClosestMobile( noto, bodyType, friendType, inflictionType, maxDistance );
                    }
                    else
                    {
                        m = GetNextMobile( noto, bodyType, maxDistance, friendType, inflictionType, false,
                            previousMobile );
                    }

                    break;
                case TargetDistance.Closest:

                    m = GetClosestMobile( noto, bodyType, friendType, inflictionType, maxDistance );

                    break;
                case TargetDistance.Previous:

                    m = GetNextMobile( noto, bodyType, maxDistance, friendType, inflictionType, true );

                    break;
                default:
                    throw new ArgumentOutOfRangeException( nameof( targetDistance ), targetDistance, null );
            }

            return m;
        }

        /// <summary>
        ///     Head message text for a mobile target. If template contains "{" uses String.Format with:
        ///     {0} name, {1} notoriety, {2} serial (hex), {3} distance (tiles), {4} body id (hex), {5} hits, {6} hits max,
        ///     {7} hits percent (0–100).
        ///     Missing mobile uses ? or defaults for slots after {0}.
        /// </summary>
        public static string FormatFriendTargetHeadMessage( int serial )
        {
            Mobile mobile = Engine.Mobiles.GetMobile( serial );

            return BuildMobileTargetMessage( Options.CurrentOptions.FriendTargetMessage, mobile,
                mobile?.Name?.Trim() ?? "Unknown" );
        }

        private static string BuildMobileTargetMessage( string template, Mobile mobile, string nameFallback )
        {
            if ( string.IsNullOrWhiteSpace( template ) )
            {
                return string.Empty;
            }

            string cleanName = string.IsNullOrWhiteSpace( nameFallback ) ? "Unknown" : nameFallback.Trim();

            if ( mobile != null && !string.IsNullOrWhiteSpace( mobile.Name ) )
            {
                cleanName = mobile.Name.Trim();
            }

            if ( !template.Contains( "{" ) )
            {
                return $"{template} {cleanName}".Trim();
            }

            object noto = mobile?.Notoriety.ToString() ?? "?";
            object serialHex = mobile != null ? $"0x{mobile.Serial:x}" : "?";
            int distance = mobile?.Distance ?? -1;
            object idHex = mobile != null ? $"0x{mobile.ID:x}" : "?";
            int hits = mobile?.Hits ?? 0;
            int hitsMax = mobile?.HitsMax ?? 0;
            int hitsPercent = 0;

            if ( mobile != null && mobile.HitsMax > 0 )
            {
                hitsPercent = (int) Math.Round( 100.0 * mobile.Hits / (double) mobile.HitsMax );

                if ( hitsPercent < 0 )
                {
                    hitsPercent = 0;
                }
                else if ( hitsPercent > 100 )
                {
                    hitsPercent = 100;
                }
            }

            try
            {
                return string.Format( template, cleanName, noto, serialHex, distance, idHex, hits, hitsMax,
                    hitsPercent );
            }
            catch ( FormatException )
            {
                return BuildTargetMessage( template, cleanName );
            }
        }

        private static string BuildTargetMessage( string template, string name )
        {
            if ( string.IsNullOrWhiteSpace( template ) )
            {
                return string.Empty;
            }

            string cleanName = string.IsNullOrWhiteSpace( name ) ? "Unknown" : name.Trim();

            if ( template.Contains( "{0}" ) )
            {
                return string.Format( template, cleanName );
            }

            return $"{template} {cleanName}".Trim();
        }

        private static Notoriety[] NotoFlagsToArray( TargetNotoriety notoFlags )
        {
            List<Notoriety> notos = new List<Notoriety>();

            if ( notoFlags.HasFlag( TargetNotoriety.Criminal ) || notoFlags.HasFlag( TargetNotoriety.Any ) )
            {
                notos.Add( Notoriety.Criminal );
            }

            if ( notoFlags.HasFlag( TargetNotoriety.Enemy ) || notoFlags.HasFlag( TargetNotoriety.Any ) )
            {
                notos.Add( Notoriety.Enemy );
            }

            if ( notoFlags.HasFlag( TargetNotoriety.Gray ) || notoFlags.HasFlag( TargetNotoriety.Any ) )
            {
                notos.Add( Notoriety.Attackable );
            }

            if ( notoFlags.HasFlag( TargetNotoriety.Innocent ) || notoFlags.HasFlag( TargetNotoriety.Any ) )
            {
                notos.Add( Notoriety.Innocent );
            }

            if ( notoFlags.HasFlag( TargetNotoriety.Murderer ) || notoFlags.HasFlag( TargetNotoriety.Any ) )
            {
                notos.Add( Notoriety.Murderer );
            }

            if ( notoFlags.HasFlag( TargetNotoriety.Friend ) || notoFlags.HasFlag( TargetNotoriety.Any ) )
            {
                notos.Add( Notoriety.Ally );
            }

            return notos.ToArray();
        }
    }

    public static class MobileEnumerableExtensionMethods
    {
        public static Mobile[] ByInflication( this IEnumerable<Mobile> mobiles, TargetInfliction inflictionType )
        {
            switch ( inflictionType )
            {
                case TargetInfliction.Any:
                    return mobiles.ToArray();
                case TargetInfliction.Lowest:
                    return mobiles.Where( m => m.Hits < m.HitsMax && !m.IsDead ).OrderBy( m => m.Hits ).ToArray();
                case TargetInfliction.Poisoned:
                    return mobiles.Where( m => m.IsPoisoned ).ToArray();
                case TargetInfliction.Mortaled:
                    return mobiles.Where( m => m.IsYellowHits ).ToArray();
                case TargetInfliction.Paralyzed:
                    return mobiles.Where( m => m.IsFrozen ).ToArray();
                case TargetInfliction.Dead:
                    return mobiles.Where( m => m.IsDead ).ToArray();
                case TargetInfliction.Unmounted:
                    return mobiles.Where( m => m.GetLayer( Layer.Mount ) == 0 ).ToArray();
                default:
                    throw new ArgumentOutOfRangeException( nameof( inflictionType ), inflictionType, null );
            }
        }
    }
}