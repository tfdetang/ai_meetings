"""Pydantic schemas for API requests and responses"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

from ..models import (
    ModelProvider, SpeakingOrder, MeetingStatus, Agent, Meeting, Message,
    DiscussionStyle, SpeakingLength, AgendaItem, MeetingMinutes, Mention,
    MindMap, MindMapNode
)


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


class AgendaItemRequest(BaseModel):
    title: str
    description: str


class AgendaItemResponse(BaseModel):
    id: str
    title: str
    description: str
    completed: bool
    created_at: datetime
    
    @classmethod
    def from_agenda_item(cls, item: AgendaItem):
        return cls(
            id=item.id,
            title=item.title,
            description=item.description,
            completed=item.completed,
            created_at=item.created_at
        )


class MeetingCreateRequest(BaseModel):
    topic: str
    agent_ids: List[str]
    max_rounds: Optional[int] = None
    max_message_length: Optional[int] = None
    speaking_order: SpeakingOrder = SpeakingOrder.SEQUENTIAL
    moderator_id: Optional[str] = None
    moderator_type: Optional[str] = None  # 'user' or 'agent'
    agenda: Optional[List[AgendaItemRequest]] = None
    discussion_style: Optional[DiscussionStyle] = DiscussionStyle.FORMAL
    speaking_length_preferences: Optional[Dict[str, SpeakingLength]] = None
    minutes_prompt: Optional[str] = None


class ParticipantResponse(BaseModel):
    id: str
    name: str
    role_name: str


class MentionResponse(BaseModel):
    mentioned_participant_id: str
    mentioned_participant_name: str
    message_id: str
    
    @classmethod
    def from_mention(cls, mention: Mention):
        return cls(
            mentioned_participant_id=mention.mentioned_participant_id,
            mentioned_participant_name=mention.mentioned_participant_name,
            message_id=mention.message_id
        )


class MessageResponse(BaseModel):
    id: str
    speaker_id: str
    speaker_name: str
    speaker_type: str
    content: str
    timestamp: datetime
    round_number: int
    mentions: Optional[List[MentionResponse]] = None
    reasoning_content: Optional[str] = None
    
    @classmethod
    def from_message(cls, message: Message):
        return cls(
            id=message.id,
            speaker_id=message.speaker_id,
            speaker_name=message.speaker_name,
            speaker_type=message.speaker_type,
            content=message.content,
            timestamp=message.timestamp,
            round_number=message.round_number,
            mentions=[MentionResponse.from_mention(m) for m in message.mentions] if message.mentions else None,
            reasoning_content=message.reasoning_content
        )


class MeetingMinutesResponse(BaseModel):
    id: str
    content: str
    summary: str
    key_decisions: List[str]
    action_items: List[str]
    created_at: datetime
    created_by: str
    version: int
    
    @classmethod
    def from_minutes(cls, minutes: MeetingMinutes):
        return cls(
            id=minutes.id,
            content=minutes.content,
            summary=minutes.summary,
            key_decisions=minutes.key_decisions,
            action_items=minutes.action_items,
            created_at=minutes.created_at,
            created_by=minutes.created_by,
            version=minutes.version
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
    moderator_id: Optional[str] = None
    moderator_type: Optional[str] = None
    agenda: List[AgendaItemResponse] = []
    discussion_style: Optional[str] = None
    speaking_length_preferences: Optional[Dict[str, str]] = None
    current_minutes: Optional[MeetingMinutesResponse] = None
    
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
            updated_at=meeting.updated_at,
            moderator_id=meeting.moderator_id,
            moderator_type=meeting.moderator_type,
            agenda=[AgendaItemResponse.from_agenda_item(item) for item in meeting.agenda],
            discussion_style=meeting.config.discussion_style.value if meeting.config.discussion_style else None,
            speaking_length_preferences={k: v.value for k, v in meeting.config.speaking_length_preferences.items()} if meeting.config.speaking_length_preferences else None,
            current_minutes=MeetingMinutesResponse.from_minutes(meeting.current_minutes) if meeting.current_minutes else None
        )


class UserMessageRequest(BaseModel):
    message: str


class MeetingConfigUpdateRequest(BaseModel):
    max_rounds: Optional[int] = None
    max_message_length: Optional[int] = None
    speaking_order: Optional[SpeakingOrder] = None
    discussion_style: Optional[DiscussionStyle] = None
    speaking_length_preferences: Optional[Dict[str, SpeakingLength]] = None
    minutes_prompt: Optional[str] = None


class MinutesGenerateRequest(BaseModel):
    generator_id: Optional[str] = None  # Optional agent ID to use for generation


class MinutesUpdateRequest(BaseModel):
    content: str
    editor_id: str  # User or agent ID


# Mind Map schemas
class MindMapNodeResponse(BaseModel):
    id: str
    content: str
    level: int
    parent_id: Optional[str]
    children_ids: List[str]
    message_references: List[str]
    metadata: Optional[Dict] = None
    
    @classmethod
    def from_node(cls, node):
        return cls(
            id=node.id,
            content=node.content,
            level=node.level,
            parent_id=node.parent_id,
            children_ids=node.children_ids,
            message_references=node.message_references,
            metadata=node.metadata
        )


class MindMapResponse(BaseModel):
    id: str
    meeting_id: str
    root_node: MindMapNodeResponse
    nodes: Dict[str, MindMapNodeResponse]
    created_at: datetime
    created_by: str
    version: int
    
    @classmethod
    def from_mind_map(cls, mind_map):
        return cls(
            id=mind_map.id,
            meeting_id=mind_map.meeting_id,
            root_node=MindMapNodeResponse.from_node(mind_map.root_node),
            nodes={k: MindMapNodeResponse.from_node(v) for k, v in mind_map.nodes.items()},
            created_at=mind_map.created_at,
            created_by=mind_map.created_by,
            version=mind_map.version
        )


class MindMapGenerateRequest(BaseModel):
    generator_id: Optional[str] = None  # Optional agent ID to use for generation


class MindMapExportRequest(BaseModel):
    format: str  # 'png', 'svg', 'json', 'markdown'
