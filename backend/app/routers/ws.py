from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import uuid

from app.ws_manager import ws_manager

router = APIRouter(tags=["WebSocket"])
print("[ws] WebSocket Loaded")


@router.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket):
    # Each invigilator gets a unique client ID
    client_id = str(uuid.uuid4())
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive — wait for any message from client
            # Client can send "ping" to check connection
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)