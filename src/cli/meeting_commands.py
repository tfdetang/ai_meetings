"""Meeting management CLI commands"""

import click
import asyncio
from typing import Optional, List

from .main import pass_context, CLIContext
from ..models import MeetingConfig, SpeakingOrder, MeetingStatus, DiscussionStyle, SpeakingLength, AgendaItem
from ..exceptions import ValidationError, NotFoundError, MeetingStateError, PermissionError, AgendaError


@click.group()
def meeting():
    """Manage meetings"""
    pass


@meeting.command('create')
@click.option('--topic', prompt='Meeting topic', help='Topic of the meeting')
@click.option('--agents', prompt='Agent IDs (comma-separated)', help='Comma-separated list of agent IDs')
@click.option('--max-rounds', type=int, help='Maximum number of rounds')
@click.option('--max-length', type=int, help='Maximum message length')
@click.option('--order', 
              type=click.Choice(['sequential', 'random']),
              default='sequential',
              help='Speaking order')
@click.option('--style',
              type=click.Choice(['formal', 'casual', 'debate']),
              default='formal',
              help='Discussion style')
@click.option('--moderator',
              help='Moderator ID (agent ID or "user")')
@pass_context
def create_meeting(ctx: CLIContext, topic: str, agents: str, max_rounds: Optional[int],
                   max_length: Optional[int], order: str, style: str, moderator: Optional[str]):
    """Create a new meeting"""
    
    async def _create():
        try:
            # Parse agent IDs
            agent_ids = [aid.strip() for aid in agents.split(',') if aid.strip()]
            
            if not agent_ids:
                click.echo(click.style('✗ No agent IDs provided', fg='red'), err=True)
                return
            
            # Determine moderator
            moderator_id = None
            moderator_type = None
            
            if moderator:
                if moderator.lower() == 'user':
                    moderator_id = 'user'
                    moderator_type = 'user'
                else:
                    # Verify agent exists
                    try:
                        await ctx.agent_service.get_agent(moderator)
                        moderator_id = moderator
                        moderator_type = 'agent'
                    except NotFoundError:
                        click.echo(click.style(f'✗ Moderator agent not found: {moderator}', fg='red'), err=True)
                        return
            else:
                # Prompt for moderator selection
                click.echo('\nSelect moderator:')
                click.echo('  0. User (you)')
                
                # Load agents to show options
                all_agents = await ctx.agent_service.list_agents()
                agent_options = {a.id: a for a in all_agents if a.id in agent_ids}
                
                for idx, (agent_id, agent) in enumerate(agent_options.items(), 1):
                    click.echo(f'  {idx}. {agent.name} ({agent.role.name})')
                
                choice = click.prompt('Enter choice', type=int, default=0)
                
                if choice == 0:
                    moderator_id = 'user'
                    moderator_type = 'user'
                elif 1 <= choice <= len(agent_options):
                    moderator_id = list(agent_options.keys())[choice - 1]
                    moderator_type = 'agent'
                else:
                    click.echo(click.style('✗ Invalid choice', fg='red'), err=True)
                    return
            
            # Collect initial agenda items
            agenda_items = []
            if click.confirm('\nAdd initial agenda items?', default=False):
                while True:
                    title = click.prompt('Agenda item title (or empty to finish)', default='', show_default=False)
                    if not title:
                        break
                    description = click.prompt('Description', default='')
                    
                    from ..models.meeting import AgendaItem
                    import uuid
                    agenda_item = AgendaItem(
                        id=str(uuid.uuid4()),
                        title=title,
                        description=description
                    )
                    agenda_items.append(agenda_item)
                    click.echo(click.style(f'✓ Added: {title}', fg='green'))
            
            # Collect speaking length preferences
            speaking_length_prefs = {}
            if click.confirm('\nConfigure speaking length preferences?', default=False):
                from ..models.meeting import SpeakingLength
                
                for agent_id in agent_ids:
                    agent = await ctx.agent_service.get_agent(agent_id)
                    click.echo(f'\n{agent.name}:')
                    click.echo('  1. Brief')
                    click.echo('  2. Moderate')
                    click.echo('  3. Detailed')
                    choice = click.prompt('Select preference', type=int, default=2)
                    
                    if choice == 1:
                        speaking_length_prefs[agent_id] = SpeakingLength.BRIEF
                    elif choice == 3:
                        speaking_length_prefs[agent_id] = SpeakingLength.DETAILED
                    else:
                        speaking_length_prefs[agent_id] = SpeakingLength.MODERATE
            
            # Create meeting config
            from ..models.meeting import DiscussionStyle
            config = MeetingConfig(
                max_rounds=max_rounds,
                max_message_length=max_length,
                speaking_order=SpeakingOrder.SEQUENTIAL if order == 'sequential' else SpeakingOrder.RANDOM,
                discussion_style=DiscussionStyle(style),
                speaking_length_preferences=speaking_length_prefs if speaking_length_prefs else None
            )
            
            # Create meeting
            meeting = await ctx.meeting_service.create_meeting(
                topic=topic,
                agent_ids=agent_ids,
                config=config,
                moderator_id=moderator_id,
                moderator_type=moderator_type,
                agenda=agenda_items
            )
            
            click.echo(click.style(f'\n✓ Meeting created successfully!', fg='green'))
            click.echo(f'  ID: {meeting.id}')
            click.echo(f'  Topic: {meeting.topic}')
            click.echo(f'  Participants: {len(meeting.participants)}')
            click.echo(f'  Status: {meeting.status.value}')
            if moderator_id:
                moderator_label = 'User' if moderator_type == 'user' else next(
                    (a.name for a in meeting.participants if a.id == moderator_id), moderator_id
                )
                click.echo(f'  Moderator: {moderator_label}')
            click.echo(f'  Discussion Style: {meeting.config.discussion_style.value}')
            if agenda_items:
                click.echo(f'  Agenda Items: {len(agenda_items)}')
            
        except ValidationError as e:
            click.echo(click.style(f'✗ Validation error: {str(e)}', fg='red'), err=True)
        except NotFoundError as e:
            click.echo(click.style(f'✗ Agent not found: {e.resource_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_create())


@meeting.command('list')
@pass_context
def list_meetings(ctx: CLIContext):
    """List all meetings"""
    
    async def _list():
        try:
            meetings = await ctx.meeting_service.list_meetings()
            
            if not meetings:
                click.echo('No meetings found.')
                return
            
            click.echo(f'\nFound {len(meetings)} meeting(s):\n')
            for mtg in meetings:
                status_color = 'green' if mtg.status == MeetingStatus.ACTIVE else 'yellow' if mtg.status == MeetingStatus.PAUSED else 'red'
                click.echo(f'  • {mtg.topic}')
                click.echo(f'    ID: {mtg.id}')
                click.echo(f'    Status: ' + click.style(mtg.status.value, fg=status_color))
                click.echo(f'    Participants: {len(mtg.participants)}')
                click.echo(f'    Messages: {len(mtg.messages)}')
                click.echo(f'    Round: {mtg.current_round}')
                click.echo(f'    Created: {mtg.created_at.strftime("%Y-%m-%d %H:%M:%S")}')
                click.echo()
                
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_list())


@meeting.command('show')
@click.argument('meeting_id')
@click.option('--messages', is_flag=True, help='Show all messages')
@pass_context
def show_meeting(ctx: CLIContext, meeting_id: str, messages: bool):
    """Show meeting details"""
    
    async def _show():
        try:
            mtg = await ctx.meeting_service.get_meeting(meeting_id)
            
            status_color = 'green' if mtg.status == MeetingStatus.ACTIVE else 'yellow' if mtg.status == MeetingStatus.PAUSED else 'red'
            
            click.echo(f'\nMeeting: {mtg.topic}')
            click.echo(f'  ID: {mtg.id}')
            click.echo(f'  Status: ' + click.style(mtg.status.value, fg=status_color))
            click.echo(f'  Current Round: {mtg.current_round}')
            click.echo(f'  Created: {mtg.created_at.strftime("%Y-%m-%d %H:%M:%S")}')
            click.echo(f'  Updated: {mtg.updated_at.strftime("%Y-%m-%d %H:%M:%S")}')
            
            # Show moderator
            if mtg.moderator_id:
                moderator_label = 'User' if mtg.moderator_type == 'user' else next(
                    (a.name for a in mtg.participants if a.id == mtg.moderator_id), mtg.moderator_id
                )
                click.echo(f'  Moderator: {click.style(moderator_label, fg="magenta", bold=True)} 👑')
            
            click.echo(f'\nConfiguration:')
            click.echo(f'  Speaking Order: {mtg.config.speaking_order.value}')
            click.echo(f'  Discussion Style: {mtg.config.discussion_style.value}')
            if mtg.config.max_rounds:
                click.echo(f'  Max Rounds: {mtg.config.max_rounds}')
            if mtg.config.max_message_length:
                click.echo(f'  Max Message Length: {mtg.config.max_message_length}')
            
            # Show current agenda
            if mtg.agenda:
                click.echo(f'\nCurrent Agenda:')
                for item in mtg.agenda:
                    if not item.completed:
                        click.echo(f'  ○ {click.style(item.title, fg="yellow")}: {item.description}')
            
            click.echo(f'\nParticipants ({len(mtg.participants)}):')
            for p in mtg.participants:
                moderator_badge = ' 👑' if mtg.moderator_id == p.id else ''
                click.echo(f'  • {p.name} ({p.role.name}){moderator_badge}')
            
            click.echo(f'\nMessages: {len(mtg.messages)}')
            
            if messages and mtg.messages:
                click.echo('\n' + '='*60)
                for msg in mtg.messages:
                    speaker_color = 'cyan' if msg.speaker_type == 'user' else 'blue'
                    moderator_badge = ' 👑' if (msg.speaker_type == 'agent' and mtg.moderator_id == msg.speaker_id) or (msg.speaker_type == 'user' and mtg.moderator_type == 'user') else ''
                    
                    click.echo(f'\n[Round {msg.round_number}] ' + click.style(f'{msg.speaker_name}', fg=speaker_color, bold=True) + moderator_badge)
                    click.echo(f'{msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")}')
                    
                    # Highlight @mentions
                    content = msg.content
                    if msg.mentions:
                        for mention in msg.mentions:
                            # Highlight the mention in the content
                            content = content.replace(f'@{mention.mentioned_participant_name}', 
                                                     click.style(f'@{mention.mentioned_participant_name}', fg='green', bold=True))
                    
                    click.echo(f'\n{content}')
                    click.echo('\n' + '-'*60)
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_show())


@meeting.command('start')
@click.argument('meeting_id')
@pass_context
def start_meeting(ctx: CLIContext, meeting_id: str):
    """Start or resume a meeting"""
    
    async def _start():
        try:
            await ctx.meeting_service.start_meeting(meeting_id)
            click.echo(click.style('✓ Meeting started', fg='green'))
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except MeetingStateError as e:
            click.echo(click.style(f'✗ Cannot start meeting: {str(e)}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_start())


@meeting.command('pause')
@click.argument('meeting_id')
@pass_context
def pause_meeting(ctx: CLIContext, meeting_id: str):
    """Pause a meeting"""
    
    async def _pause():
        try:
            await ctx.meeting_service.pause_meeting(meeting_id)
            click.echo(click.style('✓ Meeting paused', fg='green'))
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except MeetingStateError as e:
            click.echo(click.style(f'✗ Cannot pause meeting: {str(e)}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_pause())


@meeting.command('end')
@click.argument('meeting_id')
@click.confirmation_option(prompt='Are you sure you want to end this meeting?')
@pass_context
def end_meeting(ctx: CLIContext, meeting_id: str):
    """End a meeting"""
    
    async def _end():
        try:
            await ctx.meeting_service.end_meeting(meeting_id)
            click.echo(click.style('✓ Meeting ended', fg='green'))
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except MeetingStateError as e:
            click.echo(click.style(f'✗ Cannot end meeting: {str(e)}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_end())


@meeting.command('delete')
@click.argument('meeting_id')
@click.confirmation_option(prompt='Are you sure you want to delete this meeting?')
@pass_context
def delete_meeting(ctx: CLIContext, meeting_id: str):
    """Delete a meeting"""
    
    async def _delete():
        try:
            await ctx.meeting_service.delete_meeting(meeting_id)
            click.echo(click.style('✓ Meeting deleted', fg='green'))
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_delete())


@meeting.command('send')
@click.argument('meeting_id')
@click.option('--message', prompt='Your message', help='Message to send')
@pass_context
def send_message(ctx: CLIContext, meeting_id: str, message: str):
    """Send a user message to the meeting"""
    
    async def _send():
        try:
            await ctx.meeting_service.add_user_message(meeting_id, message)
            click.echo(click.style('✓ Message sent', fg='green'))
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except ValidationError as e:
            click.echo(click.style(f'✗ Validation error: {str(e)}', fg='red'), err=True)
        except MeetingStateError as e:
            click.echo(click.style(f'✗ Cannot send message: {str(e)}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_send())


@meeting.command('request')
@click.argument('meeting_id')
@click.argument('agent_id')
@pass_context
def request_response(ctx: CLIContext, meeting_id: str, agent_id: str):
    """Request a specific agent to respond"""
    
    async def _request():
        try:
            click.echo('Requesting agent response...')
            await ctx.meeting_service.request_agent_response(meeting_id, agent_id)
            click.echo(click.style('✓ Agent response received', fg='green'))
            
            # Show the latest message
            mtg = await ctx.meeting_service.get_meeting(meeting_id)
            if mtg.messages:
                latest = mtg.messages[-1]
                click.echo(f'\n{click.style(latest.speaker_name, fg="blue", bold=True)}:')
                click.echo(f'{latest.content}\n')
            
        except NotFoundError as e:
            click.echo(click.style(f'✗ Not found: {str(e)}', fg='red'), err=True)
        except MeetingStateError as e:
            click.echo(click.style(f'✗ Cannot request response: {str(e)}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_request())


@meeting.command('run')
@click.argument('meeting_id')
@click.option('--rounds', type=int, default=1, help='Number of rounds to run')
@pass_context
def run_meeting(ctx: CLIContext, meeting_id: str, rounds: int):
    """Run meeting for specified number of rounds"""
    
    async def _run():
        try:
            mtg = await ctx.meeting_service.get_meeting(meeting_id)
            
            if mtg.status != MeetingStatus.ACTIVE:
                click.echo(click.style(f'✗ Meeting is not active (status: {mtg.status.value})', fg='red'), err=True)
                return
            
            click.echo(f'Running meeting for {rounds} round(s)...\n')
            
            # Show current agenda if any
            if mtg.agenda:
                pending_items = [item for item in mtg.agenda if not item.completed]
                if pending_items:
                    click.echo(click.style('Current Agenda:', bold=True))
                    for item in pending_items:
                        click.echo(f'  ○ {item.title}')
                    click.echo()
            
            for round_num in range(rounds):
                click.echo(f'=== Round {mtg.current_round} ===\n')
                
                # Each participant speaks once per round
                for participant in mtg.participants:
                    moderator_badge = ' 👑' if mtg.moderator_id == participant.id else ''
                    click.echo(f'Requesting response from {click.style(participant.name, fg="blue", bold=True)}{moderator_badge}...')
                    
                    await ctx.meeting_service.request_agent_response(meeting_id, participant.id)
                    
                    # Reload meeting to get updated state
                    mtg = await ctx.meeting_service.get_meeting(meeting_id)
                    
                    # Show the latest message with @mention highlighting
                    if mtg.messages:
                        latest = mtg.messages[-1]
                        content = latest.content
                        
                        # Highlight @mentions
                        if latest.mentions:
                            for mention in latest.mentions:
                                content = content.replace(f'@{mention.mentioned_participant_name}', 
                                                         click.style(f'@{mention.mentioned_participant_name}', fg='green', bold=True))
                        
                        click.echo(f'\n{content}\n')
                        click.echo('-' * 60 + '\n')
                    
                    # Check if meeting ended (e.g., max rounds reached)
                    if mtg.status == MeetingStatus.ENDED:
                        click.echo(click.style('Meeting has ended', fg='yellow'))
                        return
                
                click.echo()
            
            click.echo(click.style('✓ Rounds completed', fg='green'))
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_run())


@meeting.command('export')
@click.argument('meeting_id')
@click.option('--format', 
              type=click.Choice(['markdown', 'json']),
              default='markdown',
              help='Export format')
@click.option('--output', '-o', help='Output file path (optional)')
@pass_context
def export_meeting(ctx: CLIContext, meeting_id: str, format: str, output: Optional[str]):
    """Export meeting to file"""
    
    async def _export():
        try:
            if format == 'markdown':
                content = await ctx.meeting_service.export_meeting_markdown(meeting_id)
                extension = '.md'
            else:  # json
                content = await ctx.meeting_service.export_meeting_json(meeting_id)
                extension = '.json'
            
            # Determine output path
            if output:
                output_path = output
            else:
                # Generate default filename
                mtg = await ctx.meeting_service.get_meeting(meeting_id)
                safe_topic = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in mtg.topic)
                safe_topic = safe_topic.replace(' ', '_')[:50]
                output_path = f'meeting_{safe_topic}_{meeting_id[:8]}{extension}'
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            click.echo(click.style(f'✓ Meeting exported to: {output_path}', fg='green'))
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_export())


@meeting.command('history')
@click.argument('meeting_id')
@pass_context
def show_history(ctx: CLIContext, meeting_id: str):
    """Show complete meeting history with all messages"""
    
    async def _history():
        try:
            mtg = await ctx.meeting_service.get_meeting(meeting_id)
            
            click.echo(f'\n{"="*70}')
            click.echo(f'Meeting: {click.style(mtg.topic, bold=True)}')
            click.echo(f'ID: {mtg.id}')
            click.echo(f'Status: {mtg.status.value}')
            
            # Show moderator
            if mtg.moderator_id:
                moderator_label = 'User' if mtg.moderator_type == 'user' else next(
                    (a.name for a in mtg.participants if a.id == mtg.moderator_id), mtg.moderator_id
                )
                click.echo(f'Moderator: {click.style(moderator_label, fg="magenta", bold=True)} 👑')
            
            # Show current agenda
            if mtg.agenda:
                pending_items = [item for item in mtg.agenda if not item.completed]
                if pending_items:
                    click.echo(f'\nCurrent Agenda:')
                    for item in pending_items:
                        click.echo(f'  ○ {click.style(item.title, fg="yellow")}')
            
            click.echo(f'{"="*70}\n')
            
            if not mtg.messages:
                click.echo('No messages in this meeting yet.\n')
                return
            
            current_round = 0
            for msg in mtg.messages:
                # Print round header if new round
                if msg.round_number != current_round:
                    current_round = msg.round_number
                    click.echo(f'\n{click.style(f"=== Round {current_round} ===", fg="yellow", bold=True)}\n')
                
                # Print message with moderator badge
                speaker_color = 'cyan' if msg.speaker_type == 'user' else 'blue'
                moderator_badge = ' 👑' if (msg.speaker_type == 'agent' and mtg.moderator_id == msg.speaker_id) or (msg.speaker_type == 'user' and mtg.moderator_type == 'user') else ''
                
                click.echo(f'{click.style(msg.speaker_name, fg=speaker_color, bold=True)} ({msg.speaker_type}){moderator_badge}')
                click.echo(f'{click.style(msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"), dim=True)}')
                click.echo()
                
                # Highlight @mentions
                content = msg.content
                if msg.mentions:
                    for mention in msg.mentions:
                        # Highlight the mention in the content
                        content = content.replace(f'@{mention.mentioned_participant_name}', 
                                                 click.style(f'@{mention.mentioned_participant_name}', fg='green', bold=True))
                
                click.echo(content)
                click.echo()
                click.echo('-' * 70)
                click.echo()
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_history())


# Agenda management commands
@meeting.group('agenda')
def agenda():
    """Manage meeting agenda"""
    pass


@agenda.command('list')
@click.argument('meeting_id')
@pass_context
def list_agenda(ctx: CLIContext, meeting_id: str):
    """List all agenda items for a meeting"""
    
    async def _list():
        try:
            mtg = await ctx.meeting_service.get_meeting(meeting_id)
            
            if not mtg.agenda:
                click.echo('No agenda items in this meeting.')
                return
            
            click.echo(f'\nAgenda for: {mtg.topic}\n')
            for item in mtg.agenda:
                status_mark = click.style('✓', fg='green') if item.completed else click.style('○', fg='yellow')
                click.echo(f'{status_mark} {click.style(item.title, bold=True)}')
                click.echo(f'  ID: {item.id}')
                click.echo(f'  Description: {item.description}')
                click.echo(f'  Status: {"Completed" if item.completed else "Pending"}')
                click.echo()
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_list())


@agenda.command('add')
@click.argument('meeting_id')
@click.option('--title', prompt='Agenda item title', help='Title of the agenda item')
@click.option('--description', prompt='Description', help='Description of the agenda item')
@click.option('--requester', default='user', help='Requester ID (default: user)')
@pass_context
def add_agenda(ctx: CLIContext, meeting_id: str, title: str, description: str, requester: str):
    """Add a new agenda item to a meeting"""
    
    async def _add():
        try:
            import uuid
            
            # Determine requester type
            requester_type = 'user' if requester == 'user' else 'agent'
            
            # Create agenda item
            item = AgendaItem(
                id=str(uuid.uuid4()),
                title=title,
                description=description
            )
            
            await ctx.meeting_service.add_agenda_item(meeting_id, item, requester, requester_type)
            
            click.echo(click.style(f'\n✓ Agenda item added successfully!', fg='green'))
            click.echo(f'  Title: {title}')
            click.echo(f'  ID: {item.id}')
            
        except NotFoundError as e:
            click.echo(click.style(f'✗ Not found: {str(e)}', fg='red'), err=True)
        except PermissionError as e:
            click.echo(click.style(f'✗ Permission denied: {str(e)}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_add())


@agenda.command('remove')
@click.argument('meeting_id')
@click.argument('item_id')
@click.option('--requester', default='user', help='Requester ID (default: user)')
@click.confirmation_option(prompt='Are you sure you want to remove this agenda item?')
@pass_context
def remove_agenda(ctx: CLIContext, meeting_id: str, item_id: str, requester: str):
    """Remove an agenda item from a meeting"""
    
    async def _remove():
        try:
            # Determine requester type
            requester_type = 'user' if requester == 'user' else 'agent'
            
            await ctx.meeting_service.remove_agenda_item(meeting_id, item_id, requester, requester_type)
            
            click.echo(click.style('✓ Agenda item removed', fg='green'))
            
        except NotFoundError as e:
            click.echo(click.style(f'✗ Not found: {str(e)}', fg='red'), err=True)
        except PermissionError as e:
            click.echo(click.style(f'✗ Permission denied: {str(e)}', fg='red'), err=True)
        except AgendaError as e:
            click.echo(click.style(f'✗ Agenda error: {str(e)}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_remove())


@agenda.command('complete')
@click.argument('meeting_id')
@click.argument('item_id')
@click.option('--requester', default='user', help='Requester ID (default: user)')
@pass_context
def complete_agenda(ctx: CLIContext, meeting_id: str, item_id: str, requester: str):
    """Mark an agenda item as completed"""
    
    async def _complete():
        try:
            # Determine requester type
            requester_type = 'user' if requester == 'user' else 'agent'
            
            await ctx.meeting_service.mark_agenda_completed(meeting_id, item_id, requester, requester_type)
            
            click.echo(click.style('✓ Agenda item marked as completed', fg='green'))
            
        except NotFoundError as e:
            click.echo(click.style(f'✗ Not found: {str(e)}', fg='red'), err=True)
        except PermissionError as e:
            click.echo(click.style(f'✗ Permission denied: {str(e)}', fg='red'), err=True)
        except AgendaError as e:
            click.echo(click.style(f'✗ Agenda error: {str(e)}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_complete())



# Meeting minutes commands
@meeting.group('minutes')
def minutes():
    """Manage meeting minutes"""
    pass


@minutes.command('generate')
@click.argument('meeting_id')
@click.option('--agent', help='Agent ID to generate minutes (optional)')
@pass_context
def generate_minutes(ctx: CLIContext, meeting_id: str, agent: Optional[str]):
    """Generate meeting minutes"""
    
    async def _generate():
        try:
            click.echo('Generating meeting minutes...')
            
            minutes = await ctx.meeting_service.generate_minutes(meeting_id, agent)
            
            click.echo(click.style('\n✓ Meeting minutes generated successfully!', fg='green'))
            click.echo(f'  Version: {minutes.version}')
            click.echo(f'  Created by: {minutes.created_by}')
            click.echo(f'  Created at: {minutes.created_at.strftime("%Y-%m-%d %H:%M:%S")}')
            click.echo(f'\nSummary:\n{minutes.summary}')
            
            if minutes.key_decisions:
                click.echo(f'\nKey Decisions:')
                for decision in minutes.key_decisions:
                    click.echo(f'  • {decision}')
            
            if minutes.action_items:
                click.echo(f'\nAction Items:')
                for item in minutes.action_items:
                    click.echo(f'  • {item}')
            
        except NotFoundError as e:
            click.echo(click.style(f'✗ Not found: {str(e)}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_generate())


@minutes.command('show')
@click.argument('meeting_id')
@pass_context
def show_minutes(ctx: CLIContext, meeting_id: str):
    """Show current meeting minutes"""
    
    async def _show():
        try:
            mtg = await ctx.meeting_service.get_meeting(meeting_id)
            
            if not mtg.current_minutes:
                click.echo('No minutes available for this meeting.')
                return
            
            minutes = mtg.current_minutes
            
            click.echo(f'\nMeeting Minutes - {mtg.topic}')
            click.echo(f'{"="*70}\n')
            click.echo(f'Version: {minutes.version}')
            click.echo(f'Created by: {minutes.created_by}')
            click.echo(f'Created at: {minutes.created_at.strftime("%Y-%m-%d %H:%M:%S")}')
            click.echo(f'\n{click.style("Summary:", bold=True)}')
            click.echo(minutes.summary)
            
            if minutes.key_decisions:
                click.echo(f'\n{click.style("Key Decisions:", bold=True)}')
                for decision in minutes.key_decisions:
                    click.echo(f'  • {decision}')
            
            if minutes.action_items:
                click.echo(f'\n{click.style("Action Items:", bold=True)}')
                for item in minutes.action_items:
                    click.echo(f'  • {item}')
            
            click.echo(f'\n{click.style("Full Content:", bold=True)}')
            click.echo(minutes.content)
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_show())


@minutes.command('edit')
@click.argument('meeting_id')
@click.option('--content', prompt='New minutes content', help='Updated minutes content')
@click.option('--editor', default='user', help='Editor ID (default: user)')
@pass_context
def edit_minutes(ctx: CLIContext, meeting_id: str, content: str, editor: str):
    """Manually edit meeting minutes"""
    
    async def _edit():
        try:
            minutes = await ctx.meeting_service.update_minutes(meeting_id, content, editor)
            
            click.echo(click.style('\n✓ Meeting minutes updated successfully!', fg='green'))
            click.echo(f'  Version: {minutes.version}')
            click.echo(f'  Updated by: {minutes.created_by}')
            
        except NotFoundError as e:
            click.echo(click.style(f'✗ Not found: {str(e)}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_edit())


@minutes.command('history')
@click.argument('meeting_id')
@pass_context
def minutes_history(ctx: CLIContext, meeting_id: str):
    """Show meeting minutes version history"""
    
    async def _history():
        try:
            mtg = await ctx.meeting_service.get_meeting(meeting_id)
            
            if not mtg.minutes_history:
                click.echo('No minutes history available for this meeting.')
                return
            
            click.echo(f'\nMinutes History - {mtg.topic}')
            click.echo(f'{"="*70}\n')
            
            for minutes in mtg.minutes_history:
                click.echo(f'Version {minutes.version}:')
                click.echo(f'  Created by: {minutes.created_by}')
                click.echo(f'  Created at: {minutes.created_at.strftime("%Y-%m-%d %H:%M:%S")}')
                click.echo(f'  Summary: {minutes.summary[:100]}...' if len(minutes.summary) > 100 else f'  Summary: {minutes.summary}')
                click.echo()
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_history())



# Meeting configuration commands
@meeting.group('config')
def config():
    """Manage meeting configuration"""
    pass


@config.command('show')
@click.argument('meeting_id')
@pass_context
def show_config(ctx: CLIContext, meeting_id: str):
    """Show meeting configuration"""
    
    async def _show():
        try:
            mtg = await ctx.meeting_service.get_meeting(meeting_id)
            
            click.echo(f'\nConfiguration for: {mtg.topic}')
            click.echo(f'{"="*60}\n')
            click.echo(f'Speaking Order: {mtg.config.speaking_order.value}')
            click.echo(f'Discussion Style: {mtg.config.discussion_style.value}')
            
            if mtg.config.max_rounds:
                click.echo(f'Max Rounds: {mtg.config.max_rounds}')
            else:
                click.echo('Max Rounds: Unlimited')
            
            if mtg.config.max_message_length:
                click.echo(f'Max Message Length: {mtg.config.max_message_length}')
            else:
                click.echo('Max Message Length: Unlimited')
            
            if mtg.config.speaking_length_preferences:
                click.echo(f'\nSpeaking Length Preferences:')
                for agent_id, preference in mtg.config.speaking_length_preferences.items():
                    agent_name = next((a.name for a in mtg.participants if a.id == agent_id), agent_id)
                    click.echo(f'  {agent_name}: {preference.value}')
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_show())


@config.command('update-style')
@click.argument('meeting_id')
@click.option('--style',
              type=click.Choice(['formal', 'casual', 'debate']),
              prompt='Discussion style',
              help='New discussion style')
@pass_context
def update_style(ctx: CLIContext, meeting_id: str, style: str):
    """Update meeting discussion style"""
    
    async def _update():
        try:
            mtg = await ctx.meeting_service.get_meeting(meeting_id)
            
            # Update config
            mtg.config.discussion_style = DiscussionStyle(style)
            
            await ctx.meeting_service.update_meeting_config(meeting_id, mtg.config)
            
            click.echo(click.style(f'\n✓ Discussion style updated to: {style}', fg='green'))
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_update())


@config.command('update-length')
@click.argument('meeting_id')
@click.argument('agent_id')
@click.option('--preference',
              type=click.Choice(['brief', 'moderate', 'detailed']),
              prompt='Speaking length preference',
              help='Speaking length preference')
@pass_context
def update_length(ctx: CLIContext, meeting_id: str, agent_id: str, preference: str):
    """Update speaking length preference for an agent"""
    
    async def _update():
        try:
            mtg = await ctx.meeting_service.get_meeting(meeting_id)
            
            # Verify agent is in meeting
            if not any(a.id == agent_id for a in mtg.participants):
                click.echo(click.style(f'✗ Agent not in this meeting: {agent_id}', fg='red'), err=True)
                return
            
            # Update config
            if mtg.config.speaking_length_preferences is None:
                mtg.config.speaking_length_preferences = {}
            
            mtg.config.speaking_length_preferences[agent_id] = SpeakingLength(preference)
            
            await ctx.meeting_service.update_meeting_config(meeting_id, mtg.config)
            
            agent_name = next((a.name for a in mtg.participants if a.id == agent_id), agent_id)
            click.echo(click.style(f'\n✓ Speaking length preference for {agent_name} updated to: {preference}', fg='green'))
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_update())
