"""Meeting service implementation"""

import uuid
import random
from datetime import datetime
from typing import List, Optional

from .interfaces import IMeetingService, IStorageService, IAgentService
from ..models import Meeting, MeetingConfig, MeetingStatus, SpeakingOrder, Agent, AgendaItem
from ..exceptions import ValidationError, NotFoundError, MeetingStateError, PermissionError, AgendaError


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
        self, 
        topic: str, 
        agent_ids: List[str], 
        config: MeetingConfig,
        moderator_id: Optional[str] = None,
        moderator_type: Optional[str] = None,
        agenda: Optional[List[AgendaItem]] = None
    ) -> Meeting:
        """
        Create new meeting
        
        Args:
            topic: Meeting topic
            agent_ids: List of agent IDs to participate
            config: Meeting configuration
            moderator_id: ID of moderator (user or agent ID)
            moderator_type: Type of moderator ('user' or 'agent')
            agenda: Initial agenda items
            
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
        
        # Validate moderator if specified
        if moderator_id and moderator_type == 'agent':
            # Verify moderator agent exists and is in participants
            if moderator_id not in agent_ids:
                raise ValidationError("Moderator agent must be a participant", "moderator_id")
        
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
            current_round=1,
            moderator_id=moderator_id,
            moderator_type=moderator_type,
            agenda=agenda if agenda else []
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

    async def end_meeting(self, meeting_id: str, auto_generate_minutes: bool = True) -> None:
        """
        End meeting (transition to ended state and persist)
        
        Args:
            meeting_id: ID of meeting to end
            auto_generate_minutes: Whether to automatically generate meeting minutes (default: True)
            
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
        
        # Auto-generate minutes if enabled and meeting has messages
        if auto_generate_minutes and meeting.messages:
            try:
                print(f"[MeetingService] Auto-generating meeting minutes...")
                
                # Use moderator as generator if available, otherwise use first participant
                generator_id = None
                if meeting.moderator_id and meeting.moderator_type == 'agent':
                    generator_id = meeting.moderator_id
                
                await self.generate_minutes(meeting_id, generator_id)
                print(f"[MeetingService] ✅ Meeting minutes auto-generated")
            except Exception as e:
                # Don't fail the end_meeting operation if minutes generation fails
                print(f"[MeetingService] ⚠️ Failed to auto-generate minutes: {str(e)}")

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
        from .context_builder import parse_mentions
        
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
        
        # Parse mentions from content
        mentions = parse_mentions(content, meeting.participants)
        
        # Set message_id for all mentions
        for mention in mentions:
            mention.message_id = message_id
        
        message = Message(
            id=message_id,
            speaker_id="user",
            speaker_name="User",
            speaker_type='user',
            content=content,
            timestamp=datetime.now(),
            round_number=meeting.current_round,
            mentions=mentions if mentions else None
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
        Get next speaker based on meeting configuration and @mentions
        
        Args:
            meeting: Meeting instance
            
        Returns:
            Next agent to speak
            
        Logic:
            1. If last message contains @mentions of AI agents, prioritize the first mentioned agent
            2. Otherwise, follow the configured speaking order (sequential or random)
        """
        from .context_builder import get_next_speaker
        
        # Check if there are any messages
        if meeting.messages:
            last_message = meeting.messages[-1]
            
            # Try to get next speaker based on mentions
            mentioned_agent_id = get_next_speaker(meeting, last_message)
            
            if mentioned_agent_id:
                # Find the agent by ID
                for participant in meeting.participants:
                    if participant.id == mentioned_agent_id:
                        return participant
        
        # No mentions or no AI agents mentioned - use default speaking order
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

    async def get_next_speaker_id(self, meeting_id: str) -> str:
        """
        Get the ID of the next agent who should speak
        
        Args:
            meeting_id: ID of meeting
            
        Returns:
            Agent ID of the next speaker
            
        Raises:
            NotFoundError: If meeting doesn't exist
            
        Note:
            This method considers @mentions in the last message and prioritizes
            mentioned AI agents. If no mentions, follows the configured speaking order.
        """
        meeting = await self.get_meeting(meeting_id)
        next_agent = self._get_next_speaker(meeting)
        return next_agent.id

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
        from ..models import Message
        from ..adapters.factory import ModelAdapterFactory
        from .context_builder import build_system_prompt, build_meeting_context, build_message_history, parse_mentions
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
        
        # Check if agent is moderator
        is_moderator = (meeting.moderator_id == agent_id and meeting.moderator_type == 'agent')
        
        # Build system prompt with role, style, length preferences, and moderator duties
        system_prompt = build_system_prompt(agent, meeting, is_moderator)
        
        # Build meeting context (topic, moderator, participants, agenda, minutes, mentions)
        meeting_context = build_meeting_context(meeting, agent_id)
        
        # Build message history (optimized with minutes if available)
        conversation_messages = build_message_history(meeting)
        
        # Prepend meeting context as a user message
        if meeting_context:
            from ..models import ConversationMessage
            conversation_messages.insert(0, ConversationMessage(
                role='user',
                content=meeting_context
            ))
        
        # Create model adapter for this agent
        print(f"[MeetingService] Creating adapter for {agent.name} ({agent.model_config.provider})")
        adapter = ModelAdapterFactory.create(agent.model_config)
        
        # Get response from AI model
        print(f"[MeetingService] Sending message to AI ({len(conversation_messages)} messages in context)...")
        ai_start_time = time.time()
        
        response_content = await adapter.send_message(
            messages=conversation_messages,
            system_prompt=system_prompt,
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
        
        # Parse mentions from agent response
        mentions = parse_mentions(response_content, meeting.participants)
        
        # Set message_id for all mentions
        for mention in mentions:
            mention.message_id = message_id
        
        message = Message(
            id=message_id,
            speaker_id=agent.id,
            speaker_name=agent.name,
            speaker_type='agent',
            content=response_content,
            timestamp=datetime.now(),
            round_number=meeting.current_round,
            mentions=mentions if mentions else None
        )
        
        # Add message to meeting
        meeting.messages.append(message)
        meeting.updated_at = datetime.now()
        
        # Check if round should be incremented
        should_auto_generate_minutes = False
        if self._should_increment_round(meeting):
            meeting.current_round += 1
            print(f"[MeetingService] Round incremented to {meeting.current_round}")
            
            # Check if max rounds reached
            if meeting.config.max_rounds is not None:
                if meeting.current_round > meeting.config.max_rounds:
                    # Auto-end meeting
                    meeting.status = MeetingStatus.ENDED
                    should_auto_generate_minutes = True
                    print(f"[MeetingService] Meeting auto-ended (max rounds reached)")
        
        # Save meeting
        print(f"[MeetingService] Saving meeting...")
        await self.storage.save_meeting(meeting)
        
        # Auto-generate minutes if meeting just ended
        if should_auto_generate_minutes:
            try:
                print(f"[MeetingService] Auto-generating meeting minutes...")
                
                # Use moderator as generator if available, otherwise use first participant
                generator_id = None
                if meeting.moderator_id and meeting.moderator_type == 'agent':
                    generator_id = meeting.moderator_id
                
                await self.generate_minutes(meeting_id, generator_id)
                print(f"[MeetingService] ✅ Meeting minutes auto-generated")
            except Exception as e:
                # Don't fail the operation if minutes generation fails
                print(f"[MeetingService] ⚠️ Failed to auto-generate minutes: {str(e)}")
        
        total_duration = time.time() - start_time
        print(f"[MeetingService] ✅ request_agent_response completed in {total_duration:.2f}s")

    async def request_agent_response_stream(self, meeting_id: str, agent_id: str):
        """
        Request specific agent response with streaming
        
        Args:
            meeting_id: ID of meeting
            agent_id: ID of agent to respond
            
        Yields:
            Streaming text chunks from AI response
            
        Raises:
            NotFoundError: If meeting or agent doesn't exist
            MeetingStateError: If meeting is not active
        """
        from ..models import Message
        from ..adapters.factory import ModelAdapterFactory
        from .context_builder import build_system_prompt, build_meeting_context, build_message_history, parse_mentions
        import time
        
        start_time = time.time()
        print(f"\n[MeetingService] request_agent_response_stream: meeting_id={meeting_id}, agent_id={agent_id}")
        
        # Load meeting
        meeting = await self.get_meeting(meeting_id)
        
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
        
        # Check if agent is moderator
        is_moderator = (meeting.moderator_id == agent_id and meeting.moderator_type == 'agent')
        
        # Build system prompt
        system_prompt = build_system_prompt(agent, meeting, is_moderator)
        
        # Build meeting context
        meeting_context = build_meeting_context(meeting, agent_id)
        
        # Build message history
        conversation_messages = build_message_history(meeting)
        
        # Prepend meeting context
        if meeting_context:
            from ..models import ConversationMessage
            conversation_messages.insert(0, ConversationMessage(
                role='user',
                content=meeting_context
            ))
        
        # Create model adapter
        adapter = ModelAdapterFactory.create(agent.model_config)
        
        # Stream response from AI model
        response_content = ""
        reasoning_content = ""
        async for chunk in adapter.send_message_stream(
            messages=conversation_messages,
            system_prompt=system_prompt,
            parameters=agent.model_config.parameters
        ):
            # Handle both dict (with type) and string chunks
            if isinstance(chunk, dict):
                chunk_type = chunk.get("type")
                chunk_content = chunk.get("content", "")
                
                if chunk_type == "reasoning":
                    reasoning_content += chunk_content
                    yield chunk  # Yield the dict with type marker
                elif chunk_type == "content":
                    response_content += chunk_content
                    yield chunk  # Yield the dict with type marker
            else:
                # Legacy string chunks (for non-GLM models)
                response_content += chunk
                yield {"type": "content", "content": chunk}
        
        # Handle message length limit
        if meeting.config.max_message_length is not None:
            if len(response_content) > meeting.config.max_message_length:
                response_content = response_content[:meeting.config.max_message_length]
                response_content += "\n[截断: 消息超过长度限制]"
        
        # Create message object
        message_id = str(uuid.uuid4())
        
        # Parse mentions from agent response
        mentions = parse_mentions(response_content, meeting.participants)
        
        # Set message_id for all mentions
        for mention in mentions:
            mention.message_id = message_id
        
        message = Message(
            id=message_id,
            speaker_id=agent.id,
            speaker_name=agent.name,
            speaker_type='agent',
            content=response_content,
            timestamp=datetime.now(),
            round_number=meeting.current_round,
            mentions=mentions if mentions else None,
            reasoning_content=reasoning_content if reasoning_content else None
        )
        
        # Add message to meeting
        meeting.messages.append(message)
        meeting.updated_at = datetime.now()
        
        # Check if round should be incremented
        should_auto_generate_minutes = False
        if self._should_increment_round(meeting):
            meeting.current_round += 1
            
            # Check if max rounds reached
            if meeting.config.max_rounds is not None:
                if meeting.current_round > meeting.config.max_rounds:
                    meeting.status = MeetingStatus.ENDED
                    should_auto_generate_minutes = True
        
        # Save meeting
        await self.storage.save_meeting(meeting)
        
        # Auto-generate minutes if meeting just ended
        if should_auto_generate_minutes:
            try:
                print(f"[MeetingService] Auto-generating meeting minutes...")
                
                # Use moderator as generator if available
                generator_id = None
                if meeting.moderator_id and meeting.moderator_type == 'agent':
                    generator_id = meeting.moderator_id
                
                await self.generate_minutes(meeting_id, generator_id)
                print(f"[MeetingService] ✅ Meeting minutes auto-generated")
            except Exception as e:
                print(f"[MeetingService] ⚠️ Failed to auto-generate minutes: {str(e)}")
        
        total_duration = time.time() - start_time
        print(f"[MeetingService] ✅ request_agent_response_stream completed in {total_duration:.2f}s")
        
        # Return the message for auto-response chain
        yield {"type": "complete", "message": message}

    def get_mentioned_agents(self, message) -> List[str]:
        """
        Get list of mentioned agent IDs from a message
        
        Args:
            message: Message object with mentions
            
        Returns:
            List of agent IDs that were mentioned
        """
        if not message.mentions:
            return []
        
        return [mention.mentioned_participant_id for mention in message.mentions]

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

    def _check_moderator_permission(self, meeting: Meeting, requester_id: str, requester_type: str) -> None:
        """
        Check if requester is the moderator
        
        Args:
            meeting: Meeting instance
            requester_id: ID of the requester
            requester_type: Type of requester ('user' or 'agent')
            
        Raises:
            PermissionError: If requester is not the moderator
        """
        if meeting.moderator_id is None:
            # No moderator set, allow operation
            return
        
        if meeting.moderator_id != requester_id or meeting.moderator_type != requester_type:
            raise PermissionError(
                f"Only the moderator can perform this operation",
                required_role="moderator"
            )

    async def add_agenda_item(self, meeting_id: str, item: AgendaItem, requester_id: str, requester_type: str) -> None:
        """
        Add agenda item to meeting (moderator only)
        
        Args:
            meeting_id: ID of meeting
            item: AgendaItem to add
            requester_id: ID of the requester
            requester_type: Type of requester ('user' or 'agent')
            
        Raises:
            NotFoundError: If meeting doesn't exist
            PermissionError: If requester is not the moderator
            ValidationError: If item data is invalid
        """
        # Load meeting
        meeting = await self.get_meeting(meeting_id)
        
        # Check permission
        self._check_moderator_permission(meeting, requester_id, requester_type)
        
        # Validate item
        if not item.title or not item.title.strip():
            raise ValidationError("Agenda item title cannot be empty", "title")
        
        if not item.description or not item.description.strip():
            raise ValidationError("Agenda item description cannot be empty", "description")
        
        # Add item to agenda
        meeting.agenda.append(item)
        meeting.updated_at = datetime.now()
        
        # Save meeting
        await self.storage.save_meeting(meeting)

    async def remove_agenda_item(self, meeting_id: str, item_id: str, requester_id: str, requester_type: str) -> None:
        """
        Remove agenda item from meeting (moderator only)
        
        Args:
            meeting_id: ID of meeting
            item_id: ID of agenda item to remove
            requester_id: ID of the requester
            requester_type: Type of requester ('user' or 'agent')
            
        Raises:
            NotFoundError: If meeting doesn't exist
            PermissionError: If requester is not the moderator
            AgendaError: If agenda item doesn't exist
        """
        # Load meeting
        meeting = await self.get_meeting(meeting_id)
        
        # Check permission
        self._check_moderator_permission(meeting, requester_id, requester_type)
        
        # Find and remove item
        item_found = False
        for i, item in enumerate(meeting.agenda):
            if item.id == item_id:
                meeting.agenda.pop(i)
                item_found = True
                break
        
        if not item_found:
            raise AgendaError(
                f"Agenda item {item_id} not found in meeting {meeting_id}",
                agenda_id=item_id
            )
        
        meeting.updated_at = datetime.now()
        
        # Save meeting
        await self.storage.save_meeting(meeting)

    async def mark_agenda_completed(self, meeting_id: str, item_id: str, requester_id: str, requester_type: str) -> None:
        """
        Mark agenda item as completed (moderator only)
        
        Args:
            meeting_id: ID of meeting
            item_id: ID of agenda item to mark as completed
            requester_id: ID of the requester
            requester_type: Type of requester ('user' or 'agent')
            
        Raises:
            NotFoundError: If meeting doesn't exist
            PermissionError: If requester is not the moderator
            AgendaError: If agenda item doesn't exist
        """
        # Load meeting
        meeting = await self.get_meeting(meeting_id)
        
        # Check permission
        self._check_moderator_permission(meeting, requester_id, requester_type)
        
        # Find and mark item as completed
        item_found = False
        for item in meeting.agenda:
            if item.id == item_id:
                item.completed = True
                item_found = True
                break
        
        if not item_found:
            raise AgendaError(
                f"Agenda item {item_id} not found in meeting {meeting_id}",
                agenda_id=item_id
            )
        
        meeting.updated_at = datetime.now()
        
        # Save meeting
        await self.storage.save_meeting(meeting)

    async def generate_minutes(self, meeting_id: str, generator_id: Optional[str] = None) -> 'MeetingMinutes':
        """
        Generate meeting minutes using AI model
        
        Args:
            meeting_id: ID of meeting
            generator_id: Optional ID of agent to use for generation (if None, uses first participant)
            
        Returns:
            Generated MeetingMinutes instance
            
        Raises:
            NotFoundError: If meeting or generator agent doesn't exist
            ValidationError: If meeting has no messages to summarize
        """
        from ..models import MeetingMinutes, ConversationMessage
        from ..adapters.factory import ModelAdapterFactory
        
        # Load meeting
        meeting = await self.get_meeting(meeting_id)
        
        # Validate meeting has messages
        if not meeting.messages:
            raise ValidationError("Cannot generate minutes for meeting with no messages", "messages")
        
        # Determine which agent to use for generation
        if generator_id:
            # Find the specified agent
            generator_agent = None
            for participant in meeting.participants:
                if participant.id == generator_id:
                    generator_agent = participant
                    break
            
            if generator_agent is None:
                raise NotFoundError(
                    f"Agent {generator_id} is not a participant in meeting {meeting_id}",
                    resource_type="agent",
                    resource_id=generator_id
                )
        else:
            # Use the first participant
            generator_agent = meeting.participants[0]
        
        # Build prompt for minutes generation
        minutes_prompt = self._build_minutes_generation_prompt(meeting)
        
        # Create model adapter
        adapter = ModelAdapterFactory.create(generator_agent.model_config)
        
        # Get AI response
        conversation_messages = [
            ConversationMessage(
                role='user',
                content=minutes_prompt
            )
        ]
        
        # 使用自定义 prompt 或默认 prompt
        if meeting.config.minutes_prompt:
            system_prompt = meeting.config.minutes_prompt
        else:
            system_prompt = """你是一名专业的会议纪要助理，请根据以下会议内容，生成清晰、准确、可执行的会议纪要。

要求：
- 结构化输出（会议背景、参会人员、讨论要点、决策事项、待办任务、风险与关注点）
- 用词客观中立，不评价人员
- 不遗漏关键数字、日期、负责人、截止时间
- 可自动识别隐含的任务和风险
- 所有待办事项以 To-Do 列表总结"""
        
        response_content = await adapter.send_message(
            messages=conversation_messages,
            system_prompt=system_prompt,
            parameters=generator_agent.model_config.parameters
        )
        
        # Parse the response to extract summary, key decisions, and action items
        summary, key_decisions, action_items = self._parse_minutes_response(response_content)
        
        # Determine version number
        version = len(meeting.minutes_history) + 1
        
        # Create MeetingMinutes object
        minutes_id = str(uuid.uuid4())
        minutes = MeetingMinutes(
            id=minutes_id,
            content=response_content,
            summary=summary,
            key_decisions=key_decisions,
            action_items=action_items,
            created_at=datetime.now(),
            created_by=generator_agent.id,
            version=version
        )
        
        # Add to minutes history
        meeting.minutes_history.append(minutes)
        
        # Set as current minutes
        meeting.current_minutes = minutes
        
        # Update meeting
        meeting.updated_at = datetime.now()
        
        # Save meeting
        await self.storage.save_meeting(meeting)
        
        return minutes

    def _build_minutes_generation_prompt(self, meeting: Meeting) -> str:
        """
        Build prompt for generating meeting minutes
        
        Args:
            meeting: Meeting instance
            
        Returns:
            Prompt string for AI model
        """
        lines = []
        
        lines.append(f"请为以下会议生成纪要：")
        lines.append(f"")
        lines.append(f"会议主题：{meeting.topic}")
        lines.append(f"")
        
        # Add agenda if present
        if meeting.agenda:
            lines.append("会议议题：")
            for item in meeting.agenda:
                status = "✓" if item.completed else "○"
                lines.append(f"{status} {item.title}: {item.description}")
            lines.append("")
        
        # Add all messages
        lines.append("会议讨论内容：")
        lines.append("")
        for msg in meeting.messages:
            lines.append(f"[{msg.speaker_name}]: {msg.content}")
            lines.append("")
        
        lines.append("请生成会议纪要，包括：")
        lines.append("1. 总体摘要（SUMMARY:）")
        lines.append("2. 关键决策（KEY DECISIONS:）- 每个决策单独一行，以 - 开头")
        lines.append("3. 待办事项（ACTION ITEMS:）- 每个事项单独一行，以 - 开头")
        lines.append("")
        lines.append("请按照以下格式输出：")
        lines.append("SUMMARY:")
        lines.append("[总体摘要内容]")
        lines.append("")
        lines.append("KEY DECISIONS:")
        lines.append("- [决策1]")
        lines.append("- [决策2]")
        lines.append("")
        lines.append("ACTION ITEMS:")
        lines.append("- [待办事项1]")
        lines.append("- [待办事项2]")
        
        return "\n".join(lines)

    def _parse_minutes_response(self, response: str) -> tuple[str, List[str], List[str]]:
        """
        Parse AI response to extract summary, key decisions, and action items
        
        Args:
            response: AI model response
            
        Returns:
            Tuple of (summary, key_decisions, action_items)
        """
        summary = ""
        key_decisions = []
        action_items = []
        
        # Split response into sections
        lines = response.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            
            if line_stripped.upper().startswith('SUMMARY:'):
                if current_section and current_content:
                    self._save_section_content(current_section, current_content, summary, key_decisions, action_items)
                current_section = 'summary'
                current_content = []
                # Check if summary is on the same line
                remainder = line_stripped[8:].strip()
                if remainder:
                    current_content.append(remainder)
            elif line_stripped.upper().startswith('KEY DECISIONS:'):
                if current_section and current_content:
                    summary = self._finalize_summary(current_content)
                current_section = 'decisions'
                current_content = []
            elif line_stripped.upper().startswith('ACTION ITEMS:'):
                if current_section == 'decisions' and current_content:
                    key_decisions = self._finalize_list(current_content)
                current_section = 'actions'
                current_content = []
            elif line_stripped:
                current_content.append(line_stripped)
        
        # Finalize last section
        if current_section == 'summary' and current_content:
            summary = self._finalize_summary(current_content)
        elif current_section == 'decisions' and current_content:
            key_decisions = self._finalize_list(current_content)
        elif current_section == 'actions' and current_content:
            action_items = self._finalize_list(current_content)
        
        # Fallback: if parsing failed, use entire response as summary
        if not summary and not key_decisions and not action_items:
            summary = response.strip()
        
        return summary, key_decisions, action_items

    def _finalize_summary(self, content_lines: List[str]) -> str:
        """Join summary lines into a single string"""
        return ' '.join(content_lines)

    def _finalize_list(self, content_lines: List[str]) -> List[str]:
        """Extract list items from content lines"""
        items = []
        for line in content_lines:
            # Remove leading dash or bullet point
            if line.startswith('- '):
                items.append(line[2:].strip())
            elif line.startswith('* '):
                items.append(line[2:].strip())
            elif line.startswith('• '):
                items.append(line[2:].strip())
            else:
                items.append(line.strip())
        return items

    def _save_section_content(self, section: str, content: List[str], summary: str, decisions: List[str], actions: List[str]) -> None:
        """Helper to save section content (not used in current implementation)"""
        pass

    async def update_minutes(self, meeting_id: str, content: str, editor_id: str) -> 'MeetingMinutes':
        """
        Update meeting minutes manually (creates new version)
        
        Args:
            meeting_id: ID of meeting
            content: New minutes content
            editor_id: ID of the editor (user or agent_id)
            
        Returns:
            Updated MeetingMinutes instance
            
        Raises:
            NotFoundError: If meeting doesn't exist
            ValidationError: If content is invalid
        """
        from ..models import MeetingMinutes
        
        # Load meeting
        meeting = await self.get_meeting(meeting_id)
        
        # Validate content
        if not content or not content.strip():
            raise ValidationError("Minutes content cannot be empty", "content")
        
        content = content.strip()
        
        # Parse the content to extract summary, key decisions, and action items
        summary, key_decisions, action_items = self._parse_minutes_response(content)
        
        # Determine version number
        version = len(meeting.minutes_history) + 1
        
        # Create new MeetingMinutes object
        minutes_id = str(uuid.uuid4())
        minutes = MeetingMinutes(
            id=minutes_id,
            content=content,
            summary=summary,
            key_decisions=key_decisions,
            action_items=action_items,
            created_at=datetime.now(),
            created_by=editor_id,
            version=version
        )
        
        # Add to minutes history
        meeting.minutes_history.append(minutes)
        
        # Set as current minutes
        meeting.current_minutes = minutes
        
        # Update meeting
        meeting.updated_at = datetime.now()
        
        # Save meeting
        await self.storage.save_meeting(meeting)
        
        return minutes

    async def update_meeting_config(self, meeting_id: str, config: MeetingConfig) -> None:
        """
        Update meeting configuration
        
        Args:
            meeting_id: ID of meeting
            config: New meeting configuration
            
        Raises:
            NotFoundError: If meeting doesn't exist
        """
        # Load meeting
        meeting = await self.get_meeting(meeting_id)
        
        # Update config
        meeting.config = config
        
        # Update timestamp
        meeting.updated_at = datetime.now()
        
        # Save meeting
        await self.storage.save_meeting(meeting)
