"""Agent data models"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Literal, Dict, Any

ModelProvider = Literal['openai', 'anthropic', 'google', 'glm']


@dataclass
class ModelParameters:
    """Parameters for AI model configuration"""
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelParameters':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ModelConfig:
    """Configuration for AI model"""
    provider: ModelProvider
    model_name: str
    api_key: str
    parameters: Optional[ModelParameters] = None

    def __post_init__(self):
        """Validate model config fields"""
        self.validate()

    def validate(self) -> None:
        """Validate model config data"""
        from ..exceptions import ValidationError
        
        if not self.model_name or not self.model_name.strip():
            raise ValidationError("Model name cannot be empty", "model_name")
        
        if not self.api_key or not self.api_key.strip():
            raise ValidationError("API key cannot be empty", "api_key")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'provider': self.provider,
            'model_name': self.model_name,
            'api_key': self.api_key,
        }
        if self.parameters:
            result['parameters'] = self.parameters.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """Create from dictionary"""
        params = data.get('parameters')
        # Only create ModelParameters if params dict is not empty
        if params and isinstance(params, dict) and len(params) > 0:
            params = ModelParameters.from_dict(params)
        else:
            params = None
        return cls(
            provider=data['provider'],
            model_name=data['model_name'],
            api_key=data['api_key'],
            parameters=params
        )


@dataclass
class Role:
    """Role definition for an agent"""
    name: str
    description: str
    system_prompt: str

    def __post_init__(self):
        """Validate role fields"""
        self.validate()

    def validate(self) -> None:
        """Validate role data"""
        from ..exceptions import ValidationError
        
        if not self.name or not self.name.strip():
            raise ValidationError("Role name cannot be empty", "name")
        if len(self.name) > 50:
            raise ValidationError("Role name must be 50 characters or less", "name")
        
        if not self.description or not self.description.strip():
            raise ValidationError("Role description cannot be empty", "description")
        if len(self.description) < 1 or len(self.description) > 2000:
            raise ValidationError("Role description must be between 1 and 2000 characters", "description")
        
        if not self.system_prompt or not self.system_prompt.strip():
            raise ValidationError("Role system_prompt cannot be empty", "system_prompt")
        if len(self.system_prompt) > 2000:
            raise ValidationError("Role system_prompt must be 2000 characters or less", "system_prompt")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Role':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class Agent:
    """AI Agent representation"""
    id: str
    name: str
    role: Role
    model_config: ModelConfig

    def __post_init__(self):
        """Validate agent fields"""
        self.validate()

    def validate(self) -> None:
        """Validate agent data"""
        from ..exceptions import ValidationError
        
        if not self.name or not self.name.strip():
            raise ValidationError("Agent name cannot be empty", "name")
        if len(self.name) > 50:
            raise ValidationError("Agent name must be 50 characters or less", "name")
        
        if not self.id or not self.id.strip():
            raise ValidationError("Agent id cannot be empty", "id")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role.to_dict(),
            'model_config': self.model_config.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            name=data['name'],
            role=Role.from_dict(data['role']),
            model_config=ModelConfig.from_dict(data['model_config']),
        )
