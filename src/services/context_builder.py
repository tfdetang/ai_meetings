"""Context building utilities for meeting agent responses"""

import re
from typing import List
from ..models import Agent, Meeting, Message, ConversationMessage, DiscussionStyle, SpeakingLength, Mention


def build_system_prompt(agent: Agent, meeting: Meeting, is_moderator: bool) -> str:
    """
    Build system prompt for an agent
    
    Args:
        agent: Agent instance
        meeting: Meeting instance
        is_moderator: Whether the agent is the moderator
        
    Returns:
        Complete system prompt string with role, style, length preferences, and moderator duties
    """
    prompt_parts = []
    
    # Basic role
    prompt_parts.append(f"你的角色：{agent.role.name}")
    prompt_parts.append(f"角色描述：{agent.role.description}")
    prompt_parts.append(agent.role.system_prompt)
    
    # Discussion style
    style_guide = {
        DiscussionStyle.FORMAL: "请保持正式、专业的讨论风格",
        DiscussionStyle.CASUAL: "请使用轻松、友好的讨论风格",
        DiscussionStyle.DEBATE: "请采用辩论式风格，清晰表达观点并提供论据"
    }
    prompt_parts.append(style_guide[meeting.config.discussion_style])
    
    # Speaking length preference
    length_guide = {
        SpeakingLength.BRIEF: "请保持发言简短，直接表达要点",
        SpeakingLength.MODERATE: "请适度展开，提供必要的细节",
        SpeakingLength.DETAILED: "请详细阐述，提供充分的分析和例子"
    }
    if meeting.config.speaking_length_preferences and agent.id in meeting.config.speaking_length_preferences:
        preference = meeting.config.speaking_length_preferences[agent.id]
        prompt_parts.append(length_guide[preference])
    
    # Moderator responsibilities
    if is_moderator:
        prompt_parts.append("""
作为会议主持人，你的职责包括：
1. 引导讨论围绕议题进行
2. 确保所有参与者有机会发言
3. 总结关键观点和决策
4. 在讨论偏离主题时及时提醒
5. 推动会议向结论前进
        """)
    
    return "\n\n".join(prompt_parts)


def build_meeting_context(meeting: Meeting, current_agent_id: str) -> str:
    """
    Build meeting context information for an agent
    
    Args:
        meeting: Meeting instance
        current_agent_id: ID of the agent that will receive this context
        
    Returns:
        Complete meeting context string with topic, moderator, participants, agenda, minutes, and mentions
    """
    context_parts = []
    
    # Meeting basic information
    context_parts.append(f"会议主题：{meeting.topic}")
    
    # Moderator information
    if meeting.moderator_id:
        if meeting.moderator_type == 'user':
            moderator_name = "用户"
        else:
            # Find moderator agent name
            moderator_name = next(
                (a.name for a in meeting.participants if a.id == meeting.moderator_id),
                meeting.moderator_id
            )
        context_parts.append(f"会议主持人：{moderator_name}")
    
    # Participants list
    participants_info = []
    for participant in meeting.participants:
        participants_info.append(f"- {participant.name}（{participant.role.name}）")
    context_parts.append("参会者：\n" + "\n".join(participants_info))
    
    # Agenda list
    if meeting.agenda:
        agenda_info = []
        for item in meeting.agenda:
            status = "✓" if item.completed else "○"
            agenda_info.append(f"{status} {item.title}: {item.description}")
        context_parts.append("会议议题：\n" + "\n".join(agenda_info))
    
    # Current conclusion (from minutes)
    if meeting.current_minutes:
        context_parts.append(f"当前会议结论：\n{meeting.current_minutes.summary}")
    
    # @Mention check - check if current agent was mentioned in recent messages
    recent_mentions = [
        m for msg in meeting.messages[-5:] 
        for m in (msg.mentions or []) 
        if m.mentioned_participant_id == current_agent_id
    ]
    if recent_mentions:
        context_parts.append("注意：你在最近的讨论中被提及，请回应相关内容。")
    
    return "\n\n".join(context_parts)


def build_message_history(meeting: Meeting) -> List[ConversationMessage]:
    """
    Build message history for an agent's context
    
    Args:
        meeting: Meeting instance
        
    Returns:
        List of ConversationMessage objects representing the conversation history.
        If meeting has minutes, uses minutes summary + new messages after minutes.
        Otherwise, uses all historical messages.
    """
    messages = []
    
    if meeting.current_minutes:
        # Use meeting minutes to optimize context
        messages.append(ConversationMessage(
            role='system',
            content=f"会议纪要（截至 {meeting.current_minutes.created_at.strftime('%Y-%m-%d %H:%M:%S')}）：\n{meeting.current_minutes.content}"
        ))
        
        # Add new messages after minutes were created
        minutes_time = meeting.current_minutes.created_at
        new_messages = [m for m in meeting.messages if m.timestamp > minutes_time]
        for msg in new_messages:
            messages.append(ConversationMessage(
                role='assistant' if msg.speaker_type == 'agent' else 'user',
                content=f"{msg.speaker_name}: {msg.content}"
            ))
    else:
        # Use full message history
        for msg in meeting.messages:
            messages.append(ConversationMessage(
                role='assistant' if msg.speaker_type == 'agent' else 'user',
                content=f"{msg.speaker_name}: {msg.content}"
            ))
    
    return messages


def parse_mentions(content: str, participants: List[Agent]) -> List[Mention]:
    """
    Parse @mentions from message content
    
    Args:
        content: Message content to parse
        participants: List of meeting participants
        
    Returns:
        List of Mention objects for recognized participants
        
    Examples:
        - @Alice -> matches participant named "Alice"
        - @"Bob Smith" -> matches participant named "Bob Smith"
    """
    mentions = []
    
    # Match @username or @"username with spaces"
    # Pattern: @ followed by either:
    #   1. A quoted string: "..."
    #   2. A word (alphanumeric + underscore): \w+
    pattern = r'@(?:"([^"]+)"|(\w+))'
    matches = re.finditer(pattern, content)
    
    for match in matches:
        # Extract the mentioned name (either from group 1 or group 2)
        mentioned_name = match.group(1) or match.group(2)
        
        # Find matching participant
        for participant in participants:
            if participant.name == mentioned_name:
                mentions.append(Mention(
                    mentioned_participant_id=participant.id,
                    mentioned_participant_name=participant.name,
                    message_id=""  # Will be set when message is created
                ))
                break
    
    return mentions


def get_next_speaker(meeting: Meeting, last_message: Message) -> str:
    """
    Determine the next speaker based on @mentions and meeting configuration
    
    Args:
        meeting: Meeting instance
        last_message: The most recent message in the meeting
        
    Returns:
        Agent ID of the next speaker
        
    Logic:
        1. If last message contains @mentions of AI agents, prioritize the first mentioned agent
        2. Otherwise, follow the configured speaking order (sequential or random)
    """
    # Check if last message has mentions
    if last_message and last_message.mentions:
        # Find the first mentioned participant who is an AI agent
        for mention in last_message.mentions:
            # Check if mentioned participant is an AI agent in this meeting
            for participant in meeting.participants:
                if participant.id == mention.mentioned_participant_id:
                    # Found a mentioned AI agent - they should speak next
                    return participant.id
    
    # No mentions or no AI agents mentioned - use default speaking order
    # This will be handled by the meeting service's existing logic
    return None


def build_mind_map_generation_prompt(meeting: Meeting) -> str:
    """
    Build prompt for generating mind map from meeting content
    
    Args:
        meeting: Meeting instance
        
    Returns:
        Prompt string for AI model to generate mind map structure
    """
    lines = []
    
    lines.append("请根据以下会议内容生成思维导图结构。")
    lines.append("")
    lines.append(f"会议主题：{meeting.topic}")
    lines.append("")
    
    # Add agenda if present
    if meeting.agenda:
        lines.append("会议议题：")
        for item in meeting.agenda:
            status = "✓" if item.completed else "○"
            lines.append(f"{status} {item.title}: {item.description}")
        lines.append("")
    
    # Add meeting minutes if available (for context optimization)
    if meeting.current_minutes:
        lines.append("会议纪要：")
        lines.append(meeting.current_minutes.content)
        lines.append("")
        
        # Add messages after minutes
        minutes_time = meeting.current_minutes.created_at
        new_messages = [m for m in meeting.messages if m.timestamp > minutes_time]
        if new_messages:
            lines.append("纪要后的新讨论：")
            for msg in new_messages:
                lines.append(f"[{msg.speaker_name}]: {msg.content}")
            lines.append("")
    else:
        # Add all messages
        lines.append("会议讨论内容：")
        for msg in meeting.messages:
            lines.append(f"[{msg.speaker_name}] (消息ID: {msg.id}): {msg.content}")
        lines.append("")
    
    lines.append("请生成思维导图的JSON结构，要求：")
    lines.append("1. 根节点（level 0）是会议主题")
    lines.append("2. 一级分支节点（level 1）是会议议题或主要讨论主题")
    lines.append("3. 二级及以下分支节点（level 2+）是关键讨论点、观点、决策等")
    lines.append("4. 每个节点包含相关的消息ID引用（message_references）")
    lines.append("5. 节点之间通过parent_id和children_ids建立层级关系")
    lines.append("")
    lines.append("输出格式（JSON）：")
    lines.append("{")
    lines.append('  "nodes": [')
    lines.append('    {')
    lines.append('      "id": "node_0",')
    lines.append('      "content": "会议主题",')
    lines.append('      "level": 0,')
    lines.append('      "parent_id": null,')
    lines.append('      "children_ids": ["node_1", "node_2"],')
    lines.append('      "message_references": []')
    lines.append('    },')
    lines.append('    {')
    lines.append('      "id": "node_1",')
    lines.append('      "content": "议题1或主题1",')
    lines.append('      "level": 1,')
    lines.append('      "parent_id": "node_0",')
    lines.append('      "children_ids": ["node_1_1", "node_1_2"],')
    lines.append('      "message_references": ["msg_id_1", "msg_id_2"]')
    lines.append('    },')
    lines.append('    ...')
    lines.append('  ]')
    lines.append('}')
    lines.append("")
    lines.append("请只输出JSON，不要包含其他说明文字。")
    
    return "\n".join(lines)
