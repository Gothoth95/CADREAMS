using Assistant;
using ClassicAssist.Data.Macros.Commands;
using ClassicAssist.Data.Targeting;
using ClassicAssist.Shared.Resources;
using ClassicAssist.UO;
using ClassicAssist.UO.Data;
using ClassicAssist.UO.Network.Packets;
using ClassicAssist.UO.Objects;
using UOC = ClassicAssist.UO.Commands;

namespace ClassicAssist.Data.Hotkeys.Commands
{
    public class Targeting
    {
        [HotkeyCommand( Name = "Set Enemy", Category = "Targeting" )]
        public class SetEnemyCommand : HotkeyCommand
        {
            public override void Execute()
            {
                TargetManager manager = TargetManager.GetInstance();

                Entity mobile = manager.PromptTarget();

                if ( mobile == null )
                {
                    return;
                }

                manager.SetEnemy( mobile );
                Engine.SendPacketToServer( new LookRequest( mobile.Serial ) );
            }
        }

        [HotkeyCommand( Name = "Set Friend", Category = "Targeting" )]
        public class SetFriendCommand : HotkeyCommand
        {
            public override void Execute()
            {
                TargetManager manager = TargetManager.GetInstance();

                Entity mobile = manager.PromptTarget();

                if ( mobile == null )
                {
                    return;
                }

                manager.SetFriend( mobile );
                Engine.SendPacketToServer( new LookRequest( mobile.Serial ) );
            }
        }

        [HotkeyCommand( Name = "Set Last Target", Category = "Targeting" )]
        public class SetLastTargetCommand : HotkeyCommand
        {
            public override void Execute()
            {
                TargetManager manager = TargetManager.GetInstance();

                Entity entity = manager.PromptTarget();

                if ( entity == null )
                {
                    return;
                }

                manager.SetLastTarget( entity );

                if ( UOMath.IsMobile( entity.Serial ) )
                {
                    Engine.SendPacketToServer( new LookRequest( entity.Serial ) );
                }
            }
        }

        [HotkeyCommand( Name = "Target Enemy", Category = "Targeting" )]
        public class TargetEnemyCommand : HotkeyCommand
        {
            public override void Execute()
            {
                TargetCommands.Target( "enemy", Options.CurrentOptions.RangeCheckLastTarget,
                    Options.CurrentOptions.QueueLastTarget );
            }
        }

        [HotkeyCommand( Name = "Target Last", Category = "Targeting" )]
        public class TargetLastCommand : HotkeyCommand
        {
            public override void Execute()
            {
                if ( Options.CurrentOptions.SmartTargetOption == SmartTargetOption.None )
                {
                    TargetCommands.Target( "last", Options.CurrentOptions.RangeCheckLastTarget,
                        Options.CurrentOptions.QueueLastTarget );
                }
                else
                {
                    if ( Engine.TargetExists )
                    {
                        if ( Options.CurrentOptions.SmartTargetOption.HasFlag( SmartTargetOption.Friend ) &&
                             Engine.TargetFlags == TargetFlags.Beneficial && AliasCommands.FindAlias( "friend" ) )
                        {
                            TargetCommands.Target( "friend", Options.CurrentOptions.RangeCheckLastTarget,
                                Options.CurrentOptions.QueueLastTarget );
                            return;
                        }

                        if ( Options.CurrentOptions.SmartTargetOption.HasFlag( SmartTargetOption.Enemy ) &&
                             Engine.TargetFlags == TargetFlags.Harmful && AliasCommands.FindAlias( "enemy" ) )
                        {
                            TargetCommands.Target( "enemy", Options.CurrentOptions.RangeCheckLastTarget,
                                Options.CurrentOptions.QueueLastTarget );
                            return;
                        }
                    }

                    TargetCommands.Target( "last", Options.CurrentOptions.RangeCheckLastTarget,
                        Options.CurrentOptions.QueueLastTarget );
                }
            }
        }

        [HotkeyCommand( Name = "Target Friend", Category = "Targeting" )]
        public class TargetFriendCommand : HotkeyCommand
        {
            public override void Execute()
            {
                TargetCommands.Target( "friend", Options.CurrentOptions.RangeCheckLastTarget,
                    Options.CurrentOptions.QueueLastTarget );
            }
        }

        [HotkeyCommand( Name = "Target Self", Category = "Targeting" )]
        public class TargetSelfCommand : HotkeyCommand
        {
            public override void Execute()
            {
                TargetCommands.Target( "self", Options.CurrentOptions.RangeCheckLastTarget,
                    Options.CurrentOptions.QueueLastTarget );
            }
        }

        [HotkeyCommand( Name = "Clear Target Queue", Category = "Targeting" )]
        public class ClearTargetQueueCommand : HotkeyCommand
        {
            public override void Execute()
            {
                TargetCommands.ClearTargetQueue();
            }
        }

        [HotkeyCommand( Name = "Attack Last", Category = "Targeting" )]
        public class AttackLastCommand : HotkeyCommand
        {
            public override void Execute()
            {
                ActionCommands.Attack( "last" );
            }
        }

        [HotkeyCommand( Name = "Attack Enemy", Category = "Targeting" )]
        public class AttackEnemyCommand : HotkeyCommand
        {
            public override void Execute()
            {
                ActionCommands.Attack( "enemy" );
            }
        }

        [HotkeyCommand( Name = "Target Next PvP Enemy", Category = "Targeting" )]
        public class TargetNextPvpEnemyCommand : HotkeyCommand
        {
            public override void Execute()
            {
                // PvP-oriented cycle: skips invulnerable by notoriety and avoids monster bodies.
                TargetManager.GetInstance().GetEnemy(
                    BuildTargetNextPvpNotorietyFlags(),
                    TargetBodyType.Both,
                    TargetDistance.Next,
                    TargetFriendType.None );
            }

            private static TargetNotoriety BuildTargetNextPvpNotorietyFlags()
            {
                TargetNotoriety flags = TargetNotoriety.None;

                if ( Options.CurrentOptions.TargetNextPvpIncludeInnocent )
                {
                    flags |= TargetNotoriety.Innocent;
                }

                if ( Options.CurrentOptions.TargetNextPvpIncludeGray )
                {
                    flags |= TargetNotoriety.Gray;
                }

                if ( Options.CurrentOptions.TargetNextPvpIncludeCriminal )
                {
                    flags |= TargetNotoriety.Criminal;
                }

                if ( Options.CurrentOptions.TargetNextPvpIncludeEnemy )
                {
                    flags |= TargetNotoriety.Enemy;
                }

                if ( Options.CurrentOptions.TargetNextPvpIncludeMurderer )
                {
                    flags |= TargetNotoriety.Murderer;
                }

                if ( flags == TargetNotoriety.None )
                {
                    flags = TargetNotoriety.Innocent | TargetNotoriety.Gray | TargetNotoriety.Criminal |
                            TargetNotoriety.Enemy | TargetNotoriety.Murderer;
                }

                return flags;
            }
        }

        [HotkeyCommand( Name = "Target Next Friendly", Category = "Targeting" )]
        public class TargetNextFriendlyCommand : HotkeyCommand
        {
            public override void Execute()
            {
                TargetManager.GetInstance().GetFriendlyNext( TargetBodyType.Both );
            }
        }

        [HotkeyCommand( Name = "Show Next Target In Queue", Category = "Targeting" )]
        public class ShowNextTargetQueue : HotkeyCommand
        {
            public override void Execute()
            {
                if ( !Options.CurrentOptions.QueueLastTarget )
                {
                    UOC.SystemMessage( Strings.Target_queue_is_not_enabled___ );
                    return;
                }

                object nextTarget = Engine.LastTargetQueue.Peek()?.Object;

                switch ( nextTarget )
                {
                    case string targetAlias:
                        MsgCommands.HeadMsg( string.Format( Strings.Next_Target___0_, targetAlias ),
                            Engine.Player?.Serial );
                        break;
                    case int targetSerial:
                    {
                        Mobile entity = Engine.Mobiles.GetMobile( targetSerial );

                        MsgCommands.HeadMsg(
                            string.Format( Strings.Next_Target___0_,
                                $"0x{targetSerial:x} - {entity?.Name ?? "Unknown"}" ), Engine.Player?.Serial );
                        break;
                    }
                }
            }
        }

        [HotkeyCommand( Name = "Attack Enemy + Rehue Target", Category = "Targeting" )]
        public class AttackEnemyRehueTarget : HotkeyCommand
        {
            public override void Execute()
            {
                int serial = Engine.Player?.EnemyTargetSerial ?? 0;

                if ( serial == 0 )
                {
                    ActionCommands.Attack( "enemy" );
                    serial = Engine.Player?.EnemyTargetSerial ?? 0;
                }

                if ( serial == 0 )
                {
                    return;
                }

                Mobile mobile = Engine.Mobiles.GetMobile( serial );

                if ( mobile == null )
                {
                    return;
                }

                // Perform the attack first, then force the custom rehue so it wins visually.
                ActionCommands.Attack( serial );

                int rehue = Options.CurrentOptions.AttackTargetRehueHue;
                Engine.RehueList.RemoveByType( RehueType.Enemies, true );
                Engine.RehueList.Add( serial, rehue, RehueType.Enemies );

                // Force immediate visual refresh in all common packet shapes.
                Engine.RehueList.CheckMobileIncoming( mobile, mobile.Equipment );
                Engine.RehueList.CheckMobileUpdate( mobile );
                Engine.RehueList.CheckMobileMoving( mobile );

                string name = mobile.Name?.Trim() ?? "Unknown";
                MsgCommands.HeadMsg( $"[Attack] {name}", serial, rehue );

                if ( Engine.Player != null )
                {
                    MsgCommands.HeadMsg( $"[Attack] {name}", Engine.Player.Serial, rehue );
                }
            }
        }
    }
}