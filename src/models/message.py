"""Message data models"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Literal, Dict, Any, List, Optional

SpeakerType = Literal['agent', 'user']


@dataclass
class Mention:
    """Represents a mention (@) of a participant in a message"""
    mentioned_participant_id: str
    mentioned_participant_name: str
    message_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Mention':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class Message:
    """Message in a meeting"""
    id: str
    speaker_id: str
    speaker_name: str
    speaker_type: SpeakerType
    content: str
    timestamp: datetime
    round_number: int
    mentions: Optional[List[Mention]] = None
    reasoning_content: Optional[str] = None  # 思考过程（仅用于显示，不参与上下文传递和导出）

    def __post_init__(self):
        """Validate message fields"""
        self.validate()

    def validate(self) -> None:
        """Validate message data"""
        from ..exceptions import ValidationError
        
        if not self.content or not self.content.strip():
            raise ValidationError("Message content cannot be empty or whitespace only", "content")
        
        if len(self.content) > 10000:
            raise ValidationError("Message content must be 10000 characters or less", "content")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'speaker_id': self.speaker_id,
            'speaker_name': self.speaker_name,
            'speaker_type': self.speaker_type,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'round_number': self.round_number,
            'mentions': [m.to_dict() for m in self.mentions] if self.mentions else None,
            'reasoning_content': self.reasoning_content
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create from dictionary"""
        data_copy = data.copy()
        if isinstance(data_copy['timestamp'], str):
            data_copy['timestamp'] = datetime.fromisoformat(data_copy['timestamp'])
        if data_copy.get('mentions'):
            data_copy['mentions'] = [Mention.from_dict(m) for m in data_copy['mentions']]
        return cls(**data_copy)

    def format_display(self) -> str:
        """
        Format message for display with metadata
        
        Returns:
            Formatted string with speaker identity, timestamp, and content
        """
        timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        speaker_label = f"[{self.speaker_type.upper()}] {self.speaker_name}"
        return f"{timestamp_str} | {speaker_label}\n{self.content}"


@dataclass
class ConversationMessage:
    """Message format for AI model conversation"""
    role: Literal['system', 'user', 'assistant']
    content: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
