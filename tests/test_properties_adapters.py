"""Property-based tests for model adapters"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp

from src.adapters import ModelAdapterFactory
from src.models import ModelConfig, ModelParameters, ConversationMessage
from src.exceptions import APIError


# Strategies for generating test data
model_config_strategy = st.builds(
    ModelConfig,
    provider=st.sampled_from(['openai', 'anthropic', 'google', 'glm']),
    model_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    api_key=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    parameters=st.none()
)

conversation_message_strategy = st.builds(
    ConversationMessage,
    role=st.sampled_from(['user', 'assistant']),
    content=st.text(min_size=1, max_size=1000, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip())
)


# Feature: ai-agent-meeting, Property 7: API 错误处理
# Validates: Requirements 2.4
@given(
    config=model_config_strategy,
    messages=st.lists(conversation_message_strategy, min_size=1, max_size=5),
    system_prompt=st.text(min_size=1, max_size=500, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    error_status=st.sampled_from([400, 500, 502, 503])
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_api_error_handling(config, messages, system_prompt, error_status):
    """
    Property 7: API Error Handling
    For any simulated API failure scenario, the system should return a clear error message
    rather than crashing.
    """
    adapter = ModelAdapterFactory.create(config)
    
    # Mock the HTTP response to simulate API error
    mock_response = AsyncMock()
    mock_response.status = error_status
    mock_response.text = AsyncMock(return_value=f"API Error: Status {error_status}")
    
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.post = MagicMock()
    mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
    mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Patch aiohttp.ClientSession to return our mock
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # The adapter should raise APIError, not crash
        with pytest.raises(APIError) as exc_info:
            await adapter.send_message(
                messages=messages,
                system_prompt=system_prompt,
                parameters=None
            )
        
        # Verify we got a clear error message
        assert exc_info.value.provider == config.provider
        assert exc_info.value.status_code == error_status
        assert isinstance(str(exc_info.value), str)
        assert len(str(exc_info.value)) > 0


# Feature: ai-agent-meeting, Property 7: API 错误处理 (Authentication errors)
# Validates: Requirements 2.4
@given(
    config=model_config_strategy,
    messages=st.lists(conversation_message_strategy, min_size=1, max_size=5),
    system_prompt=st.text(min_size=1, max_size=500, alphabet=st.characters(blacklist_categories=('Cs',))).filter(lambda x: x.strip()),
    auth_error_status=st.sampled_from([401, 403])
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_api_error_handling_auth_no_retry(config, messages, system_prompt, auth_error_status):
    """
    Property 7: API Error Handling (Authentication)
    For authentication errors (401, 403), the system should fail immediately without retrying.
    """
    adapter = ModelAdapterFactory.create(config)
    
    # Mock the HTTP response to simulate authentication error
    mock_response = AsyncMock()
    mock_response.status = auth_error_status
    mock_response.text = AsyncMock(return_value=f"Authentication Error: Status {auth_error_status}")
    
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.post = MagicMock()
    mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
    mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
    
    call_count = 0
    
    def track_calls(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return mock_session.post.return_value
    
    mock_session.post.side_effect = track_calls
    
    # Patch aiohttp.ClientSession to return our mock
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # The adapter should raise APIError immediately
        with pytest.raises(APIError) as exc_info:
            await adapter.send_message(
                messages=messages,
                system_prompt=system_prompt,
                parameters=None
            )
        
        # Verify authentication error was raised
        assert exc_info.value.status_code == auth_error_status
        
        # Verify it didn't retry (should only call once)
        assert call_count == 1


# Feature: ai-agent-meeting, Property 8: 连接测试响应
# Validates: Requirements 2.5
@given(
    config=model_config_strategy,
    success=st.booleans()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_connection_test_response(config, success):
    """
    Property 8: Connection Test Response
    For any agent configuration, the test connection operation should return a boolean value
    (success or failure).
    """
    adapter = ModelAdapterFactory.create(config)
    
    # Mock the HTTP response
    mock_response = AsyncMock()
    if success:
        mock_response.status = 200
        # Mock different response formats for different providers
        if config.provider == 'openai' or config.provider == 'glm':
            mock_response.json = AsyncMock(return_value={
                "choices": [{"message": {"content": "Hello"}}]
            })
        elif config.provider == 'anthropic':
            mock_response.json = AsyncMock(return_value={
                "content": [{"text": "Hello"}]
            })
        elif config.provider == 'google':
            mock_response.json = AsyncMock(return_value={
                "candidates": [{"content": {"parts": [{"text": "Hello"}]}}]
            })
    else:
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Server Error")
    
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.post = MagicMock()
    mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
    mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Patch aiohttp.ClientSession to return our mock
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await adapter.test_connection()
        
        # Verify result is a boolean
        assert isinstance(result, bool)
        
        # Verify result matches expected success/failure
        assert result == success
