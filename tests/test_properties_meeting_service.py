"""Property-based tests for meeting service operations"""

import pytest
import tempfile
import shutil
from hypothesis import given, strategies as st

from src.models import (
    Agent, Role, ModelConfig, ModelParameters,
    Meeting, MeetingConfig, MeetingStatus, SpeakingOrder
)
from src.storage import FileStorageService
from src.services.agent_service import AgentService
from src.services.meeting_service import MeetingService


# Reuse strategies from other test files
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

# Meeting config strategy
meeting_config_strategy = st.builds(
    MeetingConfig,
    max_rounds=st.none() | st.integers(min_value=1, max_value=100),
    max_message_length=st.none() | st.integers(min_value=1, max_value=10000),
    speaking_order=st.sampled_from([SpeakingOrder.SEQUENTIAL, SpeakingOrder.RANDOM])
)


# Feature: ai-agent-meeting, Property 12: 会议创建要求
# Validates: Requirements 4.1
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=1, max_size=5, unique_by=lambda a: a.id),
    config=meeting_config_strategy
)
@pytest.mark.asyncio
async def test_property_meeting_creation_requirements(topic, agents, config):
    """
    Property 12: Meeting Creation Requirements
    For any meeting creation request, must include non-empty topic and at least one agent
    to successfully create.
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Verify meeting was created successfully
        assert meeting is not None
        assert meeting.id is not None
        
        # Verify topic is set correctly (stripped)
        assert meeting.topic == topic.strip()
        assert len(meeting.topic) > 0
        assert len(meeting.topic) <= 200
        
        # Verify at least one participant
        assert len(meeting.participants) >= 1
        assert len(meeting.participants) == len(agents)
        
        # Verify all participants match the provided agents
        participant_ids = {p.id for p in meeting.participants}
        expected_ids = {a.id for a in agents}
        assert participant_ids == expected_ids
        
        # Verify initial state
        assert meeting.status == MeetingStatus.ACTIVE
        assert meeting.messages == []
        assert meeting.current_round == 1
        
        # Verify config is set
        assert meeting.config == config
        
        # Verify timestamps are set
        assert meeting.created_at is not None
        assert meeting.updated_at is not None
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 27: 会议配置接受
# Validates: Requirements 7.1
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=1, max_size=5, unique_by=lambda a: a.id),
    max_rounds=st.none() | st.integers(min_value=1, max_value=100),
    max_message_length=st.none() | st.integers(min_value=1, max_value=10000),
    speaking_order=st.sampled_from([SpeakingOrder.SEQUENTIAL, SpeakingOrder.RANDOM])
)
@pytest.mark.asyncio
async def test_property_meeting_config_acceptance(topic, agents, max_rounds, max_message_length, speaking_order):
    """
    Property 27: Meeting Configuration Acceptance
    For any meeting creation request, should be able to set round limit, message length limit,
    and speaking order mode.
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create config with specified parameters
        config = MeetingConfig(
            max_rounds=max_rounds,
            max_message_length=max_message_length,
            speaking_order=speaking_order
        )
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Verify meeting was created successfully
        assert meeting is not None
        
        # Verify config parameters are set correctly
        assert meeting.config.max_rounds == max_rounds
        assert meeting.config.max_message_length == max_message_length
        assert meeting.config.speaking_order == speaking_order
        
        # Reload meeting from storage to verify persistence
        reloaded_meeting = await meeting_service.get_meeting(meeting.id)
        
        # Verify config persisted correctly
        assert reloaded_meeting.config.max_rounds == max_rounds
        assert reloaded_meeting.config.max_message_length == max_message_length
        assert reloaded_meeting.config.speaking_order == speaking_order
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)



# Feature: ai-agent-meeting, Property 17: 暂停状态保持
# Validates: Requirements 4.6
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=1, max_size=5, unique_by=lambda a: a.id),
    config=meeting_config_strategy
)
@pytest.mark.asyncio
async def test_property_pause_state_preservation(topic, agents, config):
    """
    Property 17: Pause State Preservation
    For any active meeting, after pausing, the meeting status should become 'paused'
    and the message list should not grow.
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create meeting (starts as active)
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Verify initial state
        assert meeting.status == MeetingStatus.ACTIVE
        initial_message_count = len(meeting.messages)
        
        # Pause the meeting
        await meeting_service.pause_meeting(meeting.id)
        
        # Reload meeting
        paused_meeting = await meeting_service.get_meeting(meeting.id)
        
        # Verify status changed to paused
        assert paused_meeting.status == MeetingStatus.PAUSED
        
        # Verify message list hasn't grown
        assert len(paused_meeting.messages) == initial_message_count
        
        # Verify all other properties remain the same
        assert paused_meeting.id == meeting.id
        assert paused_meeting.topic == meeting.topic
        assert len(paused_meeting.participants) == len(meeting.participants)
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 18: 结束状态持久化
# Validates: Requirements 4.7
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=1, max_size=5, unique_by=lambda a: a.id),
    config=meeting_config_strategy
)
@pytest.mark.asyncio
async def test_property_end_state_persistence(topic, agents, config):
    """
    Property 18: End State Persistence
    For any meeting, after ending, the meeting status should become 'ended'
    and the meeting should be persisted to storage.
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Verify initial state
        assert meeting.status == MeetingStatus.ACTIVE
        
        # End the meeting
        await meeting_service.end_meeting(meeting.id)
        
        # Reload meeting from storage
        ended_meeting = await meeting_service.get_meeting(meeting.id)
        
        # Verify status changed to ended
        assert ended_meeting.status == MeetingStatus.ENDED
        
        # Verify meeting is persisted (can be loaded from storage)
        assert ended_meeting is not None
        assert ended_meeting.id == meeting.id
        
        # Verify all meeting data is preserved
        assert ended_meeting.topic == meeting.topic
        assert len(ended_meeting.participants) == len(meeting.participants)
        assert len(ended_meeting.messages) == len(meeting.messages)
        
        # Verify the meeting appears in the list of all meetings
        all_meetings = await meeting_service.list_meetings()
        meeting_ids = [m.id for m in all_meetings]
        assert meeting.id in meeting_ids
        
        # Find the ended meeting in the list and verify its status
        ended_meeting_in_list = next(m for m in all_meetings if m.id == meeting.id)
        assert ended_meeting_in_list.status == MeetingStatus.ENDED
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 13: 发言顺序一致性
# Validates: Requirements 4.2, 7.5
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=2, max_size=5, unique_by=lambda a: a.id),
)
@pytest.mark.asyncio
async def test_property_speaking_order_consistency(topic, agents):
    """
    Property 13: Speaking Order Consistency
    For any meeting configured for sequential speaking, agent speaking order should
    match the participant list order.
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create config with sequential speaking order
        config = MeetingConfig(speaking_order=SpeakingOrder.SEQUENTIAL)
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Get next speakers multiple times (at least 2 full rounds)
        num_calls = len(agents) * 2
        speakers = []
        for _ in range(num_calls):
            speaker = meeting_service._get_next_speaker(meeting)
            speakers.append(speaker.id)
        
        # Verify the order matches participant list order
        expected_order = [agent.id for agent in meeting.participants]
        
        # Check that speakers cycle through in the expected order
        for i in range(num_calls):
            expected_speaker_id = expected_order[i % len(expected_order)]
            assert speakers[i] == expected_speaker_id, \
                f"At position {i}, expected {expected_speaker_id} but got {speakers[i]}"
        
        # Verify the pattern repeats correctly
        first_round = speakers[:len(agents)]
        second_round = speakers[len(agents):len(agents)*2]
        assert first_round == second_round, "Sequential order should repeat consistently"
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 30: 随机顺序变化
# Validates: Requirements 7.4
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=3, max_size=5, unique_by=lambda a: a.id),
)
@pytest.mark.asyncio
async def test_property_random_order_variation(topic, agents):
    """
    Property 30: Random Order Variation
    For any meeting configured for random speaking, in multiple rounds at least one round's
    speaking order should differ from the initial order (when agent count >= 3).
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create config with random speaking order
        config = MeetingConfig(speaking_order=SpeakingOrder.RANDOM)
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Get the initial participant order
        initial_order = [agent.id for agent in meeting.participants]
        
        # Collect speakers over many rounds to check for variation
        # With random selection, we should see variation
        num_rounds = 20
        rounds = []
        for _ in range(num_rounds):
            round_speakers = []
            for _ in range(len(agents)):
                speaker = meeting_service._get_next_speaker(meeting)
                round_speakers.append(speaker.id)
            rounds.append(round_speakers)
        
        # Verify that random selection is working:
        # At least one round should differ from the initial order
        # (This is probabilistic but with 20 rounds and 3+ agents, 
        # the probability of all matching is astronomically low)
        variation_found = any(round_order != initial_order for round_order in rounds)
        
        # With 3+ agents and 20 rounds, we should see variation
        # The probability of no variation is extremely low
        assert variation_found, \
            "Random speaking order should produce variation over multiple rounds"
        
        # Also verify that all agents can be selected (no agent is excluded)
        all_selected_agents = set()
        for round_speakers in rounds:
            all_selected_agents.update(round_speakers)
        
        expected_agent_ids = set(agent.id for agent in agents)
        assert all_selected_agents == expected_agent_ids, \
            "All agents should be selectable in random mode"
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 10: 角色提示词传递
# Validates: Requirements 3.2
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=1, max_size=3, unique_by=lambda a: a.id),
)
@pytest.mark.asyncio
async def test_property_role_prompt_passing(topic, agents):
    """
    Property 10: Role Prompt Passing
    For any agent speaking, the message sent to the AI model should include
    that agent's role description as the system prompt.
    """
    from unittest.mock import patch, AsyncMock
    from tests.mock_adapter import MockModelAdapter
    
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create config
        config = MeetingConfig(speaking_order=SpeakingOrder.SEQUENTIAL)
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Test each agent
        for agent in agents:
            # Create a mock adapter that captures the system prompt
            mock_adapter = MockModelAdapter(response_template=f"Response from {agent.name}")
            
            # Patch the factory to return our mock adapter
            with patch('src.adapters.factory.ModelAdapterFactory.create', return_value=mock_adapter):
                # Request agent response
                await meeting_service.request_agent_response(meeting.id, agent.id)
                
                # Verify the system prompt matches the agent's role system prompt
                assert mock_adapter.last_system_prompt == agent.role.system_prompt, \
                    f"System prompt should match agent's role system prompt"
                
                # Verify send_message was called
                assert mock_adapter.call_count == 1, "send_message should be called once"
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 14: 会议上下文传递
# Validates: Requirements 4.3
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=2, max_size=3, unique_by=lambda a: a.id),
    num_prior_messages=st.integers(min_value=1, max_value=5)
)
@pytest.mark.asyncio
async def test_property_meeting_context_passing(topic, agents, num_prior_messages):
    """
    Property 14: Meeting Context Passing
    For any agent speaking, the context sent to the AI model should include
    all messages from before that moment in the meeting.
    """
    from unittest.mock import patch
    from tests.mock_adapter import MockModelAdapter
    
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create config
        config = MeetingConfig(speaking_order=SpeakingOrder.SEQUENTIAL)
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Create mock adapter
        mock_adapter = MockModelAdapter(response_template="Test response")
        
        # Have agents speak multiple times to build up context
        with patch('src.adapters.factory.ModelAdapterFactory.create', return_value=mock_adapter):
            for i in range(num_prior_messages):
                agent = agents[i % len(agents)]
                await meeting_service.request_agent_response(meeting.id, agent.id)
            
            # Get the meeting state before the next call
            meeting_before = await meeting_service.get_meeting(meeting.id)
            message_count_before = len(meeting_before.messages)
            
            # Reset mock to track the next call
            mock_adapter.call_count = 0
            mock_adapter.last_messages = None
            
            # Request one more response
            next_agent = agents[num_prior_messages % len(agents)]
            await meeting_service.request_agent_response(meeting.id, next_agent.id)
            
            # Verify the context includes all prior messages
            assert mock_adapter.last_messages is not None, "Messages should be passed to adapter"
            assert len(mock_adapter.last_messages) == message_count_before, \
                f"Context should include all {message_count_before} prior messages"
            
            # Verify the content matches
            for i, msg in enumerate(meeting_before.messages):
                assert mock_adapter.last_messages[i].content == msg.content, \
                    f"Message {i} content should match"
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 15: 消息记录增长
# Validates: Requirements 4.4
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=1, max_size=3, unique_by=lambda a: a.id),
)
@pytest.mark.asyncio
async def test_property_message_record_growth(topic, agents):
    """
    Property 15: Message Record Growth
    For any agent or user speaking, the meeting's message list length should increase by 1.
    """
    from unittest.mock import patch
    from tests.mock_adapter import MockModelAdapter
    
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create config
        config = MeetingConfig(speaking_order=SpeakingOrder.SEQUENTIAL)
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Get initial message count
        initial_count = len(meeting.messages)
        
        # Create mock adapter
        mock_adapter = MockModelAdapter(response_template="Test response")
        
        # Have each agent speak once
        with patch('src.adapters.factory.ModelAdapterFactory.create', return_value=mock_adapter):
            for agent in agents:
                # Get message count before
                meeting_before = await meeting_service.get_meeting(meeting.id)
                count_before = len(meeting_before.messages)
                
                # Request agent response
                await meeting_service.request_agent_response(meeting.id, agent.id)
                
                # Get message count after
                meeting_after = await meeting_service.get_meeting(meeting.id)
                count_after = len(meeting_after.messages)
                
                # Verify count increased by exactly 1
                assert count_after == count_before + 1, \
                    f"Message count should increase by 1 (was {count_before}, now {count_after})"
        
        # Verify total growth
        final_meeting = await meeting_service.get_meeting(meeting.id)
        assert len(final_meeting.messages) == initial_count + len(agents), \
            f"Total message count should be {initial_count + len(agents)}"
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 29: 消息长度截断
# Validates: Requirements 7.3
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=1, max_size=2, unique_by=lambda a: a.id),
    max_length=st.integers(min_value=10, max_value=100)
)
@pytest.mark.asyncio
async def test_property_message_length_truncation(topic, agents, max_length):
    """
    Property 29: Message Length Truncation
    For any agent response exceeding the length limit, the stored message should be
    truncated and include a truncation marker.
    """
    from unittest.mock import patch
    from tests.mock_adapter import MockModelAdapter
    
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create config with message length limit
        config = MeetingConfig(
            speaking_order=SpeakingOrder.SEQUENTIAL,
            max_message_length=max_length
        )
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Create a long response that exceeds the limit
        long_response = "A" * (max_length + 50)
        mock_adapter = MockModelAdapter(response_template=long_response)
        
        # Request agent response with mock that returns long message
        with patch('src.adapters.factory.ModelAdapterFactory.create', return_value=mock_adapter):
            agent = agents[0]
            await meeting_service.request_agent_response(meeting.id, agent.id)
            
            # Get the meeting and check the message
            meeting_after = await meeting_service.get_meeting(meeting.id)
            assert len(meeting_after.messages) == 1, "Should have one message"
            
            stored_message = meeting_after.messages[0]
            
            # Verify the message was truncated
            assert len(stored_message.content) <= max_length + 50, \
                "Message should be truncated (including marker)"
            
            # Verify truncation marker is present
            assert "[截断: 消息超过长度限制]" in stored_message.content, \
                "Truncation marker should be present"
            
            # Verify the message starts with the original content
            assert stored_message.content.startswith("A" * max_length), \
                "Message should start with original content up to limit"
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 16: 轮次递增
# Validates: Requirements 4.5
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=2, max_size=4, unique_by=lambda a: a.id),
)
@pytest.mark.asyncio
async def test_property_round_increment(topic, agents):
    """
    Property 16: Round Increment
    For any meeting, when all participating agents complete one round of speaking,
    the round counter should increase by 1.
    """
    from unittest.mock import patch
    from tests.mock_adapter import MockModelAdapter
    
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create config
        config = MeetingConfig(speaking_order=SpeakingOrder.SEQUENTIAL)
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Verify initial round
        assert meeting.current_round == 1, "Initial round should be 1"
        
        # Create mock adapter
        mock_adapter = MockModelAdapter(response_template="Test response")
        
        # Have all agents speak once (complete one round)
        with patch('src.adapters.factory.ModelAdapterFactory.create', return_value=mock_adapter):
            for i, agent in enumerate(agents):
                # Request agent response
                await meeting_service.request_agent_response(meeting.id, agent.id)
                
                # Get meeting state
                meeting_state = await meeting_service.get_meeting(meeting.id)
                
                # If this is the last agent in the round, round should increment
                if i == len(agents) - 1:
                    assert meeting_state.current_round == 2, \
                        f"Round should increment to 2 after all {len(agents)} agents speak"
                else:
                    # Otherwise, should still be in round 1
                    assert meeting_state.current_round == 1, \
                        f"Round should still be 1 after {i+1} of {len(agents)} agents speak"
            
            # Have all agents speak again (complete second round)
            for i, agent in enumerate(agents):
                await meeting_service.request_agent_response(meeting.id, agent.id)
                
                meeting_state = await meeting_service.get_meeting(meeting.id)
                
                if i == len(agents) - 1:
                    assert meeting_state.current_round == 3, \
                        "Round should increment to 3 after second complete round"
                else:
                    assert meeting_state.current_round == 2, \
                        "Round should still be 2 during second round"
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 28: 轮次限制自动结束
# Validates: Requirements 7.2
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=2, max_size=3, unique_by=lambda a: a.id),
    max_rounds=st.integers(min_value=1, max_value=3)
)
@pytest.mark.asyncio
async def test_property_round_limit_auto_end(topic, agents, max_rounds):
    """
    Property 28: Round Limit Auto End
    For any meeting with a round limit set, when the limit is reached,
    the meeting should automatically transition to 'ended' status.
    """
    from unittest.mock import patch
    from tests.mock_adapter import MockModelAdapter
    
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create config with round limit
        config = MeetingConfig(
            speaking_order=SpeakingOrder.SEQUENTIAL,
            max_rounds=max_rounds
        )
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Verify initial state
        assert meeting.status == MeetingStatus.ACTIVE, "Meeting should start as active"
        assert meeting.current_round == 1, "Should start at round 1"
        
        # Create mock adapter
        mock_adapter = MockModelAdapter(response_template="Test response")
        
        # Have agents speak for max_rounds complete rounds
        with patch('src.adapters.factory.ModelAdapterFactory.create', return_value=mock_adapter):
            for round_num in range(max_rounds):
                for agent in agents:
                    # Get meeting state before
                    meeting_before = await meeting_service.get_meeting(meeting.id)
                    
                    # Request agent response
                    await meeting_service.request_agent_response(meeting.id, agent.id)
                    
                    # Get meeting state after
                    meeting_after = await meeting_service.get_meeting(meeting.id)
                    
                    # Check if this was the last agent in the last round
                    is_last_agent = agent.id == agents[-1].id
                    is_last_round = round_num == max_rounds - 1
                    
                    if is_last_agent and is_last_round:
                        # Meeting should auto-end after completing max_rounds
                        assert meeting_after.status == MeetingStatus.ENDED, \
                            f"Meeting should auto-end after {max_rounds} complete rounds"
                        assert meeting_after.current_round == max_rounds + 1, \
                            f"Round should be {max_rounds + 1} when ended"
                    elif is_last_agent:
                        # Round should increment but meeting should still be active
                        assert meeting_after.status == MeetingStatus.ACTIVE, \
                            f"Meeting should still be active in round {round_num + 1}"
                        assert meeting_after.current_round == round_num + 2, \
                            f"Round should increment to {round_num + 2}"
        
        # Verify final state
        final_meeting = await meeting_service.get_meeting(meeting.id)
        assert final_meeting.status == MeetingStatus.ENDED, \
            "Meeting should be ended after reaching round limit"
        
        # Verify we have the expected number of messages
        expected_messages = max_rounds * len(agents)
        assert len(final_meeting.messages) == expected_messages, \
            f"Should have {expected_messages} messages ({max_rounds} rounds × {len(agents)} agents)"
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 19: 用户消息上下文传递
# Validates: Requirements 5.2
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=1, max_size=3, unique_by=lambda a: a.id),
    user_message=st.text(min_size=1, max_size=500, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip())
)
@pytest.mark.asyncio
async def test_property_user_message_context_passing(topic, agents, user_message):
    """
    Property 19: User Message Context Passing
    For any user message sent in a meeting, that message should appear in the context
    of subsequent agent responses.
    """
    from unittest.mock import patch
    from tests.mock_adapter import MockModelAdapter
    
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create config
        config = MeetingConfig(speaking_order=SpeakingOrder.SEQUENTIAL)
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Add user message
        await meeting_service.add_user_message(meeting.id, user_message)
        
        # Verify user message was added
        meeting_after_user = await meeting_service.get_meeting(meeting.id)
        assert len(meeting_after_user.messages) == 1
        # Content should be stripped
        assert meeting_after_user.messages[0].content == user_message.strip()
        assert meeting_after_user.messages[0].speaker_type == 'user'
        
        # Create mock adapter
        mock_adapter = MockModelAdapter(response_template="Agent response")
        
        # Request agent response
        with patch('src.adapters.factory.ModelAdapterFactory.create', return_value=mock_adapter):
            agent = agents[0]
            await meeting_service.request_agent_response(meeting.id, agent.id)
            
            # Verify the user message was included in the context
            assert mock_adapter.last_messages is not None, "Messages should be passed to adapter"
            assert len(mock_adapter.last_messages) >= 1, "Context should include at least the user message"
            
            # Find the user message in the context (content is stripped)
            stripped_user_message = user_message.strip()
            user_message_found = False
            for msg in mock_adapter.last_messages:
                if msg.content == stripped_user_message and msg.role == 'user':
                    user_message_found = True
                    break
            
            assert user_message_found, "User message should be in the context passed to agent"
            
            # Verify the first message in context is the user message
            assert mock_adapter.last_messages[0].content == stripped_user_message, \
                "User message should be first in context"
            assert mock_adapter.last_messages[0].role == 'user', \
                "User message should have 'user' role"
        
        # Verify the meeting now has both messages
        final_meeting = await meeting_service.get_meeting(meeting.id)
        assert len(final_meeting.messages) == 2, "Should have user message and agent response"
        assert final_meeting.messages[0].speaker_type == 'user'
        assert final_meeting.messages[1].speaker_type == 'agent'
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 20: 指定代理响应
# Validates: Requirements 5.3
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=2, max_size=5, unique_by=lambda a: a.id),
)
@pytest.mark.asyncio
async def test_property_specified_agent_response(topic, agents):
    """
    Property 20: Specified Agent Response
    For any user-specified agent, that agent should become the next speaker.
    """
    from unittest.mock import patch
    from tests.mock_adapter import MockModelAdapter
    
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create config
        config = MeetingConfig(speaking_order=SpeakingOrder.SEQUENTIAL)
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Create mock adapter
        mock_adapter = MockModelAdapter(response_template="Test response")
        
        # Test requesting response from each agent specifically
        with patch('src.adapters.factory.ModelAdapterFactory.create', return_value=mock_adapter):
            for target_agent in agents:
                # Get message count before
                meeting_before = await meeting_service.get_meeting(meeting.id)
                message_count_before = len(meeting_before.messages)
                
                # Request response from specific agent
                await meeting_service.request_agent_response(meeting.id, target_agent.id)
                
                # Get meeting after
                meeting_after = await meeting_service.get_meeting(meeting.id)
                
                # Verify a new message was added
                assert len(meeting_after.messages) == message_count_before + 1, \
                    "A new message should be added"
                
                # Verify the new message is from the specified agent
                new_message = meeting_after.messages[-1]
                assert new_message.speaker_id == target_agent.id, \
                    f"Message should be from specified agent {target_agent.id}"
                assert new_message.speaker_name == target_agent.name, \
                    f"Message should have speaker name {target_agent.name}"
                assert new_message.speaker_type == 'agent', \
                    "Message should be from an agent"
        
        # Verify all agents have spoken
        final_meeting = await meeting_service.get_meeting(meeting.id)
        assert len(final_meeting.messages) == len(agents), \
            f"Should have {len(agents)} messages (one from each agent)"
        
        # Verify each agent spoke exactly once
        speaker_ids = [msg.speaker_id for msg in final_meeting.messages]
        assert len(set(speaker_ids)) == len(agents), \
            "Each agent should have spoken exactly once"
        
        # Verify all agents are represented
        for agent in agents:
            assert agent.id in speaker_ids, \
                f"Agent {agent.id} should have spoken"
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# Feature: ai-agent-meeting, Property 25: 会议导出格式
# Validates: Requirements 6.4
@given(
    topic=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agents=st.lists(agent_strategy, min_size=1, max_size=3, unique_by=lambda a: a.id),
    config=meeting_config_strategy
)
@pytest.mark.asyncio
async def test_property_meeting_export_format(topic, agents, config):
    """
    Property 25: Meeting Export Format
    For any meeting, the export operation should return valid Markdown or JSON format strings.
    """
    import json
    from unittest.mock import patch
    from tests.mock_adapter import MockModelAdapter
    
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        meeting_service = MeetingService(temp_storage, agent_service)
        
        # Save all agents first
        for agent in agents:
            await temp_storage.save_agent(agent)
        
        # Extract agent IDs
        agent_ids = [agent.id for agent in agents]
        
        # Create meeting
        meeting = await meeting_service.create_meeting(topic, agent_ids, config)
        
        # Add some messages to make the export more interesting
        mock_adapter = MockModelAdapter(response_template="Test response")
        with patch('src.adapters.factory.ModelAdapterFactory.create', return_value=mock_adapter):
            # Add a user message
            await meeting_service.add_user_message(meeting.id, "Test user message")
            
            # Have first agent respond
            if len(agents) > 0:
                await meeting_service.request_agent_response(meeting.id, agents[0].id)
        
        # Test Markdown export
        markdown_export = await meeting_service.export_meeting_markdown(meeting.id)
        
        # Verify Markdown export is a non-empty string
        assert isinstance(markdown_export, str), "Markdown export should be a string"
        assert len(markdown_export) > 0, "Markdown export should not be empty"
        
        # Verify Markdown contains key elements
        assert topic.strip() in markdown_export, "Markdown should contain meeting topic"
        assert meeting.id in markdown_export, "Markdown should contain meeting ID"
        
        # Verify Markdown contains participant information
        for agent in agents:
            assert agent.name in markdown_export, f"Markdown should contain agent name {agent.name}"
        
        # Verify Markdown contains messages if any exist
        meeting_state = await meeting_service.get_meeting(meeting.id)
        if len(meeting_state.messages) > 0:
            for msg in meeting_state.messages:
                assert msg.content in markdown_export, \
                    f"Markdown should contain message content: {msg.content[:50]}"
        
        # Verify Markdown has proper structure (headers)
        assert "# " in markdown_export, "Markdown should have headers"
        assert "## " in markdown_export, "Markdown should have subheaders"
        
        # Test JSON export
        json_export = await meeting_service.export_meeting_json(meeting.id)
        
        # Verify JSON export is a non-empty string
        assert isinstance(json_export, str), "JSON export should be a string"
        assert len(json_export) > 0, "JSON export should not be empty"
        
        # Verify JSON is valid by parsing it
        try:
            parsed_json = json.loads(json_export)
        except json.JSONDecodeError as e:
            pytest.fail(f"JSON export is not valid JSON: {e}")
        
        # Verify JSON contains all required fields
        assert "id" in parsed_json, "JSON should contain meeting ID"
        assert "topic" in parsed_json, "JSON should contain topic"
        assert "participants" in parsed_json, "JSON should contain participants"
        assert "messages" in parsed_json, "JSON should contain messages"
        assert "config" in parsed_json, "JSON should contain config"
        assert "status" in parsed_json, "JSON should contain status"
        assert "created_at" in parsed_json, "JSON should contain created_at"
        assert "updated_at" in parsed_json, "JSON should contain updated_at"
        
        # Verify JSON data matches meeting data
        assert parsed_json["id"] == meeting.id, "JSON ID should match meeting ID"
        assert parsed_json["topic"] == topic.strip(), "JSON topic should match meeting topic"
        assert len(parsed_json["participants"]) == len(agents), \
            "JSON should have correct number of participants"
        
        # Verify all messages are in JSON
        assert len(parsed_json["messages"]) == len(meeting_state.messages), \
            "JSON should contain all messages"
        
        # Verify each message has required metadata
        for json_msg in parsed_json["messages"]:
            assert "speaker_id" in json_msg, "JSON message should have speaker_id"
            assert "speaker_name" in json_msg, "JSON message should have speaker_name"
            assert "speaker_type" in json_msg, "JSON message should have speaker_type"
            assert "content" in json_msg, "JSON message should have content"
            assert "timestamp" in json_msg, "JSON message should have timestamp"
            assert "round_number" in json_msg, "JSON message should have round_number"
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
