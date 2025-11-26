"""Main CLI entry point"""

import click
import asyncio
from pathlib import Path

from ..storage.file_storage import FileStorageService
from ..services.agent_service import AgentService
from ..services.meeting_service import MeetingService


# Global context for services
class CLIContext:
    """Context object for CLI commands"""
    def __init__(self, data_path: str = "data"):
        self.storage = FileStorageService(data_path)
        self.agent_service = AgentService(self.storage)
        self.meeting_service = MeetingService(self.storage, self.agent_service)


pass_context = click.make_pass_decorator(CLIContext, ensure=True)


@click.group()
@click.option('--data-path', default='data', help='Path to data directory')
@click.pass_context
def cli(ctx, data_path):
    """AI Agent Meeting System - Multi-agent discussion platform"""
    ctx.obj = CLIContext(data_path)


# Import subcommands
from . import agent_commands
from . import meeting_commands


# Register command groups
cli.add_command(agent_commands.agent)
cli.add_command(meeting_commands.meeting)


if __name__ == '__main__':
    cli()
