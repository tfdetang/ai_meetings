"""Tests for agent service role template functionality"""

import pytest
from src.services.agent_service import AgentService
from src.storage.file_storage import FileStorageService
from src.exceptions import ValidationError


@pytest.fixture
async def agent_service(tmp_path):
    """Create agent service with temporary storage"""
    storage = FileStorageService(str(tmp_path))
    return AgentService(storage)


@pytest.mark.asyncio
async def test_create_agent_from_template(agent_service):
    """Test creating an agent from a role template"""
    model_config = {
        'provider': 'openai',
        'model_name': 'gpt-4',
        'api_key': 'test-key-123'
    }
    
    agent = await agent_service.create_agent_from_template(
        name='Alice',
        template_name='product_manager',
        model_config=model_config
    )
    
    assert agent.name == 'Alice'
    assert agent.role.name == 'Product Manager'
    assert len(agent.role.description) > 0
    assert len(agent.role.system_prompt) > 0
    assert 'product' in agent.role.system_prompt.lower()
    assert agent.model_config.provider == 'openai'
    assert agent.model_config.model_name == 'gpt-4'


@pytest.mark.asyncio
async def test_create_agent_from_template_invalid_template(agent_service):
    """Test creating agent with invalid template name"""
    model_config = {
        'provider': 'openai',
        'model_name': 'gpt-4',
        'api_key': 'test-key-123'
    }
    
    with pytest.raises(ValidationError) as exc_info:
        await agent_service.create_agent_from_template(
            name='Bob',
            template_name='nonexistent_template',
            model_config=model_config
        )
    
    assert 'template' in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_multiple_agents_from_different_templates(agent_service):
    """Test creating multiple agents from different templates"""
    model_config = {
        'provider': 'openai',
        'model_name': 'gpt-4',
        'api_key': 'test-key-123'
    }
    
    pm_agent = await agent_service.create_agent_from_template(
        name='PM Agent',
        template_name='product_manager',
        model_config=model_config
    )
    
    eng_agent = await agent_service.create_agent_from_template(
        name='Engineer Agent',
        template_name='software_engineer',
        model_config=model_config
    )
    
    designer_agent = await agent_service.create_agent_from_template(
        name='Designer Agent',
        template_name='ux_designer',
        model_config=model_config
    )
    
    # Verify they have different roles
    assert pm_agent.role.name != eng_agent.role.name
    assert eng_agent.role.name != designer_agent.role.name
    assert pm_agent.role.system_prompt != eng_agent.role.system_prompt
    
    # Verify all were saved
    agents = await agent_service.list_agents()
    assert len(agents) == 3


@pytest.mark.asyncio
async def test_get_available_role_templates(agent_service):
    """Test getting list of available role templates"""
    templates = agent_service.get_available_role_templates()
    
    assert isinstance(templates, list)
    assert len(templates) > 0
    assert 'product_manager' in templates
    assert 'software_engineer' in templates
    assert 'ux_designer' in templates


@pytest.mark.asyncio
async def test_create_agent_from_template_with_parameters(agent_service):
    """Test creating agent from template with model parameters"""
    model_config = {
        'provider': 'openai',
        'model_name': 'gpt-4',
        'api_key': 'test-key-123',
        'parameters': {
            'temperature': 0.7,
            'max_tokens': 1000
        }
    }
    
    agent = await agent_service.create_agent_from_template(
        name='Configured Agent',
        template_name='qa_engineer',
        model_config=model_config
    )
    
    assert agent.role.name == 'QA Engineer'
    assert agent.model_config.parameters is not None
    assert agent.model_config.parameters.temperature == 0.7
    assert agent.model_config.parameters.max_tokens == 1000


@pytest.mark.asyncio
async def test_create_agent_from_template_persists(agent_service):
    """Test that agent created from template is properly persisted"""
    model_config = {
        'provider': 'anthropic',
        'model_name': 'claude-3',
        'api_key': 'test-key-456'
    }
    
    agent = await agent_service.create_agent_from_template(
        name='Persistent Agent',
        template_name='security_engineer',
        model_config=model_config
    )
    
    # Retrieve the agent
    retrieved = await agent_service.get_agent(agent.id)
    
    assert retrieved.id == agent.id
    assert retrieved.name == agent.name
    assert retrieved.role.name == agent.role.name
    assert retrieved.role.description == agent.role.description
    assert retrieved.role.system_prompt == agent.role.system_prompt
