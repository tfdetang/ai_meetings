"""Service interfaces"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..models import (
    Agent,
    Meeting,
    MeetingConfig,
    ConversationMessage,
    ModelParameters,
)


class IModelAdapter(ABC):
    """Interface for AI model adapters"""

    @abstractmethod
    async def send_message(
        self,
        messages: List[ConversationMessage],
        system_prompt: str,
        parameters: Optional[ModelParameters] = None
    ) -> str:
        """Send message to AI model and get response"""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to AI model"""
        pass


class IAgentService(ABC):
    """Interface for agent management service"""

    @abstractmethod
    async def create_agent(self, agent_data: Dict[str, Any]) -> Agent:
        """Create new agent"""
        pass

    @abstractmethod
    async def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Agent:
        """Update agent"""
        pass

    @abstractmethod
    async def delete_agent(self, agent_id: str) -> None:
        """Delete agent"""
        pass

    @abstractmethod
    async def get_agent(self, agent_id: str) -> Agent:
        """Get agent details"""
        pass

    @abstractmethod
    async def list_agents(self) -> List[Agent]:
        """List all agents"""
        pass

    @abstractmethod
    async def test_agent_connection(self, agent_id: str) -> bool:
        """Test agent connection"""
        pass


class IMeetingService(ABC):
    """Interface for meeting management service"""

    @abstractmethod
    async def create_meeting(
        self, topic: str, agent_ids: List[str], config: MeetingConfig
    ) -> Meeting:
        """Create new meeting"""
        pass

    @abstractmethod
    async def start_meeting(self, meeting_id: str) -> None:
        """Start meeting"""
        pass

    @abstractmethod
    async def pause_meeting(self, meeting_id: str) -> None:
        """Pause meeting"""
        pass

    @abstractmethod
    async def end_meeting(self, meeting_id: str) -> None:
        """End meeting"""
        pass

    @abstractmethod
    async def add_user_message(self, meeting_id: str, content: str) -> None:
        """Add user message"""
        pass

    @abstractmethod
    async def request_agent_response(self, meeting_id: str, agent_id: str) -> None:
        """Request specific agent response"""
        pass

    @abstractmethod
    async def get_meeting(self, meeting_id: str) -> Meeting:
        """Get meeting details"""
        pass

    @abstractmethod
    async def list_meetings(self) -> List[Meeting]:
        """List all meetings"""
        pass

    @abstractmethod
    async def delete_meeting(self, meeting_id: str) -> None:
        """Delete meeting"""
        pass

    @abstractmethod
    async def export_meeting_markdown(self, meeting_id: str) -> str:
        """Export meeting to Markdown format"""
        pass

    @abstractmethod
    async def export_meeting_json(self, meeting_id: str) -> str:
        """Export meeting to JSON format"""
        pass


class IStorageService(ABC):
    """Interface for storage service"""

    @abstractmethod
    async def save_agent(self, agent: Agent) -> None:
        """Save agent"""
        pass

    @abstractmethod
    async def load_agent(self, agent_id: str) -> Optional[Agent]:
        """Load agent"""
        pass

    @abstractmethod
    async def load_all_agents(self) -> List[Agent]:
        """Load all agents"""
        pass

    @abstractmethod
    async def delete_agent(self, agent_id: str) -> None:
        """Delete agent"""
        pass

    @abstractmethod
    async def save_meeting(self, meeting: Meeting) -> None:
        """Save meeting"""
        pass

    @abstractmethod
    async def load_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Load meeting"""
        pass

    @abstractmethod
    async def load_all_meetings(self) -> List[Meeting]:
        """Load all meetings"""
        pass

    @abstractmethod
    async def delete_meeting(self, meeting_id: str) -> None:
        """Delete meeting"""
        pass
