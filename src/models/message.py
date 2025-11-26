"""Message data models"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Literal, Dict, Any

SpeakerType = Literal['agent', 'user']


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
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create from dictionary"""
        data_copy = data.copy()
        if isinstance(data_copy['timestamp'], str):
            data_copy['timestamp'] = datetime.fromisoformat(data_copy['timestamp'])
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
