"""Meeting data models"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Literal

from .agent import Agent
from .message import Message


class SpeakingOrder(Enum):
    """Order in which agents speak"""
    SEQUENTIAL = 'sequential'
    RANDOM = 'random'


class MeetingStatus(Enum):
    """Status of a meeting"""
    ACTIVE = 'active'
    PAUSED = 'paused'
    ENDED = 'ended'


class DiscussionStyle(Enum):
    """Discussion style for a meeting"""
    FORMAL = 'formal'
    CASUAL = 'casual'
    DEBATE = 'debate'


class SpeakingLength(Enum):
    """Speaking length preference"""
    BRIEF = 'brief'
    MODERATE = 'moderate'
    DETAILED = 'detailed'


@dataclass
class AgendaItem:
    """Agenda item for a meeting"""
    id: str
    title: str
    description: str
    completed: bool = False
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Set created_at if not provided"""
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgendaItem':
        """Create from dictionary"""
        data_copy = data.copy()
        if data_copy.get('created_at') and isinstance(data_copy['created_at'], str):
            data_copy['created_at'] = datetime.fromisoformat(data_copy['created_at'])
        return cls(**data_copy)


@dataclass
class MeetingMinutes:
    """Meeting minutes/summary"""
    id: str
    content: str
    summary: str
    key_decisions: List[str]
    action_items: List[str]
    created_at: datetime
    created_by: str  # user or agent_id
    version: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'content': self.content,
            'summary': self.summary,
            'key_decisions': self.key_decisions,
            'action_items': self.action_items,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'version': self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeetingMinutes':
        """Create from dictionary"""
        data_copy = data.copy()
        if isinstance(data_copy['created_at'], str):
            data_copy['created_at'] = datetime.fromisoformat(data_copy['created_at'])
        return cls(**data_copy)


@dataclass
class MeetingConfig:
    """Configuration for a meeting"""
    max_rounds: Optional[int] = None
    max_message_length: Optional[int] = None
    speaking_order: SpeakingOrder = SpeakingOrder.SEQUENTIAL
    discussion_style: DiscussionStyle = DiscussionStyle.FORMAL
    speaking_length_preferences: Optional[Dict[str, SpeakingLength]] = None
    minutes_prompt: Optional[str] = None  # 自定义会议纪要生成提示词

    def __post_init__(self):
        """Set defaults"""
        if self.speaking_length_preferences is None:
            self.speaking_length_preferences = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'max_rounds': self.max_rounds,
            'max_message_length': self.max_message_length,
            'speaking_order': self.speaking_order.value,
            'discussion_style': self.discussion_style.value,
            'speaking_length_preferences': {k: v.value for k, v in self.speaking_length_preferences.items()} if self.speaking_length_preferences else {},
            'minutes_prompt': self.minutes_prompt,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeetingConfig':
        """Create from dictionary"""
        speaking_length_prefs = data.get('speaking_length_preferences', {})
        if speaking_length_prefs:
            speaking_length_prefs = {k: SpeakingLength(v) for k, v in speaking_length_prefs.items()}
        
        return cls(
            max_rounds=data.get('max_rounds'),
            max_message_length=data.get('max_message_length'),
            speaking_order=SpeakingOrder(data.get('speaking_order', 'sequential')),
            discussion_style=DiscussionStyle(data.get('discussion_style', 'formal')),
            speaking_length_preferences=speaking_length_prefs,
            minutes_prompt=data.get('minutes_prompt'),
        )


@dataclass
class Meeting:
    """Meeting representation"""
    id: str
    topic: str
    participants: List[Agent]
    messages: List[Message]
    config: MeetingConfig
    status: MeetingStatus
    created_at: datetime
    updated_at: datetime
    current_round: int = 1
    moderator_id: Optional[str] = None
    moderator_type: Optional[Literal['user', 'agent']] = None
    agenda: Optional[List[AgendaItem]] = None
    minutes_history: Optional[List[MeetingMinutes]] = None
    current_minutes: Optional[MeetingMinutes] = None

    def __post_init__(self):
        """Validate meeting fields and set defaults"""
        if self.agenda is None:
            self.agenda = []
        if self.minutes_history is None:
            self.minutes_history = []
        self.validate()

    def validate(self) -> None:
        """Validate meeting data"""
        from ..exceptions import ValidationError
        
        if not self.topic or not self.topic.strip():
            raise ValidationError("Meeting topic cannot be empty", "topic")
        
        if len(self.topic) > 200:
            raise ValidationError("Meeting topic must be 200 characters or less", "topic")
        
        if not self.participants or len(self.participants) == 0:
            raise ValidationError("Meeting must have at least one participant", "participants")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'topic': self.topic,
            'participants': [p.to_dict() for p in self.participants],
            'messages': [m.to_dict() for m in self.messages],
            'config': self.config.to_dict(),
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'current_round': self.current_round,
            'moderator_id': self.moderator_id,
            'moderator_type': self.moderator_type,
            'agenda': [item.to_dict() for item in self.agenda] if self.agenda else [],
            'minutes_history': [m.to_dict() for m in self.minutes_history] if self.minutes_history else [],
            'current_minutes': self.current_minutes.to_dict() if self.current_minutes else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Meeting':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            topic=data['topic'],
            participants=[Agent.from_dict(p) for p in data['participants']],
            messages=[Message.from_dict(m) for m in data['messages']],
            config=MeetingConfig.from_dict(data['config']),
            status=MeetingStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            current_round=data.get('current_round', 1),
            moderator_id=data.get('moderator_id'),
            moderator_type=data.get('moderator_type'),
            agenda=[AgendaItem.from_dict(item) for item in data.get('agenda', [])],
            minutes_history=[MeetingMinutes.from_dict(m) for m in data.get('minutes_history', [])],
            current_minutes=MeetingMinutes.from_dict(data['current_minutes']) if data.get('current_minutes') else None,
        )

    def export_to_markdown(self) -> str:
        """
        Export meeting to Markdown format
        
        Returns:
            Markdown-formatted string with all meeting data and messages
        """
        lines = []
        
        # Header
        lines.append(f"# {self.topic}")
        lines.append("")
        
        # Metadata
        lines.append("## Meeting Information")
        lines.append(f"- **Meeting ID**: {self.id}")
        lines.append(f"- **Status**: {self.status.value}")
        lines.append(f"- **Created**: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- **Updated**: {self.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- **Current Round**: {self.current_round}")
        if self.moderator_id:
            moderator_label = f"{self.moderator_type}: {self.moderator_id}"
            lines.append(f"- **Moderator**: {moderator_label}")
        lines.append("")
        
        # Participants
        lines.append("## Participants")
        for participant in self.participants:
            lines.append(f"- **{participant.name}** ({participant.role.name})")
        lines.append("")
        
        # Agenda
        if self.agenda:
            lines.append("## Agenda")
            for item in self.agenda:
                status_mark = "✓" if item.completed else "○"
                lines.append(f"{status_mark} **{item.title}**: {item.description}")
            lines.append("")
        
        # Current Minutes
        if self.current_minutes:
            lines.append("## Current Meeting Minutes")
            lines.append(f"**Version**: {self.current_minutes.version}")
            lines.append(f"**Created by**: {self.current_minutes.created_by}")
            lines.append(f"**Created at**: {self.current_minutes.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")
            lines.append("### Summary")
            lines.append(self.current_minutes.summary)
            lines.append("")
            if self.current_minutes.key_decisions:
                lines.append("### Key Decisions")
                for decision in self.current_minutes.key_decisions:
                    lines.append(f"- {decision}")
                lines.append("")
            if self.current_minutes.action_items:
                lines.append("### Action Items")
                for item in self.current_minutes.action_items:
                    lines.append(f"- {item}")
                lines.append("")
        
        # Configuration
        lines.append("## Configuration")
        lines.append(f"- **Speaking Order**: {self.config.speaking_order.value}")
        lines.append(f"- **Discussion Style**: {self.config.discussion_style.value}")
        if self.config.max_rounds is not None:
            lines.append(f"- **Max Rounds**: {self.config.max_rounds}")
        if self.config.max_message_length is not None:
            lines.append(f"- **Max Message Length**: {self.config.max_message_length}")
        if self.config.speaking_length_preferences:
            lines.append("- **Speaking Length Preferences**:")
            for participant_id, preference in self.config.speaking_length_preferences.items():
                lines.append(f"  - {participant_id}: {preference.value}")
        lines.append("")
        
        # Messages
        lines.append("## Discussion")
        if not self.messages:
            lines.append("*No messages yet*")
        else:
            for msg in self.messages:
                lines.append(f"### Round {msg.round_number} - {msg.speaker_name} ({msg.speaker_type})")
                lines.append(f"*{msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*")
                lines.append("")
                lines.append(msg.content)
                lines.append("")
        
        return "\n".join(lines)

    def export_to_json(self) -> str:
        """
        Export meeting to JSON format
        
        Returns:
            JSON-formatted string with all meeting data and messages
        """
        import json
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
