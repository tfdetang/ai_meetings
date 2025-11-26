# Role Templates

Role templates provide preset role configurations for common agent types in the AI Agent Meeting System. This feature makes it easy to quickly create agents with well-defined, consistent roles without having to manually write role descriptions and system prompts.

## Available Templates

The system includes the following preset role templates:

1. **product_manager** - Product Manager
   - Strategic focus on user needs, business value, and product vision
   - Balances technical feasibility with market demands

2. **software_engineer** - Software Engineer
   - Pragmatic focus on technical implementation and code quality
   - Values maintainability and scalability

3. **ux_designer** - UX Designer
   - User-centered focus on experience and interface design
   - Advocates for intuitive and accessible design

4. **qa_engineer** - QA Engineer
   - Detail-oriented focus on testing and quality assurance
   - Identifies potential issues and edge cases early

5. **data_analyst** - Data Analyst
   - Analytical focus on metrics and data-driven insights
   - Uses data to inform product and business decisions

6. **business_analyst** - Business Analyst
   - Bridges technical and business stakeholders
   - Focuses on requirements, processes, and business value

7. **devops_engineer** - DevOps Engineer
   - Infrastructure focus on deployment and reliability
   - Concerned with monitoring and operational excellence

8. **security_engineer** - Security Engineer
   - Security focus on vulnerabilities and threat modeling
   - Advocates for security best practices

9. **technical_writer** - Technical Writer
   - Documentation focus on clear communication
   - Makes complex technical concepts accessible

10. **project_manager** - Project Manager
    - Organizational focus on timelines and resources
    - Ensures projects are delivered successfully

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
