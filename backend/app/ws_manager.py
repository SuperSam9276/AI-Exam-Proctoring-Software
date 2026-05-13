from fastapi import WebSocket
from typing import Dict
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"[ws] Client connected: {client_id}")

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        print(f"[ws] Client disconnected: {client_id}")

    async def broadcast(self, message: dict):
        disconnected = []
        for client_id, ws in self.active_connections.items():
            try:
                await ws.send_json(message)
            except:
                disconnected.append(client_id)
        for client_id in disconnected:
            self.disconnect(client_id)

    def broadcast_sync(self, message: dict):
        """
        Called from sync functions like process_violation.
        Finds the running event loop and schedules the broadcast on it.
        """
        try:
            loop = asyncio.get_running_loop()
            asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)
        except RuntimeError:
            # No running loop — create one just for this call
            asyncio.run(self.broadcast(message))

ws_manager = ConnectionManager()