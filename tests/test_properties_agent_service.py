"""Property-based tests for agent service operations"""

import pytest
import tempfile
import shutil
from hypothesis import given, strategies as st

from src.models import Agent, Role, ModelConfig, ModelParameters
from src.storage import FileStorageService
from src.services.agent_service import AgentService


# Reuse strategies from other test files
role_strategy = st.builds(
    Role,
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    description=st.text(min_size=1, max_size=2000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    system_prompt=st.text(min_size=1, max_size=2000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip())
)

model_parameters_strategy = st.builds(
    ModelParameters,
    temperature=st.none() | st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
    max_tokens=st.none() | st.integers(min_value=1, max_value=100000),
    top_p=st.none() | st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
)

model_config_strategy = st.builds(
    ModelConfig,
    provider=st.sampled_from(['openai', 'anthropic', 'google', 'glm']),
    model_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    api_key=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    parameters=st.none() | model_parameters_strategy
)

# Strategy for filesystem-safe IDs (alphanumeric + dash/underscore)
filesystem_safe_id_strategy = st.text(
    min_size=1, 
    max_size=100, 
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
).filter(lambda x: x and x.strip() and not x.startswith('-') and not x.startswith('_'))

agent_strategy = st.builds(
    Agent,
    id=filesystem_safe_id_strategy,
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    role=role_strategy,
    model_config=model_config_strategy
)


# Feature: ai-agent-meeting, Property 4: 代理更新一致性
# Validates: Requirements 1.4
@given(
    agent=agent_strategy,
    update_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    update_role=role_strategy,
    update_model_config=model_config_strategy
)
@pytest.mark.asyncio
async def test_property_agent_update_consistency(agent, update_name, update_role, update_model_config):
    """
    Property 4: Agent Update Consistency
    For any existing agent and valid update data, after the update operation,
    reloading should reflect all changes.
    """
    # Create temporary storage for this test
    temp_dir = tempfile.mkdtemp()
    try:
        temp_storage = FileStorageService(base_path=temp_dir)
        agent_service = AgentService(temp_storage)
        
        # Save the original agent
        await temp_storage.save_agent(agent)
        
        # Prepare update data
        updates = {
            'name': update_name,
            'role': {
                'name': update_role.name,
                'description': update_role.description,
                'system_prompt': update_role.system_prompt
            },
            'model_config': {
                'provider': update_model_config.provider,
                'model_name': update_model_config.model_name,
                'api_key': update_model_config.api_key,
                'parameters': None if update_model_config.parameters is None else {
                    'temperature': update_model_config.parameters.temperature,
                    'max_tokens': update_model_config.parameters.max_tokens,
                    'top_p': update_model_config.parameters.top_p
                }
            }
        }
        
        # Update the agent
        updated_agent = await agent_service.update_agent(agent.id, updates)
        
        # Reload the agent from storage
        reloaded_agent = await agent_service.get_agent(agent.id)
        
        # Verify the ID remains the same
        assert reloaded_agent.id == agent.id
        
        # The agent service strips whitespace from names, so we need to compare with stripped version
        expected_name = update_name.strip()
        
        # Verify all updated fields are reflected
        assert reloaded_agent.name == expected_name
        assert reloaded_agent.role.name == update_role.name
        assert reloaded_agent.role.description == update_role.description
        assert reloaded_agent.role.system_prompt == update_role.system_prompt
        assert reloaded_agent.model_config.provider == update_model_config.provider
        assert reloaded_agent.model_config.model_name == update_model_config.model_name
        assert reloaded_agent.model_config.api_key == update_model_config.api_key
        
        # Determine expected parameters based on update_model_config
        expected_has_params = False
        if update_model_config.parameters:
            # Check if parameters has any non-None values
            expected_has_params = (
                update_model_config.parameters.temperature is not None or
                update_model_config.parameters.max_tokens is not None or
                update_model_config.parameters.top_p is not None
            )
        
        # Verify parameters match expectations
        if expected_has_params:
            assert reloaded_agent.model_config.parameters is not None
            assert reloaded_agent.model_config.parameters.temperature == update_model_config.parameters.temperature
            assert reloaded_agent.model_config.parameters.max_tokens == update_model_config.parameters.max_tokens
            assert reloaded_agent.model_config.parameters.top_p == update_model_config.parameters.top_p
        else:
            # Empty parameters (all None) or None should become None after round-trip
            assert reloaded_agent.model_config.parameters is None
        
        # Verify the updated_agent returned by update_agent matches the reloaded one
        assert updated_agent.name == reloaded_agent.name
        assert updated_agent.role.name == reloaded_agent.role.name
        assert updated_agent.model_config.provider == reloaded_agent.model_config.provider
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
