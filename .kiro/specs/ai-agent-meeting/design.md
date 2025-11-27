# AI 代理会议系统 - 设计文档

## 概述

AI 代理会议系统是一个支持多 AI 模型协作讨论的应用程序。系统采用模块化架构，将会议管理、AI 模型集成、用户交互和数据持久化分离为独立组件。核心设计理念是通过适配器模式统一不同 AI 供应商的接口，通过事件驱动架构管理会议流程，确保系统的可扩展性和可维护性。

## 架构

### 整体架构

系统采用分层架构，包含以下主要层次：

```
┌─────────────────────────────────────┐
│      用户界面层 (UI Layer)           │
│   (CLI / Web Interface)             │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    应用服务层 (Application Layer)    │
│  - MeetingService                   │
│  - AgentService                     │
│  - ConfigurationService             │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│     领域层 (Domain Layer)            │
│  - Meeting                          │
│  - Agent                            │
│  - Message                          │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   基础设施层 (Infrastructure Layer)  │
│  - ModelAdapters (OpenAI, etc.)     │
│  - Storage (File/Database)          │
└─────────────────────────────────────┘
```

### 关键设计决策

1. **适配器模式**: 为不同的 AI 模型供应商创建统一接口，便于扩展新供应商
2. **事件驱动**: 会议流程通过事件驱动，支持异步处理和灵活的流程控制
3. **依赖注入**: 组件间通过接口依赖，提高可测试性和可维护性
4. **不可变消息**: 会议消息一旦创建不可修改，确保历史记录的完整性

## 组件和接口

### 1. 领域模型

#### Agent（代理）
```python
from dataclasses import dataclass
from typing import Optional, Literal
from datetime import datetime

@dataclass
class ModelParameters:
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None

ModelProvider = Literal['openai', 'anthropic', 'google', 'glm']

@dataclass
class ModelConfig:
    provider: ModelProvider
    model_name: str
    api_key: str
    parameters: Optional[ModelParameters] = None

@dataclass
class Role:
    name: str
    description: str
    system_prompt: str

@dataclass
class Agent:
    id: str
    name: str
    role: Role
    model_config: ModelConfig
```

#### Meeting（会议）
```python
from typing import List, Optional, Dict
from enum import Enum

class SpeakingOrder(Enum):
    SEQUENTIAL = 'sequential'
    RANDOM = 'random'

class MeetingStatus(Enum):
    ACTIVE = 'active'
    PAUSED = 'paused'
    ENDED = 'ended'

class DiscussionStyle(Enum):
    FORMAL = 'formal'
    CASUAL = 'casual'
    DEBATE = 'debate'

class SpeakingLength(Enum):
    BRIEF = 'brief'
    MODERATE = 'moderate'
    DETAILED = 'detailed'

@dataclass
class AgendaItem:
    id: str
    title: str
    description: str
    completed: bool = False
    created_at: datetime = None

@dataclass
class MeetingMinutes:
    id: str
    content: str
    summary: str
    key_decisions: List[str]
    action_items: List[str]
    created_at: datetime
    created_by: str  # user or agent_id
    version: int

@dataclass
class Mention:
    mentioned_participant_id: str
    mentioned_participant_name: str
    message_id: str

@dataclass
class MeetingConfig:
    max_rounds: Optional[int] = None
    max_message_length: Optional[int] = None
    speaking_order: SpeakingOrder = SpeakingOrder.SEQUENTIAL
    discussion_style: DiscussionStyle = DiscussionStyle.FORMAL
    speaking_length_preferences: Dict[str, SpeakingLength] = None  # participant_id -> preference

@dataclass
class MindMapNode:
    id: str
    content: str
    level: int  # 0 for root, 1 for first level branches, etc.
    parent_id: Optional[str]
    children_ids: List[str]
    message_references: List[str]  # message IDs related to this node
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class MindMap:
    id: str
    meeting_id: str
    root_node: MindMapNode
    nodes: Dict[str, MindMapNode]  # node_id -> node
    created_at: datetime
    created_by: str  # user or agent_id
    version: int

@dataclass
class Meeting:
    id: str
    topic: str
    participants: List[Agent]
    moderator_id: str  # user or agent_id
    moderator_type: Literal['user', 'agent']
    agenda: List[AgendaItem]
    messages: List['Message']
    minutes_history: List[MeetingMinutes]
    current_minutes: Optional[MeetingMinutes]
    mind_map: Optional[MindMap]
    config: MeetingConfig
    status: MeetingStatus
    created_at: datetime
    updated_at: datetime
```

#### Message（消息）
```python
from typing import Literal, List

SpeakerType = Literal['agent', 'user']

@dataclass
class Message:
    id: str
    speaker_id: str
    speaker_name: str
    speaker_type: SpeakerType
    content: str
    timestamp: datetime
    round_number: int
    mentions: List[Mention] = None  # @提及的参会者列表
```

### 2. 服务接口

#### IModelAdapter（模型适配器接口）
```python
from abc import ABC, abstractmethod
from typing import List, Optional

@dataclass
class ConversationMessage:
    role: Literal['system', 'user', 'assistant']
    content: str

class IModelAdapter(ABC):
    @abstractmethod
    async def send_message(
        self,
        messages: List[ConversationMessage],
        system_prompt: str,
        parameters: Optional[ModelParameters] = None
    ) -> str:
        """发送消息到 AI 模型并获取响应"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """测试与 AI 模型的连接"""
        pass
```

#### IMeetingService（会议服务接口）
```python
class IMeetingService(ABC):
    @abstractmethod
    async def create_meeting(
        self, 
        topic: str, 
        agent_ids: List[str], 
        moderator_id: str,
        moderator_type: Literal['user', 'agent'],
        agenda: List[AgendaItem],
        config: MeetingConfig
    ) -> Meeting:
        """创建新会议"""
        pass
    
    @abstractmethod
    async def start_meeting(self, meeting_id: str) -> None:
        """启动会议"""
        pass
    
    @abstractmethod
    async def pause_meeting(self, meeting_id: str) -> None:
        """暂停会议"""
        pass
    
    @abstractmethod
    async def end_meeting(self, meeting_id: str) -> None:
        """结束会议"""
        pass
    
    @abstractmethod
    async def add_user_message(self, meeting_id: str, content: str) -> None:
        """添加用户消息"""
        pass
    
    @abstractmethod
    async def request_agent_response(self, meeting_id: str, agent_id: str) -> None:
        """请求特定代理响应"""
        pass
    
    @abstractmethod
    async def add_agenda_item(self, meeting_id: str, item: AgendaItem) -> None:
        """添加议题"""
        pass
    
    @abstractmethod
    async def remove_agenda_item(self, meeting_id: str, item_id: str) -> None:
        """删除议题"""
        pass
    
    @abstractmethod
    async def mark_agenda_completed(self, meeting_id: str, item_id: str) -> None:
        """标记议题为已完成"""
        pass
    
    @abstractmethod
    async def generate_minutes(self, meeting_id: str, generator_id: Optional[str] = None) -> MeetingMinutes:
        """生成会议纪要（可选指定生成者）"""
        pass
    
    @abstractmethod
    async def update_minutes(self, meeting_id: str, content: str, editor_id: str) -> MeetingMinutes:
        """更新会议纪要"""
        pass
    
    @abstractmethod
    async def update_meeting_config(self, meeting_id: str, config: MeetingConfig) -> None:
        """更新会议配置"""
        pass
    
    @abstractmethod
    async def get_meeting(self, meeting_id: str) -> Meeting:
        """获取会议详情"""
        pass
    
    @abstractmethod
    async def list_meetings(self) -> List[Meeting]:
        """列出所有会议"""
        pass
    
    @abstractmethod
    async def delete_meeting(self, meeting_id: str) -> None:
        """删除会议"""
        pass
    
    @abstractmethod
    async def generate_mind_map(self, meeting_id: str, generator_id: Optional[str] = None) -> MindMap:
        """生成思维导图（可选指定生成者）"""
        pass
    
    @abstractmethod
    async def update_mind_map(self, meeting_id: str, mind_map: MindMap) -> MindMap:
        """更新思维导图"""
        pass
    
    @abstractmethod
    async def export_mind_map(self, meeting_id: str, format: Literal['png', 'svg', 'json', 'markdown']) -> bytes:
        """导出思维导图为指定格式"""
        pass
```

#### IAgentService（代理服务接口）
```python
class IAgentService(ABC):
    @abstractmethod
    async def create_agent(self, agent_data: dict) -> Agent:
        """创建新代理"""
        pass
    
    @abstractmethod
    async def update_agent(self, agent_id: str, updates: dict) -> Agent:
        """更新代理"""
        pass
    
    @abstractmethod
    async def delete_agent(self, agent_id: str) -> None:
        """删除代理"""
        pass
    
    @abstractmethod
    async def get_agent(self, agent_id: str) -> Agent:
        """获取代理详情"""
        pass
    
    @abstractmethod
    async def list_agents(self) -> List[Agent]:
        """列出所有代理"""
        pass
    
    @abstractmethod
    async def test_agent_connection(self, agent_id: str) -> bool:
        """测试代理连接"""
        pass
```

#### IStorageService（存储服务接口）
```python
class IStorageService(ABC):
    @abstractmethod
    async def save_agent(self, agent: Agent) -> None:
        """保存代理"""
        pass
    
    @abstractmethod
    async def load_agent(self, agent_id: str) -> Optional[Agent]:
        """加载代理"""
        pass
    
    @abstractmethod
    async def load_all_agents(self) -> List[Agent]:
        """加载所有代理"""
        pass
    
    @abstractmethod
    async def delete_agent(self, agent_id: str) -> None:
        """删除代理"""
        pass
    
    @abstractmethod
    async def save_meeting(self, meeting: Meeting) -> None:
        """保存会议"""
        pass
    
    @abstractmethod
    async def load_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """加载会议"""
        pass
    
    @abstractmethod
    async def load_all_meetings(self) -> List[Meeting]:
        """加载所有会议"""
        pass
    
    @abstractmethod
    async def delete_meeting(self, meeting_id: str) -> None:
        """删除会议"""
        pass
```

### 3. 模型适配器实现

每个模型供应商需要实现 `IModelAdapter` 接口：

- **OpenAIAdapter**: 使用 OpenAI API（GPT-3.5, GPT-4 等）
- **AnthropicAdapter**: 使用 Anthropic API（Claude 系列）
- **GoogleAdapter**: 使用 Google AI API（Gemini 系列）
- **GLMAdapter**: 使用智谱 AI API（GLM 系列）

适配器工厂模式：
```python
class ModelAdapterFactory:
    @staticmethod
    def create(config: ModelConfig) -> IModelAdapter:
        """根据配置创建对应的模型适配器"""
        if config.provider == 'openai':
            return OpenAIAdapter(config)
        elif config.provider == 'anthropic':
            return AnthropicAdapter(config)
        elif config.provider == 'google':
            return GoogleAdapter(config)
        elif config.provider == 'glm':
            return GLMAdapter(config)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
```

### 4. 上下文构建策略

#### 4.1 基础上下文结构

当代理准备发言时，系统需要构建完整的上下文信息。上下文包含以下部分：

1. **系统提示词（System Prompt）**：
   - 代理的角色描述
   - 讨论风格指导
   - 发言长度偏好
   - 主持人职责（如果是主持人）

2. **会议元信息**：
   - 会议主题
   - 会议主持人身份
   - 所有参会者列表（姓名和角色）
   - 当前议题列表
   - 当前会议结论（如果有）

3. **历史消息**：
   - 如果存在会议纪要：纪要内容 + 纪要生成后的新消息
   - 如果不存在纪要：所有历史消息
   - @提及标注（如果被提及）

#### 4.2 系统提示词构建

```python
def build_system_prompt(agent: Agent, meeting: Meeting, is_moderator: bool) -> str:
    """构建代理的系统提示词"""
    prompt_parts = []
    
    # 基础角色
    prompt_parts.append(f"你的角色：{agent.role.name}")
    prompt_parts.append(f"角色描述：{agent.role.description}")
    prompt_parts.append(agent.role.system_prompt)
    
    # 讨论风格
    style_guide = {
        DiscussionStyle.FORMAL: "请保持正式、专业的讨论风格",
        DiscussionStyle.CASUAL: "请使用轻松、友好的讨论风格",
        DiscussionStyle.DEBATE: "请采用辩论式风格，清晰表达观点并提供论据"
    }
    prompt_parts.append(style_guide[meeting.config.discussion_style])
    
    # 发言长度偏好
    length_guide = {
        SpeakingLength.BRIEF: "请保持发言简短，直接表达要点",
        SpeakingLength.MODERATE: "请适度展开，提供必要的细节",
        SpeakingLength.DETAILED: "请详细阐述，提供充分的分析和例子"
    }
    if agent.id in meeting.config.speaking_length_preferences:
        preference = meeting.config.speaking_length_preferences[agent.id]
        prompt_parts.append(length_guide[preference])
    
    # 主持人职责
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
```

#### 4.3 会议上下文构建

```python
def build_meeting_context(meeting: Meeting, current_agent_id: str) -> str:
    """构建会议元信息上下文"""
    context_parts = []
    
    # 会议基本信息
    context_parts.append(f"会议主题：{meeting.topic}")
    
    # 主持人信息
    moderator_name = "用户" if meeting.moderator_type == 'user' else \
                     next(a.name for a in meeting.participants if a.id == meeting.moderator_id)
    context_parts.append(f"会议主持人：{moderator_name}")
    
    # 参会者列表
    participants_info = []
    for participant in meeting.participants:
        participants_info.append(f"- {participant.name}（{participant.role.name}）")
    context_parts.append("参会者：\n" + "\n".join(participants_info))
    
    # 议题列表
    if meeting.agenda:
        agenda_info = []
        for item in meeting.agenda:
            status = "✓" if item.completed else "○"
            agenda_info.append(f"{status} {item.title}: {item.description}")
        context_parts.append("会议议题：\n" + "\n".join(agenda_info))
    
    # 当前结论
    if meeting.current_minutes:
        context_parts.append(f"当前会议结论：\n{meeting.current_minutes.summary}")
    
    # @提及检查
    recent_mentions = [m for msg in meeting.messages[-5:] 
                      for m in (msg.mentions or []) 
                      if m.mentioned_participant_id == current_agent_id]
    if recent_mentions:
        context_parts.append("注意：你在最近的讨论中被提及，请回应相关内容。")
    
    return "\n\n".join(context_parts)
```

#### 4.4 历史消息构建

```python
def build_message_history(meeting: Meeting) -> List[ConversationMessage]:
    """构建历史消息列表"""
    messages = []
    
    if meeting.current_minutes:
        # 使用会议纪要替代之前的历史
        messages.append(ConversationMessage(
            role='system',
            content=f"会议纪要（截至 {meeting.current_minutes.created_at}）：\n{meeting.current_minutes.content}"
        ))
        
        # 添加纪要生成后的新消息
        minutes_time = meeting.current_minutes.created_at
        new_messages = [m for m in meeting.messages if m.timestamp > minutes_time]
        for msg in new_messages:
            messages.append(ConversationMessage(
                role='assistant' if msg.speaker_type == 'agent' else 'user',
                content=f"{msg.speaker_name}: {msg.content}"
            ))
    else:
        # 使用全量历史消息
        for msg in meeting.messages:
            messages.append(ConversationMessage(
                role='assistant' if msg.speaker_type == 'agent' else 'user',
                content=f"{msg.speaker_name}: {msg.content}"
            ))
    
    return messages
```

### 5. @提及处理

#### 5.1 提及解析

```python
import re

def parse_mentions(content: str, participants: List[Agent]) -> List[Mention]:
    """从消息内容中解析@提及"""
    mentions = []
    # 匹配 @用户名 或 @"用户名"
    pattern = r'@(?:"([^"]+)"|(\S+))'
    matches = re.finditer(pattern, content)
    
    for match in matches:
        mentioned_name = match.group(1) or match.group(2)
        # 查找匹配的参与者
        for participant in participants:
            if participant.name == mentioned_name:
                mentions.append(Mention(
                    mentioned_participant_id=participant.id,
                    mentioned_participant_name=participant.name,
                    message_id=""  # 将在保存消息时设置
                ))
                break
    
    return mentions
```

#### 5.2 发言顺序调整

当消息中包含@提及时，系统应优先安排被提及的代理发言：

```python
def get_next_speaker(meeting: Meeting, last_message: Message) -> Optional[str]:
    """确定下一个发言者"""
    # 如果最后一条消息包含@提及，优先安排被提及者
    if last_message.mentions:
        for mention in last_message.mentions:
            # 检查被提及者是否是AI代理
            if any(a.id == mention.mentioned_participant_id for a in meeting.participants):
                return mention.mentioned_participant_id
    
    # 否则按照配置的发言顺序
    if meeting.config.speaking_order == SpeakingOrder.SEQUENTIAL:
        return get_next_sequential_speaker(meeting)
    else:
        return get_random_speaker(meeting)
```

## 数据模型

### 存储结构

系统使用文件系统进行数据持久化，采用 JSON 格式：

```
data/
├── agents/
│   ├── agent-1.json
│   ├── agent-2.json
│   └── ...
└── meetings/
    ├── meeting-1.json
    ├── meeting-2.json
    └── ...
```

### 数据验证

所有输入数据需要经过验证：
- Agent 名称：非空，长度 1-50 字符
- Role 描述：非空，长度 1-2000 字符
- API Key：非空
- Meeting 主题：非空，长度 1-200 字符
- Message 内容：非空，长度 1-10000 字符

## 正确性属性

*属性是指在系统所有有效执行中都应该成立的特征或行为——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 主持人管理属性

**属性 31: 主持人配置完整性**
*对于任何*会议创建请求，如果指定了主持人（用户或AI代理），创建的会议对象应包含正确的主持人ID和类型
**验证需求: 9.1**

**属性 32: 主持人系统提示词增强**
*对于任何*作为主持人的AI代理，其系统提示词应包含主持人职责说明
**验证需求: 9.3**

**属性 33: 会议信息包含主持人**
*对于任何*会议，会议对象应包含主持人身份信息（ID和类型）
**验证需求: 9.4**

### 议题管理属性

**属性 34: 初始议题列表接受**
*对于任何*会议创建请求，如果包含初始议题列表，创建的会议对象应包含所有议题
**验证需求: 10.1**

**属性 35: 议题动态添加**
*对于任何*活动会议和新议题，添加议题后会议的议题列表长度应增加1
**验证需求: 10.2**

**属性 36: 议题状态管理**
*对于任何*会议中的议题，标记为已完成后该议题的completed字段应为True；删除后该议题不应出现在议题列表中
**验证需求: 10.3**

**属性 37: 议题上下文注入**
*对于任何*代理发言，构建的上下文应包含当前会议的议题列表
**验证需求: 10.5, 12.1**

### 会议配置属性

**属性 38: 讨论风格配置**
*对于任何*会议创建或配置请求，如果指定了讨论风格，会议配置应包含该风格设置
**验证需求: 11.1**

**属性 39: 发言长度偏好配置**
*对于任何*会议配置，如果为参与者指定了发言长度偏好，配置应正确存储每个参与者的偏好
**验证需求: 11.2**

**属性 40: 配置注入系统提示词**
*对于任何*代理发言，系统提示词应包含会议的讨论风格和该代理的发言长度偏好（如果配置了）
**验证需求: 11.3**

**属性 41: 配置更新应用**
*对于任何*会议配置更新，更新后代理发言时应使用新的配置构建系统提示词
**验证需求: 11.4**

### 上下文注入属性

**属性 42: 会议结论上下文注入**
*对于任何*存在会议纪要的会议，代理发言时的上下文应包含当前会议结论
**验证需求: 12.2**

**属性 43: 角色描述上下文注入**
*对于任何*代理发言，系统提示词应包含该代理的角色描述
**验证需求: 12.3**

**属性 44: 主持人职责上下文注入**
*对于任何*作为主持人的AI代理发言，系统提示词应额外包含主持人的特殊任务和职责
**验证需求: 12.4**

**属性 45: 参会者列表上下文注入**
*对于任何*代理发言，上下文应包含所有参会者的姓名和角色信息
**验证需求: 12.5**

**属性 46: 主持人身份上下文注入**
*对于任何*代理发言，上下文应包含会议主持人的身份信息
**验证需求: 12.6**

### 会议纪要属性

**属性 47: 纪要生成功能**
*对于任何*会议，触发纪要生成后应创建一个非空的会议纪要对象
**验证需求: 13.1, 14.1**

**属性 48: 纪要持久化**
*对于任何*生成的会议纪要，该纪要应被保存到会议的纪要历史中
**验证需求: 13.3**

**属性 49: 纪要优化上下文**
*对于任何*存在会议纪要的会议，代理发言时的历史消息上下文应使用纪要内容而非纪要生成前的全量消息
**验证需求: 13.4**

**属性 50: 纪要后新消息包含**
*对于任何*存在会议纪要的会议，代理发言时的上下文应包含纪要生成后的所有新消息
**验证需求: 13.5**

**属性 51: 纪要手动编辑**
*对于任何*会议纪要，手动编辑后纪要内容应反映更新
**验证需求: 14.2**

**属性 52: 纪要AI更新**
*对于任何*会议，指定AI代理更新纪要后应生成新版本的纪要
**验证需求: 14.3**

**属性 53: 纪要版本历史**
*对于任何*会议纪要，每次更新后版本历史列表长度应增加1
**验证需求: 14.4**

**属性 54: 当前纪要显示**
*对于任何*存在纪要的会议，会议对象应包含当前有效的纪要
**验证需求: 14.5**

### @提及功能属性

**属性 55: 提及解析**
*对于任何*包含@符号和参会者名称的消息，系统应正确识别被提及的参会者
**验证需求: 15.1**

**属性 56: 提及上下文标注**
*对于任何*包含@提及的消息，被提及者下次发言时的上下文应包含提及标注
**验证需求: 15.2**

**属性 57: 提及优先发言**
*对于任何*消息中@提及的AI代理，该代理应成为下一个发言者（优先于正常发言顺序）
**验证需求: 15.3**

### 代理管理属性

**属性 1: 代理创建完整性**
*对于任何*有效的代理配置（包含供应商、模型名称、API 密钥和角色描述），创建代理后返回的代理对象应包含所有指定字段
**验证需求: 1.1**

**属性 2: 代理持久化往返**
*对于任何*有效的代理配置，保存后重新加载应返回等价的代理对象
**验证需求: 1.2**

**属性 3: 代理列表完整性**
*对于任何*代理集合，列表操作应返回所有已保存的代理，且每个代理包含名称、角色和模型信息
**验证需求: 1.3**

**属性 4: 代理更新一致性**
*对于任何*现有代理和有效的更新数据，更新操作后重新加载应反映所有更改
**验证需求: 1.4**

**属性 5: 代理删除完整性**
*对于任何*已存在的代理，删除后该代理不应出现在列表中且无法被加载
**验证需求: 1.5**

### 模型供应商属性

**属性 6: API 凭证往返**
*对于任何*模型供应商和凭证信息，保存后重新加载应返回相同的凭证
**验证需求: 2.2**

**属性 7: API 错误处理**
*对于任何*模拟的 API 失败场景，系统应返回清晰的错误消息而不是崩溃
**验证需求: 2.4**

**属性 8: 连接测试响应**
*对于任何*代理配置，测试连接操作应返回布尔值（成功或失败）
**验证需求: 2.5**

### 角色配置属性

**属性 9: 角色字段完整性**
*对于任何*包含角色名称、背景描述和行为指导的角色配置，系统应接受并存储所有字段
**验证需求: 3.1**

**属性 10: 角色提示词传递**
*对于任何*代理发言，发送给 AI 模型的消息应包含该代理的角色描述作为系统提示词
**验证需求: 3.2**

**属性 11: 角色描述验证**
*对于任何*角色描述，空描述或超出长度限制（1-2000 字符）的描述应被拒绝
**验证需求: 3.3**

### 会议流程属性

**属性 12: 会议创建要求**
*对于任何*会议创建请求，必须包含非空主题和至少一个代理才能成功创建
**验证需求: 4.1**

**属性 13: 发言顺序一致性**
*对于任何*配置为顺序发言的会议，代理发言顺序应与参与者列表顺序一致
**验证需求: 4.2, 7.5**

**属性 14: 会议上下文传递**
*对于任何*代理发言，发送给 AI 模型的上下文应包含该时刻之前的所有会议消息
**验证需求: 4.3**

**属性 15: 消息记录增长**
*对于任何*代理或用户发言，会议的消息列表长度应增加 1
**验证需求: 4.4, 5.1**

**属性 16: 轮次递增**
*对于任何*会议，当所有参与代理完成一轮发言后，轮次计数器应增加 1
**验证需求: 4.5**

**属性 17: 暂停状态保持**
*对于任何*活动会议，暂停后会议状态应变为 'paused' 且消息列表不再增长
**验证需求: 4.6**

**属性 18: 结束状态持久化**
*对于任何*会议，结束后会议状态应变为 'ended' 且会议应被持久化存储
**验证需求: 4.7**

### 用户参与属性

**属性 19: 用户消息上下文传递**
*对于任何*用户在会议中发送的消息，该消息应出现在后续代理发言的上下文中
**验证需求: 5.2**

**属性 20: 指定代理响应**
*对于任何*用户指定的代理，该代理应成为下一个发言者
**验证需求: 5.3**

**属性 21: 空消息拒绝**
*对于任何*空消息或纯空白字符消息，系统应拒绝提交且会议状态保持不变
**验证需求: 5.4**

### 会议历史属性

**属性 22: 消息元数据完整性**
*对于任何*会议消息，应包含发言者身份、内容和时间戳
**验证需求: 6.1**

**属性 23: 会议列表完整性**
*对于任何*已保存的会议集合，列表操作应返回所有会议及其基本信息
**验证需求: 6.2**

**属性 24: 会议加载往返**
*对于任何*已保存的会议，重新加载后应包含所有原始消息和元数据
**验证需求: 6.3**

**属性 25: 会议导出格式**
*对于任何*会议，导出操作应返回有效的 Markdown 或 JSON 格式字符串
**验证需求: 6.4**

**属性 26: 会议删除完整性**
*对于任何*已存在的会议，删除后该会议不应出现在列表中且无法被加载
**验证需求: 6.5**

### 会议控制属性

**属性 27: 会议配置接受**
*对于任何*会议创建请求，应能够设置轮次限制、消息长度限制和发言顺序模式
**验证需求: 7.1**

**属性 28: 轮次限制自动结束**
*对于任何*设置了轮次限制的会议，达到限制后会议应自动变为 'ended' 状态
**验证需求: 7.2**

**属性 29: 消息长度截断**
*对于任何*超过长度限制的代理响应，存储的消息应被截断且包含截断标注
**验证需求: 7.3**

**属性 30: 随机顺序变化**
*对于任何*配置为随机发言的会议，在多轮中至少有一轮的发言顺序与初始顺序不同（当代理数量 >= 3 时）
**验证需求: 7.4**

## 错误处理

### 错误类型

系统定义以下错误类型：

```python
class ValidationError(Exception):
    """输入验证错误"""
    def __init__(self, message: str, field: str):
        super().__init__(message)
        self.field = field

class NotFoundError(Exception):
    """资源未找到错误"""
    def __init__(self, message: str, resource_type: str, resource_id: str):
        super().__init__(message)
        self.resource_type = resource_type
        self.resource_id = resource_id

class APIError(Exception):
    """API 调用错误"""
    def __init__(self, message: str, provider: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code

class MeetingStateError(Exception):
    """会议状态错误"""
    def __init__(self, message: str, current_state: MeetingStatus):
        super().__init__(message)
        self.current_state = current_state

class PermissionError(Exception):
    """权限错误"""
    def __init__(self, message: str, required_role: str):
        super().__init__(message)
        self.required_role = required_role

class AgendaError(Exception):
    """议题操作错误"""
    def __init__(self, message: str, agenda_id: str):
        super().__init__(message)
        self.agenda_id = agenda_id
```

### 错误处理策略

1. **输入验证错误**: 在数据进入系统前进行验证，抛出 `ValidationError`
2. **资源未找到**: 查询不存在的资源时抛出 `NotFoundError`
3. **API 调用失败**: 
   - 网络错误：重试最多 3 次，指数退避
   - 认证错误：立即失败，提示用户检查 API 密钥
   - 速率限制：等待并重试
   - 其他错误：记录详细信息并抛出 `APIError`
4. **状态错误**: 在不合法的会议状态下执行操作时抛出 `MeetingStateError`
5. **存储错误**: 文件系统操作失败时记录错误并向上传播

### 错误日志

所有错误应记录到日志系统，包含：
- 时间戳
- 错误类型
- 错误消息
- 堆栈跟踪
- 相关上下文（用户 ID、会议 ID 等）

## 测试策略

### 单元测试

单元测试覆盖以下场景：

1. **数据验证**:
   - 有效输入被接受
   - 无效输入被拒绝（空值、超长、格式错误）
   - 边界值测试

2. **业务逻辑**:
   - 会议状态转换
   - 发言顺序管理
   - 轮次计数

3. **错误处理**:
   - 各种错误类型被正确抛出
   - 错误消息清晰准确

4. **集成点**:
   - 服务间接口调用
   - 存储操作

### 基于属性的测试

系统使用 **Hypothesis** 库进行基于属性的测试。

**配置要求**:
- 每个属性测试至少运行 100 次迭代
- 每个测试必须用注释标注对应的设计文档属性
- 标注格式: `# Feature: ai-agent-meeting, Property X: [属性描述]`

**测试覆盖**:

基于属性的测试验证以下正确性属性：

1. **往返属性** (Properties 2, 6, 24):
   - 代理保存和加载
   - API 凭证存储和检索
   - 会议持久化和恢复

2. **不变量属性** (Properties 1, 3, 9, 22, 31, 33, 34, 45, 46):
   - 数据结构完整性
   - 必需字段存在性
   - 元数据一致性
   - 主持人信息完整性
   - 参会者信息完整性

3. **状态转换属性** (Properties 16, 17, 18, 28, 36):
   - 会议状态机正确性
   - 轮次管理
   - 自动结束条件
   - 议题状态管理

4. **集合操作属性** (Properties 3, 5, 23, 26, 35, 53):
   - 列表完整性
   - 删除操作正确性
   - 查询一致性
   - 议题列表增长
   - 纪要版本历史增长

5. **顺序属性** (Properties 13, 30, 57):
   - 顺序发言模式
   - 随机发言模式
   - @提及优先发言

6. **验证属性** (Properties 11, 21, 29):
   - 输入验证规则
   - 长度限制
   - 空值拒绝

7. **上下文构建属性** (Properties 37, 40, 42, 43, 44, 49, 50, 56):
   - 议题上下文注入
   - 配置注入系统提示词
   - 会议结论注入
   - 角色描述注入
   - 主持人职责注入
   - 纪要优化上下文
   - 纪要后新消息包含
   - 提及上下文标注

8. **配置管理属性** (Properties 38, 39, 41):
   - 讨论风格配置
   - 发言长度偏好配置
   - 配置更新应用

9. **纪要管理属性** (Properties 47, 48, 51, 52, 54):
   - 纪要生成功能
   - 纪要持久化
   - 纪要手动编辑
   - 纪要AI更新
   - 当前纪要显示

10. **提及处理属性** (Properties 55):
    - 提及解析正确性

11. **思维导图生成属性** (Properties 69, 70, 71, 72, 73):
    - 思维导图生成功能
    - 结构正确性（根节点为主题，议题为分支）
    - 持久化往返
    - 更新功能
    - 访问入口存在性

12. **思维导图交互属性** (Properties 74, 75, 76, 77, 78, 79):
    - 渲染完整性
    - 节点展开折叠
    - 详细信息显示
    - 消息引用跳转
    - 视图变换状态
    - 搜索功能

13. **思维导图导出属性** (Properties 80, 81, 82, 83, 84):
    - 多格式支持
    - 图片导出有效性
    - JSON 往返一致性
    - Markdown 层级结构
    - 导出结果可用性

**生成器策略**:

为属性测试创建智能生成器：

```python
from hypothesis import strategies as st

# 示例：代理配置生成器
role_strategy = st.builds(
    Role,
    name=st.text(min_size=1, max_size=50),
    description=st.text(min_size=1, max_size=2000),
    system_prompt=st.text(min_size=1, max_size=2000)
)

model_config_strategy = st.builds(
    ModelConfig,
    provider=st.sampled_from(['openai', 'anthropic', 'google', 'glm']),
    model_name=st.text(min_size=1, max_size=50),
    api_key=st.text(min_size=1, max_size=100),
    parameters=st.none() | st.builds(ModelParameters)
)

agent_strategy = st.builds(
    Agent,
    id=st.uuids().map(str),
    name=st.text(min_size=1, max_size=50),
    role=role_strategy,
    model_config=model_config_strategy
)
```

### 测试执行顺序

1. 实现功能代码
2. 编写单元测试验证具体场景
3. 编写属性测试验证通用规则
4. 运行所有测试确保通过
5. 修复发现的问题

### 测试工具

- **测试框架**: pytest
- **属性测试库**: Hypothesis
- **异步测试**: pytest-asyncio
- **模拟库**: unittest.mock（根据需要使用，但优先测试真实功能）
- **覆盖率工具**: pytest-cov

### 持续验证

- 所有测试在每次代码提交前运行
- 属性测试帮助发现边缘情况和意外行为
- 测试失败时，分析失败的输入以改进实现或规范



## 前端用户体验优化设计

### 1. 首页优化 - 进行中会议展示

#### 设计目标
提升首页吸引力，让用户快速了解当前活动并继续参与进行中的会议。

#### 实现方案

**数据获取**：
- 在首页加载时，获取所有会议列表
- 过滤出状态为 `active` 的会议
- 按 `updated_at` 降序排序
- 取前 5 个会议

**展示内容**：
```jsx
<Card title="进行中的会议" style={{ marginBottom: 24 }}>
  {activeMeetings.length === 0 ? (
    <Empty description="暂无进行中的会议" />
  ) : (
    <List
      dataSource={activeMeetings}
      renderItem={(meeting) => (
        <List.Item
          onClick={() => navigate(`/meetings/${meeting.id}`)}
          style={{ cursor: 'pointer' }}
        >
          <List.Item.Meta
            title={meeting.topic}
            description={
              <Space>
                <Tag>{meeting.participants.length} 个代理</Tag>
                <Tag>{meeting.messages.length} 条消息</Tag>
                <span>最后更新: {formatTime(meeting.updated_at)}</span>
              </Space>
            }
          />
        </List.Item>
      )}
    />
  )}
</Card>
```

### 2. 代理列表页面优化 - 详细信息展示

#### 设计目标
让用户更好地了解每个代理的特点和配置，提供更丰富的信息展示。

#### 实现方案

**卡片布局增强**：
```jsx
<Card>
  <Card.Meta
    title={
      <Space>
        <span style={{ fontSize: '18px', fontWeight: 'bold' }}>
          {agent.name}
        </span>
        <Tag color="blue">{agent.role.name}</Tag>
      </Space>
    }
    description={
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* 角色描述 - 可展开/收起 */}
        <div>
          <Text strong>角色描述：</Text>
          <Paragraph
            ellipsis={{
              rows: 2,
              expandable: true,
              symbol: '展开'
            }}
          >
            {agent.role.description}
          </Paragraph>
        </div>
        
        {/* 模型信息 */}
        <div>
          <Text strong>模型：</Text>
          <Space>
            <Tag color="green">{agent.model_config.provider}</Tag>
            <Tag>{agent.model_config.model_name}</Tag>
          </Space>
        </div>
      </Space>
    }
  />
</Card>
```

**空状态优化**：
```jsx
{agents.length === 0 && (
  <Empty
    description="还没有创建任何代理"
    image={Empty.PRESENTED_IMAGE_SIMPLE}
  >
    <Button type="primary" onClick={() => navigate('/agents/create')}>
      创建第一个代理
    </Button>
  </Empty>
)}
```

### 3. 会议信息面板折叠设计

#### 设计目标
节省屏幕空间，让用户专注于会议消息内容，同时保持重要信息的可访问性。

#### 实现方案

**状态管理**：
```jsx
const [meetingInfoCollapsed, setMeetingInfoCollapsed] = useState(
  localStorage.getItem('meetingInfoCollapsed') === 'true'
)

useEffect(() => {
  localStorage.setItem('meetingInfoCollapsed', meetingInfoCollapsed)
}, [meetingInfoCollapsed])
```

**折叠面板结构**：
```jsx
<Card 
  style={{ marginBottom: 16 }}
  title={
    <div 
      onClick={() => setMeetingInfoCollapsed(!meetingInfoCollapsed)}
      style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between' }}
    >
      <Space>
        <span>会议信息</span>
        {meetingInfoCollapsed && (
          <Space size="small">
            <Tag>{meeting.participants.length} 个参与者</Tag>
            <Tag>{getStatusBadge(meeting.status)}</Tag>
          </Space>
        )}
      </Space>
      {meetingInfoCollapsed ? <DownOutlined /> : <UpOutlined />}
    </div>
  }
>
  {!meetingInfoCollapsed && (
    <Space direction="vertical" style={{ width: '100%' }}>
      {/* 完整的会议信息内容 */}
    </Space>
  )}
</Card>
```

### 4. 会议纪要图标化设计

#### 设计目标
将会议纪要以图标形式固定在界面，点击后以抽屉或弹窗形式展示，节省主要空间。

#### 实现方案

**浮动按钮**：
```jsx
{/* 固定在右上角的纪要图标 */}
<FloatButton
  icon={meeting.current_minutes ? <FileTextOutlined /> : <PlusOutlined />}
  tooltip={meeting.current_minutes ? '查看会议纪要' : '生成会议纪要'}
  onClick={() => setMinutesDrawerVisible(true)}
  style={{ right: 24, top: 100 }}
  badge={meeting.current_minutes ? { dot: true, color: 'green' } : null}
/>
```

**抽屉展示**：
```jsx
<Drawer
  title="会议纪要"
  placement="right"
  width={600}
  open={minutesDrawerVisible}
  onClose={() => setMinutesDrawerVisible(false)}
  extra={
    <Space>
      <Button icon={<EditOutlined />} onClick={handleEditMinutes}>
        编辑
      </Button>
      <Button icon={<HistoryOutlined />} onClick={handleViewHistory}>
        历史
      </Button>
      {meeting.status !== 'ended' && (
        <Button type="primary" onClick={handleRegenerateMinutes}>
          重新生成
        </Button>
      )}
    </Space>
  }
>
  {meeting.current_minutes ? (
    <div>
      <div style={{ marginBottom: 16, color: '#666', fontSize: '12px' }}>
        版本 {meeting.current_minutes.version} · 
        {new Date(meeting.current_minutes.created_at).toLocaleString('zh-CN')}
      </div>
      <MarkdownMessage content={meeting.current_minutes.content} />
    </div>
  ) : (
    <Empty description="暂无会议纪要">
      <Button type="primary" onClick={handleGenerateMinutes}>
        生成会议纪要
      </Button>
    </Empty>
  )}
</Drawer>
```

### 5. 议题侧边栏设计

#### 设计目标
将议题列表以侧边栏形式展示，可收起为图标，方便用户随时查看议题而不影响消息阅读。

#### 实现方案

**状态管理**：
```jsx
const [agendaSidebarCollapsed, setAgendaSidebarCollapsed] = useState(
  localStorage.getItem('agendaSidebarCollapsed') === 'true'
)

useEffect(() => {
  localStorage.setItem('agendaSidebarCollapsed', agendaSidebarCollapsed)
}, [agendaSidebarCollapsed])
```

**侧边栏布局**：
```jsx
<div style={{ display: 'flex', gap: 16 }}>
  {/* 议题侧边栏 */}
  {meeting.agenda && meeting.agenda.length > 0 && (
    <div
      style={{
        width: agendaSidebarCollapsed ? '60px' : '300px',
        transition: 'width 0.3s',
        borderRight: '1px solid #f0f0f0',
        padding: '16px',
        position: 'sticky',
        top: 0,
        height: '100vh',
        overflowY: 'auto'
      }}
    >
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 16
      }}>
        {!agendaSidebarCollapsed && <span style={{ fontWeight: 'bold' }}>议题列表</span>}
        <Button
          type="text"
          icon={agendaSidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={() => setAgendaSidebarCollapsed(!agendaSidebarCollapsed)}
        />
      </div>
      
      {agendaSidebarCollapsed ? (
        <Badge count={meeting.agenda.filter(a => !a.completed).length}>
          <FileTextOutlined style={{ fontSize: 24 }} />
        </Badge>
      ) : (
        <List
          dataSource={meeting.agenda}
          renderItem={(item) => (
            <List.Item
              style={{
                padding: '8px 0',
                borderBottom: '1px solid #f0f0f0'
              }}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space>
                  <Checkbox checked={item.completed} disabled />
                  <Text
                    style={{
                      textDecoration: item.completed ? 'line-through' : 'none',
                      fontWeight: item.completed ? 'normal' : 'bold'
                    }}
                  >
                    {item.title}
                  </Text>
                </Space>
                {item.description && (
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {item.description}
                  </Text>
                )}
              </Space>
            </List.Item>
          )}
        />
      )}
    </div>
  )}
  
  {/* 主要内容区域 */}
  <div style={{ flex: 1 }}>
    {/* 会议消息等内容 */}
  </div>
</div>
```

### 6. 消息输入框固定底部设计

#### 设计目标
将消息输入区域固定在底部，限制高度占比，为消息历史留出更多空间。

#### 实现方案

**整体布局结构**：
```jsx
<div style={{ 
  display: 'flex', 
  flexDirection: 'column', 
  height: 'calc(100vh - 64px)' // 减去顶部导航栏高度
}}>
  {/* 顶部：会议标题和控制按钮 */}
  <div style={{ flexShrink: 0 }}>
    <Card>
      {/* 会议标题、状态、控制按钮 */}
    </Card>
  </div>
  
  {/* 中间：可折叠的会议信息 */}
  {!meetingInfoCollapsed && (
    <div style={{ flexShrink: 0 }}>
      <Card>
        {/* 会议信息内容 */}
      </Card>
    </div>
  )}
  
  {/* 主要内容：消息列表（可滚动） */}
  <div style={{ 
    flex: 1, 
    overflowY: 'auto',
    marginBottom: 16
  }}>
    <Card title="会议消息">
      {/* 消息列表 */}
    </Card>
  </div>
  
  {/* 底部：固定的输入区域 */}
  {meeting.status !== 'ended' && (
    <div style={{ 
      flexShrink: 0,
      maxHeight: '20vh', // 限制最大高度为视口的20%
      borderTop: '1px solid #f0f0f0',
      backgroundColor: 'white',
      padding: '16px',
      position: 'sticky',
      bottom: 0,
      zIndex: 10
    }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* 快速@标签 */}
        <div style={{ marginBottom: 8 }}>
          <span style={{ color: '#666', fontSize: '12px' }}>快速 @: </span>
          {meeting.participants.map(p => (
            <Tag 
              key={p.id}
              style={{ cursor: 'pointer' }}
              onClick={() => setUserMessage(prev => prev + `@${p.name} `)}
            >
              @{p.name}
            </Tag>
          ))}
        </div>
        
        {/* 输入框 */}
        <TextArea
          rows={3}
          value={userMessage}
          onChange={handleMessageChange}
          placeholder="输入你的消息... (输入 @ 可以提及代理)"
          disabled={meeting.status !== 'active'}
          style={{ 
            resize: 'none', // 禁止手动调整大小
            maxHeight: '15vh', // 限制输入框最大高度
            overflowY: 'auto' // 内容超出时内部滚动
          }}
        />
        
        {/* 发送按钮 */}
        <Space wrap>
          <Button type="primary" icon={<SendOutlined />} onClick={handleSend}>
            发送
          </Button>
          {/* 其他操作按钮 */}
        </Space>
      </Space>
    </div>
  )}
</div>
```

**关键CSS样式**：
```css
/* 确保输入区域固定在底部 */
.message-input-area {
  position: sticky;
  bottom: 0;
  background: white;
  z-index: 10;
  max-height: 20vh;
  border-top: 1px solid #f0f0f0;
  padding: 16px;
}

/* 输入框内部滚动 */
.message-textarea {
  resize: none;
  max-height: 15vh;
  overflow-y: auto;
}

/* 消息列表区域 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
```

## 前端优化正确性属性

### 首页优化属性

**属性 58: 进行中会议列表展示**
*对于任何*首页访问，如果存在进行中的会议，系统应显示最多5个按最后更新时间排序的会议
**验证需求: 16.1, 16.2, 16.5**

**属性 59: 进行中会议点击跳转**
*对于任何*首页显示的进行中会议，点击后应正确跳转到对应的会议室页面
**验证需求: 16.3**

### 代理列表优化属性

**属性 60: 代理详细信息展示**
*对于任何*代理列表项，应包含代理名称、角色名称、角色描述、模型供应商和模型名称
**验证需求: 17.1, 17.2, 17.4**

**属性 61: 角色描述展开功能**
*对于任何*超过指定长度的角色描述，应提供展开/收起功能
**验证需求: 17.3**

### 会议界面优化属性

**属性 62: 会议信息面板折叠状态持久化**
*对于任何*会议信息面板的折叠/展开状态，刷新页面后应保持用户上次的选择
**验证需求: 18.5**

**属性 63: 折叠面板显示摘要信息**
*对于任何*折叠状态的会议信息面板，标题栏应显示关键信息摘要（参与者数量、会议状态）
**验证需求: 18.3**

**属性 64: 纪要图标状态指示**
*对于任何*会议，如果存在纪要则显示纪要图标，否则显示生成纪要的入口图标
**验证需求: 19.1, 19.5**

**属性 65: 议题侧边栏状态持久化**
*对于任何*议题侧边栏的展开/收起状态，刷新页面后应保持用户上次的选择
**验证需求: 20.6**

**属性 66: 议题侧边栏徽章显示**
*对于任何*收起状态的议题侧边栏，应显示当前未完成议题数量的徽章
**验证需求: 20.3**

**属性 67: 消息输入区域高度限制**
*对于任何*会议室页面，消息输入区域的高度应不超过视口高度的20%
**验证需求: 21.2**

**属性 68: 输入框固定底部**
*对于任何*消息列表滚动操作，输入区域应保持固定在底部不随滚动移动
**验证需求: 21.3**

## 思维导图功能设计

### 1. 思维导图数据结构

思维导图采用树形结构，每个节点包含内容、层级、父子关系和消息引用。

#### 1.1 节点设计

```python
@dataclass
class MindMapNode:
    id: str  # 唯一标识符
    content: str  # 节点内容文本
    level: int  # 层级：0=根节点，1=一级分支，2=二级分支...
    parent_id: Optional[str]  # 父节点ID，根节点为None
    children_ids: List[str]  # 子节点ID列表
    message_references: List[str]  # 相关消息ID列表
    metadata: Optional[Dict[str, Any]] = None  # 扩展元数据
```

**设计决策**：
- 使用扁平化的节点字典存储，通过 ID 引用建立关系，便于查找和更新
- 每个节点记录相关消息引用，支持从思维导图跳转到具体讨论内容
- metadata 字段预留扩展空间，可存储节点颜色、图标、标签等

#### 1.2 思维导图结构

```python
@dataclass
class MindMap:
    id: str
    meeting_id: str
    root_node: MindMapNode  # 根节点（会议主题）
    nodes: Dict[str, MindMapNode]  # 所有节点的字典 {node_id: node}
    created_at: datetime
    created_by: str  # 生成者ID（user 或 agent_id）
    version: int  # 版本号，每次更新递增
```

### 2. 思维导图生成策略

#### 2.1 生成流程

```python
async def generate_mind_map(meeting: Meeting, generator_id: Optional[str] = None) -> MindMap:
    """
    生成思维导图的核心流程：
    1. 创建根节点（会议主题）
    2. 为每个议题创建一级分支节点
    3. 分析会议消息，提取关键讨论点
    4. 使用 AI 模型组织讨论点为二级/三级分支
    5. 建立节点与消息的引用关系
    """
    
    # 1. 创建根节点
    root_node = MindMapNode(
        id=generate_id(),
        content=meeting.topic,
        level=0,
        parent_id=None,
        children_ids=[],
        message_references=[]
    )
    
    nodes = {root_node.id: root_node}
    
    # 2. 为议题创建一级分支
    for agenda_item in meeting.agenda:
        agenda_node = MindMapNode(
            id=generate_id(),
            content=agenda_item.title,
            level=1,
            parent_id=root_node.id,
            children_ids=[],
            message_references=[]
        )
        nodes[agenda_node.id] = agenda_node
        root_node.children_ids.append(agenda_node.id)
    
    # 3. 使用 AI 分析会议内容，提取关键讨论点
    discussion_points = await extract_discussion_points(meeting, generator_id)
    
    # 4. 将讨论点组织为思维导图节点
    for point in discussion_points:
        # 确定父节点（根据议题关联或内容相似度）
        parent_node = find_best_parent_node(point, nodes)
        
        point_node = MindMapNode(
            id=generate_id(),
            content=point.content,
            level=parent_node.level + 1,
            parent_id=parent_node.id,
            children_ids=[],
            message_references=point.message_ids
        )
        nodes[point_node.id] = point_node
        parent_node.children_ids.append(point_node.id)
    
    # 5. 创建思维导图对象
    mind_map = MindMap(
        id=generate_id(),
        meeting_id=meeting.id,
        root_node=root_node,
        nodes=nodes,
        created_at=datetime.now(),
        created_by=generator_id or 'system',
        version=1
    )
    
    return mind_map
```

#### 2.2 AI 提示词设计

生成思维导图时，向 AI 模型发送的提示词：

```python
def build_mind_map_generation_prompt(meeting: Meeting) -> str:
    """构建思维导图生成的 AI 提示词"""
    
    prompt = f"""
请分析以下会议内容，提取关键讨论点并组织为思维导图结构。

会议主题：{meeting.topic}

会议议题：
{format_agenda_items(meeting.agenda)}

会议讨论内容：
{format_messages_for_analysis(meeting.messages, meeting.current_minutes)}

请按以下格式输出思维导图节点：

1. 识别每个议题下的主要讨论点（2-5个）
2. 为每个讨论点提取支持性观点或细节（1-3个）
3. 标注每个节点关联的消息ID

输出格式（JSON）：
{{
  "discussion_points": [
    {{
      "content": "讨论点内容",
      "parent_agenda": "关联的议题标题",
      "message_ids": ["msg_id_1", "msg_id_2"],
      "sub_points": [
        {{
          "content": "子观点内容",
          "message_ids": ["msg_id_3"]
        }}
      ]
    }}
  ]
}}

要求：
- 内容简洁，每个节点不超过20个字
- 保持逻辑层次清晰
- 确保消息ID引用准确
"""
    return prompt
```

### 3. 思维导图可视化设计

#### 3.1 前端渲染方案

使用 **React Flow** 或 **D3.js** 实现可互动的思维导图可视化。

**推荐方案：React Flow**
- 优点：React 生态集成好，提供开箱即用的拖拽、缩放、连接线等功能
- 适合快速开发和维护

**布局算法**：
- 使用树形布局（Tree Layout）
- 根节点居中，子节点按层级向外辐射
- 自动计算节点位置，避免重叠

#### 3.2 交互功能实现

```typescript
// 思维导图组件状态
interface MindMapState {
  nodes: Node[]  // React Flow 节点
  edges: Edge[]  // React Flow 连接线
  expandedNodes: Set<string>  // 展开的节点ID集合
  selectedNode: string | null  // 当前选中的节点
  viewTransform: { x: number, y: number, zoom: number }  // 视图变换
}

// 节点点击处理：展开/折叠
const handleNodeClick = (nodeId: string) => {
  setExpandedNodes(prev => {
    const newSet = new Set(prev)
    if (newSet.has(nodeId)) {
      newSet.delete(nodeId)  // 折叠
    } else {
      newSet.add(nodeId)  // 展开
    }
    return newSet
  })
  
  // 重新计算可见节点和连接线
  updateVisibleElements()
}

// 节点悬停处理：显示详细信息
const handleNodeHover = (nodeId: string) => {
  const node = mindMap.nodes[nodeId]
  setTooltip({
    visible: true,
    content: node.content,
    messageRefs: node.message_references,
    position: getNodePosition(nodeId)
  })
}

// 消息引用点击：跳转到会议记录
const handleMessageRefClick = (messageId: string) => {
  // 滚动到对应消息
  scrollToMessage(messageId)
  // 高亮显示消息
  highlightMessage(messageId)
}

// 搜索功能
const handleSearch = (keyword: string) => {
  const matchedNodes = Object.values(mindMap.nodes).filter(node =>
    node.content.toLowerCase().includes(keyword.toLowerCase())
  )
  
  // 高亮匹配的节点
  setHighlightedNodes(matchedNodes.map(n => n.id))
  
  // 展开匹配节点的路径
  matchedNodes.forEach(node => {
    expandPathToNode(node.id)
  })
}
```

#### 3.3 UI 组件设计

```jsx
<div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
  {/* 工具栏 */}
  <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0' }}>
    <Space>
      <Input.Search
        placeholder="搜索节点内容..."
        onSearch={handleSearch}
        style={{ width: 300 }}
      />
      <Button icon={<ZoomInOutlined />} onClick={handleZoomIn}>
        放大
      </Button>
      <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut}>
        缩小
      </Button>
      <Button icon={<ExpandOutlined />} onClick={handleExpandAll}>
        全部展开
      </Button>
      <Button icon={<CompressOutlined />} onClick={handleCollapseAll}>
        全部折叠
      </Button>
      <Dropdown menu={{ items: exportMenuItems }}>
        <Button icon={<DownloadOutlined />}>
          导出
        </Button>
      </Dropdown>
    </Space>
  </div>
  
  {/* 思维导图画布 */}
  <div style={{ flex: 1 }}>
    <ReactFlow
      nodes={visibleNodes}
      edges={visibleEdges}
      onNodeClick={(event, node) => handleNodeClick(node.id)}
      onNodeMouseEnter={(event, node) => handleNodeHover(node.id)}
      onNodeMouseLeave={() => setTooltip({ visible: false })}
      fitView
      attributionPosition="bottom-left"
    >
      <Background />
      <Controls />
      <MiniMap />
    </ReactFlow>
  </div>
  
  {/* 节点详情提示框 */}
  {tooltip.visible && (
    <div style={{
      position: 'absolute',
      ...tooltip.position,
      background: 'white',
      border: '1px solid #d9d9d9',
      borderRadius: '4px',
      padding: '12px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      maxWidth: '300px',
      zIndex: 1000
    }}>
      <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>
        {tooltip.content}
      </div>
      {tooltip.messageRefs.length > 0 && (
        <div>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
            相关消息：
          </div>
          {tooltip.messageRefs.map(msgId => (
            <Tag
              key={msgId}
              style={{ cursor: 'pointer' }}
              onClick={() => handleMessageRefClick(msgId)}
            >
              跳转到消息
            </Tag>
          ))}
        </div>
      )}
    </div>
  )}
</div>
```

### 4. 思维导图导出实现

#### 4.1 导出格式处理

```python
class MindMapExporter:
    """思维导图导出器"""
    
    async def export_as_json(self, mind_map: MindMap) -> bytes:
        """导出为 JSON 格式"""
        data = {
            'id': mind_map.id,
            'meeting_id': mind_map.meeting_id,
            'version': mind_map.version,
            'created_at': mind_map.created_at.isoformat(),
            'root_node': asdict(mind_map.root_node),
            'nodes': {nid: asdict(node) for nid, node in mind_map.nodes.items()}
        }
        return json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    
    async def export_as_markdown(self, mind_map: MindMap) -> bytes:
        """导出为 Markdown 格式"""
        lines = [f"# {mind_map.root_node.content}\n"]
        
        def traverse_node(node: MindMapNode, indent_level: int):
            """递归遍历节点生成 Markdown"""
            if node.level > 0:  # 跳过根节点
                indent = "  " * (indent_level - 1)
                lines.append(f"{indent}- {node.content}")
                
                # 添加消息引用
                if node.message_references:
                    lines.append(f"{indent}  *相关消息: {', '.join(node.message_references)}*")
            
            # 递归处理子节点
            for child_id in node.children_ids:
                child_node = mind_map.nodes[child_id]
                traverse_node(child_node, indent_level + 1)
        
        traverse_node(mind_map.root_node, 0)
        return "\n".join(lines).encode('utf-8')
    
    async def export_as_svg(self, mind_map: MindMap) -> bytes:
        """导出为 SVG 格式"""
        # 使用图形库（如 graphviz 或 matplotlib）生成 SVG
        # 这里需要计算节点位置和连接线
        svg_content = self._generate_svg_from_mind_map(mind_map)
        return svg_content.encode('utf-8')
    
    async def export_as_png(self, mind_map: MindMap) -> bytes:
        """导出为 PNG 格式"""
        # 先生成 SVG，然后转换为 PNG
        svg_bytes = await self.export_as_svg(mind_map)
        png_bytes = self._convert_svg_to_png(svg_bytes)
        return png_bytes
```

#### 4.2 前端导出触发

```typescript
const handleExport = async (format: 'png' | 'svg' | 'json' | 'markdown') => {
  try {
    setExporting(true)
    
    // 调用后端 API
    const response = await fetch(`/api/meetings/${meetingId}/mind-map/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format })
    })
    
    if (!response.ok) throw new Error('导出失败')
    
    // 获取文件数据
    const blob = await response.blob()
    
    // 触发下载
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `mind-map-${meetingId}.${format}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    
    message.success('导出成功')
  } catch (error) {
    message.error('导出失败：' + error.message)
  } finally {
    setExporting(false)
  }
}
```

### 5. 思维导图与会议纪要的集成

思维导图和会议纪要是互补的两种会议总结方式：

- **会议纪要**：线性文本，详细记录决策和待办事项，适合阅读和归档
- **思维导图**：图形化结构，展示讨论层次和关联，适合快速理解和回顾

**集成策略**：
1. 生成会议纪要时，可同时生成思维导图
2. 思维导图的节点可以引用纪要中的关键决策
3. 在 UI 中提供纪要和思维导图的切换视图

```python
async def generate_meeting_summary(meeting_id: str) -> Tuple[MeetingMinutes, MindMap]:
    """同时生成会议纪要和思维导图"""
    meeting = await get_meeting(meeting_id)
    
    # 并行生成
    minutes_task = generate_minutes(meeting)
    mind_map_task = generate_mind_map(meeting)
    
    minutes, mind_map = await asyncio.gather(minutes_task, mind_map_task)
    
    return minutes, mind_map
```

### 思维导图生成属性

**属性 69: 思维导图生成功能**
*对于任何*会议，触发思维导图生成后应创建一个包含非空节点数据的思维导图对象
**验证需求: 22.1**

**属性 70: 思维导图结构正确性**
*对于任何*生成的思维导图，中心节点的内容应为会议主题，且会议议题应出现在分支节点中
**验证需求: 22.2**

**属性 71: 思维导图持久化**
*对于任何*生成的思维导图，重新加载会议后应包含该思维导图数据
**验证需求: 22.3**

**属性 72: 思维导图更新功能**
*对于任何*已有思维导图的会议，添加新消息后重新生成思维导图应更新思维导图版本
**验证需求: 22.4**

**属性 73: 思维导图访问入口**
*对于任何*包含思维导图数据的会议，会议对象的 mind_map 字段应非空
**验证需求: 22.5**

### 思维导图交互属性

**属性 74: 思维导图渲染完整性**
*对于任何*思维导图数据，渲染函数应返回包含所有节点和连接关系的渲染结构
**验证需求: 23.1**

**属性 75: 节点展开折叠状态切换**
*对于任何*思维导图节点，点击操作应正确切换该节点的展开/折叠状态
**验证需求: 23.2**

**属性 76: 节点详细信息显示**
*对于任何*思维导图节点，悬停事件应返回该节点的详细信息和消息引用列表
**验证需求: 23.3**

**属性 77: 消息引用跳转**
*对于任何*节点中的消息引用，点击应返回正确的消息ID用于导航
**验证需求: 23.4**

**属性 78: 视图变换状态管理**
*对于任何*拖拽或缩放操作，视图变换状态应正确更新并反映在渲染中
**验证需求: 23.5**

**属性 79: 思维导图搜索功能**
*对于任何*包含多个节点的思维导图和搜索关键词，搜索应返回所有内容匹配的节点
**验证需求: 23.6**

### 思维导图导出属性

**属性 80: 导出格式支持**
*对于任何*思维导图导出请求，系统应支持 PNG、SVG、JSON 和 Markdown 四种格式
**验证需求: 24.1**

**属性 81: 图片格式导出有效性**
*对于任何*思维导图，导出为 PNG 或 SVG 格式应返回有效的图片数据
**验证需求: 24.2**

**属性 82: JSON 导出往返一致性**
*对于任何*思维导图，导出为 JSON 后解析应得到包含所有节点和关系的等价结构
**验证需求: 24.3**

**属性 83: Markdown 导出层级结构**
*对于任何*思维导图，导出为 Markdown 应包含正确的层级结构（使用标题或列表缩进）
**验证需求: 24.4**

**属性 84: 导出结果可用性**
*对于任何*思维导图导出操作，应返回文件数据或下载 URL
**验证需求: 24.5**

