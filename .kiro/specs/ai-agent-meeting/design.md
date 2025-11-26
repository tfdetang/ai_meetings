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
from typing import List
from enum import Enum

class SpeakingOrder(Enum):
    SEQUENTIAL = 'sequential'
    RANDOM = 'random'

class MeetingStatus(Enum):
    ACTIVE = 'active'
    PAUSED = 'paused'
    ENDED = 'ended'

@dataclass
class MeetingConfig:
    max_rounds: Optional[int] = None
    max_message_length: Optional[int] = None
    speaking_order: SpeakingOrder = SpeakingOrder.SEQUENTIAL

@dataclass
class Meeting:
    id: str
    topic: str
    participants: List[Agent]
    messages: List['Message']
    config: MeetingConfig
    status: MeetingStatus
    created_at: datetime
    updated_at: datetime
```

#### Message（消息）
```python
from typing import Literal

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
        self, topic: str, agent_ids: List[str], config: MeetingConfig
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

2. **不变量属性** (Properties 1, 3, 9, 22):
   - 数据结构完整性
   - 必需字段存在性
   - 元数据一致性

3. **状态转换属性** (Properties 16, 17, 18, 28):
   - 会议状态机正确性
   - 轮次管理
   - 自动结束条件

4. **集合操作属性** (Properties 3, 5, 23, 26):
   - 列表完整性
   - 删除操作正确性
   - 查询一致性

5. **顺序属性** (Properties 13, 30):
   - 顺序发言模式
   - 随机发言模式

6. **验证属性** (Properties 11, 21, 29):
   - 输入验证规则
   - 长度限制
   - 空值拒绝

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

