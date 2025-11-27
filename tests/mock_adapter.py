"""Mock adapter for testing"""

from typing import List, Optional
from src.services.interfaces import IModelAdapter
from src.models import ConversationMessage, ModelParameters


class MockModelAdapter(IModelAdapter):
    """Mock adapter that returns predictable responses for testing"""
    
    def __init__(self, response_template: str = "Mock response"):
        """
        Initialize mock adapter
        
        Args:
            response_template: Template for responses
        """
        self.response_template = response_template
        self.last_messages = None
        self.last_system_prompt = None
        self.last_parameters = None
        self.call_count = 0
    
    async def send_message(
        self,
        messages: List[ConversationMessage],
        system_prompt: str,
        parameters: Optional[ModelParameters] = None
    ) -> str:
        """Send message and return mock response"""
        # Store the call parameters for verification
        self.last_messages = messages
        self.last_system_prompt = system_prompt
        self.last_parameters = parameters
        self.call_count += 1
        
        # Return a response that includes context for verification
        return f"{self.response_template} (call {self.call_count})"
    
    async def send_message_stream(
        self,
        messages: List[ConversationMessage],
        system_prompt: str,
        parameters: Optional[ModelParameters] = None
    ):
        """Send message and return mock streaming response"""
        # Store the call parameters for verification
        self.last_messages = messages
        self.last_system_prompt = system_prompt
        self.last_parameters = parameters
        self.call_count += 1
        
        # Yield response in chunks
        response = f"{self.response_template} (call {self.call_count})"
        for char in response:
            yield {"type": "content", "content": char}
    
    async def test_connection(self) -> bool:
        """Test connection (always succeeds for mock)"""
        return True
