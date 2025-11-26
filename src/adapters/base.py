"""Base adapter implementation with retry logic"""

import asyncio
from typing import List, Optional
from abc import ABC

from ..services.interfaces import IModelAdapter
from ..models import ConversationMessage, ModelParameters, ModelConfig
from ..exceptions import APIError


class BaseModelAdapter(IModelAdapter, ABC):
    """Base class for model adapters with common retry logic"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except APIError as e:
                last_exception = e
                
                # Don't retry on authentication errors
                if e.status_code == 401 or e.status_code == 403:
                    raise
                
                # For rate limits or server errors, retry with backoff
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                
                # Last attempt failed, raise the exception
                raise
            except Exception as e:
                # For unexpected errors, wrap and raise
                raise APIError(
                    f"Unexpected error: {str(e)}",
                    provider=self.config.provider,
                    status_code=None
                ) from e
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
