"""Agent management CLI commands"""

import click
import asyncio
from typing import Optional

from .main import pass_context, CLIContext
from ..exceptions import ValidationError, NotFoundError


@click.group()
def agent():
    """Manage AI agents"""
    pass


@agent.command('create')
@click.option('--name', prompt='Agent name', help='Name of the agent')
@click.option('--provider', 
              type=click.Choice(['openai', 'anthropic', 'google', 'glm']),
              prompt='Model provider',
              help='AI model provider')
@click.option('--model', prompt='Model name', help='Model name (e.g., gpt-4, claude-3)')
@click.option('--api-key', prompt='API key', hide_input=True, help='API key for the model provider')
@click.option('--template', help='Role template name (optional)')
@click.option('--role-name', help='Custom role name (if not using template)')
@click.option('--role-description', help='Custom role description (if not using template)')
@click.option('--role-prompt', help='Custom system prompt (if not using template)')
@pass_context
def create_agent(ctx: CLIContext, name: str, provider: str, model: str, api_key: str,
                 template: Optional[str], role_name: Optional[str], 
                 role_description: Optional[str], role_prompt: Optional[str]):
    """Create a new AI agent"""
    
    async def _create():
        try:
            # Determine role configuration
            if template:
                # Use template
                agent = await ctx.agent_service.create_agent_from_template(
                    name=name,
                    template_name=template,
                    model_config={
                        'provider': provider,
                        'model_name': model,
                        'api_key': api_key
                    }
                )
            else:
                # Use custom role or prompt for details
                if not role_name:
                    role_name_input = click.prompt('Role name')
                else:
                    role_name_input = role_name
                
                if not role_description:
                    role_description_input = click.prompt('Role description')
                else:
                    role_description_input = role_description
                
                if not role_prompt:
                    role_prompt_input = click.prompt('System prompt')
                else:
                    role_prompt_input = role_prompt
                
                agent_data = {
                    'name': name,
                    'role': {
                        'name': role_name_input,
                        'description': role_description_input,
                        'system_prompt': role_prompt_input
                    },
                    'model_config': {
                        'provider': provider,
                        'model_name': model,
                        'api_key': api_key
                    }
                }
                agent = await ctx.agent_service.create_agent(agent_data)
            
            click.echo(click.style(f'\n✓ Agent created successfully!', fg='green'))
            click.echo(f'  ID: {agent.id}')
            click.echo(f'  Name: {agent.name}')
            click.echo(f'  Role: {agent.role.name}')
            click.echo(f'  Model: {agent.model_config.provider}/{agent.model_config.model_name}')
            
        except ValidationError as e:
            click.echo(click.style(f'✗ Validation error: {str(e)}', fg='red'), err=True)
        except KeyError as e:
            click.echo(click.style(f'✗ Invalid template: {str(e)}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_create())


@agent.command('list')
@pass_context
def list_agents(ctx: CLIContext):
    """List all agents"""
    
    async def _list():
        try:
            agents = await ctx.agent_service.list_agents()
            
            if not agents:
                click.echo('No agents found.')
                return
            
            click.echo(f'\nFound {len(agents)} agent(s):\n')
            for agent in agents:
                click.echo(f'  • {agent.name}')
                click.echo(f'    ID: {agent.id}')
                click.echo(f'    Role: {agent.role.name}')
                click.echo(f'    Model: {agent.model_config.provider}/{agent.model_config.model_name}')
                click.echo()
                
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_list())


@agent.command('show')
@click.argument('agent_id')
@pass_context
def show_agent(ctx: CLIContext, agent_id: str):
    """Show detailed information about an agent"""
    
    async def _show():
        try:
            agent = await ctx.agent_service.get_agent(agent_id)
            
            click.echo(f'\nAgent Details:')
            click.echo(f'  ID: {agent.id}')
            click.echo(f'  Name: {agent.name}')
            click.echo(f'\nRole:')
            click.echo(f'  Name: {agent.role.name}')
            click.echo(f'  Description: {agent.role.description}')
            click.echo(f'  System Prompt: {agent.role.system_prompt[:100]}...' if len(agent.role.system_prompt) > 100 else f'  System Prompt: {agent.role.system_prompt}')
            click.echo(f'\nModel Configuration:')
            click.echo(f'  Provider: {agent.model_config.provider}')
            click.echo(f'  Model: {agent.model_config.model_name}')
            click.echo(f'  API Key: {"*" * 8}{agent.model_config.api_key[-4:]}')
            
            if agent.model_config.parameters:
                click.echo(f'\nParameters:')
                if agent.model_config.parameters.temperature is not None:
                    click.echo(f'  Temperature: {agent.model_config.parameters.temperature}')
                if agent.model_config.parameters.max_tokens is not None:
                    click.echo(f'  Max Tokens: {agent.model_config.parameters.max_tokens}')
                if agent.model_config.parameters.top_p is not None:
                    click.echo(f'  Top P: {agent.model_config.parameters.top_p}')
            
        except NotFoundError:
            click.echo(click.style(f'✗ Agent not found: {agent_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_show())


@agent.command('update')
@click.argument('agent_id')
@click.option('--name', help='New name for the agent')
@click.option('--model', help='New model name')
@click.option('--api-key', help='New API key')
@pass_context
def update_agent(ctx: CLIContext, agent_id: str, name: Optional[str], 
                 model: Optional[str], api_key: Optional[str]):
    """Update an existing agent"""
    
    async def _update():
        try:
            updates = {}
            
            if name:
                updates['name'] = name
            
            if model or api_key:
                # Load current agent to get existing config
                agent = await ctx.agent_service.get_agent(agent_id)
                model_config = {
                    'provider': agent.model_config.provider,
                    'model_name': model if model else agent.model_config.model_name,
                    'api_key': api_key if api_key else agent.model_config.api_key
                }
                if agent.model_config.parameters:
                    model_config['parameters'] = agent.model_config.parameters.to_dict()
                updates['model_config'] = model_config
            
            if not updates:
                click.echo('No updates specified. Use --name, --model, or --api-key options.')
                return
            
            agent = await ctx.agent_service.update_agent(agent_id, updates)
            
            click.echo(click.style(f'\n✓ Agent updated successfully!', fg='green'))
            click.echo(f'  ID: {agent.id}')
            click.echo(f'  Name: {agent.name}')
            click.echo(f'  Model: {agent.model_config.provider}/{agent.model_config.model_name}')
            
        except NotFoundError:
            click.echo(click.style(f'✗ Agent not found: {agent_id}', fg='red'), err=True)
        except ValidationError as e:
            click.echo(click.style(f'✗ Validation error: {str(e)}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_update())


@agent.command('delete')
@click.argument('agent_id')
@click.confirmation_option(prompt='Are you sure you want to delete this agent?')
@pass_context
def delete_agent(ctx: CLIContext, agent_id: str):
    """Delete an agent"""
    
    async def _delete():
        try:
            await ctx.agent_service.delete_agent(agent_id)
            click.echo(click.style(f'✓ Agent deleted successfully', fg='green'))
            
        except NotFoundError:
            click.echo(click.style(f'✗ Agent not found: {agent_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_delete())


@agent.command('test')
@click.argument('agent_id')
@pass_context
def test_agent(ctx: CLIContext, agent_id: str):
    """Test agent connection to AI model"""
    
    async def _test():
        try:
            click.echo('Testing connection...')
            success = await ctx.agent_service.test_agent_connection(agent_id)
            
            if success:
                click.echo(click.style('✓ Connection successful!', fg='green'))
            else:
                click.echo(click.style('✗ Connection failed', fg='red'), err=True)
                
        except NotFoundError:
            click.echo(click.style(f'✗ Agent not found: {agent_id}', fg='red'), err=True)
        except Exception as e:
            click.echo(click.style(f'✗ Error: {str(e)}', fg='red'), err=True)
    
    asyncio.run(_test())


@agent.command('templates')
@pass_context
def list_templates(ctx: CLIContext):
    """List available role templates"""
    
    templates = ctx.agent_service.get_available_role_templates()
    
    click.echo(f'\nAvailable role templates ({len(templates)}):\n')
    
    from ..models.role_templates import get_role_template_info
    
    for template_name in templates:
        info = get_role_template_info(template_name)
        click.echo(f'  • {template_name}')
        click.echo(f'    {info["name"]}: {info["description"]}')
        click.echo()
