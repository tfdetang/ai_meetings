"""FastAPI application for AI Agent Meeting System"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime
import json
import uuid
import asyncio

from ..services.agent_service import AgentService
from ..services.meeting_service import MeetingService
from ..storage.file_storage import FileStorageService
from ..models import (
    Agent, Meeting, MeetingConfig, SpeakingOrder, 
    MeetingStatus, ModelProvider, DiscussionStyle, SpeakingLength
)
from ..models.role_templates import ROLE_TEMPLATES
from ..exceptions import ValidationError, NotFoundError, MeetingStateError, PermissionError, AgendaError, APIError

from .schemas import (
    AgentCreateRequest, AgentUpdateRequest, AgentResponse,
    MeetingCreateRequest, MeetingResponse, MessageResponse,
    UserMessageRequest, TemplateResponse, AgendaItemRequest,
    AgendaItemResponse, MeetingConfigUpdateRequest,
    MinutesGenerateRequest, MinutesUpdateRequest, MeetingMinutesResponse
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
        # Build agenda items if provided
        agenda = None
        if request.agenda:
            from ..models import AgendaItem
            agenda = []
            for item_req in request.agenda:
                agenda_item = AgendaItem(
                    id=str(uuid.uuid4()),
                    title=item_req.title,
                    description=item_req.description,
                    completed=False,
                    created_at=datetime.now()
                )
                agenda.append(agenda_item)
        
        config = MeetingConfig(
            max_rounds=request.max_rounds,
            max_message_length=request.max_message_length,
            speaking_order=request.speaking_order,
            discussion_style=request.discussion_style if request.discussion_style else DiscussionStyle.FORMAL,
            speaking_length_preferences=request.speaking_length_preferences
        )
        meeting = await meeting_service.create_meeting(
            topic=request.topic,
            agent_ids=request.agent_ids,
            config=config,
            moderator_id=request.moderator_id,
            moderator_type=request.moderator_type,
            agenda=agenda
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
async def end_meeting(meeting_id: str, auto_generate_minutes: bool = True):
    """End meeting and optionally auto-generate minutes"""
    try:
        await meeting_service.end_meeting(meeting_id, auto_generate_minutes)
        meeting = await meeting_service.get_meeting(meeting_id)
        
        # Broadcast status change
        await manager.broadcast(meeting_id, {
            "type": "status_change",
            "status": meeting.status.value
        })
        
        # If minutes were auto-generated, broadcast that too
        if auto_generate_minutes and meeting.current_minutes:
            await manager.broadcast(meeting_id, {
                "type": "minutes_generated",
                "minutes": {
                    "id": meeting.current_minutes.id,
                    "summary": meeting.current_minutes.summary,
                    "created_at": meeting.current_minutes.created_at.isoformat()
                }
            })
        
        return {
            "message": "Meeting ended",
            "minutes_generated": auto_generate_minutes and meeting.current_minutes is not None
        }
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


# Agenda management endpoints
@app.post("/api/meetings/{meeting_id}/agenda")
async def add_agenda_item(meeting_id: str, request: AgendaItemRequest, requester_id: str = "user", requester_type: str = "user"):
    """Add agenda item to meeting (moderator only)"""
    try:
        from ..models import AgendaItem
        
        agenda_item = AgendaItem(
            id=str(uuid.uuid4()),
            title=request.title,
            description=request.description,
            completed=False,
            created_at=datetime.now()
        )
        
        await meeting_service.add_agenda_item(meeting_id, agenda_item, requester_id, requester_type)
        return {"message": "Agenda item added", "item": AgendaItemResponse.from_agenda_item(agenda_item).dict()}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/meetings/{meeting_id}/agenda/{item_id}")
async def remove_agenda_item(meeting_id: str, item_id: str, requester_id: str = "user", requester_type: str = "user"):
    """Remove agenda item from meeting (moderator only)"""
    try:
        await meeting_service.remove_agenda_item(meeting_id, item_id, requester_id, requester_type)
        return {"message": "Agenda item removed"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except AgendaError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.patch("/api/meetings/{meeting_id}/agenda/{item_id}")
async def mark_agenda_completed(meeting_id: str, item_id: str, requester_id: str = "user", requester_type: str = "user"):
    """Mark agenda item as completed (moderator only)"""
    try:
        await meeting_service.mark_agenda_completed(meeting_id, item_id, requester_id, requester_type)
        return {"message": "Agenda item marked as completed"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except AgendaError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Meeting configuration endpoint
@app.patch("/api/meetings/{meeting_id}/config")
async def update_meeting_config(meeting_id: str, request: MeetingConfigUpdateRequest):
    """Update meeting configuration"""
    try:
        # Get current meeting to preserve existing config
        meeting = await meeting_service.get_meeting(meeting_id)
        
        # Build updated config
        config = MeetingConfig(
            max_rounds=request.max_rounds if request.max_rounds is not None else meeting.config.max_rounds,
            max_message_length=request.max_message_length if request.max_message_length is not None else meeting.config.max_message_length,
            speaking_order=request.speaking_order if request.speaking_order is not None else meeting.config.speaking_order,
            discussion_style=request.discussion_style if request.discussion_style is not None else meeting.config.discussion_style,
            speaking_length_preferences=request.speaking_length_preferences if request.speaking_length_preferences is not None else meeting.config.speaking_length_preferences
        )
        
        await meeting_service.update_meeting_config(meeting_id, config)
        return {"message": "Meeting configuration updated"}
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
            message_response = MessageResponse.from_message(latest_message)
            await manager.broadcast(meeting_id, {
                "type": "new_message",
                "message": json.loads(message_response.json())
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
            message_response = MessageResponse.from_message(latest_message)
            await manager.broadcast(meeting_id, {
                "type": "new_message",
                "message": json.loads(message_response.json())
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


@app.get("/api/meetings/{meeting_id}/request-stream/{agent_id}")
async def request_agent_response_stream(meeting_id: str, agent_id: str):
    """Request specific agent to respond with streaming"""
    
    async def generate():
        try:
            print(f"[API] Starting streaming response for meeting={meeting_id}, agent={agent_id}")
            
            # Stream the response
            async for chunk in meeting_service.request_agent_response_stream(meeting_id, agent_id):
                if isinstance(chunk, dict) and chunk.get("type") == "complete":
                    # Send completion message with full message data
                    message = chunk["message"]
                    print(f"[API] Streaming complete, sending final message")
                    message_response = MessageResponse.from_message(message)
                    yield f"data: {json.dumps({'type': 'complete', 'message': json.loads(message_response.json())})}\n\n"
                    
                    # Broadcast the complete message via WebSocket
                    await manager.broadcast(meeting_id, {
                        "type": "new_message",
                        "message": json.loads(message_response.json())
                    })
                elif isinstance(chunk, dict):
                    # Send typed chunk (reasoning or content)
                    chunk_type = chunk.get("type")
                    chunk_content = chunk.get("content", "")
                    print(f"[API] Streaming {chunk_type} chunk: {chunk_content[:50]}...")
                    yield f"data: {json.dumps(chunk)}\n\n"
                else:
                    # Legacy string chunk
                    print(f"[API] Streaming chunk: {chunk[:50]}...")
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                    
        except NotFoundError as e:
            print(f"[API] ❌ NotFoundError in streaming: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        except MeetingStateError as e:
            print(f"[API] ❌ MeetingStateError in streaming: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        except APIError as e:
            print(f"[API] ❌ APIError in streaming: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'error': 'AI 服务错误: ' + str(e)})}\n\n"
        except Exception as e:
            print(f"[API] ❌ Unexpected error in streaming: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/meetings/{meeting_id}/request-with-auto-response/{agent_id}")
async def request_agent_with_auto_response(meeting_id: str, agent_id: str, max_depth: int = 5):
    """Request agent response and automatically trigger mentioned agents (with depth limit)"""
    import time
    
    try:
        processed_agents = set()
        depth = 0
        current_agent_id = agent_id
        
        while depth < max_depth:
            # Avoid infinite loops
            if current_agent_id in processed_agents:
                break
            
            processed_agents.add(current_agent_id)
            
            # Request response from current agent
            await meeting_service.request_agent_response(meeting_id, current_agent_id)
            
            # Get the latest message
            meeting = await meeting_service.get_meeting(meeting_id)
            latest_message = meeting.messages[-1] if meeting.messages else None
            
            if latest_message:
                # Broadcast the message
                message_response = MessageResponse.from_message(latest_message)
                await manager.broadcast(meeting_id, {
                    "type": "new_message",
                    "message": json.loads(message_response.json())
                })
                
                # Check for mentions
                mentioned_agent_ids = meeting_service.get_mentioned_agents(latest_message)
                
                if mentioned_agent_ids:
                    # Get the first mentioned agent that hasn't been processed
                    next_agent_id = None
                    for mentioned_id in mentioned_agent_ids:
                        if mentioned_id not in processed_agents:
                            next_agent_id = mentioned_id
                            break
                    
                    if next_agent_id:
                        current_agent_id = next_agent_id
                        depth += 1
                        # Small delay to avoid overwhelming the system
                        await asyncio.sleep(0.5)
                        continue
            
            # No more mentions or all mentioned agents processed
            break
        
        return {
            "message": "Auto-response chain completed",
            "agents_responded": list(processed_agents),
            "depth": depth
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MeetingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except APIError as e:
        raise HTTPException(status_code=503, detail=f"AI 服务错误: {str(e)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# Meeting minutes endpoints
@app.post("/api/meetings/{meeting_id}/minutes", response_model=MeetingMinutesResponse)
async def generate_minutes(meeting_id: str, request: MinutesGenerateRequest = MinutesGenerateRequest()):
    """Generate meeting minutes using AI"""
    try:
        minutes = await meeting_service.generate_minutes(meeting_id, request.generator_id)
        return MeetingMinutesResponse.from_minutes(minutes)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/meetings/{meeting_id}/minutes", response_model=MeetingMinutesResponse)
async def get_current_minutes(meeting_id: str):
    """Get current meeting minutes"""
    try:
        meeting = await meeting_service.get_meeting(meeting_id)
        if meeting.current_minutes is None:
            raise HTTPException(status_code=404, detail="No minutes available for this meeting")
        return MeetingMinutesResponse.from_minutes(meeting.current_minutes)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")


@app.put("/api/meetings/{meeting_id}/minutes", response_model=MeetingMinutesResponse)
async def update_minutes(meeting_id: str, request: MinutesUpdateRequest):
    """Update meeting minutes manually"""
    try:
        minutes = await meeting_service.update_minutes(meeting_id, request.content, request.editor_id)
        return MeetingMinutesResponse.from_minutes(minutes)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/meetings/{meeting_id}/minutes/history", response_model=List[MeetingMinutesResponse])
async def get_minutes_history(meeting_id: str):
    """Get meeting minutes history"""
    try:
        meeting = await meeting_service.get_meeting(meeting_id)
        return [MeetingMinutesResponse.from_minutes(m) for m in meeting.minutes_history]
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")


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
