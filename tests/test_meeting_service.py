"""Unit tests for meeting service"""

import pytest
import tempfile
import shutil

from src.models import Agent, Role, ModelConfig, MeetingConfig, MeetingStatus, SpeakingOrder
from src.storage import FileStorageService
from src.services.agent_service import AgentService
from src.services.meeting_service import MeetingService
from src.exceptions import ValidationError, NotFoundError, MeetingStateError


@pytest.fixture
async def setup_services():
    """Setup services with temporary storage"""
    temp_dir = tempfile.mkdtemp()
    storage = FileStorageService(base_path=temp_dir)
    agent_service = AgentService(storage)
    meeting_service = MeetingService(storage, agent_service)
    
    yield storage, agent_service, meeting_service
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
async def sample_agent(setup_services):
    """Create a sample agent"""
    storage, agent_service, _ = setup_services
    
    agent_data = {
        'name': 'Test Agent',
        'role': {
            'name': 'Tester',
            'description': 'A test agent',
            'system_prompt': 'You are a test agent'
        },
        'model_config': {
            'provider': 'openai',
            'model_name': 'gpt-4',
            'api_key': 'test-key'
        }
    }
    
    agent = await agent_service.create_agent(agent_data)
    return agent


@pytest.mark.asyncio
async def test_create_meeting_basic(setup_services, sample_agent):
    """Test basic meeting creation"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    assert meeting is not None
    assert meeting.topic == "Test Meeting"
    assert len(meeting.participants) == 1
    assert meeting.status == MeetingStatus.ACTIVE


@pytest.mark.asyncio
async def test_create_meeting_empty_topic(setup_services, sample_agent):
    """Test that empty topic is rejected"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    config = MeetingConfig()
    
    with pytest.raises(ValidationError) as exc_info:
        await meeting_service.create_meeting(
            topic="",
            agent_ids=[agent.id],
            config=config
        )
    
    assert exc_info.value.field == "topic"


@pytest.mark.asyncio
async def test_create_meeting_no_agents(setup_services):
    """Test that meeting without agents is rejected"""
    _, _, meeting_service = setup_services
    
    config = MeetingConfig()
    
    with pytest.raises(ValidationError) as exc_info:
        await meeting_service.create_meeting(
            topic="Test Meeting",
            agent_ids=[],
            config=config
        )
    
    assert exc_info.value.field == "agent_ids"


@pytest.mark.asyncio
async def test_start_meeting(setup_services, sample_agent):
    """Test starting a paused meeting"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create meeting
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    # Pause it first
    await meeting_service.pause_meeting(meeting.id)
    
    # Verify it's paused
    paused_meeting = await meeting_service.get_meeting(meeting.id)
    assert paused_meeting.status == MeetingStatus.PAUSED
    
    # Start it again
    await meeting_service.start_meeting(meeting.id)
    
    # Verify it's active
    active_meeting = await meeting_service.get_meeting(meeting.id)
    assert active_meeting.status == MeetingStatus.ACTIVE


@pytest.mark.asyncio
async def test_pause_meeting(setup_services, sample_agent):
    """Test pausing an active meeting"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create meeting (starts as active)
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    # Pause it
    await meeting_service.pause_meeting(meeting.id)
    
    # Verify it's paused
    paused_meeting = await meeting_service.get_meeting(meeting.id)
    assert paused_meeting.status == MeetingStatus.PAUSED


@pytest.mark.asyncio
async def test_pause_non_active_meeting(setup_services, sample_agent):
    """Test that pausing a non-active meeting raises error"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create and end meeting
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    await meeting_service.end_meeting(meeting.id)
    
    # Try to pause ended meeting
    with pytest.raises(MeetingStateError):
        await meeting_service.pause_meeting(meeting.id)


@pytest.mark.asyncio
async def test_end_meeting(setup_services, sample_agent):
    """Test ending a meeting"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create meeting
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    # End it
    await meeting_service.end_meeting(meeting.id)
    
    # Verify it's ended
    ended_meeting = await meeting_service.get_meeting(meeting.id)
    assert ended_meeting.status == MeetingStatus.ENDED


@pytest.mark.asyncio
async def test_end_already_ended_meeting(setup_services, sample_agent):
    """Test that ending an already ended meeting raises error"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create and end meeting
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    await meeting_service.end_meeting(meeting.id)
    
    # Try to end again
    with pytest.raises(MeetingStateError):
        await meeting_service.end_meeting(meeting.id)


@pytest.mark.asyncio
async def test_start_ended_meeting(setup_services, sample_agent):
    """Test that starting an ended meeting raises error"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create and end meeting
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    await meeting_service.end_meeting(meeting.id)
    
    # Try to start ended meeting
    with pytest.raises(MeetingStateError):
        await meeting_service.start_meeting(meeting.id)


@pytest.mark.asyncio
async def test_get_meeting(setup_services, sample_agent):
    """Test getting a meeting"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create meeting
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    # Get meeting
    retrieved_meeting = await meeting_service.get_meeting(meeting.id)
    
    assert retrieved_meeting.id == meeting.id
    assert retrieved_meeting.topic == meeting.topic


@pytest.mark.asyncio
async def test_get_nonexistent_meeting(setup_services):
    """Test getting a nonexistent meeting"""
    _, _, meeting_service = setup_services
    
    with pytest.raises(NotFoundError):
        await meeting_service.get_meeting("nonexistent-id")


@pytest.mark.asyncio
async def test_list_meetings(setup_services, sample_agent):
    """Test listing meetings"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create multiple meetings
    config = MeetingConfig()
    meeting1 = await meeting_service.create_meeting(
        topic="Meeting 1",
        agent_ids=[agent.id],
        config=config
    )
    meeting2 = await meeting_service.create_meeting(
        topic="Meeting 2",
        agent_ids=[agent.id],
        config=config
    )
    
    # List meetings
    meetings = await meeting_service.list_meetings()
    
    assert len(meetings) == 2
    meeting_ids = {m.id for m in meetings}
    assert meeting1.id in meeting_ids
    assert meeting2.id in meeting_ids


@pytest.mark.asyncio
async def test_delete_meeting(setup_services, sample_agent):
    """Test deleting a meeting"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create meeting
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    # Delete meeting
    await meeting_service.delete_meeting(meeting.id)
    
    # Verify it's deleted
    with pytest.raises(NotFoundError):
        await meeting_service.get_meeting(meeting.id)


@pytest.mark.asyncio
async def test_delete_nonexistent_meeting(setup_services):
    """Test deleting a nonexistent meeting"""
    _, _, meeting_service = setup_services
    
    with pytest.raises(NotFoundError):
        await meeting_service.delete_meeting("nonexistent-id")


@pytest.mark.asyncio
async def test_add_user_message(setup_services, sample_agent):
    """Test adding a user message to a meeting"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create meeting
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    # Add user message
    await meeting_service.add_user_message(meeting.id, "Hello from user")
    
    # Verify message was added
    updated_meeting = await meeting_service.get_meeting(meeting.id)
    assert len(updated_meeting.messages) == 1
    
    message = updated_meeting.messages[0]
    assert message.content == "Hello from user"
    assert message.speaker_type == 'user'
    assert message.speaker_name == "User"
    assert message.round_number == 1


@pytest.mark.asyncio
async def test_add_user_message_empty_content(setup_services, sample_agent):
    """Test that empty user message is rejected"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create meeting
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    # Try to add empty message
    with pytest.raises(ValidationError) as exc_info:
        await meeting_service.add_user_message(meeting.id, "")
    
    assert exc_info.value.field == "content"


@pytest.mark.asyncio
async def test_add_user_message_whitespace_only(setup_services, sample_agent):
    """Test that whitespace-only user message is rejected"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create meeting
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    # Try to add whitespace-only message
    with pytest.raises(ValidationError) as exc_info:
        await meeting_service.add_user_message(meeting.id, "   \n\t  ")
    
    assert exc_info.value.field == "content"


@pytest.mark.asyncio
async def test_add_user_message_too_long(setup_services, sample_agent):
    """Test that too long user message is rejected"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create meeting
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    # Try to add message that's too long
    long_message = "A" * 10001
    with pytest.raises(ValidationError) as exc_info:
        await meeting_service.add_user_message(meeting.id, long_message)
    
    assert exc_info.value.field == "content"


@pytest.mark.asyncio
async def test_add_user_message_to_paused_meeting(setup_services, sample_agent):
    """Test that adding user message to paused meeting raises error"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create and pause meeting
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    await meeting_service.pause_meeting(meeting.id)
    
    # Try to add user message
    with pytest.raises(MeetingStateError):
        await meeting_service.add_user_message(meeting.id, "Hello")


@pytest.mark.asyncio
async def test_add_user_message_to_ended_meeting(setup_services, sample_agent):
    """Test that adding user message to ended meeting raises error"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create and end meeting
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    await meeting_service.end_meeting(meeting.id)
    
    # Try to add user message
    with pytest.raises(MeetingStateError):
        await meeting_service.add_user_message(meeting.id, "Hello")



@pytest.mark.asyncio
async def test_request_specific_agent_response(setup_services):
    """Test requesting response from a specific agent"""
    from unittest.mock import patch
    from tests.mock_adapter import MockModelAdapter
    
    storage, agent_service, meeting_service = setup_services
    
    # Create two agents
    agent1_data = {
        'name': 'Agent 1',
        'role': {
            'name': 'Role 1',
            'description': 'First agent',
            'system_prompt': 'You are agent 1'
        },
        'model_config': {
            'provider': 'openai',
            'model_name': 'gpt-4',
            'api_key': 'test-key-1'
        }
    }
    agent1 = await agent_service.create_agent(agent1_data)
    
    agent2_data = {
        'name': 'Agent 2',
        'role': {
            'name': 'Role 2',
            'description': 'Second agent',
            'system_prompt': 'You are agent 2'
        },
        'model_config': {
            'provider': 'openai',
            'model_name': 'gpt-4',
            'api_key': 'test-key-2'
        }
    }
    agent2 = await agent_service.create_agent(agent2_data)
    
    # Create meeting with both agents
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent1.id, agent2.id],
        config=config
    )
    
    # Mock adapter
    mock_adapter = MockModelAdapter(response_template="Response from agent")
    
    # Request response from specific agent (agent2)
    with patch('src.adapters.factory.ModelAdapterFactory.create', return_value=mock_adapter):
        await meeting_service.request_agent_response(meeting.id, agent2.id)
    
    # Verify the response was added
    updated_meeting = await meeting_service.get_meeting(meeting.id)
    assert len(updated_meeting.messages) == 1
    
    # Verify it's from the specified agent
    message = updated_meeting.messages[0]
    assert message.speaker_id == agent2.id
    assert message.speaker_name == agent2.name
    assert message.speaker_type == 'agent'


@pytest.mark.asyncio
async def test_request_nonexistent_agent_response(setup_services, sample_agent):
    """Test that requesting response from non-participant agent raises error"""
    _, _, meeting_service = setup_services
    agent = sample_agent
    
    # Create meeting with one agent
    config = MeetingConfig()
    meeting = await meeting_service.create_meeting(
        topic="Test Meeting",
        agent_ids=[agent.id],
        config=config
    )
    
    # Try to request response from non-existent agent
    with pytest.raises(NotFoundError) as exc_info:
        await meeting_service.request_agent_response(meeting.id, "nonexistent-agent-id")
    
    assert exc_info.value.resource_type == "agent"
    assert exc_info.value.resource_id == "nonexistent-agent-id"
