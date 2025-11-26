"""Pydantic schemas for API requests and responses"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

from ..models import ModelProvider, SpeakingOrder, MeetingStatus, Agent, Meeting, Message


class AgentCreateRequest(BaseModel):
    name: str
    provider: ModelProvider
    model: str
    api_key: str
    role_name: Optional[str] = None
    role_description: Optional[str] = None
    role_prompt: Optional[str] = None
    template_name: Optional[str] = None


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    role_name: Optional[str] = None
    role_description: Optional[str] = None
    role_prompt: Optional[str] = None


class RoleResponse(BaseModel):
    name: str
    description: str
    prompt: str


class AgentResponse(BaseModel):
    id: str
    name: str
    provider: str
    model: str
    role: RoleResponse
    
    @classmethod
    def from_agent(cls, agent: Agent):
        return cls(
            id=agent.id,
            name=agent.name,
            provider=agent.model_config.provider,
            model=agent.model_config.model_name,
            role=RoleResponse(
                name=agent.role.name,
                description=agent.role.description,
                prompt=agent.role.system_prompt
            )
        )


class TemplateResponse(BaseModel):
    name: str
    role_name: str
    description: str


class MeetingCreateRequest(BaseModel):
    topic: str
    agent_ids: List[str]
    max_rounds: Optional[int] = None
    max_message_length: Optional[int] = None
    speaking_order: SpeakingOrder = SpeakingOrder.SEQUENTIAL


class ParticipantResponse(BaseModel):
    id: str
    name: str
    role_name: str


class MessageResponse(BaseModel):
    id: str
    speaker_id: str
    speaker_name: str
    speaker_type: str
    content: str
    timestamp: datetime
    round_number: int
    
    @classmethod
    def from_message(cls, message: Message):
        return cls(
            id=message.id,
            speaker_id=message.speaker_id,
            speaker_name=message.speaker_name,
            speaker_type=message.speaker_type,
            content=message.content,
            timestamp=message.timestamp,
            round_number=message.round_number
        )


class MeetingResponse(BaseModel):
    id: str
    topic: str
    status: str
    current_round: int
    participants: List[ParticipantResponse]
    messages: List[MessageResponse]
    max_rounds: Optional[int]
    max_message_length: Optional[int]
    speaking_order: str
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_meeting(cls, meeting: Meeting):
        return cls(
            id=meeting.id,
            topic=meeting.topic,
            status=meeting.status.value,
            current_round=meeting.current_round,
            participants=[
                ParticipantResponse(
                    id=p.id,
                    name=p.name,
                    role_name=p.role.name
                )
                for p in meeting.participants
            ],
            messages=[MessageResponse.from_message(m) for m in meeting.messages],
            max_rounds=meeting.config.max_rounds,
            max_message_length=meeting.config.max_message_length,
            speaking_order=meeting.config.speaking_order.value,
            created_at=meeting.created_at,
            updated_at=meeting.updated_at
        )


class UserMessageRequest(BaseModel):
    message: str
