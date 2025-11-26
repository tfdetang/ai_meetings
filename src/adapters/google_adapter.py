"""Google AI model adapter"""

import aiohttp
from typing import List, Optional

from .base import BaseModelAdapter
from ..models import ConversationMessage, ModelParameters, ModelConfig
from ..exceptions import APIError


class GoogleAdapter(BaseModelAdapter):
    """Adapter for Google AI API (Gemini)"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.api_base = "https://generativelanguage.googleapis.com/v1beta"
    
    async def send_message(
        self,
        messages: List[ConversationMessage],
        system_prompt: str,
        parameters: Optional[ModelParameters] = None
    ) -> str:
        """Send message to Google AI API and get response"""
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
        # Google uses a different message format
        # System prompt goes into systemInstruction
        # Messages are converted to parts with role mapping
        contents = []
        
        for msg in messages:
            # Map roles: assistant -> model, user -> user
            role = "model" if msg.role == "assistant" else "user"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        
        # Build request payload
        payload = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            }
        }
        
        # Add generation config if parameters provided
        params = parameters or self.config.parameters
        if params:
            generation_config = {}
            if params.temperature is not None:
                generation_config["temperature"] = params.temperature
            if params.max_tokens is not None:
                generation_config["maxOutputTokens"] = params.max_tokens
            if params.top_p is not None:
                generation_config["topP"] = params.top_p
            
            if generation_config:
                payload["generationConfig"] = generation_config
        
        # API key is passed as query parameter
        url = f"{self.api_base}/models/{self.config.model_name}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    params={"key": self.config.api_key},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        error_text = await response.text()
                        raise APIError(
                            f"Google AI API error: {error_text}",
                            provider="google",
                            status_code=response.status
                        )
        except aiohttp.ClientError as e:
            raise APIError(
                f"Network error calling Google AI API: {str(e)}",
                provider="google",
                status_code=None
            ) from e
    
    async def test_connection(self) -> bool:
        """Test connection to Google AI API"""
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
