"""Property-based tests for data models"""

import pytest
from hypothesis import given, strategies as st
from datetime import datetime

from src.models import (
    Agent,
    Role,
    ModelConfig,
    ModelParameters,
    Message,
)
from src.exceptions import ValidationError


# Strategies for generating valid test data
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

agent_strategy = st.builds(
    Agent,
    id=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    role=role_strategy,
    model_config=model_config_strategy
)


# Feature: ai-agent-meeting, Property 1: 代理创建完整性
# Validates: Requirements 1.1
@given(
    provider=st.sampled_from(['openai', 'anthropic', 'google', 'glm']),
    model_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    api_key=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    role_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    role_description=st.text(min_size=1, max_size=2000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    system_prompt=st.text(min_size=1, max_size=2000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agent_id=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    agent_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
)
def test_property_agent_creation_integrity(
    provider, model_name, api_key, role_name, role_description, 
    system_prompt, agent_id, agent_name
):
    """
    Property 1: Agent Creation Integrity
    For any valid agent configuration (containing provider, model name, API key, and role description),
    the agent object returned after creation should contain all specified fields.
    """
    # Create role
    role = Role(
        name=role_name,
        description=role_description,
        system_prompt=system_prompt
    )
    
    # Create model config
    model_config = ModelConfig(
        provider=provider,
        model_name=model_name,
        api_key=api_key
    )
    
    # Create agent
    agent = Agent(
        id=agent_id,
        name=agent_name,
        role=role,
        model_config=model_config
    )
    
    # Verify all fields are present and match
    assert agent.id == agent_id
    assert agent.name == agent_name
    assert agent.role.name == role_name
    assert agent.role.description == role_description
    assert agent.role.system_prompt == system_prompt
    assert agent.model_config.provider == provider
    assert agent.model_config.model_name == model_name
    assert agent.model_config.api_key == api_key


# Feature: ai-agent-meeting, Property 11: 角色描述验证
# Validates: Requirements 3.3
# Feature: ai-agent-meeting, Property 9: 角色字段完整性
# Validates: Requirements 3.1
@given(
    role_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    role_description=st.text(min_size=1, max_size=2000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    system_prompt=st.text(min_size=1, max_size=2000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip())
)
def test_property_role_field_integrity(role_name, role_description, system_prompt):
    """
    Property 9: Role Field Integrity
    For any role configuration containing role name, background description, and behavior guidance,
    the system should accept and store all fields.
    """
    # Create role with all three fields
    role = Role(
        name=role_name,
        description=role_description,
        system_prompt=system_prompt
    )
    
    # Verify all fields are present and match the input
    assert role.name == role_name
    assert role.description == role_description
    assert role.system_prompt == system_prompt
    
    # Verify fields are accessible and non-empty
    assert role.name.strip()
    assert role.description.strip()
    assert role.system_prompt.strip()


@given(
    role_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    # Generate invalid descriptions: empty or too long
    invalid_description=st.one_of(
        st.just(""),  # Empty string
        st.just("   "),  # Whitespace only
        st.text(min_size=2001, max_size=3000, alphabet=st.characters(blacklist_categories=('Cs',)))  # Too long
    ),
    system_prompt=st.text(min_size=1, max_size=2000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip())
)
def test_property_role_description_validation(role_name, invalid_description, system_prompt):
    """
    Property 11: Role Description Validation
    For any role description, empty descriptions or descriptions exceeding length limits (1-2000 characters)
    should be rejected.
    """
    # Attempt to create role with invalid description should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        Role(
            name=role_name,
            description=invalid_description,
            system_prompt=system_prompt
        )
    
    # Verify the error is about the description field
    assert exc_info.value.field == "description"


@given(
    role_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    valid_description=st.text(min_size=1, max_size=2000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    system_prompt=st.text(min_size=1, max_size=2000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip())
)
def test_property_role_description_validation_accepts_valid(role_name, valid_description, system_prompt):
    """
    Property 11 (positive case): Role Description Validation
    For any valid role description (1-2000 characters, non-empty), it should be accepted.
    """
    # Valid description should be accepted
    role = Role(
        name=role_name,
        description=valid_description,
        system_prompt=system_prompt
    )
    
    assert role.description == valid_description


# Feature: ai-agent-meeting, Property 21: 空消息拒绝
# Validates: Requirements 5.4
@given(
    message_id=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    speaker_id=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    speaker_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    speaker_type=st.sampled_from(['agent', 'user']),
    # Generate empty or whitespace-only content
    empty_content=st.one_of(
        st.just(""),  # Empty string
        st.text(min_size=1, max_size=50, alphabet=st.just(' ')),  # Whitespace only
        st.text(min_size=1, max_size=50, alphabet=st.just('\t')),  # Tabs only
        st.text(min_size=1, max_size=50, alphabet=st.just('\n')),  # Newlines only
        st.text(min_size=1, max_size=50, alphabet=st.sampled_from([' ', '\t', '\n']))  # Mixed whitespace
    ),
    round_number=st.integers(min_value=1, max_value=1000)
)
def test_property_empty_message_rejection(
    message_id, speaker_id, speaker_name, speaker_type, empty_content, round_number
):
    """
    Property 21: Empty Message Rejection
    For any empty message or pure whitespace message, the system should reject submission
    and the meeting state should remain unchanged.
    """
    # Attempt to create message with empty/whitespace content should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        Message(
            id=message_id,
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            speaker_type=speaker_type,
            content=empty_content,
            timestamp=datetime.now(),
            round_number=round_number
        )
    
    # Verify the error is about the content field
    assert exc_info.value.field == "content"


@given(
    message_id=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    speaker_id=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    speaker_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    speaker_type=st.sampled_from(['agent', 'user']),
    # Generate valid content (non-empty, not just whitespace)
    valid_content=st.text(min_size=1, max_size=10000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    round_number=st.integers(min_value=1, max_value=1000)
)
def test_property_empty_message_rejection_accepts_valid(
    message_id, speaker_id, speaker_name, speaker_type, valid_content, round_number
):
    """
    Property 21 (positive case): Empty Message Rejection
    For any valid message content (non-empty, not just whitespace), it should be accepted.
    """
    # Valid content should be accepted
    message = Message(
        id=message_id,
        speaker_id=speaker_id,
        speaker_name=speaker_name,
        speaker_type=speaker_type,
        content=valid_content,
        timestamp=datetime.now(),
        round_number=round_number
    )
    
    assert message.content == valid_content


# Feature: ai-agent-meeting, Property 22: 消息元数据完整性
# Validates: Requirements 6.1
@given(
    message_id=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    speaker_id=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    speaker_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    speaker_type=st.sampled_from(['agent', 'user']),
    content=st.text(min_size=1, max_size=10000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    round_number=st.integers(min_value=1, max_value=1000)
)
def test_property_message_metadata_integrity(
    message_id, speaker_id, speaker_name, speaker_type, content, round_number
):
    """
    Property 22: Message Metadata Integrity
    For any meeting message, it should include speaker identity, content, and timestamp.
    """
    # Create message
    timestamp = datetime.now()
    message = Message(
        id=message_id,
        speaker_id=speaker_id,
        speaker_name=speaker_name,
        speaker_type=speaker_type,
        content=content,
        timestamp=timestamp,
        round_number=round_number
    )
    
    # Verify all metadata fields are present
    assert message.speaker_id == speaker_id
    assert message.speaker_name == speaker_name
    assert message.speaker_type == speaker_type
    assert message.content == content
    assert message.timestamp == timestamp
    assert message.round_number == round_number
    
    # Verify formatted display includes speaker identity and timestamp
    formatted = message.format_display()
    assert speaker_name in formatted
    assert content in formatted
    # Verify timestamp is in the formatted output (check for date components)
    assert str(timestamp.year) in formatted
