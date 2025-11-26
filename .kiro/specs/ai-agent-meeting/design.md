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

