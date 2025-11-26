"""Data models for the AI Agent Meeting System"""

from .agent import Agent, Role, ModelConfig, ModelParameters, ModelProvider
from .meeting import (
    Meeting, MeetingConfig, MeetingStatus, SpeakingOrder, 
    AgendaItem, MeetingMinutes, DiscussionStyle, SpeakingLength
)
from .message import Message, SpeakerType, ConversationMessage, Mention
from .role_templates import (
    get_role_template,
    list_role_templates,
    get_all_role_templates,
    get_role_template_info,
    ROLE_TEMPLATES
)

__all__ = [
    'Agent',
    'Role',
    'ModelConfig',
    'ModelParameters',
    'ModelProvider',
    'Meeting',
    'MeetingConfig',
    'MeetingStatus',
    'SpeakingOrder',
    'AgendaItem',
    'MeetingMinutes',
    'DiscussionStyle',
    'SpeakingLength',
    'Message',
    'SpeakerType',
    'ConversationMessage',
    'Mention',
    'get_role_template',
    'list_role_templates',
    'get_all_role_templates',
    'get_role_template_info',
    'ROLE_TEMPLATES',
]
