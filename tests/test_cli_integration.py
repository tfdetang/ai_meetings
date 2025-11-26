"""Integration tests for CLI"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner

from src.cli.main import cli
from src.storage.file_storage import FileStorageService
from src.services.agent_service import AgentService
from src.services.meeting_service import MeetingService


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def runner():
    """Create CLI runner"""
    return CliRunner()


def test_cli_help(runner):
    """Test CLI help command"""
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'AI Agent Meeting System' in result.output


def test_agent_commands_help(runner):
    """Test agent commands help"""
    result = runner.invoke(cli, ['agent', '--help'])
    assert result.exit_code == 0
    assert 'Manage AI agents' in result.output


def test_meeting_commands_help(runner):
    """Test meeting commands help"""
    result = runner.invoke(cli, ['meeting', '--help'])
    assert result.exit_code == 0
    assert 'Manage meetings' in result.output


def test_agent_templates(runner, temp_data_dir):
    """Test listing role templates"""
    result = runner.invoke(cli, ['--data-path', temp_data_dir, 'agent', 'templates'])
    assert result.exit_code == 0
    assert 'product_manager' in result.output
    assert 'software_engineer' in result.output


def test_agent_list_empty(runner, temp_data_dir):
    """Test listing agents when none exist"""
    result = runner.invoke(cli, ['--data-path', temp_data_dir, 'agent', 'list'])
    assert result.exit_code == 0
    assert 'No agents found' in result.output


def test_meeting_list_empty(runner, temp_data_dir):
    """Test listing meetings when none exist"""
    result = runner.invoke(cli, ['--data-path', temp_data_dir, 'meeting', 'list'])
    assert result.exit_code == 0
    assert 'No meetings found' in result.output


def test_agent_create_with_template(runner, temp_data_dir):
    """Test creating agent with template"""
    result = runner.invoke(cli, [
        '--data-path', temp_data_dir,
        'agent', 'create',
        '--name', 'TestAgent',
        '--provider', 'openai',
        '--model', 'gpt-4',
        '--api-key', 'test-key-123',
        '--template', 'product_manager'
    ])
    assert result.exit_code == 0
    assert 'Agent created successfully' in result.output
    assert 'TestAgent' in result.output


def test_agent_create_and_list(runner, temp_data_dir):
    """Test creating agent and listing it"""
    # Create agent
    result = runner.invoke(cli, [
        '--data-path', temp_data_dir,
        'agent', 'create',
        '--name', 'TestAgent',
        '--provider', 'openai',
        '--model', 'gpt-4',
        '--api-key', 'test-key-123',
        '--template', 'software_engineer'
    ])
    assert result.exit_code == 0
    
    # List agents
    result = runner.invoke(cli, ['--data-path', temp_data_dir, 'agent', 'list'])
    assert result.exit_code == 0
    assert 'TestAgent' in result.output
    assert 'Software Engineer' in result.output


def test_agent_show_not_found(runner, temp_data_dir):
    """Test showing non-existent agent"""
    result = runner.invoke(cli, [
        '--data-path', temp_data_dir,
        'agent', 'show',
        'non-existent-id'
    ])
    assert result.exit_code == 0
    assert 'not found' in result.output


def test_meeting_create_validation(runner, temp_data_dir):
    """Test meeting creation validation"""
    # Try to create meeting with no agents
    result = runner.invoke(cli, [
        '--data-path', temp_data_dir,
        'meeting', 'create',
        '--topic', 'Test Meeting',
        '--agents', ''
    ])
    assert result.exit_code == 0
    assert 'error' in result.output.lower() or 'No agent IDs provided' in result.output


def test_full_workflow(runner, temp_data_dir):
    """Test complete workflow: create agents, create meeting, list"""
    # Create first agent
    result = runner.invoke(cli, [
        '--data-path', temp_data_dir,
        'agent', 'create',
        '--name', 'Agent1',
        '--provider', 'openai',
        '--model', 'gpt-4',
        '--api-key', 'key1',
        '--template', 'product_manager'
    ])
    assert result.exit_code == 0
    
    # Extract agent ID from output
    lines = result.output.split('\n')
    agent1_id = None
    for line in lines:
        if 'ID:' in line:
            agent1_id = line.split('ID:')[1].strip()
            break
    
    assert agent1_id is not None
    
    # Create second agent
    result = runner.invoke(cli, [
        '--data-path', temp_data_dir,
        'agent', 'create',
        '--name', 'Agent2',
        '--provider', 'openai',
        '--model', 'gpt-4',
        '--api-key', 'key2',
        '--template', 'software_engineer'
    ])
    assert result.exit_code == 0
    
    # Extract second agent ID
    lines = result.output.split('\n')
    agent2_id = None
    for line in lines:
        if 'ID:' in line:
            agent2_id = line.split('ID:')[1].strip()
            break
    
    assert agent2_id is not None
    
    # Create meeting
    result = runner.invoke(cli, [
        '--data-path', temp_data_dir,
        'meeting', 'create',
        '--topic', 'Test Discussion',
        '--agents', f'{agent1_id},{agent2_id}',
        '--max-rounds', '2',
        '--order', 'sequential'
    ])
    assert result.exit_code == 0
    assert 'Meeting created successfully' in result.output
    
    # List meetings
    result = runner.invoke(cli, ['--data-path', temp_data_dir, 'meeting', 'list'])
    assert result.exit_code == 0
    assert 'Test Discussion' in result.output
    assert '2' in result.output  # Should show 2 participants
