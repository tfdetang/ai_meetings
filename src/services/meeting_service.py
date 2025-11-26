"""Meeting service implementation"""

import uuid
import random
from datetime import datetime
from typing import List, Optional

from .interfaces import IMeetingService, IStorageService, IAgentService
from ..models import Meeting, MeetingConfig, MeetingStatus, SpeakingOrder, Agent
from ..exceptions import ValidationError, NotFoundError, MeetingStateError


class MeetingService(IMeetingService):
    """Service for managing meetings"""

    def __init__(self, storage: IStorageService, agent_service: IAgentService):
        """
        Initialize meeting service
        
        Args:
            storage: Storage service for persisting meetings
            agent_service: Agent service for retrieving agents
        """
        self.storage = storage
        self.agent_service = agent_service
        self._speaker_indices = {}  # Track current speaker index for each meeting

    async def create_meeting(
        self, topic: str, agent_ids: List[str], config: MeetingConfig
    ) -> Meeting:
        """
        Create new meeting
        
        Args:
            topic: Meeting topic
            agent_ids: List of agent IDs to participate
            config: Meeting configuration
            
        Returns:
            Created Meeting instance
            
        Raises:
            ValidationError: If input data is invalid
            NotFoundError: If any agent doesn't exist
        """
        # Validate topic
        if not topic or not topic.strip():
            raise ValidationError("Meeting topic cannot be empty", "topic")
        
        topic = topic.strip()
        if len(topic) > 200:
            raise ValidationError("Meeting topic must be 200 characters or less", "topic")
        
        # Validate agent_ids
        if not agent_ids or len(agent_ids) == 0:
            raise ValidationError("Meeting must have at least one participant", "agent_ids")
        
        # Load all agents and verify they exist
        participants = []
        for agent_id in agent_ids:
            agent = await self.agent_service.get_agent(agent_id)
            participants.append(agent)
        
        # Generate unique ID
        meeting_id = str(uuid.uuid4())
        
        # Create meeting with initial state
        now = datetime.now()
        meeting = Meeting(
            id=meeting_id,
            topic=topic,
            participants=participants,
            messages=[],
            config=config,
            status=MeetingStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            current_round=1
        )
        
        # Save meeting
        await self.storage.save_meeting(meeting)
        
        return meeting

    async def start_meeting(self, meeting_id: str) -> None:
        """
        Start meeting (transition to active state)
        
        Args:
            meeting_id: ID of meeting to start
            
        Raises:
            NotFoundError: If meeting doesn't exist
            MeetingStateError: If meeting is already ended
        """
        meeting = await self.get_meeting(meeting_id)
        
        # Validate state transition
        if meeting.status == MeetingStatus.ENDED:
            raise MeetingStateError(
                "Cannot start an ended meeting",
                current_state=meeting.status
            )
        
        # Update status
        meeting.status = MeetingStatus.ACTIVE
        meeting.updated_at = datetime.now()
        
        # Save meeting
        await self.storage.save_meeting(meeting)

    async def pause_meeting(self, meeting_id: str) -> None:
        """
        Pause meeting
        
        Args:
            meeting_id: ID of meeting to pause
            
        Raises:
            NotFoundError: If meeting doesn't exist
            MeetingStateError: If meeting is not active
        """
        meeting = await self.get_meeting(meeting_id)
        
        # Validate state transition
        if meeting.status != MeetingStatus.ACTIVE:
            raise MeetingStateError(
                f"Cannot pause meeting in {meeting.status.value} state",
                current_state=meeting.status
            )
        
        # Update status
        meeting.status = MeetingStatus.PAUSED
        meeting.updated_at = datetime.now()
        
        # Save meeting
        await self.storage.save_meeting(meeting)

    async def end_meeting(self, meeting_id: str) -> None:
        """
        End meeting (transition to ended state and persist)
        
        Args:
            meeting_id: ID of meeting to end
            
        Raises:
            NotFoundError: If meeting doesn't exist
            MeetingStateError: If meeting is already ended
        """
        meeting = await self.get_meeting(meeting_id)
        
        # Validate state transition
        if meeting.status == MeetingStatus.ENDED:
            raise MeetingStateError(
                "Meeting is already ended",
                current_state=meeting.status
            )
        
        # Update status
        meeting.status = MeetingStatus.ENDED
        meeting.updated_at = datetime.now()
        
        # Save meeting (persist)
        await self.storage.save_meeting(meeting)

    async def add_user_message(self, meeting_id: str, content: str) -> None:
        """
        Add user message to meeting
        
        Args:
            meeting_id: ID of meeting
            content: Message content
            
        Raises:
            NotFoundError: If meeting doesn't exist
            ValidationError: If content is invalid
            MeetingStateError: If meeting is not active
        """
        from ..models import Message
        
        # Load meeting
        meeting = await self.get_meeting(meeting_id)
        
        # Verify meeting is active
        if meeting.status != MeetingStatus.ACTIVE:
            raise MeetingStateError(
                f"Cannot add user message in {meeting.status.value} state",
                current_state=meeting.status
            )
        
        # Validate content (non-empty, length limit)
        if not content or not content.strip():
            raise ValidationError("Message content cannot be empty or whitespace only", "content")
        
        content = content.strip()
        if len(content) > 10000:
            raise ValidationError("Message content must be 10000 characters or less", "content")
        
        # Create message object
        message_id = str(uuid.uuid4())
        message = Message(
            id=message_id,
            speaker_id="user",
            speaker_name="User",
            speaker_type='user',
            content=content,
            timestamp=datetime.now(),
            round_number=meeting.current_round
        )
        
        # Add message to meeting
        meeting.messages.append(message)
        meeting.updated_at = datetime.now()
        
        # Save meeting
        await self.storage.save_meeting(meeting)

    def _get_next_speaker_sequential(self, meeting: Meeting) -> Agent:
        """
        Get next speaker in sequential order
        
        Args:
            meeting: Meeting instance
            
        Returns:
            Next agent to speak
        """
        # Initialize speaker index if not exists
        if meeting.id not in self._speaker_indices:
            self._speaker_indices[meeting.id] = 0
        
        # Get current index
        current_index = self._speaker_indices[meeting.id]
        
        # Get next speaker
        next_speaker = meeting.participants[current_index % len(meeting.participants)]
        
        # Increment index for next time
        self._speaker_indices[meeting.id] = (current_index + 1) % len(meeting.participants)
        
        return next_speaker

    def _get_next_speaker_random(self, meeting: Meeting) -> Agent:
        """
        Get next speaker in random order
        
        Args:
            meeting: Meeting instance
            
        Returns:
            Randomly selected agent to speak
        """
        return random.choice(meeting.participants)

    def _get_next_speaker(self, meeting: Meeting) -> Agent:
        """
        Get next speaker based on meeting configuration
        
        Args:
            meeting: Meeting instance
            
        Returns:
            Next agent to speak
        """
        if meeting.config.speaking_order == SpeakingOrder.SEQUENTIAL:
            return self._get_next_speaker_sequential(meeting)
        else:  # RANDOM
            return self._get_next_speaker_random(meeting)

    def _should_increment_round(self, meeting: Meeting) -> bool:
        """
        Check if round should be incremented
        
        Args:
            meeting: Meeting instance
            
        Returns:
            True if all participants have spoken in current round
        """
        # Count messages in current round
        messages_in_round = [
            m for m in meeting.messages 
            if m.round_number == meeting.current_round and m.speaker_type == 'agent'
        ]
        
        # Round is complete when all participants have spoken
        return len(messages_in_round) >= len(meeting.participants)

    async def request_agent_response(self, meeting_id: str, agent_id: str) -> None:
        """
        Request specific agent response
        
        Args:
            meeting_id: ID of meeting
            agent_id: ID of agent to respond
            
        Raises:
            NotFoundError: If meeting or agent doesn't exist
            MeetingStateError: If meeting is not active
        """
        from ..models import Message, ConversationMessage
        from ..adapters.factory import ModelAdapterFactory
        import time
        
        start_time = time.time()
        print(f"\n[MeetingService] request_agent_response: meeting_id={meeting_id}, agent_id={agent_id}")
        
        # Load meeting
        meeting = await self.get_meeting(meeting_id)
        print(f"[MeetingService] Meeting loaded: {meeting.topic}, status={meeting.status.value}")
        
        # Verify meeting is active
        if meeting.status != MeetingStatus.ACTIVE:
            raise MeetingStateError(
                f"Cannot request agent response in {meeting.status.value} state",
                current_state=meeting.status
            )
        
        # Find the agent in participants
        agent = None
        for participant in meeting.participants:
            if participant.id == agent_id:
                agent = participant
                break
        
        if agent is None:
            raise NotFoundError(
                f"Agent {agent_id} is not a participant in meeting {meeting_id}",
                resource_type="agent",
                resource_id=agent_id
            )
        
        # Build conversation context from meeting history
        conversation_messages = []
        for msg in meeting.messages:
            # Map speaker type to conversation role
            if msg.speaker_type == 'user':
                role = 'user'
            else:  # agent
                role = 'assistant'
            
            conversation_messages.append(
                ConversationMessage(role=role, content=msg.content)
            )
        
        # Create model adapter for this agent
        print(f"[MeetingService] Creating adapter for {agent.name} ({agent.model_config.provider})")
        adapter = ModelAdapterFactory.create(agent.model_config)
        
        # Get response from AI model
        print(f"[MeetingService] Sending message to AI ({len(conversation_messages)} messages in context)...")
        ai_start_time = time.time()
        
        response_content = await adapter.send_message(
            messages=conversation_messages,
            system_prompt=agent.role.system_prompt,
            parameters=agent.model_config.parameters
        )
        
        ai_duration = time.time() - ai_start_time
        print(f"[MeetingService] ✅ AI response received in {ai_duration:.2f}s, length={len(response_content)} chars")
        
        # Handle message length limit if configured
        if meeting.config.max_message_length is not None:
            if len(response_content) > meeting.config.max_message_length:
                response_content = response_content[:meeting.config.max_message_length]
                response_content += "\n[截断: 消息超过长度限制]"
        
        # Create message object
        message_id = str(uuid.uuid4())
        message = Message(
            id=message_id,
            speaker_id=agent.id,
            speaker_name=agent.name,
            speaker_type='agent',
            content=response_content,
            timestamp=datetime.now(),
            round_number=meeting.current_round
        )
        
        # Add message to meeting
        meeting.messages.append(message)
        meeting.updated_at = datetime.now()
        
        # Check if round should be incremented
        if self._should_increment_round(meeting):
            meeting.current_round += 1
            print(f"[MeetingService] Round incremented to {meeting.current_round}")
            
            # Check if max rounds reached
            if meeting.config.max_rounds is not None:
                if meeting.current_round > meeting.config.max_rounds:
                    # Auto-end meeting
                    meeting.status = MeetingStatus.ENDED
                    print(f"[MeetingService] Meeting auto-ended (max rounds reached)")
        
        # Save meeting
        print(f"[MeetingService] Saving meeting...")
        await self.storage.save_meeting(meeting)
        
        total_duration = time.time() - start_time
        print(f"[MeetingService] ✅ request_agent_response completed in {total_duration:.2f}s")

    async def get_meeting(self, meeting_id: str) -> Meeting:
        """
        Get meeting details
        
        Args:
            meeting_id: ID of meeting to retrieve
            
        Returns:
            Meeting instance
            
        Raises:
            NotFoundError: If meeting doesn't exist
        """
        meeting = await self.storage.load_meeting(meeting_id)
        if meeting is None:
            raise NotFoundError(
                f"Meeting {meeting_id} not found",
                resource_type="meeting",
                resource_id=meeting_id
            )
        return meeting

    async def list_meetings(self) -> List[Meeting]:
        """
        List all meetings
        
        Returns:
            List of all Meeting instances
        """
        return await self.storage.load_all_meetings()

    async def delete_meeting(self, meeting_id: str) -> None:
        """
        Delete meeting
        
        Args:
            meeting_id: ID of meeting to delete
            
        Raises:
            NotFoundError: If meeting doesn't exist
        """
        await self.storage.delete_meeting(meeting_id)

    async def export_meeting_markdown(self, meeting_id: str) -> str:
        """
        Export meeting to Markdown format
        
        Args:
            meeting_id: ID of meeting to export
            
        Returns:
            Markdown-formatted string with all meeting data
            
        Raises:
            NotFoundError: If meeting doesn't exist
        """
        meeting = await self.get_meeting(meeting_id)
        return meeting.export_to_markdown()

    async def export_meeting_json(self, meeting_id: str) -> str:
        """
        Export meeting to JSON format
        
        Args:
            meeting_id: ID of meeting to export
            
        Returns:
            JSON-formatted string with all meeting data
            
        Raises:
            NotFoundError: If meeting doesn't exist
        """
        meeting = await self.get_meeting(meeting_id)
        return meeting.export_to_json()
