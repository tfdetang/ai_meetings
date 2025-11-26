"""Tests for AgentService"""

import pytest
from src.services.agent_service import AgentService
from src.storage.file_storage import FileStorageService
from src.exceptions import ValidationError, NotFoundError


@pytest.fixture
async def agent_service(tmp_path):
    """Create agent service with temporary storage"""
    storage = FileStorageService(str(tmp_path / "test_data"))
    return AgentService(storage)


@pytest.fixture
def valid_agent_data():
    """Valid agent data for testing"""
    return {
        'name': 'Test Agent',
        'role': {
            'name': 'Tester',
            'description': 'A test role for testing purposes',
            'system_prompt': 'You are a helpful test assistant'
        },
        'model_config': {
            'provider': 'openai',
            'model_name': 'gpt-4',
            'api_key': 'test-api-key-123'
        }
    }


@pytest.mark.asyncio
async def test_create_agent(agent_service, valid_agent_data):
    """Test creating an agent"""
    agent = await agent_service.create_agent(valid_agent_data)
    
    assert agent.id is not None
    assert agent.name == 'Test Agent'
    assert agent.role.name == 'Tester'
    assert agent.model_config.provider == 'openai'


@pytest.mark.asyncio
async def test_create_agent_with_parameters(agent_service, valid_agent_data):
    """Test creating an agent with model parameters"""
    valid_agent_data['model_config']['parameters'] = {
        'temperature': 0.7,
        'max_tokens': 1000
    }
    
    agent = await agent_service.create_agent(valid_agent_data)
    
    assert agent.model_config.parameters is not None
    assert agent.model_config.parameters.temperature == 0.7
    assert agent.model_config.parameters.max_tokens == 1000


@pytest.mark.asyncio
async def test_create_agent_empty_name(agent_service, valid_agent_data):
    """Test that empty name is rejected"""
    valid_agent_data['name'] = ''
    
    with pytest.raises(ValidationError) as exc_info:
        await agent_service.create_agent(valid_agent_data)
    
    assert exc_info.value.field == 'name'


@pytest.mark.asyncio
async def test_create_agent_missing_role(agent_service, valid_agent_data):
    """Test that missing role is rejected"""
    del valid_agent_data['role']
    
    with pytest.raises(ValidationError) as exc_info:
        await agent_service.create_agent(valid_agent_data)
    
    assert exc_info.value.field == 'role'


@pytest.mark.asyncio
async def test_get_agent(agent_service, valid_agent_data):
    """Test getting an agent"""
    created_agent = await agent_service.create_agent(valid_agent_data)
    
    retrieved_agent = await agent_service.get_agent(created_agent.id)
    
    assert retrieved_agent.id == created_agent.id
    assert retrieved_agent.name == created_agent.name


@pytest.mark.asyncio
async def test_get_nonexistent_agent(agent_service):
    """Test getting a nonexistent agent raises NotFoundError"""
    with pytest.raises(NotFoundError) as exc_info:
        await agent_service.get_agent('nonexistent-id')
    
    assert exc_info.value.resource_type == 'agent'


@pytest.mark.asyncio
async def test_list_agents(agent_service, valid_agent_data):
    """Test listing agents"""
    # Create multiple agents
    agent1 = await agent_service.create_agent(valid_agent_data)
    
    valid_agent_data['name'] = 'Second Agent'
    agent2 = await agent_service.create_agent(valid_agent_data)
    
    agents = await agent_service.list_agents()
    
    assert len(agents) == 2
    agent_ids = [a.id for a in agents]
    assert agent1.id in agent_ids
    assert agent2.id in agent_ids


@pytest.mark.asyncio
async def test_update_agent_name(agent_service, valid_agent_data):
    """Test updating agent name"""
    agent = await agent_service.create_agent(valid_agent_data)
    
    updated_agent = await agent_service.update_agent(agent.id, {'name': 'Updated Name'})
    
    assert updated_agent.name == 'Updated Name'
    assert updated_agent.id == agent.id


@pytest.mark.asyncio
async def test_update_agent_role(agent_service, valid_agent_data):
    """Test updating agent role"""
    agent = await agent_service.create_agent(valid_agent_data)
    
    new_role = {
        'name': 'New Role',
        'description': 'A new role description',
        'system_prompt': 'New system prompt'
    }
    
    updated_agent = await agent_service.update_agent(agent.id, {'role': new_role})
    
    assert updated_agent.role.name == 'New Role'
    assert updated_agent.role.description == 'A new role description'


@pytest.mark.asyncio
async def test_update_nonexistent_agent(agent_service):
    """Test updating a nonexistent agent raises NotFoundError"""
    with pytest.raises(NotFoundError):
        await agent_service.update_agent('nonexistent-id', {'name': 'New Name'})


@pytest.mark.asyncio
async def test_delete_agent(agent_service, valid_agent_data):
    """Test deleting an agent"""
    agent = await agent_service.create_agent(valid_agent_data)
    
    await agent_service.delete_agent(agent.id)
    
    with pytest.raises(NotFoundError):
        await agent_service.get_agent(agent.id)


@pytest.mark.asyncio
async def test_delete_nonexistent_agent(agent_service):
    """Test deleting a nonexistent agent raises NotFoundError"""
    with pytest.raises(NotFoundError):
        await agent_service.delete_agent('nonexistent-id')


@pytest.mark.asyncio
async def test_test_agent_connection_returns_bool(agent_service, valid_agent_data):
    """Test that test_agent_connection returns a boolean"""
    agent = await agent_service.create_agent(valid_agent_data)
    
    # This will likely return False since we don't have real API keys
    # but it should return a boolean, not raise an exception
    result = await agent_service.test_agent_connection(agent.id)
    
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_test_connection_nonexistent_agent(agent_service):
    """Test testing connection for nonexistent agent raises NotFoundError"""
    with pytest.raises(NotFoundError):
        await agent_service.test_agent_connection('nonexistent-id')
