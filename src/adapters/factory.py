"""Factory for creating model adapters"""

from ..models import ModelConfig
from ..services.interfaces import IModelAdapter


class ModelAdapterFactory:
    """Factory for creating model adapters based on provider"""
    
    @staticmethod
    def create(config: ModelConfig) -> IModelAdapter:
        """Create appropriate model adapter based on configuration
        
        Args:
            config: Model configuration
            
        Returns:
            IModelAdapter instance for the specified provider
            
        Raises:
            ValueError: If provider is not supported
        """
        if config.provider == 'openai':
            from .openai_adapter import OpenAIAdapter
            return OpenAIAdapter(config)
        elif config.provider == 'anthropic':
            from .anthropic_adapter import AnthropicAdapter
            return AnthropicAdapter(config)
        elif config.provider == 'google':
            from .google_adapter import GoogleAdapter
            return GoogleAdapter(config)
        elif config.provider == 'glm':
            from .glm_adapter import GLMAdapter
            return GLMAdapter(config)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
