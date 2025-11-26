"""
Example usage of role templates in the AI Agent Meeting System

This example demonstrates how to use preset role templates to quickly
create agents with predefined roles.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.role_templates import (
    list_role_templates,
    get_role_template,
    get_role_template_info,
    get_all_role_templates
)
from src.services.agent_service import AgentService
from src.storage.file_storage import FileStorageService


async def example_list_templates():
    """Example: List all available role templates"""
    print("Available Role Templates:")
    print("-" * 50)
    
    templates = list_role_templates()
    for template_name in templates:
        info = get_role_template_info(template_name)
        print(f"\n{template_name}:")
        print(f"  Name: {info['name']}")
        print(f"  Description: {info['description']}")


async def example_get_template():
    """Example: Get a specific role template"""
    print("\n\nGetting Product Manager Template:")
    print("-" * 50)
    
    role = get_role_template('product_manager')
    print(f"Name: {role.name}")
    print(f"Description: {role.description}")
    print(f"System Prompt: {role.system_prompt[:100]}...")


async def example_create_agent_with_template():
    """Example: Create an agent using a role template"""
    print("\n\nCreating Agent with Template:")
    print("-" * 50)
    
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
        name='Alice the PM',
        template_name='product_manager',
        model_config=model_config
    )
    
    print(f"Created agent: {agent.name}")
    print(f"Role: {agent.role.name}")
    print(f"Model: {agent.model_config.provider}/{agent.model_config.model_name}")


async def example_create_meeting_with_template_agents():
    """Example: Create a meeting with multiple agents from templates"""
    print("\n\nCreating Meeting with Template Agents:")
    print("-" * 50)
    
    # Initialize services
    storage = FileStorageService('./data')
    agent_service = AgentService(storage)
    
    # Model configuration (same for all agents in this example)
    model_config = {
        'provider': 'openai',
        'model_name': 'gpt-4',
        'api_key': 'your-api-key-here'
    }
    
    # Create multiple agents with different roles
    pm_agent = await agent_service.create_agent_from_template(
        name='Product Manager',
        template_name='product_manager',
        model_config=model_config
    )
    
    engineer_agent = await agent_service.create_agent_from_template(
        name='Software Engineer',
        template_name='software_engineer',
        model_config=model_config
    )
    
    designer_agent = await agent_service.create_agent_from_template(
        name='UX Designer',
        template_name='ux_designer',
        model_config=model_config
    )
    
    qa_agent = await agent_service.create_agent_from_template(
        name='QA Engineer',
        template_name='qa_engineer',
        model_config=model_config
    )
    
    print(f"Created {len([pm_agent, engineer_agent, designer_agent, qa_agent])} agents:")
    for agent in [pm_agent, engineer_agent, designer_agent, qa_agent]:
        print(f"  - {agent.name} ({agent.role.name})")
    
    print("\nThese agents can now participate in a meeting!")


async def example_manual_role_vs_template():
    """Example: Compare manual role creation vs template usage"""
    print("\n\nManual Role vs Template:")
    print("-" * 50)
    
    # Manual role creation (the old way)
    from src.models import Role
    
    manual_role = Role(
        name="Product Manager",
        description="A product manager focused on user needs and business value",
        system_prompt="You are a product manager. Focus on user needs and business value."
    )
    
    # Template role (the new way)
    template_role = get_role_template('product_manager')
    
    print("Manual Role:")
    print(f"  System Prompt Length: {len(manual_role.system_prompt)} chars")
    print(f"  Description Length: {len(manual_role.description)} chars")
    
    print("\nTemplate Role:")
    print(f"  System Prompt Length: {len(template_role.system_prompt)} chars")
    print(f"  Description Length: {len(template_role.description)} chars")
    
    print("\nTemplates provide more detailed and consistent role definitions!")


async def main():
    """Run all examples"""
    await example_list_templates()
    await example_get_template()
    # Uncomment to run examples that create agents (requires valid API keys)
    # await example_create_agent_with_template()
    # await example_create_meeting_with_template_agents()
    await example_manual_role_vs_template()


if __name__ == '__main__':
    asyncio.run(main())
