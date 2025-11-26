"""GLM (智谱AI) model adapter"""

import asyncio
import aiohttp
import json
from typing import List, Optional, AsyncIterator

from .base import BaseModelAdapter
from ..models import ConversationMessage, ModelParameters, ModelConfig
from ..exceptions import APIError


class GLMAdapter(BaseModelAdapter):
    """Adapter for GLM API (智谱AI)
    
    Supports both streaming and non-streaming responses.
    """
    
    def __init__(self, config: ModelConfig, stream: bool = False):
        """Initialize GLM adapter
        
        Args:
            config: Model configuration
            stream: Whether to use streaming mode (default: False)
        """
        super().__init__(config)
        self.api_base = "https://open.bigmodel.cn/api/paas/v4"
        self.stream = stream
    
    async def send_message(
        self,
        messages: List[ConversationMessage],
        system_prompt: str,
        parameters: Optional[ModelParameters] = None
    ) -> str:
        """Send message to GLM API and get response"""
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
        """Implementation of send_message with actual API call
        
        Supports both streaming and non-streaming modes based on self.stream.
        """
        # Build messages list with system prompt
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend([msg.to_dict() for msg in messages])
        
        # Build request payload
        payload = {
            "model": self.config.model_name,
            "messages": api_messages,
            "stream": self.stream,
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
                    timeout=aiohttp.ClientTimeout(total=300)  # Increased to 300 seconds (5 minutes)
                ) as response:
                    if response.status == 200:
                        if self.stream:
                            # Handle streaming response
                            return await self._handle_streaming_response(response)
                        else:
                            # Handle non-streaming response
                            data = await response.json()
                            return data["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        raise APIError(
                            f"GLM API error: {error_text}",
                            provider="glm",
                            status_code=response.status
                        )
        except asyncio.TimeoutError as e:
            raise APIError(
                f"GLM API request timed out after 300 seconds. Please try again.",
                provider="glm",
                status_code=None
            ) from e
        except aiohttp.ClientError as e:
            raise APIError(
                f"Network error calling GLM API: {str(e)}",
                provider="glm",
                status_code=None
            ) from e
    
    async def _handle_streaming_response(self, response: aiohttp.ClientResponse) -> str:
        """Handle streaming response from GLM API
        
        Args:
            response: The aiohttp response object
            
        Returns:
            Complete message content assembled from stream chunks
        """
        content_parts = []
        
        async for line in response.content:
            line = line.decode('utf-8').strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # GLM streaming format: "data: {json}"
            if line.startswith("data: "):
                data_str = line[6:]  # Remove "data: " prefix
                
                # Check for stream end marker
                if data_str == "[DONE]":
                    break
                
                try:
                    data = json.loads(data_str)
                    # Extract content delta from the chunk
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        
                        # GLM-4.6 supports reasoning
                        # Collect both reasoning_content and content
                        if "reasoning_content" in delta:
                            content_parts.append(delta["reasoning_content"])
                        if "content" in delta:
                            content_parts.append(delta["content"])
                except json.JSONDecodeError:
                    # Skip malformed JSON chunks
                    continue
        
        return "".join(content_parts)
    
    async def send_message_stream(
        self,
        messages: List[ConversationMessage],
        system_prompt: str,
        parameters: Optional[ModelParameters] = None
    ):
        """Send message to GLM API and get streaming response
        
        Yields:
            Text chunks as they arrive from the API
        """
        print(f"[GLMAdapter] send_message_stream called")
        
        # Build messages list with system prompt
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend([msg.to_dict() for msg in messages])
        
        # Build request payload with streaming enabled
        payload = {
            "model": self.config.model_name,
            "messages": api_messages,
            "stream": True,
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
            "Authorization": f"Bearer {self.config.api_key[:10]}...",  # Don't log full key
            "Content-Type": "application/json",
        }
        
        print(f"[GLMAdapter] Sending streaming request to GLM API...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    print(f"[GLMAdapter] Response status: {response.status}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[GLMAdapter] ❌ API error: {error_text}")
                        raise APIError(
                            f"GLM API error: {error_text}",
                            provider="glm",
                            status_code=response.status
                        )
                    
                    print(f"[GLMAdapter] Starting to stream response...")
                    chunk_count = 0
                    
                    # Stream response chunks
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        # Skip empty lines
                        if not line:
                            continue
                        
                        # GLM streaming format: "data: {json}"
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            # Check for stream end marker
                            if data_str == "[DONE]":
                                print(f"[GLMAdapter] Stream ended, total chunks: {chunk_count}")
                                break
                            
                            try:
                                data = json.loads(data_str)
                                # Extract content delta from the chunk
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    
                                    # GLM-4.6 supports reasoning (思考链)
                                    # It returns reasoning_content first, then content
                                    # We yield them separately with type markers
                                    
                                    # First check for reasoning content (思考过程)
                                    reasoning = delta.get("reasoning_content")
                                    if reasoning:
                                        chunk_count += 1
                                        print(f"[GLMAdapter] Reasoning chunk {chunk_count}: {reasoning[:50]}...")
                                        yield {"type": "reasoning", "content": reasoning}
                                    
                                    # Then check for final content (最终答案)
                                    content = delta.get("content")
                                    if content:
                                        chunk_count += 1
                                        print(f"[GLMAdapter] Content chunk {chunk_count}: {content[:50]}...")
                                        yield {"type": "content", "content": content}
                                        
                            except json.JSONDecodeError as e:
                                print(f"[GLMAdapter] ⚠️ JSON decode error: {e}")
                                # Skip malformed JSON chunks
                                continue
                    
                    print(f"[GLMAdapter] ✅ Streaming complete, {chunk_count} chunks sent")
                                
        except asyncio.TimeoutError as e:
            raise APIError(
                f"GLM API request timed out after 300 seconds",
                provider="glm",
                status_code=None
            ) from e
        except aiohttp.ClientError as e:
            raise APIError(
                f"Network error calling GLM API: {str(e)}",
                provider="glm",
                status_code=None
            ) from e
    
    async def test_connection(self) -> bool:
        """Test connection to GLM API"""
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
