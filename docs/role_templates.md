# Role Templates

Role templates provide preset role configurations for common agent types in the AI Agent Meeting System. This feature makes it easy to quickly create agents with well-defined, consistent roles without having to manually write role descriptions and system prompts.

## Available Templates

The system includes the following preset role templates:

1. **product_manager** - 产品经理
   - 资深产品经理，从业务目标、用户价值、需求拆解等角度提供专业意见
   - 提供结构化观点和多个备选方案

2. **art_director** - 美术总监
   - 负责整体美术方向、风格统一性、资源计划和成本控制
   - 清晰描述视觉风格并给出可执行的资源计划

3. **tech_lead** - 技术负责人
   - 从技术视角评估可行性、架构、性能和风险
   - 提供多个技术方案和风险评估

4. **accountant** - 会计师
   - 从财务角度分析成本结构、预算执行和合规性
   - 说明财务影响和会计处理逻辑

5. **auditor** - 审计师
   - 从审计视角评估内部控制、流程风险和合规性
   - 提供风险级别和整改建议

6. **marketing_director** - 营销总监
   - 负责市场分析、用户画像、渠道策略和品牌传播
   - 基于数据提供营销动作和 KPI 测量方式

7. **operations_manager** - 运营负责人
   - 负责流程设计、用户生命周期、活动体系和成本效益
   - 提供关键流程、指标和可执行方案

8. **sales_director** - 销售总监
   - 负责销售管线、客户需求、定价策略和收入预测
   - 分析销售机会和成交阻力

9. **ux_designer** - UX 设计师
   - 关注用户旅程、可用性、信息架构和可访问性
   - 提供用户痛点分析和原型建议

10. **data_scientist** - 数据科学家
    - 从数据角度提供洞察、模型方法和假设验证
    - 包含数据洞察、模型方案和验证方法

11. **legal_advisor** - 法务顾问
    - 从法律角度评估合同风险、知识产权、合规性和责任边界
    - 提供法律风险级别和法务建议

12. **general_employee** - 通用会议参与者
    - 能够从多角度分析问题、拆解议题并提供结构化建议
    - 适用于需要全面分析的通用会议场景

## Usage

### Listing Available Templates

```python
from src.models.role_templates import list_role_templates

# Get list of all template names
templates = list_role_templates()
print(templates)
# ['product_manager', 'software_engineer', 'ux_designer', ...]
```

### Getting Template Information

```python
from src.models.role_templates import get_role_template_info

# Get basic info about a template
info = get_role_template_info('product_manager')
print(info['name'])  # "Product Manager"
print(info['description'])  # "A strategic product manager..."
```

### Creating a Role from a Template

```python
from src.models.role_templates import get_role_template

# Get a complete Role object from a template
role = get_role_template('software_engineer')
print(role.name)  # "Software Engineer"
print(role.description)
print(role.system_prompt)
```

### Creating an Agent with a Template (Recommended)

The easiest way to use templates is through the `AgentService`:

```python
from src.services.agent_service import AgentService
from src.storage.file_storage import FileStorageService

# Initialize services
storage = FileStorageService('./data')
agent_service = AgentService(storage)

# Model configuration
model_config = {
    'provider': 'openai',
    'model_name': 'gpt-4',
    'api_key': 'your-api-key-here',
    'parameters': {
        'temperature': 0.7,
        'max_tokens': 1000
    }
}

# Create agent from template
agent = await agent_service.create_agent_from_template(
    name='Alice',
    template_name='product_manager',
    model_config=model_config
)
```

### Getting Available Templates from Agent Service

```python
# List templates through the agent service
templates = agent_service.get_available_role_templates()
```

## Creating a Meeting with Template Agents

Here's a complete example of creating a meeting with multiple agents using templates:

```python
import asyncio
from src.services.agent_service import AgentService
from src.services.meeting_service import MeetingService
from src.storage.file_storage import FileStorageService
from src.models import MeetingConfig, SpeakingOrder

async def create_product_meeting():
    # Initialize services
    storage = FileStorageService('./data')
    agent_service = AgentService(storage)
    meeting_service = MeetingService(storage, agent_service)
    
    # Model configuration
    model_config = {
        'provider': 'openai',
        'model_name': 'gpt-4',
        'api_key': 'your-api-key-here'
    }
    
    # Create agents with different roles
    pm = await agent_service.create_agent_from_template(
        name='Product Manager',
        template_name='product_manager',
        model_config=model_config
    )
    
    engineer = await agent_service.create_agent_from_template(
        name='Engineer',
        template_name='software_engineer',
        model_config=model_config
    )
    
    designer = await agent_service.create_agent_from_template(
        name='Designer',
        template_name='ux_designer',
        model_config=model_config
    )
    
    # Create meeting
    meeting_config = MeetingConfig(
        max_rounds=5,
        speaking_order=SpeakingOrder.SEQUENTIAL
    )
    
    meeting = await meeting_service.create_meeting(
        topic='Discuss new feature: User Dashboard',
        agent_ids=[pm.id, engineer.id, designer.id],
        config=meeting_config
    )
    
    return meeting

# Run the example
asyncio.run(create_product_meeting())
```

## Benefits of Using Templates

1. **Consistency**: All agents with the same role have consistent behavior
2. **Speed**: Quickly create agents without writing detailed prompts
3. **Quality**: Templates include well-crafted system prompts and descriptions
4. **Maintainability**: Update role definitions in one place
5. **Best Practices**: Templates embody best practices for each role type

## Customization

While templates provide good defaults, you can still customize agents after creation:

```python
# Create agent from template
agent = await agent_service.create_agent_from_template(
    name='Custom PM',
    template_name='product_manager',
    model_config=model_config
)

# Customize the role if needed
await agent_service.update_agent(agent.id, {
    'role': {
        'name': 'Senior Product Manager',
        'description': agent.role.description + ' Specializes in B2B products.',
        'system_prompt': agent.role.system_prompt + ' Focus on enterprise needs.'
    }
})
```

## Adding New Templates

To add new role templates, edit `src/models/role_templates.py` and add entries to the `ROLE_TEMPLATES` dictionary:

```python
ROLE_TEMPLATES = {
    # ... existing templates ...
    
    "your_new_role": Role(
        name="Your Role Name",
        description="Brief description of the role",
        system_prompt="Detailed system prompt for the AI model"
    ),
}
```

Make sure the role follows validation rules:
- Name: 1-50 characters
- Description: 1-2000 characters
- System Prompt: 1-2000 characters
