#!/usr/bin/env python3
"""Simple script to test the Web API endpoints"""

import asyncio
import sys
from src.web.api import app, agent_service, meeting_service

async def test_api():
    """Test basic API functionality"""
    print("Testing API endpoints...")
    
    # Test 1: List agents (should be empty initially)
    print("\n1. Testing list_agents...")
    agents = await agent_service.list_agents()
    print(f"   Found {len(agents)} agents")
    
    # Test 2: List templates
    print("\n2. Testing templates...")
    from src.models.role_templates import ROLE_TEMPLATES
    print(f"   Found {len(ROLE_TEMPLATES)} templates")
    for name, template in list(ROLE_TEMPLATES.items())[:3]:
        print(f"   - {name}: {template.name}")
    
    # Test 3: Create a test agent
    print("\n3. Testing create_agent...")
    try:
        from src.models.role_templates import get_role_template
        role = get_role_template('product_manager')
        agent_data = {
            'name': 'Test Agent',
            'role': {
                'name': role.name,
                'description': role.description,
                'system_prompt': role.system_prompt
            },
            'model_config': {
                'provider': 'openai',
                'model_name': 'gpt-4',
                'api_key': 'test-key-12345',
                'parameters': None
            }
        }
        agent = await agent_service.create_agent(agent_data)
        print(f"   Created agent: {agent.name} (ID: {agent.id})")
        
        # Test 4: Get agent
        print("\n4. Testing get_agent...")
        retrieved_agent = await agent_service.get_agent(agent.id)
        print(f"   Retrieved agent: {retrieved_agent.name}")
        
        # Test 5: List meetings (should be empty)
        print("\n5. Testing list_meetings...")
        meetings = await meeting_service.list_meetings()
        print(f"   Found {len(meetings)} meetings")
        
        # Test 6: Create a meeting
        print("\n6. Testing create_meeting...")
        from src.models import MeetingConfig, SpeakingOrder
        config = MeetingConfig(
            max_rounds=3,
            speaking_order=SpeakingOrder.SEQUENTIAL
        )
        meeting = await meeting_service.create_meeting(
            topic="Test Meeting",
            agent_ids=[agent.id],
            config=config
        )
        print(f"   Created meeting: {meeting.topic} (ID: {meeting.id})")
        print(f"   Status: {meeting.status.value}")
        print(f"   Participants: {len(meeting.participants)}")
        
        # Cleanup
        print("\n7. Cleanup...")
        await meeting_service.delete_meeting(meeting.id)
        print("   Deleted meeting")
        await agent_service.delete_agent(agent.id)
        print("   Deleted agent")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_api())
    sys.exit(0 if success else 1)
