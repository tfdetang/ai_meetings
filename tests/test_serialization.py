"""Test serialization and deserialization of models"""

import pytest
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


def test_model_parameters_round_trip():
    """Test ModelParameters serialization round trip"""
    params = ModelParameters(temperature=0.7, max_tokens=100, top_p=0.9)
    data = params.to_dict()
    restored = ModelParameters.from_dict(data)
    assert restored.temperature == params.temperature
    assert restored.max_tokens == params.max_tokens
    assert restored.top_p == params.top_p


def test_role_round_trip():
    """Test Role serialization round trip"""
    role = Role(
        name="Product Manager",
        description="Focuses on user needs",
        system_prompt="You are a product manager"
    )
    data = role.to_dict()
    restored = Role.from_dict(data)
    assert restored.name == role.name
    assert restored.description == role.description
    assert restored.system_prompt == role.system_prompt


def test_model_config_round_trip():
    """Test ModelConfig serialization round trip"""
    config = ModelConfig(
        provider="openai",
        model_name="gpt-4",
        api_key="test-key",
        parameters=ModelParameters(temperature=0.7)
    )
    data = config.to_dict()
    restored = ModelConfig.from_dict(data)
    assert restored.provider == config.provider
    assert restored.model_name == config.model_name
    assert restored.api_key == config.api_key
    assert restored.parameters.temperature == config.parameters.temperature


def test_agent_round_trip():
    """Test Agent serialization round trip"""
    role = Role(
        name="Engineer",
        description="Technical expert",
        system_prompt="You are an engineer"
    )
    config = ModelConfig(
        provider="anthropic",
        model_name="claude-3",
        api_key="test-key"
    )
    agent = Agent(
        id="agent-1",
        name="Alice",
        role=role,
        model_config=config
    )
    data = agent.to_dict()
    restored = Agent.from_dict(data)
    assert restored.id == agent.id
    assert restored.name == agent.name
    assert restored.role.name == agent.role.name
    assert restored.model_config.provider == agent.model_config.provider


def test_message_round_trip():
    """Test Message serialization round trip"""
    now = datetime.now()
    msg = Message(
        id="msg-1",
        speaker_id="agent-1",
        speaker_name="Alice",
        speaker_type="agent",
        content="Hello world",
        timestamp=now,
        round_number=1
    )
    data = msg.to_dict()
    restored = Message.from_dict(data)
    assert restored.id == msg.id
    assert restored.speaker_id == msg.speaker_id
    assert restored.content == msg.content
    assert restored.timestamp.isoformat() == msg.timestamp.isoformat()


def test_meeting_config_round_trip():
    """Test MeetingConfig serialization round trip"""
    config = MeetingConfig(
        max_rounds=5,
        max_message_length=1000,
        speaking_order=SpeakingOrder.RANDOM
    )
    data = config.to_dict()
    restored = MeetingConfig.from_dict(data)
    assert restored.max_rounds == config.max_rounds
    assert restored.max_message_length == config.max_message_length
    assert restored.speaking_order == config.speaking_order


def test_meeting_round_trip():
    """Test Meeting serialization round trip"""
    role = Role(
        name="Engineer",
        description="Technical expert",
        system_prompt="You are an engineer"
    )
    model_config = ModelConfig(
        provider="google",
        model_name="gemini-pro",
        api_key="test-key"
    )
    agent = Agent(
        id="agent-1",
        name="Alice",
        role=role,
        model_config=model_config
    )
    
    now = datetime.now()
    msg = Message(
        id="msg-1",
        speaker_id="agent-1",
        speaker_name="Alice",
        speaker_type="agent",
        content="Hello",
        timestamp=now,
        round_number=1
    )
    
    meeting = Meeting(
        id="meeting-1",
        topic="Project Planning",
        participants=[agent],
        messages=[msg],
        config=MeetingConfig(max_rounds=3),
        status=MeetingStatus.ACTIVE,
        created_at=now,
        updated_at=now,
        current_round=1
    )
    
    data = meeting.to_dict()
    restored = Meeting.from_dict(data)
    
    assert restored.id == meeting.id
    assert restored.topic == meeting.topic
    assert len(restored.participants) == 1
    assert restored.participants[0].name == "Alice"
    assert len(restored.messages) == 1
    assert restored.messages[0].content == "Hello"
    assert restored.status == meeting.status
    assert restored.current_round == meeting.current_round
