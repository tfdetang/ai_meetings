"""File-based storage service implementation"""

import json
import os
from pathlib import Path
from typing import List, Optional

from ..models import Agent, Meeting
from ..services.interfaces import IStorageService
from ..exceptions import NotFoundError


class FileStorageService(IStorageService):
    """File system storage implementation"""

    def __init__(self, base_path: str = "data"):
        """
        Initialize file storage service
        
        Args:
            base_path: Base directory for storing data
        """
        self.base_path = Path(base_path)
        self.agents_path = self.base_path / "agents"
        self.meetings_path = self.base_path / "meetings"
        
        # Create directories if they don't exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure storage directories exist"""
        self.agents_path.mkdir(parents=True, exist_ok=True)
        self.meetings_path.mkdir(parents=True, exist_ok=True)

    def _get_agent_file_path(self, agent_id: str) -> Path:
        """Get file path for an agent"""
        return self.agents_path / f"{agent_id}.json"

    def _get_meeting_file_path(self, meeting_id: str) -> Path:
        """Get file path for a meeting"""
        return self.meetings_path / f"{meeting_id}.json"

    async def save_agent(self, agent: Agent) -> None:
        """Save agent to file system"""
        file_path = self._get_agent_file_path(agent.id)
        try:
            data = agent.to_dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise IOError(f"Failed to save agent {agent.id}: {str(e)}") from e

    async def load_agent(self, agent_id: str) -> Optional[Agent]:
        """Load agent from file system"""
        file_path = self._get_agent_file_path(agent_id)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Agent.from_dict(data)
        except (IOError, OSError, json.JSONDecodeError) as e:
            raise IOError(f"Failed to load agent {agent_id}: {str(e)}") from e

    async def load_all_agents(self) -> List[Agent]:
        """Load all agents from file system"""
        agents = []
        
        try:
            for file_path in self.agents_path.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    agent = Agent.from_dict(data)
                    agents.append(agent)
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    # Log error but continue loading other agents
                    print(f"Warning: Failed to load agent from {file_path}: {str(e)}")
                    continue
        except (IOError, OSError) as e:
            raise IOError(f"Failed to list agents: {str(e)}") from e
        
        return agents

    async def delete_agent(self, agent_id: str) -> None:
        """Delete agent from file system"""
        file_path = self._get_agent_file_path(agent_id)
        
        if not file_path.exists():
            raise NotFoundError(
                f"Agent {agent_id} not found",
                resource_type="agent",
                resource_id=agent_id
            )
        
        try:
            file_path.unlink()
        except (IOError, OSError) as e:
            raise IOError(f"Failed to delete agent {agent_id}: {str(e)}") from e

    async def save_meeting(self, meeting: Meeting) -> None:
        """Save meeting to file system"""
        file_path = self._get_meeting_file_path(meeting.id)
        try:
            data = meeting.to_dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise IOError(f"Failed to save meeting {meeting.id}: {str(e)}") from e

    async def load_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Load meeting from file system"""
        file_path = self._get_meeting_file_path(meeting_id)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Meeting.from_dict(data)
        except (IOError, OSError, json.JSONDecodeError) as e:
            raise IOError(f"Failed to load meeting {meeting_id}: {str(e)}") from e

    async def load_all_meetings(self) -> List[Meeting]:
        """Load all meetings from file system"""
        meetings = []
        
        try:
            for file_path in self.meetings_path.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    meeting = Meeting.from_dict(data)
                    meetings.append(meeting)
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    # Log error but continue loading other meetings
                    print(f"Warning: Failed to load meeting from {file_path}: {str(e)}")
                    continue
        except (IOError, OSError) as e:
            raise IOError(f"Failed to list meetings: {str(e)}") from e
        
        return meetings

    async def delete_meeting(self, meeting_id: str) -> None:
        """Delete meeting from file system"""
        file_path = self._get_meeting_file_path(meeting_id)
        
        if not file_path.exists():
            raise NotFoundError(
                f"Meeting {meeting_id} not found",
                resource_type="meeting",
                resource_id=meeting_id
            )
        
        try:
            file_path.unlink()
        except (IOError, OSError) as e:
            raise IOError(f"Failed to delete meeting {meeting_id}: {str(e)}") from e
