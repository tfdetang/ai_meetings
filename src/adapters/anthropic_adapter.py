"""Anthropic model adapter"""

import aiohttp
from typing import List, Optional

from .base import BaseModelAdapter
from ..models import ConversationMessage, ModelParameters, ModelConfig
from ..exceptions import APIError


class AnthropicAdapter(BaseModelAdapter):
    """Adapter for Anthropic API (Claude)"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.api_base = "https://api.anthropic.com/v1"
        self.api_version = "2023-06-01"
    
    async def send_message(
        self,
        messages: List[ConversationMessage],
        system_prompt: str,
        parameters: Optional[ModelParameters] = None
    ) -> str:
        """Send message to Anthropic API and get response"""
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
        # Anthropic uses system parameter separately from messages
        # Messages should only contain user and assistant roles
        api_messages = []
        
        for msg in messages:
            # Skip system messages as they go in the system parameter
            if msg.role != "system":
                api_messages.append(msg.to_dict())
        
        # Build request payload
        payload = {
            "model": self.config.model_name,
            "messages": api_messages,
            "system": system_prompt,
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
        else:
            # Anthropic requires max_tokens to be set
            payload["max_tokens"] = 1024
        
        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": self.api_version,
            "Content-Type": "application/json",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/messages",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Anthropic returns content as a list of content blocks
                        return data["content"][0]["text"]
                    else:
                        error_text = await response.text()
                        raise APIError(
                            f"Anthropic API error: {error_text}",
                            provider="anthropic",
                            status_code=response.status
                        )
        except aiohttp.ClientError as e:
            raise APIError(
                f"Network error calling Anthropic API: {str(e)}",
                provider="anthropic",
                status_code=None
            ) from e
    
    async def test_connection(self) -> bool:
        """Test connection to Anthropic API"""
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
