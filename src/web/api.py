"""FastAPI application for AI Agent Meeting System"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
import json

from ..services.agent_service import AgentService
from ..services.meeting_service import MeetingService
from ..storage.file_storage import FileStorageService
from ..models import (
    Agent, Meeting, MeetingConfig, SpeakingOrder, 
    MeetingStatus, ModelProvider
)
from ..models.role_templates import ROLE_TEMPLATES
from ..exceptions import ValidationError, NotFoundError, MeetingStateError

from .schemas import (
    AgentCreateRequest, AgentUpdateRequest, AgentResponse,
    MeetingCreateRequest, MeetingResponse, MessageResponse,
    UserMessageRequest, TemplateResponse
)

# Initialize services
storage = FileStorageService()
agent_service = AgentService(storage)
meeting_service = MeetingService(storage, agent_service)

# Create FastAPI app
app = FastAPI(
    title="AI Agent Meeting API",
    description="API for managing AI agents and meetings",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite and React default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, meeting_id: str):
        await websocket.accept()
        if meeting_id not in self.active_connections:
            self.active_connections[meeting_id] = []
        self.active_connections[meeting_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, meeting_id: str):
        if meeting_id in self.active_connections:
            self.active_connections[meeting_id].remove(websocket)
    
    async def broadcast(self, meeting_id: str, message: dict):
        if meeting_id in self.active_connections:
            for connection in self.active_connections[meeting_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()


# Health check
@app.get("/")
async def root():
    return {"status": "ok", "message": "AI Agent Meeting API"}


# Agent endpoints
@app.get("/api/agents", response_model=List[AgentResponse])
async def list_agents():
    """List all agents"""
    agents = await agent_service.list_agents()
    return [AgentResponse.from_agent(agent) for agent in agents]


@app.post("/api/agents", response_model=AgentResponse)
async def create_agent(request: AgentCreateRequest):
    """Create a new agent"""
    try:
        # If template is provided, use it
        if request.template_name:
            from ..models.role_templates import get_role_template
            role = get_role_template(request.template_name)
            role_dict = {
                'name': role.name,
                'description': role.description,
                'system_prompt': role.system_prompt
            }
        else:
            # Use custom role
            role_dict = {
                'name': request.role_name or '',
                'description': request.role_description or '',
                'system_prompt': request.role_prompt or ''
            }
        
        agent_data = {
            'name': request.name,
            'role': role_dict,
            'model_config': {
                'provider': request.provider,
                'model_name': request.model,
                'api_key': request.api_key,
                'parameters': None
            }
        }
        
        agent = await agent_service.create_agent(agent_data)
        return AgentResponse.from_agent(agent)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent details"""
    try:
        agent = await agent_service.get_agent(agent_id)
        return AgentResponse.from_agent(agent)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")


@app.put("/api/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, request: AgentUpdateRequest):
    """Update agent"""
    try:
        updates = {}
        
        if request.name is not None:
            updates['name'] = request.name
        
        if any([request.role_name, request.role_description, request.role_prompt]):
            # Get current agent to preserve existing values
            current_agent = await agent_service.get_agent(agent_id)
            updates['role'] = {
                'name': request.role_name if request.role_name is not None else current_agent.role.name,
                'description': request.role_description if request.role_description is not None else current_agent.role.description,
                'system_prompt': request.role_prompt if request.role_prompt is not None else current_agent.role.system_prompt
            }
        
        if request.api_key is not None:
            current_agent = await agent_service.get_agent(agent_id)
            updates['model_config'] = {
                'provider': current_agent.model_config.provider,
                'model_name': current_agent.model_config.model_name,
                'api_key': request.api_key,
                'parameters': current_agent.model_config.parameters
            }
        
        agent = await agent_service.update_agent(agent_id, updates)
        return AgentResponse.from_agent(agent)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete agent"""
    try:
        await agent_service.delete_agent(agent_id)
        return {"message": "Agent deleted successfully"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")


@app.post("/api/agents/{agent_id}/test")
async def test_agent(agent_id: str):
    """Test agent connection"""
    try:
        result = await agent_service.test_agent_connection(agent_id)
        return {"success": result, "message": "Connection successful" if result else "Connection failed"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.get("/api/templates", response_model=List[TemplateResponse])
async def list_templates():
    """List available role templates"""
    return [
        TemplateResponse(
            name=name,
            role_name=template.name,
            description=template.description
        )
        for name, template in ROLE_TEMPLATES.items()
    ]


# Meeting endpoints
@app.get("/api/meetings", response_model=List[MeetingResponse])
async def list_meetings():
    """List all meetings"""
    meetings = await meeting_service.list_meetings()
    return [MeetingResponse.from_meeting(meeting) for meeting in meetings]


@app.post("/api/meetings", response_model=MeetingResponse)
async def create_meeting(request: MeetingCreateRequest):
    """Create a new meeting"""
    try:
        config = MeetingConfig(
            max_rounds=request.max_rounds,
            max_message_length=request.max_message_length,
            speaking_order=request.speaking_order
        )
        meeting = await meeting_service.create_meeting(
            topic=request.topic,
            agent_ids=request.agent_ids,
            config=config
        )
        return MeetingResponse.from_meeting(meeting)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/meetings/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(meeting_id: str):
    """Get meeting details"""
    try:
        meeting = await meeting_service.get_meeting(meeting_id)
        return MeetingResponse.from_meeting(meeting)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")


@app.post("/api/meetings/{meeting_id}/start")
async def start_meeting(meeting_id: str):
    """Start or resume meeting"""
    try:
        await meeting_service.start_meeting(meeting_id)
        meeting = await meeting_service.get_meeting(meeting_id)
        await manager.broadcast(meeting_id, {
            "type": "status_change",
            "status": meeting.status.value
        })
        return {"message": "Meeting started"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")
    except MeetingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/meetings/{meeting_id}/pause")
async def pause_meeting(meeting_id: str):
    """Pause meeting"""
    try:
        await meeting_service.pause_meeting(meeting_id)
        meeting = await meeting_service.get_meeting(meeting_id)
        await manager.broadcast(meeting_id, {
            "type": "status_change",
            "status": meeting.status.value
        })
        return {"message": "Meeting paused"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")
    except MeetingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/meetings/{meeting_id}/end")
async def end_meeting(meeting_id: str):
    """End meeting"""
    try:
        await meeting_service.end_meeting(meeting_id)
        meeting = await meeting_service.get_meeting(meeting_id)
        await manager.broadcast(meeting_id, {
            "type": "status_change",
            "status": meeting.status.value
        })
        return {"message": "Meeting ended"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")
    except MeetingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str):
    """Delete meeting"""
    try:
        await meeting_service.delete_meeting(meeting_id)
        return {"message": "Meeting deleted"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")


@app.post("/api/meetings/{meeting_id}/messages")
async def send_message(meeting_id: str, request: UserMessageRequest):
    """Send user message to meeting"""
    try:
        await meeting_service.add_user_message(meeting_id, request.message)
        meeting = await meeting_service.get_meeting(meeting_id)
        latest_message = meeting.messages[-1] if meeting.messages else None
        
        if latest_message:
            await manager.broadcast(meeting_id, {
                "type": "new_message",
                "message": MessageResponse.from_message(latest_message).dict()
            })
        
        return {"message": "Message sent"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except MeetingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/meetings/{meeting_id}/request/{agent_id}")
async def request_agent_response(meeting_id: str, agent_id: str):
    """Request specific agent to respond"""
    import time
    start_time = time.time()
    
    print(f"\n[API] Request agent response: meeting_id={meeting_id}, agent_id={agent_id}")
    
    try:
        print(f"[API] Calling meeting_service.request_agent_response...")
        await meeting_service.request_agent_response(meeting_id, agent_id)
        
        duration = time.time() - start_time
        print(f"[API] ✅ Agent response received in {duration:.2f}s")
        
        meeting = await meeting_service.get_meeting(meeting_id)
        latest_message = meeting.messages[-1] if meeting.messages else None
        
        if latest_message:
            print(f"[API] Broadcasting new message: {latest_message.speaker_name}")
            await manager.broadcast(meeting_id, {
                "type": "new_message",
                "message": MessageResponse.from_message(latest_message).dict()
            })
        
        return {"message": "Agent response received", "duration": f"{duration:.2f}s"}
    except NotFoundError as e:
        duration = time.time() - start_time
        print(f"[API] ❌ NotFoundError after {duration:.2f}s: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except MeetingStateError as e:
        duration = time.time() - start_time
        print(f"[API] ❌ MeetingStateError after {duration:.2f}s: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except APIError as e:
        duration = time.time() - start_time
        print(f"[API] ❌ APIError after {duration:.2f}s: {str(e)}")
        raise HTTPException(status_code=503, detail=f"AI 服务错误: {str(e)}")
    except Exception as e:
        duration = time.time() - start_time
        print(f"[API] ❌ Unexpected error after {duration:.2f}s: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@app.get("/api/meetings/{meeting_id}/export/markdown")
async def export_markdown(meeting_id: str):
    """Export meeting as markdown"""
    try:
        content = await meeting_service.export_meeting_markdown(meeting_id)
        return {"content": content}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")


@app.get("/api/meetings/{meeting_id}/export/json")
async def export_json(meeting_id: str):
    """Export meeting as JSON"""
    try:
        content = await meeting_service.export_meeting_json(meeting_id)
        return {"content": content}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")


# WebSocket endpoint for real-time updates
@app.websocket("/ws/meetings/{meeting_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str):
    """WebSocket connection for real-time meeting updates"""
    await manager.connect(websocket, meeting_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket, meeting_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
