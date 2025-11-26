"""OpenAI model adapter"""

import aiohttp
from typing import List, Optional

from .base import BaseModelAdapter
from ..models import ConversationMessage, ModelParameters, ModelConfig
from ..exceptions import APIError


class OpenAIAdapter(BaseModelAdapter):
    """Adapter for OpenAI API"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.api_base = "https://api.openai.com/v1"
    
    async def send_message(
        self,
        messages: List[ConversationMessage],
        system_prompt: str,
        parameters: Optional[ModelParameters] = None
    ) -> str:
        """Send message to OpenAI API and get response"""
        return await self._retry_with_backoff(
            self._send_message_impl,
            messages,
            system_prompt,
            parameters
        )
    
    async def _send_message_impl(
        self,
        messages: List[ConversationMessage],
        system_prompt: str,
        parameters: Optional[ModelParameters] = None
    ) -> str:
        """Implementation of send_message with actual API call"""
        # Build messages list with system prompt
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend([msg.to_dict() for msg in messages])
        
        # Build request payload
        payload = {
            "model": self.config.model_name,
            "messages": api_messages,
        }
        
        # Add optional parameters
        params = parameters or self.config.parameters
        if params:
            if params.temperature is not None:
                payload["temperature"] = params.temperature
            if params.max_tokens is not None:
                payload["max_tokens"] = params.max_tokens
            if params.top_p is not None:
                payload["top_p"] = params.top_p
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        raise APIError(
                            f"OpenAI API error: {error_text}",
                            provider="openai",
                            status_code=response.status
                        )
        except aiohttp.ClientError as e:
            raise APIError(
                f"Network error calling OpenAI API: {str(e)}",
                provider="openai",
                status_code=None
            ) from e
    
    async def test_connection(self) -> bool:
        """Test connection to OpenAI API"""
        try:
            # Send a minimal test message
            test_messages = [
                ConversationMessage(role="user", content="Hello")
            ]
            await self.send_message(
                messages=test_messages,
                system_prompt="You are a helpful assistant.",
                parameters=ModelParameters(max_tokens=5)
            )
            return True
        except APIError:
            return False
