"""Basic tests for data models"""

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


def test_model_parameters_creation():
    """Test ModelParameters can be created"""
    params = ModelParameters(temperature=0.7, max_tokens=100)
    assert params.temperature == 0.7
    assert params.max_tokens == 100


def test_role_creation():
    """Test Role can be created"""
    role = Role(
        name="Product Manager",
        description="Focuses on user needs",
        system_prompt="You are a product manager"
    )
    assert role.name == "Product Manager"


def test_model_config_creation():
    """Test ModelConfig can be created"""
    config = ModelConfig(
        provider="openai",
        model_name="gpt-4",
        api_key="test-key"
    )
    assert config.provider == "openai"
    assert config.model_name == "gpt-4"


def test_agent_creation():
    """Test Agent can be created"""
    role = Role(
        name="Engineer",
        description="Technical expert",
        system_prompt="You are an engineer"
    )
    config = ModelConfig(
        provider="openai",
        model_name="gpt-4",
        api_key="test-key"
    )
    agent = Agent(
        id="agent-1",
        name="Alice",
        role=role,
        model_config=config
    )
    assert agent.id == "agent-1"
    assert agent.name == "Alice"


def test_meeting_config_creation():
    """Test MeetingConfig can be created"""
    config = MeetingConfig(
        max_rounds=5,
        max_message_length=1000,
        speaking_order=SpeakingOrder.SEQUENTIAL
    )
    assert config.max_rounds == 5
    assert config.speaking_order == SpeakingOrder.SEQUENTIAL


def test_message_creation():
    """Test Message can be created"""
    msg = Message(
        id="msg-1",
        speaker_id="agent-1",
        speaker_name="Alice",
        speaker_type="agent",
        content="Hello",
        timestamp=datetime.now(),
        round_number=1
    )
    assert msg.id == "msg-1"
    assert msg.content == "Hello"


def test_meeting_creation():
    """Test Meeting can be created"""
    role = Role(
        name="Engineer",
        description="Technical expert",
        system_prompt="You are an engineer"
    )
    config = ModelConfig(
        provider="openai",
        model_name="gpt-4",
        api_key="test-key"
    )
    agent = Agent(
        id="agent-1",
        name="Alice",
        role=role,
        model_config=config
    )
    
    meeting = Meeting(
        id="meeting-1",
        topic="Project Planning",
        participants=[agent],
        messages=[],
        config=MeetingConfig(),
        status=MeetingStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    assert meeting.id == "meeting-1"
    assert meeting.topic == "Project Planning"
    assert len(meeting.participants) == 1
