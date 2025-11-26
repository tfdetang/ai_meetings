"""Meeting management CLI commands"""

import click
import asyncio
from typing import Optional, List

from .main import pass_context, CLIContext
from ..models import MeetingConfig, SpeakingOrder, MeetingStatus
from ..exceptions import ValidationError, NotFoundError, MeetingStateError


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
@pass_context
def create_meeting(ctx: CLIContext, topic: str, agents: str, max_rounds: Optional[int],
                   max_length: Optional[int], order: str):
    """Create a new meeting"""
    
    async def _create():
        try:
            # Parse agent IDs
            agent_ids = [aid.strip() for aid in agents.split(',') if aid.strip()]
            
            if not agent_ids:
                click.echo(click.style('✗ No agent IDs provided', fg='red'), err=True)
                return
            
            # Create meeting config
            config = MeetingConfig(
                max_rounds=max_rounds,
                max_message_length=max_length,
                speaking_order=SpeakingOrder.SEQUENTIAL if order == 'sequential' else SpeakingOrder.RANDOM
            )
            
            # Create meeting
            meeting = await ctx.meeting_service.create_meeting(topic, agent_ids, config)
            
            click.echo(click.style(f'\n✓ Meeting created successfully!', fg='green'))
            click.echo(f'  ID: {meeting.id}')
            click.echo(f'  Topic: {meeting.topic}')
            click.echo(f'  Participants: {len(meeting.participants)}')
            click.echo(f'  Status: {meeting.status.value}')
            
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
            
            click.echo(f'\nConfiguration:')
            click.echo(f'  Speaking Order: {mtg.config.speaking_order.value}')
            if mtg.config.max_rounds:
                click.echo(f'  Max Rounds: {mtg.config.max_rounds}')
            if mtg.config.max_message_length:
                click.echo(f'  Max Message Length: {mtg.config.max_message_length}')
            
            click.echo(f'\nParticipants ({len(mtg.participants)}):')
            for p in mtg.participants:
                click.echo(f'  • {p.name} ({p.role.name})')
            
            click.echo(f'\nMessages: {len(mtg.messages)}')
            
            if messages and mtg.messages:
                click.echo('\n' + '='*60)
                for msg in mtg.messages:
                    speaker_color = 'cyan' if msg.speaker_type == 'user' else 'blue'
                    click.echo(f'\n[Round {msg.round_number}] ' + click.style(f'{msg.speaker_name}', fg=speaker_color, bold=True))
                    click.echo(f'{msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")}')
                    click.echo(f'\n{msg.content}')
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
            
            for round_num in range(rounds):
                click.echo(f'=== Round {mtg.current_round} ===\n')
                
                # Each participant speaks once per round
                for participant in mtg.participants:
                    click.echo(f'Requesting response from {click.style(participant.name, fg="blue", bold=True)}...')
                    
                    await ctx.meeting_service.request_agent_response(meeting_id, participant.id)
                    
                    # Reload meeting to get updated state
                    mtg = await ctx.meeting_service.get_meeting(meeting_id)
                    
                    # Show the latest message
                    if mtg.messages:
                        latest = mtg.messages[-1]
                        click.echo(f'\n{latest.content}\n')
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
                
                # Print message
                speaker_color = 'cyan' if msg.speaker_type == 'user' else 'blue'
                click.echo(f'{click.style(msg.speaker_name, fg=speaker_color, bold=True)} ({msg.speaker_type})')
                click.echo(f'{click.style(msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"), dim=True)}')
                click.echo()
                click.echo(msg.content)
                click.echo()
                click.echo('-' * 70)
                click.echo()
            
        except NotFoundError:
            click.echo(click.style(f'✗ Meeting not found: {meeting_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_history())
