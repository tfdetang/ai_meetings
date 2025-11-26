"""Meeting data models"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

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


@dataclass
class MeetingConfig:
    """Configuration for a meeting"""
    max_rounds: Optional[int] = None
    max_message_length: Optional[int] = None
    speaking_order: SpeakingOrder = SpeakingOrder.SEQUENTIAL

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'max_rounds': self.max_rounds,
            'max_message_length': self.max_message_length,
            'speaking_order': self.speaking_order.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeetingConfig':
        """Create from dictionary"""
        return cls(
            max_rounds=data.get('max_rounds'),
            max_message_length=data.get('max_message_length'),
            speaking_order=SpeakingOrder(data.get('speaking_order', 'sequential')),
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

    def __post_init__(self):
        """Validate meeting fields"""
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
        lines.append("")
        
        # Participants
        lines.append("## Participants")
        for participant in self.participants:
            lines.append(f"- **{participant.name}** ({participant.role.name})")
        lines.append("")
        
        # Configuration
        lines.append("## Configuration")
        lines.append(f"- **Speaking Order**: {self.config.speaking_order.value}")
        if self.config.max_rounds is not None:
            lines.append(f"- **Max Rounds**: {self.config.max_rounds}")
        if self.config.max_message_length is not None:
            lines.append(f"- **Max Message Length**: {self.config.max_message_length}")
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
