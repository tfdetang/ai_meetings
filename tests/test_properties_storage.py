"""Property-based tests for storage operations"""

import pytest
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st
from datetime import datetime

from src.models import (
    Agent,
    Role,
    ModelConfig,
    ModelParameters,
    Meeting,
    MeetingConfig,
    MeetingStatus,
    SpeakingOrder,
    Message,
)
from src.storage import FileStorageService


# Reuse strategies from test_properties_models.py
role_strategy = st.builds(
    Role,
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    description=st.text(min_size=1, max_size=2000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    system_prompt=st.text(min_size=1, max_size=2000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip())
)

model_parameters_strategy = st.builds(
    ModelParameters,
    temperature=st.none() | st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
    max_tokens=st.none() | st.integers(min_value=1, max_value=100000),
    top_p=st.none() | st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
)

model_config_strategy = st.builds(
    ModelConfig,
    provider=st.sampled_from(['openai', 'anthropic', 'google', 'glm']),
    model_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    api_key=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    parameters=st.none() | model_parameters_strategy
)

# Strategy for filesystem-safe IDs (alphanumeric + dash/underscore)
filesystem_safe_id_strategy = st.text(
    min_size=1, 
    max_size=100, 
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
).filter(lambda x: x and x.strip() and not x.startswith('-') and not x.startswith('_'))

agent_strategy = st.builds(
    Agent,
    id=filesystem_safe_id_strategy,
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    role=role_strategy,
    model_config=model_config_strategy
)

message_strategy = st.builds(
    Message,
    id=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    speaker_id=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    speaker_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    speaker_type=st.sampled_from(['agent', 'user']),
    content=st.text(min_size=1, max_size=10000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    timestamp=st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)),
    round_number=st.integers(min_value=1, max_value=1000)
)

meeting_config_strategy = st.builds(
    MeetingConfig,
    max_rounds=st.none() | st.integers(min_value=1, max_value=100),
    max_message_length=st.none() | st.integers(min_value=1, max_value=100000),
    speaking_order=st.sampled_from([SpeakingOrder.SEQUENTIAL, SpeakingOrder.RANDOM])
)

meeting_strategy = st.builds(
    Meeting,
    id=filesystem_safe_id_strategy,
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    participants=st.lists(agent_strategy, min_size=1, max_size=5),
    messages=st.lists(message_strategy, min_size=0, max_size=10),
    config=meeting_config_strategy,
    status=st.sampled_from([MeetingStatus.ACTIVE, MeetingStatus.PAUSED, MeetingStatus.ENDED]),
    created_at=st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)),
    updated_at=st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)),
    current_round=st.integers(min_value=1, max_value=100)
)


# Feature: ai-agent-meeting, Property 2: 代理持久化往返
# Validates: Requirements 1.2
@given(agent=agent_strategy)
@pytest.mark.asyncio
async def test_property_agent_persistence_round_trip(agent):
    """
    Property 2: Agent Persistence Round Trip
    For any valid agent configuration, saving and then reloading should return
    an equivalent agent object.
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        
        # Save the agent
        await temp_storage.save_agent(agent)
    
        # Load the agent back
        loaded_agent = await temp_storage.load_agent(agent.id)
        
        # Verify the loaded agent is not None
        assert loaded_agent is not None
        
        # Verify all fields match
        assert loaded_agent.id == agent.id
        assert loaded_agent.name == agent.name
        assert loaded_agent.role.name == agent.role.name
        assert loaded_agent.role.description == agent.role.description
        assert loaded_agent.role.system_prompt == agent.role.system_prompt
        assert loaded_agent.model_config.provider == agent.model_config.provider
        assert loaded_agent.model_config.model_name == agent.model_config.model_name
        assert loaded_agent.model_config.api_key == agent.model_config.api_key
        
        # Verify parameters if present and non-empty
        # Note: ModelParameters with all None values is treated as None after round-trip
        if agent.model_config.parameters:
            # Check if parameters has any non-None values
            has_values = (
                agent.model_config.parameters.temperature is not None or
                agent.model_config.parameters.max_tokens is not None or
                agent.model_config.parameters.top_p is not None
            )
            if has_values:
                assert loaded_agent.model_config.parameters is not None
                assert loaded_agent.model_config.parameters.temperature == agent.model_config.parameters.temperature
                assert loaded_agent.model_config.parameters.max_tokens == agent.model_config.parameters.max_tokens
                assert loaded_agent.model_config.parameters.top_p == agent.model_config.parameters.top_p
            else:
                # Empty parameters (all None) should become None after round-trip
                assert loaded_agent.model_config.parameters is None
        else:
            assert loaded_agent.model_config.parameters is None
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 6: API 凭证往返
# Validates: Requirements 2.2
@given(
    provider=st.sampled_from(['openai', 'anthropic', 'google', 'glm']),
    model_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    api_key=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
)
@pytest.mark.asyncio
async def test_property_api_credentials_round_trip(provider, model_name, api_key):
    """
    Property 6: API Credentials Round Trip
    For any model provider and credentials, saving and then reloading should return
    the same credentials.
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        
        # Create an agent with the credentials
        role = Role(
            name="Test Role",
            description="Test description",
            system_prompt="Test prompt"
        )
        model_config = ModelConfig(
            provider=provider,
            model_name=model_name,
            api_key=api_key
        )
        agent = Agent(
            id="test-agent-credentials",
            name="Test Agent",
            role=role,
            model_config=model_config
        )
        
        # Save the agent
        await temp_storage.save_agent(agent)
        
        # Load the agent back
        loaded_agent = await temp_storage.load_agent(agent.id)
        
        # Verify credentials are preserved
        assert loaded_agent is not None
        assert loaded_agent.model_config.provider == provider
        assert loaded_agent.model_config.model_name == model_name
        assert loaded_agent.model_config.api_key == api_key
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 24: 会议加载往返
# Validates: Requirements 6.3
@given(meeting=meeting_strategy)
@pytest.mark.asyncio
async def test_property_meeting_load_round_trip(meeting):
    """
    Property 24: Meeting Load Round Trip
    For any saved meeting, reloading should include all original messages and metadata.
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        
        # Save the meeting
        await temp_storage.save_meeting(meeting)
        
        # Load the meeting back
        loaded_meeting = await temp_storage.load_meeting(meeting.id)
        
        # Verify the loaded meeting is not None
        assert loaded_meeting is not None
        
        # Verify basic fields
        assert loaded_meeting.id == meeting.id
        assert loaded_meeting.topic == meeting.topic
        assert loaded_meeting.status == meeting.status
        assert loaded_meeting.current_round == meeting.current_round
        
        # Verify timestamps (compare as ISO strings to handle precision)
        assert loaded_meeting.created_at.isoformat() == meeting.created_at.isoformat()
        assert loaded_meeting.updated_at.isoformat() == meeting.updated_at.isoformat()
        
        # Verify config
        assert loaded_meeting.config.max_rounds == meeting.config.max_rounds
        assert loaded_meeting.config.max_message_length == meeting.config.max_message_length
        assert loaded_meeting.config.speaking_order == meeting.config.speaking_order
        
        # Verify participants
        assert len(loaded_meeting.participants) == len(meeting.participants)
        for loaded_p, original_p in zip(loaded_meeting.participants, meeting.participants):
            assert loaded_p.id == original_p.id
            assert loaded_p.name == original_p.name
            assert loaded_p.role.name == original_p.role.name
            assert loaded_p.model_config.provider == original_p.model_config.provider
        
        # Verify messages (all original messages and metadata)
        assert len(loaded_meeting.messages) == len(meeting.messages)
        for loaded_m, original_m in zip(loaded_meeting.messages, meeting.messages):
            assert loaded_m.id == original_m.id
            assert loaded_m.speaker_id == original_m.speaker_id
            assert loaded_m.speaker_name == original_m.speaker_name
            assert loaded_m.speaker_type == original_m.speaker_type
            assert loaded_m.content == original_m.content
            assert loaded_m.round_number == original_m.round_number
            assert loaded_m.timestamp.isoformat() == original_m.timestamp.isoformat()
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 3: 代理列表完整性
# Validates: Requirements 1.3
@given(agents=st.lists(agent_strategy, min_size=1, max_size=10, unique_by=lambda a: a.id))
@pytest.mark.asyncio
async def test_property_agent_list_integrity(agents):
    """
    Property 3: Agent List Integrity
    For any agent collection, the list operation should return all saved agents,
    and each agent should include name, role, and model information.
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        
        # Save all agents
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Load all agents
        loaded_agents = await temp_storage.load_all_agents()
        
        # Verify count matches
        assert len(loaded_agents) == len(agents)
        
        # Create a map of loaded agents by ID for easy lookup
        loaded_by_id = {a.id: a for a in loaded_agents}
        
        # Verify each original agent is in the loaded list
        for agent in agents:
            assert agent.id in loaded_by_id
            loaded = loaded_by_id[agent.id]
            
            # Verify key information is present
            assert loaded.name == agent.name
            assert loaded.role.name == agent.role.name
            assert loaded.role.description == agent.role.description
            assert loaded.model_config.provider == agent.model_config.provider
            assert loaded.model_config.model_name == agent.model_config.model_name
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 5: 代理删除完整性
# Validates: Requirements 1.5
@given(
    agents=st.lists(agent_strategy, min_size=2, max_size=10, unique_by=lambda a: a.id),
    delete_index=st.data()
)
@pytest.mark.asyncio
async def test_property_agent_deletion_integrity(agents, delete_index):
    """
    Property 5: Agent Deletion Integrity
    For any existing agent, after deletion the agent should not appear in the list
    and should not be loadable.
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        
        # Save all agents
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Pick an agent to delete
        idx = delete_index.draw(st.integers(min_value=0, max_value=len(agents) - 1))
        agent_to_delete = agents[idx]
        
        # Delete the agent
        await temp_storage.delete_agent(agent_to_delete.id)
        
        # Verify the agent is not in the list
        loaded_agents = await temp_storage.load_all_agents()
        loaded_ids = {a.id for a in loaded_agents}
        assert agent_to_delete.id not in loaded_ids
        
        # Verify the agent cannot be loaded
        loaded_agent = await temp_storage.load_agent(agent_to_delete.id)
        assert loaded_agent is None
        
        # Verify other agents are still present
        assert len(loaded_agents) == len(agents) - 1
        for agent in agents:
            if agent.id != agent_to_delete.id:
                assert agent.id in loaded_ids
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 23: 会议列表完整性
# Validates: Requirements 6.2
@given(meetings=st.lists(meeting_strategy, min_size=1, max_size=10, unique_by=lambda m: m.id))
@pytest.mark.asyncio
async def test_property_meeting_list_integrity(meetings):
    """
    Property 23: Meeting List Integrity
    For any saved meeting collection, the list operation should return all meetings
    with their basic information.
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        
        # Save all meetings
        for meeting in meetings:
            await temp_storage.save_meeting(meeting)
        
        # Load all meetings
        loaded_meetings = await temp_storage.load_all_meetings()
        
        # Verify count matches
        assert len(loaded_meetings) == len(meetings)
        
        # Create a map of loaded meetings by ID for easy lookup
        loaded_by_id = {m.id: m for m in loaded_meetings}
        
        # Verify each original meeting is in the loaded list with basic info
        for meeting in meetings:
            assert meeting.id in loaded_by_id
            loaded = loaded_by_id[meeting.id]
            
            # Verify basic information is present
            assert loaded.topic == meeting.topic
            assert loaded.status == meeting.status
            assert len(loaded.participants) == len(meeting.participants)
            assert len(loaded.messages) == len(meeting.messages)
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 26: 会议删除完整性
# Validates: Requirements 6.5
@given(
    meetings=st.lists(meeting_strategy, min_size=2, max_size=10, unique_by=lambda m: m.id),
    delete_index=st.data()
)
@pytest.mark.asyncio
async def test_property_meeting_deletion_integrity(meetings, delete_index):
    """
    Property 26: Meeting Deletion Integrity
    For any existing meeting, after deletion the meeting should not appear in the list
    and should not be loadable.
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        
        # Save all meetings
        for meeting in meetings:
            await temp_storage.save_meeting(meeting)
        
        # Pick a meeting to delete
        idx = delete_index.draw(st.integers(min_value=0, max_value=len(meetings) - 1))
        meeting_to_delete = meetings[idx]
        
        # Delete the meeting
        await temp_storage.delete_meeting(meeting_to_delete.id)
        
        # Verify the meeting is not in the list
        loaded_meetings = await temp_storage.load_all_meetings()
        loaded_ids = {m.id for m in loaded_meetings}
        assert meeting_to_delete.id not in loaded_ids
        
        # Verify the meeting cannot be loaded
        loaded_meeting = await temp_storage.load_meeting(meeting_to_delete.id)
        assert loaded_meeting is None
        
        # Verify other meetings are still present
        assert len(loaded_meetings) == len(meetings) - 1
        for meeting in meetings:
            if meeting.id != meeting_to_delete.id:
                assert meeting.id in loaded_ids
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
