"""Agent service implementation"""

import uuid
from typing import Dict, Any, List

from .interfaces import IAgentService, IStorageService
from ..models import Agent, Role, ModelConfig, ModelParameters
from ..models.role_templates import get_role_template, list_role_templates
from ..exceptions import ValidationError, NotFoundError
from ..adapters.factory import ModelAdapterFactory


class AgentService(IAgentService):
    """Service for managing AI agents"""

    def __init__(self, storage: IStorageService):
        """
        Initialize agent service
        
        Args:
            storage: Storage service for persisting agents
        """
        self.storage = storage

    async def create_agent(self, agent_data: Dict[str, Any]) -> Agent:
        """
        Create new agent
        
        Args:
            agent_data: Dictionary containing agent configuration
                Required keys: name, role (dict), model_config (dict)
                
        Returns:
            Created Agent instance
            
        Raises:
            ValidationError: If input data is invalid
        """
        # Generate unique ID
        agent_id = str(uuid.uuid4())
        
        # Extract and validate name
        name = agent_data.get('name', '').strip()
        if not name:
            raise ValidationError("Agent name cannot be empty", "name")
        if len(name) > 50:
            raise ValidationError("Agent name must be 50 characters or less", "name")
        
        # Extract and create role
        role_data = agent_data.get('role')
        if not role_data:
            raise ValidationError("Role configuration is required", "role")
        
        try:
            role = Role(
                name=role_data.get('name', ''),
                description=role_data.get('description', ''),
                system_prompt=role_data.get('system_prompt', '')
            )
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Invalid role configuration: {str(e)}", "role")
        
        # Extract and create model config
        model_config_data = agent_data.get('model_config')
        if not model_config_data:
            raise ValidationError("Model configuration is required", "model_config")
        
        try:
            # Handle parameters if present
            params_data = model_config_data.get('parameters')
            parameters = None
            if params_data and isinstance(params_data, dict) and len(params_data) > 0:
                parameters = ModelParameters(
                    temperature=params_data.get('temperature'),
                    max_tokens=params_data.get('max_tokens'),
                    top_p=params_data.get('top_p')
                )
            
            model_config = ModelConfig(
                provider=model_config_data.get('provider'),
                model_name=model_config_data.get('model_name', ''),
                api_key=model_config_data.get('api_key', ''),
                parameters=parameters
            )
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Invalid model configuration: {str(e)}", "model_config")
        
        # Create agent
        agent = Agent(
            id=agent_id,
            name=name,
            role=role,
            model_config=model_config
        )
        
        # Save agent
        await self.storage.save_agent(agent)
        
        return agent

    async def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Agent:
        """
        Update agent
        
        Args:
            agent_id: ID of agent to update
            updates: Dictionary containing fields to update
            
        Returns:
            Updated Agent instance
            
        Raises:
            NotFoundError: If agent doesn't exist
            ValidationError: If update data is invalid
        """
        # Load existing agent
        agent = await self.storage.load_agent(agent_id)
        if agent is None:
            raise NotFoundError(
                f"Agent {agent_id} not found",
                resource_type="agent",
                resource_id=agent_id
            )
        
        # Update name if provided
        if 'name' in updates:
            name = updates['name'].strip() if isinstance(updates['name'], str) else ''
            if not name:
                raise ValidationError("Agent name cannot be empty", "name")
            if len(name) > 50:
                raise ValidationError("Agent name must be 50 characters or less", "name")
            agent.name = name
        
        # Update role if provided
        if 'role' in updates:
            role_data = updates['role']
            if not isinstance(role_data, dict):
                raise ValidationError("Role must be a dictionary", "role")
            
            try:
                agent.role = Role(
                    name=role_data.get('name', agent.role.name),
                    description=role_data.get('description', agent.role.description),
                    system_prompt=role_data.get('system_prompt', agent.role.system_prompt)
                )
            except ValidationError:
                raise
            except Exception as e:
                raise ValidationError(f"Invalid role configuration: {str(e)}", "role")
        
        # Update model_config if provided
        if 'model_config' in updates:
            model_config_data = updates['model_config']
            if not isinstance(model_config_data, dict):
                raise ValidationError("Model config must be a dictionary", "model_config")
            
            try:
                # Handle parameters
                # Check if 'parameters' key is explicitly in the update data
                if 'parameters' in model_config_data:
                    params_data = model_config_data['parameters']
                    if params_data is None:
                        # Explicitly clearing parameters
                        parameters = None
                    elif isinstance(params_data, dict) and len(params_data) > 0:
                        parameters = ModelParameters(
                            temperature=params_data.get('temperature'),
                            max_tokens=params_data.get('max_tokens'),
                            top_p=params_data.get('top_p')
                        )
                    else:
                        # Empty dict or other falsy value - clear parameters
                        parameters = None
                else:
                    # 'parameters' key not in updates - keep existing parameters
                    parameters = agent.model_config.parameters
                
                agent.model_config = ModelConfig(
                    provider=model_config_data.get('provider', agent.model_config.provider),
                    model_name=model_config_data.get('model_name', agent.model_config.model_name),
                    api_key=model_config_data.get('api_key', agent.model_config.api_key),
                    parameters=parameters
                )
            except ValidationError:
                raise
            except Exception as e:
                raise ValidationError(f"Invalid model configuration: {str(e)}", "model_config")
        
        # Save updated agent
        await self.storage.save_agent(agent)
        
        return agent

    async def delete_agent(self, agent_id: str) -> None:
        """
        Delete agent
        
        Args:
            agent_id: ID of agent to delete
            
        Raises:
            NotFoundError: If agent doesn't exist
        """
        await self.storage.delete_agent(agent_id)

    async def get_agent(self, agent_id: str) -> Agent:
        """
        Get agent details
        
        Args:
            agent_id: ID of agent to retrieve
            
        Returns:
            Agent instance
            
        Raises:
            NotFoundError: If agent doesn't exist
        """
        agent = await self.storage.load_agent(agent_id)
        if agent is None:
            raise NotFoundError(
                f"Agent {agent_id} not found",
                resource_type="agent",
                resource_id=agent_id
            )
        return agent

    async def list_agents(self) -> List[Agent]:
        """
        List all agents
        
        Returns:
            List of all Agent instances
        """
        return await self.storage.load_all_agents()

    async def test_agent_connection(self, agent_id: str) -> bool:
        """
        Test agent connection to AI model
        
        Args:
            agent_id: ID of agent to test
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            NotFoundError: If agent doesn't exist
        """
        # Get agent
        agent = await self.get_agent(agent_id)
        
        # Create adapter for the agent's model
        try:
            adapter = ModelAdapterFactory.create(agent.model_config)
            return await adapter.test_connection()
        except Exception:
            # If adapter creation or connection test fails, return False
            return False

    async def create_agent_from_template(
        self,
        name: str,
        template_name: str,
        model_config: Dict[str, Any]
    ) -> Agent:
        """
        Create agent using a role template
        
        Args:
            name: Name for the agent
            template_name: Name of the role template to use
            model_config: Model configuration dictionary
            
        Returns:
            Created Agent instance
            
        Raises:
            ValidationError: If input data is invalid
            KeyError: If template_name doesn't exist
        """
        # Get the role template
        try:
            role = get_role_template(template_name)
        except KeyError as e:
            raise ValidationError(
                f"Invalid role template: {str(e)}",
                "template_name"
            )
        
        # Create agent data with the template role
        agent_data = {
            'name': name,
            'role': role.to_dict(),
            'model_config': model_config
        }
        
        return await self.create_agent(agent_data)

    def get_available_role_templates(self) -> List[str]:
        """
        Get list of available role template names
        
        Returns:
            List of template names
        """
        return list_role_templates()
