from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

# -------------------------------
# Home Route
# -------------------------------
@app.get("/")
def home():
    return {"status": "Chatterbox Milestone 4 Server Running 🚀"}


# -------------------------------
# Connection Manager
# -------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, str] = {}
        self.usernames: dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, username: str, room: str):
        self.active_connections[websocket] = room
        self.usernames[websocket] = username
        await self.broadcast_system(room, f"{username} joined {room} 👋")

    def disconnect(self, websocket: WebSocket):
        room = self.active_connections.pop(websocket, None)
        username = self.usernames.pop(websocket, "Someone")
        return username, room

    async def broadcast_room(self, room: str, data: dict):
        for ws, user_room in list(self.active_connections.items()):
            if user_room == room:
                try:
                    await ws.send_json(data)
                except:
                    self.disconnect(ws)

    async def broadcast_system(self, room: str, message: str):
        await self.broadcast_room(room, {
            "type": "system",
            "message": message
        })


manager = ConnectionManager()


# -------------------------------
# WebSocket Endpoint
# -------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        try:
            join_data = await websocket.receive_json()
        except Exception:
             # If receive fails (e.g. immediate disconnect), close and return
            return

        username = join_data.get("username", "Anonymous")
        room = join_data.get("room", "general")

        await manager.connect(websocket, username, room)

        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")

            # Chat message
            if event_type == "chat":
                message = data.get("message", "").strip()
                if not message:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Empty messages are not allowed"
                    })
                    continue

                await manager.broadcast_room(room, {
                    "type": "chat",
                    "username": username,
                    "message": message
                })

            # Typing indicator
            elif event_type == "typing":
                print(f"User {username} is typing in {room}") # DEBUG
                await manager.broadcast_room(room, {
                    "type": "typing",
                    "username": username
                })

            elif event_type == "stop_typing":
                await manager.broadcast_room(room, {
                    "type": "stop_typing",
                    "username": username
                })

    except WebSocketDisconnect:
        username, room = manager.disconnect(websocket)
        if room:
            await manager.broadcast_system(
                room, f"{username} left {room} ❌"
            )


if __name__ == "__main__":
    uvicorn.run("final:app", host="127.0.0.1", port=8000, reload=True)